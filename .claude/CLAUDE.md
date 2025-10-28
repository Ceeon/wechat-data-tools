# 微信公众号文章监控系统 - 项目说明

## 📋 项目概述

这是一个**自动化监控微信公众号文章**的完整系统,实现:
- 每天自动采集公众号文章
- 获取文章互动数据(阅读、点赞、在看、评论)
- 生成可视化数据报表
- 追踪数据变化趋势

**适用场景**: AI内容创作者、运营人员、数据分析师

---

## 🗂️ 项目结构

```
公众号数据获取/
├── README.md                    # 项目简介
├── claude.md                    # 本文档(项目完整说明)
├── requirements.txt             # Python依赖
│
├── wechat-monitor/             # 核心监控系统 ⭐️
│   ├── claude.md               # 系统详细文档
│   ├── 每日自动化使用说明.md   # 快速使用指南
│   │
│   ├── config/                 # 配置文件
│   │   ├── config.yaml         # API密钥配置
│   │   └── subscriptions.csv   # RSS订阅列表
│   │
│   ├── scripts/                # 核心脚本
│   │   ├── fetch_recent_days_stats.py    # 获取前1-2天数据 ⭐️
│   │   ├── daily_auto_workflow.py        # 完整自动化流程 ⭐️
│   │   ├── daily_fetch.py                # RSS文章采集
│   │   ├── generate_report.py            # 报表生成
│   │   ├── fetch_article_stats.py        # 批量获取互动数据
│   │   ├── smart_fetch_stats.py          # 智能获取策略
│   │   └── utils/
│   │       └── jizhile_api.py            # 极致了API封装
│   │
│   ├── data/                   # 数据存储
│   │   └── articles/           # 文章目录
│   │       └── YYYYMMDD_HHMMSS_ID_标题/
│   │           ├── article.md           # 文章内容
│   │           ├── metadata.json        # 文章元数据
│   │           ├── stats_metadata.json  # 最新互动数据
│   │           └── stats_history.json   # 历史互动数据
│   │
│   ├── reports/                # 数据报表
│   │   └── all_articles.html  # 可视化展示页面
│   │
│   └── logs/                   # 执行日志
│       └── daily_auto_*.log
│
├── wechat2rss-docker/          # RSS服务部署
│   ├── docker-compose.yml      # Docker配置
│   └── Wechat2RSS部署指南.md   # 部署说明
│
└── wechat_article_scraper.py   # 独立采集脚本(备用)
```

---

## 🚀 快速开始

### 第一步: 安装依赖

```bash
cd /Users/chengfeng/Desktop/公众号数据获取
pip3 install -r requirements.txt
```

依赖包:
- `requests` - HTTP请求
- `feedparser` - RSS解析
- `beautifulsoup4` - HTML解析
- `pyyaml` - YAML配置
- `python-dateutil` - 日期处理

### 第二步: 配置API密钥

编辑配置文件:
```bash
vi wechat-monitor/config/config.yaml
```

填入极致了API密钥:
```yaml
jizhile:
  api_key: "your_api_key_here"  # 在 https://jizhile.com/ 获取
```

### 第三步: 配置RSS订阅

编辑订阅列表:
```bash
vi wechat-monitor/config/subscriptions.csv
```

格式:
```csv
name,biz,rss_url,category
AI产品自由,MzU3MjU5Mzc2Nw==,https://your-rss-url,AI
数字生命卡兹克,MzIyMzA5NjEyOA==,https://your-rss-url,AI
```

### 第四步: 手动执行测试

```bash
cd wechat-monitor/scripts

# 测试获取前1-2天的数据
python3 fetch_recent_days_stats.py

# 生成报表
python3 generate_report.py

# 查看报表
open ../reports/all_articles.html
```

