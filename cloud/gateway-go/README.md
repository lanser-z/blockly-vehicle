# Blockly Gateway (Golang)

Blockly小车云端网关服务 - Golang实现

## 功能特性

- WebSocket连接管理（原生WebSocket协议）
- 车载服务连接池
- 前端客户端管理
- 心跳检测和自动清理
- 消息路由和转发
- HTTP健康检查和API

## 技术栈

| 库 | 版本 | 用途 |
|----|------|------|
| gorilla/websocket | ^1.5.0 | WebSocket服务 |
| gin-gonic/gin | ^1.9.0 | HTTP路由 |
| sirupsen/logrus | ^1.9.0 | 结构化日志 |

## 目录结构

```
├── cmd/gateway/main.go         # 主程序入口
├── internal/
│   ├── message/                # 消息类型定义
│   ├── pool/                   # 连接池管理
│   └── handler/                # WebSocket和消息处理
├── api/http/                   # HTTP API
├── configs/config.yaml         # 配置文件
└── deployments/                # 部署配置
```

## 编译

```bash
# 本地编译
make build

# 交叉编译到Linux
make build-linux

# 下载依赖
make deps
```

## 运行

```bash
# 直接运行
make run

# 或编译后运行
./bin/gateway
```

## 部署

```bash
# 部署到本地服务器
make deploy

# 手动部署
sudo mkdir -p /opt/blockly-gateway
sudo cp bin/gateway /opt/blockly-gateway/bin/
sudo cp -r configs /opt/blockly-gateway/
sudo chown -R www-data:www-data /opt/blockly-gateway
```

## systemd服务

```bash
# 安装服务
sudo cp deployments/blockly-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blockly-gateway
sudo systemctl start blockly-gateway

# 查看状态
sudo systemctl status blockly-gateway

# 查看日志
sudo journalctl -u blockly-gateway -f
```

## API

### HTTP端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/vehicles` | GET | 获取在线车辆列表 |

### WebSocket端点

| 端点 | 说明 |
|------|------|
| `/ws/gateway` | WebSocket连接端点 |

**请求头**（车载服务）:
- `X-Vehicle-ID: vehicle-001` - 标识车载服务

## 消息格式

### 前端 → 网关

```json
{
  "type": "execute_code",
  "vehicle_id": "vehicle-001",
  "data": {
    "code": "python_code_here",
    "timeout": 60,
    "execution_id": "exec_123"
  },
  "timestamp": 1700000000
}
```

### 车载 → 网关

```json
{
  "type": "execution_started",
  "data": {
    "execution_id": "exec_123",
    "process_id": "proc_456"
  }
}
```

## 性能

| 指标 | 数值 |
|------|------|
| 内存占用 | ~15MB |
| 启动时间 | ~10ms |
| 并发连接 | 10000+ |

## 配置

参见 `configs/config.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 5001

gateway:
  heartbeat_check_interval: 30
  heartbeat_timeout: 60

log:
  level: "info"
  format: "json"
```
