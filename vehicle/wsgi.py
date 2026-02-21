"""
车载服务WSGI入口

生产环境使用gunicorn启动:
gunicorn -w 1 -k eventlet -b 0.0.0.0:5000 wsgi:app
"""

import os
import sys
import threading
import time

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio, config

# 创建 Flask 应用
# 注意：对于 Flask-SocketIO，Flask app 本身就是 WSGI 入口
# socketio 会自动包装它
flask_app = create_app()

# gunicorn 入口点是 Flask app（socketio 会自动处理）
app = flask_app

# 启动云端连接管理器
# 需要在 worker 启动后延迟执行，避免阻塞应用加载
def start_connection_manager():
    """启动云端连接管理器"""
    time.sleep(2)  # 等待 gunicorn 完全启动
    from connection.manager import get_connection_manager
    connection_manager = get_connection_manager()
    if connection_manager:
        try:
            connection_manager.connect()
        except Exception as e:
            print(f"连接管理器启动失败: {e}")

# 在后台线程启动连接管理器
# 这会在 gunicorn worker 启动时执行
threading.Thread(target=start_connection_manager, daemon=True).start()

if __name__ == '__main__':
    # 启动服务（开发模式）
    socketio.run(
        app,
        host=config['FLASK_HOST'],
        port=config['FLASK_PORT'],
        debug=config['DEBUG'],
        allow_unsafe_werkzeug=True
    )
