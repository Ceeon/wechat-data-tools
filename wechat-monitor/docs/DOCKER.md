# Docker 部署指南

## 系统架构

### 服务组成

系统由两个 Docker 容器组成（通过 `docker-compose.yml` 编排）：

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │   wechat2rss     │         │ wechat-monitor   │     │
│  │                  │         │                  │     │
│  │ - 提供 RSS 订阅  │◄────────┤ - 采集文章       │     │
│  │ - 端口: 4001     │         │ - 获取互动数据   │     │
│  │                  │         │ - 生成报表       │     │
│  └──────────────────┘         │ - SQLite 数据库  │     │
│                                └──────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 1. wechat2rss（第三方服务）
- **职责**: 提供微信公众号 RSS 订阅
- **端口**: 4001 (映射到容器内 8080)
- **镜像**: `ttttmr/wechat2rss:latest`
- **配置**: 需要付费许可证（LIC_EMAIL + LIC_CODE）
- **数据持久化**: `./wechat2rss-data`

### 2. wechat-monitor（监控系统）
- **职责**: 数据采集、存储、分析、报表生成
- **构建**: 从本地 `Dockerfile` 构建
- **定时任务**: 每天 9:00 自动执行采集流程（cron）
- **数据存储**: SQLite 数据库 + JSON 文件备份
- **数据持久化**:
  - `./data` - 文章数据和数据库
  - `./reports` - HTML 报表
  - `./config` - 配置文件
  - `./logs` - 日志文件

## 快速开始

### 1. 准备工作

#### 配置环境变量

创建 `.env` 文件（在 `wechat-monitor/` 目录下）：

```bash
# wechat2rss 配置
WECHAT2RSS_EMAIL=your-email@example.com
WECHAT2RSS_LICENSE=your-license-code
WECHAT2RSS_PORT=4001

# 极致了 API 配置
JIZHILE_API_KEY=your-api-key
```

#### 配置订阅列表

编辑 `config/subscriptions.csv`：

```csv
name,biz,rss_url,category
AI产品自由,3572593767,http://localhost:4001/feed/3572593767?k=TOKEN,AI
```

**注意**: RSS Token 需要从容器日志获取（启动后执行）：

```bash
docker logs wechat2rss 2>&1 | grep "Token:"
```

### 2. 启动服务

```bash
cd wechat-monitor

# 启动所有服务（后台运行）
docker-compose up -d

# 查看日志（实时）
docker-compose logs -f

# 查看特定服务的日志
docker-compose logs -f wechat-monitor
docker-compose logs -f wechat2rss
```

### 3. 验证服务状态

```bash
# 查看容器状态
docker-compose ps

# 应该看到两个容器都在运行
# NAME              STATUS        PORTS
# wechat2rss        Up (healthy)  0.0.0.0:4001->8080/tcp
# wechat-monitor    Up (healthy)
```

访问 RSS 管理界面：
```
http://localhost:4001
```

### 4. 首次运行

容器启动后会自动：

1. **检查数据库**：如果不存在，创建空数据库
2. **迁移数据**：如果发现现有 JSON 文件，自动迁移到数据库
3. **启动定时任务**：每天 9:00 执行自动化流程

查看启动日志：
```bash
docker-compose logs wechat-monitor | head -30
```

应该看到：
```
🗄️  数据库不存在，正在初始化...
📝 创建空数据库...
✅ 数据库创建成功
📅 启动定时任务服务...
✅ 定时任务服务已启动
```

## 数据库管理

### 数据库位置

```
wechat-monitor/data/wechat_monitor.db
```

### 数据库初始化

容器启动时，`entrypoint.sh` 会自动：

1. **检查数据库是否存在**
   - 如果不存在且有 JSON 数据 → 自动迁移
   - 如果不存在且无数据 → 创建空数据库
   - 如果存在 → 跳过初始化

2. **迁移流程**
   ```bash
   # 容器内自动执行
   python3 /app/scripts/migrate_to_db.py
   ```

### 手动管理数据库

```bash
# 进入容器
docker-compose exec wechat-monitor bash

# 查看数据库统计
python3 scripts/query_db.py --summary

# 查看最新文章
python3 scripts/query_db.py --latest 10

# 查看热门文章
python3 scripts/query_db.py --top 5

# 使用 SQLite 命令行
sqlite3 data/wechat_monitor.db
```

### 数据库备份

```bash
# 方法1: 直接复制数据库文件（推荐）
cp data/wechat_monitor.db data/wechat_monitor_backup_$(date +%Y%m%d).db

# 方法2: 使用 SQLite 导出
docker-compose exec wechat-monitor sqlite3 data/wechat_monitor.db .dump > backup.sql

# 方法3: 备份整个 data 目录
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

## 定时任务管理

### 定时任务配置

文件: `wechat-monitor/crontab`

```cron
# 每天早上 9:00 执行自动化流程
0 9 * * * /usr/local/bin/python3 /app/scripts/daily_auto_workflow.py >> /app/logs/cron_$(date +\%Y\%m\%d).log 2>&1
```

### 自动化流程步骤

`daily_auto_workflow.py` 执行的步骤：

1. **采集昨天的文章** (`daily_fetch.py --mode yesterday`)
2. **同步新文章到数据库** (`migrate_to_db.py`)
3. **获取前1-2天的互动数据** (`fetch_recent_days_stats.py`)
4. **同步统计数据到数据库** (`migrate_to_db.py`)
5. **生成 HTML 报表** (`generate_report.py`)

### 手动执行任务

```bash
# 完整流程
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py

