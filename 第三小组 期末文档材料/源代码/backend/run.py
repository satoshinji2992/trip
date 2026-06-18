"""Flask应用启动入口"""
import os
import sys

# 确保backend目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
