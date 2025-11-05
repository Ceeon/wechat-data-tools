# 归档脚本

这个目录包含了不常用的分析和数据处理脚本。这些脚本已从主目录移除，以保持项目结构简洁，但仍保留以供未来需要时使用。

## 脚本列表

### 分析类脚本

1. **analyze_topics.py** - 话题分析
   - 功能：分析文章中的热门话题和关键词
   - 用途：了解内容趋势

2. **analyze_coding_topics.py** - AI编程话题分析
   - 功能：专门分析 AI 编程相关话题
   - 用途：垂直领域内容分析

3. **analyze_engagement.py** - 互动数据分析
   - 功能：分析文章互动率、传播指数等指标
   - 用途：评估内容质量

4. **analyze_timeline.py** - 时间线分析
   - 功能：分析文章发布时间与互动的关系
   - 用途：优化发布策略

5. **recommend_best_topic.py** - 推荐最佳话题
   - 功能：基于历史数据推荐高互动话题
   - 用途：选题参考

### 旧版脚本

6. **fetch_article_stats.py** - 文章统计获取（旧版）
   - 功能：获取单篇文章的互动数据
   - 替代方案：使用 `fetch_recent_days_stats.py`

7. **smart_fetch_stats.py** - 智能统计获取
   - 功能：智能判断并获取统计数据
   - 替代方案：使用 `fetch_recent_days_stats.py`

## 如何使用

如果需要使用这些脚本，可以直接从归档目录运行：

```bash
cd scripts/archived
python3 analyze_topics.py
```

或者将需要的脚本移回主目录：

```bash
mv scripts/archived/analyze_topics.py scripts/
```

## 为什么归档？

这些脚本被归档的原因：
- **分析类脚本**：非日常使用，按需运行即可
- **旧版脚本**：已有更好的替代方案

核心的数据采集和报表生成流程不依赖这些脚本。
