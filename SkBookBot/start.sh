#!/bin/bash
# SkBookBot 启动脚本

cd "$(dirname "$0")"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查并安装依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
fi

# 创建数据目录
mkdir -p data logs

# 启动
echo "启动 SkBookBot..."
python3 main.py