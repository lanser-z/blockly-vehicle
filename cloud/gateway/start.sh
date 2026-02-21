#!/bin/bash
# 云端网关服务启动脚本

cd "$(dirname "$0")"

echo "=== 启动Blockly云端网关服务 ==="

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv未安装"
    echo "请运行: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 请在cloud/gateway目录下运行此脚本"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
uv sync

# 启动服务
echo "启动网关服务..."
uv run uvicorn main:app --host 127.0.0.1 --port 5001
