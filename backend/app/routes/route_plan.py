"""路线规划路由 - 最短路径、多点路线、交通工具策略"""
from flask import Blueprint, request
from app.services.graph_service import (
    build_graph_from_db, shortest_path, multi_destination_shortest_path, build_indoor_graph
)
from app.models.graph import GraphNode, GraphEdge
from app.utils.response import success, error

route_bp = Blueprint('route', __name__)


@route_bp.route('/shortest', methods=['POST'])
def get_shortest_path():
    """
    最短路径规划 - 核心算法为Dijkstra最短路径算法
    
    请求体:
        scenic_id: 景区/校园ID
        from_node_id: 起点节点ID
        to_node_id: 终点节点ID
        strategy: 策略 - distance=最短距离, time=最短时间
        transport: 交通工具 - walk=步行, bike=自行车, cart=电瓶车
    """
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    scenic_id = data.get('scenic_id')
    from_node_id = data.get('from_node_id')
    to_node_id = data.get('to_node_id')
    strategy = data.get('strategy', 'distance')
    transport = data.get('transport', 'walk')

    if not all([scenic_id, from_node_id, to_node_id]):
        return error('缺少必要参数：scenic_id, from_node_id, to_node_id')

    # 验证节点存在
    from_node = GraphNode.query.get(from_node_id)
    to_node = GraphNode.query.get(to_node_id)
    if not from_node or not to_node:
        return error('起点或终点不存在')

    # 构建图（考虑交通工具限制）
    graph = build_graph_from_db(scenic_id, transport_mode=transport)

    # 确定权重类型
    weight_type = 'distance' if strategy == 'distance' else 'time'

    # 执行Dijkstra最短路径算法
    path, total_cost = shortest_path(graph, from_node_id, to_node_id, weight_type)

    if not path:
        return error('未找到可达路径')

    # 构建路径详细信息
    path_details = []
    for node_id in path:
        node_info = graph.nodes.get(node_id, {})
        path_details.append({
            'node_id': node_id,
            'name': node_info.get('name', ''),
            'x': node_info.get('x', 0),
            'y': node_info.get('y', 0),
            'latitude': node_info.get('latitude', 0),
            'longitude': node_info.get('longitude', 0),
        })

    # 计算另一种策略的成本（如果按距离算，也提供时间估算，反之亦然）
    other_type = 'time' if weight_type == 'distance' else 'distance'
    _, other_cost = shortest_path(graph, from_node_id, to_node_id, other_type)

    return success({
        'path': path,
        'path_details': path_details,
        'total_cost': round(total_cost, 2),
        'cost_unit': '米' if weight_type == 'distance' else '分钟',
        'strategy': strategy,
        'transport': transport,
        'distance': round(total_cost, 2) if weight_type == 'distance' else round(other_cost, 2),
        'time': round(other_cost, 2) if weight_type == 'distance' else round(total_cost, 2),
        'node_count': len(path),
    })


@route_bp.route('/multi', methods=['POST'])
def get_multi_destination_path():
    """
    途经多点最短路径 - 核心算法为途经多点最短路径算法（TSP近似）
    从当前位置出发，参观多个景点/场所，参观完返回当前位置
    
    请求体:
        scenic_id: 景区/校园ID
        start_node_id: 起点（当前位置）节点ID
        destinations: 目标节点ID列表
        strategy: 策略 - distance=最短距离, time=最短时间
        transport: 交通工具
        return_to_start: 是否返回起点，默认true
    """
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    scenic_id = data.get('scenic_id')
    start_node_id = data.get('start_node_id')
    destinations = data.get('destinations', [])
    strategy = data.get('strategy', 'distance')
    transport = data.get('transport', 'walk')
    return_to_start = data.get('return_to_start', True)

    if not all([scenic_id, start_node_id]):
        return error('缺少必要参数')

    if not destinations:
        return error('至少需要一个目的地')

    # 验证节点
    start_node = GraphNode.query.get(start_node_id)
    if not start_node:
        return error('起点不存在')

    for dest_id in destinations:
        node = GraphNode.query.get(dest_id)
        if not node:
            return error(f'目标节点 {dest_id} 不存在')

    # 构建图
    graph = build_graph_from_db(scenic_id, transport_mode=transport)
    weight_type = 'distance' if strategy == 'distance' else 'time'

    # 执行多点最短路径算法
    ordered_path, ordered_destinations, total_cost, segment_paths = \
        multi_destination_shortest_path(graph, start_node_id, destinations, weight_type, return_to_start)

    if not ordered_path:
        return error('未找到可达路径')

    # 构建路径详细信息
    path_details = []
    for node_id in ordered_path:
        node_info = graph.nodes.get(node_id, {})
        path_details.append({
            'node_id': node_id,
            'name': node_info.get('name', ''),
            'x': node_info.get('x', 0),
            'y': node_info.get('y', 0),
        })

    # 构建分段路径信息
    segments_info = []
    unreachable_node_ids = []
    for seg in segment_paths:
        if 'unreachable' in seg:
            unreachable_node_ids.extend(seg.get('unreachable') or [])
            continue
        from_info = graph.nodes.get(seg['from'], {})
        to_info = graph.nodes.get(seg['to'], {})
        segments_info.append({
            'from_node_id': seg['from'],
            'from_name': from_info.get('name', ''),
            'to_node_id': seg['to'],
            'to_name': to_info.get('name', ''),
            'path': seg['path'],
            'cost': round(seg['cost'], 2),
        })

    return success({
        'ordered_path': ordered_path,
        'path_details': path_details,
        'visit_order': ordered_destinations,
        'total_cost': round(total_cost, 2),
        'cost_unit': '米' if weight_type == 'distance' else '分钟',
        'segments': segments_info,
        'strategy': strategy,
        'transport': transport,
        'return_to_start': return_to_start,
        'unreachable_node_ids': unreachable_node_ids,
        'unreachable_names': [
            graph.nodes.get(node_id, {}).get('name', str(node_id))
            for node_id in unreachable_node_ids
        ],
    })