### 第五步: 设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加任务(每天早上9点执行)
0 9 * * * cd /Users/chengfeng/Desktop/公众号数据获取/wechat-monitor/scripts && /usr/bin/python3 daily_auto_workflow.py >> /Users/chengfeng/Desktop/公众号数据获取/wechat-monitor/logs/daily_auto_$(date +\%Y\%m\%d).log 2>&1
```

---

## 📊 核心功能详解

### 1. 每日自动化流程

**执行时间**: 每天早上9点(可自定义)

**自动执行步骤**:

#### ① 采集昨天发布的文章
- 从RSS源读取昨天发布的文章列表
- 下载文章内容并保存为Markdown
- 提取文章元数据(标题、作者、发布时间、链接等)
- 保存到 `data/articles/` 目录

#### ② 获取前1-2天文章的互动数据
- 自动识别前1天(昨天)和前2天(前天)发布的文章
- 调用极致了API获取互动数据:
  - ✅ 阅读数 (read_num)
  - ✅ 点赞数 (like_num)
  - ✅ 在看数 (looking_num)
  - ✅ 评论数 (in_comment_num)
  - ✅ 分享数 (share_num)
  - ✅ 收藏数 (collect_num)
- 保存最新数据到 `stats_metadata.json`
- 追加历史记录到 `stats_history.json`

#### ③ 生成数据展示页面
- 汇总所有文章的互动数据
- 生成HTML可视化报表
- 支持排序、搜索、筛选
- 展示前1-2天文章的最新数据

### 2. 核心脚本说明

#### `fetch_recent_days_stats.py` ⭐️ 核心脚本

**功能**: 获取前1-2天发布文章的互动数据

**特点**:
- 全自动,无需用户交互
- 智能识别目标日期
- 自动去重(每天只记录一次)
- API限流保护(0.5秒/次)

**使用**:
```bash
python3 fetch_recent_days_stats.py
```

**输出示例**:
```
============================================================
📊 获取前1-2天发布文章的互动数据
============================================================

📅 目标日期:
   前1天: 2025-10-23
   前2天: 2025-10-22

📁 扫描文章...

📋 找到 13 篇符合条件的文章

[1/13] Vidu Q2的参考生视频...
  📊 获取互动数据...
  ✅ 完成! 阅读:24418, 点赞:879

============================================================
✅ 获取完成!
   成功: 13 篇
   失败: 0 篇
============================================================
```

#### `daily_auto_workflow.py` ⭐️ 完整流程

**功能**: 整合完整自动化流程

**执行步骤**:
1. 采集昨天的文章
2. 获取前1-2天的互动数据
3. 生成HTML报表

**使用**:
```bash
python3 daily_auto_workflow.py
```

#### `daily_fetch.py` - 文章采集

**功能**: 从RSS采集文章

**使用**:
```bash
# 采集昨天的文章
python3 daily_fetch.py --mode yesterday

# 采集今天的文章
python3 daily_fetch.py --mode today

# 采集最近N篇
python3 daily_fetch.py --mode recent --limit 20
```

#### `generate_report.py` - 报表生成

**功能**: 生成HTML数据展示页面

**使用**:
```bash
python3 generate_report.py
```

**输出**: `reports/all_articles.html`

---

## 📈 数据格式

### stats_metadata.json (最新数据)

每篇文章的最新互动数据:

```json
{
  "read_num": 24418,        // 阅读数
  "like_num": 879,          // 点赞数
  "looking_num": 577,       // 在看数
  "in_comment_num": 64,     // 评论数
  "share_num": 0,           // 分享数
  "collect_num": 0,         // 收藏数
  "fetched_time": "2025-10-24 02:23:45",
  "fetched_date": "2025-10-24"
}
```

### stats_history.json (历史数据)

支持数据趋势分析:

```json
{
  "history": [
    {
      "read_num": 20000,
      "like_num": 800,
      "fetched_date": "2025-10-24"
    },
    {
      "read_num": 24418,
      "like_num": 879,
      "fetched_date": "2025-10-25"
    }
  ]
}
```

---

## 💰 成本说明

### API费用

- **极致了API**: 约 ¥0.05/篇
- **每日消耗**:
  - 假设每天采集10篇新文章
  - 获取前1-2天共20篇文章的数据
  - 合计: ¥1.0/天
- **月成本**: 约 ¥30/月

### 服务器费用

- 如果使用本地运行: 免费
- 如果使用云服务器: 根据配置约 ¥50-100/月

---

## 🔧 维护与管理

### 日常检查

```bash
# 查看执行日志
tail -f wechat-monitor/logs/daily_auto_*.log

# 查看定时任务
crontab -l

# 查看API余额(登录极致了平台)
# https://jizhile.com/
```

### 备份数据

```bash
# 备份文章数据
tar -czf articles_backup_$(date +%Y%m%d).tar.gz wechat-monitor/data/articles/

