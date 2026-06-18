"""旅游日记数据初始化"""
import json
import random
from app import db
from app.models.diary import Diary, DiaryComment


def create_diaries(users, scenics):
    """为用户创建旅游日记"""
    diary_templates = [
        ("故宫一日游记", "今天参观了故宫博物院，感受了中华文明的博大精深。太和殿的宏伟气势让人震撼，珍宝馆里的文物令人叹为观止。建议大家预留一整天的时间来慢慢参观。"),
        ("西湖漫步", "西湖的美让人陶醉，断桥残雪、苏堤春晓，每一个景点都有不同的韵味。推荐租一辆自行车环湖骑行，别有一番风味。"),
        ("长城攀登记", "今天爬了八达岭长城，虽然很累但是站在长城上俯瞰群山的感觉太棒了！不到长城非好汉，确实名不虚传。"),
        ("成都美食之旅", "成都不愧是美食之都，锦里的小吃、宽窄巷子的茶馆，每一样都让人回味无穷。强烈推荐火锅和串串香！"),
        ("厦门文艺之行", "鼓浪屿的小巷、曾厝垵的涂鸦墙，厦门是一个充满文艺气息的城市。推荐在环岛路骑行，海风吹拂很舒服。"),
        ("张家界奇峰记", "张家界的石柱林立，仿佛进入了阿凡达的世界。天门山的玻璃栈道刺激又震撼，是一次难忘的体验。"),
        ("丽江古城夜色", "丽江古城的夜晚很美，古城里的酒吧和小店各有特色。玉龙雪山的壮丽也让人难以忘怀。"),
        ("黄山日出", "凌晨三点起床去看黄山日出，虽然辛苦但绝对值得。迎客松前拍照留念，云海翻腾的景象美不胜收。"),
        ("大理洱海环游", "租了一辆电动车环洱海，一路上风景如画。苍山洱海之间，感受到了大理独特的慢生活节奏。"),
        ("北大校园漫步", "参观了未名湖和博雅塔，北京大学的校园真的很美。图书馆的建筑也很有特色，学术氛围浓厚。"),
        ("清华园印象", "清华大学的校园很大，骑自行车逛了一圈。荷塘月色、水木清华，每个角落都有故事。"),
        ("武汉樱花季", "武汉大学的樱花真的太美了，粉色花瓣纷飞如雪。东湖绿道骑行也是不错的体验。"),
        ("重庆火锅之旅", "洪崖洞的夜景、磁器口的古镇、还有那无处不在的火锅香味，重庆是一座让人流连忘返的城市。"),
        ("西安历史之旅", "兵马俑的壮观、城墙上的骑行、回民街的美食，西安是一座活着的历史博物馆。"),
        ("苏州园林记", "拙政园的精致、虎丘的斜塔，苏州园林真是园林艺术的巅峰之作。评弹和苏绣也值得一看。"),
        ("桂林山水甲天下", "漓江竹筏漂流是此行的亮点，两岸的喀斯特地貌如诗如画。阳朔的啤酒鱼也很好吃！"),
        ("九寨沟之旅", "九寨沟的水真的是五彩斑斓的，五花海、珍珠滩瀑布，每一处都是大自然的杰作。"),
        ("布达拉宫朝圣", "站在布达拉宫前，感受到了信仰的力量。拉萨的蓝天白云和藏族文化让人心灵宁静。"),
        ("青海湖骑行", "环青海湖骑行是我一直想做的事情，终于实现了！湖水碧蓝如镜，油菜花黄灿灿的，美极了。"),
        ("三亚海边度假", "亚龙湾的沙滩细腻柔软，海水清澈见底。在海边晒太阳、游泳，度过了一个完美的假期。"),
    ]

    total_diaries = 0
    total_comments = 0

    for i, (title, content) in enumerate(diary_templates):
        user = users[i % len(users)]
        scenic = scenics[i % min(len(scenics), 20)]

        diary = Diary(
            user_id=user.id,
            title=title,
            scenic_id=scenic.id,
            destination=scenic.name,
            tags=json.dumps(json.loads(scenic.tags) if scenic.tags else [], ensure_ascii=False),
            is_public=True,
            view_count=random.randint(50, 5000),
            rating_sum=0.0,
            rating_count=0,
        )
        diary.set_content(content)
        db.session.add(diary)
        db.session.flush()
        total_diaries += 1

        # 随机添加评论
        num_comments = random.randint(1, 5)
        commenters = random.sample(users, min(num_comments, len(users)))
        for commenter in commenters:
            if commenter.id == user.id:
                continue
            rating = round(random.uniform(3.0, 5.0), 1)
            comment = DiaryComment(
                diary_id=diary.id,
                user_id=commenter.id,
                content=random.choice([
                    "写得很好，很有参考价值！",
                    "照片拍得真漂亮，种草了！",
                    "攻略很详细，谢谢分享！",
                    "看完好想去，已加入计划！",
                    "文笔很好，身临其境的感觉。",
                    "下次去一定参考你的路线。",
                ]),
                rating=rating,
            )
            diary.rating_sum += rating
            diary.rating_count += 1
            db.session.add(comment)
            total_comments += 1

    db.session.commit()
    print(f"  创建了 {total_diaries} 篇日记和 {total_comments} 条评论")
