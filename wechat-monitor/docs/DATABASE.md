# SQLite 数据库使用指南

## 概述

为了更高效地管理和查询微信公众号文章数据，我们引入了 SQLite 数据库作为数据存储方案。数据库提供了比 JSON 文件更强大的查询能力和更好的性能。

## 数据库结构

### 表结构

#### 1. articles（文章表）

存储文章的基本信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| article_id | TEXT (PK) | 文章唯一ID（从URL的mid参数提取） |
| title | TEXT | 文章标题 |
| author | TEXT | 作者 |
| publish_time | DATETIME | 发布时间 |
| url | TEXT | 文章URL |
| account_name | TEXT | 公众号名称 |
| biz | TEXT | 公众号BID |
| category | TEXT | 文章分类 |
| content_path | TEXT | Markdown文件路径 |
| collected_time | DATETIME | 采集时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 2. article_stats（统计数据表）

存储文章的互动数据历史记录：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER (PK) | 自增主键 |
| article_id | TEXT (FK) | 文章ID（外键） |
| read_num | INTEGER | 阅读数 |
| like_num | INTEGER | 点赞数 |
| looking_num | INTEGER | 在看数 |
| in_comment_num | INTEGER | 评论数 |
| share_num | INTEGER | 分享数 |
| collect_num | INTEGER | 收藏数 |
| fetched_time | DATETIME | 获取时间 |
| fetched_date | DATE | 获取日期 |
| created_at | DATETIME | 创建时间 |

**特性**：
- `(article_id, fetched_date)` 唯一索引：确保每篇文章每天只记录一次数据
- 支持追踪文章数据的历史变化趋势

### 数据库位置

```
wechat-monitor/data/wechat_monitor.db
```

## 核心脚本

### 1. 数据库管理模块

**路径**: `scripts/utils/database.py`

提供数据库操作的核心类 `WechatDatabase`：

```python
from utils.database import WechatDatabase

# 使用上下文管理器
with WechatDatabase() as db:
    # 插入文章
    db.insert_article(article_data)

    # 插入统计数据
    db.insert_article_stats(article_id, stats_data)

    # 查询文章
    article = db.get_article(article_id)

    # 获取最新文章
    articles = db.get_latest_articles(limit=50)

    # 获取文章统计历史
    stats = db.get_article_stats(article_id)
```

### 2. 数据迁移脚本

**路径**: `scripts/migrate_to_db.py`

将现有的 JSON 文件数据导入到 SQLite 数据库：

```bash
# 迁移所有现有数据
python3 scripts/migrate_to_db.py
```

**功能**：
- 扫描 `data/articles/` 目录
- 读取每个文章的 `metadata.json`
- 读取统计数据（`stats_metadata.json` 和 `stats_history.json`）
- 导入到 SQLite 数据库
- 自动去重（同一文章同一天的数据只保留一份）

### 3. 数据库查询工具

**路径**: `scripts/query_db.py`

提供便捷的命令行查询界面：

```bash
# 显示数据库摘要
python3 scripts/query_db.py --summary

# 显示最新 10 篇文章
python3 scripts/query_db.py --latest 10

# 显示 Top 5 热门文章（按阅读数）
python3 scripts/query_db.py --top 5

# 按点赞数排序
python3 scripts/query_db.py --top 5 --metric like_num

# 显示指定文章的数据趋势
python3 scripts/query_db.py --trend 2247509099

# 搜索文章
python3 scripts/query_db.py --search "Claude"
```

**支持的排序指标**：
- `read_num`: 阅读数（默认）
- `like_num`: 点赞数
- `looking_num`: 在看数
- `in_comment_num`: 评论数

## 常用查询示例

### 使用 Python API

```python
from utils.database import WechatDatabase

with WechatDatabase() as db:
    # 1. 获取数据库统计
    summary = db.get_stats_summary()
    print(f"总文章数: {summary['total_articles']}")
    print(f"统计记录数: {summary['total_stats_records']}")

    # 2. 获取指定分类的最新文章
    ai_articles = db.get_latest_articles(limit=20, category='AI')

    # 3. 获取日期范围内的文章
    articles = db.get_articles_by_date_range('2025-10-01', '2025-10-31')

    # 4. 查看文章数据趋势
    stats = db.get_article_stats('2247509099')
    for stat in stats:
        print(f"{stat['fetched_date']}: {stat['read_num']} 阅读")
```

### 使用 SQL 直接查询

