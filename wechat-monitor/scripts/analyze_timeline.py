#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间维度数据分析脚本
分析最近30天的发布规律、最佳发布时间、标题类型效果、内容长度关系
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

PROJECT_ROOT = Path(__file__).parent.parent
ARTICLES_DIR = PROJECT_ROOT / "data" / "articles"


def load_article_data_with_time():
    """加载所有文章数据，包含时间信息"""
    articles = []

    for article_dir in ARTICLES_DIR.glob("*"):
        if not article_dir.is_dir():
            continue

        # 解析文件夹名称: 20251018_033536_id_title
        parts = article_dir.name.split('_')
        if len(parts) < 4:
            continue

        date_str = parts[0]  # 20251018
        time_str = parts[1]  # 033536

        metadata_file = article_dir / "metadata.json"
        stats_file = article_dir / "stats_metadata.json"
        article_file = article_dir / "article.md"

        if not metadata_file.exists():
            continue

        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 读取互动数据
        stats = {}
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)

        # 读取文章内容以计算长度
        content_length = 0
        if article_file.exists():
            with open(article_file, 'r', encoding='utf-8') as f:
                content = f.read()
                content_length = len(content)

        # 解析发布时间
        try:
            publish_time = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M%S")
        except:
            continue

        # 合并数据
        article = {
            **metadata,
            'publish_time': publish_time,
            'publish_date': date_str,
            'publish_hour': int(time_str[:2]),
            'weekday': publish_time.weekday(),  # 0=周一, 6=周日
            'weekday_name': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][publish_time.weekday()],
            'read_num': stats.get('read_num', 0),
            'like_num': stats.get('like_num', 0),
            'looking_num': stats.get('looking_num', 0),
            'in_comment_num': stats.get('in_comment_num', 0),
            'content_length': content_length,
            'engagement_rate': 0
        }

        # 计算互动率
        if article['read_num'] > 0:
            article['engagement_rate'] = (
                article['like_num'] +
                article['looking_num'] +
                article['in_comment_num']
            ) / article['read_num'] * 100

        articles.append(article)

    return articles


def filter_recent_days(articles, days=30):
    """筛选最近N天的文章"""
    cutoff_date = datetime.now() - timedelta(days=days)
    return [a for a in articles if a['publish_time'] >= cutoff_date]


def analyze_update_frequency(articles):
    """分析更新频率"""
    if not articles:
        return {}

    # 按日期分组
    by_date = defaultdict(list)
    for article in articles:
        by_date[article['publish_date']].append(article)

    # 计算统计数据
    days_with_content = len(by_date)
    total_articles = len(articles)

    # 计算日期范围
    dates = sorted([datetime.strptime(d, "%Y%m%d") for d in by_date.keys()])
    if len(dates) >= 2:
        date_range = (dates[-1] - dates[0]).days + 1
    else:
        date_range = 1

    # 每天文章数分布
    articles_per_day = [len(articles) for articles in by_date.values()]

    return {
        'total_days': date_range,
        'days_with_content': days_with_content,
        'total_articles': total_articles,
        'avg_per_day': total_articles / date_range if date_range > 0 else 0,
        'avg_per_active_day': statistics.mean(articles_per_day) if articles_per_day else 0,
        'max_per_day': max(articles_per_day) if articles_per_day else 0,
        'publish_rate': days_with_content / date_range * 100 if date_range > 0 else 0,
        'by_date': dict(by_date)
    }


def analyze_best_publish_time(articles):
    """分析最佳发布时间"""
    # 按星期几分组
    by_weekday = defaultdict(list)
    for article in articles:
        if article['read_num'] > 0:
            by_weekday[article['weekday']].append(article)

    # 统计每个星期的平均数据
    weekday_stats = {}
    for weekday, arts in by_weekday.items():
        weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][weekday]
        weekday_stats[weekday_name] = {
            'count': len(arts),
            'avg_reads': statistics.mean([a['read_num'] for a in arts]),
            'avg_engagement': statistics.mean([a['engagement_rate'] for a in arts]),
            'total_reads': sum([a['read_num'] for a in arts])
        }

    # 按小时分组
    by_hour = defaultdict(list)
    for article in articles:
        if article['read_num'] > 0:
            by_hour[article['publish_hour']].append(article)

    # 统计每个小时的平均数据
    hour_stats = {}
    for hour, arts in by_hour.items():
        hour_stats[hour] = {
            'count': len(arts),
            'avg_reads': statistics.mean([a['read_num'] for a in arts]),
            'avg_engagement': statistics.mean([a['engagement_rate'] for a in arts])
        }

    return {
        'by_weekday': weekday_stats,
        'by_hour': hour_stats
    }


