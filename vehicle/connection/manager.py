"""
车载服务云端连接管理器

功能：
1. 主动连接到云端网关
2. 心跳保活
3. 断线重连（指数退避）
4. 消息发送和接收
"""

import json
import logging
import threading
import time
import websocket
from typing import Callable, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VehicleConnectionManager:
    """车载服务云端连接管理器"""

    def __init__(self, cloud_url: str, vehicle_id: str):
        self.cloud_url = cloud_url
        self.vehicle_id = vehicle_id
        self.ws: Optional[websocket.WebSocketApp] = None
        self.running = False
        self.reconnect_delay = 1
        self.max_delay = 60

        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {}

        # 连接状态回调
        self.on_connect_cb: Optional[Callable] = None
        self.on_disconnect_cb: Optional[Callable] = None
        self.on_error_cb: Optional[Callable] = None

        # 消息接收线程
        self._receive_thread: Optional[threading.Thread] = None

    def register_handler(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[msg_type] = handler

    def set_callbacks(self,
                      on_connect: Optional[Callable] = None,
                      on_disconnect: Optional[Callable] = None,
                      on_error: Optional[Callable] = None):
        """设置连接状态回调"""
        self.on_connect_cb = on_connect
        self.on_disconnect_cb = on_disconnect
        self.on_error_cb = on_error

    def connect(self) -> threading.Thread:
        """连接到云端（在独立线程中运行）"""
        thread = threading.Thread(target=self._connect_loop, daemon=True)
        thread.start()
        return thread

    def _connect_loop(self):
        """连接循环（带重连）"""
        while True:
            try:
                logger.info(f"正在连接到云端: {self.cloud_url}")

                # 创建WebSocket连接
                self.ws = websocket.WebSocketApp(
                    self.cloud_url,
                    header={"X-Vehicle-ID": self.vehicle_id},
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )

                # 运行WebSocket（阻塞直到断开）
                self.ws.run_forever()

            except Exception as e:
                logger.error(f"连接异常: {e}")

            # 连接断开后处理
            self.running = False

            # 调用断开回调
            if self.on_disconnect_cb:
                self.on_disconnect_cb()

            # 指数退避重连
            logger.info(f"{self.reconnect_delay}秒后重连...")
            time.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_delay)

    def _on_open(self, ws):
        """连接成功回调"""
        logger.info(f"已连接到云端服务 (vehicle_id: {self.vehicle_id})")
        self.running = True
        self.reconnect_delay = 1  # 重置重连延迟

        # 发送注册消息
        self._send_register()

        # 启动心跳线程
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

        # 调用连接回调
        if self.on_connect_cb:
            self.on_connect_cb()

    def _on_message(self, ws, message):
        """接收消息回调"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            logger.debug(f"收到消息: {msg_type}")

            # 调用对应的处理器
            handler = self.message_handlers.get(msg_type)
            if handler:
                handler(data)
            else:
                logger.warning(f"未知消息类型: {msg_type}")

        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    def _on_error(self, ws, error):
        """错误回调"""
        logger.error(f"WebSocket错误: {error}")

        # 调用错误回调
        if self.on_error_cb:
            self.on_error_cb(error)

    def _on_close(self, ws, close_status_code, close_msg):
        """关闭回调"""
        logger.info(f"云端连接已关闭: {close_status_code} - {close_msg}")
        self.running = False

    def _send_register(self):
        """发送注册消息"""
        self.send({
            "type": "register",
            "data": {
                "vehicle_id": self.vehicle_id,
                "name": f"小车{self.vehicle_id.split('-')[1]}",
                "capabilities": {
                    "motion": True,
                    "sensors": ["ultrasonic", "infrared", "battery"],
                    "vision": True
                }
            }
        })

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                break

    def send(self, message: dict):
        """发送消息到云端"""
        if self.ws and self.running:
            message['vehicle_id'] = self.vehicle_id
            message['timestamp'] = int(time.time())

            try:
                self.ws.send(json.dumps(message))
                logger.debug(f"发送消息: {message.get('type')}")
            except Exception as e:
                logger.error(f"发送消息失败: {e}")

    def send_heartbeat(self):
        """发送心跳"""
        self.send({
            "type": "heartbeat",
            "data": {}
        })

    def send_execution_started(self, execution_id: str):
        """发送执行开始事件"""
        self.send({
            "type": "execution_started",
            "data": {
                "execution_id": execution_id
            }
        })

    def send_execution_finished(self, execution_id: str, success: bool = True):
        """发送执行完成事件"""
        self.send({
            "type": "execution_finished",
            "data": {
                "execution_id": execution_id,
                "success": success
            }
        })

    def send_execution_error(self, execution_id: str, error: str):
        """发送执行错误事件"""
        self.send({
            "type": "execution_error",
            "data": {
                "execution_id": execution_id,
                "error": error
            }
        })

    def send_sensor_update(self, sensors: dict):
        """发送传感器更新"""
        self.send({
            "type": "sensor_update",
            "data": {
                "sensors": sensors
            }
        })

    def send_status_update(self, busy: bool = False):
        """发送状态更新"""
        self.send({
            "type": "status_update",
            "data": {
                "busy": busy
            }
        })

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.running


# ===== 全局连接管理器实例 =====
_connection_manager: Optional[VehicleConnectionManager] = None


def get_connection_manager() -> Optional[VehicleConnectionManager]:
    """获取全局连接管理器实例"""
    return _connection_manager


def init_connection_manager(cloud_url: str, vehicle_id: str) -> VehicleConnectionManager:
    """初始化全局连接管理器"""
    global _connection_manager
    _connection_manager = VehicleConnectionManager(cloud_url, vehicle_id)
    return _connection_manager
