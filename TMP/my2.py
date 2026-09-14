#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox 直播源获取工具（Cloudflare绕过 + 自动识别 M3U/TXT 格式）
修复说明：
  - 数据源 ds65.tv1288.xyz 实际返回 TXT 格式（“分组名,#genre#” + “频道名,URL”），
    原脚本只用 M3U 格式解析（#EXTINF / group-title），导致解析出 0 分组 0 频道。
  - 本次新增 TXT 格式解析，并自动检测格式，两种格式统一归一为
    {分组名: ["频道名,URL", ...]}，分组过滤、去重、输出逻辑保持不变。
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

EXCLUDE_KEYWORDS = ["音乐", "金曲", "DJ", "黄色", "激情", "私拍", "体育", "代理", "广场舞",
                    "歌曲", "女团", "舞曲", "电台", "戏曲", "乡村美食", "更新", 
                     "移动", "赛事", "内网", "限"]

OUTPUT_FILE = "my3.txt"
MAX_RETRIES = 3
FIXED_GROUP = "mengyxx,#genre#"


def create_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
        delay=10,
    )


def fetch_content(url):
    """抓取内容，返回文本；失败返回 None。格式判断交给后续处理。"""
    scraper = create_scraper()
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  尝试 {attempt + 1}/{MAX_RETRIES}...")
            resp = scraper.get(url, timeout=30)
            text = resp.text.strip()
            if "Just a moment" in text or "cloudflare" in text.lower():
                print("  ⚠ 仍被 Cloudflare 拦截，更换指纹重试...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
                    scraper = create_scraper()
                continue
            if text:
                print(f"  ✓ 成功获取 (大小: {len(text)} 字节)")
                return text
            print("  ✗ 返回空内容")
            return None
        except Exception as e:
            print(f"  ✗ 请求失败: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
    return None


def detect_format(text):
    """检测内容格式：'m3u' 或 'txt'。"""
    head = text[:3000]
    if "#EXTM3U" in head or "#EXTINF" in head:
        return "m3u"
    if "#genre#" in head:
        return "txt"
    # 都不明确时默认按 M3U 处理（向后兼容）
    return "m3u"


def _valid_url(u):
    u = u.strip()
    if not u:
        return False
    return "://" in u.lower()


def parse_txt(txt_content):
    """解析 TXT 格式：'分组名,#genre#' 作分组标题，后续行为 '频道名,URL'。"""
    all_groups = []
    channels_by_group = {}
    current_group = "其他"

    for line in txt_content.splitlines():
        line = line.strip()
        if not line:
            continue
        # 分组标题行：xxx,#genre#（兼容 ##genre# 等写法）
        if "#genre#" in line:
            current_group = line.split("#genre#")[0].strip().rstrip(",，")
            current_group = current_group or "其他"
            if current_group not in all_groups:
                all_groups.append(current_group)
            continue
        if line.startswith("#"):
            continue
        # 频道行：名称,URL（用第一个逗号分隔，URL 里若含逗号也不会被拆坏）
        if "," in line:
            name, url = line.split(",", 1)
            name, url = name.strip(), url.strip()
            if name and _valid_url(url):
                channels_by_group.setdefault(current_group, []).append(f"{name},{url}")

    return all_groups, channels_by_group


def parse_m3u(m3u_content):
    """解析 M3U 格式（保留原逻辑）。"""
    all_groups = []
    channels_by_group = {}
    current_group = "其他"
    current_name = None

    for line in m3u_content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTM3U") or line.startswith("#EXT-X-") or line.startswith("//"):
            continue
        if line.startswith("#EXTINF"):
            m = re.search(r',([^,]+)$', line)
            if m:
                current_name = m.group(1).strip()
            gm = re.search(r'group-title="([^"]*)"', line)
            if gm:
                current_group = gm.group(1).strip()
                if current_group not in all_groups:
                    all_groups.append(current_group)
            continue
        if line and not line.startswith("#") and current_name:
            channels_by_group.setdefault(current_group, []).append(f"{current_name},{line}")
            current_name = None

    return all_groups, channels_by_group


def parse_content(text):
    """按格式自动选择解析器，返回 (all_groups, channels_by_group)。"""
    fmt = detect_format(text)
    print(f"  检测到格式: {fmt.upper()}")
    if fmt == "txt":
        return parse_txt(text)
    return parse_m3u(text)


def filter_groups(channels_by_group, exclude_keywords):
    filtered = {}
    skipped = []
    for group_name, channels in channels_by_group.items():
        if any(kw.lower() in group_name.lower() for kw in exclude_keywords):
            skipped.append((group_name, len(channels)))
            continue
        filtered[group_name] = channels
    return filtered, skipped


def main():
    print("=" * 50)
    print("TVBox M3U/TXT → TXT 转换工具 (按分组过滤版)")
    print("=" * 50)

    all_channels = []
    for url in API_URLS:
        print(f"\n正在处理: {url}")
        text = fetch_content(url)
        if not text:
            print("  ✗ 获取失败，跳过")
            continue
        print("  ↳ 解析分组信息...")
        all_groups, channels_by_group = parse_content(text)
        total = sum(len(v) for v in channels_by_group.values())
        print(f"  ↳ 发现 {len(all_groups)} 个分组，共 {total} 个频道")

        print("  ↳ 按分组名过滤...")
        filtered, skipped = filter_groups(channels_by_group, EXCLUDE_KEYWORDS)
        for g, c in skipped:
            print(f"    ✗ 跳过分组 [{g}] - {c} 个频道")

        for g, channels in filtered.items():
            all_channels.extend(channels)

    print(f"\n  ↳ 保留 {len(all_channels)} 个频道")

    if not all_channels:
        print("\n❌ 未获取到任何有效内容，退出")
        return

    unique = list(dict.fromkeys(all_channels))
    dedup = len(all_channels) - len(unique)
    if dedup:
        print(f"  已去除 {dedup} 个重复频道")

    final_content = FIXED_GROUP + "\n" + "\n".join(unique)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_content)

    print("\n" + "=" * 50)
    print(f"✅ 完成！已保存到 {OUTPUT_FILE}")
    print(f"  最终频道数: {len(unique)}")
    print(f"  文件大小: {len(final_content.encode('utf-8'))} 字节")
    print(f"  固定分组: {FIXED_GROUP}")
    print("=" * 50)

    print("\n📄 内容预览（前10行）：")
    for i, line in enumerate(final_content.splitlines()[:10], 1):
        print(f"  {i:2d}. {line[:80]}")


if __name__ == "__main__":
    main()
