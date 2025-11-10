# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个**微信公众号监控系统**，使用 Docker 微服务架构自动化采集公众号文章并追踪数据变化。

**核心功能**：
- 每日自动采集公众号文章（从 RSS）
- 获取文章互动数据（阅读/点赞/在看/评论，通过极致了 API）
- 生成 HTML 可视化报表

---

## 系统架构

### 微服务设计

系统由两个 Docker 容器组成（通过 `wechat-monitor/docker-compose.yml` 编排）：

1. **wechat2rss** (第三方服务)
   - 职责：提供微信公众号 RSS 订阅
   - 端口：4001
   - 镜像：`ttttmr/wechat2rss:latest`
   - 需要付费许可证（LIC_EMAIL + LIC_CODE）
   - 配置：从 `.env` 读取 `WECHAT2RSS_EMAIL` 和 `WECHAT2RSS_LICENSE`

2. **wechat-monitor** (自研监控系统)
   - 职责：数据采集、分析、报表生成
   - 构建：从 `wechat-monitor/Dockerfile`
   - 定时任务：每天 9:00 执行自动化流程（通过 cron）
   - 依赖：wechat2rss（通过 Docker 网络 `http://wechat2rss:8080` 访问）

### 关键服务通信

- wechat-monitor 通过 Docker 内部网络访问 wechat2rss
- 外部通过 `http://localhost:4001` 访问 RSS 管理界面
- RSS Token 用于验证订阅请求（从容器日志获取）

---

## Docker 开发命令

### 启动和管理服务

```bash
# 进入项目目录
cd wechat-monitor

# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志（实时）
docker-compose logs -f
docker-compose logs -f wechat2rss      # 只看 RSS 服务
docker-compose logs -f wechat-monitor  # 只看监控系统

# 重启服务
docker-compose restart
docker-compose restart wechat2rss      # 只重启 RSS 服务

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 重新构建并启动（代码变更后）
docker-compose up -d --build
```

### 容器内执行命令

```bash
# 在监控容器内执行 Python 脚本
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py

# 进入容器 shell
docker-compose exec wechat-monitor bash

# 查看 cron 任务
docker-compose exec wechat-monitor crontab -l

# 查看 cron 服务状态
docker-compose exec wechat-monitor service cron status
```

---

## 核心脚本工作流

### 每日自动化流程

主脚本：`wechat-monitor/scripts/daily_auto_workflow.py`

**执行步骤**：
1. 调用 `daily_fetch.py --mode yesterday` 采集昨天的文章
2. 调用 `fetch_recent_days_stats.py` 获取前 1-2 天文章的互动数据
3. 调用 `generate_report.py` 生成 HTML 报表

**定时触发**：
- 容器内 cron 任务：每天早上 9:00
- 配置文件：`wechat-monitor/crontab`
- 日志输出：`/app/logs/cron_YYYYMMDD.log`

### 手动执行脚本

```bash
# 方式1：在容器外（本地有 Python 环境）
cd wechat-monitor/scripts
python3 daily_auto_workflow.py          # 完整流程
python3 fetch_recent_days_stats.py      # 只获取数据
python3 generate_report.py              # 只生成报表

# 方式2：在容器内（推荐，环境一致）
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py
```

### 文章采集模式

`daily_fetch.py` 支持多种模式：

```bash
# 采集昨天的文章
python3 daily_fetch.py --mode yesterday

# 采集今天的文章
python3 daily_fetch.py --mode today

# 采集最近 N 篇文章
python3 daily_fetch.py --mode recent --limit 20
```

---

## 配置文件结构

### 必需配置

1. **`.env`** - Docker 环境变量（敏感信息）
   ```bash
   WECHAT2RSS_EMAIL=your-email@example.com
   WECHAT2RSS_LICENSE=your-license-code
   WECHAT2RSS_PORT=4001
   JIZHILE_API_KEY=your-api-key
   ```

