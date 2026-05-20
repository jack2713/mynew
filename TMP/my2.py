#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox M3U直播源获取工具
- 直接获取 M3U 格式内容
- 转换为 TXT（频道名,URL）
- 按分组过滤排除关键词
"""

import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== 配置 ====================
API_URLS = [
    "https://ds65.tv1288.xyz",
]

EXCLUDE_KEYWORDS = ["音乐", "金曲", "DJ", "黄色", "激情", "私拍"]  # 分组名含这些关键词则跳过
OUTPUT_FILE = "my3.txt"

USER_AGENTS = [
    "okhttp/3.12.1",
    "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def fetch_m3u(url):
    """尝试多个 UA 获取 M3U 内容"""
    for ua in USER_AGENTS:
        try:
            resp = requests.get(url, headers={"User-Agent": ua}, timeout=15, verify=False)
            resp.encoding = "utf-8"
            text = resp.text.strip()
            if text.startswith("#EXTM3U") or "#EXTINF" in text[:500]:
                print(f"✓ 成功获取 M3U (UA: {ua[:30]}...)")
                return text
        except:
            continue
    return None

def parse_m3u_to_txt(m3u_content):
    """
    将 M3U 转换为 TXT 格式
    输入: M3U 字符串
    输出: TXT 字符串，每行 "频道名,URL"
    """
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

        # 跳过注释行（但不跳过 #EXTINF）
        if line.startswith("#EXTM3U") or line.startswith("#EXT-X-") or line.startswith("//"):
            continue

        # 处理 #EXTINF 行
        if line.startswith("#EXTINF"):
            # 提取频道名
            match = re.search(r',([^,]+)$', line)
            if match:
                current_name = match.group(1).strip()
            # 提取分组名 (group-title)
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                current_group = group_match.group(1).strip()
            continue

        # 处理 URL 行（非注释行且不是空行）
        if line and not line.startswith("#") and current_name:
            # 如果分组有效，先添加分组标记（仅在分组变化时）
            if current_group:
                group_line = f"{current_group},#genre#"
                if not result or result[-1] != group_line:
                    result.append(group_line)
            # 添加频道行
            result.append(f"{current_name},{line}")
            current_name = None  # 重置，等待下一个 #EXTINF

    # 去重分组标记（保留第一次出现）
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
    """
    按分组过滤：如果分组名包含任意排除关键词，则删除整个分组及其所有频道
    """
    if not txt_content:
        return ""

    lines = txt_content.splitlines()
    filtered = []
    skip_group = False

    for line in lines:
        if line.endswith(",#genre#"):
            # 分组行
            group_name = line[:-7]  # 去掉结尾的 ",#genre#"
            if any(kw.lower() in group_name.lower() for kw in exclude_keywords):
                skip_group = True
            else:
                skip_group = False
                filtered.append(line)  # 保留分组行
        else:
            if not skip_group:
                filtered.append(line)

    return "\n".join(filtered)

def main():
    print("TVBox M3U → TXT 转换工具")
    all_txt_parts = []

    for url in API_URLS:
        print(f"\n正在处理: {url}")
        m3u = fetch_m3u(url)
        if not m3u:
            print("✗ 获取失败，跳过")
            continue

        print("  ↳ 转换为 TXT...")
        txt = parse_m3u_to_txt(m3u)
        if txt:
            all_txt_parts.append(txt)
            print(f"  ↳ 转换完成，共 {len(txt.splitlines())} 行")
        else:
            print("  ↳ 转换结果为空")

    if not all_txt_parts:
        print("\n未获取到任何有效内容，退出")
        return

    combined = "\n\n".join(all_txt_parts)
    filtered = filter_by_group(combined, EXCLUDE_KEYWORDS)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(filtered)

    print(f"\n✅ 完成！已保存到 {OUTPUT_FILE}")
    print(f"   原始行数: {len(combined.splitlines())}")
    print(f"   过滤后行数: {len(filtered.splitlines())}")

if __name__ == "__main__":
    main()
