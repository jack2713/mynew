import re
import os
import sys
import chardet
import requests
from urllib.parse import urlparse

# 全局排除关键词定义
EXCLUDE_KEYWORDS = ["成人", "激情", "虎牙", "体育", "熊猫", "提示","记录","解说","春晚","直播中国","更新","赛事","SPORTS","电视剧","优质个源","明星","主题片","戏曲","游戏","MTV","收音机","悍刀","家人","甄嬛"]

class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
        # 设置requests的请求头，模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def fetch_url_content(self, url: str):
        """使用 requests 获取URL内容，处理编码问题"""
        try:
            print(f"获取: {url}")
            
            # 发送HTTP请求
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()  # 检查请求是否成功
            
            # 检测响应内容的编码
            if response.encoding.lower() == 'utf-8':
                # 如果服务器明确指定了UTF-8编码
                content = response.text
                detected_encoding = 'utf-8'
            else:
                # 自动检测编码
                raw_data = response.content
                detected_encoding = self.detect_encoding(raw_data)
                print(f"  检测到编码: {detected_encoding}")
                
                # 使用检测到的编码解码内容
                try:
                    content = raw_data.decode(detected_encoding, errors='replace')
                except (UnicodeDecodeError, LookupError):
                    # 如果检测的编码无法解码，尝试常用编码
                    encodings_to_try = ['utf-8', 'gbk', 'gb18030', 'big5', 'iso-8859-1']
                    for encoding in encodings_to_try:
                        try:
                            content = raw_data.decode(encoding, errors='strict')
                            detected_encoding = encoding
                            print(f"  使用备用编码: {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # 所有编码都失败，使用UTF-8并忽略错误
                        content = raw_data.decode('utf-8', errors='replace')
                        detected_encoding = 'utf-8'
            
            # 清理并分割行
            lines = []
            for line in content.splitlines():
                line = line.strip()
                if line:
                    # 修复编码问题
                    line = self.fix_encoding_issues(line, detected_encoding)
                    lines.append(line)
            
            print(f"  成功: {len(lines)} 行")
            return lines
            
        except requests.exceptions.RequestException as e:
            print(f"  网络请求失败: {e}")
            return []
        except Exception as e:
            print(f"  处理失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def detect_encoding(self, data: bytes) -> str:
        """检测字节数据的编码"""
        try:
            # 使用chardet检测编码
            result = chardet.detect(data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            print(f"  chardet检测: {encoding} (置信度: {confidence:.2f})")
            
            if encoding:
                encoding = encoding.lower()
                # 规范化编码名称
                if 'gb' in encoding and '18030' not in encoding:
                    return 'gb18030'  # 使用最全的中文编码
                elif encoding in ['utf-8', 'utf8']:
                    return 'utf-8'
                elif 'big5' in encoding:
                    return 'big5'
                elif 'iso-8859' in encoding:
                    return 'utf-8'  # 通常需要转换为UTF-8
                else:
                    return encoding
            
            return 'utf-8'
        except Exception as e:
            print(f"  编码检测失败: {e}")
            return 'utf-8'

    def fix_encoding_issues(self, text: str, original_encoding: str = 'utf-8') -> str:
        """修复编码问题"""
        if not text:
            return text
        
        # 检查是否已经包含正常的中文字符
        if self.contains_chinese(text):
            # 如果已经有中文字符，直接返回
            return text
        
        # 常见的编码错误修复（UTF-8被错误解释的情况）
        try:
            # 尝试将文本重新编码为原始编码，然后解码为UTF-8
            if original_encoding != 'utf-8':
                try:
                    # 先将文本编码回原始编码的字节
                    encoded_bytes = text.encode('iso-8859-1', errors='ignore')
                    # 再使用正确的编码解码
                    decoded = encoded_bytes.decode(original_encoding, errors='ignore')
                    if self.contains_chinese(decoded):
                        return decoded
                except:
                    pass
        except:
            pass
        
        # 尝试常见的编码转换
        common_encodings = ['gbk', 'gb18030', 'big5', 'utf-8']
        for encoding in common_encodings:
            try:
                # 假设文本是UTF-8但被错误解释，尝试用其他编码重新解释
                if encoding != 'utf-8':
                    encoded_bytes = text.encode('iso-8859-1', errors='ignore')
                    decoded = encoded_bytes.decode(encoding, errors='ignore')
                    if self.contains_chinese(decoded):
                        return decoded
            except:
                continue
        
        return text

    def contains_chinese(self, text: str) -> bool:
        """检查是否包含中文字符"""
        import re
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars) > 3  # 至少3个中文字符才认为是包含中文

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
        """保存到文件，确保UTF-8编码"""
        try:
            content = [first_line] + lines
            
            # 使用UTF-8 with BOM保存，确保Windows系统能正确识别
            with open(filename, 'w', encoding='utf-8-sig') as f:
                f.write('\n'.join(content))
            
            file_size = os.path.getsize(filename)
            print(f"保存: {filename} ({len(content)}行, {file_size}字节)")
            
            # 验证文件编码和内容
            self.verify_file_encoding(filename)
            
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verify_file_encoding(self, filename: str):
        """验证文件编码是否正确"""
        try:
            # 读取文件内容
            with open(filename, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            # 统计中文字符数量
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
            print(f"文件包含中文数量: {len(chinese_chars)} 个字符")
            
            # 显示一些中文示例
            if chinese_chars:
                samples = chinese_chars[:10]
                print(f"中文示例: {''.join(samples)}...")
            
            # 检查是否有明显的乱码字符
            garbled_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]')
            garbled = garbled_pattern.findall(content[:1000])
            if garbled:
                print(f"警告: 发现潜在乱码字符: {set(garbled)}")
            
        except Exception as e:
            print(f"编码验证失败: {e}")

    def process(self):
        """主处理流程"""
        print("开始处理直播源")
        # 使用指定的URL
        urls = [
            "https://txt.gt.tc/users/HKTV.txt?i=1",
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
        print("错误: requests库未安装，请运行: pip install requests chardet")
        sys.exit(1)
    
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
