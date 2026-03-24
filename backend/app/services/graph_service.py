"""
图算法服务 - 路线规划核心
包含：Dijkstra最短路径、多点最短路径（TSP近似）、不同交通工具策略、拥挤度策略
所有核心算法均基于自设计的数据结构，自己编程实现
"""
import heapq
from collections import defaultdict


class Graph:
    """自定义图数据结构 - 邻接表表示"""

    def __init__(self):
        # 邻接表: {node_id: [(neighbor_id, distance, time_cost, edge_info), ...]}
        self.adjacency = defaultdict(list)
        self.nodes = {}  # {node_id: node_info}

    def add_node(self, node_id, info=None):
        """添加节点"""
        self.nodes[node_id] = info or {}

    def add_edge(self, from_id, to_id, distance, time_cost, edge_info=None):
        """添加有向边"""
        self.adjacency[from_id].append((to_id, distance, time_cost, edge_info or {}))

    def add_undirected_edge(self, from_id, to_id, distance, time_cost, edge_info=None):
        """添加无向边"""
        self.add_edge(from_id, to_id, distance, time_cost, edge_info)
        self.add_edge(to_id, from_id, distance, time_cost, edge_info)

    def get_neighbors(self, node_id):
        """获取邻居节点"""
        return self.adjacency.get(node_id, [])


class MinHeap:
    """最小堆 - 用于Dijkstra算法的优先队列，自实现数据结构"""

    def __init__(self):
        self._data = []
        self._size = 0

    def push(self, priority, item):
        """插入元素"""
        self._data.append((priority, item))
        self._size += 1
        self._sift_up(self._size - 1)

    def pop(self):
        """弹出最小元素"""
        if self._size == 0:
            raise IndexError("堆为空")
        min_item = self._data[0]
        self._size -= 1
        if self._size > 0:
            self._data[0] = self._data[self._size]
            self._data.pop()
            self._sift_down(0)
        else:
            self._data.pop()
        return min_item

    def is_empty(self):
        return self._size == 0

    def _sift_up(self, index):
        """上浮操作"""
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index][0] < self._data[parent][0]:
                self._data[index], self._data[parent] = self._data[parent], self._data[index]
                index = parent
            else:
                break

    def _sift_down(self, index):
        """下沉操作"""
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2
            if left < self._size and self._data[left][0] < self._data[smallest][0]:
                smallest = left
            if right < self._size and self._data[right][0] < self._data[smallest][0]:
                smallest = right
            if smallest != index:
                self._data[index], self._data[smallest] = self._data[smallest], self._data[index]
                index = smallest
            else:
                break


def dijkstra(graph, start_id, end_id=None, weight_type='distance'):
    """
    Dijkstra最短路径算法 - 核心算法，自实现
    
    参数:
        graph: Graph对象
        start_id: 起点节点ID
        end_id: 终点节点ID（None表示计算到所有节点的最短路径）
        weight_type: 权重类型，'distance'=最短距离，'time'=最短时间
    
    返回:
        distances: {node_id: 最短距离/时间}
        predecessors: {node_id: 前驱节点ID}，用于路径重建
    """
    distances = {start_id: 0}
    predecessors = {start_id: None}
    visited = set()

    # 使用自实现的最小堆
    heap = MinHeap()
    heap.push(0, start_id)

    while not heap.is_empty():
        current_dist, current_node = heap.pop()

        if current_node in visited:
            continue
        visited.add(current_node)

        # 如果找到了目标节点，提前返回
        if end_id is not None and current_node == end_id:
            break

        for neighbor_id, distance, time_cost, edge_info in graph.get_neighbors(current_node):
            if neighbor_id in visited:
                continue

            weight = distance if weight_type == 'distance' else time_cost
            new_dist = current_dist + weight

            if neighbor_id not in distances or new_dist < distances[neighbor_id]:
                distances[neighbor_id] = new_dist
                predecessors[neighbor_id] = current_node
                heap.push(new_dist, neighbor_id)

    return distances, predecessors


