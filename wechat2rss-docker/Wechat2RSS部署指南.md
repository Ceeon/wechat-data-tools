# Wechat2RSS 部署指南

## 📋 购买激活码

### 步骤1: 扫码付款

访问官网查看付款二维码：https://wechat2rss.xlab.app/deploy

**价格**：
- 月费：15元/月
- 年费：150元/年（推荐，相当于12.5元/月）

### 步骤2: 备注邮箱

⚠️ **非常重要**：付款时务必备注您的邮箱地址！

### 步骤3: 等待激活码

- 24小时内会收到激活码
- 发件人：i@xlab.app
- 注意检查垃圾邮件箱

---

## 🚀 部署步骤

### 1. 修改配置文件

收到激活码后，编辑配置文件：

```bash
cd ~/Desktop/公众号数据获取/wewe-rss
nano docker-compose-wechat2rss.yml
```

修改以下三处：

```yaml
environment:
  # 填写您的邮箱（必须与付款备注的邮箱一致）
  - LIC_EMAIL=your-email@example.com

  # 填写收到的激活码
  - LIC_CODE=your-license-code-here

  # RSS地址（本地部署保持默认即可）
  - RSS_HOST=http://localhost:3000
```

**示例**：
```yaml
environment:
  - LIC_EMAIL=zhangsan@gmail.com
  - LIC_CODE=ABC123XYZ789
  - RSS_HOST=http://localhost:3000
```

### 2. 启动服务

```bash
# 停止WeWe RSS（避免端口冲突）
docker-compose down

# 启动Wechat2RSS
docker-compose -f docker-compose-wechat2rss.yml up -d

# 查看启动日志
docker logs wechat2rss -f
```

### 3. 访问服务

打开浏览器访问：
```
http://localhost:3000
```

### 4. 登录微信账号

1. 页面会显示微信登录二维码
2. 用微信扫码登录
3. 登录成功后即可添加公众号

---

## 📝 添加公众号

### 方式1: 通过文章链接添加

1. 在Wechat2RSS管理界面点击"添加公众号"
2. 粘贴任意一篇该公众号的文章链接
3. 系统自动识别并添加

### 方式2: 通过BIZ ID添加

如果有公众号的BIZ ID，也可以直接填写：
- 饼干哥哥AGI: `MP_WXS_2394281674`
- 新公众号: `MzkxNzYzODgwNw==`

---

## 🔧 更新 wechat-monitor 配置

添加公众号成功后，更新监控系统的订阅列表：

```bash
cd ~/Desktop/公众号数据获取/wechat-monitor
nano config/subscriptions.csv
```

添加新的公众号：

```csv
name,biz,rss_url,category
饼干哥哥AGI,MP_WXS_2394281674,http://localhost:3000/feed/MP_WXS_2394281674,AI
新公众号,MzkxNzYzODgwNw==,http://localhost:3000/feed/MzkxNzYzODgwNw==,分类
```

⚠️ **注意**：RSS地址从 `localhost:4000` 改为 `localhost:3000`

---

## ✅ 验证部署

### 测试RSS订阅

```bash
# 测试饼干哥哥AGI的RSS
curl http://localhost:3000/feed/MP_WXS_2394281674

# 测试新公众号的RSS
curl http://localhost:3000/feed/MzkxNzYzODgwNw==
```

如果返回XML格式的RSS内容，说明成功！

### 运行采集脚本

```bash
cd ~/Desktop/公众号数据获取/wechat-monitor

# 采集文章
python3 scripts/daily_fetch.py

# 获取互动数据
python3 scripts/fetch_article_stats.py

# 生成报表
python3 scripts/generate_report.py

# 查看报表
open reports/all_articles.html
```

---

## 🔄 日常维护

### 查看服务状态

```bash
docker ps | grep wechat2rss
```

### 查看日志

```bash
docker logs wechat2rss --tail 50
```

### 重启服务

```bash
cd ~/Desktop/公众号数据获取/wewe-rss
docker-compose -f docker-compose-wechat2rss.yml restart
```

### 升级服务

```bash
cd ~/Desktop/公众号数据获取/wewe-rss

# 拉取最新镜像
docker-compose -f docker-compose-wechat2rss.yml pull

# 重启服务
docker-compose -f docker-compose-wechat2rss.yml up -d
```

---

## ❓ 常见问题

### Q1: 激活码24小时后还没收到怎么办？

1. 检查垃圾邮件箱
2. 确认付款时是否备注了邮箱
3. 联系客服（加群反馈）

### Q2: 提示"授权失败"怎么办？

检查：
1. 邮箱是否与付款备注的一致
2. 邮箱是否全小写
3. 激活码是否复制完整

### Q3: 微信扫码后无法登录？

1. 确保网络连接正常
2. 查看Docker日志排查问题
3. 尝试重启服务

### Q4: 如何从WeWe RSS迁移？

1. 在Wechat2RSS中重新添加所有公众号
2. 更新 `subscriptions.csv` 中的RSS地址
3. 停止WeWe RSS服务

---

## 📊 对比WeWe RSS的优势

| 项目 | WeWe RSS | Wechat2RSS |
|------|----------|------------|
| 价格 | 免费 | 15元/月 |
| 稳定性 | ⚠️ Token频繁失效 | ✅ 稳定 |
| 订阅数量 | 受限 | ✅ 不限 |
| 更新频率 | 每小时（容易触发反爬） | 平均6小时 |
| 维护成本 | 高（频繁重新登录） | ✅ 低 |
| 全文输出 | 有 | ✅ 更好 |
| 图片/视频代理 | 基本 | ✅ 完整 |

---

## 📞 获取帮助

- 官方文档：https://wechat2rss.xlab.app
- GitHub：https://github.com/ttttmr/wechat2rss
- 邮箱：i@xlab.app

---

**最后更新**: 2025-10-18
**版本**: v1.0
