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

def parse_m3u_to_txt(m3u_content):
    """将M3U转换为TXT格式"""
    if not m3u_content:
        return ""
    
    lines = m3u_content.splitlines()
    result = []
    current_group = None
    current_name = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过全局注释
        if line.startswith("#EXTM3U") or line.startswith("#EXT-X-") or line.startswith("//"):
            continue
        
        # 处理 #EXTINF 行
        if line.startswith("#EXTINF"):
            # 提取频道名
            match = re.search(r',([^,]+)$', line)
            if match:
                current_name = match.group(1).strip()
            # 提取分组名
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                current_group = group_match.group(1).strip()
            continue
        
        # 处理 URL 行
        if line and not line.startswith("#") and current_name:
            if current_group:
                group_line = f"{current_group},#genre#"
                if not result or result[-1] != group_line:
                    result.append(group_line)
            result.append(f"{current_name},{line}")
            current_name = None
    
    # 去重分组标记
    seen = set()
    unique_result = []
    for line in result:
        if line.endswith(",#genre#"):
            if line in seen:
                continue
            seen.add(line)
        unique_result.append(line)
    
    return "\n".join(unique_result)


def filter_by_group(txt_content, exclude_keywords):
    """按分组过滤"""
    if not txt_content:
        return ""
    
    lines = txt_content.splitlines()
    filtered = []
    skip_group = False
    skipped_groups = set()
    
    for line in lines:
        if line.endswith(",#genre#"):
            group_name = line[:-7]
            if any(kw.lower() in group_name.lower() for kw in exclude_keywords):
                skip_group = True
                skipped_groups.add(group_name)
            else:
                skip_group = False
                filtered.append(line)
        else:
            if not skip_group:
                filtered.append(line)
    
    if skipped_groups:
        print(f"  已过滤 {len(skipped_groups)} 个分组: {list(skipped_groups)[:3]}...")
    
    return "\n".join(filtered)


def main():
    print("=" * 50)
    print("TVBox M3U → TXT 转换工具 (模拟TVBox UA)")
    print("=" * 50)
    
    all_txt_parts = []
    
    for url in API_URLS:
        print(f"\n正在处理: {url}")
        m3u = fetch_m3u(url)
        
        if not m3u:
            print("  ✗ 获取失败，跳过")
            continue
        
        print("  ↳ 转换为 TXT 格式...")
        txt = parse_m3u_to_txt(m3u)
        
        if txt:
            all_txt_parts.append(txt)
            print(f"  ↳ 转换完成，共 {len(txt.splitlines())} 行")
        else:
            print("  ↳ 转换结果为空，尝试直接保存原始内容...")
            all_txt_parts.append(m3u)
    
    if not all_txt_parts:
        print("\n❌ 未获取到任何有效内容，退出")
        return
    
    combined = "\n\n".join(all_txt_parts)
    filtered = filter_by_group(combined, EXCLUDE_KEYWORDS)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(filtered)
    
    print("\n" + "=" * 50)
    print(f"✅ 完成！已保存到 {OUTPUT_FILE}")
    print(f"  原始行数: {len(combined.splitlines())}")
    print(f"  过滤后行数: {len(filtered.splitlines())}")
    print(f"  文件大小: {len(filtered.encode('utf-8'))} 字节")
    print("=" * 50)
    
    # 显示前几行预览
    print("\n📄 内容预览（前10行）：")
    preview_lines = filtered.splitlines()[:10]
    for i, line in enumerate(preview_lines, 1):
        print(f"  {i:2d}. {line[:80]}")


if __name__ == "__main__":
    main()