```bash
# 打开数据库
sqlite3 wechat-monitor/data/wechat_monitor.db

# 查询示例
sqlite> -- 查看所有表
SELECT name FROM sqlite_master WHERE type='table';

sqlite> -- 统计文章数
SELECT COUNT(*) FROM articles;

sqlite> -- 查询最新文章
SELECT title, publish_time FROM articles
ORDER BY publish_time DESC LIMIT 10;

sqlite> -- 查询阅读数最高的文章
SELECT a.title, s.read_num, s.fetched_date
FROM articles a
INNER JOIN article_stats s ON a.article_id = s.article_id
ORDER BY s.read_num DESC LIMIT 10;

sqlite> -- 查看文章增长趋势
SELECT fetched_date, read_num, like_num
FROM article_stats
WHERE article_id = '2247509099'
ORDER BY fetched_date;
```

## 数据迁移说明

### 首次迁移

如果这是第一次使用数据库，运行迁移脚本：

```bash
cd wechat-monitor
python3 scripts/migrate_to_db.py
```

**预期输出**：
```
开始数据迁移...
发现 340 个文章目录
✓ 已导入文章 [1/64]: 文章标题
...
============================================================
数据迁移完成！
============================================================
文章数据: 64/64 成功
统计数据: 54/54 成功
```

### 增量更新

目前迁移脚本会：
- 使用 `INSERT OR REPLACE` 更新已存在的文章
- 使用 `INSERT OR IGNORE` 避免重复插入同一天的统计数据

这意味着您可以多次运行迁移脚本而不会产生重复数据。

## 与现有系统集成

### 保持兼容性

目前数据库与 JSON 文件系统**并存**：

- JSON 文件依然保留（用于备份和兼容）
- 数据库提供更快的查询能力
- 未来可以选择只使用数据库或双写模式

### 后续集成计划

1. **数据采集脚本** (`daily_fetch.py`, `fetch_recent_days_stats.py`)
   - 在保存 JSON 的同时，也写入数据库
   - 或只写入数据库，按需导出 JSON

2. **报表生成脚本** (`generate_report.py`)
   - 从数据库读取数据生成报表
   - 性能更好，查询更灵活

## 性能优化

### 索引

数据库已创建以下索引以提高查询性能：

- `idx_articles_category`: 文章分类索引
- `idx_articles_publish_time`: 发布时间索引
- `idx_stats_article_id`: 统计数据文章ID索引
- `idx_stats_fetched_date`: 统计数据获取日期索引

### 查询优化建议

1. **使用 LEFT JOIN 查询最新统计**：避免多次查询
2. **利用索引**：WHERE 条件使用索引字段
3. **限制返回数量**：使用 LIMIT 避免返回过多数据

## 备份与恢复

### 备份数据库

```bash
# 方法1: 直接复制文件
cp wechat-monitor/data/wechat_monitor.db wechat-monitor/data/wechat_monitor_backup.db

# 方法2: 使用 SQLite 备份命令
sqlite3 wechat-monitor/data/wechat_monitor.db ".backup wechat-monitor/data/backup.db"

# 方法3: 导出为 SQL 脚本
sqlite3 wechat-monitor/data/wechat_monitor.db .dump > backup.sql
```

### 恢复数据库

```bash
# 从备份文件恢复
cp wechat-monitor/data/wechat_monitor_backup.db wechat-monitor/data/wechat_monitor.db

# 从 SQL 脚本恢复
sqlite3 wechat-monitor/data/wechat_monitor.db < backup.sql
```

## 故障排查

### 数据库文件不存在

```bash
# 运行迁移脚本创建数据库
python3 scripts/migrate_to_db.py
```

### 数据库锁定

如果遇到 "database is locked" 错误：

```bash
# 检查是否有其他进程正在使用数据库
lsof wechat-monitor/data/wechat_monitor.db

# 关闭所有数据库连接后重试
```

### 数据不一致

如果发现数据库和 JSON 文件不一致：

```bash
# 重新运行迁移脚本（会更新已存在的记录）
python3 scripts/migrate_to_db.py
```

## 依赖项

```bash
# SQLite（通常已预装）
sqlite3 --version

# Python 库（已包含在标准库中）
# - sqlite3: Python 内置

# 查询工具依赖
pip3 install tabulate
```

## 下一步计划

- [ ] 修改数据采集脚本，同时写入数据库
- [ ] 修改报表生成脚本，从数据库读取数据
- [ ] 添加数据库自动备份功能
- [ ] 创建 Web 管理界面
- [ ] 添加数据分析和可视化功能

---

**提示**：如有问题或建议，请查看项目文档或提交 Issue。
