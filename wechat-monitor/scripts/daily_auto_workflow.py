#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动化工作流
功能:
1. 从RSS采集昨天发布的文章
2. 获取前1-2天发布文章的互动数据
3. 生成每日数据展示页面
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "scripts"))


def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def run_command(description, command, cwd=None):
    """
    运行命令并返回是否成功

    Args:
        description: 步骤描述
        command: 要执行的命令列表
        cwd: 工作目录

    Returns:
        bool: 是否成功
    """
    log(f">>> {description}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT / "scripts",
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            log(f"✅ {description} - 成功")
            return True
        else:
            log(f"❌ {description} - 失败")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        log(f"❌ {description} - 异常: {e}")
        return False


def main():
    """主流程"""
    log("=" * 60)
    log("🚀 开始每日自动化工作流")
    log("=" * 60)

    # 步骤1: 从RSS采集昨天发布的文章
    log("\n📥 步骤1: 从RSS采集昨天发布的文章")
    success_fetch = run_command(
        "采集昨天的文章",
        [sys.executable, "daily_fetch.py", "--mode", "yesterday"]
    )

    if not success_fetch:
        log("⚠️  文章采集失败，但继续执行后续步骤")

    # 步骤2: 同步新文章到数据库
    log("\n🗄️  步骤2: 同步新文章到数据库")
    db_path = PROJECT_ROOT / "data" / "wechat_monitor.db"

    if db_path.exists():
        success_sync = run_command(
            "同步文章数据到数据库",
            [sys.executable, "migrate_to_db.py"]
        )
        if not success_sync:
            log("⚠️  数据库同步失败，但继续执行后续步骤")
    else:
        log("ℹ️  数据库不存在，跳过同步步骤")

    # 步骤3: 获取前1-2天发布文章的互动数据
    log("\n📊 步骤3: 获取前1-2天发布文章的互动数据")

    # 使用fetch_article_stats.py的自动模式
    # 创建一个临时脚本来获取前1-2天的数据
    stats_script = PROJECT_ROOT / "scripts" / "fetch_recent_stats.py"

    # 如果临时脚本不存在，使用fetch_article_stats.py
    success_stats = run_command(
        "获取互动数据(前1-2天发布的文章)",
        [sys.executable, "fetch_recent_days_stats.py"]
    )

    if not success_stats:
        log("⚠️  互动数据获取失败，但继续执行后续步骤")

    # 步骤4: 同步统计数据到数据库
    if db_path.exists():
        log("\n🗄️  步骤4: 同步统计数据到数据库")
        success_sync = run_command(
            "同步统计数据到数据库",
            [sys.executable, "migrate_to_db.py"]
        )
        if not success_sync:
            log("⚠️  统计数据同步失败，但继续生成报表")
    else:
        log("ℹ️  数据库不存在，跳过同步步骤")

    # 步骤5: 生成每日数据展示页面
    log("\n📄 步骤5: 生成每日数据展示页面")
    success_report = run_command(
        "生成数据报表",
        [sys.executable, "generate_report.py"]
    )

    if not success_report:
        log("❌ 报表生成失败")
        return False

    # 步骤6: 生成爆款警报
    log("\n🚨 步骤6: 生成爆款警报")
    success_alert = run_command(
        "检测爆款文章",
        [sys.executable, "viral_alert.py"]
    )

    if not success_alert:
        log("⚠️  爆款警报生成失败，但不影响主流程")

    # 完成
    log("\n" + "=" * 60)
    log("✅ 每日自动化工作流完成!")
    log("=" * 60)

    # 显示报表位置
    report_file = PROJECT_ROOT / "reports" / "all_articles.html"
    viral_alert_file = PROJECT_ROOT / "reports" / "viral_alert.html"

    log("\n📊 生成的报表:")
    if report_file.exists():
        log(f"  • 全部文章: {report_file}")
    if viral_alert_file.exists():
        log(f"  • 爆款警报: {viral_alert_file}")
    log(f"\n🌐 在浏览器中打开查看")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
