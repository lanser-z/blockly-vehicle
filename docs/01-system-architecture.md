# Blockly少儿编程小车 - 系统总体架构设计

## 文档说明

本文档采用 **4+1视图法** 描述系统架构，涵盖：
- **逻辑视图**: 功能模块设计
- **进程视图**: 运行时进程与通信
- **开发视图**: 项目结构与依赖管理
- **物理视图**: 生产环境部署架构
- **场景视图**: 关键用例场景

---

## 1. 逻辑视图 (Logical View)

### 1.1 系统概述

**设计目标**:
- **低门槛**: 6岁儿童无需阅读代码即可控制机器人
- **高趣味**: 游戏化界面和即时反馈
- **安全可靠**: 硬件保护和参数限位
- **易扩展**: 模块化设计，便于添加新积木
- **云端分离**: 云端托管前端，车载执行硬件控制

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            用户浏览器                                        │
│                      https://lanser.fun/block/                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────────────────────┐
│                        云端服务 (lanser.fun)                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Nginx反向代理                                                         │ │
│  │  - /block/ → 前端静态资源                                              │ │
│  │  - /block/ws/ → WebSocket代理（转发到车载服务）                        │ │
│  │  - /block/api/ → REST API代理                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WebSocket中转服务                                                    │ │
│  │  - 管理车载服务连接池                                                 │ │
│  │  - 消息路由与转发                                                     │ │
│  │  - 连接状态监控                                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ TCP长连接 (WebSocket)
┌─────────────────────────────────────────────────────────────────────────────┐
│                      车载服务 (Raspberry Pi)                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  连接管理器                                                            │ │
│  │  - 主动连接云端服务                                                   │ │
│  │  - 心跳保活                                                           │ │
│  │  - 断线重连                                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Flask车载服务                                                        │ │
│  │  ├─ 代码执行API                                                       │ │
│  │  ├─ 实时控制API                                                       │ │
│  │  ├─ 状态查询API                                                       │ │
│  │  └─ 摄像头流服务                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  代码执行器                                                           │ │
│  │  - 沙箱环境                                                           │ │
│  │  - 进程管理                                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  硬件抽象层 (HAL)                                                     │ │
│  │  ├─ 运动控制器                                                        │ │
│  │  ├─ 传感器控制器                                                      │ │
│  │  └─ 视觉控制器                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  HiwonderSDK                                                          │ │
│  │  - Board.py (电机、舵机、LED)                                         │ │
│  │  - Sonar.py (超声波传感器)                                            │ │
│  │  - FourInfrared.py (巡线传感器)                                       │ │
│  │  - Camera.py (摄像头)                                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        硬件层 (Raspberry Pi 4B)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ 4x电机  │  │ 6x舵机  │  │ 超声波   │  │ 巡线传感器│                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ USB摄像头 (CSI Camera可选)                                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 功能模块划分

#### 1.3.1 云端服务 (Cloud Service)

| 模块 | 职责 | 部署位置 |
|------|------|----------|
| **Nginx反向代理** | HTTPS终止、静态资源托管、WebSocket代理 | lanser.fun |
| **WebSocket中转** | 管理车载连接、消息路由转发 | lanser.fun |
| **前端静态资源** | Blockly界面、积木定义、代码生成器 | lanser.fun |

#### 1.3.2 车载服务 (Vehicle Service)

| 模块 | 职责 | 部署位置 |
|------|------|----------|
| **连接管理器** | 主动连接云端、心跳保活、断线重连 | Raspberry Pi |
| **代码执行器** | 沙箱执行用户代码、进程管理 | Raspberry Pi |
| **硬件抽象层** | 统一的硬件控制接口 | Raspberry Pi |
| **摄像头流服务** | MJPG视频流推送 | Raspberry Pi |

### 1.4 通信架构

```
前端 ←→ 云端服务: HTTPS/WebSocket (浏览器到云端)
云端服务 ←→ 车载服务: WebSocket长连接 (云端到车载)
车载服务 ←→ 硬件: GPIO/I2C/UART (车载服务到硬件)
```

### 1.5 积木块分类设计

