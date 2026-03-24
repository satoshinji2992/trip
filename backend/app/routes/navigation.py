"""室内导航路由 - 室内导航策略"""
from flask import Blueprint, request
from app.models.building import Building, IndoorNode, IndoorEdge
from app.services.graph_service import build_indoor_graph, shortest_path
from app.utils.response import success, error

nav_bp = Blueprint('navigation', __name__)


@nav_bp.route('/indoor/path', methods=['POST'])
def indoor_navigation():
    """
    室内导航 - 模拟教学楼、博物馆等建筑内部结构
    包括大门到电梯的导航、楼层间的电梯导航和楼层内到房间的导航
    
    请求体:
        building_id: 建筑ID
        from_node_id: 起点节点ID（如大门入口）
        to_node_id: 终点节点ID（如某个房间）
    """
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    building_id = data.get('building_id')
    from_node_id = data.get('from_node_id')
    to_node_id = data.get('to_node_id')

    if not all([building_id, from_node_id, to_node_id]):
        return error('缺少必要参数')

    building = Building.query.get(building_id)
    if not building:
        return error('建筑不存在')

    # 构建室内图
    graph = build_indoor_graph(building_id)

    # 计算室内最短路径
    path, total_distance = shortest_path(graph, from_node_id, to_node_id, 'distance')

    if not path:
        return error('未找到室内路径')

    # 构建详细路径信息，包含楼层变化
    path_details = []
    navigation_steps = []
    prev_floor = None

    for i, node_id in enumerate(path):
        node_info = graph.nodes.get(node_id, {})
        current_floor = node_info.get('floor', 1)
        node_detail = {
            'node_id': node_id,
            'name': node_info.get('name', ''),
            'node_type': node_info.get('node_type', ''),
            'floor': current_floor,
            'x': node_info.get('x', 0),
            'y': node_info.get('y', 0),
        }
        path_details.append(node_detail)

        # 生成导航指令
        if prev_floor is not None and current_floor != prev_floor:
            if node_info.get('node_type') == 'elevator':
                navigation_steps.append({
                    'instruction': f'乘坐电梯从{prev_floor}层到{current_floor}层',
                    'type': 'elevator',
                    'from_floor': prev_floor,
                    'to_floor': current_floor,
                })
            elif node_info.get('node_type') == 'stair':
                direction = '上' if current_floor > prev_floor else '下'
                navigation_steps.append({
                    'instruction': f'走楼梯{direction}到{current_floor}层',
                    'type': 'stair',
                    'from_floor': prev_floor,
                    'to_floor': current_floor,
                })
        elif i > 0:
            prev_name = graph.nodes.get(path[i - 1], {}).get('name', '')
            navigation_steps.append({
                'instruction': f'从"{prev_name}"前往"{node_info.get("name", "")}"',
                'type': 'walk',
                'floor': current_floor,
            })

        prev_floor = current_floor

    return success({
        'path': path,
        'path_details': path_details,
        'navigation_steps': navigation_steps,
        'total_distance': round(total_distance, 2),
        'building_name': building.name,
        'building_floors': building.floors,
        'has_elevator': building.has_elevator,
    })


@nav_bp.route('/indoor/building/<int:building_id>', methods=['GET'])
def get_building_info(building_id):
    """获取建筑详情及室内节点"""
    building = Building.query.get(building_id)
    if not building:
        return error('建筑不存在')

    nodes = IndoorNode.query.filter_by(building_id=building_id).all()
    edges = IndoorEdge.query.filter_by(building_id=building_id).all()

    # 按楼层分组节点
    floors_data = {}
    for node in nodes:
        floor = node.floor
        if floor not in floors_data:
            floors_data[floor] = []
        floors_data[floor].append(node.to_dict())

    return success({
        'building': building.to_dict(),
        'floors': floors_data,
        'nodes': [n.to_dict() for n in nodes],
        'edges': [e.to_dict() for e in edges],
        'total_nodes': len(nodes),
        'total_edges': len(edges),
    })


@nav_bp.route('/indoor/buildings', methods=['GET'])
def list_buildings():
    """获取景区/校园的建筑物列表"""
    scenic_id = request.args.get('scenic_id', type=int)
    if not scenic_id:
        return error('缺少scenic_id参数')

    buildings = Building.query.filter_by(scenic_id=scenic_id).all()
    return success([b.to_dict() for b in buildings])
