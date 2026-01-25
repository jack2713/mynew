import requests
import re
import os
import sys  # 添加这行

# 全局排除关键词定义
EXCLUDE_KEYWORDS = ["成人", "激情", "情色", "涩情", "18禁", "R18"]

class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
    
    def fetch_url_content(self, url: str):
        """获取单个URL内容"""
        try:
            print(f"获取: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 处理编码
            if response.encoding:
                content = response.text
            else:
                content = response.content.decode('utf-8', errors='ignore')
            
            # 清理并分割行
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
        """删除genre行并去重"""
        result = []
        seen_urls = set()
        
        for line in lines:
            if "#genre#" in line:
                continue
            if not line.strip():
                continue
            
            # 提取URL去重
            url_match = re.search(r'(https?://[^\s,]+)', line)
            if url_match:
                url = url_match.group(1)
                if url not in seen_urls:
                    seen_urls.add(url)
                    result.append(line)
            else:
                result.append(line)
        
        print(f"去重后: {len(result)} 行")
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
        print("开始处理直播源")
        
        # 只使用指定的URL
        urls = [
           # "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/斯瑪特直播源1",
            "https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/my.txt",
        ]
        
        print(f"源URL: {len(urls)}个")
        
        # 1. 获取内容
        if not self.fetch_multiple_urls(urls):
            print("无内容可处理")
            return False
        
        # 2. 排除处理
        filtered = self.remove_excluded_sections()
        if not filtered:
            print("排除后无内容")
            return False
        
        # 3. 去重处理
        final = self.remove_genre_lines_and_deduplicate(filtered)
        if not final:
            print("去重后无内容")
            return False
        
        # 4. 保存文件
        if self.save_to_file(final, "my1.txt", "smt,#genre#"):
            print("处理完成")
            return True
        else:
            return False


def main():
    """主函数"""
    processor = TVSourceProcessor()
    success = processor.process()
    
    # 退出状态码
    if success and os.path.exists("my1.txt"):
        print(f"文件位置: {os.path.abspath('my1.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
