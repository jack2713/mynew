#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON URL解析器 - 从配置的URL获取JSON，提取1080p质量的条目并保存为txt
"""

import json
import os
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import time


# ==================== URL配置 ====================
# 在这里添加或修改JSON数据源的URL
URLS = [
    "https://raw.githubusercontent.com/thihazawsatellite/iptv_validated_list/refs/heads/main/validated_streams.json",
    #"https://raw.githubusercontent.com/thihazawsatellite/iptv_validated_list/refs/heads/main/validated_streams12.json",
    # 在这里继续添加更多URL...
    # "https://example.com/another.json",
]
# ================================================

# 默认配置
DEFAULT_OUTPUT = "TMP/jsontxt.txt"
DEFAULT_QUALITY = "1080p"


def fetch_json_from_url(url, timeout=30):
    """
    从URL获取JSON数据
    
    Args:
        url: JSON数据的URL地址
        timeout: 请求超时时间（秒）
    
    Returns:
        解析后的JSON数据（列表）
    """
    print(f"  正在获取: {url[:70]}...")
    
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data if isinstance(data, list) else [data]
    except HTTPError as e:
        print(f"    HTTP错误 {e.code}: {e.reason}")
        return []
    except URLError as e:
        print(f"    URL错误: {e.reason}")
        return []
    except json.JSONDecodeError as e:
        print(f"    JSON解析错误: {e}")
        return []
    except Exception as e:
        print(f"    未知错误: {e}")
        return []


def parse_json_to_txt(urls, output_path, quality_filter='1080p'):
    """
    从多个URL获取JSON并解析为txt格式
    
    Args:
        urls: URL列表
        output_path: 输出txt文件路径
        quality_filter: 质量过滤条件（默认1080p）
    
    Returns:
        过滤后的条目数和总条目数
    """
    all_items = []
    
    # 确保输出目录存在
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 从每个URL获取数据
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] 获取JSON数据...")
        data = fetch_json_from_url(url)
        if data:
            all_items.extend(data)
            print(f"    成功获取 {len(data)} 条")
        time.sleep(0.3)  # 避免请求过快
    
    print(f"\n总共获取 {len(all_items)} 条数据，开始过滤 {quality_filter}...")
    
    # 过滤并写入txt文件
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_items:
            title = item.get('title', '')
            url = item.get('url', '')
            quality = item.get('quality', '')
            
            # 只保留指定质量的内容
            if quality == quality_filter and title and url:
                f.write(f"{title},{url}\n")
                count += 1
    
    return count, len(all_items)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从配置URL获取JSON并解析为txt（仅保留1080p）')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT, help=f'输出txt文件路径（默认: {DEFAULT_OUTPUT}）')
    parser.add_argument('-q', '--quality', default=DEFAULT_QUALITY, help=f'质量过滤条件（默认: {DEFAULT_QUALITY}）')
    
    args = parser.parse_args()
    
    urls = URLS
    
    if not urls:
        print("错误：URL列表为空，请在代码中的 URLS 列表添加数据源")
        return
    
    print(f"\n" + "="*60)
    print(f"JSON URL解析器")
    print(f"="*60)
    print(f"URL数量: {len(urls)}")
    print(f"输出文件: {args.output}")
    print(f"质量过滤: {args.quality}")
    print(f"="*60 + "\n")
    
    try:
        count, total = parse_json_to_txt(urls, args.output, args.quality)
        print(f"\n" + "="*60)
        print(f"解析完成！")
        print(f"  - 总获取数据: {total} 条")
        print(f"  - {args.quality} 条目数: {count} 条")
        print(f"  - 输出文件: {args.output}")
        print(f"="*60)
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
if __name__ == '__main__':
    main()
