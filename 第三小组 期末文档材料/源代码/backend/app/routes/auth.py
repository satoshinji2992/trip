"""用户认证路由"""
import json
from flask import Blueprint, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.response import success, error

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    nickname = data.get('nickname', '').strip()
    interests = data.get('interests', [])

    if not username or not password or not email:
        return error('用户名、密码和邮箱不能为空')

    if len(username) < 3 or len(username) > 64:
        return error('用户名长度需在3-64个字符之间')

    if len(password) < 6:
        return error('密码长度不能少于6个字符')

    if User.query.filter_by(username=username).first():
        return error('用户名已存在')

    if User.query.filter_by(email=email).first():
        return error('邮箱已被注册')

    user = User(
        username=username,
        email=email,
        nickname=nickname or username,
        interests=json.dumps(interests, ensure_ascii=False),
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return success(user.to_dict(), '注册成功')
    except Exception as e:
        db.session.rollback()
        return error(f'注册失败: {str(e)}')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return error('用户名和密码不能为空')

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return error('用户名或密码错误')

    login_user(user)
    return success(user.to_dict(), '登录成功')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    logout_user()
    return success(message='登出成功')


@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取当前用户信息"""
    return success(current_user.to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户信息"""
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    if 'nickname' in data:
        current_user.nickname = data['nickname']
    if 'interests' in data:
        current_user.interests = json.dumps(data['interests'], ensure_ascii=False)
    if 'avatar' in data:
        current_user.avatar = data['avatar']
    if 'email' in data:
        existing = User.query.filter(User.email == data['email'], User.id != current_user.id).first()
        if existing:
            return error('邮箱已被其他用户使用')
        current_user.email = data['email']

    try:
        db.session.commit()
        return success(current_user.to_dict(), '更新成功')
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@auth_bp.route('/check', methods=['GET'])
def check_login():
    """检查登录状态"""
    if current_user.is_authenticated:
        return success(current_user.to_dict(), '已登录')
    return error('未登录', 401)
