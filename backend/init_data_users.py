"""用户数据初始化"""
import json
from app import db
from app.models.user import User


def create_users():
    """创建12个用户"""
    users_data = [
        {"username": "zhangsan", "email": "zhangsan@example.com", "nickname": "张三", "interests": ["自然风光", "历史文化"]},
        {"username": "lisi", "email": "lisi@example.com", "nickname": "李四", "interests": ["美食", "主题乐园"]},
        {"username": "wangwu", "email": "wangwu@example.com", "nickname": "王五", "interests": ["科技", "博物馆"]},
        {"username": "zhaoliu", "email": "zhaoliu@example.com", "nickname": "赵六", "interests": ["自然风光", "摄影"]},
        {"username": "sunqi", "email": "sunqi@example.com", "nickname": "孙七", "interests": ["历史文化", "建筑"]},
        {"username": "zhouba", "email": "zhouba@example.com", "nickname": "周八", "interests": ["美食", "购物"]},
        {"username": "wujiu", "email": "wujiu@example.com", "nickname": "吴九", "interests": ["户外运动", "自然风光"]},
        {"username": "zhengshi", "email": "zhengshi@example.com", "nickname": "郑十", "interests": ["文艺", "咖啡"]},
        {"username": "xiaoming", "email": "xiaoming@example.com", "nickname": "小明", "interests": ["科技", "主题乐园"]},
        {"username": "xiaohong", "email": "xiaohong@example.com", "nickname": "小红", "interests": ["摄影", "美食"]},
        {"username": "admin", "email": "admin@example.com", "nickname": "管理员", "interests": ["自然风光", "历史文化", "美食"]},
        {"username": "tourist", "email": "tourist@example.com", "nickname": "游客", "interests": ["自然风光"]},
    ]
    users = []
    for u_data in users_data:
        user = User(
            username=u_data["username"],
            email=u_data["email"],
            nickname=u_data["nickname"],
            interests=json.dumps(u_data["interests"], ensure_ascii=False),
        )
        user.set_password("123456")
        db.session.add(user)
        users.append(user)
    db.session.commit()
    print(f"  创建了 {len(users)} 个用户")
    return users
