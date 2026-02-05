import re
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 全局排除关键词定义
EXCLUDE_KEYWORDS = ["成人", "激情", "虎牙", "体育", "熊猫", "提示","记录","解说","春晚","直播中国","更新","赛事","SPORTS","电视剧","优质个源","明星","主题片","戏曲","游戏","MTV","收音机","悍刀","家人","甄嬛"]

class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
        # 配置 Chrome 无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)

    def fetch_url_content(self, url: str):
        """使用 Selenium 获取URL内容"""
        try:
            print(f"获取: {url}")
            self.driver.get(url)
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "pre"))
            )
            
            # 获取页面内容
            content = self.driver.find_element(By.TAG_NAME, "pre").text
            
            # 清理并分割行
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            print(f" 成功: {len(lines)} 行")
            return lines
        except Exception as e:
            print(f" 失败: {e}")
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
            "https://txt.gt.tc/users/HKTV.txt?i=1",
            "https://live.hacks.tools/tv/iptv4.txt",
            "https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/bbxx.txt",
        ]
        print(f"源URL: {len(urls)}个")
        
        # 1. 获取内容
        if not self.fetch_multiple_urls(urls):
            print("无内容可处理")
            self.driver.quit()
            return False
        
        # 2. 排除处理
        filtered = self.remove_excluded_sections()
        if not filtered:
            print("排除后无内容")
            self.driver.quit()
            return False
        
        # 3. 去重处理
        final = self.remove_genre_lines_and_deduplicate(filtered)
        if not final:
            print("去重后无内容")
            self.driver.quit()
            return False
        
        # 4. 保存文件
        if self.save_to_file(final, "my1.txt", "smt,#genre#"):
            print("处理完成")
            self.driver.quit()
            return True
        else:
            self.driver.quit()
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
