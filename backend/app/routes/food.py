"""美食推荐路由 - 核心算法为模糊查找算法和排序算法"""
import json
from flask import Blueprint, request
from flask_login import current_user
from app import db
from app.models.food import Food, Restaurant
from app.models.graph import GraphNode
from app.services.graph_service import build_graph_from_db, dijkstra
from app.services.sort_service import recommend_foods, SortableItem, top_k_sort
from app.services.search_service import fuzzy_search
from app.utils.response import success, error

food_bp = Blueprint('food', __name__)


@food_bp.route('/recommend', methods=['GET'])
def recommend_food():
    """
    美食推荐 - 核心算法为排序算法
    按用户选择的热度、评价和距离排序，根据菜系过滤
    Top-K排序：不经过完全排序即可排好前10个
    
    查询参数:
        scenic_id: 景区/校园ID
        sort_by: 排序方式 popularity/rating/distance/mixed
        cuisine: 菜系过滤
        top_k: 返回前K个
        node_id: 用户当前位置节点ID（距离排序时需要）
    """
    scenic_id = request.args.get('scenic_id', type=int)
    sort_by = request.args.get('sort_by', 'mixed')
    cuisine = request.args.get('cuisine', '')
    top_k = request.args.get('top_k', 10, type=int)
    node_id = request.args.get('node_id', type=int)

    if not scenic_id:
        return error('缺少scenic_id参数')

    # 查询餐厅
    query = Restaurant.query.filter_by(scenic_id=scenic_id)
    if cuisine:
        query = query.filter_by(cuisine=cuisine)

    restaurants = query.all()
    foods_data = [r.to_dict() for r in restaurants]

    # 如果需要按距离排序且提供了位置
    if node_id and (sort_by == 'distance' or sort_by == 'mixed'):
        graph = build_graph_from_db(scenic_id)
        distances, _ = dijkstra(graph, node_id, weight_type='distance')
        for food in foods_data:
            gn_id = food.get('graph_node_id')
            if gn_id and gn_id in distances:
                food['distance'] = distances[gn_id]
            else:
                food['distance'] = float('inf')

    # 使用Top-K排序算法
    sorted_data = recommend_foods(foods_data, sort_by=sort_by, top_k=top_k)

    return success({
        'items': sorted_data,
        'total': len(sorted_data),
        'sort_by': sort_by,
    })


@food_bp.route('/search', methods=['GET'])
def search_food():
    """
    美食搜索 - 核心算法为模糊查找算法和排序算法
    输入美食名称、菜系、饭店或窗口名称等进行基于内容的模糊查询
    查询结果按热度、评价和距离排序
    
    查询参数:
        scenic_id: 景区/校园ID
        q: 搜索关键词
        sort_by: 结果排序方式
        node_id: 用户位置节点ID（距离排序）
    """
    scenic_id = request.args.get('scenic_id', type=int)
    query_str = request.args.get('q', '').strip()
    sort_by = request.args.get('sort_by', 'mixed')
    node_id = request.args.get('node_id', type=int)

    if not scenic_id:
        return error('缺少scenic_id参数')
    if not query_str:
        return error('搜索关键词不能为空')

    # 同时搜索餐厅和菜品
    restaurants = Restaurant.query.filter_by(scenic_id=scenic_id).all()
    restaurants_data = [r.to_dict() for r in restaurants]

    foods = Food.query.join(Restaurant).filter(Restaurant.scenic_id == scenic_id).all()
    foods_data = [f.to_dict() for f in foods]

    # 模糊查找餐厅
    matched_restaurants = fuzzy_search(
        query_str, restaurants_data,
        fields=['name', 'cuisine', 'description']
    )

    # 模糊查找菜品
    matched_foods = fuzzy_search(
        query_str, foods_data,
        fields=['name', 'cuisine', 'description', 'restaurant_name']
    )

    # 如果有位置，附加距离信息
    if node_id:
        graph = build_graph_from_db(scenic_id)
        distances, _ = dijkstra(graph, node_id, weight_type='distance')
        for item in matched_restaurants:
            gn_id = item.get('graph_node_id')
            if gn_id and gn_id in distances:
                item['distance'] = distances[gn_id]
            else:
                item['distance'] = float('inf')

    # 对结果排序
    sorted_restaurants = recommend_foods(matched_restaurants, sort_by=sort_by, top_k=len(matched_restaurants))

    return success({
        'restaurants': sorted_restaurants,
        'foods': matched_foods,
        'total_restaurants': len(sorted_restaurants),
        'total_foods': len(matched_foods),
        'query': query_str,
    })


@food_bp.route('/cuisines', methods=['GET'])
def get_cuisines():
    """获取菜系列表"""
    return success([
        {'value': 'chinese', 'label': '中餐'},
        {'value': 'western', 'label': '西餐'},
        {'value': 'japanese', 'label': '日料'},
        {'value': 'korean', 'label': '韩餐'},
        {'value': 'fast_food', 'label': '快餐'},
        {'value': 'snack', 'label': '小吃'},
        {'value': 'cafe', 'label': '咖啡甜品'},
        {'value': 'other', 'label': '其他'},
    ])


@food_bp.route('/restaurant/<int:restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    """获取餐厅详情及菜品列表"""
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return error('餐厅不存在', 404)

    # 增加热度
    restaurant.popularity += 1
    db.session.commit()

    data = restaurant.to_dict()
    data['foods'] = [f.to_dict() for f in restaurant.foods.all()]

    return success(data)
