# process_iptv.py
import requests
import time
from typing import List, Dict
import os

class IPTVProcessor:
    def __init__(self):
        # 定义1：需要写入文件1的类别
        self.categories_file1 = {"新聞", "香港", "央视", "卫视", "CCTV", "卫视"}
        # 定义2：需要写入文件2的类别
        self.categories_file2 = {"体育", "台湾", "电影", "娱乐", "动漫", "少儿"}
        
        # 存储从各个URL获取的内容
        self.all_content = []
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # GitHub Raw URLs
        self.urls = [
            "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/%E5%88%AB%E4%BA%BA%E6%94%B6%E8%B4%B9%E6%BA%90",
            "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/%E6%B5%B7%E8%A7%92%E7%A4%BE%E5%8C%BA%E5%8D%9A%E4%B8%BB(%E5%85%8D%E7%95%AA%E5%BC%BA)"
        ]
    
    def fetch_content_from_urls(self) -> None:
        """从多个URL获取内容"""
        print("开始从GitHub Raw URL获取IPTV源数据...")
        
        for i, url in enumerate(self.urls):
            try:
                print(f"正在获取 URL {i+1}/{len(self.urls)}: {url}")
                response = requests.get(url, headers=self.headers, timeout=20)
                response.raise_for_status()
                content = response.text
                
                # 检查内容是否有效
                if len(content.strip()) > 100:  # 确保不是空文件或错误页面
                    self.all_content.append(content)
                    print(f"✓ 获取成功，长度: {len(content):,} 字符")
                else:
                    print(f"⚠ 内容过短或可能为空，跳过")
                
                time.sleep(1)  # 礼貌延迟
                
            except Exception as e:
                print(f"✗ 获取失败: {e}")
    
    def parse_content(self, content: str) -> Dict[str, List[str]]:
        """解析内容，按类别分组"""
        categories = {}
        current_category = None
        category_lines = []
        
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是类别行（包含,#genre#）
            if ',#genre#' in line:
                # 保存上一个类别的内容
                if current_category and category_lines:
                    if current_category not in categories:
                        categories[current_category] = []
                    # 去重
                    for item in category_lines:
                        if item not in categories[current_category]:
                            categories[current_category].append(item)
                
                # 开始新类别
                current_category = line.split(',')[0].strip()
                category_lines = [line]
            elif current_category is not None:
                # 如果是频道行，添加到当前类别
                if line and line not in category_lines:
                    category_lines.append(line)
        
        # 保存最后一个类别
        if current_category and category_lines:
            if current_category not in categories:
                categories[current_category] = []
            # 去重
            for item in category_lines:
                if item not in categories[current_category]:
                    categories[current_category].append(item)
        
        return categories
    
    def process_and_write_files(self):
        """处理内容并写入文件"""
        # 获取内容
        self.fetch_content_from_urls()
        
        if not self.all_content:
            print("错误: 未获取到任何内容")
            return
        
        print(f"\n成功获取 {len(self.all_content)} 个源文件")
        
        # 处理内容
        all_categories_file1 = {}
        all_categories_file2 = {}
        
        for content in self.all_content:
            categories = self.parse_content(content)
            
            for category, lines in categories.items():
                # 检查类别是否匹配定义
                matched_file1 = False
                matched_file2 = False
                
                # 检查是否属于文件1的类别
                for cat1 in self.categories_file1:
                    if cat1 in category:
                        if category not in all_categories_file1:
                            all_categories_file1[category] = []
                        # 去重添加
                        for line in lines:
                            if line not in all_categories_file1[category]:
                                all_categories_file1[category].append(line)
                        matched_file1 = True
                        break
                
                # 检查是否属于文件2的类别
                if not matched_file1:
                    for cat2 in self.categories_file2:
                        if cat2 in category:
                            if category not in all_categories_file2:
                                all_categories_file2[category] = []
                            # 去重添加
                            for line in lines:
                                if line not in all_categories_file2[category]:
                                    all_categories_file2[category].append(line)
                            matched_file2 = True
                            break
        
        # 写入文件1
        self.write_file("my1.txt", all_categories_file1)
        
        # 写入文件2
        self.write_file("my2.txt", all_categories_file2)
        
        # 打印统计信息
        self.print_statistics(all_categories_file1, all_categories_file2)
    
    def write_file(self, filename: str, categories: Dict[str, List[str]]):
        """写入文件"""
        if not categories:
            print(f"警告: {filename} 没有内容可写入")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# 无相关内容\n")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            for category in sorted(categories.keys()):
                # 写入类别行
                if categories[category] and categories[category][0].endswith(',#genre#'):
                    f.write(categories[category][0] + '\n')
                    # 写入频道行（跳过类别行）
                    for line in categories[category][1:]:
                        f.write(line + '\n')
                else:
                    # 如果没有类别行，添加一个
                    f.write(f"{category},#genre#\n")
                    for line in categories[category]:
                        f.write(line + '\n')
                f.write('\n')  # 类别之间空一行
        
        print(f"✓ 已写入文件: {filename}")
    
    def print_statistics(self, file1_cats, file2_cats):
        """打印统计信息"""
        total_channels_file1 = sum(len(lines) - 1 for lines in file1_cats.values() if lines)
        total_channels_file2 = sum(len(lines) - 1 for lines in file2_cats.values() if lines)
        
        print("\n" + "="*50)
        print("处理完成统计:")
        print("="*50)
        print(f"my1.txt: {len(file1_cats)} 个类别，约 {total_channels_file1} 个频道")
        print(f"my2.txt: {len(file2_cats)} 个类别，约 {total_channels_file2} 个频道")
        print("="*50)


def main():
    """主函数"""
    print("开始处理IPTV源数据...")
    
    processor = IPTVProcessor()
    
    try:
        processor.process_and_write_files()
        print("\n✅ 处理完成！文件已生成:")
        print("   - my1.txt")
        print("   - my2.txt")
        
        # 检查文件是否存在
        if os.path.exists("my1.txt") and os.path.exists("my2.txt"):
            # 显示文件大小
            size1 = os.path.getsize("my1.txt")
            size2 = os.path.getsize("my2.txt")
            print(f"\n文件大小:")
            print(f"  my1.txt: {size1:,} 字节")
            print(f"  my2.txt: {size2:,} 字节")
        else:
            print("警告: 某些输出文件不存在")
            
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
