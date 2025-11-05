#!/usr/bin/env python3
"""
数据库初始化脚本
用于 Docker 容器启动时初始化数据库
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import WechatDatabase


def main():
    """主函数"""
    # 数据库路径
    db_path = Path(__file__).parent.parent / "data" / "wechat_monitor.db"

    print(f"初始化数据库: {db_path}")

    try:
        # 创建数据库实例（会自动创建表结构）
        with WechatDatabase(str(db_path)) as db:
            summary = db.get_stats_summary()
            print(f"✅ 数据库初始化成功")
            print(f"   - 文章数: {summary['total_articles']}")
            print(f"   - 统计记录数: {summary['total_stats_records']}")

        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
