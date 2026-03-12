@echo off
chcp 65001 >nul
echo ==============================================
echo 4S店汽车销售线索自动获取系统 - 停止脚本
echo ==============================================

:: 查找并停止Python进程
echo 正在停止系统进程...
taskkill /f /im python.exe /fi "windowtitle eq 4s-auto-leads*" >nul 2>&1
taskkill /f /im pythonw.exe /fi "windowtitle eq 4s-auto-leads*" >nul 2>&1

:: 停止OpenClaw任务
echo 正在停止OpenClaw监控任务...
openclaw cron stop douyin_monitor >nul 2>&1
openclaw cron stop kuaishou_monitor >nul 2>&1
openclaw cron stop xiaohongshu_monitor >nul 2>&1

echo.
echo 系统已停止
pause
exit /b 0