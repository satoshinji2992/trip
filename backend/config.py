"""Flask应用配置"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trip-system-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "trip.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB上传限制
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    WHOOSH_INDEX_DIR = os.path.join(BASE_DIR, 'whoosh_index')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
