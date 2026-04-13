"""道路图数据初始化 - 支持真实地图导入和模拟数据回退"""
import json
import math
import os
import random
import urllib.error
import urllib.parse
import urllib.request

from app import db
from app.models.graph import GraphNode, GraphEdge


REAL_MAP_DIR = os.path.join(os.path.dirname(__file__), 'real_map_data')
REAL_MAP_MANIFEST = os.path.join(REAL_MAP_DIR, 'manifest.json')
OVERPASS_URL = os.environ.get('OVERPASS_URL', 'https://overpass-api.de/api/interpreter')
DEFAULT_FETCH_RADIUS = int(os.environ.get('REAL_MAP_RADIUS', '900'))
ALLOWED_HIGHWAYS = {
    'footway', 'pedestrian', 'path', 'steps', 'service', 'track', 'cycleway',
    'living_street', 'residential', 'unclassified', 'tertiary', 'secondary',
    'primary', 'trunk',
}


def create_road_graphs(scenics):
    """为景区和校园创建道路图，优先使用真实地图，失败时回退到模拟图"""
    total_nodes = 0
    total_edges = 0
    manifest = _load_real_map_manifest()
    env_targets = _parse_env_target_names()
    fetch_all = os.environ.get('REAL_MAP_FETCH_ALL', '').lower() in {'1', 'true', 'yes'}

    target_scenics = _collect_target_scenics(scenics, manifest, env_targets)

    for scenic in target_scenics:
        source_config = manifest.get(scenic.name, {})
        should_try_real = bool(source_config) or fetch_all or scenic.name in env_targets
        created_nodes = 0
        created_edges = 0

        if should_try_real:
            try:
                created_nodes, created_edges = _create_real_road_graph(scenic, source_config)
                print(f"  {scenic.name}: 导入真实地图 {created_nodes} 个节点 / {created_edges} 条边")
            except Exception as exc:
                print(f"  {scenic.name}: 真实地图导入失败，回退模拟图 ({exc})")

        if created_nodes == 0 or created_edges == 0:
            created_nodes, created_edges = _create_simulated_road_graph(scenic)
            print(f"  {scenic.name}: 生成模拟道路图 {created_nodes} 个节点 / {created_edges} 条边")

        total_nodes += created_nodes
        total_edges += created_edges

    db.session.commit()
    print(f"  共创建了 {total_nodes} 个节点和 {total_edges} 条边")


def _collect_target_scenics(scenics, manifest, env_targets):
    """收集需要生成道路图的景区，默认覆盖全部景区，也包含显式配置的景区"""
    scenic_by_name = {s.name: s for s in scenics}
    ordered = list(scenics)
    seen_ids = {scenic.id for scenic in ordered}

    for scenic_name in list(manifest.keys()) + list(env_targets):
        scenic = scenic_by_name.get(scenic_name)
        if scenic and scenic.id not in seen_ids:
            ordered.append(scenic)
            seen_ids.add(scenic.id)

    return ordered


def _load_real_map_manifest():
    """加载真实地图清单，可选"""
    if not os.path.exists(REAL_MAP_MANIFEST):
        return {}

    with open(REAL_MAP_MANIFEST, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError('real_map_data/manifest.json 必须是对象字典')
    return data


def _parse_env_target_names():
    """从环境变量中读取需要拉取真实地图的景区名称"""
    raw = os.environ.get('REAL_MAP_SCENICS', '').strip()
    if not raw:
        return set()
    return {item.strip() for item in raw.split(',') if item.strip()}


def _create_real_road_graph(scenic, source_config):
    """根据配置导入真实道路图"""
    source_type = source_config.get('source', '').strip().lower()
    if source_type == 'geojson':
        geojson_path = source_config.get('file', '').strip()
        if not geojson_path:
            raise ValueError('geojson 来源缺少 file 字段')
        if not os.path.isabs(geojson_path):
            geojson_path = os.path.join(REAL_MAP_DIR, geojson_path)
        return _create_graph_from_geojson_file(scenic, geojson_path)

    radius = int(source_config.get('radius', DEFAULT_FETCH_RADIUS))
    return _create_graph_from_overpass(scenic, radius=radius)


def _create_graph_from_geojson_file(scenic, geojson_path):
    """从本地 GeoJSON 文件构建道路图"""
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f'未找到 GeoJSON 文件: {geojson_path}')

    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)

    ways = _extract_geojson_ways(geojson)
    return _persist_way_graph(scenic, ways)


