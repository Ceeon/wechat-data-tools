#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取前1-2天发布文章的互动数据
自动模式，无需用户交互
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))
from utils.jizhile_api import JizhileAPI

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"


def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def extract_article_url(md_file):
    """从Markdown文件中提取文章URL"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    for line in content.split('\n'):
        if line.startswith('**原文链接**:'):
            import re
            match = re.search(r'https://mp\.weixin\.qq\.com/s[?/][^\s\)]+', line)
            if match:
                return match.group(0)
    return None


def get_article_publish_date(md_file):
    """获取文章发布日期"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    for line in content.split('\n'):
        if line.startswith('**发布时间**:'):
            time_str = line.replace('**发布时间**:', '').strip()
            try:
                from dateutil import parser
                return parser.parse(time_str)
            except:
                pass
    return None


def save_stats_metadata(article_folder, stats):
    """保存互动数据到JSON文件（同时保存历史记录）"""
    now = datetime.now()
    metadata = {
        'read_num': stats.get('read_num', 0),
        'like_num': stats.get('like_num', 0),
        'looking_num': stats.get('looking_num', 0),
        'in_comment_num': stats.get('in_comment_num', 0),
        'share_num': stats.get('share_num', 0),
        'collect_num': stats.get('collect_num', 0),
        'fetched_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'fetched_date': now.strftime('%Y-%m-%d')
    }

    # 保存最新数据
    json_file = article_folder / "stats_metadata.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 保存历史记录
    history_file = article_folder / "stats_history.json"
    history_data = {'history': []}

    # 读取已有历史
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except:
            history_data = {'history': []}

    # 检查是否今天已经获取过（避免重复）
    today = now.strftime('%Y-%m-%d')
    existing_dates = [item.get('fetched_date') for item in history_data.get('history', [])]

    if today not in existing_dates:
        # 追加新记录
        history_data['history'].append(metadata)

        # 保存历史文件
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)


def main():
    """主函数 - 自动获取前1-2天发布文章的互动数据"""
    print("=" * 60)
    print("📊 获取前1-2天发布文章的互动数据")
    print("=" * 60)

    # 加载配置
    config = load_config()
    api_key = config.get('jizhile', {}).get('api_key')
    if not api_key:
        print("❌ 请先在 config.yaml 中配置极致了 API Key")
        sys.exit(1)

    articles_dir = PROJECT_ROOT / "data" / "articles"
    if not articles_dir.exists():
        print("❌ 文章目录不存在")
        sys.exit(1)

    # 初始化API客户端
    client = JizhileAPI(api_key=api_key)

    # 计算目标日期范围 (前1天和前2天)
    today = datetime.now().date()
    day_before_1 = (datetime.now() - timedelta(days=1)).date()
    day_before_2 = (datetime.now() - timedelta(days=2)).date()
    target_dates = [day_before_1, day_before_2]

    print(f"\n📅 目标日期:")
    print(f"   前1天: {day_before_1.strftime('%Y-%m-%d')}")
    print(f"   前2天: {day_before_2.strftime('%Y-%m-%d')}")

    # 扫描文章
    all_folders = sorted(Path(articles_dir).glob("*"), reverse=True)
    candidates = []

    print(f"\n📁 扫描文章...")

    for folder in all_folders:
        if not folder.is_dir():
            continue

        md_file = folder / "article.md"
        if not md_file.exists():
            continue

        # 获取发布时间
        publish_date = get_article_publish_date(md_file)
        if not publish_date:
            continue

        pub_day = publish_date.date()

        # 只处理前1-2天发布的文章
        if pub_day not in target_dates:
            continue

        candidates.append({
            'folder': folder,
            'md_file': md_file,
            'pub_date': pub_day,
            'title': folder.name[:60]
        })

    if not candidates:
        print("\n✅ 没有需要获取数据的文章")
        return

    print(f"\n📋 找到 {len(candidates)} 篇符合条件的文章:")
    for i, item in enumerate(candidates[:10], 1):
        print(f"  {i}. [{item['pub_date']}] {item['title']}")

    if len(candidates) > 10:
        print(f"  ... 还有 {len(candidates) - 10} 篇")

    # 开始获取
    print(f"\n开始获取互动数据...")
    success = 0
    failed = 0

    for i, item in enumerate(candidates, 1):
        folder = item['folder']
        md_file = item['md_file']

        print(f"\n[{i}/{len(candidates)}] {item['title']}")

        # 提取URL
        url = extract_article_url(md_file)
        if not url:
            print("  ⚠️  未找到URL,跳过")
            failed += 1
            continue

        # 获取数据
        print("  📊 获取互动数据...")
        try:
            stats = client.get_article_stats(url)

            if not stats:
                print("  ❌ 获取失败")
                failed += 1
                continue

            # 保存
            save_stats_metadata(folder, stats)
            print(f"  ✅ 完成! 阅读:{stats.get('read_num', 0)}, 点赞:{stats.get('like_num', 0)}")
            success += 1

            # API限流
            if i < len(candidates):
                import time
                time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            failed += 1
            continue

    # 总结
    print(f"\n{'='*60}")
    print(f"✅ 获取完成!")
    print(f"   成功: {success} 篇")
    print(f"   失败: {failed} 篇")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