# 单独执行某个步骤
docker-compose exec wechat-monitor python3 /app/scripts/daily_fetch.py --mode yesterday
docker-compose exec wechat-monitor python3 /app/scripts/fetch_recent_days_stats.py
docker-compose exec wechat-monitor python3 /app/scripts/generate_report.py
docker-compose exec wechat-monitor python3 /app/scripts/migrate_to_db.py
```

### 查看定时任务日志

```bash
# 查看今天的日志
docker-compose exec wechat-monitor tail -f /app/logs/cron_$(date +%Y%m%d).log

# 查看历史日志
docker-compose exec wechat-monitor ls -lh /app/logs/
```

## 常用命令

### 容器管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 重新构建并启动（代码变更后）
docker-compose up -d --build

# 只重新构建监控服务
docker-compose up -d --build wechat-monitor
```

### 数据管理

```bash
# 查看数据库大小
du -h data/wechat_monitor.db

# 统计文章数量
docker-compose exec wechat-monitor python3 scripts/query_db.py --summary

# 生成报表
docker-compose exec wechat-monitor python3 scripts/generate_report.py

# 查看报表
open reports/all_articles.html  # macOS
xdg-open reports/all_articles.html  # Linux
```

### 日志查看

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看最近100行
docker-compose logs --tail=100

# 只看监控系统日志
docker-compose logs -f wechat-monitor

# 只看 RSS 服务日志
docker-compose logs -f wechat2rss
```

### 容器交互

```bash
# 进入容器 shell
docker-compose exec wechat-monitor bash

# 查看容器内文件
docker-compose exec wechat-monitor ls -la /app/data/

# 执行 Python 脚本
docker-compose exec wechat-monitor python3 /app/scripts/query_db.py --top 5
```

## 数据流程图

```
┌─────────────────┐
│  RSS 订阅源     │
│  (wechat2rss)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│  daily_fetch.py │──────▶│  JSON 文件      │
│  (采集文章)     │       │  (data/articles)│
└─────────────────┘       └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ migrate_to_db.py│
                          │  (数据迁移)     │
                          └────────┬────────┘
                                   │
                                   ▼
         ┌─────────────────────────┴─────────────────────────┐
         │                                                     │
         ▼                                                     ▼
┌─────────────────┐                               ┌─────────────────┐
│  极致了 API     │                               │  SQLite 数据库  │
│  (获取互动数据) │                               │  (wechat_       │
└────────┬────────┘                               │   monitor.db)   │
         │                                        └────────┬────────┘
         ▼                                                 │
┌─────────────────┐                                       │
│fetch_recent_    │                                       │
│days_stats.py    │──────▶更新统计数据────────────────────┘
└─────────────────┘
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│ generate_       │──────▶│  HTML 报表      │
│ report.py       │       │  (reports/)     │
└─────────────────┘       └─────────────────┘
```

## 故障排查

### 1. wechat2rss 容器 unhealthy

**症状**: `docker-compose ps` 显示 wechat2rss 状态为 unhealthy

**原因**:
- 许可证绑定到旧容器
- 网络连接问题

**解决方案**:

```bash
# 查看详细日志
docker logs wechat2rss

# 如果看到 "lic error: 激活码已被绑定到其他机器"
# 访问 https://wechat2rss.xlab.app/deploy/active.html 解绑

# 重启容器
docker-compose restart wechat2rss

# 获取新的 RSS Token
docker logs wechat2rss 2>&1 | grep "Token:"
```

### 2. 定时任务未执行

**检查**:

```bash
# 查看 cron 服务状态
docker-compose exec wechat-monitor service cron status

# 查看 cron 日志
docker-compose exec wechat-monitor tail -f /app/logs/cron_*.log

# 手动测试脚本
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py
```

### 3. 数据库锁定

**症状**: "database is locked" 错误

**解决**:

```bash
# 检查是否有其他进程使用数据库
docker-compose exec wechat-monitor lsof data/wechat_monitor.db

# 重启容器
docker-compose restart wechat-monitor
```

### 4. 数据不一致

**症状**: 数据库和 JSON 文件数据不同步

**解决**:

```bash
# 重新迁移数据（会更新已存在的记录）
docker-compose exec wechat-monitor python3 /app/scripts/migrate_to_db.py
```

### 5. API 余额不足

**症状**: 日志中出现 "金额不足，请充值"

**解决**:
1. 登录 https://jizhile.com/
2. 充值（建议 ¥50，约 1 个月）
3. 无需重启服务

## 数据持久化

以下目录通过 Docker volumes 持久化到主机：

```yaml
volumes:
  - ./data:/app/data              # 文章数据 + 数据库
  - ./reports:/app/reports        # HTML 报表
  - ./config:/app/config          # 配置文件
  - ./logs:/app/logs              # 日志文件
  - ./wechat2rss-data:/wechat2rss # RSS 服务数据
```

**重要**: 容器删除后数据不会丢失！

## 更新和重新部署

### 更新代码

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 清理和重建

```bash
# 完全清理（保留数据）
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 完全重置（删除所有数据）
docker-compose down -v  # 危险！会删除所有 volumes
```

## 性能优化建议

1. **定期清理日志**
   ```bash
   # 删除 30 天前的日志
   find logs/ -name "cron_*.log" -mtime +30 -delete
   ```

2. **数据库备份**
   ```bash
   # 设置定期备份（添加到 crontab）
   0 2 * * * cp data/wechat_monitor.db data/backups/backup_$(date +\%Y\%m\%d).db
   ```

3. **监控磁盘空间**
   ```bash
   # 检查数据目录大小
   du -sh data/ reports/ logs/
   ```

## 下一步

- [ ] 添加 Web 管理界面
- [ ] 支持 Webhook 通知
- [ ] 添加数据分析功能
- [ ] 支持更多公众号平台

---

**需要帮助？**
- 查看项目文档: `docs/`
- 查看数据库文档: `docs/DATABASE.md`
- 提交 Issue: GitHub Issues
