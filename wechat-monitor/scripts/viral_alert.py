#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爆款警报系统
功能: 检测最近获取数据的文章中的爆款(超过该公众号平均阅读和互动率的文章)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent


def scan_recent_articles(articles_dir: Path, days: int = 30) -> List[Dict]:
    """
    扫描最近N天的文章

    Args:
        articles_dir: 文章目录
        days: 扫描最近多少天的文章

    Returns:
        文章列表
    """
    articles = []
    cutoff_date = datetime.now() - timedelta(days=days)

    for article_folder in articles_dir.glob("*"):
        if not article_folder.is_dir():
            continue

        # 解析文件夹名称: 20251018_033536_id_title
        parts = article_folder.name.split('_')
        if len(parts) < 4:
            continue

        date_str = parts[0]  # 20251018

        # 检查日期是否在范围内
        try:
            article_date = datetime.strptime(date_str, '%Y%m%d')
            if article_date < cutoff_date:
                continue
        except ValueError:
            continue

        # 读取元数据
        metadata_file = article_folder / "metadata.json"
        if not metadata_file.exists():
            continue

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 读取最新统计数据
        stats_metadata_file = article_folder / "stats_metadata.json"
        stats_history_file = article_folder / "stats_history.json"

        latest_stats = None
        stats_history = []

        if stats_history_file.exists():
            with open(stats_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                stats_history = history_data.get('history', [])
                if stats_history:
                    latest_stats = stats_history[-1]  # 最后一个是最新的
        elif stats_metadata_file.exists():
            with open(stats_metadata_file, 'r', encoding='utf-8') as f:
                latest_stats = json.load(f)

        if not latest_stats:
            continue

        # 组合文章数据
        article_data = {
            'folder_name': article_folder.name,
            'title': metadata.get('title', ''),
            'account_name': metadata.get('account_name', ''),
            'category': metadata.get('category', ''),
            'publish_time': metadata.get('publish_time', ''),
            'url': metadata.get('url', ''),
            'latest_stats': latest_stats,
            'stats_history': stats_history
        }

        articles.append(article_data)

    return articles


def calculate_account_baselines(articles: List[Dict]) -> Dict[str, Dict]:
    """
    计算每个公众号的基准指标

    Args:
        articles: 文章列表

    Returns:
        公众号基准指标字典 {account_name: {avg_read, avg_looking_rate, avg_share_rate, ...}}
    """
    account_stats = defaultdict(lambda: {
        'read_nums': [],
        'looking_rates': [],
        'share_rates': []
    })

    for article in articles:
        account_name = article['account_name']
        latest_stats = article['latest_stats']

        read_num = latest_stats.get('read_num', 0)
        looking_num = latest_stats.get('looking_num', 0)
        share_num = latest_stats.get('share_num', 0)

        if read_num > 0:
            account_stats[account_name]['read_nums'].append(read_num)
            account_stats[account_name]['looking_rates'].append(looking_num / read_num)
            account_stats[account_name]['share_rates'].append(share_num / read_num)

    # 计算平均值
    baselines = {}
    for account_name, stats in account_stats.items():
        if stats['read_nums']:
            baselines[account_name] = {
                'avg_read': sum(stats['read_nums']) / len(stats['read_nums']),
                'avg_looking_rate': sum(stats['looking_rates']) / len(stats['looking_rates']),
                'avg_share_rate': sum(stats['share_rates']) / len(stats['share_rates']),
                'article_count': len(stats['read_nums'])
            }

    return baselines


def detect_viral_articles(articles: List[Dict], baselines: Dict[str, Dict], debug: bool = False) -> List[Dict]:
    """
    检测爆款文章

    检测条件:
    1. 最新数据是最近3天内获取的
    2. 阅读量 >= 该号平均 × 3
    3. 在看率或分享率 >= 该号平均 × 2

    Args:
        articles: 文章列表
        baselines: 公众号基准指标
        debug: 是否输出调试信息

    Returns:
        爆款文章列表
    """
    viral_articles = []
    today = datetime.now().date()

    # 扩大到最近3天
    target_dates = [
        (today - timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(3)
    ]

    if debug:
        print(f"\n调试: 目标日期 = {target_dates}")
        print(f"调试: 总文章数 = {len(articles)}")

    articles_with_recent_data = 0

    for article in articles:
        account_name = article['account_name']
        latest_stats = article['latest_stats']

        # 检查是否有基准数据
        if account_name not in baselines:
            continue

        baseline = baselines[account_name]

        # 检查最新数据的获取日期
        fetched_date = latest_stats.get('fetched_date', '')

        if debug and articles_with_recent_data < 5:
            print(f"调试: {article['title'][:30]}... | fetched_date={fetched_date}")

        if fetched_date not in target_dates:
            continue

        articles_with_recent_data += 1

        # 计算指标
        read_num = latest_stats.get('read_num', 0)
        looking_num = latest_stats.get('looking_num', 0)
        share_num = latest_stats.get('share_num', 0)

        if read_num == 0:
            continue

        looking_rate = looking_num / read_num
        share_rate = share_num / read_num

        # 判断是否为爆款
        read_multiplier = read_num / baseline['avg_read'] if baseline['avg_read'] > 0 else 0
        looking_rate_multiplier = looking_rate / baseline['avg_looking_rate'] if baseline['avg_looking_rate'] > 0 else 0
        share_rate_multiplier = share_rate / baseline['avg_share_rate'] if baseline['avg_share_rate'] > 0 else 0

        # 爆款条件
        is_viral = False
        viral_tags = []

        # 条件1: 阅读量超过平均3倍
        if read_multiplier >= 3:
            is_viral = True
            viral_tags.append(f"🔥 {read_multiplier:.1f}x阅读")

        # 条件2: 在看率超过平均2倍
        if looking_rate_multiplier >= 2:
            is_viral = True
            viral_tags.append(f"👀 {looking_rate_multiplier:.1f}x在看率")

        # 条件3: 分享率超过平均2倍
        if share_rate_multiplier >= 2:
            is_viral = True
            viral_tags.append(f"📤 {share_rate_multiplier:.1f}x分享率")

        if is_viral:
            viral_article = {
                **article,
                'read_multiplier': read_multiplier,
                'looking_rate_multiplier': looking_rate_multiplier,
                'share_rate_multiplier': share_rate_multiplier,
                'viral_tags': viral_tags,
                'baseline_read': baseline['avg_read'],
                'baseline_looking_rate': baseline['avg_looking_rate'],
                'baseline_share_rate': baseline['avg_share_rate']
            }
            viral_articles.append(viral_article)

    if debug:
        print(f"调试: 最近3天内有数据的文章 = {articles_with_recent_data}")
        print(f"调试: 检测到爆款文章 = {len(viral_articles)}")

    # 按爆款倍数排序
    viral_articles.sort(key=lambda x: x['read_multiplier'], reverse=True)

    return viral_articles


def generate_html_report(viral_articles: List[Dict], output_file: Path):
    """
    生成HTML警报报告

    Args:
        viral_articles: 爆款文章列表
        output_file: 输出文件路径
    """
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>爆款警报 - 微信公众号监控</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .viral-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.25rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .viral-card {{
            background: linear-gradient(135deg, #fff 0%, #f8f9ff 100%);
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }}

        .viral-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
        }}

        .stat-increase {{
            color: #10b981;
            font-weight: 600;
        }}
    </style>
</head>
<body class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6 md:p-10">
    <div class="max-w-6xl mx-auto">
        <!-- 标题 -->
        <div class="bg-white rounded-2xl shadow-lg p-8 mb-8 border border-blue-100">
            <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
                🚨 爆款警报
            </h1>
            <div class="flex items-center justify-between">
                <p class="text-slate-600 text-lg">
                    检测时间: {generate_time}
                </p>
                <div class="text-right">
                    <p class="text-3xl font-bold text-blue-600">{viral_count}</p>
                    <p class="text-sm text-slate-500">篇爆款文章</p>
                </div>
            </div>
        </div>

        <!-- 说明 -->
        <div class="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
            <h2 class="text-lg font-semibold text-blue-900 mb-3">🎯 爆款判断标准</h2>
            <ul class="space-y-2 text-blue-800">
                <li>✅ 阅读量超过该公众号平均的 <strong>3倍</strong></li>
                <li>✅ 在看率超过该公众号平均的 <strong>2倍</strong></li>
                <li>✅ 分享率超过该公众号平均的 <strong>2倍</strong></li>
            </ul>
            <p class="mt-4 text-sm text-blue-700">
                💡 数据来源：最近1-2天内新获取的文章统计数据
            </p>
        </div>

        <!-- 爆款文章列表 -->
        {viral_articles_html}

        <!-- 空状态 -->
        {empty_state}
    </div>
</body>
</html>
"""

    # 生成爆款文章HTML
    viral_articles_html = []

    for idx, article in enumerate(viral_articles, 1):
        latest_stats = article['latest_stats']

        read_num = latest_stats.get('read_num', 0)
        like_num = latest_stats.get('like_num', 0)
        looking_num = latest_stats.get('looking_num', 0)
        comment_num = latest_stats.get('in_comment_num', 0)
        share_num = latest_stats.get('share_num', 0)
        collect_num = latest_stats.get('collect_num', 0)
        fetched_date = latest_stats.get('fetched_date', '')

        # 徽章
        tags_html = ''.join([f'<span class="viral-badge">{tag}</span>' for tag in article['viral_tags']])

        # 对比数据
        baseline_read = article['baseline_read']
        read_vs_avg = f"{read_num:,} (平均: {baseline_read:,.0f})"

        looking_rate = (looking_num / read_num * 100) if read_num > 0 else 0
        baseline_looking_rate = article['baseline_looking_rate'] * 100
        looking_vs_avg = f"{looking_rate:.2f}% (平均: {baseline_looking_rate:.2f}%)"

        share_rate = (share_num / read_num * 100) if read_num > 0 else 0
        baseline_share_rate = article['baseline_share_rate'] * 100
        share_vs_avg = f"{share_rate:.2f}% (平均: {baseline_share_rate:.2f}%)"

        card_html = f"""
        <div class="viral-card rounded-xl shadow-md p-6 mb-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                        <span class="text-2xl font-bold text-slate-400">#{idx}</span>
                        <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                            {article['account_name']}
                        </span>
                        <span class="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium">
                            {article['category']}
                        </span>
                    </div>
                    <h3 class="text-xl font-bold text-slate-800 mb-3 leading-relaxed">
                        <a href="{article['url']}" target="_blank" class="hover:text-blue-600 transition-colors">
                            {article['title']}
                        </a>
                    </h3>
                    <div class="flex flex-wrap gap-2 mb-4">
                        {tags_html}
                    </div>
                </div>
            </div>

            <!-- 数据对比 -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white rounded-lg p-4 border border-slate-200">
                <div>
                    <p class="text-xs text-slate-500 mb-1">阅读数</p>
                    <p class="text-lg font-bold text-blue-600">{read_num:,}</p>
                    <p class="text-xs text-slate-400">平均: {baseline_read:,.0f}</p>
                </div>
                <div>
                    <p class="text-xs text-slate-500 mb-1">在看率</p>
                    <p class="text-lg font-bold text-green-600">{looking_rate:.2f}%</p>
                    <p class="text-xs text-slate-400">平均: {baseline_looking_rate:.2f}%</p>
                </div>
                <div>
                    <p class="text-xs text-slate-500 mb-1">分享率</p>
                    <p class="text-lg font-bold text-purple-600">{share_rate:.2f}%</p>
                    <p class="text-xs text-slate-400">平均: {baseline_share_rate:.2f}%</p>
                </div>
                <div>
                    <p class="text-xs text-slate-500 mb-1">数据日期</p>
                    <p class="text-lg font-bold text-slate-700">{fetched_date[5:]}</p>
                    <p class="text-xs text-slate-400">点赞: {like_num} | 评论: {comment_num}</p>
                </div>
            </div>
        </div>
        """
        viral_articles_html.append(card_html)

    # 空状态
    empty_state = ""
    if not viral_articles:
        empty_state = """
        <div class="bg-white rounded-2xl shadow-lg p-16 text-center">
            <div class="text-6xl mb-4">😌</div>
            <h2 class="text-2xl font-bold text-slate-700 mb-2">暂无爆款文章</h2>
            <p class="text-slate-500">最近1-2天内没有检测到符合爆款标准的文章</p>
        </div>
        """

    # 生成HTML
    html = html_template.format(
        generate_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        viral_count=len(viral_articles),
        viral_articles_html='\n'.join(viral_articles_html),
        empty_state=empty_state
    )

    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def print_terminal_summary(viral_articles: List[Dict]):
    """
    在终端输出警报摘要

    Args:
        viral_articles: 爆款文章列表
    """
    print("\n" + "="*80)
    print("🚨 爆款警报！")
    print("="*80)

    if not viral_articles:
        print("\n😌 暂无爆款文章")
        print("   最近1-2天内没有检测到符合爆款标准的文章\n")
        return

    print(f"\n检测到 {len(viral_articles)} 篇爆款文章：\n")

    for idx, article in enumerate(viral_articles[:10], 1):  # 只显示前10篇
        latest_stats = article['latest_stats']
        read_num = latest_stats.get('read_num', 0)
        tags = ' '.join(article['viral_tags'])

        print(f"{idx}. [{article['account_name']}] {article['title']}")
        print(f"   → {read_num:,}阅读 | {tags}")
        print()

    if len(viral_articles) > 10:
        print(f"... 还有 {len(viral_articles) - 10} 篇爆款文章，详见HTML报告\n")

    print("="*80 + "\n")


def main(debug: bool = False):
    """主函数"""
    print("📊 开始扫描文章...")

    # 扫描最近30天的文章
    articles_dir = PROJECT_ROOT / "data" / "articles"
    articles = scan_recent_articles(articles_dir, days=30)

    print(f"✅ 扫描到 {len(articles)} 篇文章")

    if not articles:
        print("❌ 没有找到文章数据")
        return

    # 计算基准指标
    print("📈 计算各公众号基准指标...")
    baselines = calculate_account_baselines(articles)
    print(f"✅ 计算了 {len(baselines)} 个公众号的基准数据")

    # 检测爆款文章
    print("🔍 检测爆款文章...")
    viral_articles = detect_viral_articles(articles, baselines, debug=debug)
    print(f"✅ 检测到 {len(viral_articles)} 篇爆款文章")

    # 生成HTML报告
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    output_file = reports_dir / "viral_alert.html"

    print("📝 生成HTML报告...")
    generate_html_report(viral_articles, output_file)
    print(f"✅ 报告已生成: {output_file}")

    # 终端输出摘要
    print_terminal_summary(viral_articles)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='爆款警报系统')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()

    main(debug=args.debug)
