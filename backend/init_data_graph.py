"""道路图数据初始化 - 边数至少200条"""
import random
from app import db
from app.models.graph import GraphNode, GraphEdge


def create_road_graphs(scenics):
    """为景区和校园创建道路图"""
    total_nodes = 0
    total_edges = 0
    target_scenics = scenics[:10]

    road_types = ['main', 'branch', 'path']

    node_names_scenic = [
        "正门", "东门", "南门", "西门", "北门", "广场", "停车场", "游客中心",
        "售票处", "湖边", "桥头", "山脚", "山腰", "山顶", "花园", "竹林",
        "古树", "喷泉", "亭子", "商业街入口", "美食广场", "纪念品商店",
        "观景台", "码头", "索道站",
    ]
    node_names_campus = [
        "正门", "东门", "南门", "西门", "教学楼A", "教学楼B", "教学楼C",
        "图书馆", "实验楼", "行政楼", "学生食堂", "第二食堂", "第三食堂",
        "体育馆", "操场", "游泳馆", "宿舍区A", "宿舍区B", "医务室",
        "超市", "快递站", "银行ATM", "校史馆", "湖边", "花园",
    ]

    for scenic in target_scenics:
        num_nodes = random.randint(15, 25)
        names = node_names_campus if scenic.type == 'campus' else node_names_scenic
        nodes = []

        for i in range(min(num_nodes, len(names))):
            node = GraphNode(
                scenic_id=scenic.id, name=names[i], node_type='intersection',
                latitude=scenic.latitude + random.uniform(-0.008, 0.008),
                longitude=scenic.longitude + random.uniform(-0.008, 0.008),
                x=random.uniform(50, 950), y=random.uniform(50, 650),
            )
            db.session.add(node)
            nodes.append(node)

        db.session.flush()

        # 生成树保证连通
        for i in range(1, len(nodes)):
            parent = random.randint(0, i - 1)
            distance = random.uniform(50, 500)
            congestion = random.uniform(0.0, 0.8)
            rt = random.choice(road_types)
            transport = 'all'
            if scenic.type == 'campus':
                transport = random.choice(['all', 'all', 'bike'])
            else:
                transport = random.choice(['all', 'all', 'cart'])
            speed = {'main': 5.0, 'branch': 4.0, 'path': 3.0}.get(rt, 5.0)

            edge = GraphEdge(
                scenic_id=scenic.id, from_node_id=nodes[parent].id, to_node_id=nodes[i].id,
                distance=round(distance, 1),
                road_name=f"{nodes[parent].name}-{nodes[i].name}路",
                bidirectional=True, congestion=round(congestion, 2),
                road_type=rt, transport_allowed=transport, ideal_speed=speed,
            )
            db.session.add(edge)
            total_edges += 1

        # 额外边增加连通性
        extra = random.randint(8, 18)
        for _ in range(extra):
            a, b = random.sample(range(len(nodes)), 2)
            edge = GraphEdge(
                scenic_id=scenic.id, from_node_id=nodes[a].id, to_node_id=nodes[b].id,
                distance=round(random.uniform(30, 400), 1),
                road_name=f"{nodes[a].name}-{nodes[b].name}",
                bidirectional=True, congestion=round(random.uniform(0.0, 0.7), 2),
                road_type=random.choice(road_types),
                transport_allowed=random.choice(['all', 'all', 'bike', 'cart']),
                ideal_speed=round(random.uniform(3.0, 6.0), 1),
            )
            db.session.add(edge)
            total_edges += 1

        total_nodes += len(nodes)

    db.session.commit()
    print(f"  创建了 {total_nodes} 个节点和 {total_edges} 条边")