def _create_graph_from_overpass(scenic, radius=900):
    """从 Overpass API 拉取景区周边步行道路"""
    query = f"""
    [out:json][timeout:25];
    (
      way(around:{radius},{scenic.latitude},{scenic.longitude})["highway"];
    );
    (._;>;);
    out body;
    """
    params = urllib.parse.urlencode({'data': query})
    url = f'{OVERPASS_URL}?{params}'

    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Overpass 请求失败: {exc}') from exc

    ways = _extract_overpass_ways(payload, scenic)
    return _persist_way_graph(scenic, ways)


def _extract_overpass_ways(payload, scenic):
    """将 Overpass 响应转换为标准化 way 列表"""
    elements = payload.get('elements', [])
    node_lookup = {}
    for element in elements:
        if element.get('type') == 'node':
            node_lookup[element['id']] = {
                'lat': element['lat'],
                'lng': element['lon'],
                'name': element.get('tags', {}).get('name', ''),
            }

    ways = []
    for element in elements:
        if element.get('type') != 'way':
            continue
        tags = element.get('tags', {})
        highway = tags.get('highway')
        if highway not in ALLOWED_HIGHWAYS:
            continue

        coords = []
        for node_id in element.get('nodes', []):
            node = node_lookup.get(node_id)
            if not node:
                continue
            coords.append({
                'lat': node['lat'],
                'lng': node['lng'],
                'node_name': node.get('name', ''),
            })

        if len(coords) < 2:
            continue

        ways.append({
            'id': element['id'],
            'name': tags.get('name') or tags.get('ref') or f'{scenic.name}道路{len(ways) + 1}',
            'highway': highway,
            'oneway': str(tags.get('oneway', 'no')).lower() in {'yes', 'true', '1'},
            'coords': coords,
            'surface': tags.get('surface', ''),
        })

    return ways


def _extract_geojson_ways(geojson):
    """从 GeoJSON 中提取线状道路要素"""
    features = geojson.get('features', [])
    ways = []

    for index, feature in enumerate(features, start=1):
        geometry = feature.get('geometry') or {}
        properties = feature.get('properties') or {}
        geom_type = geometry.get('type')
        coordinates = geometry.get('coordinates') or []
        if geom_type == 'LineString':
            coordinates = [coordinates]
        elif geom_type != 'MultiLineString':
            continue

        for segment_index, segment in enumerate(coordinates, start=1):
            if len(segment) < 2:
                continue
            coords = []
            for lng, lat, *rest in segment:
                coords.append({'lat': lat, 'lng': lng, 'node_name': ''})

            highway = properties.get('highway') or properties.get('road_type') or 'path'
            ways.append({
                'id': f'geojson-{index}-{segment_index}',
                'name': properties.get('name') or f'GeoJSON道路{index}-{segment_index}',
                'highway': str(highway),
                'oneway': bool(properties.get('oneway', False)),
                'coords': coords,
                'surface': properties.get('surface', ''),
            })

    return ways