def classify_title_type(title):
    """分类标题类型"""
    types = []

    # 数字型
    if re.search(r'\d+', title):
        types.append('数字型')

    # 对比型
    if any(word in title for word in ['vs', 'VS', '对比', '超越', '硬刚', '谁更强', 'PK']):
        types.append('对比型')

    # 劝退型
    if any(word in title for word in ['劝退', '不要', '别再', '不用', '过时']):
        types.append('劝退型')

    # 实战型
    if any(word in title for word in ['实战', '教程', '技巧', '方法', '玩法', '策略', '全流程', '实测', '测试']):
        types.append('实战型')

    # 爆料型
    if any(word in title for word in ['曝光', '揭秘', '拆解', '扒', '深度', '解析']):
        types.append('爆料型')

    # 问题型
    if '？' in title or '?' in title:
        types.append('问题型')

    # 新闻型
    if any(word in title for word in ['突发', '刚', '发布', '推出', '上线', '开源']):
        types.append('新闻型')

    # 观点型
    if any(word in title for word in ['真觉得', '我认为', '其实', '才是', '可能是']):
        types.append('观点型')

    # 悬念型
    if any(word in title for word in ['竟然', '意外', '想不到', '出乎意料', '居然']):
        types.append('悬念型')

    return types if types else ['普通型']


def analyze_title_types(articles):
    """分析标题类型与互动率的关系"""
    type_stats = defaultdict(lambda: {
        'count': 0,
        'total_reads': 0,
        'total_engagement': 0,
        'articles': []
    })

    for article in articles:
        if article['read_num'] == 0:
            continue

        types = classify_title_type(article['title'])

        for title_type in types:
            type_stats[title_type]['count'] += 1
            type_stats[title_type]['total_reads'] += article['read_num']
            type_stats[title_type]['total_engagement'] += article['engagement_rate']
            type_stats[title_type]['articles'].append(article)

    # 计算平均值
    results = {}
    for title_type, stats in type_stats.items():
        if stats['count'] > 0:
            results[title_type] = {
                'count': stats['count'],
                'avg_reads': stats['total_reads'] / stats['count'],
                'avg_engagement': stats['total_engagement'] / stats['count'],
                'total_reads': stats['total_reads']
            }

    return results


def analyze_content_length(articles):
    """分析内容长度与数据的关系"""
    # 按长度分段
    length_ranges = [
        (0, 1000, '极短 (<1K)'),
        (1000, 3000, '短 (1-3K)'),
        (3000, 5000, '中 (3-5K)'),
        (5000, 8000, '长 (5-8K)'),
        (8000, 15000, '很长 (8-15K)'),
        (15000, float('inf'), '超长 (>15K)')
    ]

    range_stats = defaultdict(lambda: {
        'count': 0,
        'articles': []
    })

    for article in articles:
        if article['read_num'] == 0:
            continue

        length = article['content_length']
        for min_len, max_len, label in length_ranges:
            if min_len <= length < max_len:
                range_stats[label]['count'] += 1
                range_stats[label]['articles'].append(article)
                break

    # 计算统计数据
    results = {}
    for label, stats in range_stats.items():
        if stats['count'] > 0:
            articles = stats['articles']
            results[label] = {
                'count': stats['count'],
                'avg_reads': statistics.mean([a['read_num'] for a in articles]),
                'avg_engagement': statistics.mean([a['engagement_rate'] for a in articles]),
                'avg_length': statistics.mean([a['content_length'] for a in articles])
            }

    return results


