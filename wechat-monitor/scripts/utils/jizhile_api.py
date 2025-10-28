#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极致了API工具模块
用于获取微信公众号文章的互动数据
"""

import requests
import time
from typing import Dict, Optional


class JizhileAPI:
    """极致了API客户端"""

    def __init__(self, api_key: str, verifycode: str = ""):
        """
        初始化API客户端

        Args:
            api_key: 极致了API密钥
            verifycode: 附加码（可选）
        """
        self.api_key = api_key
        self.verifycode = verifycode
        self.base_url = "https://www.dajiala.com/fbmain/monitor/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def get_article_stats(self, article_url: str) -> Optional[Dict]:
        """
        获取文章统计数据

        Args:
            article_url: 文章URL

        Returns:
            包含统计数据的字典，失败返回None
            {
                'read_num': 阅读数,
                'like_num': 点赞数,
                'in_comment_num': 评论数,
                'share_num': 分享数,
                'collect_num': 收藏数
            }
        """
        endpoint = f"{self.base_url}/read_zan_pro"

        payload = {
            'url': article_url,
            'key': self.api_key
        }

        # 如果有附加码，添加到请求中
        if self.verifycode:
            payload['verifycode'] = self.verifycode

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()

                # 检查返回码
                if result.get('code') == 0:
                    data = result.get('data', {})

                    # 转换字段名以匹配系统格式
                    return {
                        'read_num': data.get('read', 0),
                        'like_num': data.get('zan', 0),
                        'in_comment_num': data.get('comment_count', 0),
                        'share_num': data.get('share_num', 0),
                        'collect_num': data.get('collect_num', 0),
                        'looking_num': data.get('looking', 0),  # 在看数
                        'cost_money': result.get('cost_money', 0),
                        'remain_money': result.get('remain_money', 0)
                    }
                else:
                    print(f"⚠️  API返回错误: {result.get('msg', '未知错误')}")
                    return None
            else:
                print(f"⚠️  HTTP错误: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"⚠️  请求超时")
            return None
        except Exception as e:
            print(f"⚠️  请求失败: {e}")
            return None

    def batch_get_stats(self, article_urls: list, delay: float = 0.5) -> Dict[str, Dict]:
        """
        批量获取文章统计数据

        Args:
            article_urls: 文章URL列表
            delay: 请求间隔（秒），避免API限流

        Returns:
            字典，key为URL，value为统计数据
        """
        results = {}
        total = len(article_urls)

        print(f"\n📊 开始批量获取互动数据 (共{total}篇)")

        for i, url in enumerate(article_urls, 1):
            print(f"[{i}/{total}] 获取: {url[:50]}...")

            stats = self.get_article_stats(url)
            if stats:
                results[url] = stats
                print(f"  ✅ 阅读: {stats.get('read_num', 0)}, "
                      f"点赞: {stats.get('like_num', 0)}, "
                      f"评论: {stats.get('in_comment_num', 0)}")
            else:
                print(f"  ❌ 获取失败")

            # API限流
            if i < total:
                time.sleep(delay)

        print(f"\n✅ 批量获取完成: {len(results)}/{total}")
        return results


def test_api():
    """测试API功能"""
    # 测试用例
    api_key = "your_api_key_here"
    test_url = "https://mp.weixin.qq.com/s/XJy4sEuOF4MZ7rDqif1cXg"

    client = JizhileAPI(api_key)

    print("测试获取单篇文章数据...")
    stats = client.get_article_stats(test_url)

    if stats:
        print(f"✅ 测试成功!")
        print(f"   阅读数: {stats.get('read_num')}")
        print(f"   点赞数: {stats.get('like_num')}")
        print(f"   评论数: {stats.get('in_comment_num')}")
    else:
        print("❌ 测试失败")


if __name__ == "__main__":
    test_api()