def _persist_way_graph(scenic, ways):
    """持久化标准化道路数据到数据库"""
    if not ways:
        raise ValueError('未解析到可用道路数据')

    coordinate_nodes = {}
    graph_nodes = []
    all_points = []
    edge_specs = []

    for way in ways:
        for point in way['coords']:
            all_points.append((point['lat'], point['lng']))

    projected = _project_coordinates(all_points)
    projected_index = 0
    for way in ways:
        node_refs_in_way = []
        for point in way['coords']:
            key = _coordinate_key(point['lat'], point['lng'])
            if key not in coordinate_nodes:
                x, y = projected[projected_index]
                projected_index += 1
                node = GraphNode(
                    scenic_id=scenic.id,
                    name='',
                    node_type='intersection',
                    latitude=point['lat'],
                    longitude=point['lng'],
                    x=x,
                    y=y,
                )
                db.session.add(node)
                coordinate_nodes[key] = {
                    'db_node': node,
                    'source_name': point.get('node_name', ''),
                    'ways': set(),
                }
                graph_nodes.append(node)
            node_data = coordinate_nodes[key]
            node_data['ways'].add(way['name'])
            node_refs_in_way.append(node_data['db_node'])

        for idx in range(len(node_refs_in_way) - 1):
            from_node = node_refs_in_way[idx]
            to_node = node_refs_in_way[idx + 1]
            distance = _haversine_meters(
                from_node.latitude, from_node.longitude,
                to_node.latitude, to_node.longitude,
            )
            if distance < 1:
                continue

            edge_specs.append({
                'from_node': from_node,
                'to_node': to_node,
                'distance': round(distance, 1),
                'road_name': way['name'],
                'bidirectional': not way['oneway'],
                'road_type': _map_highway_to_road_type(way['highway']),
                'transport_allowed': _map_highway_to_transport(way['highway'], scenic.type),
                'ideal_speed': _ideal_speed_for_highway(way['highway']),
                'congestion': _default_congestion_for_highway(way['highway']),
            })

    db.session.flush()
    node_degree = {node.id: 0 for node in graph_nodes}
    graph_edges = []

    for spec in edge_specs:
        edge = GraphEdge(
            scenic_id=scenic.id,
            from_node_id=spec['from_node'].id,
            to_node_id=spec['to_node'].id,
            distance=spec['distance'],
            road_name=spec['road_name'],
            bidirectional=spec['bidirectional'],
            congestion=spec['congestion'],
            road_type=spec['road_type'],
            transport_allowed=spec['transport_allowed'],
            ideal_speed=spec['ideal_speed'],
        )
        db.session.add(edge)
        graph_edges.append(edge)
        node_degree[spec['from_node'].id] = node_degree.get(spec['from_node'].id, 0) + 1
        node_degree[spec['to_node'].id] = node_degree.get(spec['to_node'].id, 0) + 1

    db.session.flush()

    for index, node in enumerate(graph_nodes, start=1):
        key = _coordinate_key(node.latitude, node.longitude)
        node_data = coordinate_nodes[key]
        if node_data['source_name']:
            node.name = node_data['source_name']
        elif len(node_data['ways']) >= 2:
            joined = '/'.join(list(sorted(node_data['ways']))[:2])
            node.name = f'{joined}交汇点'
        elif node_degree.get(node.id, 0) <= 1:
            node.name = f'{scenic.name}入口{index}'
            node.node_type = 'gate'
        else:
            node.name = f'{scenic.name}节点{index}'

    if not graph_nodes or not graph_edges:
        raise ValueError('真实地图数据不足以形成可用图结构')

    return len(graph_nodes), len(graph_edges)