| 类别 | 名称 | 颜色(HSV) | 积木示例 | 数量 |
|------|------|-----------|----------|------|
| **运动** | 运动控制 | Hue=230 | 前进/后退/左平移/右平移/旋转/停止 | 11 |
| **传感** | 传感器 | Hue=120 | 超声波距离/巡线状态/电池电量 | 3 |
| **视觉** | 视觉功能 | Hue=270 | 检测颜色/追踪颜色/视觉巡线 | 4 |
| **逻辑** | 逻辑控制 | Hue=330 | 如果/重复/等待/比较 | 6 |
| **输出** | 输出控制 | Hue=45 | LED灯/蜂鸣器 | 4 |
| **高级** | 高级功能 | Hue=0 | 避障/组合动作 | 2 |

---

## 2. 进程视图 (Process View)

### 2.1 运行时进程架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户浏览器                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  UI主线程                                                             │ │
│  │  - Blockly工作区渲染                                                  │ │
│  │  - 积木拖拽交互                                                       │ │
│  │  - 代码生成触发                                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WebSocket客户端线程                                                  │ │
│  │  - 发送代码执行请求                                                   │ │
│  │  - 接收状态推送                                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────────────────────┐
│                         云端服务器 (lanser.fun)                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Nginx Worker进程                                                    │ │
│  │  - 静态资源服务                                                       │ │
│  │  - HTTPS终止                                                          │ │
│  │  - WebSocket代理                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WebSocket中转服务                                                   │ │
│  │  ├─ 连接池管理 (管理所有车载服务连接)                                 │ │
│  │  ├─ 消息路由 (根据vehicle_id转发到对应车载)                           │ │
│  │  ├─ 心跳检测 (监控车载服务在线状态)                                   │ │
│  │  └─ 断线处理 (清理超时连接)                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ WebSocket长连接
┌─────────────────────────────────────────────────────────────────────────────┐
│                      车载服务 (Raspberry Pi)                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  连接管理器线程                                                      │ │
│  │  - 主动连接云端服务                                                   │ │
│  │  - 心跳发送 (30s间隔)                                                 │ │
│  │  - 断线重连 (指数退避)                                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Flask主进程 (Gunicorn + Eventlet)                                    │ │
│  │  ├─ HTTP服务线程池                                                    │ │
│  │  │  ├─ /api/execute (代码执行)                                        │ │
│  │  │  ├─ /api/stop (停止执行)                                          │ │
│  │  │  └─ /api/status (状态查询)                                        │ │
│  │  ├─ WebSocket服务线程                                                │ │
│  │  │  ├─ /ws/control (实时控制)                                        │ │
│  │  │  └─ /ws/status (状态推送)                                         │ │
│  │  └─ 后台任务线程                                                      │ │
│  │     ├─ 传感器状态广播 (10Hz)                                          │ │
│  │     └─ 摄像头流服务                                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  代码执行子进程池                                                     │ │
│  │  ├─ 执行进程1 (用户代码)                                              │ │
│  │  ├─ 执行进程2 (用户代码)                                              │ │
│  │  └─ 执行进程N (用户代码)                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  HiwonderSDK硬件驱动                                                  │ │
│  │  ├─ GPIO/I2C线程                                                     │ │
│  │  ├─ Camera捕获线程                                                    │ │
│  │  └─ UART通信线程                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 通信协议栈

| 通信链路 | 协议 | 方向 | 数据内容 | 频率 |
|---------|------|------|----------|------|
| 浏览器 ↔ 云端 | HTTPS/WSS | 双向 | API请求/响应、WebSocket消息 | 按需/实时 |
| 云端 ↔ 车载 | WSS | 双向 | 代码执行、状态同步、控制指令 | 实时 |
| 车载内部 | Python函数调用 | 单向 | 硬件控制指令 | 高频 |
| 车载 → 云端 → 浏览器 | WSS代理 | 单向 | 传感器状态、执行状态 | 10Hz |

### 2.3 连接管理策略

