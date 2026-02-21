#!/bin/bash
# Blockly小车车载服务启动脚本
# 自动检查并安装依赖，然后启动服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================"
echo "  Blockly小车车载服务启动中..."
echo "======================================"

# 检查是否在 Raspberry Pi 上运行
IS_RPI=0
if [ -f /proc/device-tree/model ]; then
    MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "")
    if echo "$MODEL" | grep -qi "raspberry pi"; then
        IS_RPI=1
        echo -e "${GREEN}✓ 检测到 Raspberry Pi 硬件${NC}"
    fi
fi

# 检查是否启用了 MOCK_HARDWARE
if [ "$MOCK_HARDWARE" = "true" ]; then
    echo -e "${YELLOW}⚠ MOCK_HARDWARE=true，使用模拟模式${NC}"
    IS_RPI=0
fi

# 检查权限（仅 Raspberry Pi）
NEED_SUDO=0
if [ $IS_RPI -eq 1 ]; then
    echo ""
    echo "检查硬件权限..."

    # 检查 /dev/mem 访问权限
    if [ -r /dev/mem ]; then
        echo -e "${GREEN}✓ /dev/mem 可读${NC}"
    else
        echo -e "${RED}✗ /dev/mem 不可读${NC}"
        NEED_SUDO=1
    fi

    # 检查用户组
    CURRENT_USER=$(whoami)
    if groups "$CURRENT_USER" | grep -q '\bgpio\b'; then
        echo -e "${GREEN}✓ 用户在 gpio 组${NC}"
    else
        echo -e "${YELLOW}⚠ 用户不在 gpio 组${NC}"
        NEED_SUDO=1
    fi

    if groups "$CURRENT_USER" | grep -q '\bvideo\b'; then
        echo -e "${GREEN}✓ 用户在 video 组${NC}"
    else
        echo -e "${YELLOW}⚠ 用户不在 video 组（摄像头可能无法使用）${NC}"
    fi

    # 如果需要 sudo，提示用户
    if [ $NEED_SUDO -eq 1 ]; then
        echo ""
        echo -e "${YELLOW}⚠ 检测到权限不足，可能的解决方案：${NC}"
        echo ""
        echo "1. 添加用户到必要的组（推荐，需要重新登录）："
        echo -e "   ${BLUE}sudo usermod -a -G gpio,video,i2c \$USER${NC}"
        echo "   然后重新登录或运行: ${BLUE}su - \$USER${NC}"
        echo ""
        echo "2. 使用 sudo 启动服务："
        echo -e "   ${BLUE}sudo ./vehicle-start.sh${NC}"
        echo ""
    fi
    echo ""
fi

# ===== 虚拟环境设置 =====
echo "检查虚拟环境..."

# 检查虚拟环境是否需要重建（需要 --system-site-packages 来访问系统包如 smbus）
NEED_RECREATE_VENV=0
if [ ! -d ".venv" ]; then
    NEED_RECREATE_VENV=1
else
    # 检查 pyvenv.cfg 是否包含 system-site-packages=true
    if [ -f ".venv/pyvenv.cfg" ]; then
        if ! grep -q "system-site-packages = true" .venv/pyvenv.cfg 2>/dev/null; then
            NEED_RECREATE_VENV=1
        fi
    else
        NEED_RECREATE_VENV=1
    fi
fi

if [ $NEED_RECREATE_VENV -eq 1 ]; then
    echo -e "${YELLOW}⚠ 虚拟环境需要重建（需要 --system-site-packages 来访问硬件包）${NC}"
    echo "正在重建虚拟环境..."

    # 备份旧的虚拟环境
    if [ -d ".venv" ]; then
        mv .venv .venv.backup.$(date +%s)
    fi

    # 使用 uv 创建带系统站点包的虚拟环境
    if command -v uv &> /dev/null; then
        uv venv --system-site-packages
    else
        python3 -m venv --system-site-packages .venv
    fi
    echo -e "${GREEN}✓ 虚拟环境已重建${NC}"
fi

# 检查并安装系统硬件包（仅 Raspberry Pi）
if [ $IS_RPI -eq 1 ]; then
    echo ""
    echo "检查系统硬件包..."

    # 检查 python3-smbus
    if ! dpkg -l | grep -q "python3-smbus"; then
        echo -e "${YELLOW}⚠ python3-smbus 未安装，正在安装...${NC}"
        sudo apt-get update
        sudo apt-get install -y python3-smbus python3-dev
    else
        echo -e "${GREEN}✓ python3-smbus 已安装${NC}"
    fi

    # 检查 python3-rpi.gpio
    if ! dpkg -l | grep -q "python3-rpi.gpio"; then
        echo -e "${YELLOW}⚠ python3-rpi.gpio 未安装，正在安装...${NC}"
        sudo apt-get install -y python3-rpi.gpio
    else
        echo -e "${GREEN}✓ python3-rpi.gpio 已安装${NC}"
    fi

    echo ""
fi

# 使用 uv 同步依赖
echo "同步 Python 依赖..."
if command -v uv &> /dev/null; then
    if [ $IS_RPI -eq 1 ]; then
        # Raspberry Pi: 安装包括 hardware 组的依赖
        uv sync --group hardware
    else
        # 非硬件环境: 只安装基础依赖
        uv sync
    fi
else
    echo -e "${YELLOW}⚠ uv 未安装，跳过依赖同步${NC}"
fi
echo ""

# 检查端口占用
PORT=5000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ 端口 $PORT 已被占用，尝试停止现有服务...${NC}"
    if [ $NEED_SUDO -eq 1 ]; then
        sudo pkill -f "gunicorn.*wsgi:app" || true
    else
        pkill -f "gunicorn.*wsgi:app" || true
    fi
    sleep 2
fi

# 启动服务
echo "======================================"
echo "  启动车载服务..."
echo "======================================"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 使用 sudo 启动（如果需要）
if [ $NEED_SUDO -eq 1 ]; then
    echo -e "${YELLOW}使用 sudo 启动服务...${NC}"
    sudo -E uv run gunicorn --config config/gunicorn.conf.py wsgi:app
else
    uv run gunicorn --config config/gunicorn.conf.py wsgi:app
fi
