#!/bin/bash
# 车载服务启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/vehicle"

echo "=== 启动Blockly车载服务 ==="

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv未安装"
    echo "请运行: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 设置环境变量
export VEHICLE_ID=${VEHICLE_ID:-vehicle-001}
export CLOUD_GATEWAY_URL=${CLOUD_GATEWAY_URL:-wss://lanser.fun/block/ws/gateway}
export FLASK_ENV=${FLASK_ENV:-production}
export MOCK_HARDWARE=${MOCK_HARDWARE:-true}
export TURBOPI_PATH=${TURBOPI_PATH:-./TurboPi}

echo "配置:"
echo "  VEHICLE_ID: $VEHICLE_ID"
echo "  CLOUD_GATEWAY_URL: $CLOUD_GATEWAY_URL"
echo "  MOCK_HARDWARE: $MOCK_HARDWARE"
echo ""

# 安装依赖
echo "安装依赖..."
uv sync

# 启动服务
echo "启动车载服务..."
uv run python app.py