```python
# 云端服务：连接池管理
class VehicleConnectionPool:
    def __init__(self):
        self.connections = {}  # {vehicle_id: WebSocket}
        self.last_heartbeat = {}  # {vehicle_id: timestamp}

    def add_connection(self, vehicle_id, ws):
        self.connections[vehicle_id] = ws
        self.last_heartbeat[vehicle_id] = time.time()

    def route_message(self, vehicle_id, message):
        if vehicle_id in self.connections:
            self.connections[vehicle_id].send(message)

    def cleanup_stale(self, timeout=60):
        # 清理超过timeout未发送心跳的连接
        stale = [vid for vid, t in self.last_heartbeat.items()
                 if time.time() - t > timeout]
        for vid in stale:
            self.connections[vid].close()
            del self.connections[vid]

# 车载服务：连接管理器
class VehicleConnectionManager:
    def __init__(self, cloud_url):
        self.cloud_url = cloud_url
        self.reconnect_delay = 1  # 初始重连延迟1秒
        self.max_delay = 60       # 最大延迟60秒

    def connect(self):
        while True:
            try:
                ws = websocket.create_connection(self.cloud_url)
                self.reconnect_delay = 1  # 重置重连延迟
                self.heartbeat_loop(ws)
            except Exception as e:
                print(f"连接断开: {e}, {self.reconnect_delay}秒后重连...")
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_delay)

    def heartbeat_loop(self, ws):
        while True:
            ws.send(json.dumps({"type": "heartbeat", "vehicle_id": self.vehicle_id}))
            time.sleep(30)  # 每30秒发送心跳
```

### 2.4 消息路由流程

```
前端发送执行请求
    ↓
POST /block/api/execute (到云端Nginx)
    ↓
云端WebSocket中转服务接收
    ↓
根据vehicle_id路由到对应车载连接
    ↓
车载Flask服务接收请求
    ↓
车载执行代码并调用硬件
    ↓
状态通过同一WebSocket连接推送回云端
    ↓
云端中转服务推送给前端
```

---

## 3. 开发视图 (Development View)

### 3.1 项目目录结构

```
blockly-vehicle/
├── docs/                               # 设计文档
│   ├── 01-system-architecture.md      # 系统架构（本文档）
│   ├── 02-block-api.md                # 积木API规范
│   ├── 03-code-generator.md           # 代码生成器
│   ├── 04-communication.md            # 通信协议
│   ├── 05-block-definitions.md        # 积木定义
│   └── 06-course-design.md            # 课程设计
│
├── cloud/                              # 云端服务项目
│   ├── nginx/                         # Nginx配置
│   │   └── sites-available/
│   │       └── blockly-vehicle.conf   # 站点配置
│   ├── gateway/                       # WebSocket中转服务
│   │   ├── pyproject.toml             # Python项目配置
│   │   ├── uv.lock                    # 依赖锁定
│   │   ├── main.py                    # 服务入口
│   │   ├── connection_pool.py         # 连接池管理
│   │   └── message_router.py          # 消息路由
│   └── frontend/                      # 前端项目
│       ├── package.json               # 前端依赖
│       ├── index.html                 # 主页面
│       ├── css/
│       │   ├── main.css
│       │   ├── blocks.css
│       │   └── themes.css
│       ├── js/
│       │   ├── main.js
│       │   ├── blocks/                # 积木块定义
│       │   │   ├── motion.js
│       │   │   ├── sensor.js
│       │   │   ├── vision.js
│       │   │   ├── logic.js
│       │   │   └── advanced.js
│       │   ├── generators/
│       │   │   └── python.js          # 代码生成器
│       │   ├── api.js
│       │   └── ui.js
│       └── assets/
│           ├── icons/
│           └── sounds/
│
├── vehicle/                            # 车载服务项目
│   ├── pyproject.toml                 # Python项目配置
│   ├── uv.lock                        # 依赖锁定
│   ├── app.py                         # Flask主应用
│   ├── wsgi.py                        # WSGI入口
│   ├── connection/                    # 连接管理
│   │   ├── __init__.py
│   │   └── manager.py                 # 云端连接管理器
│   ├── api/                           # API路由
│   │   ├── __init__.py
│   │   ├── code.py                    # 代码执行API
│   │   ├── control.py                 # 实时控制API
│   │   └── status.py                  # 状态查询API
│   ├── core/                          # 核心业务
│   │   ├── __init__.py
│   │   ├── executor.py                # 代码执行器
│   │   ├── process_manager.py         # 进程管理
│   │   └── sandbox.py                 # 安全沙箱
│   ├── hal/                           # 硬件抽象层
│   │   ├── __init__.py
│   │   ├── motion_controller.py       # 运动控制
│   │   ├── sensor_controller.py       # 传感器
│   │   └── vision_controller.py       # 视觉功能
│   ├── stream/                        # 摄像头流服务
│   │   ├── __init__.py
│   │   └── mjpg_server.py             # MJPG流服务器
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── validator.py
│   └── config/
│       ├── __init__.py
│       ├── settings.py                # 车载服务配置
│       └── blocks.yaml                # 积木配置
│
├── TurboPi/                           # 硬件SDK（已存在）
│   └── HiwonderSDK/
│
├── tests/
│   ├── cloud/                         # 云端服务测试
│   ├── vehicle/                       # 车载服务测试
│   └── integration/                   # 集成测试
│
├── scripts/
│   ├── cloud-start.sh                 # 云端服务启动
│   ├── vehicle-start.sh               # 车载服务启动
│   ├── dev.sh                         # 开发联调启动
│   └── deploy.sh                      # 部署脚本
│
├── .gitignore
├── README.md
└── LICENSE
```