def reconstruct_path(predecessors, start_id, end_id):
    """从前驱数组重建路径"""
    if end_id not in predecessors:
        return []

    path = []
    current = end_id
    while current is not None:
        path.append(current)
        current = predecessors.get(current)
    path.reverse()

    if path and path[0] == start_id:
        return path
    return []


def shortest_path(graph, start_id, end_id, weight_type='distance'):
    """
    计算两点之间的最短路径
    
    返回:
        path: 节点ID列表
        total_cost: 总距离/时间
    """
    distances, predecessors = dijkstra(graph, start_id, end_id, weight_type)
    path = reconstruct_path(predecessors, start_id, end_id)
    total_cost = distances.get(end_id, float('inf'))
    return path, total_cost


def multi_destination_shortest_path(graph, start_id, destinations, weight_type='distance', return_to_start=True):
    """
    途经多点最短路径算法 - TSP近似解（贪心+2-opt优化）
    核心算法：从当前位置出发，参观多个景点/场所的最优旅游线路，参观完返回当前位置
    
    参数:
        graph: Graph对象
        start_id: 起点节点ID
        destinations: 目标节点ID列表
        weight_type: 权重类型
        return_to_start: 是否返回起点
    
    返回:
        ordered_path: 完整路径（包含所有中间节点）
        ordered_destinations: 目的地访问顺序
        total_cost: 总距离/时间
        segment_paths: 每段路径详情
    """
    if not destinations:
        return [], [], 0, []

    # 计算所有关键点之间的最短距离矩阵
    all_points = [start_id] + list(destinations)
    dist_matrix = {}
    path_matrix = {}

    for point in all_points:
        distances, predecessors = dijkstra(graph, point, weight_type=weight_type)
        for other_point in all_points:
            if point != other_point:
                dist_matrix[(point, other_point)] = distances.get(other_point, float('inf'))
                path_matrix[(point, other_point)] = reconstruct_path(predecessors, point, other_point)

    # 贪心算法构建初始解：每次选择最近的未访问节点
    unvisited = set(destinations)
    current = start_id
    greedy_order = []

    while unvisited:
        nearest = None
        nearest_dist = float('inf')
        for dest in unvisited:
            d = dist_matrix.get((current, dest), float('inf'))
            if d < nearest_dist:
                nearest_dist = d
                nearest = dest
        if nearest is None:
            break
        greedy_order.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    # 2-opt优化：反转子路径以减少总距离
    def calculate_total_cost(order):
        """计算给定访问顺序的总成本"""
        cost = 0
        prev = start_id
        for node in order:
            cost += dist_matrix.get((prev, node), float('inf'))
            prev = node
        if return_to_start:
            cost += dist_matrix.get((prev, start_id), float('inf'))
        return cost

    best_order = greedy_order[:]
    best_cost = calculate_total_cost(best_order)
    improved = True
    max_iterations = 100

    iteration = 0
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        for i in range(len(best_order) - 1):
            for j in range(i + 1, len(best_order)):
                # 尝试反转 i 到 j 之间的子路径
                new_order = best_order[:i] + best_order[i:j + 1][::-1] + best_order[j + 1:]
                new_cost = calculate_total_cost(new_order)
                if new_cost < best_cost:
                    best_order = new_order
                    best_cost = new_cost
                    improved = True

    # 构建完整路径
    ordered_path = []
    segment_paths = []
    prev = start_id
    for dest in best_order:
        segment = path_matrix.get((prev, dest), [])
        segment_cost = dist_matrix.get((prev, dest), 0)
        segment_paths.append({
            'from': prev,
            'to': dest,
            'path': segment,
            'cost': segment_cost,
        })
        # 避免重复添加连接点
        if ordered_path and segment and segment[0] == ordered_path[-1]:
            ordered_path.extend(segment[1:])
        else:
            ordered_path.extend(segment)
        prev = dest

    if return_to_start and best_order:
        last = best_order[-1]
        return_segment = path_matrix.get((last, start_id), [])
        return_cost = dist_matrix.get((last, start_id), 0)
        segment_paths.append({
            'from': last,
            'to': start_id,
            'path': return_segment,
            'cost': return_cost,
        })
        if ordered_path and return_segment and return_segment[0] == ordered_path[-1]:
            ordered_path.extend(return_segment[1:])
        else:
            ordered_path.extend(return_segment)

    return ordered_path, best_order, best_cost, segment_paths


