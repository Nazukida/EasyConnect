#!/bin/bash
echo "========================================"
echo "  EasyConnect - 局域网文件传输工具"
echo "========================================"
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "[提示] 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[提示] 正在安装依赖包..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "[提示] 正在启动 EasyConnect..."
echo
python3 main.py
