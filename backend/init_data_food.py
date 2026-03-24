"""餐厅和美食数据初始化"""
import json
import random
from app import db
from app.models.food import Restaurant, Food
from app.models.graph import GraphNode


def create_restaurants_and_foods(scenics):
    """为景区/校园创建餐厅和美食"""
    cuisines = ['chinese', 'western', 'japanese', 'korean', 'fast_food', 'snack', 'cafe']
    cuisine_names = {
        'chinese': '中餐', 'western': '西餐', 'japanese': '日料',
        'korean': '韩餐', 'fast_food': '快餐', 'snack': '小吃', 'cafe': '咖啡甜品',
    }
    restaurant_prefixes = [
        "老王", "金味", "鲜香", "天府", "湘味", "粤式", "川香",
        "江南", "北方", "东北", "云南", "福建", "山西",
    ]
    food_names_map = {
        'chinese': ["红烧肉", "宫保鸡丁", "麻婆豆腐", "清蒸鱼", "糖醋排骨", "回锅肉", "水煮牛肉", "鱼香肉丝"],
        'western': ["牛排", "意面", "披萨", "沙拉", "汉堡", "薯条", "芝士蛋糕"],
        'japanese': ["寿司", "拉面", "天妇罗", "刺身", "烤鳗鱼", "味增汤"],
        'korean': ["石锅拌饭", "炸鸡", "部队锅", "烤肉", "冷面", "泡菜汤"],
        'fast_food': ["炸鸡汉堡", "鸡肉卷", "薯条", "可乐", "冰淇淋"],
        'snack': ["煎饼果子", "烤红薯", "臭豆腐", "糖葫芦", "烤串", "凉皮", "肉夹馍"],
        'cafe': ["美式咖啡", "拿铁", "卡布奇诺", "抹茶蛋糕", "提拉米苏", "奶茶"],
    }

    total_restaurants = 0
    total_foods = 0
    target_scenics = scenics[:10]

    for scenic in target_scenics:
        nodes = GraphNode.query.filter_by(scenic_id=scenic.id).all()
        node_ids = [n.id for n in nodes] if nodes else []
        num_restaurants = random.randint(3, 6)

        for _ in range(num_restaurants):
            cuisine = random.choice(cuisines)
            prefix = random.choice(restaurant_prefixes)
            gn_id = random.choice(node_ids) if node_ids else None

            restaurant = Restaurant(
                scenic_id=scenic.id,
                name=f"{prefix}{cuisine_names[cuisine]}馆",
                cuisine=cuisine,
                description=f"位于{scenic.name}内的{cuisine_names[cuisine]}餐厅，环境优雅，味道正宗。",
                address=f"{scenic.name}内",
                latitude=scenic.latitude + random.uniform(-0.005, 0.005),
                longitude=scenic.longitude + random.uniform(-0.005, 0.005),
                graph_node_id=gn_id,
                avg_price=round(random.uniform(15, 100), 0),
                rating=round(random.uniform(3.5, 5.0), 1),
                rating_count=random.randint(10, 500),
                popularity=random.randint(100, 5000),
                open_time="08:00-22:00",
            )
            db.session.add(restaurant)
            db.session.flush()
            total_restaurants += 1

            # 每个餐厅创建3-6道菜
            food_names = food_names_map.get(cuisine, ["招牌菜", "特色菜", "推荐菜"])
            num_foods = min(random.randint(3, 6), len(food_names))
            selected = random.sample(food_names, num_foods)

            for fname in selected:
                food = Food(
                    restaurant_id=restaurant.id,
                    name=fname, cuisine=cuisine,
                    description=f"{prefix}家的{fname}，选用上等食材精心烹制。",
                    price=round(random.uniform(8, 88), 0),
                    rating=round(random.uniform(3.5, 5.0), 1),
                    popularity=random.randint(10, 1000),
                    tags=json.dumps([cuisine_names[cuisine], "推荐"], ensure_ascii=False),
                )
                db.session.add(food)
                total_foods += 1

    db.session.commit()
    print(f"  创建了 {total_restaurants} 个餐厅和 {total_foods} 道美食")
