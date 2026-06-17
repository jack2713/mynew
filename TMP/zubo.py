#!/usr/bin/env python3
import re
import os
import sys
import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 全局排除关键词定义（用于分类排除）
EXCLUDE_KEYWORDS = ["移动", "联通"]

# 行内容过滤关键词
CONTENT_FILTER_KEYWORDS = ["CCTV", "CG", "卫视"]

# 网络连接测试超时（秒）
CONNECT_TIMEOUT = 3

# 连接测试并发数
MAX_WORKERS = 50


class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.connect_cache = {}

    def fetch_url_content(self, url: str):
        """使用 requests 获取URL内容"""
        try:
            print(f"获取: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            content = response.text
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            print(f"  成功: {len(lines)} 行")
            return lines
        except Exception as e:
            print(f"  失败: {e}")
            return []

    def fetch_multiple_urls(self, urls: list):
        """获取多个URL内容"""
        self.all_lines = []
        for url in urls:
            lines = self.fetch_url_content(url)
            if lines:
                self.all_lines.extend(lines)
        print(f"总计: {len(self.all_lines)} 行")
        return len(self.all_lines) > 0

    def remove_excluded_sections(self):
        """排除指定区域"""
        if not self.all_lines:
            return []
        result = []
        in_excluded_section = False
        for line in self.all_lines:
            if "#genre#" in line:
                if any(keyword in line for keyword in EXCLUDE_KEYWORDS):
                    in_excluded_section = True
                else:
                    in_excluded_section = False
                result.append(line)
            elif not in_excluded_section:
                result.append(line)
        print(f"排除后: {len(result)} 行")
        return result

    def remove_genre_lines_and_deduplicate(self, lines: list):
        """删除genre行，按URL去重，并过滤内容关键词"""
        result = []
        seen_urls = set()
        filtered_count = 0
        for line in lines:
            if "#genre#" in line:
                continue
            if not line.strip():
                continue
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in CONTENT_FILTER_KEYWORDS):
                filtered_count += 1
                continue
            url_match = re.search(r'(https?://[^\s,]+)', line)
            if url_match:
                url = url_match.group(1)
                if url not in seen_urls:
                    seen_urls.add(url)
                    result.append(line)
            else:
                result.append(line)
        print(f"内容过滤: {filtered_count} 行被过滤")
        print(f"去重后: {len(result)} 行")
        return result

    def _test_single_connection(self, host: str, port: int):
        """测试单个 ip:port 的TCP连通性"""
        key = f"{host}:{port}"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECT_TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            return key, (result == 0)
        except Exception:
            return key, False

    def test_connections(self, lines: list):
        """对所有行的ip:port进行连通性测试，相同ip:port只测一次"""
        ip_port_map = {}
        line_to_ipport = {}

        # 支持 http/rtp/rtsp/rtmp 中的 ip:port，以及裸 ip:port
        pattern_url = re.compile(r'(?:https?|rtp|rtsp|rtmp)://(\d+\.\d+\.\d+\.\d+):(\d+)')
        pattern_raw = re.compile(r'(\d+\.\d+\.\d+\.\d+):(\d+)')

        for i, line in enumerate(lines):
            m = pattern_url.search(line)
            if not m:
                m = pattern_raw.search(line)
            if m:
                ip, port = m.group(1), int(m.group(2))
                key = f"{ip}:{port}"
                ip_port_map[key] = None
                line_to_ipport[i] = key

        if not ip_port_map:
            print("未发现任何IP:端口，跳过连接测试")
            return lines

        unique_count = len(ip_port_map)
        print(f"\n连接测试: 发现 {unique_count} 个唯一 ip:port，并发 {MAX_WORKERS}，超时 {CONNECT_TIMEOUT}s")

        success_count = 0
        fail_count = 0
        done_count = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for key in ip_port_map:
                parts = key.split(":")
                host, port = parts[0], int(parts[1])
                futures[executor.submit(self._test_single_connection, host, port)] = key

            for future in as_completed(futures):
                key, is_ok = future.result()
                ip_port_map[key] = is_ok
                done_count += 1
                if is_ok:
                    success_count += 1
                else:
                    fail_count += 1
                if done_count % 50 == 0 or done_count == unique_count:
                    print(f"  进度: {done_count}/{unique_count}  成功:{success_count}  失败:{fail_count}")

        print(f"连接测试完成: 成功 {success_count}, 失败 {fail_count}")

        # 过滤掉连接失败的行
        result = []
        dropped = 0
        for i, line in enumerate(lines):
            key = line_to_ipport.get(i)
            if key is None:
                result.append(line)
            elif ip_port_map.get(key, False):
                result.append(line)
            else:
                dropped += 1

        print(f"连通性过滤: {dropped} 行被移除，保留 {len(result)} 行")
        return result

    def save_to_file(self, lines: list, filename: str, first_line: str):
        """保存到文件"""
        try:
            content = [first_line] + lines
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            file_size = os.path.getsize(filename)
            print(f"保存: {filename} ({len(content)}行, {file_size}字节)")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def process(self):
        """主处理流程"""
        print("=" * 50)
        print("开始处理直播源")
        print("=" * 50)

        urls = [
            "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt"
        ]
        print(f"源URL: {len(urls)}个")

        if not self.fetch_multiple_urls(urls):
            print("无内容可处理")
            return False

        filtered = self.remove_excluded_sections()
        if not filtered:
            print("排除后无内容")
            return False

        final = self.remove_genre_lines_and_deduplicate(filtered)
        if not final:
            print("去重后无内容")
            return False

        final = self.test_connections(final)

        if not final:
            print("连通性过滤后无内容")
            return False

        if self.save_to_file(final, "zubo.txt", "组播,#genre#"):
            print("处理完成")
            return True
        return False


def main():
    processor = TVSourceProcessor()
    success = processor.process()
    if success and os.path.exists("zubo.txt"):
        print(f"文件位置: {os.path.abspath('zubo.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
