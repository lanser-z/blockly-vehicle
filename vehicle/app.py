"""
Blockly小车车载服务主应用

功能：
1. Flask Web服务
2. API路由（代码执行、控制、状态）
3. 集成连接管理器
4. 代码沙箱执行
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'blockly-vehicle-secret')

# 启用CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 导入连接管理器和配置
from connection.manager import init_connection_manager

# 导入硬件抽象层和执行器
import hal
from executor import ProcessManager

# 从配置文件加载配置
def load_config():
    """加载配置"""
    config = {
        'VEHICLE_ID': os.getenv('VEHICLE_ID', 'vehicle-001'),
        'CLOUD_GATEWAY_URL': os.getenv('CLOUD_GATEWAY_URL', 'wss://lanser.fun/block/ws/gateway'),
        'FLASK_HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
        'FLASK_PORT': int(os.getenv('FLASK_PORT', 5000)),
        'DEBUG': os.getenv('FLASK_ENV', 'production') == 'development',
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'MOCK_HARDWARE': os.getenv('MOCK_HARDWARE', 'false').lower() == 'true',
        'TURBOPI_PATH': os.getenv('TURBOPI_PATH', './TurboPi'),
        'EXECUTION_TIMEOUT': int(os.getenv('EXECUTION_TIMEOUT', 30)),
    }
    return config

# 加载配置
config = load_config()

# 配置日志级别
logging.getLogger().setLevel(getattr(logging, config['LOG_LEVEL'], logging.INFO))

# 初始化连接管理器
connection_manager = init_connection_manager(
    cloud_url=config['CLOUD_GATEWAY_URL'],
    vehicle_id=config['VEHICLE_ID']
)

# 初始化进程管理器（带HAL模块）
process_manager = ProcessManager(hal_module=hal)


# ===== 路由 =====

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'vehicle_id': config['VEHICLE_ID'],
        'connected': connection_manager.is_connected(),
        'mock_hardware': config['MOCK_HARDWARE']
    })


@app.route('/api/status')
def get_status():
    """获取状态"""
    proc_status = process_manager.get_status()
    sensor_data = hal.sensor_controller.get_all_sensors()

    return jsonify({
        'success': True,
        'data': {
            'vehicle_id': config['VEHICLE_ID'],
            'connected': connection_manager.is_connected(),
            'busy': proc_status['executing'],
            'process_id': proc_status.get('process_id'),
            'sensors': sensor_data
        }
    })


# ===== SocketIO事件处理 =====

@socketio.on('connect')
def handle_connect():
    """处理SocketIO连接"""
    logger.info('客户端已连接')
    emit('connected', {
        'vehicle_id': config['VEHICLE_ID'],
        'status': process_manager.get_status()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """处理断开连接"""
    logger.info('客户端已断开')


@socketio.on('execute_code')
def handle_execute_code(data):
    """处理代码执行请求"""
    code = data.get('code')
    execution_id = data.get('execution_id')
    timeout = data.get('timeout', config['EXECUTION_TIMEOUT'])

    if not code:
        emit('error', {'code': 'CODE_EMPTY', 'message': '代码为空'})
        return {'success': False, 'error': '代码为空'}

    logger.info(f"执行代码: {execution_id}")

    # 通知开始执行
    connection_manager.send_execution_started(execution_id)
    emit('execution_started', {'execution_id': execution_id})

    # 执行代码
    result = process_manager.start_execution(code, process_id=execution_id, timeout=timeout)

    # 通知执行结果
    if result['success']:
        connection_manager.send_execution_finished(execution_id, success=True, output=result.get('output', []))
        emit('execution_finished', {
            'execution_id': execution_id,
            'success': True,
            'output': result.get('output', [])
        })
    else:
        connection_manager.send_execution_finished(
            execution_id,
            success=False,
            error=result.get('error'),
            output=result.get('output', [])
        )
        emit('execution_finished', {
            'execution_id': execution_id,
            'success': False,
            'error': result.get('error'),
            'output': result.get('output', [])
        })

    return {'success': result['success'], 'execution_id': execution_id}


@socketio.on('stop_execution')
def handle_stop_execution(data):
    """处理停止执行请求"""
    execution_id = data.get('execution_id')
    logger.info(f"停止执行: {execution_id}")

    stopped = process_manager.stop_execution()

    if stopped:
        connection_manager.send_execution_stopped(execution_id or process_manager.current_process_id)
        emit('execution_stopped', {'execution_id': execution_id})
        return {'success': True}
    else:
        return {'success': False, 'error': '没有正在执行的代码'}


@socketio.on('emergency_stop')
def handle_emergency_stop(data):
    """处理紧急停止请求"""
    logger.warning("紧急停止！")

    process_manager.emergency_stop()

    connection_manager.send_emergency_stop()
    emit('emergency_stop', {'vehicle_id': config['VEHICLE_ID']})

    return {'success': True}


# ===== 云端连接事件处理 =====

def handle_cloud_message(data):
    """处理来自云端的消息"""
    msg_type = data.get('type')

    if msg_type == 'execute_code':
        # 代码执行请求
        payload = data.get('data', {})
        execution_id = payload.get('execution_id')
        code = payload.get('code')
        timeout = payload.get('timeout', config['EXECUTION_TIMEOUT'])

        logger.info(f"收到代码执行请求: {execution_id}")

        if code:
            # 通知开始执行
            connection_manager.send_execution_started(execution_id)

            # 执行代码
            result = process_manager.start_execution(code, process_id=execution_id, timeout=timeout)

            # 通知执行结果
            if result['success']:
                connection_manager.send_execution_finished(
                    execution_id,
                    success=True,
                    output=result.get('output', [])
                )
            else:
                connection_manager.send_execution_finished(
                    execution_id,
                    success=False,
                    error=result.get('error'),
                    output=result.get('output', [])
                )
        else:
            connection_manager.send_execution_finished(
                execution_id,
                success=False,
                error='代码为空'
            )

    elif msg_type == 'stop_execution':
        # 停止执行请求
        execution_id = data.get('data', {}).get('execution_id')
        logger.info(f"收到停止执行请求: {execution_id}")

        stopped = process_manager.stop_execution()
        if stopped:
            connection_manager.send_execution_stopped(execution_id)

    elif msg_type == 'emergency_stop':
        # 紧急停止
        logger.warning("收到紧急停止请求")
        process_manager.emergency_stop()
        connection_manager.send_emergency_stop()

    elif msg_type == 'get_status':
        # 状态查询
        proc_status = process_manager.get_status()
        sensor_data = hal.sensor_controller.get_all_sensors()

        connection_manager.send({
            "type": "status_update",
            "data": {
                'vehicle_id': config['VEHICLE_ID'],
                'busy': proc_status['executing'],
                'process_id': proc_status.get('process_id'),
                'sensors': sensor_data
            }
        })

    elif msg_type == 'ping':
        # 心跳检测
        connection_manager.send({
            "type": "pong",
            "data": {}
        })


# ===== 主程序 =====

def create_app():
    """创建应用实例"""
    # 注册消息处理器
    connection_manager.register_handler('execute_code', handle_cloud_message)
    connection_manager.register_handler('stop_execution', handle_cloud_message)
    connection_manager.register_handler('emergency_stop', handle_cloud_message)
    connection_manager.register_handler('get_status', handle_cloud_message)
    connection_manager.register_handler('ping', handle_cloud_message)

    # 设置连接状态回调
    connection_manager.set_callbacks(
        on_connect=lambda: logger.info('已连接到云端'),
        on_disconnect=lambda: logger.warning('与云端断开连接'),
        on_error=lambda e: logger.error(f'连接错误: {e}')
    )

    return app


# ===== 启动函数 =====

def start():
    """启动服务"""
    app = create_app()

    # 连接到云端
    logger.info(f"正在连接到云端: {config['CLOUD_GATEWAY_URL']}")
    connection_manager.connect()

    # 启动Flask服务
    logger.info(f"启动车载服务: {config['FLASK_HOST']}:{config['FLASK_PORT']}")
    socketio.run(
        app,
        host=config['FLASK_HOST'],
        port=config['FLASK_PORT'],
        debug=config['DEBUG'],
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    start()