2. **`config/config.yaml`** - API 配置
   ```yaml
   jizhile:
     api_key: "JZL..."
     rate_limit: 0.5  # API 调用间隔（秒）
   ```

3. **`config/subscriptions.csv`** - RSS 订阅列表
   ```csv
   name,biz,rss_url,category
   AI产品自由,3572593767,http://localhost:4001/feed/3572593767?k=TOKEN,AI
   ```
   - `biz`: 公众号 BID（数字 ID）
   - `rss_url`: 包含 RSS Token 的完整 URL
   - TOKEN 从 wechat2rss 容器日志获取

### RSS Token 获取

```bash
# 查看容器日志，找到 "Token: XXXXXXXX" 行
docker logs wechat2rss 2>&1 | grep "Token:"
```

---

## 数据存储结构

### 文章数据目录

```
wechat-monitor/data/articles/
└── YYYYMMDD_HHMMSS_<article_id>_<title>/
    ├── article.md           # 文章 Markdown 内容
    ├── metadata.json        # 文章元数据（标题、作者、发布时间等）
    ├── stats_metadata.json  # 最新互动数据
    └── stats_history.json   # 历史互动数据（追踪趋势）
```

### 关键数据字段

**stats_metadata.json**:
```json
{
  "read_num": 24418,         // 阅读数
  "like_num": 879,           // 点赞数
  "looking_num": 577,        // 在看数
  "in_comment_num": 64,      // 评论数
  "share_num": 0,            // 分享数
  "collect_num": 0,          // 收藏数
  "fetched_time": "2025-10-24 02:23:45",
  "fetched_date": "2025-10-24"
}
```

**stats_history.json**:
```json
{
  "history": [
    {
      "read_num": 20000,
      "fetched_date": "2025-10-24"
    },
    {
      "read_num": 24418,
      "fetched_date": "2025-10-25"
    }
  ]
}
```

---

## 关键实现细节

### 前 1-2 天数据获取策略

**脚本**: `fetch_recent_days_stats.py`

**逻辑**:
1. 计算目标日期：前 1 天（昨天）和前 2 天（前天）
2. 扫描 `data/articles/` 目录，匹配日期前缀的文件夹
3. 检查 `stats_history.json`，去重已采集的日期
4. 调用极致了 API 获取数据（限流 0.5 秒/次）
5. 保存最新数据到 `stats_metadata.json`
6. 追加历史记录到 `stats_history.json`

**去重机制**:
- 每天只记录一次数据（检查 `stats_history.json` 中是否已存在今天的 `fetched_date`）
- 避免重复调用 API 浪费费用

### 极致了 API 调用

**封装**: `scripts/utils/jizhile_api.py`

**费用**: 约 ¥0.05/篇

**限流**:
- 配置文件: `config.yaml` 中 `jizhile.rate_limit`
- 默认: 0.5 秒/次（避免触发反爬）

---

## 故障排查

### wechat2rss 容器状态为 unhealthy

**可能原因**:
1. 许可证绑定到旧容器（重新创建容器后需解绑）
2. 网络连接问题

**解决**:
```bash
# 查看详细日志
docker logs wechat2rss

# 如果看到 "lic error: 激活码已被绑定到其他机器"
# 访问 https://wechat2rss.xlab.app/deploy/active.html 解绑

# 重启容器
docker-compose restart wechat2rss
```

### 定时任务未执行

**检查**:
```bash
# 查看 cron 服务状态
docker-compose exec wechat-monitor service cron status

# 查看 cron 日志
docker-compose exec wechat-monitor tail -f /app/logs/cron_*.log

# 手动测试脚本
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py
```

### API 余额不足

**现象**: 日志中出现 "金额不足，请充值"

**解决**:
1. 登录 https://jizhile.com/
2. 充值（建议 ¥50，可用约 1 个月）
3. 无需重启服务

---

## Windows 开发者注意事项

### 换行符问题（CRLF vs LF）