@route_bp.route('/transport-options', methods=['GET'])
def get_transport_options():
    """
    获取交通工具选项
    校区内: 自行车和步行（默认自行车任何地点都有）
    景区内: 步行和电瓶车（电瓶车路线固定，默认上车即走）
    """
    scenic_id = request.args.get('scenic_id', type=int)
    if not scenic_id:
        return error('缺少scenic_id参数')

    from app.models.scenic import Scenic
    scenic = Scenic.query.get(scenic_id)
    if not scenic:
        return error('景区/校园不存在')

    if scenic.type == 'campus':
        options = [
            {'value': 'walk', 'label': '步行', 'speed': '5km/h', 'description': '步行可到达任意地点'},
            {'value': 'bike', 'label': '自行车', 'speed': '15km/h', 'description': '校区内默认自行车任何地点都有'},
        ]
    else:
        options = [
            {'value': 'walk', 'label': '步行', 'speed': '5km/h', 'description': '步行可到达任意地点'},
            {'value': 'cart', 'label': '电瓶车', 'speed': '20km/h', 'description': '电瓶车路线固定，上车即走'},
        ]

    return success(options)


@route_bp.route('/nodes', methods=['GET'])
def get_graph_nodes():
    """获取景区/校园的道路图节点"""
    scenic_id = request.args.get('scenic_id', type=int)
    if not scenic_id:
        return error('缺少scenic_id参数')

    nodes = GraphNode.query.filter_by(scenic_id=scenic_id).all()
    return success([n.to_dict() for n in nodes])


@route_bp.route('/edges', methods=['GET'])
def get_graph_edges():
    """获取景区/校园的道路图边"""
    scenic_id = request.args.get('scenic_id', type=int)
    if not scenic_id:
        return error('缺少scenic_id参数')

    edges = GraphEdge.query.filter_by(scenic_id=scenic_id).all()
    return success([e.to_dict() for e in edges])


@route_bp.route('/map-data', methods=['GET'])
def get_map_data():
    """获取完整地图数据（节点+边），用于前端地图展示"""
    scenic_id = request.args.get('scenic_id', type=int)
    if not scenic_id:
        return error('缺少scenic_id参数')

    nodes = GraphNode.query.filter_by(scenic_id=scenic_id).all()
    edges = GraphEdge.query.filter_by(scenic_id=scenic_id).all()
    from app.models.building import Building
    from app.models.facility import Facility
    buildings = Building.query.filter_by(scenic_id=scenic_id).all()
    facilities = Facility.query.filter_by(scenic_id=scenic_id).all()

    return success({
        'nodes': [n.to_dict() for n in nodes],
        'edges': [e.to_dict() for e in edges],
        'buildings': [b.to_dict() for b in buildings],
        'facilities': [f.to_dict() for f in facilities],
        'node_count': len(nodes),
        'edge_count': len(edges),
        'building_count': len(buildings),
        'facility_count': len(facilities),
    })
