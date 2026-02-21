"""
车载服务WSGI入口

生产环境使用gunicorn启动:
gunicorn -w 4 -k eventlet -b 0.0.0.0:5000 wsgi:app
"""

import os
import sys

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio, config

app = create_app()

if __name__ == '__main__':
    # 连接到云端
    from connection.manager import get_connection_manager
    connection_manager = get_connection_manager()
    if connection_manager:
        import threading
        threading.Thread(target=connection_manager.connect, daemon=True).start()

    # 启动服务
    socketio.run(
        app,
        host=config['FLASK_HOST'],
        port=config['FLASK_PORT'],
        debug=config['DEBUG'],
        allow_unsafe_werkzeug=True
    )
