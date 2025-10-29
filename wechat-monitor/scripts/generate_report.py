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
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '#667eea',
                        secondary: '#764ba2',
                    }}
                }}
            }}
        }}
    </script>
    <style>
        tr.article-group {{
            border-top: 2px solid #3b82f6 !important;
        }}

        tr.history-row {{
            border-left: 2px solid #3b82f6;
        }}

        thead {{
            position: sticky;
            top: 0;
            z-index: 10;
        }}
    </style>
</head>
<body class="min-h-screen bg-slate-50 p-6 md:p-10">
    <div class="max-w-[1600px] mx-auto">
        <!-- 筛选器 -->
        <div class="bg-white rounded-lg p-6 border border-slate-200 mb-6 flex flex-wrap gap-4">
            <input type="text" id="searchInput" placeholder="🔍 搜索标题、公众号..." onkeyup="filterTable()"
                class="flex-1 min-w-[280px] px-4 py-2.5 border border-slate-300 rounded-md text-sm transition-colors focus:outline-none focus:border-blue-500">
            <select id="categoryFilter" onchange="filterTable()"
                class="min-w-[160px] px-4 py-2.5 border border-slate-300 rounded-md text-sm bg-white transition-colors focus:outline-none focus:border-blue-500">
                <option value="">📁 所有分类</option>
                {category_options}
            </select>
            <select id="accountFilter" onchange="filterTable()"
                class="min-w-[160px] px-4 py-2.5 border border-slate-300 rounded-md text-sm bg-white transition-colors focus:outline-none focus:border-blue-500">
                <option value="">👤 所有公众号</option>
                {account_options}
            </select>
        </div>

        <!-- 表格 -->
        <div class="bg-white rounded-lg border border-slate-200 overflow-x-auto">
            <table id="articleTable" class="w-full border-collapse">
            <thead class="bg-blue-600">
                <tr>
                    <th onclick="sortTable(0)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-12">#</th>
                    <th onclick="sortTable(1)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 min-w-[350px] max-w-[450px]">标题</th>
                    <th onclick="sortTable(2)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-28">公众号</th>
                    <th onclick="sortTable(3)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-20">分类</th>
                    <th onclick="sortTable(4)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-36">发布时间</th>
                    <th onclick="sortTable(5)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-24">采集日期</th>
                    <th onclick="sortTable(6)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-20">阅读</th>
                    <th onclick="sortTable(7)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-16">点赞</th>
                    <th onclick="sortTable(8)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-16">在看</th>
                    <th onclick="sortTable(9)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-16">评论</th>
                    <th onclick="sortTable(10)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-16">分享</th>
                    <th onclick="sortTable(11)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-16">收藏</th>
                    <th onclick="sortTable(12)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-20" title="(点赞+在看)/阅读×1000">互动率‰</th>
                    <th onclick="sortTable(13)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-20" title="(转发×2+在看)/阅读×1000">传播‰</th>
                    <th onclick="sortTable(14)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-24" title="(收藏×2+评论)/阅读×1000">价值‰</th>
                    <th onclick="sortTable(15)" class="px-4 py-4 text-left text-xs font-semibold text-white cursor-pointer select-none whitespace-nowrap uppercase tracking-wide transition-colors hover:bg-blue-700 w-20" title="(点赞×1+在看×2+评论×3+收藏×4+转发×5)/阅读×100">热度分</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        </div>

        <div id="noResults" class="hidden text-center py-20 px-5 text-slate-400 text-lg bg-white rounded-2xl mt-5">
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

            const noResults = document.getElementById('noResults');
            if (visibleCount === 0) {{
                noResults.classList.remove('hidden');
            }} else {{
                noResults.classList.add('hidden');
            }}
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
                <tr class="article-group hover:bg-blue-50/50 transition-colors">
                    <td rowspan="{len(stats_history)}" class="px-4 py-3 border-b border-slate-200 text-slate-700 text-sm">{article_index}</td>
                    <td rowspan="{len(stats_history)}" class="px-4 py-3 border-b border-slate-200">
                        <a href="{article['url']}" target="_blank" class="block text-blue-600 font-semibold hover:text-blue-700 transition-colors mb-1.5 overflow-hidden text-ellipsis whitespace-nowrap max-w-[400px] text-sm">{article['title']}</a>
                        <div class="text-slate-400 text-xs leading-relaxed max-w-[400px] mt-1 overflow-hidden text-ellipsis whitespace-nowrap">{article['summary']}...</div>
                    </td>
                    <td rowspan="{len(stats_history)}" class="px-4 py-3 border-b border-slate-200 text-slate-700 text-sm font-medium">{article['account']}</td>
                    <td rowspan="{len(stats_history)}" class="px-4 py-3 border-b border-slate-200"><span class="inline-block px-3 py-1 bg-blue-600 text-white rounded text-xs font-medium">{article['category']}</span></td>
                    <td rowspan="{len(stats_history)}" class="px-4 py-3 border-b border-slate-200 text-slate-500 text-xs font-mono">{publish_time_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-slate-500 text-xs font-mono">{fetched_time[:10]}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{read_num:,}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{like_num:,}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{looking_num:,}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{comment_num:,}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{share_num:,}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{collect_num:,}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{engagement_rate:.1f}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{virality_index:.1f}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{content_value:.1f}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{hotness_score:.1f}</td>
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
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-slate-500 text-xs font-mono">{fetched_time[:10]}</td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{read_num:,}<br><small class="text-xs opacity-80">{read_growth}</small></td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{like_num:,}<br><small class="text-xs opacity-80">{like_growth}</small></td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{looking_num:,}<br><small class="text-xs opacity-80">{looking_growth}</small></td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{comment_num:,}<br><small class="text-xs opacity-80">{comment_growth}</small></td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{share_num:,}<br><small class="text-xs opacity-80">{share_growth}</small></td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{collect_num:,}<br><small class="text-xs opacity-80">{collect_growth}</small></td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{engagement_rate:.1f}</td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{virality_index:.1f}</td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{content_value:.1f}</td>
                    <td class="px-4 py-3 bg-blue-50/40 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{hotness_score:.1f}</td>
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

            # 判断数值是否较高，使用绿色高亮（数据高亮功能）
            engagement_class = "px-4 py-3 border-b border-slate-200 text-emerald-600 font-semibold font-mono text-sm" if article.get('engagement_rate', 0) > 50 else "px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm"
            virality_class = "px-4 py-3 border-b border-slate-200 text-emerald-600 font-semibold font-mono text-sm" if article.get('virality_index', 0) > 300 else "px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm"
            content_value_class = "px-4 py-3 border-b border-slate-200 text-emerald-600 font-semibold font-mono text-sm" if article.get('content_value', 0) > 80 else "px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm"
            hotness_class = "px-4 py-3 border-b border-slate-200 text-emerald-600 font-semibold font-mono text-sm" if article.get('hotness_score', 0) > 100 else "px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm"

            row = f"""
                <tr class="even:bg-slate-50 hover:bg-blue-50/50 transition-colors">
                    <td class="px-4 py-3 border-b border-slate-200 text-slate-700 text-sm">{article_index}</td>
                    <td class="px-4 py-3 border-b border-slate-200">
                        <a href="{article['url']}" target="_blank" class="block text-blue-600 font-semibold hover:text-blue-700 transition-colors mb-1.5 overflow-hidden text-ellipsis whitespace-nowrap max-w-[400px] text-sm">{article['title']}</a>
                        <div class="text-slate-400 text-xs leading-relaxed max-w-[400px] mt-1 overflow-hidden text-ellipsis whitespace-nowrap">{article['summary']}...</div>
                    </td>
                    <td class="px-4 py-3 border-b border-slate-200 text-slate-700 text-sm font-medium">{article['account']}</td>
                    <td class="px-4 py-3 border-b border-slate-200"><span class="inline-block px-3 py-1 bg-blue-600 text-white rounded text-xs font-medium">{article['category']}</span></td>
                    <td class="px-4 py-3 border-b border-slate-200 text-slate-500 text-xs font-mono">{publish_time_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-slate-500 text-xs font-mono">{fetched_date}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{read_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{like_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{looking_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{comment_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{share_display}</td>
                    <td class="px-4 py-3 border-b border-slate-200 text-blue-600 font-semibold font-mono text-sm">{collect_display}</td>
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