### 3.2 云端服务 (cloud/)

#### 3.2.1 前端项目

**技术栈**: Node.js + Vite + Blockly

**package.json**:
```json
{
  "name": "blockly-vehicle-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "blockly": "^11.0.0",
    "socket.io-client": "^4.6.0"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

#### 3.2.2 WebSocket中转服务

**pyproject.toml**:
```toml
[project]
name = "blockly-gateway"
version = "1.0.0"
requires-python = ">=3.9"
dependencies = [
    "python-socketio==5.11.0",
    "aiohttp==3.9.0",
    "uvicorn==0.24.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
]
```

**main.py**:
```python
from aiohttp import web
import socketio
from connection_pool import VehicleConnectionPool

# 创建SocketIO服务
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
pool = VehicleConnectionPool()

@sio.on('connect')
async def handle_connect(sid, environ):
    # 车载服务连接
    vehicle_id = environ.get('HTTP_X_VEHICLE_ID')
    if vehicle_id:
        await pool.add_connection(vehicle_id, sid)
        print(f"车载服务 {vehicle_id} 已连接")

@sio.on('message')
async def handle_message(sid, data):
    # 路由消息到对应车载
    vehicle_id = data.get('vehicle_id')
    if vehicle_id:
        await pool.route_message(vehicle_id, data)

@sio.on('heartbeat')
async def handle_heartbeat(sid, data):
    # 更新车载心跳
    vehicle_id = data.get('vehicle_id')
    if vehicle_id:
        await pool.update_heartbeat(vehicle_id)

app = web.Application()
sio.attach(app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5001)
```

### 3.3 车载服务 (vehicle/)

#### 3.3.1 项目配置

**pyproject.toml**:
```toml
[project]
name = "blockly-vehicle"
version = "1.0.0"
requires-python = ">=3.9"
dependencies = [
    "Flask==3.0.0",
    "Flask-CORS==4.0.0",
    "Flask-SocketIO==5.3.6",
    "eventlet==0.33.3",
    "python-socketio==5.11.0",
    "gunicorn==21.2.0",
    "RestrictedPython==7.0",
    "opencv-python==4.8.1",
    "pyyaml==6.0.1",
    "requests==2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.3",
    "pytest-cov==4.1.0",
    "black==23.12.1",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
]
```

**settings.py**:
```python
import os

# 车载服务配置
VEHICLE_ID = os.getenv('VEHICLE_ID', 'vehicle-001')
CLOUD_GATEWAY_URL = os.getenv('CLOUD_GATEWAY_URL', 'wss://lanser.fun/block/ws/gateway')

# Flask配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG = False

# HiwonderSDK路径
HIWONDER_SDK_PATH = os.path.join(
    os.path.dirname(__file__),
    '../../TurboPi/HiwonderSDK'
)

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', '/var/log/blockly-vehicle/app.log')

# 硬件SDK路径
TURBOPI_PATH = os.path.join(
    os.path.dirname(__file__),
    '../../TurboPi'
)
```

#### 3.3.2 连接管理器

**connection/manager.py**:
```python
import websocket
import json
import time
import threading
from ..config.settings import CLOUD_GATEWAY_URL, VEHICLE_ID

