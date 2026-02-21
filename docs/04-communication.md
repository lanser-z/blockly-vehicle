# 通信协议设计

## 1. 概述

本文档定义了Blockly少儿编程小车系统的通信协议，采用**云端+车载双层架构**：
- **前端 ↔ 云端**: HTTPS/WebSocket（浏览器到lanser.fun）
- **云端 ↔ 车载**: WebSocket长连接（lanser.fun到Raspberry Pi）

---

## 2. 通信架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          前端 (Browser)                                    │
│                    https://lanser.fun/block/                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────────────────────┐
│                       云端服务 (lanser.fun)                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Nginx反向代理                                                         │ │
│  │  - /block/ → 静态资源                                                  │ │
│  │  - /block/ws/gateway/ → WebSocket网关                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WebSocket网关服务                                                    │ │
│  │  - 连接池管理（管理所有车载连接）                                     │ │
│  │  - 消息路由（根据vehicle_id转发）                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓ WebSocket长连接
┌─────────────────────────────────────────────────────────────────────────────┐
│                      车载服务 (Raspberry Pi)                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  连接管理器                                                            │ │
│  │  - 主动连接云端                                                       │ │
│  │  - 心跳保活                                                           │ │
│  │  - 断线重连                                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Flask车载服务                                                        │ │
│  │  - 代码执行API                                                        │ │
│  │  - 实时控制API                                                        │ │
│  │  - 状态查询API                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 前端 ↔ 云端通信

### 3.1 WebSocket连接

**连接端点**: `wss://lanser.fun/block/ws/gateway`

**连接参数**:
```javascript
const ws = new WebSocket('wss://lanser.fun/block/ws/gateway');
```

**连接初始化**:
```javascript
// 连接成功后发送注册消息
ws.send(JSON.stringify({
    type: 'client_register',
    client_id: generateClientId(),  // 前端生成唯一ID
    timestamp: Date.now()
}));
```

### 3.2 消息格式

所有消息使用JSON格式：

```json
{
    "type": "message_type",     // 消息类型
    "vehicle_id": "vehicle-001", // 目标车辆ID
    "data": {},                  // 消息数据
    "timestamp": 1234567890      // 时间戳
}
```

### 3.3 消息类型定义

#### 3.3.1 前端 → 云端

| 类型 | 用途 | data字段 |
|------|------|----------|
| `client_register` | 客户端注册 | {client_id} |
| `execute_code` | 执行代码 | {code, timeout} |
| `stop_execution` | 停止执行 | {execution_id} |
| `emergency_stop` | 紧急停止 | {} |
| `get_status` | 获取状态 | {} |
| `ping` | 心跳检测 | {} |

**示例：执行代码**
```json
{
    "type": "execute_code",
    "vehicle_id": "vehicle-001",
    "data": {
        "code": "motion.qianjin(50)\ndengdai(2)\nmotion.tingzhi()",
        "timeout": 60
    },
    "timestamp": 1234567890
}
```

#### 3.3.2 云端 → 前端

| 类型 | 用途 | data字段 |
|------|------|----------|
| `execution_started` | 执行开始 | {execution_id} |
| `execution_output` | 执行输出 | {output} |
| `execution_finished` | 执行完成 | {execution_id, success} |
| `execution_error` | 执行错误 | {error} |
| `sensor_update` | 传感器更新 | {sensors} |
| `vehicle_status` | 车辆状态 | {online, busy} |
| `vehicle_list` | 车辆列表 | [{vehicle_id, name, online}] |
| `error` | 错误通知 | {code, message} |

**示例：传感器更新**
```json
{
    "type": "sensor_update",
    "vehicle_id": "vehicle-001",
    "data": {
        "sensors": {
            "ultrasonic": 250,
            "infrared": [false, true, true, false],
            "battery": 7.8
        }
    },
    "timestamp": 1234567890
}
```

---

## 4. 云端 ↔ 车载通信

### 4.1 WebSocket连接

**车载主动连接云端**: `wss://lanser.fun/block/ws/gateway`

**连接头部**:
```python
headers = {
    "X-Vehicle-ID": "vehicle-001",
    "X-Vehicle-Secret": "optional-secret-key"  # 可选的认证密钥
}
```

**连接初始化**:
```json
{
    "type": "register",
    "vehicle_id": "vehicle-001",
    "timestamp": 1234567890
}
```

### 4.2 消息类型定义

#### 4.2.1 云端 → 车载

| 类型 | 用途 | data字段 |
|------|------|----------|
| `execute_code` | 执行代码请求 | {code, timeout, execution_id} |
| `stop_execution` | 停止执行 | {execution_id} |
| `emergency_stop` | 紧急停止 | {} |
| `get_status` | 获取状态 | {} |
| `ping` | 心跳检测 | {} |

#### 4.2.2 车载 → 云端

