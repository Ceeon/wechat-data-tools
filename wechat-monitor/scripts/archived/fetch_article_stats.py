#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量获取文章互动数据
功能: 使用极致了API获取文章的阅读数、点赞数等数据
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime

# 添加utils路径
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
    """
    从Markdown文件中提取文章URL

    Args:
        md_file: Markdown文件路径

    Returns:
        str: 文章URL，如果没找到返回None
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 在元数据中查找URL
    for line in content.split('\n'):
        if line.startswith('**原文链接**:') or line.startswith('URL:'):
            # 提取URL
            parts = line.split('](')
            if len(parts) == 2:
                url = parts[1].rstrip(')')
                return url
            # 或者直接在行中
            import re
            match = re.search(r'https://mp\.weixin\.qq\.com/s[?/][^\s\)]+', line)
            if match:
                return match.group(0)

    return None


def save_stats_metadata(article_folder, stats):
    """
    保存互动数据到JSON文件

    Args:
        article_folder: 文章文件夹
        stats: 互动数据字典
    """
    metadata = {
        'read_num': stats.get('read_num', 0),
        'like_num': stats.get('like_num', 0),
        'looking_num': stats.get('looking_num', 0),  # 在看数
        'in_comment_num': stats.get('in_comment_num', 0),
        'share_num': stats.get('share_num', 0),
        'collect_num': stats.get('collect_num', 0),
        'fetched_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    json_file = article_folder / "stats_metadata.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def update_markdown_with_stats(md_file, stats):
    """
    更新Markdown文件，添加互动数据（暂时禁用，数据已在JSON中）

    Args:
        md_file: Markdown文件路径
        stats: 互动数据字典
    """
    # 互动数据已保存在stats_metadata.json中
    # Markdown中不再添加，避免报表摘要显示重复内容
    pass


def fetch_stats_for_articles(articles_dir, api_key, skip_fetched=True, limit=None):
    """
    批量获取文章互动数据

    Args:
        articles_dir: 文章目录
        api_key: 极致了API Key
        skip_fetched: 是否跳过已获取的文章
        limit: 限制处理数量(None表示全部)
    """
    print("=" * 60)
    print("📊 批量获取文章互动数据")
    print("=" * 60)

    # 初始化API客户端
    client = JizhileAPI(api_key=api_key)

    # 扫描所有文章
    article_folders = sorted(Path(articles_dir).glob("*"), reverse=True)

    if limit:
        article_folders = article_folders[:limit]

    total = len(article_folders)
    processed = 0
    skipped = 0
    failed = 0

    print(f"\n📁 找到 {total} 篇文章")

    for i, article_folder in enumerate(article_folders, 1):
        if not article_folder.is_dir():
            continue

        folder_name = article_folder.name
        print(f"\n[{i}/{total}] 处理: {folder_name[:50]}...")

        # 检查是否已获取
        stats_metadata_file = article_folder / "stats_metadata.json"
        if skip_fetched and stats_metadata_file.exists():
            print("  ⏭️  已获取,跳过")
            skipped += 1
            continue

        # 读取Markdown文件
        md_file = article_folder / "article.md"
        if not md_file.exists():
            print("  ❌ Markdown文件不存在")
            failed += 1
            continue

        try:
            # 提取文章URL
            print("  🔍 提取文章URL...")
            article_url = extract_article_url(md_file)

            if not article_url:
                print("  ⚠️  未找到文章URL,跳过")
                skipped += 1
                continue

            # 获取互动数据
            print(f"  📊 获取互动数据...")
            stats = client.get_article_stats(article_url)

            if not stats:
                print("  ❌ 获取失败")
                failed += 1
                continue

            # 保存元数据
            print("  💾 保存互动数据...")
            save_stats_metadata(article_folder, stats)

            # 更新Markdown文件
            print("  📝 更新Markdown...")
            update_markdown_with_stats(md_file, stats)

            print(f"  ✅ 完成!")
            print(f"     阅读: {stats.get('read_num', 0)}, "
                  f"点赞: {stats.get('like_num', 0)}, "
                  f"评论: {stats.get('in_comment_num', 0)}")

            processed += 1

            # API限流
            if i < total:
                import time
                print("  ⏸️  等待0.5秒...")
                time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            failed += 1
            continue

    # 总结
    print(f"\n{'='*60}")
    print(f"✅ 批量获取完成!")
    print(f"   总计: {total} 篇")
    print(f"   已获取: {processed} 篇")
    print(f"   跳过: {skipped} 篇")
    print(f"   失败: {failed} 篇")
    print(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量获取文章互动数据')
    parser.add_argument('--mode', choices=['1', '2', '3'], default='1',
                       help='处理模式: 1=只获取未获取的(默认), 2=重新获取所有, 3=限制数量')
    parser.add_argument('--limit', type=int, default=None,
                       help='限制获取数量(仅mode=3时有效)')
    parser.add_argument('--auto', action='store_true',
                       help='自动模式,不询问确认')
    args = parser.parse_args()

    # 加载配置
    config = load_config()

    # 检查API Key
    api_key = config.get('jizhile', {}).get('api_key')
    if not api_key:
        print("❌ 请先在 config.yaml 中配置极致了 API Key")
        print("   访问 https://jizhile.com/ 获取API Key")
        print("\n配置示例:")
        print("jizhile:")
        print("  api_key: \"your_api_key_here\"")
        sys.exit(1)

    # 文章目录
    articles_dir = PROJECT_ROOT / "data" / "articles"
    if not articles_dir.exists():
        print("❌ 文章目录不存在")
        sys.exit(1)

    # 根据命令行参数或交互式输入确定处理选项
    if args.auto:
        # 自动模式:使用命令行参数
        choice = args.mode
        skip_fetched = True
        limit = None

        if choice == '2':
            skip_fetched = False
        elif choice == '3':
            limit = args.limit
    else:
        # 交互模式:询问用户
        print("=" * 60)
        print("批量获取互动数据配置")
        print("=" * 60)
        print("\n选择处理模式:")
        print("1. 只获取未获取的文章(推荐)")
        print("2. 重新获取所有文章")
        print("3. 限制获取数量(测试用)")

        choice = input("\n请选择 (1/2/3): ").strip()

        skip_fetched = True
        limit = None

        if choice == '2':
            confirm = input("⚠️  确认重新获取所有文章? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("已取消")
                return
            skip_fetched = False
        elif choice == '3':
            limit_str = input("输入获取数量: ").strip()
            try:
                limit = int(limit_str)
            except:
                print("❌ 无效的数量")
                return

    # 开始获取
    fetch_stats_for_articles(
        articles_dir,
        api_key,
        skip_fetched=skip_fetched,
        limit=limit
    )


if __name__ == "__main__":
    main()
