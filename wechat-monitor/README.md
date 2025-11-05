# 微信公众号监控系统

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)

> 🚀 自动监控微信公众号文章，追踪数据变化，生成可视化报表

## 📖 简介

完整的微信公众号数据监控系统，基于 Docker 微服务架构，支持：

- 📰 每日自动采集公众号文章
- 📊 获取文章互动数据（阅读/点赞/在看/评论）
- 🗄️ SQLite 数据库存储与管理
- 📈 追踪数据变化趋势
- 📋 生成 HTML 可视化报表

**适用场景**：内容运营、数据分析、竞品监控

---

## ✨ 核心特性

### 🎯 快速部署
- ✅ Docker Compose 一键启动
- ✅ 自动初始化数据库
- ✅ 开箱即用的定时任务

### 📊 数据管理
- ✅ SQLite 数据库（高效查询）
- ✅ JSON 文件备份（数据安全）
- ✅ 历史数据追踪（趋势分析）
- ✅ 命令行查询工具

### 📈 可视化报表
- ✅ HTML 交互式报表
- ✅ 搜索筛选排序
- ✅ 数据增长趋势
- ✅ 多维度指标分析

---

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- wechat2rss 许可证（[获取方式](https://wechat2rss.xlab.app/)）
- 极致了 API Key（[获取方式](https://jizhile.com/)）

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat-monitor
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# wechat2rss 配置
WECHAT2RSS_EMAIL=your-email@example.com
WECHAT2RSS_LICENSE=your-license-code
WECHAT2RSS_PORT=4001

# 极致了 API 配置
JIZHILE_API_KEY=your-api-key
```

### 3. 配置订阅列表

编辑 `config/subscriptions.csv`：

```csv
name,biz,rss_url,category
AI产品自由,3572593767,http://localhost:4001/feed/3572593767?k=TOKEN,AI
```

### 4. 启动服务

```bash
docker-compose up -d
```

### 5. 获取 RSS Token

```bash
docker logs wechat2rss 2>&1 | grep "Token:"
```

将 Token 更新到 `config/subscriptions.csv` 的 RSS URL 中。

### 6. 查看报表

```bash
# 报表路径
open reports/all_articles.html
```

---

## 📊 数据库管理

### SQLite 数据库

系统使用 SQLite 存储所有数据：

```
data/wechat_monitor.db
```

**表结构**：
- `articles` - 文章信息
- `article_stats` - 互动数据历史

### 查询工具

```bash
# 查看数据库统计
python3 scripts/query_db.py --summary

# 查看最新10篇文章
python3 scripts/query_db.py --latest 10

# 查看Top 5热门文章
python3 scripts/query_db.py --top 5 --metric read_num

# 搜索文章
python3 scripts/query_db.py --search "Claude"
```

### 数据迁移

首次运行或有新数据时：

```bash
python3 scripts/migrate_to_db.py
```

容器启动时会自动检测并迁移数据。

**详细文档**: [数据库使用指南](docs/DATABASE.md)

---

## 🔄 自动化流程

### 定时任务

每天早上 9:00 自动执行：

```
1. 采集昨天的文章 → JSON 文件
2. 同步文章到数据库
3. 获取前1-2天的互动数据 → JSON 文件
4. 同步统计到数据库
5. 生成 HTML 报表（从数据库读取）
```

### 手动执行

```bash
# 完整流程
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py

# 单独步骤
docker-compose exec wechat-monitor python3 /app/scripts/daily_fetch.py --mode yesterday
docker-compose exec wechat-monitor python3 /app/scripts/fetch_recent_days_stats.py
docker-compose exec wechat-monitor python3 /app/scripts/generate_report.py
```

---

## 📋 项目结构

```
wechat-monitor/
├── config/                    # 配置文件
│   ├── config.yaml           # API 配置
│   └── subscriptions.csv     # RSS 订阅列表
│
├── data/                      # 数据目录
│   ├── articles/             # JSON 备份
│   └── wechat_monitor.db     # SQLite 数据库 ⭐
│
├── scripts/                   # 核心脚本
│   ├── daily_auto_workflow.py      # ⭐ 每日自动化
│   ├── daily_fetch.py              # 文章采集
│   ├── fetch_recent_days_stats.py  # 数据获取
│   ├── generate_report.py          # 报表生成
│   ├── migrate_to_db.py            # 数据迁移
│   ├── query_db.py                 # 查询工具
│   ├── init_db.py                  # 数据库初始化
│   ├── archived/                   # 归档的分析脚本
│   └── utils/                      # 工具模块
│       ├── database.py             # 数据库管理类
│       ├── jizhile_api.py          # API 封装
│       └── ai_processor.py         # AI 工具
│
├── reports/                   # HTML 报表
├── logs/                      # 日志文件
├── docs/                      # 文档
│   ├── DATABASE.md           # 数据库指南
│   ├── DOCKER.md             # Docker 指南
│   └── PROJECT_STRUCTURE.md  # 项目结构
│
├── docker-compose.yml        # Docker 编排
├── Dockerfile                # 镜像构建
├── entrypoint.sh             # 启动脚本
├── requirements.txt          # Python 依赖
└── README.md                 # 本文档
```

**详细说明**: [项目结构文档](docs/PROJECT_STRUCTURE.md)

---

## 🛠️ 常用命令

### Docker 管理

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f wechat-monitor

# 重启服务
docker-compose restart wechat-monitor

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build
```

### 数据管理

```bash
# 查看数据库统计
python3 scripts/query_db.py --summary

# 查看热门文章
python3 scripts/query_db.py --top 10

# 数据迁移
python3 scripts/migrate_to_db.py

# 生成报表
python3 scripts/generate_report.py
```

---

## 📚 文档

- [数据库使用指南](docs/DATABASE.md) - SQLite 数据库详细说明
- [Docker 部署指南](docs/DOCKER.md) - 容器化部署完整文档
- [项目结构说明](docs/PROJECT_STRUCTURE.md) - 目录结构和模块说明
- [归档脚本说明](scripts/archived/README.md) - 分析工具使用

---

## 🔧 故障排查

### wechat2rss 服务 unhealthy

```bash
# 查看日志
docker logs wechat2rss

# 如果许可证被绑定，访问解绑页面
# https://wechat2rss.xlab.app/deploy/active.html

# 重启服务
docker-compose restart wechat2rss
```

### 定时任务未执行

```bash
# 查看 cron 状态
docker-compose exec wechat-monitor service cron status

# 查看定时任务日志
docker-compose exec wechat-monitor tail -f /app/logs/cron_*.log

# 手动测试
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py
```

### 数据库问题

```bash
# 检查数据库文件
ls -lh data/wechat_monitor.db

# 重新迁移数据
python3 scripts/migrate_to_db.py

# 查看数据库内容
sqlite3 data/wechat_monitor.db "SELECT COUNT(*) FROM articles;"
```

---

## 🎯 高级功能

### 分析脚本

归档目录提供了额外的分析功能：

```bash
cd scripts/archived

# 话题分析
python3 analyze_topics.py

# 互动分析
python3 analyze_engagement.py

# 时间线分析
python3 analyze_timeline.py
```

**详细说明**: [归档脚本文档](scripts/archived/README.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- [wechat2rss](https://wechat2rss.xlab.app/) - RSS 服务提供
- [极致了](https://jizhile.com/) - 互动数据 API

---

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**⭐ 如果这个项目对你有帮助，欢迎 Star！**
