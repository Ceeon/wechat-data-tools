#!/bin/bash
set -e

echo "=========================================="
echo "🚀 微信公众号数据监控系统启动中..."
echo "=========================================="

# 检查配置文件是否存在
if [ ! -f "/app/config/config.yaml" ]; then
    echo "⚠️  警告：未找到 config.yaml 配置文件"
    echo "请确保配置文件存在于 ./config/config.yaml"
fi

# 创建必要的目录
mkdir -p /app/logs /app/data/articles /app/reports

# 启动 cron 服务
echo "📅 启动定时任务服务..."
service cron start

# 检查 cron 状态
if service cron status > /dev/null 2>&1; then
    echo "✅ 定时任务服务已启动"
    echo "⏰ 任务调度：每天早上 9:00 执行数据采集"
else
    echo "❌ 定时任务服务启动失败"
    exit 1
fi

# 显示 crontab 配置
echo ""
echo "📋 定时任务配置："
crontab -l

# 显示当前时间
echo ""
echo "🕐 当前时间：$(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "=========================================="
echo "✅ 系统已就绪，等待定时任务触发..."
echo "=========================================="
echo ""
echo "💡 提示："
echo "  - 查看日志：docker-compose logs -f"
echo "  - 手动执行：docker-compose exec wechat-monitor python3 scripts/daily_auto_workflow.py"
echo "  - 查看报表：open ./reports/all_articles.html"
echo ""

# 保持容器运行，并输出 cron 日志
tail -f /var/log/cron.log /app/logs/*.log 2>/dev/null || tail -f /dev/null
