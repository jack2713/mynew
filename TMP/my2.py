#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox M3U直播源获取工具（Cloudflare绕过版）
优化版：按分组名过滤整个分组，最后统一放在mengyxx分组下
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
    "http://wangziduoqing.com/yuan/zb.txt",
    "https://ds65.tv1288.xyz",
]
# 分组名含这些关键词则过滤整个分组
EXCLUDE_KEYWORDS = ["音乐", "金曲", "DJ", "黄色", "激情", "私拍", "体育", "代理", "广场舞","歌曲","女团","舞曲","电台","戏曲","乡村美食","更新","轮播","测试","移动","赛事","内网","限"]
OUTPUT_FILE = "my3.txt"
MAX_RETRIES = 3
FIXED_GROUP = "mengyxx,#genre#"  # 最终固定分组名称


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


def parse_m3u_with_groups(m3u_content):
    """解析M3U，保留分组信息用于后续过滤"""
    if not m3u_content:
        return [], {}
    
    lines = m3u_content.splitlines()
    channels_by_group = {}  # {分组名: [频道列表]}
    current_group = "其他"
    current_name = None
    all_groups = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("#EXTM3U") or line.startswith("#EXT-X-") or line.startswith("//"):
            continue
        
        if line.startswith("#EXTINF"):
            match = re.search(r',([^,]+)$', line)
            if match:
                current_name = match.group(1).strip()
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                current_group = group_match.group(1).strip()
                if current_group not in all_groups:
                    all_groups.append(current_group)
            continue
        
        if line and not line.startswith("#") and current_name:
            if current_group not in channels_by_group:
                channels_by_group[current_group] = []
            channels_by_group[current_group].append(f"{current_name},{line}")
            current_name = None
    
    return all_groups, channels_by_group


def filter_groups(channels_by_group, exclude_keywords):
    """按分组名过滤整个分组"""
    filtered = {}
    skipped_groups = []
    
    for group_name, channels in channels_by_group.items():
        # 检查分组名是否包含排除关键词
        if any(kw.lower() in group_name.lower() for kw in exclude_keywords):
            skipped_groups.append((group_name, len(channels)))
            continue
        filtered[group_name] = channels
    
    return filtered, skipped_groups


def main():
    print("=" * 50)
    print("TVBox M3U → TXT 转换工具 (按分组过滤版)")
    print("=" * 50)
    
    all_channels = []
    
    for url in API_URLS:
        print(f"\n正在处理: {url}")
        m3u = fetch_m3u(url)
        
        if not m3u:
            print("  ✗ 获取失败，跳过")
            continue
        
        print("  ↳ 解析分组信息...")
        all_groups, channels_by_group = parse_m3u_with_groups(m3u)
        print(f"  ↳ 发现 {len(all_groups)} 个分组，共 {sum(len(v) for v in channels_by_group.values())} 个频道")
        
        # 按分组名过滤
        print("  ↳ 按分组名过滤...")
        filtered_channels, skipped = filter_groups(channels_by_group, EXCLUDE_KEYWORDS)
        
        # 统计过滤的频道
        for group_name, count in skipped:
            print(f"    ✗ 跳过分组 [{group_name}] - {count} 个频道")
        
        # 收集所有保留的频道
        for group_name, channels in filtered_channels.items():
            all_channels.extend(channels)
        
        print(f"  ↳ 保留 {len(filtered_channels)} 个分组，{len(all_channels)} 个频道")
    
    if not all_channels:
        print("\n❌ 未获取到任何有效内容，退出")
        return
    
    # 去重
    unique_channels = list(dict.fromkeys(all_channels))
    dedup_count = len(all_channels) - len(unique_channels)
    
    if dedup_count > 0:
        print(f"\n  已去除 {dedup_count} 个重复频道")
    
    # 添加固定分组在第一行
    final_content = FIXED_GROUP + "\n" + "\n".join(unique_channels)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print("\n" + "=" * 50)
    print(f"✅ 完成！已保存到 {OUTPUT_FILE}")
    print(f"  最终频道数: {len(unique_channels)}")
    print(f"  文件大小: {len(final_content.encode('utf-8'))} 字节")
    print(f"  固定分组: {FIXED_GROUP}")
    print("=" * 50)
    
    # 显示前几行预览
    print("\n📄 内容预览（前10行）：")
    preview_lines = final_content.splitlines()[:10]
    for i, line in enumerate(preview_lines, 1):
        print(f"  {i:2d}. {line[:80]}")


if __name__ == "__main__":
    main()