def build_graph_from_db(scenic_id, transport_mode='walk'):
    """
    从数据库构建图数据结构
    
    参数:
        scenic_id: 景区/校园ID
        transport_mode: 交通模式 - walk=步行, bike=自行车, cart=电瓶车
    
    返回:
        Graph对象
    """
    from app.models.graph import GraphNode, GraphEdge

    graph = Graph()

    # 加载节点
    nodes = GraphNode.query.filter_by(scenic_id=scenic_id).all()
    for node in nodes:
        graph.add_node(node.id, node.to_dict())

    # 加载边，根据交通模式过滤
    edges = GraphEdge.query.filter_by(scenic_id=scenic_id).all()
    for edge in edges:
        # 检查交通工具是否允许
        if not _is_transport_allowed(edge, transport_mode):
            continue

        # 根据交通模式调整速度
        adjusted_speed = _get_adjusted_speed(edge, transport_mode)
        distance = edge.distance
        # 时间 = 距离(米) / 速度(km/h) * 60 / 1000 = 距离 / 速度 * 0.06
        time_cost = (distance / 1000.0) / adjusted_speed * 60.0 if adjusted_speed > 0 else float('inf')

        edge_info = {
            'edge_id': edge.id,
            'road_name': edge.road_name,
            'road_type': edge.road_type,
            'congestion': edge.congestion,
            'transport': transport_mode,
        }

        if edge.bidirectional:
            graph.add_undirected_edge(edge.from_node_id, edge.to_node_id, distance, time_cost, edge_info)
        else:
            graph.add_edge(edge.from_node_id, edge.to_node_id, distance, time_cost, edge_info)

    return graph


def _is_transport_allowed(edge, transport_mode):
    """检查该边是否允许指定交通工具通行"""
    allowed = edge.transport_allowed
    if allowed == 'all':
        return True
    if transport_mode == 'walk':
        return True  # 步行总是允许的
    if transport_mode == 'bike':
        return allowed in ('bike', 'all', 'bike_walk')
    if transport_mode == 'cart':
        return allowed in ('cart', 'all', 'cart_only')
    return True


def _get_adjusted_speed(edge, transport_mode):
    """根据交通模式和拥挤度调整速度"""
    base_speeds = {
        'walk': 5.0,    # 步行 5km/h
        'bike': 15.0,   # 自行车 15km/h
        'cart': 20.0,   # 电瓶车 20km/h（固定路线）
    }
    base_speed = base_speeds.get(transport_mode, 5.0)
    # 考虑拥挤度: 实际速度 = (1 - congestion) * 基础速度，最低为基础速度的10%
    congestion_factor = max(0.1, 1.0 - edge.congestion)
    return base_speed * congestion_factor


def build_indoor_graph(building_id):
    """从数据库构建室内导航图"""
    from app.models.building import IndoorNode, IndoorEdge

    graph = Graph()

    nodes = IndoorNode.query.filter_by(building_id=building_id).all()
    for node in nodes:
        graph.add_node(node.id, node.to_dict())

    edges = IndoorEdge.query.filter_by(building_id=building_id).all()
    for edge in edges:
        time_cost = edge.distance / 1.0 * 0.02  # 室内步行速度约 3km/h
        edge_info = {'edge_type': edge.edge_type}
        if edge.bidirectional:
            graph.add_undirected_edge(edge.from_node_id, edge.to_node_id, edge.distance, time_cost, edge_info)
        else:
            graph.add_edge(edge.from_node_id, edge.to_node_id, edge.distance, time_cost, edge_info)

    return graph
