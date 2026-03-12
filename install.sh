#!/bin/bash
echo "=============================================="
echo "4S店汽车销售线索自动获取系统 - 一键安装脚本"
echo "=============================================="

# 检查系统类型
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "检测到Windows系统，请使用install.bat进行安装"
    pause
    exit 1
fi

# 检查Python版本
echo "检查Python版本..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.10"

if [ $(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc) -ne 1 ]; then
    echo "错误: Python版本过低，需要Python $REQUIRED+，当前版本: $PYTHON_VERSION"
    echo "请先升级Python版本后重试"
    exit 1
fi
echo "Python版本检查通过: $PYTHON_VERSION"

# 更新包管理器
echo ""
echo "更新系统依赖..."
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3-pip python3-venv libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
elif command -v yum &> /dev/null; then
    sudo yum update
    sudo yum install -y python3-pip python3-venv glib2 nss nspr atk at-spi2-atk cups-libs libdrm dbus-libs libxkbcommon libXcomposite libXdamage libXfixes libXrandr mesa-libgbm pango cairo alsa-lib
elif command -v brew &> /dev/null; then
    brew install python3
fi

# 创建虚拟环境
echo ""
echo "创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
echo ""
echo "安装Python依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 安装Playwright浏览器
echo ""
echo "安装Playwright浏览器..."
playwright install chromium
playwright install-deps chromium

# 复制环境变量模板
if [ ! -f ".env" ]; then
    echo ""
    echo "复制环境变量模板..."
    cp .env.example .env
fi

# 创建必要的目录
echo ""
echo "创建目录结构..."
mkdir -p data/logs/tasks
mkdir -p data/backup

# 设置执行权限
echo ""
echo "设置脚本执行权限..."
chmod +x scripts/*.sh
chmod +x install.sh

echo ""
echo "=============================================="
echo "安装完成！"
echo "=============================================="
echo ""
echo "下一步操作："
echo "1. 编辑 .env 文件，配置相关API密钥"
echo "2. 编辑 config/settings.yaml，配置平台账号和监控视频"
echo "3. 运行 ./scripts/start.sh 启动系统"
echo ""
echo "如果需要配置OpenClaw定时任务，请参考README.md中的说明"
echo ""