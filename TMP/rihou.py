import re
import os
import sys
import requests

# 全局排除关键词定义（用于分类排除）
EXCLUDE_KEYWORDS = [
    "猫TV", "赛评", "赛事", "全集", "华山论剑", "三国粤", "大时代","世杯",
    "流星花园", "还珠格格", "甄嬛", "大地恩情", "粤经典剧",
    "射雕英雄", "神雕侠侣", "音乐", "凡人修仙", "轮播",
    "频晴", "频陆", "地区", "轮播", "测试", "移动", "赛事", "内网",
    "限", "歌曲","移动", "联通","私密","少儿","体育","记录","听书","老年","解说","监控","DJ","加入","(内)","韩剧","专用",
                    "动漫","非诚","向前冲","百分百","集结号","好野","行不行","更新","国际影院","专用","上海综合","江西综合",
                    "虎牙","斗鱼","电台","定制","综艺","电视剧","广场舞","戏曲","风景","游戏","梯","TG","三网2","NBA","直播","四季","内网","测试"
]

# 行内容过滤关键词
CONTENT_FILTER_KEYWORDS = [
    "盗源", "DJ", "p3p", "shorturl", "更新", "group", "颜人中",
    "打赏", "购买", "河南网", "阜阳", "野草", "少儿", "广东体育",
    "\\", "iill.top", "凡人修仙传", "woshinibaba", "cfss.cc",
    "75.127.89.169","ottiptv","P2p","111.56.90.5","47.92.252.72","合集","huya","douyu","iptv.852851.xyz","catvod"
]


class TVSourceProcessor:
    def __init__(self):
        # 按 (url, genre_name) 对存储，格式: [(url, genre), ...]
        self.url_genre_pairs = []
        # 按 genre 分组存储原始行: {genre: [lines]}
        self.genre_lines = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        })

    def parse_urls_config(self, urls_config):
        """
        解析 URL 配置，支持两种格式：
        1. 旧格式: ["url1", "url2", ...]
        2. 新格式: ["url1", "段名1", "url2", "段名2", ...]
        如果没有段名，默认使用 "default"
        """
        pairs = []
        i = 0
        while i < len(urls_config):
            url = urls_config[i]
            # 检查下一个元素是否是段名（非URL的字符串）
            if i + 1 < len(urls_config) and not urls_config[i + 1].startswith('http'):
                genre = urls_config[i + 1]
                i += 2
            else:
                genre = "default"
                i += 1
            pairs.append((url, genre))
        self.url_genre_pairs = pairs
        print(f"URL配置解析: {len(pairs)}个源")
        for url, genre in pairs:
            print(f"  [{genre}] {url}")
        return pairs

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

    def fetch_multiple_urls(self, urls_config):
        """获取多个URL内容，按段名分组存储"""
        pairs = self.parse_urls_config(urls_config)
        total_lines = 0
        for url, genre in pairs:
            lines = self.fetch_url_content(url)
            if lines:
                if genre not in self.genre_lines:
                    self.genre_lines[genre] = []
                self.genre_lines[genre].extend(lines)
                total_lines += len(lines)
        print(f"总计: {total_lines} 行, {len(self.genre_lines)} 个段")
        return total_lines > 0

    def remove_excluded_sections(self, lines: list):
        """排除指定区域（针对单个段的行列表）"""
        if not lines:
            return []
        result = []
        in_excluded_section = False
        for line in lines:
            if "#genre#" in line:
                if any(keyword in line for keyword in EXCLUDE_KEYWORDS):
                    in_excluded_section = True
                else:
                    in_excluded_section = False
                result.append(line)
            elif not in_excluded_section:
                result.append(line)
        return result

    def remove_genre_lines_and_deduplicate(self, lines: list, seen_urls: set):
        """
        删除genre行，按URL全局去重，并过滤内容关键词
        seen_urls 跨段共享，确保同一URL不会出现在多个段中
        """
        result = []
        filtered_count = 0
        dup_count = 0
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
                    dup_count += 1
            else:
                result.append(line)
        print(f"  内容过滤: {filtered_count} 行, 去重: {dup_count} 行, 保留: {len(result)} 行")
        return result

    def process_genre_lines(self):
        """对所有段分别处理：排除区域 → 过滤去重"""
        seen_urls = set()  # 全局去重集合，跨段共享
        processed = {}
        for genre, lines in self.genre_lines.items():
            print(f"\n处理段: {genre} ({len(lines)} 行)")
            filtered = self.remove_excluded_sections(lines)
            if not filtered:
                print(f"  排除后无内容")
                continue
            final = self.remove_genre_lines_and_deduplicate(filtered, seen_urls)
            if final:
                processed[genre] = final
        return processed

    def save_to_file(self, genre_lines: dict, filename: str):
        """
        按段写入文件，每个段以 "段名,#genre#" 开头
        段之间空一行分隔
        """
        try:
            content = []
            for genre, lines in genre_lines.items():
                content.append(f"{genre},#genre#")
                content.extend(lines)
                content.append("")  # 段间空行
            # 去掉末尾多余的空行
            while content and content[-1] == "":
                content.pop()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            file_size = os.path.getsize(filename)
            total_lines = len(content)
            print(f"\n保存: {filename} ({total_lines}行, {file_size}字节)")
            # 打印各段统计
            for genre, lines in genre_lines.items():
                print(f"  [{genre}] {len(lines)} 个频道")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def process(self):
        """主处理流程"""
        print("开始处理直播源")
        # URL配置：url, 段名 交替排列
        # 段名紧跟在URL后面，表示该URL的频道归入哪个段
        urls = [
            "http://wangziduoqing.com/yuan/zb.txt", "yuan",
            "http://rihou.cc:555/gggg.nzk", "rihou",
            "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg1","test",
            "https://raw.githubusercontent.com/fafa002/yf2025/refs/heads/main/yiyifafa.txt","test",
            "https://raw.githubusercontent.com/zxmlxw520/5566/refs/heads/main/cjdszb.txt","test",
            "https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/TMP/temp.txt","yuchen",
            "https://raw.githubusercontent.com/swhtv/1/refs/heads/main/swtvlive","swtv",
        ]
        print(f"源URL: {len(urls)}个配置项")
        if not self.fetch_multiple_urls(urls):
            print("无内容可处理")
            return False

        processed = self.process_genre_lines()
        if not processed:
            print("处理后无内容")
            return False

        if self.save_to_file(processed, "rihou.txt"):
            print("处理完成")
            return True
        return False


def main():
    processor = TVSourceProcessor()
    success = processor.process()
    if success and os.path.exists("rihou.txt"):
        print(f"文件位置: {os.path.abspath('rihou.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
