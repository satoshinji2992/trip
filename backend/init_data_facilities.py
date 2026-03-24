"""服务设施数据初始化 - 至少50个"""
import random
from app import db
from app.models.facility import Facility
from app.models.graph import GraphNode


def create_facilities(scenics):
    """为景区/校园创建服务设施"""
    facility_templates = [
        ('shop', '商店'), ('restaurant', '饭店'), ('restroom', '洗手间'),
        ('library', '图书馆'), ('canteen', '食堂'), ('supermarket', '超市'),
        ('cafe', '咖啡馆'), ('hospital', '医务室'), ('atm', 'ATM'), ('parking', '停车场'),
    ]
    total = 0
    target_scenics = scenics[:10]

    for scenic in target_scenics:
        nodes = GraphNode.query.filter_by(scenic_id=scenic.id).all()
        node_ids = [n.id for n in nodes] if nodes else []
        num = random.randint(5, 8)
        used = random.sample(facility_templates, min(num, len(facility_templates)))

        for f_type, f_label in used:
            gn_id = random.choice(node_ids) if node_ids else None
            f = Facility(
                scenic_id=scenic.id,
                name=f"{scenic.name}{f_label}",
                type=f_type, category=f_label,
                description=f"{scenic.name}内的{f_label}服务设施",
                latitude=scenic.latitude + random.uniform(-0.005, 0.005),
                longitude=scenic.longitude + random.uniform(-0.005, 0.005),
                graph_node_id=gn_id,
                open_time="08:00-22:00",
                rating=round(random.uniform(3.5, 5.0), 1),
            )
            db.session.add(f)
            total += 1

    db.session.commit()
    print(f"  创建了 {total} 个服务设施")
