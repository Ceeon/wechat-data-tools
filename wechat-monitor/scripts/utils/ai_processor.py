#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI处理模块
功能: Claude API调用,生成摘要和提取标签
"""

import os
from anthropic import Anthropic


class AIProcessor:
    """AI处理器"""

    def __init__(self, api_key, model="claude-3-5-sonnet-20241022"):
        """
        初始化AI处理器

        Args:
            api_key: Claude API Key
            model: 模型名称
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_summary(self, article_content, max_tokens=500):
        """
        生成文章摘要

        Args:
            article_content: 文章内容(Markdown格式)
            max_tokens: 最大token数

        Returns:
            str: 文章摘要
        """
        prompt = f"""请为以下文章生成一个简洁的摘要(100-200字):

{article_content}

要求:
1. 提炼文章核心观点和要点
2. 使用简洁易懂的语言
3. 保持客观中立的态度
4. 不超过200字

摘要:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = message.content[0].text.strip()
            return summary

        except Exception as e:
            print(f"❌ AI摘要生成失败: {e}")
            return "摘要生成失败"

    def extract_tags(self, article_content, max_tokens=300):
        """
        提取文章标签

        Args:
            article_content: 文章内容(Markdown格式)
            max_tokens: 最大token数

        Returns:
            list: 标签列表
        """
        prompt = f"""请为以下文章提取3-5个关键标签:

{article_content}

要求:
1. 标签要准确反映文章主题和领域
2. 使用简短的词语或短语
3. 优先选择技术、行业相关的标签
4. 返回格式: 标签1, 标签2, 标签3

标签:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            tags_text = message.content[0].text.strip()
            # 解析标签
            tags = [tag.strip() for tag in tags_text.split(',')]
            return tags

        except Exception as e:
            print(f"❌ AI标签提取失败: {e}")
            return []


if __name__ == "__main__":
    # 测试代码
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("请设置环境变量 CLAUDE_API_KEY")
        exit(1)

    processor = AIProcessor(api_key=api_key)

    test_content = """
    # Claude Code实战案例

    本文介绍了如何使用Claude Code进行自动化开发。
    Claude Code是一个强大的AI编程助手,可以帮助开发者提高效率。

    主要功能包括:
    - 代码生成
    - 代码审查
    - 文档编写

    通过实际案例展示了Claude Code在项目中的应用。
    """

    print("测试AI摘要生成:")
    summary = processor.generate_summary(test_content)
    print(f"摘要: {summary}\n")

    print("测试标签提取:")
    tags = processor.extract_tags(test_content)
    print(f"标签: {tags}")
