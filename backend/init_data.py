"""
数据初始化脚本入口
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db


def init_all():
    """初始化所有数据"""
    app = create_app('development')
    with app.app_context():
        print("正在清除旧数据...")
        db.drop_all()
        db.create_all()

        from init_data_users import create_users
        from init_data_scenics import create_scenics
        from init_data_buildings import create_buildings
        from init_data_graph import create_road_graphs
        from init_data_facilities import create_facilities
        from init_data_food import create_restaurants_and_foods
        from init_data_indoor import create_indoor_navigation
        from init_data_diary import create_diaries

        print("正在创建用户...")
        users = create_users()

        print("正在创建景区和校园...")
        scenics = create_scenics()

        print("正在创建建筑物...")
        buildings = create_buildings(scenics)

        print("正在创建道路图...")
        create_road_graphs(scenics)

        print("正在创建服务设施...")
        create_facilities(scenics)

        print("正在创建餐厅和美食...")
        create_restaurants_and_foods(scenics)

        print("正在创建室内导航数据...")
        create_indoor_navigation(buildings)

        print("正在创建旅游日记...")
        create_diaries(users, scenics)

        print("正在重建全文搜索索引...")
        from app.services.search_service import rebuild_diary_index
        index_dir = app.config.get('WHOOSH_INDEX_DIR', 'whoosh_index')
        count = rebuild_diary_index(index_dir)
        print(f"  索引了 {count} 篇日记")

        # 统计
        from app.models.user import User
        from app.models.scenic import Scenic
        from app.models.building import Building, IndoorNode, IndoorEdge
        from app.models.facility import Facility
        from app.models.graph import GraphNode, GraphEdge
        from app.models.food import Restaurant, Food
        from app.models.diary import Diary
        print("\n===== 数据统计 =====")
        print(f"用户数: {User.query.count()}")
        print(f"景区/校园数: {Scenic.query.count()}")
        print(f"建筑物数: {Building.query.count()}")
        print(f"服务设施数: {Facility.query.count()}")
        print(f"道路图节点数: {GraphNode.query.count()}")
        print(f"道路图边数: {GraphEdge.query.count()}")
        print(f"餐厅数: {Restaurant.query.count()}")
        print(f"美食数: {Food.query.count()}")
        print(f"旅游日记数: {Diary.query.count()}")
        print(f"室内节点数: {IndoorNode.query.count()}")
        print(f"室内边数: {IndoorEdge.query.count()}")
        print("===== 初始化完成 =====")


if __name__ == '__main__':
    init_all()
