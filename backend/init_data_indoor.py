"""室内导航数据初始化"""
import random
from app import db
from app.models.building import IndoorNode, IndoorEdge


def create_indoor_navigation(buildings):
    """为有多层的建筑创建室内导航数据"""
    total_nodes = 0
    total_edges = 0

    for building in buildings:
        if building.floors <= 1:
            continue

        nodes_by_floor = {}

        for floor in range(1, building.floors + 1):
            floor_nodes = []

            # 每层创建基本节点
            entrance = IndoorNode(
                building_id=building.id,
                name=f"{floor}层入口" if floor == 1 else f"{floor}层走廊",
                node_type='entrance' if floor == 1 else 'corridor',
                floor=floor, x=50, y=50,
            )
            db.session.add(entrance)
            floor_nodes.append(entrance)

            # 电梯节点
            if building.has_elevator:
                elevator = IndoorNode(
                    building_id=building.id,
                    name=f"{floor}层电梯",
                    node_type='elevator',
                    floor=floor, x=100, y=50,
                )
                db.session.add(elevator)
                floor_nodes.append(elevator)

            # 楼梯节点
            stair = IndoorNode(
                building_id=building.id,
                name=f"{floor}层楼梯",
                node_type='stair',
                floor=floor, x=150, y=50,
            )
            db.session.add(stair)
            floor_nodes.append(stair)

            # 房间节点 2-4个
            num_rooms = random.randint(2, 4)
            for r in range(num_rooms):
                room = IndoorNode(
                    building_id=building.id,
                    name=f"{floor}{str(r+1).zfill(2)}室",
                    node_type='room',
                    floor=floor,
                    x=50 + r * 80, y=150,
                )
                db.session.add(room)
                floor_nodes.append(room)

            nodes_by_floor[floor] = floor_nodes
            total_nodes += len(floor_nodes)

        db.session.flush()

        # 创建同层内的边
        for floor, nodes in nodes_by_floor.items():
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    dist = random.uniform(5, 30)
                    edge = IndoorEdge(
                        building_id=building.id,
                        from_node_id=nodes[i].id,
                        to_node_id=nodes[j].id,
                        distance=round(dist, 1),
                        bidirectional=True,
                        edge_type='corridor',
                    )
                    db.session.add(edge)
                    total_edges += 1

        # 创建跨层的边（电梯和楼梯）
        for floor in range(1, building.floors):
            if floor + 1 not in nodes_by_floor:
                continue
            curr_nodes = nodes_by_floor[floor]
            next_nodes = nodes_by_floor[floor + 1]

            # 楼梯连接
            curr_stair = next((n for n in curr_nodes if n.node_type == 'stair'), None)
            next_stair = next((n for n in next_nodes if n.node_type == 'stair'), None)
            if curr_stair and next_stair:
                edge = IndoorEdge(
                    building_id=building.id,
                    from_node_id=curr_stair.id,
                    to_node_id=next_stair.id,
                    distance=10.0, bidirectional=True, edge_type='stair',
                )
                db.session.add(edge)
                total_edges += 1

            # 电梯连接
            if building.has_elevator:
                curr_elev = next((n for n in curr_nodes if n.node_type == 'elevator'), None)
                next_elev = next((n for n in next_nodes if n.node_type == 'elevator'), None)
                if curr_elev and next_elev:
                    edge = IndoorEdge(
                        building_id=building.id,
                        from_node_id=curr_elev.id,
                        to_node_id=next_elev.id,
                        distance=3.0, bidirectional=True, edge_type='elevator',
                    )
                    db.session.add(edge)
                    total_edges += 1

    db.session.commit()
    print(f"  创建了 {total_nodes} 个室内节点和 {total_edges} 条室内边")
