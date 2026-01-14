#!/usr/bin/env python3
# process_iptv.py - 处理IPTV源文件并分类去重
import requests
import time
import os
import hashlib
from typing import List, Dict, Set, Tuple
from datetime import datetime
from collections import defaultdict


class IPTVProcessor:
    def __init__(self):
        # 定义1：需要写入文件1的类别
        self.categories_file1 = {
            "电影", "新闻", "体育", "台湾", "中国", 
            "香港", "韩国", "印度", "日本", "越南", 
            "泰国", "新加坡", "英国", "马来西亚", 
            "儿童", "纪录"
        }
        
        # 定义2：需要写入文件2的类别
        self.categories_file2 = {
            "【1】", "【2】", "【3】", "【4】", "【5】", 
            "【6】", "【7】", "【8】", "【9】", "【10】", 
            "【11】", "【12】", "【13】", "【14】", "【15】", "【16】"
        }
        
        # 源URL列表
        self.source_urls = [
            "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/斯瑪特直播源1",
            "https://raw.githubusercontent.com/FGBLH/FG/refs/heads/main/%E6%B5%B7%E8%A7%92%E7%A4%BE%E5%8C%BA%E5%8D%9A%E4%B8%BB(%E5%85%8D%E7%95%AA%E5%BC%BA)"
        ]
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/plain',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # 存储处理结果
        self.file1_content = []  # 存储分类后的分组
        self.file2_content = []
        
        # 去重相关
        self.url_signatures = set()  # 存储URL的签名用于去重
        self.channel_cache = {      # 缓存每个文件中的频道
            'file1': defaultdict(set),  # category -> set(channel_lines)
            'file2': defaultdict(set)
        }
        
        # 统计信息
        self.stats = {
            'total_urls': 0,
            'success_urls': 0,
            'duplicate_channels': 0,
            'unique_channels': 0,
            'file1_categories': set(),
            'file2_categories': set()
        }
    
    def fetch_content(self, url: str) -> Tuple[str, bool]:
        """从URL获取内容，返回内容和是否成功"""
        try:
            print(f"📡 正在获取: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # 计算内容签名用于去重
            content_hash = hashlib.md5(response.content).hexdigest()
            if content_hash in self.url_signatures:
                print(f"⚠️  检测到重复内容，跳过: {url}")
                return "", False
                
            self.url_signatures.add(content_hash)
            self.stats['success_urls'] += 1
            return response.text, True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取失败 {url}: {e}")
            return "", False
        except Exception as e:
            print(f"❌ 处理URL时出错 {url}: {e}")
            return "", False
    
    def extract_channel_info(self, line: str) -> Tuple[str, str, str]:
        """从频道行提取信息，返回(频道名, URL, 签名)"""
        parts = line.split(',')
        if len(parts) >= 2:
            channel_name = parts[0].strip()
            channel_url = parts[1].strip()
            # 创建频道签名（使用名称和URL的hash）
            signature = hashlib.md5(f"{channel_name}:{channel_url}".encode()).hexdigest()
            return channel_name, channel_url, signature
        return "", "", ""
    
    def is_duplicate_channel(self, category: str, channel_line: str, file_type: str) -> bool:
        """检查频道是否重复"""
        _, _, signature = self.extract_channel_info(channel_line)
        if signature:
            if signature in self.channel_cache[file_type][category]:
                return True
            self.channel_cache[file_type][category].add(signature)
        return False
    
    def process_content(self, content: str):
        """处理内容并分类去重"""
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
                    self.classify_and_deduplicate(current_category, current_group)
                
                # 开始新分组
                current_category = line.split(',')[0]
                current_group = [line]
            else:
                # 添加频道行到当前分组
                if current_group is not None:
                    current_group.append(line)
        
        # 处理最后一个分组
        if current_group and current_category:
            self.classify_and_deduplicate(current_category, current_group)
    
    def classify_and_deduplicate(self, category: str, lines: List[str]):
        """分类并去重分组"""
        if len(lines) <= 1:  # 只有标题没有频道
            return
        
        # 检查类别属于哪个文件
        target_file = None
        for cat1 in self.categories_file1:
            if cat1 in category:
                target_file = 'file1'
                self.stats['file1_categories'].add(category)
                break
        
        if not target_file:
            for cat2 in self.categories_file2:
                if cat2 in category:
                    target_file = 'file2'
                    self.stats['file2_categories'].add(category)
                    break
        
        if not target_file:
            return  # 不匹配任何类别，跳过
        
        # 去重处理
        unique_lines = [lines[0]]  # 标题行
        seen_channels = set()
        
        for channel_line in lines[1:]:
            if not self.is_duplicate_channel(category, channel_line, target_file):
                unique_lines.append(channel_line)
                self.stats['unique_channels'] += 1
            else:
                self.stats['duplicate_channels'] += 1
        
        # 如果有实际频道内容，添加到对应文件
        if len(unique_lines) > 1:
            if target_file == 'file1':
                self.file1_content.append({
                    "category": category,
                    "lines": unique_lines
                })
            else:
                self.file2_content.append({
                    "category": category,
                    "lines": unique_lines
                })
    
    def write_files(self):
        """写入文件"""
        # 写入my1.txt
        self._write_single_file("my1.txt", self.file1_content, "文件1")
        
        # 写入my2.txt
        self._write_single_file("my2.txt", self.file2_content, "文件2")
    
    def _write_single_file(self, filename: str, content_list: List[Dict], file_desc: str):
        """写入单个文件"""
        total_channels = sum(len(item["lines"]) - 1 for item in content_list)
        
        with open(filename, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write(f"# IPTV源文件 - {file_desc}\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 源URL: {', '.join(self.source_urls)}\n")
            f.write(f"# 分组数量: {len(content_list)}\n")
            f.write(f"# 频道数量: {total_channels}\n")
            f.write(f"# 过滤重复频道: {self.stats['duplicate_channels']}\n")
            f.write("# " + "="*60 + "\n\n")
            
            # 写入内容
            for item in content_list:
                for line in item["lines"]:
                    f.write(line + "\n")
                f.write("\n")  # 分组之间空一行
        
        # 输出结果
        if total_channels > 0:
            print(f"✅ {filename}: {len(content_list)}个分组, {total_channels}个唯一频道")
        else:
            print(f"⚠️  {filename}: 没有内容可写入")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {file_desc} - 暂无内容\n")
    
    def run(self):
        """主运行方法"""
        print("="*60)
        print("🎬 IPTV源文件处理工具 (带去重功能)")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 获取并处理所有源
        self.stats['total_urls'] = len(self.source_urls)
        
        for idx, url in enumerate(self.source_urls, 1):
            print(f"\n📋 处理源 {idx}/{len(self.source_urls)}")
            content, success = self.fetch_content(url)
            if success and content:
                self.process_content(content)
                time.sleep(0.3)  # 礼貌延迟
        
        # 写入文件
        print("\n💾 写入文件...")
        self.write_files()
        
        # 输出统计信息
        self.print_statistics()
        
        print("="*60)
        print("🎉 处理完成!")
        print("="*60)
    
    def print_statistics(self):
        """打印详细统计信息"""
        print("\n📊 详细统计信息:")
        print("-" * 60)
        
        # 总体统计
        print(f"🌐 源处理统计:")
        print(f"   总URL数量: {self.stats['total_urls']}")
        print(f"   成功获取: {self.stats['success_urls']}")
        print(f"   重复内容源: {self.stats['total_urls'] - self.stats['success_urls']}")
        
        # 频道统计
        print(f"\n📺 频道统计:")
        print(f"   唯一频道数: {self.stats['unique_channels']:,}")
        print(f"   过滤重复频道数: {self.stats['duplicate_channels']:,}")
        print(f"   总处理频道数: {self.stats['unique_channels'] + self.stats['duplicate_channels']:,}")
        
        # 文件1统计
        if self.file1_content:
            channels1 = sum(len(item["lines"]) - 1 for item in self.file1_content)
            categories1 = list(self.stats['file1_categories'])
            print(f"\n📁 my1.txt (类别匹配: {', '.join(self.categories_file1)})")
            print(f"   分组数量: {len(self.file1_content)}")
            print(f"   频道数量: {channels1}")
            print(f"   包含类别: {', '.join(sorted(categories1)[:8])}")
            if len(categories1) > 8:
                print(f"             ... 等{len(categories1)}个类别")
        else:
            print(f"\n📁 my1.txt: 无匹配内容")
        
        # 文件2统计
        if self.file2_content:
            channels2 = sum(len(item["lines"]) - 1 for item in self.file2_content)
            categories2 = list(self.stats['file2_categories'])
            print(f"\n📁 my2.txt (类别匹配: {', '.join(self.categories_file2)})")
            print(f"   分组数量: {len(self.file2_content)}")
            print(f"   频道数量: {channels2}")
            print(f"   包含类别: {', '.join(sorted(categories2)[:8])}")
            if len(categories2) > 8:
                print(f"             ... 等{len(categories2)}个类别")
        else:
            print(f"\n📁 my2.txt: 无匹配内容")


def main():
    """主函数"""
    processor = IPTVProcessor()
    
    try:
        processor.run()
        
        # 验证文件
        print("\n🔍 文件验证:")
        for filename in ["my1.txt", "my2.txt"]:
            try:
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    lines_count = 0
                    with open(filename, 'r', encoding='utf-8') as f:
                        lines_count = len(f.readlines())
                    
                    print(f"   📄 {filename}: {size:,} 字节, {lines_count} 行")
                else:
                    print(f"   ⚠️  {filename}: 文件未生成")
            except Exception as e:
                print(f"   ❌ {filename}: 验证出错 - {e}")
                
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
