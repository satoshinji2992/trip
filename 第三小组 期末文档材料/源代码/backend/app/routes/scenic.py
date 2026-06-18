"""景区/校园路由 - 旅游推荐功能"""
import json
from flask import Blueprint, request
from flask_login import current_user
from app import db
from app.models.scenic import Scenic
from app.services.sort_service import recommend_scenics
from app.services.search_service import fuzzy_search, Trie
from app.utils.response import success, error, paginate

scenic_bp = Blueprint('scenic', __name__)

# 全局Trie树缓存，用于高效名称查找
_scenic_trie = None


def _get_scenic_trie():
    """获取或构建景区名称Trie树"""
    global _scenic_trie
    if _scenic_trie is None:
        _scenic_trie = Trie()
        scenics = Scenic.query.all()
        for s in scenics:
            # 插入名称的每个字符前缀
            _scenic_trie.insert(s.name.lower(), s.id)
            # 插入分类
            if s.category:
                _scenic_trie.insert(s.category.lower(), s.id)
    return _scenic_trie


def _invalidate_trie():
    """使Trie缓存失效"""
    global _scenic_trie
    _scenic_trie = None


@scenic_bp.route('/list', methods=['GET'])
def list_scenics():
    """
    获取景区/校园列表，支持排序和过滤
    
    查询参数:
        page: 页码
        per_page: 每页数量
        type: 类型过滤 scenic/campus
        category: 分类过滤
        sort_by: 排序方式 popularity/rating/mixed
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    scenic_type = request.args.get('type', '')
    category = request.args.get('category', '')
    sort_by = request.args.get('sort_by', 'mixed')

    query = Scenic.query
    if scenic_type:
        query = query.filter_by(type=scenic_type)
    if category:
        query = query.filter_by(category=category)

    # 获取所有符合条件的数据
    all_scenics = query.all()
    scenics_data = [s.to_dict() for s in all_scenics]

    # 获取用户兴趣
    user_interests = None
    if current_user.is_authenticated:
        try:
            user_interests = json.loads(current_user.interests) if current_user.interests else None
        except Exception:
            user_interests = None

    # 使用推荐排序算法（Top-K排序，不经过完全排序即可排好前K个）
    sorted_data = recommend_scenics(scenics_data, user_interests, sort_by, top_k=len(scenics_data))

    # 手动分页
    start = (page - 1) * per_page
    end = start + per_page
    paged_data = sorted_data[start:end]

    return success({
        'items': paged_data,
        'total': len(sorted_data),
        'page': page,
        'per_page': per_page,
        'pages': (len(sorted_data) + per_page - 1) // per_page,
    })


@scenic_bp.route('/recommend', methods=['GET'])
def recommend():
    """
    推荐景区/校园 - 核心功能
    使用Top-K排序算法，只排好前10个，不经过完全排序
    考虑数据动态变化
    
    查询参数:
        sort_by: 排序方式 popularity/rating/mixed
        top_k: 返回前K个，默认10
        type: 类型过滤
    """
    sort_by = request.args.get('sort_by', 'mixed')
    top_k = request.args.get('top_k', 10, type=int)
    scenic_type = request.args.get('type', '')

    query = Scenic.query
    if scenic_type:
        query = query.filter_by(type=scenic_type)

    all_scenics = query.all()
    scenics_data = [s.to_dict() for s in all_scenics]

    # 获取用户兴趣
    user_interests = None
    if current_user.is_authenticated:
        try:
            user_interests = json.loads(current_user.interests) if current_user.interests else None
        except Exception:
            user_interests = None

    # 核心：Top-K排序，不经过完全排序
    sorted_data = recommend_scenics(scenics_data, user_interests, sort_by, top_k=top_k)

    return success({
        'items': sorted_data,
        'total': len(sorted_data),
        'sort_by': sort_by,
    })


@scenic_bp.route('/search', methods=['GET'])
def search_scenics():
    """
    搜索景区/校园
    核心算法：查找算法和排序算法
    支持按名称、类别、关键字搜索，结果按热度和评价排序
    
    查询参数:
        q: 搜索关键词
        type: 类型过滤
        category: 分类过滤
        sort_by: 结果排序方式
    """
    query_str = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    scenic_type = request.args.get('type', '')
    category = request.args.get('category', '')
    sort_by = request.args.get('sort_by', 'mixed')

    if not query_str:
        return error('搜索关键词不能为空')

    # 构建基础查询
    query = Scenic.query
    if scenic_type:
        query = query.filter_by(type=scenic_type)
    if category:
        query = query.filter_by(category=category)

    all_scenics = query.all()
    scenics_data = [s.to_dict() for s in all_scenics]

    # 使用模糊查找算法搜索
    matched = fuzzy_search(query_str, scenics_data, fields=['name', 'category', 'tags'])

    # 对结果再按热度/评价排序
    user_interests = None
    if current_user.is_authenticated:
        try:
            user_interests = json.loads(current_user.interests) if current_user.interests else None
        except Exception:
            user_interests = None

    if sort_by != 'relevance':
        sorted_data = recommend_scenics(matched, user_interests, sort_by, top_k=len(matched))
    else:
        sorted_data = matched

    start = (page - 1) * per_page
    end = start + per_page
    paged_data = sorted_data[start:end]

    return success({
        'items': paged_data,
        'total': len(sorted_data),
        'query': query_str,
        'page': page,
        'per_page': per_page,
        'pages': (len(sorted_data) + per_page - 1) // per_page,
    })


@scenic_bp.route('/<int:scenic_id>', methods=['GET'])
def get_scenic(scenic_id):
    """获取景区/校园详情"""
    scenic = Scenic.query.get(scenic_id)
    if not scenic:
        return error('景区/校园不存在', 404)

    # 增加热度
    scenic.popularity += 1
    db.session.commit()

    data = scenic.to_dict()
    # 附加建筑物列表
    data['buildings'] = [b.to_dict() for b in scenic.buildings.all()]
    # 附加设施列表
    data['facilities'] = [f.to_dict() for f in scenic.facilities.all()]

    return success(data)


@scenic_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    categories = db.session.query(Scenic.category).distinct().all()
    return success([c[0] for c in categories if c[0]])


@scenic_bp.route('/types', methods=['GET'])
def get_types():
    """获取所有类型"""
    return success([
        {'value': 'scenic', 'label': '景区'},
        {'value': 'campus', 'label': '校园'},
    ])