def _create_simulated_road_graph(scenic):
    """创建模拟道路图，作为真实地图失败时的兜底方案"""
    road_types = ['main', 'branch', 'path']
    node_names_scenic = [
        '正门', '东门', '南门', '西门', '北门', '广场', '停车场', '游客中心',
        '售票处', '湖边', '桥头', '山脚', '山腰', '山顶', '花园', '竹林',
        '古树', '喷泉', '亭子', '商业街入口', '美食广场', '纪念品商店',
        '观景台', '码头', '索道站',
    ]
    node_names_campus = [
        '正门', '东门', '南门', '西门', '教学楼A', '教学楼B', '教学楼C',
        '图书馆', '实验楼', '行政楼', '学生食堂', '第二食堂', '第三食堂',
        '体育馆', '操场', '游泳馆', '宿舍区A', '宿舍区B', '医务室',
        '超市', '快递站', '银行ATM', '校史馆', '湖边', '花园',
    ]

    num_nodes = random.randint(15, 25)
    names = node_names_campus if scenic.type == 'campus' else node_names_scenic
    nodes = []
    edge_count = 0

    for i in range(min(num_nodes, len(names))):
        node = GraphNode(
            scenic_id=scenic.id,
            name=names[i],
            node_type='intersection',
            latitude=scenic.latitude + random.uniform(-0.008, 0.008),
            longitude=scenic.longitude + random.uniform(-0.008, 0.008),
            x=random.uniform(50, 950),
            y=random.uniform(50, 650),
        )
        db.session.add(node)
        nodes.append(node)

    db.session.flush()

    for i in range(1, len(nodes)):
        parent = random.randint(0, i - 1)
        distance = random.uniform(50, 500)
        congestion = random.uniform(0.0, 0.8)
        road_type = random.choice(road_types)
        transport = random.choice(['all', 'all', 'bike']) if scenic.type == 'campus' else random.choice(['all', 'all', 'cart'])
        speed = {'main': 5.0, 'branch': 4.0, 'path': 3.0}.get(road_type, 5.0)

        db.session.add(GraphEdge(
            scenic_id=scenic.id,
            from_node_id=nodes[parent].id,
            to_node_id=nodes[i].id,
            distance=round(distance, 1),
            road_name=f'{nodes[parent].name}-{nodes[i].name}路',
            bidirectional=True,
            congestion=round(congestion, 2),
            road_type=road_type,
            transport_allowed=transport,
            ideal_speed=speed,
        ))
        edge_count += 1

    extra = random.randint(8, 18)
    for _ in range(extra):
        a, b = random.sample(range(len(nodes)), 2)
        db.session.add(GraphEdge(
            scenic_id=scenic.id,
            from_node_id=nodes[a].id,
            to_node_id=nodes[b].id,
            distance=round(random.uniform(30, 400), 1),
            road_name=f'{nodes[a].name}-{nodes[b].name}',
            bidirectional=True,
            congestion=round(random.uniform(0.0, 0.7), 2),
            road_type=random.choice(road_types),
            transport_allowed=random.choice(['all', 'all', 'bike', 'cart']),
            ideal_speed=round(random.uniform(3.0, 6.0), 1),
        ))
        edge_count += 1

    return len(nodes), edge_count


def _project_coordinates(points):
    """将经纬度投影到前端 canvas 使用的相对坐标系"""
    lats = [lat for lat, _ in points]
    lngs = [lng for _, lng in points]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    lat_span = max(max_lat - min_lat, 1e-6)
    lng_span = max(max_lng - min_lng, 1e-6)

    projected = []
    for lat, lng in points:
        x = 50 + ((lng - min_lng) / lng_span) * 900
        y = 650 - ((lat - min_lat) / lat_span) * 600
        projected.append((round(x, 2), round(y, 2)))
    return projected


def _coordinate_key(lat, lng):
    """对坐标做有限精度归一，减少重复节点"""
    return round(lat, 6), round(lng, 6)


def _haversine_meters(lat1, lng1, lat2, lng2):
    """计算两点球面距离（米）"""
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _map_highway_to_road_type(highway):
    """OSM highway 到业务 road_type 的映射"""
    if highway in {'primary', 'secondary', 'tertiary'}:
        return 'main'
    if highway in {'residential', 'service', 'living_street', 'unclassified', 'cycleway'}:
        return 'branch'
    return 'path'


def _map_highway_to_transport(highway, scenic_type):
    """根据道路类型推断可用交通方式"""
    if highway in {'steps', 'footway', 'path', 'pedestrian', 'track'}:
        return 'walk_only'
    if scenic_type == 'campus' and highway in {'cycleway', 'residential', 'service', 'living_street'}:
        return 'bike_walk'
    if scenic_type != 'campus' and highway in {'service', 'residential', 'living_street'}:
        return 'cart_only'
    return 'all'


def _ideal_speed_for_highway(highway):
    """根据道路类型给出基础速度"""
    if highway in {'primary', 'secondary', 'tertiary'}:
        return 5.5
    if highway in {'cycleway', 'residential', 'service', 'living_street'}:
        return 4.5
    if highway == 'steps':
        return 2.5
    return 3.5


def _default_congestion_for_highway(highway):
    """给真实道路默认拥挤度，避免所有道路时间成本相同"""
    if highway in {'primary', 'secondary'}:
        return 0.35
    if highway in {'pedestrian', 'footway'}:
        return 0.2
    if highway == 'steps':
        return 0.45
    return 0.15
