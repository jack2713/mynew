#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox M3U直播源获取工具（Cloudflare绕过版）
"""
import re
import time

try:
    import cloudscraper
except ImportError:
    print("安装 cloudscraper: pip install cloudscraper")
    exit(1)

# ==================== 配置 ====================
API_URLS = [
    "https://ds65.tv1288.xyz",
]
EXCLUDE_KEYWORDS = ["音乐", "金曲", "DJ", "黄色", "激情", "私拍"]
OUTPUT_FILE = "my3.txt"
MAX_RETRIES = 3

def create_scraper():
    """创建Cloudflare绕过的scraper"""
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        delay=10
    )

def fetch_m3u(url):
    scraper = create_scraper()
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  尝试 {attempt + 1}/{MAX_RETRIES}...")
            resp = scraper.get(url, timeout=30)
            text = resp.text.strip()
            
            if "Just a moment" in text or "cloudflare" in text.lower():
                print(f"  ⚠ 仍被Cloudflare拦截，尝试更换指纹...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
                    scraper = create_scraper()
                    continue
            
            if text.startswith("#EXTM3U") or "#EXTINF" in text[:500]:
                print(f"  ✓ 成功获取 (大小: {len(text)} 字节)")
                return text
            else:
                print(f"  前100字符: {text[:100]}")
                return text
                
        except Exception as e:
            print(f"  ✗ 请求失败: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
                continue
            return None
    
    return None

# ... 其余函数保持不变 ...
