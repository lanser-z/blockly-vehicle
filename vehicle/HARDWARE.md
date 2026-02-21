# 硬件依赖安装说明

## Raspberry Pi 硬件依赖

车载服务在真实硬件上运行时，需要以下 Raspberry Pi 专用 Python 包：

## 快速开始（推荐）

### 方式一：使用启动脚本（自动安装依赖）

```bash
cd /home/data/aiprj/blockly-vehicle/vehicle

# 一键启动（自动检测并安装依赖）
./vehicle-start.sh
```

启动脚本会自动：
- 检测是否为 Raspberry Pi 硬件
- 检查并安装硬件依赖包
- 检查并安装 Python 依赖
- 启动车载服务

### 方式二：先检查依赖

```bash
cd /home/data/aiprj/blockly-vehicle/vehicle

# 运行依赖检查
./check-deps.sh
```

检查脚本会显示：
- 系统命令状态
- Python 依赖状态
- 硬件依赖状态
- 权限和接口状态
- 缺失依赖的安装命令

## 手动安装

### Python 依赖

```bash
cd /home/data/aiprj/blockly-vehicle/vehicle

# 使用 uv（推荐）
uv sync --group hardware

# 或使用 pip
pip install -r requirements-hardware.txt
pip install -e .
```

### 硬件包单独安装

```bash
# GPIO 控制
pip install RPi.GPIO

# I2C 通信
pip install smbus2

# RGB LED 控制
pip install rpi-ws281x
```

### 系统依赖

```bash
# 更新系统包
sudo apt update

# 安装 Python 开发依赖
sudo apt install -y python3-dev python3-pip python3-opencv

# 安装 I2C 工具
sudo apt install -y i2c-tools libi2c-dev

# 启用 I2C 和 SPI
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TURBOPI_PATH` | TurboPi 目录路径 | `./TurboPi` |
| `MOCK_HARDWARE` | 是否使用模拟模式 | `false` |

## 验证安装

```bash
# 使用依赖检查脚本
./check-deps.sh

# 或手动检查
python3 -c "import RPi.GPIO; print('RPi.GPIO: OK')"
python3 -c "import smbus2; print('smbus2: OK')"
python3 -c "import rpi_ws281x; print('rpi_ws281x: OK')"

# 检查 OpenCV
python3 -c "import cv2; print('OpenCV: ' + cv2.__version__)"

# 检查 TurboPi 路径
python3 -c "import sys; print(sys.path)"
```

## 故障排除

### 问题：`No module named 'RPi'`

**原因**：Raspberry Pi 硬件包未安装

**解决**：
```bash
pip install RPi.GPIO smbus2 rpi-ws281x
```

### 问题：`RuntimeError: ws2811_init failed with code -5 (mmap() failed)`

**原因**：`/dev/mem` 访问权限不足，GPIO 访问需要 root 权限或特殊组权限

**解决方案（推荐顺序）**：

1. **添加用户到 gpio 组（推荐）**：
```bash
# 添加用户到必要的组
sudo usermod -a -G gpio,video,i2c $USER

# 重新登录生效
su - $USER
# 或重启
sudo reboot
```

2. **使用 sudo 启动服务**：
```bash
sudo ./vehicle-start.sh
```

3. **使用模拟模式（开发测试）**：
```bash
export MOCK_HARDWARE=true
./vehicle-start.sh
```

### 问题：`ImportError: libgbm.so.1`

**原因**：缺少系统图形库

**解决**：
```bash
sudo apt install -y libgbm-dev
```

### 问题：摄像头无法打开

**原因**：摄像头权限问题

**解决**：
```bash
# 添加用户到 video 组
sudo usermod -a -G video $USER

# 重新登录生效
# 或重启
sudo reboot
```

### 问题：I2C 通信失败

**原因**：I2C 未启用或权限问题

**解决**：
```bash
# 启用 I2C
sudo raspi-config nonint do_i2c 0

# 添加用户到 i2c 组
sudo usermod -a -G i2c $USER

# 检查 I2C 设备
i2cdetect -y 1
```

## 模拟模式

如果需要在非 Raspberry Pi 环境下开发测试，可以启用模拟模式：

```bash
export MOCK_HARDWARE=true
./vehicle-start.sh
```

模拟模式下：
- 运动控制：模拟日志输出
- 传感器：返回模拟数据
- 视觉：返回随机检测结果
- 云台：模拟角度变化
