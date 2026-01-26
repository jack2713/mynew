import requests
import os
import re
from collections import defaultdict

def fetch_m3u_channels_and_save(urls, output_file_path):
    """最简单直接的版本"""
    all_channels = defaultdict(list)
    
    for source_url in urls:  # 改名为source_url避免冲突
        try:
            print(f"正在获取: {source_url}")
            response = requests.get(source_url, timeout=10)
            response.encoding = 'utf-8'
            content = response.text
            
            lines = content.splitlines()
            
            for i in range(len(lines)):
                line = lines[i].strip()
                if line.startswith('#EXTINF'):
                    # 获取分组
                    group_match = re.search(r'group-title="([^"]*)"', line)
                    group = group_match.group(1) if group_match else "未分组"
                    
                    # 获取名称
                    name_match = re.search(r'tvg-name="([^"]*)"', line)
                    if name_match:
                        name = name_match.group(1)
                    else:
                        name = line.split(',')[-1].split(' - ')[0].strip()
                    
                    # 获取URL（注意：这里的url变量名与循环变量冲突了）
                    if i + 1 < len(lines) and lines[i+1].startswith(('http://', 'https://')):
                        channel_url = lines[i+1].strip()  # 改名为channel_url
                        if name and channel_url:
                            all_channels[group].append((name, channel_url))
                            
        except Exception as e:
            print(f"处理 {source_url} 时出错: {e}")
    
    # 保存到文件
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建目录: {output_dir}")
    
    # 统计总频道数
    total_channels = sum(len(channels) for channels in all_channels.values())
    print(f"总共获取到 {len(all_channels)} 个分组，{total_channels} 个频道")
    
    with open(output_file_path, "w", encoding="utf-8") as f:
        for group, channels in all_channels.items():
            if group and channels:
                f.write(f"{group},#genre#\n")
                for name, url in channels:
                    f.write(f"{name},{url}\n")
                f.write("\n")  # 添加空行分隔不同分组
    
    print(f"完成！保存到: {output_file_path}")
    
    # 验证文件是否成功写入
    if os.path.exists(output_file_path):
        file_size = os.path.getsize(output_file_path)
        print(f"文件大小: {file_size} 字节")
        
        # 读取前几行显示
        with open(output_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"文件行数: {len(lines)}")
            if lines:
                print("文件前5行内容:")
                for i in range(min(5, len(lines))):
                    print(f"  {i+1}: {lines[i].strip()}")
    else:
        print(f"错误: 文件 {output_file_path} 未成功创建")

if __name__ == "__main__":
    urls = [
        'https://live.hacks.tools/iptv/categories/movies.m3u',
    ]
    
    output_file_path = "TMP/temp.txt"
    print(f"脚本开始执行，输出文件路径: {output_file_path}")
    print(f"当前工作目录: {os.getcwd()}")
    
    fetch_m3u_channels_and_save(urls, output_file_path)
    
    # 最后确认文件是否存在
    if os.path.exists(output_file_path):
        print(f"✓ 文件已成功创建: {output_file_path}")
    else:
        print(f"✗ 文件创建失败: {output_file_path}")
