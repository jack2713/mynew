#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox M3U直播源获取工具（模拟TVBox UA）
优化版：增加重试机制、进度显示、更好的错误处理
"""
import requests
import re
import urllib3
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== 配置 ====================
API_URLS = [
    "https://ds65.tv1288.xyz",
]
EXCLUDE_KEYWORDS = ["音乐", "金曲", "DJ", "黄色", "激情", "私拍"]  # 分组名含这些关键词则跳过
OUTPUT_FILE = "my3.txt"
TVBOX_UA = "okhttp/3.15"  # TVBox的默认User-Agent
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔（秒）


def create_session():
    """创建带重试机制的session"""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 429],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_m3u(url):
    """使用TVBox UA获取M3U内容"""
    session = create_session()
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  尝试 {attempt + 1}/{MAX_RETRIES}...")
            resp = session.get(
                url,
                headers={
                    'User-Agent': TVBOX_UA,
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                timeout=20,
                verify=False
            )
            resp.encoding = "utf-8"
            text = resp.text.strip()
            
            if text.startswith("#EXTM3U") or "#EXTINF" in text[:500]:
                print(f"  ✓ 成功获取M3U (Status: {resp.status_code}, 大小: {len(text)} 字节)")
                return text
            elif text.startswith("{") and "data" in text:
                print(f"  ⚠ 返回的是JSON格式，尝试提取内容...")
                print(f"  前200字符: {text[:200]}")
                return text
            else:
                print(f"  ✗ 内容格式未知，前100字符: {text[:100]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return text
                
        except requests.RequestException as e:
            print(f"  ✗ 请求失败: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
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
