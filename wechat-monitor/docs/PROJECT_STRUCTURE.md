# 项目结构

## 目录结构

```
wechat-monitor/
├── config/                    # 配置文件
│   ├── config.yaml           # API 配置（极致了 API Key等）
│   ├── config.yaml.example   # 配置模板
│   ├── subscriptions.csv     # RSS 订阅列表
│   └── subscriptions.csv.example
│
├── data/                      # 数据目录
│   ├── articles/             # 文章 JSON 文件（备份）
│   └── wechat_monitor.db     # SQLite 数据库（主要数据源）
│
├── docs/                      # 文档
│   ├── DATABASE.md           # 数据库使用指南
│   ├── DOCKER.md             # Docker 部署指南
│   └── PROJECT_STRUCTURE.md  # 本文件
│
├── logs/                      # 日志文件
│   └── cron_YYYYMMDD.log     # 定时任务日志
│
├── reports/                   # 生成的HTML报表
│   └── all_articles.html     # 所有文章报表
│
├── scripts/                   # 核心脚本
│   ├── archived/             # 归档的分析脚本
│   │   ├── README.md         # 归档说明
│   │   ├── analyze_*.py      # 各种分析脚本
│   │   └── *.py              # 旧版脚本
│   │
│   ├── utils/                # 工具模块
│   │   ├── database.py       # 数据库管理类
│   │   ├── jizhile_api.py    # 极致了 API 封装
│   │   └── ai_processor.py   # AI 处理工具
│   │
│   ├── daily_auto_workflow.py      # ⭐ 每日自动化流程
│   ├── daily_fetch.py              # 采集文章
│   ├── fetch_recent_days_stats.py  # 获取互动数据
│   ├── generate_report.py          # 生成HTML报表
│   ├── migrate_to_db.py            # 数据迁移到数据库
│   ├── query_db.py                 # 数据库查询工具
│   └── init_db.py                  # 数据库初始化
│
├── wechat2rss-data/          # RSS 服务数据（Docker volume）
│
├── .env                       # 环境变量（敏感信息，不提交）
├── .env.example              # 环境变量模板
├── .gitignore                # Git 忽略规则
├── .dockerignore             # Docker 忽略规则
├── Dockerfile                # Docker 镜像构建
├── docker-compose.yml        # Docker Compose 配置
├── entrypoint.sh             # 容器启动脚本
├── crontab                   # 定时任务配置
├── requirements.txt          # Python 依赖
├── setup.sh                  # 本地安装脚本
├── LICENSE                   # MIT 许可证
└── README.md                 # 项目说明
```

## 核心模块

### 1. 数据采集模块

| 脚本 | 功能 | 使用频率 |
|------|------|---------|
| `daily_fetch.py` | 从 RSS 采集文章 | 每日自动 |
| `fetch_recent_days_stats.py` | 获取文章互动数据 | 每日自动 |

### 2. 数据存储模块

| 文件 | 功能 | 说明 |
|------|------|------|
| `data/wechat_monitor.db` | SQLite 数据库 | ⭐ 主要数据源 |
| `data/articles/` | JSON 文件 | 数据备份 |
| `utils/database.py` | 数据库管理类 | CRUD操作 |
| `migrate_to_db.py` | 数据迁移脚本 | JSON→SQLite |

### 3. 数据分析模块

| 脚本 | 功能 | 位置 |
|------|------|------|
| `generate_report.py` | 生成 HTML 报表 | scripts/ |
| `query_db.py` | 命令行查询工具 | scripts/ |
| `analyze_*.py` | 高级分析功能 | scripts/archived/ |

### 4. 自动化模块

| 文件 | 功能 | 说明 |
|------|------|------|
| `daily_auto_workflow.py` | ⭐ 每日自动化流程 | 核心调度脚本 |
| `crontab` | 定时任务配置 | 每天 9:00 执行 |
| `entrypoint.sh` | 容器启动脚本 | 初始化+启动cron |

## 工作流程

### 每日自动化流程

