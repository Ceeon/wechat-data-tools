#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能获取互动数据
功能: 按策略获取文章数据,节省成本
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import yaml

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

    # 保存最新数据（向后兼容）
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


def smart_fetch(strategy='conservative'):
    """
    智能获取互动数据

    策略选项:
    - yesterday: 前2天策略 - 获取前2天发布的文章（24-72小时内）
    - conservative: 保守策略(最省钱) - 48小时后 + 手动选择
    - weekly: 每周策略 - 7天前的文章,一次性获取
    - important: 重要文章策略 - 只获取AI标记为重要的
    """
    print("=" * 60)
    print("🧠 智能获取互动数据")
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

    # 扫描文章
    all_folders = sorted(Path(articles_dir).glob("*"), reverse=True)
    candidates = []

    print(f"\n📁 扫描文章...")

    for folder in all_folders:
        if not folder.is_dir():
            continue

        # 检查是否已获取
        stats_file = folder / "stats_metadata.json"
        if stats_file.exists():
            continue

        md_file = folder / "article.md"
        if not md_file.exists():
            continue

        # 获取发布时间
        publish_date = get_article_publish_date(md_file)
        if not publish_date:
            continue

        # 计算文章年龄
        age_hours = (datetime.now() - publish_date).total_seconds() / 3600

        # 根据策略筛选
        if strategy == 'yesterday':
            # 前2天策略: 获取前2天发布的文章 (24-72小时内)
            if age_hours < 24 or age_hours > 72:
                continue
        elif strategy == 'conservative':
            # 保守策略: 48小时后的文章
            if age_hours < 48:
                continue
        elif strategy == 'weekly':
            # 每周策略: 7天前的文章
            if age_hours < 168:  # 7天
                continue
        elif strategy == 'important':
            # 重要文章策略: 有AI标签的
            ai_file = folder / "ai_metadata.json"
            if not ai_file.exists():
                continue

        candidates.append({
            'folder': folder,
            'md_file': md_file,
            'age_hours': age_hours,
            'publish_date': publish_date
        })

    if not candidates:
        print("\n✅ 没有符合条件的文章需要获取")
        return

    print(f"\n📋 找到 {len(candidates)} 篇符合条件的文章")

    # 显示预估成本
    estimated_cost = len(candidates) * 0.05
    print(f"💰 预估成本: ¥{estimated_cost:.2f}")

    # 显示候选文章列表
    print(f"\n候选文章:")
    for i, item in enumerate(candidates[:10], 1):
        folder_name = item['folder'].name
        age_days = item['age_hours'] / 24
        print(f"  {i}. {folder_name[:60]}... (发布 {age_days:.1f} 天前)")

    if len(candidates) > 10:
        print(f"  ... 还有 {len(candidates) - 10} 篇")

    # 询问确认
    print("\n选择操作:")
    print("1. 获取全部")
    print("2. 获取前N篇")
    print("3. 取消")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == '3':
        print("已取消")
        return

    if choice == '2':
        limit_str = input("输入获取数量: ").strip()
        try:
            limit = int(limit_str)
            candidates = candidates[:limit]
            estimated_cost = len(candidates) * 0.05
            print(f"\n💰 实际成本: ¥{estimated_cost:.2f}")
        except:
            print("❌ 无效的数量")
            return

    # 确认
    confirm = input(f"\n确认获取 {len(candidates)} 篇文章? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("已取消")
        return

    # 开始获取
    print(f"\n开始获取...")
    success = 0
    failed = 0

    for i, item in enumerate(candidates, 1):
        folder = item['folder']
        md_file = item['md_file']

        print(f"\n[{i}/{len(candidates)}] {folder.name[:50]}...")

        # 提取URL
        url = extract_article_url(md_file)
        if not url:
            print("  ⚠️  未找到URL,跳过")
            failed += 1
            continue

        # 获取数据
        print("  📊 获取互动数据...")
        stats = client.get_article_stats(url)

        if not stats:
            print("  ❌ 获取失败")
            failed += 1
            continue

        # 保存
        save_stats_metadata(folder, stats)
        print(f"  ✅ 完成! 阅读: {stats.get('read_num', 0)}, 点赞: {stats.get('like_num', 0)}")
        success += 1

        # API限流
        if i < len(candidates):
            import time
            time.sleep(0.5)

    # 总结
    actual_cost = success * 0.05
    print(f"\n{'='*60}")
    print(f"✅ 获取完成!")
    print(f"   成功: {success} 篇")
    print(f"   失败: {failed} 篇")
    print(f"   实际花费: ¥{actual_cost:.2f}")
    print(f"{'='*60}\n")


def main():
    """主函数"""
    print("\n选择获取策略:")
    print("1. 前2天策略 - 获取前2天发布的文章 (推荐,可对比数据变化)")
    print("2. 保守策略 - 48小时后的文章 (数据稳定)")
    print("3. 每周策略 - 7天前的文章")
    print("4. 重要文章 - 只获取有AI标签的文章")

    choice = input("\n请选择 (1/2/3/4): ").strip()

    strategy_map = {
        '1': 'yesterday',
        '2': 'conservative',
        '3': 'weekly',
        '4': 'important'
    }

    strategy = strategy_map.get(choice, 'yesterday')
    smart_fetch(strategy)


if __name__ == "__main__":
    main()
