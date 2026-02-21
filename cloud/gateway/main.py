"""
Blockly小车云端网关服务

功能：
1. 管理车载服务连接池
2. 路由前端消息到对应车载
3. 心跳检测和连接管理
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict

from aiohttp import web
import socketio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建SocketIO服务
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    cors_allowed_origins='*',
    logger=logger,
    engineio_logger=False
)


class VehicleConnectionPool:
    """车载服务连接池"""

    def __init__(self):
        # vehicle_id -> sid (WebSocket会话ID)
        self.vehicle_connections: Dict[str, str] = {}
        # vehicle_id -> 最后心跳时间
        self.last_heartbeat: Dict[str, float] = {}
        # sid -> vehicle_id (反向映射)
        self.sid_to_vehicle: Dict[str, str] = {}
        self._heartbeat_task = None

    def start_heartbeat_monitor(self):
        """启动心跳检测任务"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

    async def add_connection(self, vehicle_id: str, sid: str):
        """添加车载连接"""
        self.vehicle_connections[vehicle_id] = sid
        self.sid_to_vehicle[sid] = vehicle_id
        self.last_heartbeat[vehicle_id] = time.time()

        logger.info(f"车载服务 {vehicle_id} 已连接 (sid: {sid})")

        # 通知所有客户端有新车辆上线
        await self._broadcast_vehicle_list()

    async def remove_connection(self, sid: str):
        """移除连接"""
        if sid in self.sid_to_vehicle:
            vehicle_id = self.sid_to_vehicle[sid]
            del self.vehicle_connections[vehicle_id]
            del self.last_heartbeat[vehicle_id]
            del self.sid_to_vehicle[sid]

            logger.info(f"车载服务 {vehicle_id} 已断开")

            # 广播更新后的车辆列表
            await self._broadcast_vehicle_list()

    async def update_heartbeat(self, vehicle_id: str):
        """更新心跳时间"""
        if vehicle_id in self.last_heartbeat:
            self.last_heartbeat[vehicle_id] = time.time()

    async def route_to_vehicle(self, vehicle_id: str, message: dict) -> bool:
        """路由消息到指定车辆"""
        if vehicle_id not in self.vehicle_connections:
            logger.warning(f"车辆 {vehicle_id} 未连接")
            return False

        sid = self.vehicle_connections[vehicle_id]
        await sio.emit('message', message, room=sid)
        return True

    async def get_vehicle_list(self) -> list:
        """获取在线车辆列表"""
        return [
            {
                'vehicle_id': vid,
                'name': f'小车{vid.split("-")[1]}',
                'online': True
            }
            for vid in self.vehicle_connections.keys()
        ]

    async def _heartbeat_monitor(self):
        """心跳监控任务"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                current_time = time.time()
                timeout_vehicles = []

                # 检查超时车辆（60秒无心跳）
                for vehicle_id, last_time in self.last_heartbeat.items():
                    if current_time - last_time > 60:
                        timeout_vehicles.append(vehicle_id)

                # 清理超时连接
                for vehicle_id in timeout_vehicles:
                    sid = self.vehicle_connections.get(vehicle_id)
                    if sid:
                        await sio.disconnect(sid, reason='heartbeat timeout')
                        logger.warning(f"车辆 {vehicle_id} 心跳超时，已断开")

            except Exception as e:
                logger.error(f"心跳监控错误: {e}")

    async def _broadcast_vehicle_list(self):
        """广播车辆列表到所有客户端"""
        vehicle_list = await self.get_vehicle_list()
        await sio.emit('vehicle_list', {'vehicles': vehicle_list})


# 全局连接池实例
pool = VehicleConnectionPool()


# ===== SocketIO事件处理 =====

@sio.on('connect')
async def handle_connect(sid, environ):
    """处理WebSocket连接"""
    logger.info(f"客户端连接: {sid}")

    # 检查是否是车载服务连接
    vehicle_id = environ.get('HTTP_X_VEHICLE_ID')
    if vehicle_id:
        # 车载服务连接
        await pool.add_connection(vehicle_id, sid)
    else:
        # 前端客户端连接
        # 发送当前车辆列表
        vehicle_list = await pool.get_vehicle_list()
        await sio.emit('vehicle_list', {'vehicles': vehicle_list}, room=sid)


@sio.on('disconnect')
async def handle_disconnect(sid):
    """处理断开连接"""
    logger.info(f"客户端断开: {sid}")
    await pool.remove_connection(sid)


@sio.on('client_register')
async def handle_client_register(sid, data):
    """处理客户端注册"""
    client_id = data.get('client_id')
    logger.info(f"客户端注册: {client_id} (sid: {sid})")


@sio.on('register')
async def handle_vehicle_register(sid, data):
    """处理车载服务注册"""
    vehicle_id = data.get('vehicle_id')
    if vehicle_id:
        # 更新连接池中的vehicle_id
        if sid in pool.sid_to_vehicle:
            old_vehicle_id = pool.sid_to_vehicle[sid]
            del pool.vehicle_connections[old_vehicle_id]
            del pool.last_heartbeat[old_vehicle_id]

        await pool.add_connection(vehicle_id, sid)

        # 返回注册成功
        await sio.emit('registered', {'vehicle_id': vehicle_id}, room=sid)


@sio.on('heartbeat')
async def handle_heartbeat(sid, data):
    """处理心跳"""
    vehicle_id = data.get('vehicle_id')
    if vehicle_id:
        await pool.update_heartbeat(vehicle_id)
        await sio.emit('pong', room=sid)


@sio.on('message')
async def handle_message(sid, data):
    """处理消息路由"""
    msg_type = data.get('type')
    vehicle_id = data.get('vehicle_id')

    if not vehicle_id:
        await sio.emit('error', {
            'code': 'MISSING_VEHICLE_ID',
            'message': '缺少车辆ID'
        }, room=sid)
        return

    # 根据消息类型处理
    if msg_type == 'execute_code':
        # 路由代码执行请求到车载
        success = await pool.route_to_vehicle(vehicle_id, data)
        if not success:
            await sio.emit('error', {
                'code': 'VEHICLE_OFFLINE',
                'message': f'车辆 {vehicle_id} 未连接'
            }, room=sid)

    elif msg_type == 'stop_execution':
        await pool.route_to_vehicle(vehicle_id, data)

    elif msg_type == 'emergency_stop':
        # 紧急停止，高优先级
        await pool.route_to_vehicle(vehicle_id, data)

    elif msg_type == 'get_vehicle_list':
        vehicle_list = await pool.get_vehicle_list()
        await sio.emit('vehicle_list', {'vehicles': vehicle_list}, room=sid)

    elif msg_type == 'get_status':
        await pool.route_to_vehicle(vehicle_id, data)

    else:
        # 其他消息直接转发到车载
        await pool.route_to_vehicle(vehicle_id, data)


# 车载服务发送的消息需要转发回前端
@sio.on('execution_started')
async def handle_execution_started(sid, data):
    """转发执行开始事件"""
    # 广播到所有前端客户端
    await sio.emit('execution_started', data)


@sio.on('execution_finished')
async def handle_execution_finished(sid, data):
    """转发执行完成事件"""
    vehicle_id = pool.sid_to_vehicle.get(sid)
    if vehicle_id:
        data['vehicle_id'] = vehicle_id
    await sio.emit('execution_finished', data)


@sio.on('execution_error')
async def handle_execution_error(sid, data):
    """转发执行错误事件"""
    vehicle_id = pool.sid_to_vehicle.get(sid)
    if vehicle_id:
        data['vehicle_id'] = vehicle_id
    await sio.emit('execution_error', data)


@sio.on('sensor_update')
async def handle_sensor_update(sid, data):
    """转发传感器更新"""
    vehicle_id = pool.sid_to_vehicle.get(sid)
    if vehicle_id:
        await sio.emit('sensor_update', {
            'vehicle_id': vehicle_id,
            'sensors': data.get('sensors', {})
        })


@sio.on('status_update')
async def handle_status_update(sid, data):
    """转发状态更新"""
    vehicle_id = pool.sid_to_vehicle.get(sid)
    if vehicle_id:
        await sio.emit('vehicle_status', {
            'vehicle_id': vehicle_id,
            'online': True,
            'busy': data.get('busy', False)
        })


# ===== HTTP API =====

async def health_check(request):
    """健康检查"""
    return web.json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'vehicles_online': len(pool.vehicle_connections)
    })


async def get_vehicles(request):
    """获取在线车辆列表"""
    vehicle_list = await pool.get_vehicle_list()
    return web.json_response({
        'success': True,
        'data': {
            'vehicles': vehicle_list
        }
    })


# ===== 主程序 =====

async def on_startup(app):
    """应用启动时的处理"""
    pool.start_heartbeat_monitor()
    logger.info("云端网关服务已启动")


def create_app():
    """创建aiohttp应用"""
    app = web.Application()

    # 设置启动处理
    app.on_startup.append(on_startup)

    # 挂载SocketIO
    sio.attach(app)

    # 注册HTTP路由
    app.router.add_get('/health', health_check)
    app.router.add_get('/api/vehicles', get_vehicles)

    return app


if __name__ == '__main__':
    app = create_app()

    logger.info("启动Blockly云端网关服务...")
    # 使用aiohttp直接运行
    import aiohttp
    from aiohttp import web

    web.run_app(
        app,
        host='127.0.0.1',
        port=5001,
        print=logger.info
    )
