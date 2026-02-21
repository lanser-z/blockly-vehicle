import multiprocessing
import os

# 服务器地址
bind = "0.0.0.0:5000"

# Worker 进程数（小车只需单进程处理控制）
workers = 1

# Worker 类型（eventlet 用于 Flask-SocketIO）
worker_class = "eventlet"

# Worker 进程名称
proc_name = "blockly-vehicle"

# 每个 worker 的最大请求数（重启 worker 防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 超时设置
timeout = 120
keepalive = 5

# 日志配置
accesslog = "-"  # 输出到 stdout
errorlog = "-"   # 输出到 stderr
loglevel = "info"

# 进程管理
daemon = False
pidfile = None
umask = 0o007

# 服务器钩子
def on_starting(server):
    """服务器启动时调用"""
    server.log.info("Blockly Vehicle Service starting...")

def on_exit(server):
    """服务器退出时调用"""
    server.log.info("Blockly Vehicle Service shutting down...")
