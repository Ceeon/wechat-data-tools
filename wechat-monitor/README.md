# 微信公众号监控系统

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 一站式解决方案 - 自动监控微信公众号文章，追踪数据变化，生成可视化报表

## 📖 简介

这是一个完整的微信公众号数据监控系统，集成了 RSS 服务和数据采集分析功能。只需一条命令即可启动所有服务，自动完成：

- 📰 每日自动采集公众号文章
- 📊 获取文章互动数据（阅读/点赞/在看/评论）
- 📈 追踪数据变化趋势
- 📋 生成 HTML 可视化报表

**适用人群**：内容创作者、运营人员、数据分析师

---

## ✨ 核心特性

### 🎯 一键部署
- **完整集成**：内置 wechat2rss + 数据监控系统
- **开箱即用**：`docker-compose up -d` 即可运行
- **自动配置**：服务间自动连接，无需手动配置

### 📊 数据采集
- **自动化采集**：每天定时采集昨天发布的文章
- **智能追踪**：自动获取前 1-2 天文章的互动数据
- **历史记录**：支持多次采集，追踪数据增长趋势

### 📈 可视化报表
- **HTML 报表**：美观的数据展示页面
- **搜索筛选**：支持按标题、公众号、分类筛选
- **排序功能**：支持按阅读数、点赞数等排序
- **趋势分析**：展示数据增长趋势和百分比

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────┐
│        Docker Compose 一键部署            │
└──────────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌─────────┐      ┌──────────────┐
│wechat2  │      │   wechat-    │
│  rss    │◄─────│   monitor    │
│(RSS服务)│      │  (监控系统)   │
└─────────┘      └──────────────┘
   4001端口         定时任务9:00

              ▼
    ┌──────────────────┐
    │   本地文件系统    │
    ├──────────────────┤
    │ data/articles/   │ 文章数据
    │ reports/         │ HTML报表
    │ logs/            │ 日志文件
    └──────────────────┘
```

---

## ⚡ 快速安装（推荐）

**一条命令完成所有安装**：

```bash
# 1. 克隆项目
git clone https://github.com/your-username/wechat-data-tools.git
cd wechat-data-tools

# 2. 运行自动化安装脚本（一次搞定！）
bash setup.sh
# 选择 1) wechat-monitor
```

**脚本会自动帮你完成**：

### 步骤 1: 智能安装 Docker
- ✅ 检查 Docker 是否已安装
- ✅ 如未安装，自动检测你的操作系统
- ✅ **Mac 系统**：
  - 自动检测芯片类型（Intel / Apple Silicon）
  - 下载对应版本的 Docker.dmg 到下载文件夹
  - 自动打开 .dmg 安装程序
  - 提供详细安装步骤指引
- ✅ **Windows 系统**：
  - 下载 Docker Desktop 安装程序到下载文件夹
  - 自动打开 .exe 安装程序
  - 提供详细安装步骤指引
- ✅ **Linux 系统**：
  - 提供官方一键安装脚本
  - 询问是否立即执行自动安装

### 步骤 2: 获取密钥
- ✅ 自动打开 [Wechat2RSS 官网](https://wechat2rss.xlab.app/deploy/)
- ✅ 自动打开 [极致了官网](https://dajiala.com/main/interface?actnav=0)
- ✅ 交互式引导你输入激活码和 API Key

### 步骤 3: 生成配置
- ✅ 自动生成 `.env` 配置文件
- ✅ 自动创建 `config.yaml` 和 `subscriptions.csv`
- ✅ 询问是否编辑订阅源

### 步骤 4: 启动服务
- ✅ 询问是否立即启动
- ✅ 自动执行 `docker-compose up -d`
- ✅ **同时启动 wechat2rss (RSS服务) + wechat-monitor (监控系统)**
- ✅ 自动打开 RSS 管理页面

**全程只需按提示操作，无需手动输入命令！**

---

## 📋 手动安装（可选）

如果你想手动完成准备工作，请按照以下步骤：

## 安装前准备

在开始之前，需要准备以下 3 样东西：

### 1️⃣ 安装 Docker

根据你的操作系统选择：

**macOS**：
```bash
# 下载 Docker Desktop for Mac
# 访问: https://www.docker.com/products/docker-desktop/

