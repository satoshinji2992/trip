"""Flask应用配置"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _load_env_file(path=os.path.join(BASE_DIR, '.env')):
    """加载本地.env文件，已有系统环境变量优先。"""
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trip-system-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "trip.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB上传限制
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    WHOOSH_INDEX_DIR = os.path.join(BASE_DIR, 'whoosh_index')
    AIGC_BASE_URL = os.environ.get('AIGC_BASE_URL', 'http://10.21.129.82:8000')
    AIGC_ENDPOINT = os.environ.get('AIGC_ENDPOINT', '/generate')
    AIGC_DEFAULT_PROMPT = os.environ.get('AIGC_DEFAULT_PROMPT', '')


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
