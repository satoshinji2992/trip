"""Flask应用工厂"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='default'):
    """创建Flask应用实例"""
    app = Flask(__name__)

    from config import config_map
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # 确保上传目录存在
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('WHOOSH_INDEX_DIR', 'whoosh_index'), exist_ok=True)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # 初始化扩展
    db.init_app(app)
    CORS(app, supports_credentials=True)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.scenic import scenic_bp
    from app.routes.route_plan import route_bp
    from app.routes.facility import facility_bp
    from app.routes.diary import diary_bp
    from app.routes.food import food_bp
    from app.routes.navigation import nav_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scenic_bp, url_prefix='/api/scenic')
    app.register_blueprint(route_bp, url_prefix='/api/route')
    app.register_blueprint(facility_bp, url_prefix='/api/facility')
    app.register_blueprint(diary_bp, url_prefix='/api/diary')
    app.register_blueprint(food_bp, url_prefix='/api/food')
    app.register_blueprint(nav_bp, url_prefix='/api/navigation')

    # 创建数据库表
    with app.app_context():
        from app.models import user, scenic, graph, facility, diary, food, building
        db.create_all()

    return app