# 或使用 Homebrew 安装
brew install --cask docker
```

**Windows**：
```bash
# 下载 Docker Desktop for Windows
# 访问: https://www.docker.com/products/docker-desktop/
```

**Linux (Ubuntu/Debian)**：
```bash
# 使用官方脚本一键安装
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

**验证安装**：
```bash
docker --version
docker-compose --version
```

---

### 2️⃣ 获取 Wechat2RSS 激活码

**步骤**：

1. 访问官网：**https://wechat2rss.xlab.app/deploy/**
2. 点击 "获取激活码"
3. 填写邮箱，获取激活码
4. 保存邮箱和激活码（后面配置会用到）

**快速打开**：
```bash
# macOS/Linux
open https://wechat2rss.xlab.app/deploy/

# Windows
start https://wechat2rss.xlab.app/deploy/
```

---

### 3️⃣ 获取极致了 API Key

**步骤**：

1. 访问官网：**https://dajiala.com/main/interface?actnav=0**
2. 注册/登录账号
3. 充值（建议充值 ¥50，可用一个多月）
4. 复制 API Key

**快速打开**：
```bash
# macOS/Linux
open https://dajiala.com/main/interface?actnav=0

# Windows
start https://dajiala.com/main/interface?actnav=0
```

**💡 提示**：极致了 API 用于获取文章互动数据（阅读数、点赞数等）

---

## 🚀 快速开始

准备好上面 3 样东西后，开始部署：

### 部署步骤

#### 1️⃣ 克隆项目

```bash
git clone https://github.com/your-username/wechat-monitor.git
cd wechat-monitor
```

#### 2️⃣ 配置密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件（只需填写 3 项）
vi .env
```

填写以下 3 项必填配置：

```bash
# Wechat2RSS 许可证
WECHAT2RSS_EMAIL=your_email@example.com
WECHAT2RSS_LICENSE=your-license-code

# 极致了 API Key
JIZHILE_API_KEY=your_jizhile_api_key
```

#### 3️⃣ 配置订阅源

```bash
# 复制配置模板
cp config/config.yaml.example config/config.yaml
cp config/subscriptions.csv.example config/subscriptions.csv

# 编辑订阅源（添加要监控的公众号）
vi config/subscriptions.csv
```

订阅源格式：

```csv
name,biz,rss_url,category
AI产品自由,MzU3MjU5Mzc2Nw==,http://localhost:4001/feed/xxx,AI
```

#### 4️⃣ 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看启动状态
docker-compose ps

# 查看日志（可选）
docker-compose logs -f
```

#### 5️⃣ 验证部署

```bash
# 访问 RSS 服务
open http://localhost:4001

# 手动执行一次任务（测试）
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py

# 查看报表
open ./reports/all_articles.html
```

✅ **完成！** 系统将在每天早上 9:00 自动运行。

---

## 📁 项目结构

```
wechat-monitor/
├── config/                          # 配置文件
│   ├── config.yaml.example          # API 配置模板
│   └── subscriptions.csv.example    # 订阅源模板
│
├── scripts/                         # 核心脚本
│   ├── daily_auto_workflow.py       # 完整自动化流程
│   ├── daily_fetch.py               # 文章采集
│   ├── fetch_recent_days_stats.py   # 获取前1-2天数据
│   ├── generate_report.py           # 报表生成
│   └── utils/
│       └── jizhile_api.py           # 极致了API封装
│
├── data/                            # 数据存储（自动生成）
├── reports/                         # 报表输出（自动生成）
├── logs/                            # 日志文件（自动生成）
├── wechat2rss-data/                 # RSS数据（自动生成）
│
├── docker-compose.yml               # Docker编排文件
├── Dockerfile                       # 监控系统镜像
├── entrypoint.sh                    # 容器启动脚本
├── crontab                          # 定时任务配置
├── requirements.txt                 # Python依赖
└── README.md                        # 项目文档
```

