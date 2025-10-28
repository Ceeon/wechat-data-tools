#!/bin/bash

# 微信公众号数据分析工具集 - 快速安装
# 这是工作区的总入口脚本

set -e

echo "======================================"
echo "📦 微信公众号数据分析工具集"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检测操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=Mac;;
    CYGWIN*|MINGW*|MSYS*) PLATFORM=Windows;;
    *)          PLATFORM="UNKNOWN"
esac

echo "欢迎使用微信公众号数据分析工具！"
echo ""
echo "本工作区包含以下项目："
echo ""
echo "  1. ${GREEN}wechat-monitor${NC} (推荐) - 完整监控系统"
echo "     包含 RSS 服务 + 数据采集 + 报表生成"
echo "     一键部署，自动化程度最高"
echo ""
echo "  2. ${YELLOW}wechat2rss-docker${NC} - 独立 RSS 服务"
echo "     仅提供 RSS 订阅功能"
echo ""

read -p "请选择要安装的项目 (1/2): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "======================================"
        echo "🚀 安装 wechat-monitor"
        echo "======================================"
        echo ""

        # ============================================
        # 步骤 1: 检查 Docker
        # ============================================
        echo "======================================"
        echo "📦 步骤 1/3: 检查 Docker"
        echo "======================================"

        if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
            DOCKER_VERSION=$(docker --version)
            COMPOSE_VERSION=$(docker-compose --version)
            echo -e "${GREEN}✅ Docker 已安装${NC}"
            echo "   版本: $DOCKER_VERSION"
            echo "   Docker Compose: $COMPOSE_VERSION"
        else
            echo -e "${RED}❌ Docker 未安装${NC}"
            echo ""
            echo "正在为您自动下载 Docker Desktop..."
            echo ""

            if [ "$PLATFORM" = "Mac" ]; then
                # 检测 Mac 芯片架构
                ARCH=$(uname -m)
                if [ "$ARCH" = "arm64" ]; then
                    DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
                    CHIP_TYPE="Apple Silicon (M1/M2/M3)"
                else
                    DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
                    CHIP_TYPE="Intel"
                fi

                echo "检测到 Mac 系统 - $CHIP_TYPE"
                echo "下载地址: $DOCKER_URL"
                echo ""

                # 下载到下载文件夹
                DOWNLOAD_DIR="$HOME/Downloads"
                DOCKER_FILE="$DOWNLOAD_DIR/Docker.dmg"

                echo "正在下载 Docker Desktop 到: $DOCKER_FILE"
                echo "请稍候..."

                if curl -L -o "$DOCKER_FILE" "$DOCKER_URL"; then
                    echo ""
                    echo -e "${GREEN}✅ 下载完成！${NC}"
                    echo "安装包位置: $DOCKER_FILE"
                    echo ""
                    echo "正在自动打开安装程序..."
                    sleep 1
                    open "$DOCKER_FILE"
                    echo ""
                    echo -e "${YELLOW}📝 安装步骤：${NC}"
                    echo "   1. 将 Docker 图标拖动到 Applications 文件夹"
                    echo "   2. 从 Applications 启动 Docker"
                    echo "   3. 等待 Docker 启动完成（状态栏会显示）"
                    echo "   4. 回到这里按回车继续"
                else
                    echo ""
                    echo -e "${RED}❌ 下载失败${NC}"
                    echo "请手动访问下载: https://www.docker.com/products/docker-desktop/"
                    echo "或使用 Homebrew 安装: brew install --cask docker"
                fi

            elif [ "$PLATFORM" = "Windows" ]; then
                DOCKER_URL="https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

                echo "检测到 Windows 系统"
                echo "下载地址: $DOCKER_URL"
                echo ""

                # 下载到下载文件夹
                DOWNLOAD_DIR="$HOME/Downloads"
                DOCKER_FILE="$DOWNLOAD_DIR/DockerDesktopInstaller.exe"

                echo "正在下载 Docker Desktop 到: $DOCKER_FILE"
                echo "请稍候..."

                if curl -L -o "$DOCKER_FILE" "$DOCKER_URL"; then
                    echo ""
                    echo -e "${GREEN}✅ 下载完成！${NC}"
                    echo "安装包位置: $DOCKER_FILE"
                    echo ""
                    echo "正在自动打开安装程序..."
                    sleep 1
                    # Windows 下使用 cmd.exe 来启动
                    cmd.exe /c start "" "$DOCKER_FILE" 2>/dev/null || explorer.exe "$DOCKER_FILE" 2>/dev/null || echo "请手动打开: $DOCKER_FILE"
                    echo ""
                    echo -e "${YELLOW}📝 安装步骤：${NC}"
                    echo "   1. 按照安装向导完成安装"
                    echo "   2. 安装完成后启动 Docker Desktop"
                    echo "   3. 等待 Docker 启动完成"
                    echo "   4. 回到这里按回车继续"
                else
                    echo ""
                    echo -e "${RED}❌ 下载失败${NC}"
                    echo "请手动访问下载: https://www.docker.com/products/docker-desktop/"
                fi

            elif [ "$PLATFORM" = "Linux" ]; then
                echo "检测到 Linux 系统"
                echo ""
                echo "推荐使用官方脚本安装 Docker:"
                echo ""
                echo -e "${YELLOW}自动安装命令：${NC}"
                echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
                echo "  sudo sh get-docker.sh"
                echo "  sudo apt-get install docker-compose-plugin"
                echo ""
                read -p "是否现在执行自动安装? (y/n): " AUTO_INSTALL

                if [ "$AUTO_INSTALL" = "y" ] || [ "$AUTO_INSTALL" = "Y" ]; then
                    echo "开始安装..."
                    curl -fsSL https://get.docker.com -o get-docker.sh
                    sudo sh get-docker.sh
                    sudo apt-get install docker-compose-plugin
                    echo ""
                    echo -e "${GREEN}✅ Docker 安装完成！${NC}"
                fi
            else
                echo "未识别的操作系统"
                echo "请手动访问: https://www.docker.com/products/docker-desktop/"
            fi

            echo ""
            echo -e "${YELLOW}⏸️  安装完成后，请按回车继续...${NC}"
            read
        fi

        echo ""

        # ============================================
        # 步骤 2: 获取 Wechat2RSS 激活码
        # ============================================
        echo "======================================"
        echo "🔑 步骤 2/3: 获取 Wechat2RSS 激活码"
        echo "======================================"

        echo "正在打开 Wechat2RSS 官网..."
        if [ "$PLATFORM" = "Mac" ]; then
            open "https://wechat2rss.xlab.app/deploy/"
        elif [ "$PLATFORM" = "Linux" ]; then
            xdg-open "https://wechat2rss.xlab.app/deploy/" 2>/dev/null || echo "请手动访问: https://wechat2rss.xlab.app/deploy/"
        else
            echo "请访问: https://wechat2rss.xlab.app/deploy/"
        fi

        echo ""
        echo "📝 请在网页上完成以下步骤:"
        echo "   1. 填写邮箱"
        echo "   2. 获取激活码"
        echo "   3. 保存邮箱和激活码（后面配置需要）"
        echo ""

        read -p "获取激活码后，请输入你的邮箱: " WECHAT2RSS_EMAIL
        read -p "请输入激活码: " WECHAT2RSS_LICENSE

        echo ""

        # ============================================
        # 步骤 3: 获取极致了 API Key
        # ============================================
        echo "======================================"
        echo "🔑 步骤 3/3: 获取极致了 API Key"
        echo "======================================"

        echo "正在打开极致了官网..."
        if [ "$PLATFORM" = "Mac" ]; then
            open "https://dajiala.com/main/interface?actnav=0"
        elif [ "$PLATFORM" = "Linux" ]; then
            xdg-open "https://dajiala.com/main/interface?actnav=0" 2>/dev/null || echo "请手动访问: https://dajiala.com/main/interface?actnav=0"
        else
            echo "请访问: https://dajiala.com/main/interface?actnav=0"
        fi

        echo ""
        echo "📝 请在网页上完成以下步骤:"
        echo "   1. 注册/登录账号"
        echo "   2. 充值（建议 ¥50，可用一个多月）"
        echo "   3. 复制 API Key"
        echo ""

        read -p "获取 API Key 后，请输入: " JIZHILE_API_KEY

        echo ""

        # ============================================
        # 生成配置文件
        # ============================================
        echo "======================================"
        echo "⚙️  生成配置文件"
        echo "======================================"

        # 进入 wechat-monitor 目录
        cd wechat-monitor

        # 复制环境变量模板
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✅ 已创建 .env 文件${NC}"

            # 写入配置
            if [ "$PLATFORM" = "Mac" ] || [ "$PLATFORM" = "Linux" ]; then
                sed -i.bak "s/WECHAT2RSS_EMAIL=.*/WECHAT2RSS_EMAIL=$WECHAT2RSS_EMAIL/" .env
                sed -i.bak "s/WECHAT2RSS_LICENSE=.*/WECHAT2RSS_LICENSE=$WECHAT2RSS_LICENSE/" .env
                sed -i.bak "s/JIZHILE_API_KEY=.*/JIZHILE_API_KEY=$JIZHILE_API_KEY/" .env
                rm .env.bak
            fi

            echo -e "${GREEN}✅ 已自动填写配置${NC}"
        else
            echo -e "${YELLOW}⚠️  未找到 .env.example 文件${NC}"
        fi

        # 复制配置文件模板
        if [ ! -f "config/config.yaml" ] && [ -f "config/config.yaml.example" ]; then
            cp config/config.yaml.example config/config.yaml
            echo -e "${GREEN}✅ 已创建 config.yaml${NC}"
        fi

        if [ ! -f "config/subscriptions.csv" ] && [ -f "config/subscriptions.csv.example" ]; then
            cp config/subscriptions.csv.example config/subscriptions.csv
            echo -e "${GREEN}✅ 已创建 subscriptions.csv${NC}"
        fi

        echo ""

        # ============================================
        # 完成配置，询问是否启动服务
        # ============================================
        echo "======================================"
        echo "✅ 配置完成！"
        echo "======================================"
        echo ""
        echo "下一步需要编辑订阅源（添加要监控的公众号）"
        echo ""

        read -p "是否现在编辑订阅源? (y/n): " EDIT_SUBS

        if [ "$EDIT_SUBS" = "y" ] || [ "$EDIT_SUBS" = "Y" ]; then
            ${EDITOR:-vi} config/subscriptions.csv
        fi

        echo ""
        echo "======================================"
        echo "🚀 启动服务"
        echo "======================================"
        echo ""
        echo "即将启动 Docker 服务，包括："
        echo "  1. wechat2rss (RSS 服务)"
        echo "  2. wechat-monitor (监控系统)"
        echo ""

        read -p "是否现在启动服务? (y/n): " START_SERVICE

        if [ "$START_SERVICE" = "y" ] || [ "$START_SERVICE" = "Y" ]; then
            echo ""
            echo "正在启动服务..."

            # 构建并启动
            docker-compose up -d

            echo ""
            echo "⏳ 等待服务启动..."
            sleep 5

            # 检查容器状态
            echo ""
            echo "======================================"
            echo "📊 服务状态"
            echo "======================================"
            docker-compose ps

            echo ""
            echo "======================================"
            echo "✅ 安装完成！"
            echo "======================================"
            echo ""
            echo "📝 常用命令："
            echo ""
            echo "  查看日志:   ${GREEN}docker-compose logs -f${NC}"
            echo "  重启服务:   ${GREEN}docker-compose restart${NC}"
            echo "  停止服务:   ${GREEN}docker-compose stop${NC}"
            echo "  查看报表:   ${GREEN}open ./reports/all_articles.html${NC}"
            echo ""
            echo "  手动执行:   ${GREEN}docker-compose exec wechat-monitor python3 /app/scripts/daily_auto_workflow.py${NC}"
            echo ""
            echo "📖 详细文档: ${YELLOW}README.md${NC}"
            echo ""

            # 打开 RSS 服务页面
            echo "正在打开 RSS 服务管理页面..."
            sleep 2
            if [ "$PLATFORM" = "Mac" ]; then
                open "http://localhost:4001"
            elif [ "$PLATFORM" = "Linux" ]; then
                xdg-open "http://localhost:4001" 2>/dev/null
            fi
        else
            echo ""
            echo "======================================"
            echo "📋 手动启动步骤"
            echo "======================================"
            echo ""
            echo "1. 编辑订阅源:"
            echo "   ${YELLOW}vi config/subscriptions.csv${NC}"
            echo ""
            echo "2. 启动服务:"
            echo "   ${GREEN}docker-compose up -d${NC}"
            echo ""
            echo "3. 查看状态:"
            echo "   ${GREEN}docker-compose ps${NC}"
            echo ""
            echo "4. 查看报表:"
            echo "   ${GREEN}open ./reports/all_articles.html${NC}"
            echo ""
        fi
        ;;
    2)
        echo ""
        echo "======================================"
        echo "🚀 安装 wechat2rss"
        echo "======================================"
        echo ""
        echo "进入 wechat2rss-docker 目录..."
        cd wechat2rss-docker

        echo ""
        echo "启动 wechat2rss 服务..."
        docker-compose -f docker-compose-wechat2rss.yml up -d

        echo ""
        echo "✅ wechat2rss 服务已启动！"
        echo ""
        echo "访问: http://localhost:4001"
        echo ""

        # 打开浏览器
        if command -v open &> /dev/null; then
            open "http://localhost:4001"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:4001"
        fi
        ;;
    *)
        echo ""
        echo "无效选择，退出。"
        exit 1
        ;;
esac
