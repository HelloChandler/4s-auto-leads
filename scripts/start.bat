@echo off
chcp 65001 >nul
echo ==============================================
echo 4S店汽车销售线索自动获取系统 - 启动脚本
echo ==============================================

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

:: 检查是否在正确的目录
if not exist "requirements.txt" (
    echo 错误: 请在项目根目录下运行此脚本
    pause
    exit /b 1
)

:: 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 检查依赖是否安装
echo 检查依赖包...
python -c "import playwright, yaml, dotenv" >nul 2>&1
if %errorlevel% neq 0 (
    echo 依赖未安装，正在安装依赖...
    pip install -r requirements.txt
    echo 安装Playwright浏览器...
    playwright install chromium
)

:: 检查环境变量文件
if not exist ".env" (
    echo 警告: 未找到.env文件，正在复制模板...
    copy .env.example .env
    echo 请编辑.env文件配置相关密钥后重新启动
    notepad .env
    pause
    exit /b 1
)

:: 创建必要的目录
echo 初始化目录结构...
if not exist "data\logs\tasks" mkdir data\logs\tasks

echo.
echo 启动系统...
echo 按Ctrl+C可以停止系统
echo.

:: 启动主程序
python main.py

if %errorlevel% neq 0 (
    echo.
    echo 程序异常退出，请检查错误信息
    pause
)

exit /b 0