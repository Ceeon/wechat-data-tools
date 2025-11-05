#!/usr/bin/env python3
"""
数据库查询工具
提供常用的数据库查询命令
"""

import sys
from pathlib import Path
import argparse
from tabulate import tabulate

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import WechatDatabase


def show_summary(db: WechatDatabase):
    """显示数据库摘要"""
    summary = db.get_stats_summary()

    print("\n" + "="*60)
    print("数据库统计摘要")
    print("="*60)
    print(f"总文章数: {summary['total_articles']}")
    print(f"统计记录数: {summary['total_stats_records']}")
    print(f"最新文章日期: {summary['latest_article_date']}")
    print(f"\n分类统计:")
    for category, count in summary['categories'].items():
        print(f"  - {category}: {count} 篇")
    print("="*60)


def show_latest_articles(db: WechatDatabase, limit: int = 10):
    """显示最新文章"""
    articles = db.get_latest_articles(limit=limit)

    print(f"\n最新 {limit} 篇文章:")
    print("="*60)

    table_data = []
    for article in articles:
        table_data.append([
            article['title'][:40] + '...' if len(article['title']) > 40 else article['title'],
            article['publish_time'],
            article.get('read_num') or '-',
            article.get('like_num') or '-',
            article.get('looking_num') or '-'
        ])

    headers = ['标题', '发布时间', '阅读', '点赞', '在看']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


def show_top_articles(db: WechatDatabase, metric: str = 'read_num', limit: int = 10):
    """显示热门文章"""
    cursor = db.conn.cursor()

    # 获取最新统计数据的热门文章
    query = f"""
        SELECT
            a.title,
            a.publish_time,
            s.read_num,
            s.like_num,
            s.looking_num,
            s.in_comment_num,
            s.fetched_date
        FROM articles a
        INNER JOIN (
            SELECT article_id,
                   read_num, like_num, looking_num, in_comment_num,
                   fetched_date,
                   ROW_NUMBER() OVER (PARTITION BY article_id ORDER BY fetched_date DESC) as rn
            FROM article_stats
        ) s ON a.article_id = s.article_id AND s.rn = 1
        WHERE s.{metric} > 0
        ORDER BY s.{metric} DESC
        LIMIT ?
    """

    cursor.execute(query, (limit,))
    results = cursor.fetchall()

    metric_names = {
        'read_num': '阅读数',
        'like_num': '点赞数',
        'looking_num': '在看数',
        'in_comment_num': '评论数'
    }

    print(f"\n按 {metric_names.get(metric, metric)} 排名的 Top {limit} 文章:")
    print("="*60)

    table_data = []
    for row in results:
        table_data.append([
            row[0][:40] + '...' if len(row[0]) > 40 else row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5]
        ])

    headers = ['标题', '发布时间', '阅读', '点赞', '在看', '评论']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


def show_article_trend(db: WechatDatabase, article_id: str):
    """显示文章数据趋势"""
    stats = db.get_article_stats(article_id)

    if not stats:
        print(f"未找到文章 {article_id} 的统计数据")
        return

    article = db.get_article(article_id)

    print(f"\n文章: {article['title']}")
    print(f"发布时间: {article['publish_time']}")
    print("="*60)
    print("\n数据趋势:")

    table_data = []
    for stat in stats:
        table_data.append([
            stat['fetched_date'],
            stat['read_num'],
            stat['like_num'],
            stat['looking_num'],
            stat['in_comment_num']
        ])

    headers = ['日期', '阅读', '点赞', '在看', '评论']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


def search_articles(db: WechatDatabase, keyword: str):
    """搜索文章"""
    cursor = db.conn.cursor()

    cursor.execute("""
        SELECT article_id, title, author, publish_time, account_name
        FROM articles
        WHERE title LIKE ?
        ORDER BY publish_time DESC
    """, (f'%{keyword}%',))

    results = cursor.fetchall()

    if not results:
        print(f"\n未找到包含 '{keyword}' 的文章")
        return

    print(f"\n搜索结果 (关键词: '{keyword}'):")
    print("="*60)

    table_data = []
    for row in results:
        table_data.append([
            row[0],
            row[1][:50] + '...' if len(row[1]) > 50 else row[1],
            row[2],
            row[3],
            row[4]
        ])

    headers = ['ID', '标题', '作者', '发布时间', '公众号']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


def main():
    parser = argparse.ArgumentParser(description='微信公众号数据库查询工具')
    parser.add_argument('--summary', action='store_true', help='显示数据库摘要')
    parser.add_argument('--latest', type=int, metavar='N', help='显示最新 N 篇文章')
    parser.add_argument('--top', type=int, metavar='N', help='显示热门 N 篇文章')
    parser.add_argument('--metric', choices=['read_num', 'like_num', 'looking_num', 'in_comment_num'],
                        default='read_num', help='热门文章排序指标 (默认: read_num)')
    parser.add_argument('--trend', metavar='ARTICLE_ID', help='显示指定文章的数据趋势')
    parser.add_argument('--search', metavar='KEYWORD', help='搜索文章标题')

    args = parser.parse_args()

    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    db_path = project_dir / "data" / "wechat_monitor.db"

    if not db_path.exists():
        print(f"错误: 数据库文件不存在 {db_path}")
        print("请先运行 migrate_to_db.py 迁移数据")
        return

    with WechatDatabase(str(db_path)) as db:
        if args.summary:
            show_summary(db)

        if args.latest:
            show_latest_articles(db, args.latest)

        if args.top:
            show_top_articles(db, args.metric, args.top)

        if args.trend:
            show_article_trend(db, args.trend)

        if args.search:
            search_articles(db, args.search)


if __name__ == "__main__":
    main()
