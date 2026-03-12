#!/bin/bash
echo "=============================================="
echo "4S店汽车销售线索自动获取系统 - 启动脚本"
echo "=============================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python3，请先安装Python 3.10+"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查依赖是否安装
echo "检查依赖包..."
if ! python3 -c "import playwright, yaml, dotenv" &> /dev/null; then
    echo "依赖未安装，正在安装依赖..."
    pip3 install -r requirements.txt
    echo "安装Playwright浏览器..."
    playwright install chromium
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "警告: 未找到.env文件，正在复制模板..."
    cp .env.example .env
    echo "请编辑.env文件配置相关密钥后重新启动"
    nano .env
    exit 1
fi

# 创建必要的目录
echo "初始化目录结构..."
mkdir -p data/logs/tasks

echo ""
echo "启动系统..."
echo "按Ctrl+C可以停止系统"
echo ""

# 启动主程序
python3 main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "程序异常退出，请检查错误信息"
    exit 1
fi

exit 0