class VehicleConnectionManager:
    """车载服务云端连接管理器"""

    def __init__(self):
        self.cloud_url = CLOUD_GATEWAY_URL
        self.vehicle_id = VEHICLE_ID
        self.ws = None
        self.reconnect_delay = 1
        self.max_delay = 60
        self.running = False
        self.message_handlers = {}

    def on_message(self, ws, message):
        """接收云端消息"""
        data = json.loads(message)
        msg_type = data.get('type')
        handler = self.message_handlers.get(msg_type)
        if handler:
            handler(data)

    def on_error(self, ws, error):
        print(f"WebSocket错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("云端连接已关闭")
        self.running = False

    def on_open(self, ws):
        print("已连接到云端服务")
        self.running = True
        self.reconnect_delay = 1

        # 发送注册消息
        ws.send(json.dumps({
            "type": "register",
            "vehicle_id": self.vehicle_id,
            "timestamp": time.time()
        }))

    def connect(self):
        """连接到云端服务"""
        websocket.enableTrace(True)
        header = {"X-Vehicle-ID": self.vehicle_id}

        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    self.cloud_url,
                    header=header,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                print(f"连接失败: {e}")

            if not self.running:
                print(f"{self.reconnect_delay}秒后重连...")
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_delay)

    def send(self, data):
        """发送消息到云端"""
        if self.ws and self.running:
            data['vehicle_id'] = self.vehicle_id
            data['timestamp'] = time.time()
            self.ws.send(json.dumps(data))

    def register_handler(self, msg_type, handler):
        """注册消息处理器"""
        self.message_handlers[msg_type] = handler

# 全局连接管理器实例
connection_manager = VehicleConnectionManager()
```

### 3.4 开发环境配置

**开发机配置**:
- **操作系统**: Linux (Ubuntu 22.04)
- **工作目录**: `/home/data/aiprj/blockly-vehicle`
- **Python**: 3.9+
- **Node.js**: 18+

**环境变量 (.env.cloud)** - 云端服务:
```bash
# 云端网关服务配置
GATEWAY_HOST=127.0.0.1
GATEWAY_PORT=5001
LOG_LEVEL=INFO
```

**环境变量 (.env.vehicle)** - 车载服务:
```bash
# 车载服务配置
VEHICLE_ID=vehicle-001
CLOUD_GATEWAY_URL=wss://lanser.fun/block/ws/gateway
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
LOG_LEVEL=DEBUG
MOCK_HARDWARE=false  # 开发时可设为true模拟硬件
```

**开发启动脚本 (scripts/dev.sh)**:
```bash
#!/bin/bash

# 启动云端网关服务
cd cloud/gateway
uv run uvicorn main:app --host 127.0.0.1 --port 5001 &
GATEWAY_PID=$!

# 启动前端开发服务器
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 启动车载服务（开发模式，模拟硬件）
cd ../../vehicle
export MOCK_HARDWARE=true
uv run uvicorn app:create_app --host 0.0.0.0 --port 5000 &
VEHICLE_PID=$!

echo "云端网关: PID=$GATEWAY_PID"
echo "前端服务: PID=$FRONTEND_PID"
echo "车载服务: PID=$VEHICLE_PID"

