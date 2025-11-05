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

# 初始化数据库（如果不存在）
if [ ! -f "/app/data/wechat_monitor.db" ]; then
    echo "🗄️  数据库不存在，正在初始化..."
    if [ -d "/app/data/articles" ] && [ "$(ls -A /app/data/articles)" ]; then
        echo "📦 发现现有文章数据，正在迁移到数据库..."
        python3 /app/scripts/migrate_to_db.py
        if [ $? -eq 0 ]; then
            echo "✅ 数据迁移成功"
        else
            echo "⚠️  数据迁移失败，将创建空数据库"
            python3 -c "from scripts.utils.database import WechatDatabase; WechatDatabase('/app/data/wechat_monitor.db')"
        fi
    else
        echo "📝 创建空数据库..."
        python3 -c "from scripts.utils.database import WechatDatabase; WechatDatabase('/app/data/wechat_monitor.db')"
        echo "✅ 数据库创建成功"
    fi
else
    echo "✅ 数据库已存在：/app/data/wechat_monitor.db"
fi

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
