#!/bin/bash
echo "=============================================="
echo "4S店汽车销售线索自动获取系统 - 停止脚本"
echo "=============================================="

# 查找并停止Python进程
echo "正在停止系统进程..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python3.*main.py" 2>/dev/null

# 停止OpenClaw任务
echo "正在停止OpenClaw监控任务..."
openclaw cron stop douyin_monitor 2>/dev/null
openclaw cron stop kuaishou_monitor 2>/dev/null
openclaw cron stop xiaohongshu_monitor 2>/dev/null

echo ""
echo "系统已停止"
exit 0