# 等待信号
trap "kill $GATEWAY_PID $FRONTEND_PID $VEHICLE_PID" EXIT
wait
```

---

## 4. 物理视图 (Physical View)

### 4.1 生产环境部署架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户浏览器                                     │
│                       https://lanser.fun/block/                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ HTTPS (443)
┌─────────────────────────────────────────────────────────────────────────────┐
│                    云端服务器 (lanser.fun)                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Nginx (443端口)                                                      │ │
│  │  location /block/ {                                                   │ │
│  │      # 前端静态资源                                                   │ │
│  │      alias /var/www/blockly-vehicle/frontend/dist/;                    │ │
│  │  }                                                                    │ │
│  │  location /block/ws/ {                                                │ │
│  │      # WebSocket代理到网关服务                                         │ │
│  │      proxy_pass http://127.0.0.1:5001/;                               │ │
│  │      proxy_http_version 1.1;                                          │ │
│  │      proxy_set_header Upgrade $http_upgrade;                          │ │
│  │      proxy_set_header Connection "upgrade";                           │ │
│  │  }                                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WebSocket网关服务 (5001端口)                                         │ │
│  │  - 管理车载服务连接池                                                 │ │
│  │  - 消息路由转发                                                       │ │
│  │  - 心跳检测                                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  /var/www/blockly-vehicle/                                            │ │
│  │  ├── frontend/dist/       # 前端构建产物                              │ │
│  │  │   ├── index.html                                                │ │
│  │  │   └── assets/                                                   │ │
│  │  └── gateway/            # 网关服务代码                              │ │
│  │      └── .venv/          # Python虚拟环境                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ WSS长连接
┌─────────────────────────────────────────────────────────────────────────────┐
│                    车载服务器 (Raspberry Pi 4B)                             │
│  本地IP: 192.168.x.x (动态DHCP或静态IP)                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Systemd服务                                                          │ │
│  │  blockly-vehicle.service                                              │ │
│  │  - 自动启动                                                           │ │
│  │  - 崩溃重启                                                           │ │
│  │  - 日志管理                                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Gunicorn (5000端口)                                                  │ │
│  │  - 4个Worker进程                                                      │ │
│  │  - Eventlet异步模式                                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Flask车载服务                                                        │ │
│  │  ├─ 连接管理器 (主动连接云端)                                         │ │
│  │  ├─ 代码执行API                                                       │ │
│  │  ├─ 硬件抽象层                                                        │ │
│  │  └─ 摄像头流服务 (5001端口)                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  /home/blockly-vehicle/                                                │ │
│  │  ├── vehicle/            # 车载服务代码                               │ │
│  │  │   ├── app.py                                                   │ │
│  │  │   ├── api/                                                     │ │
│  │  │   ├── hal/                                                     │ │
│  │  │   └── .venv/          # Python虚拟环境                            │ │
│  │  ├── TurboPi/            # 硬件SDK                                   │ │
│  │  └── logs/              # 日志文件                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  硬件层                                                               │ │
│  │  ├─ 4x电机 (PWM控制)                                                 │ │
│  │  ├─ 6x舵机 (PWM控制)                                                 │ │
│  │  ├─ 超声波传感器 (GPIO)                                              │ │
│  │  ├─ 4路巡线传感器 (I2C)                                               │ │
│  │  └─ USB摄像头                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 云端部署配置

#### 4.2.1 Nginx配置

**文件**: `/etc/nginx/sites-available/blockly-vehicle`

```nginx
# HTTPS配置
server {
    listen 443 ssl http2;
    server_name lanser.fun;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/lanser.fun/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lanser.fun/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 前端静态资源
    location /block/ {
        alias /var/www/blockly-vehicle/frontend/dist/;
        try_files $uri $uri/ /block/index.html;

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }

    # WebSocket代理到网关服务
    location /block/ws/gateway/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket长连接超时
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # API代理（可选，如果需要云端API）
    location /block/api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HTTP重定向
server {
    listen 80;
    server_name lanser.fun;
    return 301 https://$server_name$request_uri;
}
```

#### 4.2.2 网关服务Systemd配置

**文件**: `/etc/systemd/system/blockly-gateway.service`

```ini
[Unit]
Description=Blockly Vehicle Gateway Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/blockly-vehicle/gateway
Environment="PATH=/var/www/blockly-vehicle/gateway/.venv/bin"
ExecStart=/var/www/blockly-vehicle/gateway/.venv/bin/uvicorn main:app \
    --host 127.0.0.1 \
    --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.3 车载部署配置

#### 4.3.1 车载服务Systemd配置

**文件**: `/etc/systemd/system/blockly-vehicle.service`

```ini
[Unit]
Description=Blockly Vehicle Service
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=pi
Group=pi
WorkingDirectory=/home/blockly-vehicle/vehicle
Environment="PATH=/home/blockly-vehicle/vehicle/.venv/bin"
EnvironmentFile=/home/blockly-vehicle/vehicle/.env
ExecStart=/home/blockly-vehicle/vehicle/.venv/bin/gunicorn \
    -w 4 \
    -k eventlet \
    -b 0.0.0.0:5000 \
    --pid /home/blockly-vehicle/logs/blockly-vehicle.pid \
    --access-logfile /home/blockly-vehicle/logs/access.log \
    --error-logfile /home/blockly-vehicle/logs/error.log \
    --log-level info \
    --timeout 120 \
    wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

# 硬件访问权限
SupplementaryGroups=gpio,i2c,spi

[Install]
WantedBy=multi-user.target
```

#### 4.3.2 车载环境配置

**文件**: `/home/blockly-vehicle/vehicle/.env`

```bash
# 车辆标识
VEHICLE_ID=vehicle-001

# 云端网关地址
CLOUD_GATEWAY_URL=wss://lanser.fun/block/ws/gateway

# Flask配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/home/blockly-vehicle/logs/app.log

# HiwonderSDK路径
TURBOPI_PATH=/home/blockly-vehicle/TurboPi

# 硬件配置
MOTOR_MAX_SPEED=80
SERVO_MAX_ANGLE=180
```

### 4.4 部署脚本

#### 4.4.1 云端部署脚本

**文件**: `scripts/deploy-cloud.sh`

```bash
#!/bin/bash

VERSION=$1
DEPLOY_PATH="/var/www/blockly-vehicle"
RELEASE_PATH="$DEPLOY_PATH/releases/$VERSION"
CURRENT_PATH="$DEPLOY_PATH/current"

echo "部署云端服务 v$VERSION..."

# 1. 构建前端
cd cloud/frontend
npm run build
mkdir -p "$RELEASE_PATH/frontend"
cp -r dist/* "$RELEASE_PATH/frontend/"

# 2. 部署网关服务
cd ../gateway
mkdir -p "$RELEASE_PATH/gateway"
cp -r *.py pyproject.toml uv.lock "$RELEASE_PATH/gateway/"

# 3. 安装依赖
cd "$RELEASE_PATH/gateway"
if [ ! -d "$DEPLOY_PATH/gateway/.venv" ]; then
    uv venv "$DEPLOY_PATH/gateway/.venv"
fi
uv sync --no-venv --python "$DEPLOY_PATH/gateway/.venv/bin/python"

# 4. 更新软链接
ln -sfn "$RELEASE_PATH" "$CURRENT_PATH"

# 5. 重启网关服务
sudo systemctl restart blockly-gateway

echo "云端服务部署完成!"
```

#### 4.4.2 车载部署脚本

**文件**: `scripts/deploy-vehicle.sh`

```bash
#!/bin/bash

VERSION=$1
DEPLOY_PATH="/home/blockly-vehicle"
RELEASE_PATH="$DEPLOY_PATH/releases/$VERSION"
CURRENT_PATH="$DEPLOY_PATH/current"

echo "部署车载服务 v$VERSION..."

# 1. 创建发布目录
mkdir -p "$RELEASE_PATH"

# 2. 复制车载服务代码
cp -r vehicle/* "$RELEASE_PATH/"

# 3. 确保TurboPi存在
if [ ! -d "$RELEASE_PATH/TurboPi" ]; then
    ln -s "$DEPLOY_PATH/TurboPi" "$RELEASE_PATH/TurboPi"
fi

# 4. 安装依赖
cd "$RELEASE_PATH"
if [ ! -d "$DEPLOY_PATH/.venv" ]; then
    uv venv "$DEPLOY_PATH/.venv"
fi
uv sync --no-venv --python "$DEPLOY_PATH/.venv/bin/python"

# 5. 更新软链接
ln -sfn "$RELEASE_PATH" "$CURRENT_PATH"

# 6. 重启服务
sudo systemctl restart blockly-vehicle

echo "车载服务部署完成!"
```

---

## 5. 场景视图 (Scenarios View)

### 5.1 场景一: 基础运动控制

**用户操作流程**:
```
1. 打开浏览器访问 https://lanser.fun/block/
2. 前端自动连接云端WebSocket (wss://lanser.fun/block/ws/gateway)
3. 从"运动"工具箱拖拽"前进"积木
4. 拖拽"等待2秒"积木
5. 拖拽"停止"积木
6. 点击"运行"按钮
7. 观察小车前进2秒后停止
```

**系统处理流程**:
```
前端:
  - 生成Python代码: motion.qianjin(50); dengdai(2); motion.tingzhi()
  - 通过WebSocket发送到云端网关

云端网关:
  - 接收前端消息
  - 根据vehicle_id路由到对应车载服务
  - 转发消息到车载连接

车载服务:
  - 接收代码执行请求
  - 创建执行进程运行代码
  - HAL调用 → HiwonderSDK → 电机驱动 → 小车移动
  - 状态通过同一WebSocket推送回云端 → 前端
```

### 5.2 场景二: 传感器避障

**用户操作流程**:
```
1. 拖拽"重复执行"积木
2. 嵌入"如果"积木，条件: "超声波距离 < 200mm"
3. 嵌入"停止"和"蜂鸣器响"
4. 运行代码
5. 用手遮挡超声波传感器
6. 小车自动停止并蜂鸣
```

**系统处理流程**:
```
前端:
  - 生成循环+条件判断代码
  - 发送到云端网关

云端网关:
  - 转发到车载服务

车载服务:
  - 执行循环代码，持续调用 sensor.heshengbo()
  - HAL轮询超声波传感器 (10Hz)
  - 检测到障碍 → motion.tingzhi() → 电机停止
  - 状态实时推送 → 云端 → 前端更新UI
```

### 5.3 场景三: 连接断开重连

**场景描述**: 小车网络断开后自动重连

**处理流程**:
```
车载服务:
  1. 检测到WebSocket断开
  2. 启动重连机制（指数退避: 1s, 2s, 4s, ..., 最大60s）
  3. 重连成功后发送注册消息
  4. 恢复正常通信

云端网关:
  1. 检测到车载连接超时（60s无心跳）
  2. 清理该连接
  3. 标记车辆为离线状态
  4. 前端显示"车辆离线"提示

前端:
  - 接收离线通知
  - 显示"小车已离线，请检查网络"
  - 连接恢复后自动恢复正常状态
```

### 5.4 场景四: 紧急停止

**用户操作流程**:
```
1. 小车正在执行任何动作
2. 点击"紧急停止"按钮
3. 所有电机立即停止
4. 所有舵机复位
```

**系统处理流程**:
```
前端:
  - 点击紧急停止
  - 发送紧急停止消息到云端网关

云端网关:
  - 高优先级转发到车载服务
  - 不等待排队

车载服务:
  - 立即执行:
    1. motion_controller.stop()
    2. motion_controller.reset_servos()
    3. process_manager.stop_all()
  - 发送确认消息回前端
```

### 5.5 场景五: 多车辆管理（扩展）

**场景描述**: 云端支持多辆小车同时在线

**处理流程**:
```
云端网关:
  - 维护多辆车的连接池
  - 每辆车有唯一的vehicle_id
  - 前端选择要控制的车辆

前端:
  - 显示在线车辆列表
  - 用户选择要控制的车辆
  - 所有消息携带vehicle_id

消息路由:
  - 网关根据vehicle_id路由到对应车载服务
  - 各车辆独立执行，互不干扰
```

---

## 6. 非功能需求

### 6.1 性能指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 前端首屏加载 | < 2s | Lighthouse |
| 代码生成延迟 | < 100ms | 工作区变化到代码更新 |
| 云端到车载延迟 | < 100ms | WebSocket消息往返 |
| 状态反馈延迟 | < 200ms | 传感器到UI更新 |
| 连接重连时间 | < 10s | 网络恢复到重连成功 |
| 内存占用(车载) | < 300MB | ps aux |
| CPU占用(车载空闲) | < 10% | top |

### 6.2 安全要求

| 需求 | 实现方式 |
|------|----------|
| 代码沙箱 | RestrictedPython白名单 |
| 参数验证 | 所有API输入验证 |
| HTTPS通信 | Let's Encrypt证书 |
| 车辆认证 | vehicle_id + 密钥（可选） |
| 硬件保护 | 参数范围限制、超时保护 |
| 访问控制 | 可选的用户认证系统 |

### 6.3 可靠性要求

| 需求 | 实现方式 |
|------|----------|
| 断线重连 | 指数退避重连机制 |
| 心跳保活 | 30秒心跳间隔，60秒超时 |
| 崩溃恢复 | Systemd自动重启 |
| 日志记录 | 结构化日志，便于故障排查 |
| 监控告警 | 车辆在线状态监控 |

### 6.4 可维护性

- **日志记录**: 结构化日志(JSON格式)，分级输出
- **监控告警**: 车辆在线状态、服务健康度
- **版本管理**: Git语义化版本
- **零停机部署**: 软链接切换部署
- **文档完善**: API文档、部署文档、故障排查手册

---

*文档版本: v3.0*
*创建日期: 2026-02-19*
*更新日期: 2026-02-19*
*更新内容: 重构为云端+车载双层架构，后端拆分为lanser.fun云端服务和Raspberry Pi车载服务，通过WebSocket长连接通信*
