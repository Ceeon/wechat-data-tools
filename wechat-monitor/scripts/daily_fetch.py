#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日批量获取脚本
功能: 获取当天发布的所有文章
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
import html2text
import yaml
import re
import time
import hashlib
import json


# 配置文件路径
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"
SUBSCRIPTIONS_FILE = PROJECT_ROOT / "config" / "subscriptions.csv"


def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def load_subscriptions():
    """加载订阅列表"""
    subscriptions = []
    with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('name,'):
                continue

            parts = line.split(',')
            if len(parts) >= 3:
                subscriptions.append({
                    'name': parts[0],
                    'biz': parts[1],
                    'rss_url': parts[2],
                    'category': parts[3] if len(parts) > 3 else ''
                })
    return subscriptions


def is_today(pub_date_str):
    """
    判断文章是否是今天发布的

    Args:
        pub_date_str: 发布时间字符串(RSS格式)

    Returns:
        bool: 是今天返回True
    """
    try:
        from dateutil import parser
        pub_date = parser.parse(pub_date_str)

        # 转换为本地时区
        today = datetime.now().date()
        pub_date_local = pub_date.date()

        return pub_date_local == today
    except Exception as e:
        print(f"  ⚠️  时间解析失败: {e}")
        return False


def is_yesterday(pub_date_str):
    """
    判断文章是否是昨天发布的

    Args:
        pub_date_str: 发布时间字符串(RSS格式)

    Returns:
        bool: 是昨天返回True
    """
    try:
        from dateutil import parser
        pub_date = parser.parse(pub_date_str)

        # 转换为本地时区
        yesterday = (datetime.now() - timedelta(days=1)).date()
        pub_date_local = pub_date.date()

        return pub_date_local == yesterday
    except Exception as e:
        print(f"  ⚠️  时间解析失败: {e}")
        return False


def get_article_id(url):
    """从文章URL生成唯一ID"""
    return hashlib.md5(url.encode()).hexdigest()[:16]


def check_article_exists(article_id, articles_dir):
    """检查文章是否已存在"""
    for item in Path(articles_dir).glob(f"*_{article_id}_*"):
        if item.is_dir():
            return True
    return False


def download_article_html(url, timeout=30):
    """下载文章HTML内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"  ❌ 下载文章失败: {e}")
        return None


def extract_article_content(html):
    """从HTML中提取文章正文"""
    soup = BeautifulSoup(html, 'lxml')

    title = soup.find('h1', class_='rich_media_title')
    title = title.get_text().strip() if title else "无标题"

    author = soup.find('a', class_='rich_media_meta_link')
    author = author.get_text().strip() if author else "未知作者"

    content = soup.find('div', class_='rich_media_content')
    content_html = str(content) if content else ""

    return {
        'title': title,
        'author': author,
        'content_html': content_html
    }


def html_to_markdown(html):
    """将HTML转换为Markdown"""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0

    markdown = h.handle(html)
    return markdown


def sanitize_filename(filename):
    """清理文件名,移除非法字符"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    if len(filename) > 50:
        filename = filename[:50]
    return filename


def save_article(article_data, articles_dir):
    """保存文章为Markdown文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    article_id = article_data['id']
    title = sanitize_filename(article_data['title'])
    folder_name = f"{timestamp}_{article_id}_{title}"

    article_folder = Path(articles_dir) / folder_name
    article_folder.mkdir(parents=True, exist_ok=True)

    md_content = f"""# {article_data['title']}