# 备份配置
tar -czf config_backup_$(date +%Y%m%d).tar.gz wechat-monitor/config/
```

### 清理日志

日志会自动清理30天前的记录。手动清理:

```bash
find wechat-monitor/logs -name "*.log" -mtime +30 -delete
```

---

## ⚙️ RSS服务部署 (可选)

如果需要自己部署RSS服务:

```bash
cd wechat2rss-docker

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

详见: `wechat2rss-docker/Wechat2RSS部署指南.md`

---

## 🐛 故障排查

### 问题1: API余额不足

**现象**:
```
⚠️  API返回错误: 金额不足，请充值
```

**解决**:
1. 登录 https://jizhile.com/
2. 充值API余额
3. 检查配置文件中的API Key是否正确

### 问题2: RSS无法访问

**现象**: 文章采集失败,网络超时

**解决**:
1. 检查网络连接
2. 验证RSS URL是否有效
3. 检查wechat2rss服务是否正常运行

### 问题3: 定时任务未执行

**现象**: 数据没有自动更新

**解决**:
```bash
# 查看定时任务
crontab -l

# 查看系统日志
tail -100 wechat-monitor/logs/daily_auto_*.log

# 手动测试
cd wechat-monitor/scripts
python3 daily_auto_workflow.py

# 检查Python路径
which python3
```

### 问题4: 脚本执行报错

**常见错误**:

**依赖缺失**:
```bash
pip3 install -r requirements.txt
```

**权限问题**:
```bash
chmod +x wechat-monitor/scripts/*.py
chmod +x wechat-monitor/scripts/*.sh
```

**路径错误**:
确保在正确的目录执行脚本

---

## 📚 详细文档

- **系统详细文档**: `wechat-monitor/claude.md`
- **快速使用指南**: `wechat-monitor/每日自动化使用说明.md`
- **RSS部署指南**: `wechat2rss-docker/Wechat2RSS部署指南.md`

---

## 🔄 工作流程图

```
┌─────────────────────────────────────────────────────────┐
│               每日自动化工作流 (每天9:00)                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  ① 采集昨天的文章       │
              │  (daily_fetch.py)      │
              │  - 从RSS获取文章列表    │
              │  - 下载文章内容         │
              │  - 保存为Markdown       │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  ② 获取互动数据         │
              │  (fetch_recent_days)   │
              │  - 识别前1-2天文章      │
              │  - 调用极致了API        │
              │  - 保存最新数据         │
              │  - 更新历史记录         │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  ③ 生成数据报表         │
              │  (generate_report.py)  │
              │  - 汇总所有文章数据     │
              │  - 生成HTML页面         │
              │  - 支持排序和搜索       │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  📊 查看报表            │
              │  reports/all_articles  │
              │  .html                 │
              └────────────────────────┘
```

---

## ⚡ 快速命令参考

```bash
# 进入脚本目录
cd /Users/chengfeng/Desktop/公众号数据获取/wechat-monitor/scripts

# 获取前1-2天数据
python3 fetch_recent_days_stats.py

# 完整自动化流程
python3 daily_auto_workflow.py

# 只采集文章
python3 daily_fetch.py --mode yesterday

# 只生成报表
python3 generate_report.py

# 查看定时任务
crontab -l

# 查看日志
tail -f ../logs/daily_auto_*.log

# 打开报表
open ../reports/all_articles.html
```

---

## 📞 技术支持

如有问题,请查阅:
1. 本文档 (`claude.md`)
2. 系统文档 (`wechat-monitor/claude.md`)
3. 使用说明 (`wechat-monitor/每日自动化使用说明.md`)

---

## 📝 更新日志

### 2025-10-24
- ✅ 创建项目完整文档
- ✅ 实现每日自动化流程
- ✅ 创建前1-2天数据获取脚本
- ✅ 修复URL提取正则表达式bug
- ✅ 删除无用的wewe-rss目录
- ✅ 整理项目结构

---

**项目位置**: `/Users/chengfeng/Desktop/公众号数据获取`

**核心脚本**: `wechat-monitor/scripts/fetch_recent_days_stats.py`

**数据报表**: `wechat-monitor/reports/all_articles.html`
