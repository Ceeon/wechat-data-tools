#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选题数据分析脚本
分析哪些选题方向数据表现好，找出共同特征
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import statistics

PROJECT_ROOT = Path(__file__).parent.parent
ARTICLES_DIR = PROJECT_ROOT / "data" / "articles"


def load_article_data():
    """加载所有文章数据"""
    articles = []

    for article_dir in ARTICLES_DIR.glob("*"):
        if not article_dir.is_dir():
            continue

        metadata_file = article_dir / "metadata.json"
        stats_file = article_dir / "stats_metadata.json"

        if not metadata_file.exists():
            continue

        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 读取互动数据（如果存在）
        stats = {}
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)

        # 合并数据
        article = {
            **metadata,
            'read_num': stats.get('read_num', 0),
            'like_num': stats.get('like_num', 0),
            'looking_num': stats.get('looking_num', 0),
            'in_comment_num': stats.get('in_comment_num', 0),
            'engagement_rate': 0  # 互动率
        }

        # 计算互动率 = (点赞 + 在看 + 评论) / 阅读数
        if article['read_num'] > 0:
            article['engagement_rate'] = (
                article['like_num'] +
                article['looking_num'] +
                article['in_comment_num']
            ) / article['read_num'] * 100

        articles.append(article)

    return articles


def extract_keywords(title):
    """从标题中提取关键词"""
    # 常见的技术/产品关键词
    ai_tools = ['GPT', 'ChatGPT', 'Claude', 'Sora', 'Midjourney', 'Stable Diffusion',
                'Deepseek', 'OpenAI', 'AI', 'RPA', 'n8n', 'workflow', 'Veo']

    tech_terms = ['编程', '开发', '工作流', '自动化', '生图', '视频', '模型',
                  '开源', '代码', 'Code', '出海']

    business_terms = ['赚钱', '变现', '增长', '策略', '红利', '流量', '美金',
                      '电商', '产品', '组织']

    keywords = {
        'ai_tools': [],
        'tech_terms': [],
        'business_terms': []
    }

    for tool in ai_tools:
        if tool.lower() in title.lower():
            keywords['ai_tools'].append(tool)

    for term in tech_terms:
        if term in title:
            keywords['tech_terms'].append(term)

    for term in business_terms:
        if term in title:
            keywords['business_terms'].append(term)

    return keywords


def analyze_top_performers(articles, top_n=20):
    """分析表现最好的文章"""
    # 按阅读数排序
    sorted_by_reads = sorted(articles, key=lambda x: x['read_num'], reverse=True)
    top_reads = sorted_by_reads[:top_n]

    # 按互动率排序
    sorted_by_engagement = sorted(articles, key=lambda x: x['engagement_rate'], reverse=True)
    top_engagement = sorted_by_engagement[:top_n]

    return top_reads, top_engagement


def find_common_patterns(articles):
    """找出共同特征"""
    all_keywords = defaultdict(list)

    for article in articles:
        keywords = extract_keywords(article['title'])

        for key, values in keywords.items():
            all_keywords[key].extend(values)

    # 统计关键词频率
    from collections import Counter

    patterns = {
        'ai_tools': Counter(all_keywords['ai_tools']).most_common(10),
        'tech_terms': Counter(all_keywords['tech_terms']).most_common(10),
        'business_terms': Counter(all_keywords['business_terms']).most_common(10)
    }

    return patterns


def analyze_title_patterns(articles):
    """分析标题模式"""
    patterns = {
        '数字型': 0,  # 包含数字
        '对比型': 0,  # 包含 vs、对比、超越
        '劝退型': 0,  # 劝退、不要学、过时
        '实战型': 0,  # 实战、教程、技巧、方法
        '爆料型': 0,  # 曝光、揭秘、拆解
        '问题型': 0,  # 包含问号
    }

    for article in articles:
        title = article['title']

        if re.search(r'\d+', title):
            patterns['数字型'] += 1

        if any(word in title for word in ['vs', 'VS', '对比', '超越', '硬刚']):
            patterns['对比型'] += 1

        if any(word in title for word in ['劝退', '不要学', '过时']):
            patterns['劝退型'] += 1

        if any(word in title for word in ['实战', '教程', '技巧', '方法', '玩法', '策略']):
            patterns['实战型'] += 1

        if any(word in title for word in ['曝光', '揭秘', '拆解', '扒']):
            patterns['爆料型'] += 1

        if '？' in title or '?' in title:
            patterns['问题型'] += 1

    return patterns