**作者**: {article_data['author']}
**发布时间**: {article_data['publish_time']}
**原文链接**: {article_data['url']}
**公众号**: {article_data['account_name']}
**分类**: {article_data['category']}
**采集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{article_data['content_md']}
"""

    md_file = article_folder / "article.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 保存 metadata.json
    metadata = {
        'title': article_data['title'],
        'author': article_data['author'],
        'publish_time': article_data['publish_time'],
        'url': article_data['url'],
        'account_name': article_data['account_name'],
        'category': article_data['category'],
        'collected_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    metadata_file = article_folder / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 已保存: {article_folder.name}")
    return str(article_folder)


def fetch_today_articles():
    """获取今天的文章"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='采集公众号文章')
    parser.add_argument('--mode', choices=['today', 'yesterday', 'all', 'recent'], default='yesterday',
                       help='采集模式: yesterday=只采集昨天(默认), today=只采集今天, all=采集所有未采集的, recent=采集最近N篇')
    parser.add_argument('--limit', type=int, default=20,
                       help='recent模式下采集的数量(默认20)')
    args = parser.parse_args()

    print("=" * 60)
    if args.mode == 'today':
        print(f"📅 每日文章采集 - {datetime.now().strftime('%Y年%m月%d日')}")
    elif args.mode == 'yesterday':
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y年%m月%d日')
        print(f"📅 每日文章采集 - {yesterday_date} (昨天)")
    elif args.mode == 'all':
        print(f"📅 全量文章采集 - 采集所有未采集的文章")
    else:
        print(f"📅 最近文章采集 - 采集最近{args.limit}篇未采集的文章")
    print("=" * 60)

    # 加载配置
    config = load_config()
    subscriptions = load_subscriptions()
    articles_dir = PROJECT_ROOT / config['storage']['articles_dir']

    print(f"\n📋 加载了 {len(subscriptions)} 个订阅")

    total_found = 0
    total_new = 0

    # 遍历每个订阅
    for sub in subscriptions:
        print(f"\n{'='*60}")
        print(f"📡 处理订阅: {sub['name']} ({sub['category']})")
        print(f"{'='*60}")

        # 获取RSS
        try:
            feed = feedparser.parse(sub['rss_url'])
            if not feed or not hasattr(feed, 'entries'):
                print(f"  ❌ RSS源无效或无文章")
                continue

            print(f"  📝 RSS中共有 {len(feed.entries)} 篇文章")

            # 根据模式筛选文章
            target_entries = []

            if args.mode == 'today':
                # 只采集今天的文章
                for entry in feed.entries:
                    if hasattr(entry, 'updated'):
                        if is_today(entry.updated):
                            target_entries.append(entry)
                if not target_entries:
                    print(f"  ⏭️  今天没有新文章")
                    continue
                print(f"  ✨ 今天发布了 {len(target_entries)} 篇文章")

            elif args.mode == 'yesterday':
                # 只采集昨天的文章
                for entry in feed.entries:
                    if hasattr(entry, 'updated'):
                        if is_yesterday(entry.updated):
                            target_entries.append(entry)
                if not target_entries:
                    print(f"  ⏭️  昨天没有新文章")
                    continue
                print(f"  ✨ 昨天发布了 {len(target_entries)} 篇文章")

            elif args.mode == 'all':
                # 采集所有未采集的文章
                target_entries = feed.entries
                print(f"  🔍 检查所有文章...")

            elif args.mode == 'recent':
                # 采集最近N篇未采集的文章
                target_entries = feed.entries[:args.limit]
                print(f"  🔍 检查最近 {len(target_entries)} 篇文章...")

            total_found += len(target_entries)

            # 处理筛选出的文章
            for entry in target_entries:
                try:
                    url = entry.link
                    article_id = get_article_id(url)
                    title = entry.title if hasattr(entry, 'title') else "无标题"

                    print(f"\n  处理文章: {title}")
                    print(f"    URL: {url}")

                    # 去重检查
                    if check_article_exists(article_id, articles_dir):
                        print(f"    ⏭️  文章已存在,跳过")
                        continue

                    # 获取RSS中的发布时间并格式化
                    publish_time = ""
                    if hasattr(entry, 'updated'):
                        try:
                            from dateutil import parser
                            dt = parser.parse(entry.updated)
                            publish_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            publish_time = entry.updated

                    # 优先使用RSS feed中的内容（Wechat2RSS已经包含完整内容）
                    content_html = ""
                    author = "未知作者"

                    if hasattr(entry, 'content') and entry.content:
                        # RSS feed 中有完整内容
                        content_html = entry.content[0].value
                        print(f"    ✅ 从RSS获取内容 ({len(content_html)} 字符)")
                    else:
                        # 备用方案：下载HTML
                        print(f"    ⚠️  RSS无内容，尝试下载HTML...")
                        html = download_article_html(url, timeout=config['rss']['timeout'])
                        if not html:
                            continue

                        # 提取内容
                        content = extract_article_content(html)
                        content_html = content['content_html']
                        author = content['author']

                    # 转换为Markdown
                    content_md = html_to_markdown(content_html)

                    # 组装文章数据
                    # 优先使用RSS中的标题
                    final_title = title if title != "无标题" else "无标题"

                    article_data = {
                        'id': article_id,
                        'url': url,
                        'title': final_title,
                        'author': author,
                        'publish_time': publish_time,  # 使用RSS时间
                        'content_md': content_md,
                        'account_name': sub['name'],
                        'category': sub['category']
                    }

                    # 保存文章
                    save_article(article_data, articles_dir)
                    total_new += 1

                    # 延迟
                    time.sleep(1)

                except Exception as e:
                    print(f"    ❌ 处理失败: {e}")
                    continue

        except Exception as e:
            print(f"  ❌ 订阅处理失败: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"✅ 采集完成!")
    print(f"   检查了: {total_found} 篇文章")
    print(f"   新增保存: {total_new} 篇文章")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    fetch_today_articles()