| 类型 | 用途 | data字段 |
|------|------|----------|
| `register` | 注册车辆 | {vehicle_id, name, capabilities} |
| `heartbeat` | 心跳保活 | {vehicle_id} |
| `execution_started` | 执行开始 | {execution_id} |
| `execution_output` | 执行输出 | {execution_id, output} |
| `execution_finished` | 执行完成 | {execution_id, success} |
| `execution_error` | 执行错误 | {execution_id, error} |
| `sensor_update` | 传感器更新 | {sensors} |
| `status_update` | 状态更新 | {status} |
| `pong` | 心跳响应 | {} |

### 4.3 心跳机制

**车载 → 云端** (每30秒):
```json
{
    "type": "heartbeat",
    "vehicle_id": "vehicle-001",
    "timestamp": 1234567890
}
```

**云端检测**:
- 60秒内未收到心跳 → 标记车辆离线
- 清理该车辆的连接
- 通知所有连接的前端客户端

---

## 5. 云端消息路由

### 5.1 路由表

云端网关维护车辆连接映射：

```python
class VehicleConnectionPool:
    def __init__(self):
        # vehicle_id -> WebSocket连接
        self.connections: Dict[str, WebSocket] = {}
        # vehicle_id -> 最后心跳时间
        self.last_heartbeat: Dict[str, float] = {}

    def add_connection(self, vehicle_id: str, ws: WebSocket):
        """添加车辆连接"""
        self.connections[vehicle_id] = ws
        self.last_heartbeat[vehicle_id] = time.time()
        logger.info(f"车辆 {vehicle_id} 已连接")

    def route_message(self, vehicle_id: str, message: dict):
        """路由消息到指定车辆"""
        if vehicle_id in self.connections:
            self.connections[vehicle_id].send(json.dumps(message))
        else:
            logger.warning(f"车辆 {vehicle_id} 未连接")
```

### 5.2 消息转发流程

```
前端发送消息
    ↓
云端网关接收
    ↓
提取vehicle_id
    ↓
查找对应车载连接
    ↓
转发消息到车载
    ↓
车载处理并响应
    ↓
响应通过同一连接返回云端
    ↓
云端根据session_id路由回前端
```

---

## 6. 车载连接管理

### 6.1 连接管理器

```python
class VehicleConnectionManager:
    """车载服务云端连接管理器"""

    def __init__(self, cloud_url: str, vehicle_id: str):
        self.cloud_url = cloud_url
        self.vehicle_id = vehicle_id
        self.ws = None
        self.running = False
        self.reconnect_delay = 1
        self.max_delay = 60

    def connect(self):
        """连接到云端（带重连）"""
        while True:
            try:
                self.ws = websocket.create_connection(
                    self.cloud_url,
                    header={"X-Vehicle-ID": self.vehicle_id}
                )
                self.running = True
                self.reconnect_delay = 1
                self._send_register()
                self._message_loop()
            except Exception as e:
                logger.error(f"连接失败: {e}")
            self._reconnect()

    def _reconnect(self):
        """指数退避重连"""
        if not self.running:
            logger.info(f"{self.reconnect_delay}秒后重连...")
            time.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_delay)

    def send(self, message: dict):
        """发送消息到云端"""
        if self.ws and self.running:
            message['vehicle_id'] = self.vehicle_id
            message['timestamp'] = time.time()
            self.ws.send(json.dumps(message))

    def send_heartbeat(self):
        """发送心跳"""
        self.send({
            "type": "heartbeat",
            "data": {}
        })
```

### 6.2 心跳发送

```python
def heartbeat_loop(manager: VehicleConnectionManager):
    """心跳循环"""
    while manager.running:
        try:
            manager.send_heartbeat()
            time.sleep(30)  # 每30秒
        except Exception as e:
            logger.error(f"心跳发送失败: {e}")
            break
```

---

## 7. 错误处理

### 7.1 错误码定义

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| `VEHICLE_OFFLINE` | 车辆离线 | 503 |
| `VEHICLE_BUSY` | 车辆忙碌 | 409 |
| `INVALID_VEHICLE_ID` | 无效车辆ID | 400 |
| `CODE_EMPTY` | 代码为空 | 400 |
| `EXECUTION_TIMEOUT` | 执行超时 | 408 |
| `EXECUTION_FAILED` | 执行失败 | 500 |
| `HARDWARE_ERROR` | 硬件错误 | 500 |

### 7.2 错误消息格式

```json
{
    "type": "error",
    "vehicle_id": "vehicle-001",
    "data": {
        "code": "VEHICLE_OFFLINE",
        "message": "车辆未连接到云端",
        "details": {}
    },
    "timestamp": 1234567890
}
```

---

## 8. 安全机制

### 8.1 通信安全

