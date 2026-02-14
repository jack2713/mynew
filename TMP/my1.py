import requests
import os
import sys

# 全局排除关键词定义
EXCLUDE_KEYWORDS = ["成人", "激情", "虎牙", "体育", "熊猫", "提示","记录","解说","春晚","直播","更新","赛事","SPORTS","电视剧","优质个源","明星","主题片","戏曲","游戏","MTV","收音机","悍刀","家人"]

class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
        
    def fetch_url_content(self, url: str):
        """直接获取URL内容，强制转换为UTF-8"""
        try:
            print(f"获取: {url}")
            
            # 发送HTTP请求，设置超时和请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 直接使用原始字节数据，强制转换为UTF-8
            content_bytes = response.content
            
            # 尝试多种方式解码，优先UTF-8，如果失败尝试其他编码
            decoded_content = None
            
            # 尝试UTF-8解码
            try:
                decoded_content = content_bytes.decode('utf-8')
                print(f"  使用UTF-8解码成功")
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试GBK编码（常见的中文编码）
                try:
                    decoded_content = content_bytes.decode('gbk')
                    print(f"  使用GBK解码成功")
                except UnicodeDecodeError:
                    # 如果GBK也失败，尝试GB18030（中文扩展编码）
                    try:
                        decoded_content = content_bytes.decode('gb18030')
                        print(f"  使用GB18030解码成功")
                    except UnicodeDecodeError:
                        # 如果所有尝试都失败，使用UTF-8并忽略错误
                        decoded_content = content_bytes.decode('utf-8', errors='ignore')
                        print(f"  使用UTF-8(忽略错误)解码")
            
            # 分割行
            lines = [line.strip() for line in decoded_content.splitlines() if line.strip()]
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
        import re
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
        """强制使用UTF-8编码保存到文件"""
        try:
            content = [first_line] + lines
            
            # 确保所有内容都是字符串
            str_lines = []
            for line in content:
                if isinstance(line, bytes):
                    # 如果是字节，尝试解码
                    try:
                        str_lines.append(line.decode('utf-8'))
                    except:
                        str_lines.append(str(line, errors='ignore'))
                else:
                    str_lines.append(str(line))
            
            # 使用UTF-8编码保存
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(str_lines))
            
            file_size = os.path.getsize(filename)
            print(f"保存: {filename} ({len(str_lines)}行, {file_size}字节)")
            print(f"编码: UTF-8")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def process(self):
        """主处理流程"""
        print("开始处理直播源")
        # 使用指定的URL
        urls = [
            "https://live.hacks.tools/tv/iptv4.txt",
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
    # 检查requests库是否安装
    try:
        import requests
    except ImportError:
        print("错误: requests库未安装，请运行: pip install requests")
        sys.exit(1)
    
    processor = TVSourceProcessor()
    success = processor.process()
    
    # 退出状态码
    if success and os.path.exists("my1.txt"):
        print(f"文件位置: {os.path.abspath('my1.txt')}")
        # 显示文件前几行
        try:
            with open("my1.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"文件前5行内容:")
                for i in range(min(5, len(lines))):
                    print(f"  {i+1}: {lines[i].strip()}")
        except Exception as e:
            print(f"读取文件内容失败: {e}")
        
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
