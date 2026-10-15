import requests
import re
import os
from urllib.parse import urlparse


def convert_m3u_to_txt(urls, exclude_chars=None, output_file="TMP/temp.txt"):
    """
    将指定URL列表中的M3U内容转换为TXT格式并保存到文件

    Args:
        urls (list): M3U文件的URL列表
        exclude_chars (list): 需要排除的字符列表，包含这些字符的行会被过滤掉
        output_file (str): 输出文件路径
    """
    if exclude_chars is None:
        exclude_chars = []

    channels = []          # (频道名, URL) 有序列表
    channel_set = set()    # 用 (name, url) 做去重

    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            lines = content.splitlines()

            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('#EXTINF'):
                    # 提取频道名（最后一个逗号之后）
                    name_start = line.rfind(',') + 1
                    name = line[name_start:] if name_start < len(line) else ''

                    # 提取分组信息（仅用于过滤判断）
                    group_match = re.search(r'group-title="([^"]+)"', line)
                    group_name = group_match.group(1) if group_match else ''

                    # 名称或分组命中排除词 → 跳过整条
                    if any(c in name or c in group_name for c in exclude_chars):
                        i += 1
                        continue

                    # 下一行是URL
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line.startswith('http'):
                            if not any(c in next_line for c in exclude_chars):
                                key = (name, next_line)
                                if key not in channel_set:
                                    channels.append((name, next_line))
                                    channel_set.add(key)
                                i += 1  # 跳过已处理的URL行
                i += 1

        except Exception as e:
            print(f"处理URL {url} 时出错: {e}")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    # 第一行固定"测试,#genre#"，后面直接跟频道数据（不再有分组标题）
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('测试,#genre#\n')
        f.write('\n'.join(f"{name},{url}" for name, url in channels))

    print(f"转换完成，结果已保存到 {output_file}")
    print(f"共 {len(channels)} 个频道")


if __name__ == "__main__":
    m3u_urls = [
        # "https://raw.githubusercontent.com/xJEYDAin/iptv-scraper/refs/heads/master/output/all_merged.m3u",
        "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels.m3u",
        "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
        "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u",
        # "https://raw.githubusercontent.com/yy-niuma/live-tv/refs/heads/main/output/all_merged.m3u",
        # "https://xoxo.cn.mt/Lonely.m3u",
        # "https://raw.githubusercontent.com/joaquinito2036-rgb/iptvfast/refs/heads/main/output/all.m3u",
    ]
    exclude_chars = [
        "wns.live", "cloudfront.net", "stevosure123",
        "visionplus.id", "google", "ads.deviceid"
    ]
    convert_m3u_to_txt(m3u_urls, exclude_chars)
