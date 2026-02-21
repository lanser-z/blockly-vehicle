#!/bin/bash
# Blockly小车依赖检查脚本
# 检查所有必需的依赖是否已安装

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================"
echo "  Blockly小车依赖检查"
echo "======================================"
echo ""

# 检查结果汇总
TOTAL=0
PASS=0
FAIL=0

check_item() {
    TOTAL=$((TOTAL + 1))
    local name="$1"
    local check_cmd="$2"
    local install_cmd="$3"

    if eval "$check_cmd" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        echo -e "    安装命令: ${BLUE}$install_cmd${NC}"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

# ===== 检查系统命令 =====
echo "=== 系统命令 ==="
check_item "Python 3" "command -v python3" "sudo apt install python3"
check_item "pip3" "command -v pip3" "sudo apt install python3-pip"
check_item "git" "command -v git" "sudo apt install git"

# 检查是否是 Raspberry Pi
IS_RPI=0
if [ -f /proc/device-tree/model ]; then
    MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "")
    if echo "$MODEL" | grep -qi "raspberry pi"; then
        IS_RPI=1
        echo -e "${GREEN}✓${NC} 硬件: Raspberry Pi"
    fi
fi

if [ $IS_RPI -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC} 硬件: 非 Raspberry Pi (将使用模拟模式)"
fi

echo ""

# ===== 检查 Raspberry Pi 硬件依赖 =====
if [ $IS_RPI -eq 1 ]; then
    echo "=== Raspberry Pi 硬件依赖 ==="
    check_item "RPi.GPIO" "python3 -c 'import RPi.GPIO'" "pip3 install RPi.GPIO"
    check_item "smbus2" "python3 -c 'import smbus2'" "pip3 install smbus2"
    check_item "rpi_ws281x" "python3 -c 'import rpi_ws281x'" "pip3 install rpi-ws281x"
    echo ""
fi

# ===== 检查 Python 依赖 =====
echo "=== Python 核心依赖 ==="
check_item "Flask" "python3 -c 'import flask'" "pip3 install Flask"
check_item "Flask-CORS" "python3 -c 'import flask_cors'" "pip3 install Flask-CORS"
check_item "Flask-SocketIO" "python3 -c 'import flask_socketio'" "pip3 install Flask-SocketIO"
check_item "eventlet" "python3 -c 'import eventlet'" "pip3 install eventlet"
check_item "opencv-python (cv2)" "python3 -c 'import cv2'" "pip3 install opencv-python"
check_item "numpy" "python3 -c 'import numpy'" "pip3 install numpy"
check_item "PyYAML" "python3 -c 'import yaml'" "pip3 install pyyaml"
check_item "requests" "python3 -c 'import requests'" "pip3 install requests"
check_item "websocket-client" "python3 -c 'import websocket'" "pip3 install websocket-client"
check_item "RestrictedPython" "python3 -c 'import RestrictedPython'" "pip3 install RestrictedPython"
echo ""

# ===== 检查可选工具 =====
echo "=== 可选工具 ==="
check_item "uv (包管理器)" "command -v uv" "curl -LsSf https://astral.sh/uv/install.sh | sh"
check_item "gunicorn (WSGI服务器)" "command -v gunicorn" "pip3 install gunicorn"
echo ""

# ===== 检查 TurboPi 路径 =====
echo "=== TurboPi 路径检查 ==="
TURBOPI_FOUND=0

if [ -n "$TURBOPI_PATH" ] && [ -d "$TURBOPI_PATH" ]; then
    echo -e "${GREEN}✓${NC} TURBOPI_PATH: $TURBOPI_PATH"
    TURBOPI_FOUND=1
elif [ -d "./TurboPi" ]; then
    echo -e "${GREEN}✓${NC} ./TurboPi (项目相对路径)"
    TURBOPI_FOUND=1
elif [ -d "/home/pi/TurboPi" ]; then
    echo -e "${GREEN}✓${NC} /home/pi/TurboPi (标准路径)"
    TURBOPI_FOUND=1
else
    echo -e "${YELLOW}⚠${NC} TurboPi 路径未找到"
    echo -e "    解决方案:"
    echo -e "    1. 设置环境变量: ${BLUE}export TURBOPI_PATH=/path/to/TurboPi${NC}"
    echo -e "    2. 创建符号链接: ${BLUE}ln -s /path/to/TurboPi ./TurboPi${NC}"
    echo -e "    3. 或启用模拟模式: ${BLUE}export MOCK_HARDWARE=true${NC}"
fi
echo ""

# ===== 检查权限 =====
echo "=== 权限检查 ==="
if groups | grep -q "video"; then
    echo -e "${GREEN}✓${NC} 用户在 video 组 (摄像头权限)"
else
    echo -e "${YELLOW}⚠${NC} 用户不在 video 组，可能无法访问摄像头"
    echo -e "    解决方案: ${BLUE}sudo usermod -a -G video \$USER${NC}"
fi

if [ -c /dev/i2c-1 ]; then
    if groups | grep -q "i2c"; then
        echo -e "${GREEN}✓${NC} 用户在 i2c 组 (I2C权限)"
    else
        echo -e "${YELLOW}⚠${NC} 用户不在 i2c 组，可能无法访问I2C设备"
        echo -e "    解决方案: ${BLUE}sudo usermod -a -G i2c \$USER${NC}"
    fi
fi
echo ""

# ===== 检查 I2C 和 SPI 接口 =====
if [ $IS_RPI -eq 1 ]; then
    echo "=== 接口检查 ==="
    if [ -d /sys/class/i2c-dev ]; then
        echo -e "${GREEN}✓${NC} I2C 接口已启用"
    else
        echo -e "${RED}✗${NC} I2C 接口未启用"
        echo -e "    解决方案: ${BLUE}sudo raspi-config nonint do_i2c 0${NC}"
    fi

    if [ -d /sys/class/spidev ]; then
        echo -e "${GREEN}✓${NC} SPI 接口已启用"
    else
        echo -e "${YELLOW}⚠${NC} SPI 接口未启用"
        echo -e "    解决方案: ${BLUE}sudo raspi-config nonint do_spi 0${NC}"
    fi
    echo ""
fi

# ===== 总结 =====
echo "======================================"
echo "  检查结果汇总"
echo "======================================"
echo -e "总计: $TOTAL | ${GREEN}通过: $PASS${NC} | ${RED}失败: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}所有依赖已就绪！可以运行 ./vehicle-start.sh 启动服务${NC}"
    exit 0
else
    echo -e "\n${YELLOW}缺少 $FAIL 个依赖${NC}"
    echo ""
    echo "快速安装命令:"
    if [ $IS_RPI -eq 1 ]; then
        echo "  pip3 install RPi.GPIO smbus2 rpi-ws281x"
    fi
    echo "  pip3 install -e ."
    echo ""
    echo "或运行: ./vehicle-start.sh (自动安装并启动)"
    exit 1
fi