---

## 🔧 常用命令

### Docker 管理

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down
```

### 手动执行任务

```bash
# 执行完整流程（采集+数据+报表）
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py

# 只采集文章
docker-compose exec wechat-monitor python3 /app/scripts/daily_fetch.py --mode yesterday

# 只获取互动数据
docker-compose exec wechat-monitor python3 /app/scripts/fetch_recent_days_stats.py

# 只生成报表
docker-compose exec wechat-monitor python3 /app/scripts/generate_report.py
```

### 数据管理

```bash
# 备份数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/ reports/

# 查看数据统计
docker-compose exec wechat-monitor ls -lh /app/data/articles/ | wc -l
```

---

## 📊 工作流程

系统每天自动执行以下流程：

```
┌────────────────────────┐
│  早上 9:00 定时触发     │
└────────────────────────┘
           │
           ▼
┌────────────────────────┐
│ ① 采集昨天的文章        │
│   - 从 RSS 获取列表     │
│   - 下载文章内容        │
│   - 保存为 Markdown     │
└────────────────────────┘
           │
           ▼
┌────────────────────────┐
│ ② 获取互动数据          │
│   - 识别前1-2天文章     │
│   - 调用极致了 API      │
│   - 保存最新数据        │
│   - 更新历史记录        │
└────────────────────────┘
           │
           ▼
┌────────────────────────┐
│ ③ 生成数据报表          │
│   - 汇总所有文章        │
│   - 生成 HTML 页面      │
│   - 支持搜索筛选        │
└────────────────────────┘
```

---

## 💰 成本说明

### API 费用

- **极致了 API**：约 ¥0.05/篇
- **Wechat2RSS**：免费（需激活码）

**每日消耗**（假设每天 10 篇新文章，获取前 1-2 天共 20 篇数据）：
- 合计：¥1.0/天
- 月成本：约 ¥30/月

### 服务器费用

- **本地运行**：免费
- **云服务器**：约 ¥50-100/月（根据配置）

---

## 🐛 故障排查

### 问题 1: API 余额不足

**现象**：
```
⚠️  API返回错误: 金额不足，请充值
```

**解决**：登录 [极致了](https://jizhile.com/) 充值

---

### 问题 2: RSS 服务无法访问

**现象**：文章采集失败，网络超时

**解决**：
```bash
# 检查 wechat2rss 容器状态
docker-compose ps

# 查看 wechat2rss 日志
docker-compose logs wechat2rss

# 重启 RSS 服务
docker-compose restart wechat2rss
```

---

### 问题 3: 许可证错误

**现象**：wechat2rss 容器不断重启

**解决**：
1. 访问 [重新绑定页面](https://wechat2rss.xlab.app/deploy/active.html)
2. 使用邮箱和激活码重新绑定
3. 重启容器：`docker-compose restart wechat2rss`

---

### 问题 4: 定时任务未执行

**现象**：数据没有自动更新

**解决**：
```bash
# 查看 cron 日志
docker-compose logs wechat-monitor

# 检查 cron 是否运行
docker-compose exec wechat-monitor service cron status

# 手动测试
docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py
```

---

## 🤝 贡献指南

欢迎贡献代码、提出问题或建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 开源协议

本项目采用 [MIT 许可证](LICENSE)

---

## 🙏 致谢

- [Wechat2RSS](https://github.com/ttttmr/wechat2rss) - 提供 RSS 服务
- [极致了](https://jizhile.com/) - 提供互动数据 API
- 所有贡献者

---

## 📧 联系方式

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/your-username/wechat-monitor/issues)
- 发送邮件

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

Made with ❤️ by [Your Name]

</div>