```
┌─────────────────────────────────────────────────────────┐
│              daily_auto_workflow.py                      │
│               (每天 9:00 自动执行)                       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  1. 采集昨天的文章    │
        │  daily_fetch.py       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  2. 同步到数据库      │
        │  migrate_to_db.py     │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  3. 获取互动数据      │
        │  fetch_recent_days_   │
        │  stats.py             │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  4. 同步统计到数据库  │
        │  migrate_to_db.py     │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  5. 生成HTML报表      │
        │  generate_report.py   │
        └──────────────────────┘
```

## 数据流向

```
RSS订阅 → daily_fetch.py → JSON文件 → migrate_to_db.py → SQLite数据库
                                                              ↓
极致了API → fetch_recent_days_stats.py → JSON文件 → migrate_to_db.py
                                                              ↓
                                                    generate_report.py
                                                              ↓
                                                        HTML报表
```

## 文件说明

### 配置文件

- **`.env`**: 敏感配置（API Key、许可证等），不提交到 Git
- **`config.yaml`**: API 配置
- **`subscriptions.csv`**: RSS 订阅列表

### Docker 文件

- **`Dockerfile`**: 定义监控系统镜像
- **`docker-compose.yml`**: 编排两个服务（wechat2rss + wechat-monitor）
- **`entrypoint.sh`**: 容器启动时的初始化逻辑

### Python 脚本

**核心脚本**（每日使用）：
- `daily_auto_workflow.py` - 主调度脚本
- `daily_fetch.py` - 文章采集
- `fetch_recent_days_stats.py` - 数据获取
- `generate_report.py` - 报表生成
- `migrate_to_db.py` - 数据同步

**工具脚本**：
- `query_db.py` - 数据库查询
- `init_db.py` - 数据库初始化

**归档脚本**（按需使用）：
- `scripts/archived/analyze_*.py` - 各种分析功能

### 工具模块

- **`utils/database.py`**: SQLite 数据库管理类
  - 提供 CRUD 操作
  - 自动创建表结构
  - 查询方法

- **`utils/jizhile_api.py`**: 极致了 API 封装
  - 获取文章互动数据
  - 限流控制

- **`utils/ai_processor.py`**: AI 处理工具
  - 使用 Claude API 进行文本处理

## 数据持久化

### Docker Volumes

```yaml
volumes:
  - ./data:/app/data          # 文章数据 + 数据库
  - ./reports:/app/reports    # HTML 报表
  - ./config:/app/config      # 配置文件
  - ./logs:/app/logs          # 日志文件
```

所有数据都持久化到主机，容器删除后数据不丢失。

## 快速命令

### 日常使用

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f wechat-monitor

# 手动执行采集
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py

# 查看数据库统计
docker-compose exec wechat-monitor python3 /app/scripts/query_db.py --summary

# 生成报表
docker-compose exec wechat-monitor python3 /app/scripts/generate_report.py

# 查看报表
open reports/all_articles.html
```

### 数据库管理

```bash
# 数据迁移
python3 scripts/migrate_to_db.py

# 查询统计
python3 scripts/query_db.py --summary

# 查看最新文章
python3 scripts/query_db.py --latest 10

# 查看热门文章
python3 scripts/query_db.py --top 5

# SQLite 命令行
sqlite3 data/wechat_monitor.db
```

## 扩展开发

### 添加新的分析功能

1. 在 `scripts/` 目录创建新脚本
2. 使用 `utils/database.py` 读取数据
3. 输出结果或生成报表

示例：
```python
from utils.database import WechatDatabase

with WechatDatabase() as db:
    articles = db.get_latest_articles(limit=100)
    # 进行分析...
```

### 添加新的数据源

1. 在 `scripts/` 创建采集脚本
2. 调用 `db.insert_article()` 保存数据
3. 在 `daily_auto_workflow.py` 中添加调用

## 相关文档

- [数据库使用指南](DATABASE.md)
- [Docker 部署指南](DOCKER.md)
- [归档脚本说明](../scripts/archived/README.md)
- [项目说明](../README.md)
