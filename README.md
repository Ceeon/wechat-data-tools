# 微信公众号数据分析工具集

> 📦 完整的微信公众号数据采集、分析工具集合

这是一个包含多个工具和项目的工作区，用于微信公众号数据采集、监控和分析。

---

## 📋 项目列表

### 1. ⭐️ wechat-monitor（推荐）

**完整的监控系统 - Docker 一键部署**

```bash
cd wechat-monitor
bash setup.sh          # 自动化安装
docker-compose up -d   # 启动服务
```

**功能**：
- ✅ 集成 RSS 服务 + 数据监控
- ✅ 自动化脚本，打开网页获取密钥
- ✅ 每日自动采集文章
- ✅ 获取互动数据（阅读/点赞/在看/评论）
- ✅ 生成可视化报表
- ✅ 定时任务支持

**文档**: 👉 [wechat-monitor/README.md](./wechat-monitor/README.md)

---

### 2. wechat2rss-docker

**独立的 RSS 服务部署**

如果你只需要 RSS 服务（不需要数据监控），可以使用这个。

```bash
cd wechat2rss-docker
docker-compose -f docker-compose-wechat2rss.yml up -d
```

**说明**: `wechat-monitor` 已整合此服务，推荐使用 `wechat-monitor`。

---

### 3. 其他工具

- `wechat_article_scraper.py` - 单篇文章爬虫（备用）
- `requirements.txt` - 全局 Python 依赖

---

## 🚀 快速开始

### 一键自动安装（推荐）

**从工作区根目录运行**：

```bash
# 克隆项目
git clone https://github.com/your-username/wechat-data-tools.git
cd wechat-data-tools

# 运行自动化安装
bash setup.sh
```

**安装向导会引导你选择**：
1. **wechat-monitor** (推荐) - 完整监控系统
   - ✅ **智能检测 Docker**
     - 已安装：显示版本信息
     - 未安装：自动检测系统（Mac/Windows/Linux）并下载对应版本
     - Mac：自动下载 .dmg（区分 Intel/Apple Silicon）并打开安装程序
     - Windows：自动下载 .exe 并打开安装程序
     - Linux：提供一键安装脚本
   - ✅ 自动打开 [wechat2rss 官网](https://wechat2rss.xlab.app/deploy/) 获取激活码
   - ✅ 自动打开 [极致了官网](https://dajiala.com/main/interface?actnav=0) 获取 API Key
   - ✅ 自动生成配置文件
   - ✅ 一键启动所有服务

2. **wechat2rss-docker** - 仅 RSS 服务
   - ✅ 直接启动 RSS 服务

---

### 手动安装（可选）

**方式一：完整监控系统**
```bash
cd wechat-monitor
bash setup.sh
```

**方式二：仅 RSS 服务**
```bash
cd wechat2rss-docker
docker-compose -f docker-compose-wechat2rss.yml up -d
```

---

## 📂 目录结构

```
公众号数据获取/
├── README.md                    # 本文件（项目总览）
├── requirements.txt             # 全局依赖
│
├── wechat-monitor/              # ⭐️ 完整监控系统（推荐）
│   ├── README.md                # 详细使用文档
│   ├── setup.sh                 # 🚀 自动化安装脚本
│   ├── docker-compose.yml       # Docker 编排（包含 RSS + 监控）
│   ├── Dockerfile               # 监控系统镜像
│   ├── scripts/                 # 核心脚本
│   │   ├── daily_auto_workflow.py
│   │   ├── fetch_recent_days_stats.py
│   │   ├── generate_report.py
│   │   └── ...
│   ├── config/                  # 配置文件
│   ├── data/                    # 数据存储
│   └── reports/                 # 报表输出
│
├── wechat2rss-docker/           # 独立 RSS 服务
│   ├── docker-compose-wechat2rss.yml
│   └── Wechat2RSS部署指南.md
│
└── wechat_article_scraper.py    # 单文章爬虫（备用）
```

---

## 💡 使用建议

| 场景 | 推荐方案 | 说明 |
|------|---------|------|
| 完整数据监控 | `wechat-monitor` | 包含 RSS + 数据采集 + 报表 |
| 只需要 RSS | `wechat2rss-docker` | 仅 RSS 服务 |
| 单篇文章采集 | `wechat_article_scraper.py` | 简单爬虫 |

---

## 🚀 发布到 GitHub

### 推荐：只发布 wechat-monitor

`wechat-monitor` 是完整的独立项目，可以单独发布：

```bash
cd wechat-monitor

# 添加远程仓库
git remote add origin https://github.com/your-username/wechat-monitor.git

# 推送
git push -u origin main
```

用户使用时：

```bash
git clone https://github.com/your-username/wechat-monitor.git
cd wechat-monitor
bash setup.sh
docker-compose up -d
```

---

## 📖 详细文档

- **wechat-monitor**: [wechat-monitor/README.md](./wechat-monitor/README.md)
- **wechat2rss-docker**: [wechat2rss-docker/Wechat2RSS部署指南.md](./wechat2rss-docker/Wechat2RSS部署指南.md)

---

## 💰 成本说明

**wechat-monitor 完整系统**：
- Wechat2RSS: 免费（需激活码）
- 极致了 API: ¥0.05/篇
- 每日消耗: 约 ¥1.0/天
- 月成本: 约 ¥30/月

**服务器**:
- 本地运行: 免费
- 云服务器: ¥50-100/月

---

<div align="center">

**项目路径**: `/Users/chengfeng/Desktop/数据分析/公众号数据获取`

</div>
