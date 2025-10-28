#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成每日报表
功能: 将采集的文章生成HTML报表
"""

import os
from pathlib import Path
from datetime import datetime
import json


PROJECT_ROOT = Path(__file__).parent.parent


def scan_articles(articles_dir, date_filter=None):
    """
    扫描文章目录

    Args:
        articles_dir: 文章目录
        date_filter: 日期筛选(格式: 20251018)

    Returns:
        list: 文章列表
    """
    articles = []

    for article_folder in Path(articles_dir).glob("*"):
        if not article_folder.is_dir():
            continue

        # 解析文件夹名称: 20251018_033536_id_title
        parts = article_folder.name.split('_')
        if len(parts) < 4:
            continue

        date_str = parts[0]  # 20251018
        time_str = parts[1]  # 033536
        article_id = parts[2]
        title = '_'.join(parts[3:])

        # 日期筛选
        if date_filter and date_str != date_filter:
            continue

        # 读取Markdown文件
        md_file = article_folder / "article.md"
        if not md_file.exists():
            continue

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取元数据 - 优先读取 metadata.json
        metadata = {}
        metadata_file = article_folder / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
                metadata['发布时间'] = meta_data.get('publish_time', '')
                metadata['原文链接'] = meta_data.get('url', '')
                metadata['公众号'] = meta_data.get('account_name', '')
                metadata['分类'] = meta_data.get('category', '')
                metadata['作者'] = meta_data.get('author', '')
                metadata['采集时间'] = meta_data.get('collected_time', '')
        else:
            # 从 Markdown 文件读取元数据
            lines = content.split('\n')
            for line in lines[:15]:  # 只看前15行元数据
                if line.startswith('**'):
                    if '**:' in line:
                        key, value = line.split('**:', 1)
                        key = key.replace('**', '').strip()
                        value = value.strip()
                        metadata[key] = value

        # 获取摘要(前200字)
        content_start = content.find('---')
        if content_start != -1:
            main_content = content[content_start+3:].strip()
            summary = main_content[:200].replace('\n', ' ').strip()
        else:
            summary = "无摘要"

        # 读取互动数据 - 优先读取历史记录
        stats_history_file = article_folder / "stats_history.json"
        stats_list = []

        if stats_history_file.exists():
            # 读取历史记录
            with open(stats_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                stats_list = history_data.get('history', [])
        else:
            # 兼容旧版本,读取单个stats文件
            stats_file = article_folder / "stats_metadata.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    stats_list = [stats]

        # 如果没有任何数据,添加一个空数据
        if not stats_list:
            stats_list = [{}]

        # 为了后续处理,我们保留多个历史记录
        # 先计算最新数据的指标
        stats = stats_list[-1] if stats_list else {}

        # 计算互动指标 (使用最新数据)
        read_num = stats.get('read_num', 0)
        like_num = stats.get('like_num', 0)
        looking_num = stats.get('looking_num', 0)  # 在看数
        comment_num = stats.get('in_comment_num', 0)
        share_num = stats.get('share_num', 0)
        collect_num = stats.get('collect_num', 0)

        # 计算各项指标（避免除零错误）
        if read_num > 0:
            # 1. 互动率 = (点赞数+在看数)/阅读量*1000
            engagement_rate = ((like_num + looking_num) / read_num) * 1000

            # 2. 传播指数 = (转发数×2+在看数)/阅读量*1000
            virality_index = ((share_num * 2 + looking_num) / read_num) * 1000

            # 3. 内容价值指数 = (收藏数×2+评论数)/阅读量*1000
            content_value = ((collect_num * 2 + comment_num) / read_num) * 1000

            # 4. 综合热度分 = (点赞×1+在看×2+评论×3+收藏×4+转发×5)/阅读量×100
            hotness_score = ((like_num * 1 + looking_num * 2 + comment_num * 3 +
                            collect_num * 4 + share_num * 5) / read_num) * 100
        else:
            engagement_rate = 0
            virality_index = 0
            content_value = 0
            hotness_score = 0

        # 提取发布时间（用于排序和显示）
        publish_time_str = metadata.get('发布时间', '')

        # 跳过没有发布时间的文章
        if not publish_time_str:
            continue

        articles.append({
            'date': date_str,
            'time': time_str,
            'id': article_id,
            'title': title,
            'folder': str(article_folder),
            'url': metadata.get('原文链接', ''),
            'account': metadata.get('公众号', ''),
            'category': metadata.get('分类', ''),
            'author': metadata.get('作者', ''),
            'publish_time': publish_time_str,
            'collect_time': metadata.get('采集时间', ''),
            'summary': summary,
            'read_num': read_num,
            'like_num': like_num,
            'looking_num': looking_num,
            'comment_num': comment_num,
            'share_num': share_num,
            'collect_num': collect_num,
            'engagement_rate': engagement_rate,
            'virality_index': virality_index,
            'content_value': content_value,
            'hotness_score': hotness_score,
            'has_stats': bool(stats),
            'stats_history': stats_list  # 保存完整的历史记录列表
        })

    # 按发布时间倒序排列（最新的在前面）
    def sort_key(article):
        # 优先使用发布时间排序
        pub_time = article.get('publish_time', '')
        if pub_time:
            return pub_time
        # 如果没有发布时间，使用采集时间
        return article['date'] + article['time']

    articles.sort(key=sort_key, reverse=True)

    return articles


def generate_html_report(articles, output_file, title="公众号文章报表"):
    """
    生成HTML报表

    Args:
        articles: 文章列表
        output_file: 输出文件路径
        title: 报表标题
    """
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        /* 顶部标题区 */
        .header {{
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }}

        .header h1 {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}

        /* 数据卡片区 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }}

        .stat-label {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        /* 筛选器区域 */
        .filters {{
            background: white;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }}

        .filters input,
        .filters select {{
            padding: 12px 18px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 14px;
            transition: all 0.3s ease;
            background: white;
            color: #1e293b;
        }}

        .filters input:focus,
        .filters select:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }}

        .filters input {{
            flex: 1;
            min-width: 280px;
        }}

        .filters select {{
            min-width: 160px;
        }}

        /* 表格容器 */
        .table-wrapper {{
            background: white;
            border-radius: 16px;
            overflow-x: auto;
            overflow-y: visible;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead {{
            background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th {{
            padding: 18px 16px;
            text-align: left;
            font-weight: 600;
            color: white;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
        }}

        th:hover {{
            background: rgba(255,255,255,0.15);
        }}

        th::after {{
            content: ' ⇅';
            opacity: 0.6;
            font-size: 11px;
            margin-left: 4px;
        }}

        td {{
            padding: 16px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
            font-size: 14px;
        }}

        tbody tr {{
            transition: all 0.2s ease;
        }}

        tbody tr:nth-child(even) {{
            background: #f8fafc;
        }}

        tbody tr:hover {{
            background: #eff6ff !important;
            transform: scale(1.002);
        }}

        /* 多条历史记录样式 */
        tr.article-group {{
            border-top: 3px solid #3b82f6 !important;
        }}

        tr.history-row {{
            background: #eff6ff !important;
            border-left: 3px solid #3b82f6;
        }}

        tr.history-row td {{
            background: #f0f9ff;
            font-size: 13px;
        }}

        tr.history-row:hover {{
            background: #dbeafe !important;
        }}

        tr.history-row small {{
            font-size: 11px;
            opacity: 0.8;
        }}

        /* 文章标题样式 */
        .article-title {{
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
            display: block;
            margin-bottom: 6px;
            transition: all 0.3s ease;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 400px;
            font-size: 15px;
        }}

        .article-title:hover {{
            color: #7c3aed;
            text-decoration: underline;
        }}

        /* 分类标签 */
        .category {{
            display: inline-block;
            padding: 6px 14px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.3px;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }}

        /* 公众号名称 */
        .account {{
            color: #475569;
            font-size: 13px;
            font-weight: 600;
        }}

        /* 摘要文字 */
        .summary {{
            color: #94a3b8;
            font-size: 12px;
            line-height: 1.6;
            max-width: 400px;
            margin-top: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        /* 数字样式 */
        .number {{
            color: #2563eb;
            font-weight: 700;
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
        }}

        .number.high {{
            color: #10b981;
            font-weight: 700;
        }}

        /* 时间样式 */
        .time {{
            color: #94a3b8;
            font-size: 12px;
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
        }}

        /* 空结果提示 */
        .no-results {{
            text-align: center;
            padding: 80px 20px;
            color: #94a3b8;
            font-size: 18px;
            background: white;
            border-radius: 16px;
            margin-top: 20px;
        }}

        /* 响应式设计 */
        @media (max-width: 768px) {{
            body {{
                padding: 20px 10px;
            }}

            .header h1 {{
                font-size: 28px;
            }}

            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            .filters {{
                flex-direction: column;
            }}

            .filters input,
            .filters select {{
                width: 100%;
            }}

            th, td {{
                padding: 12px 8px;
                font-size: 12px;
            }}
        }}

        /* 滚动条美化 */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f5f9;
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(135deg, #5568d3 0%, #63398d 100%);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 标题区 -->
        <div class="header">
            <h1>📊 公众号文章数据分析</h1>
            <p>数据驱动内容，洞察价值趋势</p>
        </div>

        <!-- 数据卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">📚 总文章数</div>
                <div class="stat-value">{total_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">📁 分类数</div>
                <div class="stat-value">{category_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">👥 公众号数</div>
                <div class="stat-value">{account_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">🕐 更新时间</div>
                <div class="stat-value" style="font-size: 16px; margin-top: 8px;">{generate_time}</div>
            </div>
        </div>

        <!-- 筛选器 -->
        <div class="filters">
            <input type="text" id="searchInput" placeholder="🔍 搜索标题、公众号..." onkeyup="filterTable()">
            <select id="categoryFilter" onchange="filterTable()">
                <option value="">📁 所有分类</option>
                {category_options}
            </select>
            <select id="accountFilter" onchange="filterTable()">
                <option value="">👤 所有公众号</option>
                {account_options}
            </select>
        </div>

        <!-- 表格 -->
        <div class="table-wrapper">
            <table id="articleTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)" style="width: 50px;">#</th>
                    <th onclick="sortTable(1)" style="min-width: 350px; max-width: 450px;">标题</th>
                    <th onclick="sortTable(2)" style="width: 120px;">公众号</th>
                    <th onclick="sortTable(3)" style="width: 80px;">分类</th>
                    <th onclick="sortTable(4)" style="width: 140px;">发布时间</th>
                    <th onclick="sortTable(5)" style="width: 100px;">采集日期</th>
                    <th onclick="sortTable(6)" style="width: 80px;">阅读</th>
                    <th onclick="sortTable(7)" style="width: 60px;">点赞</th>
                    <th onclick="sortTable(8)" style="width: 60px;">在看</th>
                    <th onclick="sortTable(9)" style="width: 60px;">评论</th>
                    <th onclick="sortTable(10)" style="width: 60px;">分享</th>
                    <th onclick="sortTable(11)" style="width: 60px;">收藏</th>
                    <th onclick="sortTable(12)" style="width: 80px;" title="(点赞+在看)/阅读×1000">互动率‰</th>
                    <th onclick="sortTable(13)" style="width: 80px;" title="(转发×2+在看)/阅读×1000">传播‰</th>
                    <th onclick="sortTable(14)" style="width: 90px;" title="(收藏×2+评论)/阅读×1000">价值‰</th>
                    <th onclick="sortTable(15)" style="width: 70px;" title="(点赞×1+在看×2+评论×3+收藏×4+转发×5)/阅读×100">热度分</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        </div>

        <div id="noResults" class="no-results" style="display: none;">
            😔 没有找到匹配的文章
        </div>
    </div>

    <script>
        // 排序状态
        let currentSortColumn = -1;
        let sortDirection = 'asc'; // 'asc' 或 'desc'

        function filterTable() {{
            const searchValue = document.getElementById('searchInput').value.toLowerCase();
            const categoryValue = document.getElementById('categoryFilter').value;
            const accountValue = document.getElementById('accountFilter').value;

            const table = document.getElementById('articleTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = tbody.getElementsByTagName('tr');

            let visibleCount = 0;

            for (let row of rows) {{
                const title = row.cells[1].textContent.toLowerCase();
                const account = row.cells[2].textContent;
                const category = row.cells[3].textContent;

                let show = true;

                if (searchValue && !title.includes(searchValue) && !account.toLowerCase().includes(searchValue)) {{
                    show = false;
                }}

                if (categoryValue && category !== categoryValue) {{
                    show = false;
                }}

                if (accountValue && account !== accountValue) {{
                    show = false;
                }}

                row.style.display = show ? '' : 'none';
                if (show) visibleCount++;
            }}

            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
        }}

        function sortTable(columnIndex) {{
            // 切换排序方向
            if (currentSortColumn === columnIndex) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                currentSortColumn = columnIndex;
                sortDirection = 'asc';
            }}
            const table = document.getElementById('articleTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const allRows = Array.from(tbody.getElementsByTagName('tr'));

            // 将行分组（article-group + 其后的 history-row）
            const groups = [];
            let currentGroup = [];

            allRows.forEach(row => {{
                if (row.classList.contains('article-group')) {{
                    // 如果遇到新的文章组，先保存之前的组
                    if (currentGroup.length > 0) {{
                        groups.push(currentGroup);
                    }}
                    // 开始新的组
                    currentGroup = [row];
                }} else if (row.classList.contains('history-row')) {{
                    // 历史记录行添加到当前组
                    currentGroup.push(row);
                }} else {{
                    // 普通行（没有历史记录）
                    if (currentGroup.length > 0) {{
                        groups.push(currentGroup);
                    }}
                    currentGroup = [row];
                }}
            }});

            // 最后一组
            if (currentGroup.length > 0) {{
                groups.push(currentGroup);
            }}

            // 对组进行排序（根据每组第一行的指定列）
            groups.sort((a, b) => {{
                const aValue = a[0].cells[columnIndex]?.textContent || '';
                const bValue = b[0].cells[columnIndex]?.textContent || '';

                let result = 0;

                // 尝试数字排序
                const aNum = parseFloat(aValue.replace(/,/g, ''));
                const bNum = parseFloat(bValue.replace(/,/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    result = aNum - bNum;
                }} else {{
                    // 否则字符串排序
                    result = aValue.localeCompare(bValue);
                }}

                // 应用排序方向
                return sortDirection === 'asc' ? result : -result;
            }});

            // 更新表头显示排序方向
            const headers = table.querySelectorAll('th');
            headers.forEach((th, index) => {{
                // 移除所有箭头
                th.innerHTML = th.innerHTML.replace(/ ⇅$/, '').replace(/ ↑$/, '').replace(/ ↓$/, '');
                if (index === columnIndex) {{
                    th.innerHTML += sortDirection === 'asc' ? ' ↑' : ' ↓';
                }} else {{
                    th.innerHTML += ' ⇅';
                }}
            }});

            // 清空表格并重新插入排序后的行
            tbody.innerHTML = '';
            groups.forEach(group => {{
                group.forEach(row => tbody.appendChild(row));
            }});
        }}
    </script>
</body>
</html>
"""

    # 生成表格行
    table_rows = []
    article_index = 1  # 用于文章序号

    for article in articles:
        stats_history = article.get('stats_history', [])

        # 如果有多个历史记录,显示多行
        if len(stats_history) > 1:
            # 第一行显示文章信息
            first_stats = stats_history[0]

            # 计算第一条数据的指标
            read_num = first_stats.get('read_num', 0)
            like_num = first_stats.get('like_num', 0)
            looking_num = first_stats.get('looking_num', 0)
            comment_num = first_stats.get('in_comment_num', 0)
            share_num = first_stats.get('share_num', 0)
            collect_num = first_stats.get('collect_num', 0)
            fetched_time = first_stats.get('fetched_time', '-')

            # 计算指标
            if read_num > 0:
                engagement_rate = ((like_num + looking_num) / read_num) * 1000
                virality_index = ((share_num * 2 + looking_num) / read_num) * 1000
                content_value = ((collect_num * 2 + comment_num) / read_num) * 1000
                hotness_score = ((like_num * 1 + looking_num * 2 + comment_num * 3 + collect_num * 4 + share_num * 5) / read_num) * 100
            else:
                engagement_rate = virality_index = content_value = hotness_score = 0

            # 格式化发布时间显示
            publish_time_display = article.get('publish_time', '-')
            if publish_time_display and len(publish_time_display) > 10:
                publish_time_display = publish_time_display[:16]

            # 第一行 - 带文章信息
            row = f"""
                <tr class="article-group">
                    <td rowspan="{len(stats_history)}">{article_index}</td>
                    <td rowspan="{len(stats_history)}">
                        <a href="{article['url']}" target="_blank" class="article-title">{article['title']}</a>
                        <div class="summary">{article['summary']}...</div>
                    </td>
                    <td rowspan="{len(stats_history)}" class="account">{article['account']}</td>
                    <td rowspan="{len(stats_history)}"><span class="category">{article['category']}</span></td>
                    <td rowspan="{len(stats_history)}" class="time">{publish_time_display}</td>
                    <td class="time">{fetched_time[:10]}</td>
                    <td class="number">{read_num:,}</td>
                    <td class="number">{like_num:,}</td>
                    <td class="number">{looking_num:,}</td>
                    <td class="number">{comment_num:,}</td>
                    <td class="number">{share_num:,}</td>
                    <td class="number">{collect_num:,}</td>
                    <td class="number">{engagement_rate:.1f}</td>
                    <td class="number">{virality_index:.1f}</td>
                    <td class="number">{content_value:.1f}</td>
                    <td class="number">{hotness_score:.1f}</td>
                </tr>"""
            table_rows.append(row)

            # 后续行 - 只显示数据,带增长指标
            for j in range(1, len(stats_history)):
                curr_stats = stats_history[j]
                prev_stats = stats_history[j-1]

                # 当前数据
                read_num = curr_stats.get('read_num', 0)
                like_num = curr_stats.get('like_num', 0)
                looking_num = curr_stats.get('looking_num', 0)
                comment_num = curr_stats.get('in_comment_num', 0)
                share_num = curr_stats.get('share_num', 0)
                collect_num = curr_stats.get('collect_num', 0)
                fetched_time = curr_stats.get('fetched_time', '-')

                # 计算增长
                prev_read = prev_stats.get('read_num', 0)
                prev_like = prev_stats.get('like_num', 0)
                prev_looking = prev_stats.get('looking_num', 0)
                prev_comment = prev_stats.get('in_comment_num', 0)
                prev_share = prev_stats.get('share_num', 0)
                prev_collect = prev_stats.get('collect_num', 0)

                def calc_growth(curr, prev):
                    if prev == 0:
                        return "" if curr == 0 else f"<span style='color:#52c41a;'>+{curr}</span>"
                    diff = curr - prev
                    if diff > 0:
                        pct = (diff / prev) * 100
                        return f"<span style='color:#52c41a;'>↑+{diff} ({pct:.0f}%)</span>"
                    elif diff < 0:
                        return f"<span style='color:#ff4d4f;'>↓{diff}</span>"
                    return ""

                read_growth = calc_growth(read_num, prev_read)
                like_growth = calc_growth(like_num, prev_like)
                looking_growth = calc_growth(looking_num, prev_looking)
                comment_growth = calc_growth(comment_num, prev_comment)
                share_growth = calc_growth(share_num, prev_share)
                collect_growth = calc_growth(collect_num, prev_collect)

                # 计算指标
                if read_num > 0:
                    engagement_rate = ((like_num + looking_num) / read_num) * 1000
                    virality_index = ((share_num * 2 + looking_num) / read_num) * 1000
                    content_value = ((collect_num * 2 + comment_num) / read_num) * 1000
                    hotness_score = ((like_num * 1 + looking_num * 2 + comment_num * 3 + collect_num * 4 + share_num * 5) / read_num) * 100
                else:
                    engagement_rate = virality_index = content_value = hotness_score = 0

                row = f"""
                <tr class="history-row">
                    <td class="time">{fetched_time[:10]}</td>
                    <td class="number">{read_num:,}<br><small>{read_growth}</small></td>
                    <td class="number">{like_num:,}<br><small>{like_growth}</small></td>
                    <td class="number">{looking_num:,}<br><small>{looking_growth}</small></td>
                    <td class="number">{comment_num:,}<br><small>{comment_growth}</small></td>
                    <td class="number">{share_num:,}<br><small>{share_growth}</small></td>
                    <td class="number">{collect_num:,}<br><small>{collect_growth}</small></td>
                    <td class="number">{engagement_rate:.1f}</td>
                    <td class="number">{virality_index:.1f}</td>
                    <td class="number">{content_value:.1f}</td>
                    <td class="number">{hotness_score:.1f}</td>
                </tr>"""
                table_rows.append(row)

        else:
            # 只有一条数据,正常显示
            has_stats = article.get('has_stats', False)

            if has_stats:
                read_display = f"{article.get('read_num', 0):,}"
                like_display = f"{article.get('like_num', 0):,}"
                looking_display = f"{article.get('looking_num', 0):,}"
                comment_display = f"{article.get('comment_num', 0):,}"
                share_display = f"{article.get('share_num', 0):,}"
                collect_display = f"{article.get('collect_num', 0):,}"

                engagement_display = f"{article.get('engagement_rate', 0):.1f}"
                virality_display = f"{article.get('virality_index', 0):.1f}"
                content_value_display = f"{article.get('content_value', 0):.1f}"
                hotness_display = f"{article.get('hotness_score', 0):.1f}"

                # 获取采集时间
                fetched_date = "-"
                if stats_history:
                    fetched_time = stats_history[0].get('fetched_time', '-')
                    fetched_date = fetched_time[:10] if fetched_time != '-' else '-'
            else:
                read_display = "-"
                like_display = "-"
                looking_display = "-"
                comment_display = "-"
                share_display = "-"
                collect_display = "-"
                engagement_display = "-"
                virality_display = "-"
                content_value_display = "-"
                hotness_display = "-"
                fetched_date = "-"

            # 格式化发布时间显示
            publish_time_display = article.get('publish_time', '-')
            if publish_time_display and len(publish_time_display) > 10:
                publish_time_display = publish_time_display[:16]

            # 判断数值是否较高
            engagement_class = "number high" if article.get('engagement_rate', 0) > 50 else "number"
            virality_class = "number high" if article.get('virality_index', 0) > 300 else "number"
            content_value_class = "number high" if article.get('content_value', 0) > 80 else "number"
            hotness_class = "number high" if article.get('hotness_score', 0) > 100 else "number"

            row = f"""
                <tr>
                    <td>{article_index}</td>
                    <td>
                        <a href="{article['url']}" target="_blank" class="article-title">{article['title']}</a>
                        <div class="summary">{article['summary']}...</div>
                    </td>
                    <td class="account">{article['account']}</td>
                    <td><span class="category">{article['category']}</span></td>
                    <td class="time">{publish_time_display}</td>
                    <td class="time">{fetched_date}</td>
                    <td class="number">{read_display}</td>
                    <td class="number">{like_display}</td>
                    <td class="number">{looking_display}</td>
                    <td class="number">{comment_display}</td>
                    <td class="number">{share_display}</td>
                    <td class="number">{collect_display}</td>
                    <td class="{engagement_class}">{engagement_display}</td>
                    <td class="{virality_class}">{virality_display}</td>
                    <td class="{content_value_class}">{content_value_display}</td>
                    <td class="{hotness_class}">{hotness_display}</td>
                </tr>"""
            table_rows.append(row)

        article_index += 1

    # 统计信息
    categories = set(a['category'] for a in articles if a['category'])
    accounts = set(a['account'] for a in articles if a['account'])

    category_options = '\n'.join([f'<option value="{cat}">{cat}</option>' for cat in sorted(categories)])
    account_options = '\n'.join([f'<option value="{acc}">{acc}</option>' for acc in sorted(accounts)])

    # 生成HTML
    html = html_template.format(
        title=title,
        total_count=len(articles),
        category_count=len(categories),
        account_count=len(accounts),
        generate_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        category_options=category_options,
        account_options=account_options,
        table_rows='\n'.join(table_rows)
    )

    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 报表已生成: {output_file}")
    print(f"   共 {len(articles)} 篇文章")


def main():
    """主函数"""
    articles_dir = PROJECT_ROOT / "data" / "articles"

    if not articles_dir.exists():
        print("❌ 文章目录不存在")
        return

    # 扫描所有文章
    print("📊 正在扫描文章...")
    all_articles = scan_articles(articles_dir)

    # 生成总报表
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    output_file = reports_dir / "all_articles.html"
    generate_html_report(all_articles, output_file, title="公众号文章报表 - 全部文章")

    print(f"\n📁 报表保存位置: {reports_dir}")
    print(f"   总报表: all_articles.html ({len(all_articles)} 篇)")


if __name__ == "__main__":
    main()
