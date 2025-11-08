#!/bin/bash

# ArtIntellect 启动脚本

echo "🚀 启动 ArtIntellect..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📚 安装依赖..."
pip install -q -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    echo "❗ 请编辑 .env 文件并设置你的 MS_API_KEY"
    exit 1
fi

# 启动应用
echo "🎉 启动 FastAPI 服务器..."
python main.py
