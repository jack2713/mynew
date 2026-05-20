#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox直播接口解密工具
用于获取和解析直播接口内容
使用方法: python tv_api_decrypt.py
功能:
1. 自动使用正确的User-Agent请求接口
2. 解析返回的JSON配置数据
3. 提取直播源、解析接口、站点信息等
4. 下载直播源内容并保存到my3.txt
5. 支持关键词过滤，排除特定#genre#分组
"""

import requests
import json
import re
from datetime import datetime
from urllib.parse import unquote

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== 全局配置 ====================

# 目标接口地址列表（可配置多个）
# 程序会依次获取每个接口的直播源内容并合并
API_URLS = [
    "https://ds65.tv1288.xyz",
    # 可以添加更多接口地址...
    # "http://tv.nxog.top/api.php?mz=xb&id=2&b=欧歌",
    # "http://other-api.com/config.json",
]

# 排除关键词列表（不区分大小写）
# 含有这些关键词的 #genre# 分组将被完全过滤
EXCLUDE_KEYWORDS = [
    "音乐", "金曲", "DJ", "黄色", "激情", "私拍",
    # 可以继续添加更多关键词...
]

# 输出文件名
OUTPUT_FILE = "my3.txt"


class TVBoxAPI:
    """TVBox API 解密器"""

    def __init__(self):
        # TVBox常用的User-Agent列表
        self.user_agents = [
            'okhttp/3.12.1',
            'Dalvik/2.1.0 (Linux; U; Android 10; MI 9 Build/QKQ1.190825.002)',
            'TVBox',
        ]
        self.session = requests.Session()
        self.session.verify = False
        self.data = None

    def fetch_api(self, url, params=None):
        """
        获取API数据
        使用特定的User-Agent来获取JSON格式的响应
        """
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': '*/*',
            'Accept-Encoding': 'gzip',
        }
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None

    def fetch_live_content(self, url):
        """
        获取直播源内容
        """
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': '*/*',
        }
        try:
            response = self.session.get(url, headers=headers, timeout=60)
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
                try:
                    response.encoding = encoding
                    content = response.text
                    # 检查是否解码成功（没有乱码）
                    if '频道' in content or '#genre#' in content or '#EXTM3U' in content:
                        return content
                except:
                    continue
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"获取直播源内容失败: {e}")
            return None

    def parse_json(self, text):
        """
        解析JSON数据
        处理可能包含注释的JSON
        """
        # 移除开头的空白和控制字符
        text = text.strip()

        # 移除JavaScript风格的注释
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if '//' in line and not line.strip().startswith('"'):
                in_string = False
                result = []
                for i, char in enumerate(line):
                    if char == '"' and (i == 0 or line[i-1] != '\\'):
                        in_string = not in_string
                    if char == '/' and i < len(line) - 1 and line[i+1] == '/' and not in_string:
                        break
                    result.append(char)
                cleaned_lines.append(''.join(result).rstrip())
            else:
                cleaned_lines.append(line.rstrip())

        text = '\n'.join(cleaned_lines)

        try:
            self.data = json.loads(text)
            return True
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return False

    def get_live_sources(self):
        """获取直播源地址列表"""
        if not self.data:
            return []
        lives = self.data.get('lives', [])
        sources = []
        for live in lives:
            sources.append({
                '名称': live.get('name', '未知'),
                '地址': live.get('url', ''),
            })
        return sources


def filter_live_content(content, exclude_keywords):
    """
    过滤直播源内容
    1. 根据排除关键词过滤掉含有这些关键词的#genre#分组
    2. 去掉所有#genre#行，在开头添加固定的"gt,#genre#"
    """
    if not content:
        return ""

    lines = content.split('\n')
    filtered_lines = []
    skip_mode = False

    for line in lines:
        line_stripped = line.strip()

        # 检查是否是 #genre# 行
        if '#genre#' in line_stripped:
            # 检查是否包含排除关键词
            should_skip = False
            for keyword in exclude_keywords:
                if keyword.lower() in line_stripped.lower():
                    should_skip = True
                    break
            skip_mode = should_skip
        else:
            # 非分组行，根据skip_mode决定是否保留
            if not skip_mode:
                # 只保留非空行和包含逗号的频道行
                if line_stripped and ',' in line_stripped:
                    filtered_lines.append(line)

    # 在开头添加固定的 #genre# 行
    result = ["gt,#genre#"]
    result.extend(filtered_lines)
    return '\n'.join(result)


def parse_m3u_to_txt(content):
    """
    将M3U格式转换为TXT格式
    TXT格式: 频道名,URL
    """
    if not content:
        return ""

    lines = content.split('\n')
    result = []
    current_channel = None

    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            match = re.search(r',(.+)$', line)
            if match:
                current_channel = match.group(1).strip()
            # 提取分组信息
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                group = group_match.group(1)
                result.append(f"{group},#genre#")
        elif line and not line.startswith('#'):
            if current_channel:
                result.append(f"{current_channel},{line}")
                current_channel = None

    return '\n'.join(result)


def main():
    """主函数"""
    print("TVBox直播接口解密工具")

    all_live_content = []

    # 遍历所有接口地址
    for api_index, api_url in enumerate(API_URLS, 1):
        print(f"\n正在处理接口 {api_index}: {api_url}")

        # 创建API实例
        api = TVBoxAPI()

        # 获取数据
        text = api.fetch_api(api_url)
        if not text:
            print("  获取数据失败，跳过此接口")
            continue

        # 解析JSON
        if not api.parse_json(text):
            print("  JSON解析失败，跳过此接口")
            continue

        # 获取直播源内容
        live_sources = api.get_live_sources()
        for source in live_sources:
            name = source.get('名称', '未知')
            url = source.get('地址', '')
            if not url:
                continue

            print(f"  正在获取直播源: {name}")
            content = api.fetch_live_content(url)
            if content:
                # 如果是M3U格式，转换为TXT格式
                if content.strip().startswith('#EXTM3U'):
                    content = parse_m3u_to_txt(content)
                all_live_content.append(content)

    # 合并所有直播源内容
    combined_content = '\n\n'.join(all_live_content)

    # 过滤内容
    filtered_content = filter_live_content(combined_content, EXCLUDE_KEYWORDS)

    # 直接保存到文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(filtered_content)

    print(f"\n处理完成！已保存到 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
