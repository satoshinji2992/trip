"""建筑物数据初始化 - 至少20个"""
import random
from app import db
from app.models.building import Building


def create_buildings(scenics):
    """为景区/校园创建建筑物"""
    buildings = []

    # 故宫建筑
    gugong = scenics[0]
    for name, btype, floors, elevator, desc in [
        ("太和殿", "attraction", 1, False, "故宫最大殿宇，举行大典之地"),
        ("中和殿", "attraction", 1, False, "位于太和殿和保和殿之间"),
        ("保和殿", "attraction", 1, False, "清代除夕赐宴场所"),
        ("乾清宫", "attraction", 1, False, "明清皇帝寝宫"),
        ("故宫博物院展厅", "museum", 2, True, "主要展览场所"),
    ]:
        b = Building(scenic_id=gugong.id, name=name, type=btype, description=desc,
                     floors=floors, has_elevator=elevator,
                     latitude=gugong.latitude + random.uniform(-0.003, 0.003),
                     longitude=gugong.longitude + random.uniform(-0.003, 0.003))
        db.session.add(b)
        buildings.append(b)

    # 北京大学建筑
    pku = next((s for s in scenics if s.name == "北京大学"), None)
    if pku:
        for name, btype, floors, elevator in [
            ("百周年纪念讲堂", "attraction", 3, True),
            ("北大图书馆", "library", 5, True),
            ("理科教学楼", "teaching", 6, True),
            ("文科教学楼", "teaching", 4, True),
            ("行政办公楼", "office", 5, True),
            ("学生宿舍1号楼", "dormitory", 6, False),
            ("学生宿舍2号楼", "dormitory", 6, False),
            ("赛克勒考古博物馆", "museum", 3, True),
        ]:
            b = Building(scenic_id=pku.id, name=name, type=btype,
                         description=f"北京大学{name}", floors=floors, has_elevator=elevator,
                         latitude=pku.latitude + random.uniform(-0.005, 0.005),
                         longitude=pku.longitude + random.uniform(-0.005, 0.005))
            db.session.add(b)
            buildings.append(b)

    # 清华大学建筑
    thu = next((s for s in scenics if s.name == "清华大学"), None)
    if thu:
        for name, btype, floors, elevator in [
            ("主楼", "teaching", 8, True),
            ("清华图书馆", "library", 4, True),
            ("大礼堂", "attraction", 2, False),
            ("工字厅", "office", 2, False),
            ("紫荆学生公寓", "dormitory", 7, True),
            ("美术学院", "teaching", 4, True),
            ("清华科技园", "office", 10, True),
        ]:
            b = Building(scenic_id=thu.id, name=name, type=btype,
                         description=f"清华大学{name}", floors=floors, has_elevator=elevator,
                         latitude=thu.latitude + random.uniform(-0.005, 0.005),
                         longitude=thu.longitude + random.uniform(-0.005, 0.005))
            db.session.add(b)
            buildings.append(b)

    # 西湖风景区建筑
    xihu = next((s for s in scenics if s.name == "西湖风景区"), None)
    if xihu:
        for name, btype, floors, elevator in [
            ("雷峰塔", "attraction", 5, True),
            ("岳王庙", "attraction", 1, False),
            ("浙江省博物馆", "museum", 3, True),
        ]:
            b = Building(scenic_id=xihu.id, name=name, type=btype,
                         description=f"西湖{name}", floors=floors, has_elevator=elevator,
                         latitude=xihu.latitude + random.uniform(-0.005, 0.005),
                         longitude=xihu.longitude + random.uniform(-0.005, 0.005))
            db.session.add(b)
            buildings.append(b)

    db.session.commit()
    print(f"  创建了 {len(buildings)} 个建筑物")
    return buildings
