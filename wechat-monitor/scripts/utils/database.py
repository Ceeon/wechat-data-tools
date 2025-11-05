"""
SQLite 数据库管理模块
用于存储和管理微信公众号文章及统计数据
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class WechatDatabase:
    """微信公众号数据库管理类"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，默认为 data/wechat_monitor.db
        """
        if db_path is None:
            # 默认数据库路径
            base_dir = Path(__file__).parent.parent.parent
            db_path = base_dir / "data" / "wechat_monitor.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        logger.info(f"已连接到数据库: {self.db_path}")

    def create_tables(self):
        """创建数据库表结构"""
        cursor = self.conn.cursor()

        # 创建文章表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                publish_time DATETIME,
                url TEXT UNIQUE,
                account_name TEXT,
                biz TEXT,
                category TEXT,
                content_path TEXT,
                collected_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建文章统计表（历史记录）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                read_num INTEGER DEFAULT 0,
                like_num INTEGER DEFAULT 0,
                looking_num INTEGER DEFAULT 0,
                in_comment_num INTEGER DEFAULT 0,
                share_num INTEGER DEFAULT 0,
                collect_num INTEGER DEFAULT 0,
                fetched_time DATETIME NOT NULL,
                fetched_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (article_id),
                UNIQUE(article_id, fetched_date)
            )
        """)

        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_category
            ON articles(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_publish_time
            ON articles(publish_time)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_article_id
            ON article_stats(article_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_fetched_date
            ON article_stats(fetched_date)
        """)

        self.conn.commit()
        logger.info("数据库表结构已创建/验证")

    def insert_article(self, article_data: Dict) -> bool:
        """
        插入或更新文章信息

        Args:
            article_data: 文章数据字典，包含 metadata.json 的字段

        Returns:
            bool: 操作是否成功
        """
        try:
            cursor = self.conn.cursor()

            # 从 URL 中提取 article_id (mid 参数)
            url = article_data.get('url', '')
            article_id = self._extract_article_id(url)

            if not article_id:
                logger.error(f"无法提取文章 ID: {url}")
                return False

            # 准备数据
            data = {
                'article_id': article_id,
                'title': article_data.get('title'),
                'author': article_data.get('author'),
                'publish_time': article_data.get('publish_time'),
                'url': url,
                'account_name': article_data.get('account_name'),
                'biz': article_data.get('biz'),
                'category': article_data.get('category'),
                'content_path': article_data.get('content_path'),
                'collected_time': article_data.get('collected_time'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 使用 INSERT OR REPLACE 实现 upsert
            cursor.execute("""
                INSERT OR REPLACE INTO articles
                (article_id, title, author, publish_time, url, account_name,
                 biz, category, content_path, collected_time, updated_at)
                VALUES
                (:article_id, :title, :author, :publish_time, :url, :account_name,
                 :biz, :category, :content_path, :collected_time, :updated_at)
            """, data)

            self.conn.commit()
            logger.info(f"已保存文章: {article_id} - {data['title']}")
            return True

        except Exception as e:
            logger.error(f"插入文章失败: {e}")
            self.conn.rollback()
            return False

    def insert_article_stats(self, article_id: str, stats_data: Dict) -> bool:
        """
        插入文章统计数据

        Args:
            article_id: 文章 ID
            stats_data: 统计数据字典，包含 stats_metadata.json 的字段

        Returns:
            bool: 操作是否成功
        """
        try:
            cursor = self.conn.cursor()

            data = {
                'article_id': article_id,
                'read_num': stats_data.get('read_num', 0),
                'like_num': stats_data.get('like_num', 0),
                'looking_num': stats_data.get('looking_num', 0),
                'in_comment_num': stats_data.get('in_comment_num', 0),
                'share_num': stats_data.get('share_num', 0),
                'collect_num': stats_data.get('collect_num', 0),
                'fetched_time': stats_data.get('fetched_time'),
                'fetched_date': stats_data.get('fetched_date')
            }

            # 使用 INSERT OR IGNORE 避免重复插入同一天的数据
            cursor.execute("""
                INSERT OR IGNORE INTO article_stats
                (article_id, read_num, like_num, looking_num, in_comment_num,
                 share_num, collect_num, fetched_time, fetched_date)
                VALUES
                (:article_id, :read_num, :like_num, :looking_num, :in_comment_num,
                 :share_num, :collect_num, :fetched_time, :fetched_date)
            """, data)

            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"已保存统计数据: {article_id} - {data['fetched_date']}")
            return True

        except Exception as e:
            logger.error(f"插入统计数据失败: {e}")
            self.conn.rollback()
            return False

    def get_article(self, article_id: str) -> Optional[Dict]:
        """
        获取文章信息

        Args:
            article_id: 文章 ID

        Returns:
            文章信息字典或 None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE article_id = ?", (article_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_article_stats(self, article_id: str) -> List[Dict]:
        """
        获取文章的所有统计数据（按日期排序）

        Args:
            article_id: 文章 ID

        Returns:
            统计数据列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM article_stats
            WHERE article_id = ?
            ORDER BY fetched_date ASC
        """, (article_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_latest_articles(self, limit: int = 50, category: Optional[str] = None) -> List[Dict]:
        """
        获取最新文章列表（带最新统计数据）

        Args:
            limit: 返回数量限制
            category: 可选的分类筛选

        Returns:
            文章列表，每篇文章包含最新统计数据
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                a.*,
                s.read_num,
                s.like_num,
                s.looking_num,
                s.in_comment_num,
                s.share_num,
                s.collect_num,
                s.fetched_date as latest_stats_date
            FROM articles a
            LEFT JOIN (
                SELECT article_id,
                       read_num, like_num, looking_num, in_comment_num,
                       share_num, collect_num, fetched_date
                FROM article_stats
                WHERE (article_id, fetched_date) IN (
                    SELECT article_id, MAX(fetched_date)
                    FROM article_stats
                    GROUP BY article_id
                )
            ) s ON a.article_id = s.article_id
        """

        if category:
            query += " WHERE a.category = ?"
            cursor.execute(query + " ORDER BY a.publish_time DESC LIMIT ?", (category, limit))
        else:
            cursor.execute(query + " ORDER BY a.publish_time DESC LIMIT ?", (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_articles_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取指定日期范围内的文章

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            文章列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM articles
            WHERE DATE(publish_time) BETWEEN ? AND ?
            ORDER BY publish_time DESC
        """, (start_date, end_date))

        return [dict(row) for row in cursor.fetchall()]

    def get_stats_summary(self) -> Dict:
        """
        获取数据库统计摘要

        Returns:
            包含总文章数、总统计记录数等信息的字典
        """
        cursor = self.conn.cursor()

        # 文章总数
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]

        # 统计记录总数
        cursor.execute("SELECT COUNT(*) FROM article_stats")
        total_stats = cursor.fetchone()[0]

        # 各分类文章数
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
        """)
        categories = {row[0]: row[1] for row in cursor.fetchall()}

        # 最新文章日期
        cursor.execute("SELECT MAX(publish_time) FROM articles")
        latest_article = cursor.fetchone()[0]

        return {
            'total_articles': total_articles,
            'total_stats_records': total_stats,
            'categories': categories,
            'latest_article_date': latest_article
        }

    def _extract_article_id(self, url: str) -> Optional[str]:
        """
        从文章 URL 中提取 article_id

        支持两种URL格式：
        1. 完整格式: https://mp.weixin.qq.com/s?__biz=xxx&mid=123456...
        2. 短链接格式: https://mp.weixin.qq.com/s/xxxxxx

        Args:
            url: 文章 URL

        Returns:
            article_id 或 None
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

        return None

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("已关闭数据库连接")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    with WechatDatabase() as db:
        # 显示统计信息
        summary = db.get_stats_summary()
        print("\n数据库统计:")
        print(f"总文章数: {summary['total_articles']}")
        print(f"统计记录数: {summary['total_stats_records']}")
        print(f"分类统计: {summary['categories']}")
        print(f"最新文章日期: {summary['latest_article_date']}")
