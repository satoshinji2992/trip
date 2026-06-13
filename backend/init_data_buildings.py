"""建筑物数据初始化 - 景区复用故宫建筑，校园复用北大建筑"""
import random
from app import db
from app.models.building import Building


SCENIC_BUILDING_TEMPLATES = [
    ("太和殿", "attraction", 1, False, "故宫最大殿宇，举行大典之地"),
    ("中和殿", "attraction", 1, False, "位于太和殿和保和殿之间"),
    ("保和殿", "attraction", 1, False, "清代除夕赐宴场所"),
    ("乾清宫", "attraction", 1, False, "明清皇帝寝宫"),
    ("故宫博物院展厅", "museum", 2, True, "主要展览场所"),
    ("午门", "attraction", 1, False, "景区主要入口"),
    ("神武门", "attraction", 1, False, "景区北侧出口"),
    ("东华门", "attraction", 1, False, "景区东侧入口"),
    ("西华门", "attraction", 1, False, "景区西侧入口"),
    ("御花园", "attraction", 1, False, "园林游览区"),
    ("钟表馆", "museum", 2, True, "专题展览馆"),
    ("珍宝馆", "museum", 2, True, "专题展览馆"),
    ("文华殿", "attraction", 1, False, "历史建筑"),
    ("武英殿", "attraction", 1, False, "历史建筑"),
    ("慈宁宫", "attraction", 1, False, "历史建筑"),
    ("寿康宫", "attraction", 1, False, "历史建筑"),
    ("养心殿", "attraction", 1, False, "历史建筑"),
    ("奉先殿", "museum", 2, True, "展陈建筑"),
    ("游客服务中心", "other", 2, True, "游客服务建筑"),
    ("文创商店", "other", 1, False, "文创购物建筑"),
]

CAMPUS_BUILDING_TEMPLATES = [
    ("百周年纪念讲堂", "attraction", 3, True, "校园文化活动中心"),
    ("北大图书馆", "library", 5, True, "综合图书馆"),
    ("理科教学楼", "teaching", 6, True, "理科课程教学楼"),
    ("文科教学楼", "teaching", 4, True, "文科课程教学楼"),
    ("行政办公楼", "office", 5, True, "校区行政办公楼"),
    ("学生宿舍1号楼", "dormitory", 6, False, "学生住宿楼"),
    ("学生宿舍2号楼", "dormitory", 6, False, "学生住宿楼"),
    ("赛克勒考古博物馆", "museum", 3, True, "校园博物馆"),
    ("第一教学楼", "teaching", 5, True, "公共教学楼"),
    ("第二教学楼", "teaching", 5, True, "公共教学楼"),
    ("第三教学楼", "teaching", 5, True, "公共教学楼"),
    ("实验中心", "teaching", 6, True, "实验教学楼"),
    ("信息科学楼", "teaching", 8, True, "学院教学楼"),
    ("工程训练中心", "teaching", 4, True, "实践教学楼"),
    ("校医院", "other", 3, True, "校园医疗服务建筑"),
    ("体育馆", "other", 3, True, "体育活动建筑"),
    ("游泳馆", "other", 2, True, "体育活动建筑"),
    ("第一食堂", "other", 3, True, "校园餐饮建筑"),
    ("第二食堂", "other", 3, True, "校园餐饮建筑"),
    ("学生宿舍3号楼", "dormitory", 6, False, "学生住宿楼"),
    ("学生宿舍4号楼", "dormitory", 6, False, "学生住宿楼"),
    ("国际交流中心", "office", 6, True, "校园办公与交流建筑"),
    ("创新创业中心", "office", 7, True, "创新实践办公建筑"),
    ("校史馆", "museum", 2, True, "校园文化展馆"),
]


def create_buildings(scenics):
    """为景区/校园创建建筑物，内部结构按课程要求可复用同一套模板"""
    buildings = []

    for scenic in scenics:
        templates = CAMPUS_BUILDING_TEMPLATES if scenic.type == 'campus' else SCENIC_BUILDING_TEMPLATES
        spread = 0.005 if scenic.type == 'campus' else 0.003
        for name, btype, floors, elevator, desc in templates:
            building = Building(
                scenic_id=scenic.id,
                name=name,
                type=btype,
                description=f"{scenic.name}{desc}",
                floors=floors,
                has_elevator=elevator,
                latitude=scenic.latitude + random.uniform(-spread, spread),
                longitude=scenic.longitude + random.uniform(-spread, spread),
            )
            db.session.add(building)
            buildings.append(building)

    db.session.commit()
    print(f"  创建了 {len(buildings)} 个建筑物")
    return buildings