| 措施 | 实现 |
|------|------|
| HTTPS/WSS | Let's Encrypt证书 |
| 车辆认证 | vehicle_id + 可选密钥 |
| 消息签名 | 可选HMAC签名 |
| 速率限制 | 每辆车每秒最多10条消息 |

### 8.2 车辆认证（可选）

```python
# 云端验证车辆注册
def handle_register(ws, data):
    vehicle_id = data.get('vehicle_id')
    secret = data.get('secret')

    # 验证密钥（如果启用）
    if SECRET_REQUIRED:
        expected_secret = get_vehicle_secret(vehicle_id)
        if secret != expected_secret:
            ws.close(4001, "认证失败")
            return

    # 注册连接
    pool.add_connection(vehicle_id, ws)
```

---

## 9. 前端API示例

### 9.1 WebSocket连接管理

```javascript
class BlocklyClient {
    constructor(vehicleId) {
        this.vehicleId = vehicleId;
        this.ws = null;
        this.messageHandlers = {};
    }

    connect() {
        this.ws = new WebSocket('wss://lanser.fun/block/ws/gateway');

        this.ws.onopen = () => {
            console.log('已连接到云端服务');
            this.send({
                type: 'client_register',
                data: { client_id: this.generateClientId() }
            });
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };

        this.ws.onclose = () => {
            console.log('连接已断开，5秒后重连...');
            setTimeout(() => this.connect(), 5000);
        };
    }

    send(message) {
        message.vehicle_id = this.vehicleId;
        message.timestamp = Date.now();
        this.ws.send(JSON.stringify(message));
    }

    // 执行代码
    executeCode(code, timeout = 60) {
        return new Promise((resolve, reject) => {
            const executionId = generateExecutionId();

            this.registerHandler(`execution_finished_${executionId}`, (data) => {
                if (data.success) {
                    resolve(data);
                } else {
                    reject(new Error(data.error));
                }
            });

            this.send({
                type: 'execute_code',
                data: { code, timeout, execution_id }
            });
        });
    }

    // 紧急停止
    emergencyStop() {
        this.send({
            type: 'emergency_stop',
            data: {}
        });
    }

    // 注册消息处理器
    registerHandler(eventType, handler) {
        if (!this.messageHandlers[eventType]) {
            this.messageHandlers[eventType] = [];
        }
        this.messageHandlers[eventType].push(handler);
    }

    handleMessage(message) {
        const { type, data } = message;
        const handlers = this.messageHandlers[type] || [];
        handlers.forEach(handler => handler(data));

        // 传感器状态更新
        if (type === 'sensor_update') {
            this.updateSensorDisplay(data.sensors);
        }

        // 车辆状态更新
        if (type === 'vehicle_status') {
            this.updateVehicleStatus(data);
        }
    }
}

// 使用示例
const client = new BlocklyClient('vehicle-001');
client.connect();

// 执行代码
const code = 'motion.qianjin(50)\ndengdai(2)\nmotion.tingzhi()';
client.executeCode(code).then(result => {
    console.log('执行完成:', result);
}).catch(error => {
    console.error('执行失败:', error);
});
```

---

## 10. 性能优化

### 10.1 消息压缩

对于大型消息（如代码输出），启用压缩：

```python
# 云端发送时压缩
import gzip
import base64

def compress_message(data: str) -> str:
    compressed = gzip.compress(data.encode())
    return base64.b64encode(compressed).decode()

# 车载接收时解压
def decompress_message(data: str) -> str:
    compressed = base64.b64decode(data)
    return gzip.decompress(compressed).decode()
```

### 10.2 批量状态更新

传感器状态批量发送，减少消息数量：

```json
{
    "type": "sensor_batch_update",
    "vehicle_id": "vehicle-001",
    "data": {
        "updates": [
            {"sensor": "ultrasonic", "value": 250, "time": 1234567890},
            {"sensor": "infrared", "value": [0,1,1,0], "time": 1234567891},
            {"sensor": "battery", "value": 7.8, "time": 1234567892}
        ]
    }
}
```

---

## 11. 监控指标

### 11.1 云端监控

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 在线车辆数 | 当前连接的车辆数 | - |
| 消息吞吐量 | 每秒消息数 | >1000 |
| 消息延迟 | 消息转发延迟 | >100ms |
| 连接超时率 | 心跳超时比例 | >5% |

### 11.2 车载监控

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 连接状态 | 与云端的连接状态 | 离线 |
| 重连次数 | 累计重连次数 | >10次/小时 |
| 心跳延迟 | 心跳往返延迟 | >500ms |
| 消息队列深度 | 待发送消息数 | >100 |

---

*文档版本: v2.0*
*创建日期: 2026-02-19*
*更新日期: 2026-02-19*
*更新内容: 适配云端+车载双层架构，定义前端↔云端和云端↔车载两段通信协议*
