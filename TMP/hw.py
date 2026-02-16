import os
import re
import requests
from typing import List, Optional

class WebContentFilter:
    def __init__(self, tmp_dir: str = "TMP"):
        self.tmp_dir = tmp_dir
        os.makedirs(tmp_dir, exist_ok=True)
        
    def fetch_url_content(self, url: str) -> Optional[str]:
        """获取单个URL的内容"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            print(f"获取URL {url} 失败: {e}")
            return None
    
    def filter_segments(self, content: str, exclude_words: List[str]) -> str:
        """过滤包含指定关键词的#genren#段"""
        if not exclude_words:
            return content
            
        # 分割成#genren#段
        segments = re.split(r'(#genren#)', content)
        filtered_segments = []
        
        i = 0
        while i < len(segments):
            if segments[i] == '#genren#' and i + 1 < len(segments):
                segment_content = segments[i+1]
                # 检查是否包含排除关键词
                exclude_segment = any(word in segment_content for word in exclude_words)
                if not exclude_segment:
                    filtered_segments.append('#genren#')
                    filtered_segments.append(segment_content)
                i += 2
            else:
                filtered_segments.append(segments[i])
                i += 1
                
        return ''.join(filtered_segments)
    
    def filter_lines(self, content: str, exclude_words: List[str]) -> str:
        """过滤包含指定关键词的行"""
        if not exclude_words:
            return content
            
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            if not any(word in line for word in exclude_words):
                filtered_lines.append(line)
                
        return '\n'.join(filtered_lines)
    
    def process_urls(self, urls: List[str], 
                     exclude_segment_words: List[str] = None,
                     exclude_line_words: List[str] = None,
                     output_file: str = "s.txt") -> None:
        """处理URL列表并保存结果"""
        exclude_segment_words = exclude_segment_words or []
        exclude_line_words = exclude_line_words or []
        
        all_content = []
        
        for url in urls:
            print(f"正在处理: {url}")
            content = self.fetch_url_content(url)
            if content:
                # 先过滤段
                filtered_content = self.filter_segments(content, exclude_segment_words)
                # 再过滤行
                filtered_content = self.filter_lines(filtered_content, exclude_line_words)
                all_content.append(filtered_content)
                
        # 保存结果
        output_path = os.path.join(self.tmp_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_content))
            
        print(f"处理完成，结果已保存到: {output_path}")

if __name__ == "__main__":
    # 示例配置
    urls = [
        "https://raw.githubusercontent.com/bj123sd/IPTV/refs/heads/main/hycg.txt",
        #"https://example.com/page2"
    ]
    
    # 过滤包含IPTV或直播的#genren#段
    exclude_segment_words = ["IPTV"]
    
    # 过滤包含sss的行
    exclude_line_words = ["PLTV"]
    
    # 创建过滤器实例
    filter = WebContentFilter()
    
    # 处理URL
    filter.process_urls(
        urls=urls,
        exclude_segment_words=exclude_segment_words,
        exclude_line_words=exclude_line_words
    )