def generate_topic_suggestions(patterns):
    """根据分析结果生成选题建议"""
    suggestions = []

    # 基于高频关键词组合生成建议
    suggestions.append({
        'title': 'Claude 3.5 Sonnet vs GPT-4：我测试了10个编程场景，结果太意外了',
        'reason': '结合热门AI工具对比 + 数字化 + 实测场景'
    })

    suggestions.append({
        'title': '劝退：别再手动做视频了，这个AI工作流5分钟生成爆款',
        'reason': '劝退型标题 + 效率对比 + 实战工具'
    })

    suggestions.append({
        'title': '拆解：这个AI出海产品月入10万美金的完整策略',
        'reason': '拆解型 + 具体数字 + 商业变现'
    })

    suggestions.append({
        'title': 'OpenAI刚发布的视频功能，我总结了8个超实用技巧',
        'reason': '热点追踪 + 数字化 + 实战技巧'
    })

    suggestions.append({
        'title': 'Cursor超越Claude？实测100个代码场景，差距在这里',
        'reason': '工具对比 + 大量测试 + 悬念制造'
    })

    return suggestions


def print_analysis(articles):
    """打印完整分析报告"""
    print("=" * 80)
    print("📊 文章数据分析报告")
    print("=" * 80)
    print()

    # 基础统计
    print(f"📚 总文章数: {len(articles)}")
    print(f"📖 有阅读数据的文章: {len([a for a in articles if a['read_num'] > 0])}")
    print()

    # 分析表现最好的文章
    top_reads, top_engagement = analyze_top_performers(articles, top_n=20)

    print("=" * 80)
    print("🏆 1. 表现最好的选题方向（按阅读数）")
    print("=" * 80)
    print()

    for i, article in enumerate(top_reads[:10], 1):
        print(f"{i}. 【{article.get('category', '未分类')}】{article['title']}")
        print(f"   阅读: {article['read_num']:,} | 点赞: {article['like_num']:,} | "
              f"在看: {article['looking_num']:,} | 互动率: {article['engagement_rate']:.2f}%")
        print()

    print("=" * 80)
    print("💡 2. 高阅读文章的共同特征")
    print("=" * 80)
    print()

    # 分析关键词
    patterns = find_common_patterns(top_reads)

    print("🤖 高频 AI 工具/技术:")
    for keyword, count in patterns['ai_tools'][:5]:
        print(f"   • {keyword}: {count}次")
    print()

    print("🔧 高频技术词汇:")
    for keyword, count in patterns['tech_terms'][:5]:
        print(f"   • {keyword}: {count}次")
    print()

    print("💰 高频商业词汇:")
    for keyword, count in patterns['business_terms'][:5]:
        print(f"   • {keyword}: {count}次")
    print()

    # 标题模式分析
    title_patterns = analyze_title_patterns(top_reads)
    print("📝 标题模式分析:")
    for pattern, count in sorted(title_patterns.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(top_reads) * 100
        print(f"   • {pattern}: {count}篇 ({percentage:.1f}%)")
    print()

    # 统计数据特征
    avg_reads = statistics.mean([a['read_num'] for a in top_reads if a['read_num'] > 0])
    avg_engagement = statistics.mean([a['engagement_rate'] for a in top_reads])

    print("📈 平均数据:")
    print(f"   • 平均阅读数: {avg_reads:,.0f}")
    print(f"   • 平均互动率: {avg_engagement:.2f}%")
    print()

    print("=" * 80)
    print("✨ 3. 基于数据的选题建议（5个）")
    print("=" * 80)
    print()

    suggestions = generate_topic_suggestions(patterns)

    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion['title']}")
        print(f"   💡 推荐理由: {suggestion['reason']}")
        print()

    print("=" * 80)
    print("📋 选题策略总结")
    print("=" * 80)
    print()
    print("✅ 核心要素:")
    print("   1. 热门AI工具对比（Sora, Claude, GPT等）")
    print("   2. 数字化标题（具体场景数、测试数）")
    print("   3. 实战导向（技巧、方法、策略）")
    print("   4. 商业价值（出海、赚钱、变现）")
    print("   5. 标题技巧（劝退型、拆解型、对比型）")
    print()
    print("⚠️  避免:")
    print("   • 纯理论、无实战")
    print("   • 标题平淡、无吸引力")
    print("   • 缺少数字、案例支撑")
    print()


def main():
    """主函数"""
    print("正在加载文章数据...")
    articles = load_article_data()

    if not articles:
        print("❌ 未找到文章数据")
        return

    # 只分析有阅读数据的文章
    articles_with_stats = [a for a in articles if a['read_num'] > 0]

    if not articles_with_stats:
        print("❌ 未找到有互动数据的文章")
        return

    print(f"✅ 已加载 {len(articles)} 篇文章，其中 {len(articles_with_stats)} 篇有互动数据")
    print()

    # 打印分析报告
    print_analysis(articles_with_stats)


if __name__ == "__main__":
    main()