**问题现象**：Windows 用户构建 Docker 镜像时报错：
```
"/etc/cron.d/wechat-monitor":4: bad minute
errors in crontab file, can't install.
```

**原因**：
- Windows Git 默认将文件换行符从 LF (`\n`) 转换为 CRLF (`\r\n`)
- Linux 容器内的 cron 服务只识别 LF 格式
- CRLF 会导致 crontab 解析失败

**解决方案**：

项目已通过以下方式确保跨平台兼容：

1. **`.gitattributes` 文件**（推荐，自动生效）
   - 项目根目录已配置 `.gitattributes`
   - 强制 `crontab`、`entrypoint.sh` 等文件使用 LF
   - 克隆仓库后自动应用

2. **Dockerfile 防御性转换**（双重保险）
   - 构建时自动移除可能的 `\r` 字符
   - 即使绕过 Git 也能正常工作

**手动修复方法**（如果仍遇到问题）：

```bash
# 方法 1: 配置 Git 换行符策略
git config core.autocrlf input
git rm --cached -r .
git reset --hard

# 方法 2: 使用 WSL 转换文件
wsl sed -i 's/\r$//' wechat-monitor/crontab
wsl sed -i 's/\r$//' wechat-monitor/entrypoint.sh

# 方法 3: 使用编辑器（VS Code）
# 打开文件 -> 右下角点击 "CRLF" -> 选择 "LF" -> 保存
```

**验证换行符格式**：

```bash
# Windows PowerShell
Get-Content wechat-monitor\crontab -Raw | Select-String "`r`n"
# 如果有输出 -> CRLF（需要转换）
# 如果无输出 -> LF（正确）

# WSL/Git Bash
file wechat-monitor/crontab
# 期望输出: ASCII text (无 "with CRLF" 字样)
```

### .env 文件配置

Windows 用户需确保 `.env` 文件存在并配置正确：

```bash
# 检查 .env 文件
cat wechat-monitor\.env

# 如果提示变量未设置，创建 .env 文件
cp wechat-monitor\.env.example wechat-monitor\.env
# 然后编辑填入真实配置
```

### Docker Desktop 要求

- 需要安装 **Docker Desktop for Windows**
- 启用 WSL 2 后端（推荐）
- 确保 Docker 服务正在运行

---

## 添加新公众号订阅

### 方式 1: 通过管理界面

1. 访问 `http://localhost:4001`
2. 输入 RSS Token（从容器日志获取）
3. 添加公众号（输入 BID 或文章链接）

### 方式 2: 通过 API

```bash
# 批量添加多个公众号
for bid in 3572593767 3223096120; do
  curl -s "http://localhost:4001/add/$bid?k=<RSS_TOKEN>"
done
```

### 方式 3: 更新配置文件

编辑 `config/subscriptions.csv`，添加新行（需要先在管理界面添加订阅）

---

## 开发注意事项

### 修改 Python 代码后

```bash
# 重新构建监控容器
docker-compose up -d --build wechat-monitor

# 或者停止、删除、重建
docker-compose down
docker-compose up -d --build
```

### 修改定时任务

1. 编辑 `wechat-monitor/crontab`
2. 重新构建容器（crontab 在构建时复制到镜像）
3. 重启服务

### 数据持久化

以下目录通过 Docker volumes 持久化：
- `data/` - 文章数据
- `reports/` - HTML 报表
- `config/` - 配置文件
- `logs/` - 日志文件
- `wechat2rss-data/` - RSS 服务数据

容器删除后数据不会丢失。

---

## 报表查看

**生成位置**: `wechat-monitor/reports/all_articles.html`

**打开方式**:
```bash
# macOS
open wechat-monitor/reports/all_articles.html

# Linux
xdg-open wechat-monitor/reports/all_articles.html

# Windows
start wechat-monitor/reports/all_articles.html
```

**功能**:
- 搜索筛选（标题、公众号、分类）
- 排序（阅读数、点赞数、在看数）
- 数据趋势（增长百分比）
