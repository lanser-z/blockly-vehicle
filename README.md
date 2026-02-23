# Blockly少儿编程小车

基于Google Blockly的少儿可视化编程小车项目，专为6岁儿童设计。

## 项目简介

将专业的麦克纳姆轮机器人控制系统转化为儿童可理解和操作的积木编程环境，通过拖拽积木块即可控制小车运动，培养孩子的逻辑思维和创造力。

## 硬件平台

- **主控**: Raspberry Pi 4B
- **执行器**: 4个舵机控制的麦克纳姆轮（全向移动）
- **传感器**:
  - 云台摄像头（2自由度）
  - 超声波测距模块
  - 4路巡线传感器
- **操作系统**: Raspberry Pi OS

## 系统架构

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端 Blockly  │────▶│  网关 Gateway│────▶│  车载 Vehicle │
│   (Web界面)     │     │  (Go服务)    │     │  (Python服务) │
└─────────────────┘     └─────────────┘     └─────────────┘
                                                        │
                                                        ▼
                                                  ┌──────────────┐
                                                  │ HiwonderSDK  │
                                                  │  硬件抽象层  │
                                                  └──────────────┘
```

## 功能特性

### 积木块类型
- **运动控制**: 前进/后退/左平移/右平移/左转/右转/停止
- **云台控制**: 上下左右复位
- **传感器**: 超声波测距、巡线检测
- **视觉**: 颜色识别
- **逻辑**: 如果/否则、重复执行、等待

### 速度档位
- 🐢 慢速: 40
- 🚶 中速: 60
- 🏃 快速: 80

## 项目结构

```
blockly-vehicle/
├── cloud/               # 云端服务
│   ├── frontend/        # Blockly前端界面
│   ├── gateway-go/      # Go网关服务
│   └── nginx/           # Nginx配置
├── vehicle/             # 车载服务
│   ├── hal/             # 硬件抽象层
│   ├── executor/        # 代码执行器
│   ├── connection/      # 连接管理
│   └── app.py           # Flask应用
├── TurboPi/             # HiwonderSDK源码
├── docs/                # 文档
└── tests/               # 测试
```

## 快速开始

### 前端部署

```bash
cd cloud/frontend
npm install
npm run build
# 将dist目录部署到Web服务器
```

### 网关部署

```bash
cd cloud/gateway-go
go build -o gateway ./cmd/gateway
./gateway
```

### 车载服务部署

```bash
cd vehicle
uv sync
./vehicle-start.sh  # 或手动启动: gunicorn --config config/gunicorn.conf.py wsgi:app
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VEHICLE_ID` | 小车ID | `vehicle-001` |
| `CLOUD_GATEWAY_URL` | 云端网关地址 | `wss://lanser.fun/block/ws/gateway` |
| `MOTOR_MAX_SPEED` | 电机最大速度 | `80` |
| `SERVO_MAX_ANGLE` | 舵机最大角度 | `180` |
| `EXECUTION_TIMEOUT` | 代码执行超时(秒) | `30` |

### 硬件依赖

```bash
# Raspberry Pi硬件依赖
sudo apt-get install python3-dev libgpiod-dev
pip install RPi.GPIO smbus2 rpi-ws281x
```

## 开发指南

### 添加新的积木块

1. 在 `cloud/frontend/js/main.js` 中定义积木块
2. 在 `vehicle/hal/` 中实现对应的底层控制函数
3. 在代码生成器中添加生成规则

### 修改运动控制

运动控制逻辑位于 `vehicle/hal/motion_controller.py`，直接通过电机控制实现：
- 前进: `Board.setMotor(1, s); Board.setMotor(2, s); Board.setMotor(3, s); Board.setMotor(4, s)`
- 左平移: `Board.setMotor(1, -s); Board.setMotor(2, s); Board.setMotor(3, -s); Board.setMotor(4, s)`
- 右平移: `Board.setMotor(1, s); Board.setMotor(2, -s); Board.setMotor(3, s); Board.setMotor(4, -s)`

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！
