"""
车载服务云端连接管理器

功能：
1. 主动连接到云端网关（使用原生WebSocket客户端）
2. 心跳保活
3. 断线重连（自动处理）
4. 消息发送和接收
"""

import json
import logging
import time
import threading
import websocket
from typing import Callable, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VehicleConnectionManager:
    """车载服务云端连接管理器（WebSocket 客户端）"""

    def __init__(self, cloud_url: str, vehicle_id: str):
        # 解析云端 URL
        # 支持格式: wss://lanser.fun/block/ws/gateway 或 https://lanser.fun
        self.cloud_url = cloud_url
        self.vehicle_id = vehicle_id
        self.running = False
        self.ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None

        # 规范化URL为WebSocket连接地址
        # 如果URL包含 /block/ws/gateway，直接使用
        # 否则需要构造完整路径
        if '/block/ws/gateway' in cloud_url or '/ws/gateway' in cloud_url:
            # 已经是完整路径
            self.ws_url = cloud_url.replace('https://', 'wss://').replace('http://', 'ws://')
        elif '/block' in cloud_url:
            # 有 /block 前缀，需要添加 /ws/gateway
            base = cloud_url.split('/block')[0].replace('https://', 'wss://').replace('http://', 'ws://')
            self.ws_url = f"{base}/block/ws/gateway"
        else:
            # 纯域名，添加完整路径
            base = cloud_url.replace('https://', 'wss://').replace('http://', 'ws://')
            self.ws_url = f"{base}/block/ws/gateway"

        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {}

        # 连接状态回调
        self.on_connect_cb: Optional[Callable] = None
        self.on_disconnect_cb: Optional[Callable] = None
        self.on_error_cb: Optional[Callable] = None

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

    def connect(self) -> websocket.WebSocketApp:
        """连接到云端"""
        logger.info(f"正在连接到云端: {self.ws_url}")

        def on_open(ws):
            """连接建立回调"""
            logger.info(f"WebSocket连接已建立 (vehicle_id: {self.vehicle_id})")
            self.running = True

            # 发送注册消息
            self._send_register()

            # 调用连接回调
            if self.on_connect_cb:
                self.on_connect_cb()

        def on_message(ws, message):
            """接收消息回调"""
            try:
                data = json.loads(message)
                msg_type = data.get('type') if isinstance(data, dict) else message
                logger.debug(f"收到消息: {msg_type}")

                # 调用对应的处理器
                handler = self.message_handlers.get(msg_type)
                if handler:
                    handler(data if isinstance(data, dict) else {'type': msg_type})
                else:
                    logger.warning(f"未知消息类型: {msg_type}")

            except json.JSONDecodeError:
                logger.warning(f"收到非JSON消息: {message}")
                # 尝试作为原始类型处理
                handler = self.message_handlers.get(message)
                if handler:
                    handler({'type': message})
            except Exception as e:
                logger.error(f"处理消息失败: {e}")

        def on_error(ws, error):
            """连接错误回调"""
            logger.error(f"WebSocket错误: {error}")
            if self.on_error_cb:
                self.on_error_cb(error)

        def on_close(ws, close_status_code, close_msg):
            """连接关闭回调"""
            logger.info(f"WebSocket连接已关闭: {close_status_code} - {close_msg}")
            self.running = False

            # 调用断开回调
            if self.on_disconnect_cb:
                self.on_disconnect_cb()

        # 创建WebSocket客户端
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header={'X-Vehicle-ID': self.vehicle_id}
        )

        # 在新线程中运行WebSocket（保持连接活跃）
        def run_websocket():
            """运行WebSocket（阻塞）"""
            try:
                # 启用ping/pong保活
                self.ws.run_forever(
                    ping_interval=30,  # 每30秒发送ping
                    ping_timeout=10,   # ping超时10秒
                )
            except Exception as e:
                logger.error(f"WebSocket运行异常: {e}")
                if self.on_error_cb:
                    self.on_error_cb(e)

        self._thread = threading.Thread(target=run_websocket, daemon=True)
        self._thread.start()

        return self.ws

    def _send_register(self):
        """发送注册消息"""
        self.send({
            "type": "register",
            "data": {
                "vehicle_id": self.vehicle_id,
                "name": f"小车{self.vehicle_id.split('-')[1] if '-' in self.vehicle_id else '001'}",
                "capabilities": {
                    "motion": True,
                    "sensors": ["ultrasonic", "infrared", "line", "battery"],
                    "vision": True
                }
            }
        })

    def send(self, message: dict):
        """发送消息到云端"""
        if self.ws and self.running:
            # 添加必要字段
            if 'vehicle_id' not in message:
                message['vehicle_id'] = self.vehicle_id
            if 'timestamp' not in message:
                message['timestamp'] = int(time.time())

            try:
                json_msg = json.dumps(message)
                self.ws.send(json_msg)
                logger.debug(f"发送消息: {message.get('type')}")
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
        else:
            logger.warning('未连接到云端，无法发送消息')

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

    def send_execution_finished(self, execution_id: str, success: bool = True, output=None, error=None):
        """发送执行完成事件"""
        data = {
            "type": "execution_finished",
            "data": {
                "execution_id": execution_id,
                "success": success
            }
        }
        if output is not None:
            data['data']['output'] = output
        if error is not None:
            data['data']['error'] = error
        self.send(data)

    def send_execution_stopped(self, execution_id: str):
        """发送执行停止事件"""
        self.send({
            "type": "execution_stopped",
            "data": {
                "execution_id": execution_id
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

    def send_emergency_stop(self):
        """发送紧急停止事件"""
        self.send({
            "type": "emergency_stop",
            "data": {}
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
        return self.running and self.ws is not None

    def disconnect(self):
        """断开连接"""
        if self.ws:
            self.running = False
            self.ws.close()


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
