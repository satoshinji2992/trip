"""场所查询路由 - 附近设施查找、距离排序"""
from flask import Blueprint, request
from app import db
from app.models.facility import Facility
from app.models.graph import GraphNode
from app.services.graph_service import build_graph_from_db
from app.services.sort_service import sort_by_path_distance
from app.services.search_service import fuzzy_search
from app.utils.response import success, error

facility_bp = Blueprint('facility', __name__)


@facility_bp.route('/nearby', methods=['GET'])
def get_nearby_facilities():
    """
    查找附近设施 - 核心算法为查找和排序
    选中某个景点或场所后，查找附近一定范围内的设施，按路径距离排序
    注意：距离是实际可达路径距离，不是直线距离
    
    查询参数:
        scenic_id: 景区/校园ID
        node_id: 当前位置节点ID
        type: 设施类型过滤（可选）
        category: 分类过滤（可选）
        max_distance: 最大距离（米），默认1000
    """
    scenic_id = request.args.get('scenic_id', type=int)
    node_id = request.args.get('node_id', type=int)
    facility_type = request.args.get('type', '')
    category = request.args.get('category', '')
    max_distance = request.args.get('max_distance', 1000, type=float)

    if not scenic_id or not node_id:
        return error('缺少scenic_id或node_id参数')

    # 验证节点存在
    current_node = GraphNode.query.get(node_id)
    if not current_node:
        return error('当前位置节点不存在')

    # 查询设施
    query = Facility.query.filter_by(scenic_id=scenic_id)
    if facility_type:
        query = query.filter_by(type=facility_type)
    if category:
        query = query.filter_by(category=category)

    facilities = query.all()
    facilities_data = [f.to_dict() for f in facilities]

    # 构建图并按路径距离排序（非直线距离，而是实际可达路径距离）
    graph = build_graph_from_db(scenic_id)
    sorted_facilities = sort_by_path_distance(
        facilities_data, graph, node_id, node_id_key='graph_node_id'
    )

    # 过滤最大距离
    result = [f for f in sorted_facilities if f.get('distance', float('inf')) <= max_distance]

    return success({
        'items': result,
        'total': len(result),
        'current_node_id': node_id,
        'max_distance': max_distance,
    })


@facility_bp.route('/search', methods=['GET'])
def search_facilities():
    """
    搜索设施 - 核心算法为查找和排序
    用户输入类别名称查找附近设施，按路径距离排序
    
    查询参数:
        scenic_id: 景区/校园ID
        q: 搜索关键词（类别名称、设施名称等）
        node_id: 当前位置节点ID（可选，用于距离排序）
    """
    scenic_id = request.args.get('scenic_id', type=int)
    query_str = request.args.get('q', '').strip()
    node_id = request.args.get('node_id', type=int)

    if not scenic_id:
        return error('缺少scenic_id参数')
    if not query_str:
        return error('搜索关键词不能为空')

    # 查询所有设施
    facilities = Facility.query.filter_by(scenic_id=scenic_id).all()
    facilities_data = [f.to_dict() for f in facilities]

    # 模糊查找
    matched = fuzzy_search(query_str, facilities_data, fields=['name', 'type', 'category', 'description'])

    # 如果提供了位置节点，按路径距离排序
    if node_id and matched:
        graph = build_graph_from_db(scenic_id)
        matched = sort_by_path_distance(matched, graph, node_id, node_id_key='graph_node_id')

    return success({
        'items': matched,
        'total': len(matched),
        'query': query_str,
    })


@facility_bp.route('/types', methods=['GET'])
def get_facility_types():
    """获取设施类型列表"""
    return success([
        {'value': 'shop', 'label': '商店'},
        {'value': 'restaurant', 'label': '饭店'},
        {'value': 'restroom', 'label': '洗手间'},
        {'value': 'library', 'label': '图书馆'},
        {'value': 'canteen', 'label': '食堂'},
        {'value': 'supermarket', 'label': '超市'},
        {'value': 'cafe', 'label': '咖啡馆'},
        {'value': 'hospital', 'label': '医务室'},
        {'value': 'atm', 'label': 'ATM'},
        {'value': 'parking', 'label': '停车场'},
    ])


@facility_bp.route('/by-category', methods=['GET'])
def filter_by_category():
    """
    按类别过滤设施
    可以通过选择类别对结果进行过滤
    """
    scenic_id = request.args.get('scenic_id', type=int)
    category = request.args.get('category', '').strip()

    if not scenic_id:
        return error('缺少scenic_id参数')

    query = Facility.query.filter_by(scenic_id=scenic_id)
    if category:
        query = query.filter_by(type=category)

    facilities = query.all()
    return success({
        'items': [f.to_dict() for f in facilities],
        'total': len(facilities),
    })
