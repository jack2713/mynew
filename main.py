#!/usr/bin/env python3
# process_iptv.py - 处理IPTV源文件并分类
import requests
import time
import os
from typing import List, Dict, Set
from datetime import datetime

class IPTVProcessor:
    def __init__(self):
        # 定义1：需要写入文件1的类别
        self.categories_file1 = {"电影", "新闻", "体育", "台湾", "中国", "香港", "韩国", "印度","日本","越南","泰国","新加坡","英国","马来西亚","儿童","记录"}
        
        # 定义2：需要写入文件2的类别
        self.categories_file2 = {"【1】", "【2】", "【3】", "【4】", "【5】", "【6】", "【7】", "【8】","【9】","【10】","【11】","【12】","【3】","【14】","【15】","【16】",}
        
        # 源URL列表
        self.source_urls = [
            "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/斯瑪特直播源1",
            "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/%E6%B5%B7%E8%A7%92%E7%A4%BE%E5%8C%BA%E5%8D%9A%E4%B8%BB(%E5%85%8D%E7%95%AA%E5%BC%BA)"
        ]
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/plain'
        }
        
        # 存储处理结果
        self.file1_content = []
        self.file2_content = []
        
    def fetch_content(self, url: str) -> str:
        """从URL获取内容"""
        try:
            print(f"正在获取: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"获取失败 {url}: {e}")
            return ""
    
    def process_content(self, content: str):
        """处理内容并分类"""
        if not content:
            return
            
        current_group = []
        current_category = ""
        
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是分组标题行
            if line.endswith(",#genre#"):
                # 保存上一个分组
                if current_group and current_category:
                    self.classify_group(current_category, current_group)
                
                # 开始新分组
                current_category = line.split(',')[0]
                current_group = [line]
            else:
                # 添加频道行到当前分组
                if current_group is not None:
                    current_group.append(line)
        
        # 处理最后一个分组
        if current_group and current_category:
            self.classify_group(current_category, current_group)
    
    def classify_group(self, category: str, lines: List[str]):
        """分类分组到对应的文件"""
        # 检查是否属于文件1的类别
        for cat1 in self.categories_file1:
            if cat1 in category:
                self.file1_content.append({"category": category, "lines": lines})
                return
        
        # 检查是否属于文件2的类别
        for cat2 in self.categories_file2:
            if cat2 in category:
                self.file2_content.append({"category": category, "lines": lines})
                return
        
        # 如果不匹配任何类别，可以根据需要添加到其他文件或忽略
    
    def write_files(self):
        """写入文件"""
        # 写入my1.txt
        self._write_single_file("my1.txt", self.file1_content)
        
        # 写入my2.txt
        self._write_single_file("my2.txt", self.file2_content)
    
    def _write_single_file(self, filename: str, content_list: List[Dict]):
        """写入单个文件"""
        if not content_list:
            print(f"⚠ {filename}: 没有内容可写入")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# 此文件暂无内容\n")
            return
            
        with open(filename, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write(f"# IPTV源文件 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 源URL: {', '.join(self.source_urls)}\n")
            f.write("# " + "="*50 + "\n\n")
            
            # 写入内容
            for item in content_list:
                for line in item["lines"]:
                    f.write(line + "\n")
                f.write("\n")  # 分组之间空一行
        
        # 统计信息
        total_channels = sum(len(item["lines"]) - 1 for item in content_list)
        print(f"✅ {filename}: {len(content_list)}个分组, {total_channels}个频道")
    
    def run(self):
        """主运行方法"""
        print("="*60)
        print("IPTV源文件处理工具")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 获取并处理所有源
        for url in self.source_urls:
            content = self.fetch_content(url)
            if content:
                self.process_content(content)
                time.sleep(0.5)  # 礼貌延迟
        
        # 写入文件
        self.write_files()
        
        # 输出统计信息
        self.print_statistics()
        
        print("="*60)
        print("处理完成!")
        print("="*60)
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n📊 统计信息:")
        print("-" * 40)
        
        # 文件1统计
        if self.file1_content:
            channels1 = sum(len(item["lines"]) - 1 for item in self.file1_content)
            categories1 = [item["category"] for item in self.file1_content]
            print(f"📁 my1.txt:")
            print(f"   分组数量: {len(self.file1_content)}")
            print(f"   频道数量: {channels1}")
            print(f"   包含类别: {', '.join(categories1[:5])}{'...' if len(categories1) > 5 else ''}")
        else:
            print("📁 my1.txt: 无内容")
        
        # 文件2统计
        if self.file2_content:
            channels2 = sum(len(item["lines"]) - 1 for item in self.file2_content)
            categories2 = [item["category"] for item in self.file2_content]
            print(f"\n📁 my2.txt:")
            print(f"   分组数量: {len(self.file2_content)}")
            print(f"   频道数量: {channels2}")
            print(f"   包含类别: {', '.join(categories2[:5])}{'...' if len(categories2) > 5 else ''}")
        else:
            print("\n📁 my2.txt: 无内容")


def main():
    """主函数"""
    processor = IPTVProcessor()
    
    try:
        processor.run()
        
        # 验证文件是否存在
        for filename in ["my1.txt", "my2.txt"]:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"\n📄 {filename}: {size:,} 字节")
            else:
                print(f"\n⚠ {filename}: 文件未生成")
                
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
