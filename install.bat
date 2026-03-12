@echo off
chcp 65001 >nul
echo ==============================================
echo 4S店汽车销售线索自动获取系统 - 一键安装脚本
echo ==============================================

:: 检查Python版本
echo 检查Python版本...
for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
set REQUIRED_VERSION=3.10

for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do set PYTHON_MAJOR=%%a&set PYTHON_MINOR=%%b
for /f "tokens=1,2 delims=." %%a in ("%REQUIRED_VERSION%") do set REQUIRED_MAJOR=%%a&set REQUIRED_MINOR=%%b

if %PYTHON_MAJOR% LSS %REQUIRED_MAJOR% (
    echo 错误: Python版本过低，需要Python %REQUIRED_VERSION%+，当前版本: %PYTHON_VERSION%
    echo 请先安装Python %REQUIRED_VERSION% 或更高版本
    pause
    exit /b 1
)

if %PYTHON_MAJOR% EQU %REQUIRED_MAJOR% if %PYTHON_MINOR% LSS %REQUIRED_MINOR% (
    echo 错误: Python版本过低，需要Python %REQUIRED_VERSION%+，当前版本: %PYTHON_VERSION%
    echo 请先安装Python %REQUIRED_VERSION% 或更高版本
    pause
    exit /b 1
)
echo Python版本检查通过: %PYTHON_VERSION%

:: 创建虚拟环境
echo.
echo 创建Python虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

:: 安装Python依赖
echo.
echo 安装Python依赖包...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 安装Playwright浏览器
echo.
echo 安装Playwright浏览器...
playwright install chromium
playwright install-deps chromium

:: 复制环境变量模板
if not exist ".env" (
    echo.
    echo 复制环境变量模板...
    copy .env.example .env
)

:: 创建必要的目录
echo.
echo 创建目录结构...
if not exist "data\logs\tasks" mkdir data\logs\tasks
if not exist "data\backup" mkdir data\backup

:: 设置执行权限
echo.
echo 设置脚本执行权限...
icacls scripts\*.bat /grant Everyone:F >nul

echo.
echo ==============================================
echo 安装完成！
echo ==============================================
echo.
echo 下一步操作：
echo 1. 编辑 .env 文件，配置相关API密钥
echo 2. 编辑 config\settings.yaml，配置平台账号和监控视频
echo 3. 双击 scripts\start.bat 启动系统
echo.
echo 如果需要配置OpenClaw定时任务，请参考README.md中的说明
echo.
pause
exit /b 0