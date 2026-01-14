import requests
import re
import os

# 全局排除关键词定义
EXCLUDE_KEYWORDS = ["成人", "激情", "情色", "涩情", "18禁", "R18"]

class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
    
    def fetch_url_content(self, url: str):
        try:
            print(f"获取: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            content = response.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            print(f"获取 {len(lines)} 行")
            return lines
            
        except Exception as e:
            print(f"失败: {url} - {e}")
            return []
    
    def fetch_multiple_urls(self, urls: list):
        self.all_lines = []
        for url in urls:
            lines = self.fetch_url_content(url)
            self.all_lines.extend(lines)
        print(f"总计: {len(self.all_lines)} 行")
    
    def remove_excluded_sections(self):
        if not self.all_lines:
            return []
        
        result = []
        in_excluded_section = False
        
        for line in self.all_lines:
            if "#genre#" in line:
                if any(keyword in line for keyword in EXCLUDE_KEYWORDS):
                    in_excluded_section = True
                    print(f"排除: {line[:50]}...")
                else:
                    in_excluded_section = False
                    result.append(line)
            elif not in_excluded_section:
                result.append(line)
        
        print(f"排除后: {len(result)} 行")
        return result
    
    def remove_genre_lines_and_deduplicate(self, lines: list):
        result = []
        seen_urls = set()
        
        for line in lines:
            if "#genre#" in line:
                continue
            if not line.strip():
                continue
            
            # 提取URL
            urls = re.findall(r'https?://[^\s,]+', line)
            if urls:
                url_part = urls[0]
                if url_part not in seen_urls:
                    seen_urls.add(url_part)
                    result.append(line)
            else:
                result.append(line)
        
        print(f"去重后: {len(result)} 行")
        return result
    
    def save_to_file(self, lines: list, filename: str = "my1.txt", first_line: str = "smt,#genre#"):
        try:
            content = [first_line] + lines if first_line else lines
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            print(f"保存: {filename} ({len(content)}行)")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def process(self, urls: list, output_file: str = "my1.txt", first_line: str = "smt,#genre#"):
        print("=" * 50)
        print("TV直播源处理工具")
        print(f"排除关键词: {EXCLUDE_KEYWORDS}")
        print("=" * 50)
        
        # 获取URL内容
        self.fetch_multiple_urls(urls)
        if not self.all_lines:
            print("无内容")
            return
        
        # 排除处理
        filtered_lines = self.remove_excluded_sections()
        if not filtered_lines:
            print("无剩余内容")
            return
        
        # 去重处理
        final_lines = self.remove_genre_lines_and_deduplicate(filtered_lines)
        
        # 保存结果
        self.save_to_file(final_lines, output_file, first_line)
        print("=" * 50)
        print("处理完成!")
        print("=" * 50)


def main():
    """主处理函数"""
    # 直接在代码中定义要处理的URL列表
    urls = [
        "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/斯瑪特直播源1",
        "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/斯瑪特直播源2"
        # 可以添加更多URL
    ]
    
    # 配置参数
    output_file = "my1.txt"
    first_line = "smt,#genre#"
    
    # 执行处理
    processor = TVSourceProcessor()
    processor.process(urls, output_file, first_line)


if __name__ == "__main__":
    # 直接运行，无需用户交互
    main()
