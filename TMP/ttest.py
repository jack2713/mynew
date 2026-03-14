import re
import os
import sys
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 全局排除关键词定义（用于分类排除）
EXCLUDE_KEYWORDS = ["移动", "联通", "私密", "少儿", "体育", "记录", "听书", "老年", "解说", 
                     "监控", "DJ", "加入", "(内)", "韩剧", "专用", "动漫", "非诚", "向前冲", 
                     "百分百", "集结号", "好野", "行不行", "更新", "国际影院"]

# 行内容过滤关键词
CONTENT_FILTER_KEYWORDS = ["ottiptv", "盗源", "DJ", "P2p", "shorturl", "更新", "group"]

# 已知包含无效 base-64 的参数名称列表（这些参数经常出现且通常无效）
BAD_BASE64_PARAM_NAMES = {
    'usign', 'accesstoken', 'playtoken', 'play_token', 
    'secret', 'key', 'token', 'sign', 'auth'
}


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
    
    def _looks_like_base64(self, s: str) -> bool:
        """判断字符串是否可能被误认为 base-64"""
        s = s.strip()
        
        # 只包含 base-64 字符
        if not re.match(r'^[A-Za-z0-9+/=]+$', s):
            return False
        
        # 排除明显的非 base-64：纯数字
        if re.match(r'^\d+$', s):
            return False
        
        # 排除短小的纯字母（可能是 ID）
        if re.match(r'^[a-zA-Z]+$', s) and len(s) < 16:
            return False
        
        # 排除常见的十六进制（只包含数字和小写字母 a-f）
        if re.match(r'^[0-9a-f]+$', s) and len(s) < 32:
            return False
        
        return True
    
    def _is_valid_base64(self, s: str) -> bool:
        """严格验证 base-64"""
        s = s.strip()
        
        if len(s) < 4:
            return False
        
        # 长度必须是 4 的倍数
        if len(s) % 4 != 0:
            return False
        
        # 检查填充字符
        pad_count = s.count('=')
        if pad_count > 2:
            return False
        
        # 填充字符必须在末尾且连续
        if '=' in s:
            eq_index = s.index('=')
            remaining = s[eq_index:]
            if not re.match(r'^=+$', remaining):
                return False
        
        try:
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False
    
    def check_line_for_bad_base64(self, line: str) -> tuple:
        """
        检查行中是否包含无效的 base-64 编码
        采用更全面的检查策略，模拟 TVBox 的行为
        """
        reasons = []
        
        # 提取 URL
        url_match = re.search(r'https?://[^\s,]+', line)
        if not url_match:
            return (False, [])
        
        url = url_match.group(0)
        
        # 1. 检查所有参数值
        all_params = re.findall(r'[?&]([^=]+)=([^&\s]+)', url)
        for param_name, param_value in all_params:
            # 策略1：如果参数名在黑名单中，且值看起来像 base-64 但无效，直接过滤
            param_name_lower = param_name.lower()
            if param_name_lower in BAD_BASE64_PARAM_NAMES:
                if self._looks_like_base64(param_value) and len(param_value) >= 8:
                    if not self._is_valid_base64(param_value):
                        reasons.append(f"黑名单参数 {param_name} 无效 (长度:{len(param_value)})")
                        continue
            
            # 策略2：对所有长度>=16且看起来像 base-64 的参数值进行严格检查
            if len(param_value) >= 16 and self._looks_like_base64(param_value):
                if not self._is_valid_base64(param_value):
                    reasons.append(f"参数 {param_name} 无效 (长度:{len(param_value)})")
        
        # 2. 检查 URL 路径段（长度>=32的可能是 base-64）
        path_match = re.search(r'https?://[^/]+(/[^?\s]*)?', url)
        if path_match and path_match.group(1):
            path = path_match.group(1)
            path_segments = [seg for seg in path.split('/') if seg]
            for seg in path_segments:
                if len(seg) >= 32 and self._looks_like_base64(seg):
                    if not self._is_valid_base64(seg):
                        reasons.append(f"路径段无效 (长度:{len(seg)})")
                        break  # 路径段有问题通常整个 URL 都有问题
        
        # 3. 检查特殊分隔符后的内容（$、|）
        for sep_pattern in [r'\$([^&\s]+)', r'\|([^&\s]+)']:
            matches = re.findall(sep_pattern, url)
            for match in matches:
                if len(match) >= 8 and self._looks_like_base64(match):
                    if not self._is_valid_base64(match):
                        reasons.append(f"特殊分隔符后内容无效 (长度:{len(match)})")
        
        # 4. 检查逗号分隔的第三部分及之后的内容（可能是组名或其他信息）
        comma_parts = [p.strip() for p in line.split(',')]
        if len(comma_parts) >= 3:
            for i, part in enumerate(comma_parts[2:], 2):
                if len(part) >= 16 and self._looks_like_base64(part):
                    if not self._is_valid_base64(part):
                        reasons.append(f"第{i}部分无效 (长度:{len(part)})")
        
        return (len(reasons) > 0, reasons)
    
    def remove_genre_lines_and_deduplicate(self, lines: list):
        """
        删除genre行，并按URL去重。
        同时根据 CONTENT_FILTER_KEYWORDS 过滤掉包含指定关键词的行。
        过滤掉包含无效 base-64 编码的行。
        """
        result = []
        seen_urls = set()
        
        filtered_count = 0
        bad_base64_count = 0
        bad_base64_examples = []
        
        for line in lines:
            # 跳过 genre 行
            if "#genre#" in line:
                continue
            
            # 跳过空行
            if not line.strip():
                continue
            
            # 内容过滤（不区分大小写）
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in CONTENT_FILTER_KEYWORDS):
                filtered_count += 1
                continue
            
            # 检查是否包含无效的 base-64 编码
            has_bad, reasons = self.check_line_for_bad_base64(line)
            if has_bad:
                bad_base64_count += 1
                if bad_base64_count <= 10:
                    line_preview = line[:80]
                    bad_base64_examples.append({
                        'line': line_preview,
                        'reasons': reasons
                    })
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
        
        print(f"内容过滤: {filtered_count} 行被过滤")
        print(f"Bad base-64 过滤: {bad_base64_count} 行被过滤")
        
        if bad_base64_examples:
            print("\n  被过滤的示例:")
            for ex in bad_base64_examples:
                print(f"    {ex['line']}...")
                for r in ex['reasons']:
                    print(f"      - {r}")
        
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
            "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg1",
            "https://raw.githubusercontent.com/fafa002/yf2025/refs/heads/main/yiyifafa.txt",
            "https://raw.githubusercontent.com/zxmlxw520/5566/refs/heads/main/cjdszb.txt",
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
        
        # 3. 去重及内容过滤处理（全面 bad base-64 过滤）
        final = self.remove_genre_lines_and_deduplicate(filtered)
        if not final:
            print("去重后无内容")
            self.driver.quit()
            return False
        
        # 4. 保存文件
        if self.save_to_file(final, "ttest.txt", "test,#genre#"):
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
    if success and os.path.exists("ttest.txt"):
        print(f"文件位置: {os.path.abspath('ttest.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
