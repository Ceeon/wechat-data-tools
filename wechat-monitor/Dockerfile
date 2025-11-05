FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区（中国时区）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 使用国内镜像源（解决网络问题）
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
# - cron: 定时任务
# - curl: 健康检查
# - sqlite3: 数据库命令行工具（可选，用于调试）
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs data/articles reports config

# 复制 crontab 文件并设置权限
COPY crontab /etc/cron.d/wechat-monitor
RUN chmod 0644 /etc/cron.d/wechat-monitor && \
    crontab /etc/cron.d/wechat-monitor

# 复制启动脚本并设置权限
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 暴露端口（如果需要 Web 访问报表）
# EXPOSE 8000

# 设置启动命令
ENTRYPOINT ["/entrypoint.sh"]