def print_timeline_analysis(articles, days=30):
    """打印完整的时间线分析报告"""
    print("=" * 80)
    print(f"📅 最近 {days} 天数据分析报告")
    print("=" * 80)
    print()

    if not articles:
        print("❌ 没有找到数据")
        return

    # 1. 更新频率分析
    print("=" * 80)
    print("📊 1. 内容更新频率分析")
    print("=" * 80)
    print()

    freq = analyze_update_frequency(articles)

    print(f"📆 统计周期: {freq['total_days']} 天")
    print(f"📝 总发布文章: {freq['total_articles']} 篇")
    print(f"📅 有内容的天数: {freq['days_with_content']} 天")
    print(f"📈 发布频率: {freq['publish_rate']:.1f}% (平均每 {100/freq['publish_rate']:.1f} 天发布一次)" if freq['publish_rate'] > 0 else "")
    print()
    print(f"📊 发布节奏:")
    print(f"   • 平均每天: {freq['avg_per_day']:.2f} 篇")
    print(f"   • 有更新的日子平均: {freq['avg_per_active_day']:.2f} 篇")
    print(f"   • 单日最多: {freq['max_per_day']} 篇")
    print()

    # 显示最近的发布日期
    recent_dates = sorted(freq['by_date'].keys(), reverse=True)[:10]
    print("🗓️  最近10天的发布情况:")
    for date_str in recent_dates:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        articles_count = len(freq['by_date'][date_str])
        print(f"   • {date_obj.strftime('%Y-%m-%d')} ({date_obj.strftime('%A')}): {articles_count} 篇")
    print()

    # 2. 最佳发布时间分析
    print("=" * 80)
    print("⏰ 2. 最佳发布时间分析")
    print("=" * 80)
    print()

    time_stats = analyze_best_publish_time(articles)

    print("📅 按星期几分析:")
    print()

    # 按平均阅读数排序
    weekday_sorted = sorted(
        time_stats['by_weekday'].items(),
        key=lambda x: x[1]['avg_reads'],
        reverse=True
    )

    for weekday_name, stats in weekday_sorted:
        print(f"   {weekday_name}:")
        print(f"      • 发布次数: {stats['count']} 篇")
        print(f"      • 平均阅读: {stats['avg_reads']:,.0f}")
        print(f"      • 平均互动率: {stats['avg_engagement']:.2f}%")
        print()

    best_weekday = weekday_sorted[0][0]
    print(f"🏆 最佳发布日: {best_weekday} (平均阅读 {weekday_sorted[0][1]['avg_reads']:,.0f})")
    print()

    print("🕐 按发布时间段分析:")
    print()

    # 按小时分组并排序
    hour_sorted = sorted(
        time_stats['by_hour'].items(),
        key=lambda x: x[1]['avg_reads'],
        reverse=True
    )

    for hour, stats in hour_sorted[:5]:
        print(f"   {hour:02d}:00 - {hour:02d}:59")
        print(f"      • 发布次数: {stats['count']} 篇")
        print(f"      • 平均阅读: {stats['avg_reads']:,.0f}")
        print(f"      • 平均互动率: {stats['avg_engagement']:.2f}%")
        print()

    # 3. 标题类型分析
    print("=" * 80)
    print("📝 3. 标题类型与互动率分析")
    print("=" * 80)
    print()

    title_stats = analyze_title_types(articles)

    # 按平均互动率排序
    title_sorted = sorted(
        title_stats.items(),
        key=lambda x: x[1]['avg_engagement'],
        reverse=True
    )

    print("🏆 各类型标题效果排名（按互动率）:")
    print()

    for i, (title_type, stats) in enumerate(title_sorted, 1):
        print(f"{i}. 【{title_type}】")
        print(f"   • 使用次数: {stats['count']} 篇")
        print(f"   • 平均阅读: {stats['avg_reads']:,.0f}")
        print(f"   • 平均互动率: {stats['avg_engagement']:.2f}%")
        print(f"   • 总阅读数: {stats['total_reads']:,}")
        print()

    # 4. 内容长度分析
    print("=" * 80)
    print("📏 4. 内容长度与数据关系分析")
    print("=" * 80)
    print()

    length_stats = analyze_content_length(articles)

    # 按平均阅读数排序
    length_sorted = sorted(
        length_stats.items(),
        key=lambda x: x[1]['avg_reads'],
        reverse=True
    )

    print("📊 不同长度文章的表现:")
    print()

    for label, stats in length_sorted:
        print(f"   【{label}】")
        print(f"      • 文章数: {stats['count']} 篇")
        print(f"      • 平均字数: {stats['avg_length']:,.0f}")
        print(f"      • 平均阅读: {stats['avg_reads']:,.0f}")
        print(f"      • 平均互动率: {stats['avg_engagement']:.2f}%")
        print()

    # 5. 综合建议
    print("=" * 80)
    print("💡 5. 数据洞察与建议")
    print("=" * 80)
    print()

    print("✅ 发布策略建议:")
    print(f"   • 最佳发布日: {best_weekday}")
    if hour_sorted:
        best_hour = hour_sorted[0][0]
        print(f"   • 最佳发布时间: {best_hour:02d}:00 - {best_hour:02d}:59")
    print(f"   • 建议发布频率: {freq['avg_per_day']:.1f} 篇/天")
    print()

    print("✅ 标题策略建议:")
    if title_sorted:
        top3_types = [t[0] for t in title_sorted[:3]]
        print(f"   • 优先使用: {', '.join(top3_types)}")
    print()

    print("✅ 内容长度建议:")
    if length_sorted:
        best_length = length_sorted[0][0]
        print(f"   • 最佳长度区间: {best_length}")
    print()


def main():
    """主函数"""
    print("正在加载文章数据...")
    articles = load_article_data_with_time()

    if not articles:
        print("❌ 未找到文章数据")
        return

    # 筛选最近30天
    recent_articles = filter_recent_days(articles, days=30)

    if not recent_articles:
        print("❌ 未找到最近30天的数据")
        return

    print(f"✅ 已加载 {len(articles)} 篇文章，其中最近30天有 {len(recent_articles)} 篇")
    print()

    # 只分析有互动数据的
    articles_with_stats = [a for a in recent_articles if a['read_num'] > 0]

    if not articles_with_stats:
        print("❌ 未找到有互动数据的文章")
        return

    # 打印分析报告
    print_timeline_analysis(articles_with_stats, days=30)


if __name__ == "__main__":
    main()
