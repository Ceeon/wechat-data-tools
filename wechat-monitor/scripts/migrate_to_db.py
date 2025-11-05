#!/usr/bin/env python3
"""
数据迁移脚本：将 JSON 文件数据导入 SQLite 数据库
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import WechatDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_article_id_from_url(url: str) -> str:
    """从 URL 中提取 article_id

    支持两种URL格式：
    1. 完整格式: https://mp.weixin.qq.com/s?__biz=xxx&mid=123456...
    2. 短链接格式: https://mp.weixin.qq.com/s/xxxxxx
    """
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)

        # 方法1: 尝试从查询参数中提取 mid
        params = parse_qs(parsed.query)
        if 'mid' in params:
            return params['mid'][0]

        # 方法2: 尝试从短链接路径中提取 (例如: /s/M83M2eIgRxx4TifQ7o-RHg)
        path = parsed.path
        if path.startswith('/s/'):
            article_id = path[3:]  # 移除 '/s/' 前缀
            if article_id:  # 确保不为空
                return article_id

    except Exception as e:
        logger.error(f"提取 article_id 失败: {e}")

    logger.error(f"无法提取文章 ID: {url}")
    return None


def migrate_articles(data_dir: Path, db: WechatDatabase):
    """
    迁移文章数据

    Args:
        data_dir: 文章数据目录
        db: 数据库实例
    """
    articles_dir = data_dir / "articles"

    if not articles_dir.exists():
        logger.error(f"文章目录不存在: {articles_dir}")
        return

    # 统计信息
    total_articles = 0
    success_articles = 0
    total_stats = 0
    success_stats = 0

    # 遍历所有文章目录
    article_folders = sorted([d for d in articles_dir.iterdir() if d.is_dir()])
    logger.info(f"发现 {len(article_folders)} 个文章目录")

    for folder in article_folders:
        metadata_file = folder / "metadata.json"
        stats_metadata_file = folder / "stats_metadata.json"
        stats_history_file = folder / "stats_history.json"
        article_file = folder / "article.md"

        # 读取文章元数据
        if not metadata_file.exists():
            logger.warning(f"跳过（缺少 metadata.json）: {folder.name}")
            continue

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            total_articles += 1

            # 添加内容路径
            if article_file.exists():
                metadata['content_path'] = str(article_file.relative_to(data_dir.parent))

            # 从 URL 提取 BIZ（如果没有）
            if not metadata.get('biz') and metadata.get('url'):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(metadata['url'])
                params = parse_qs(parsed.query)
                if '__biz' in params:
                    metadata['biz'] = params['__biz'][0]

            # 插入文章
            if db.insert_article(metadata):
                success_articles += 1
                logger.info(f"✓ 已导入文章 [{success_articles}/{total_articles}]: {metadata.get('title', 'Unknown')}")

                # 获取 article_id
                article_id = extract_article_id_from_url(metadata.get('url', ''))

                if article_id:
                    # 导入统计数据历史记录
                    if stats_history_file.exists():
                        try:
                            with open(stats_history_file, 'r', encoding='utf-8') as f:
                                stats_history = json.load(f)

                            history_list = stats_history.get('history', [])
                            for stats in history_list:
                                if db.insert_article_stats(article_id, stats):
                                    success_stats += 1
                                total_stats += 1

                        except Exception as e:
                            logger.error(f"导入统计历史失败 {folder.name}: {e}")

                    # 如果没有历史记录，尝试导入最新统计数据
                    elif stats_metadata_file.exists():
                        try:
                            with open(stats_metadata_file, 'r', encoding='utf-8') as f:
                                stats = json.load(f)

                            if db.insert_article_stats(article_id, stats):
                                success_stats += 1
                            total_stats += 1

                        except Exception as e:
                            logger.error(f"导入统计数据失败 {folder.name}: {e}")

        except Exception as e:
            logger.error(f"处理文章失败 {folder.name}: {e}")
            continue

    # 输出统计结果
    logger.info("\n" + "=" * 60)
    logger.info("数据迁移完成！")
    logger.info("=" * 60)
    logger.info(f"文章数据: {success_articles}/{total_articles} 成功")
    logger.info(f"统计数据: {success_stats}/{total_stats} 成功")
    logger.info("=" * 60)

    # 显示数据库摘要
    summary = db.get_stats_summary()
    logger.info("\n数据库统计:")
    logger.info(f"  总文章数: {summary['total_articles']}")
    logger.info(f"  统计记录数: {summary['total_stats_records']}")
    logger.info(f"  分类统计: {summary['categories']}")
    logger.info(f"  最新文章: {summary['latest_article_date']}")


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"

    logger.info("开始数据迁移...")
    logger.info(f"数据目录: {data_dir}")

    # 创建数据库实例
    db_path = data_dir / "wechat_monitor.db"
    logger.info(f"数据库路径: {db_path}")

    with WechatDatabase(str(db_path)) as db:
        migrate_articles(data_dir, db)

    logger.info("\n迁移完成！")


if __name__ == "__main__":
    main()
