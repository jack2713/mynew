import requests
import os
import re
import json
from collections import defaultdict

def simple_get_and_save(urls, output_file_path):
    """最简单的GET请求，模拟Postman"""
    
    print(f"开始获取数据...")
    print(f"输出文件: {output_file_path}")
    
    all_channels = defaultdict(list)
    
    for url in urls:
        try:
            print(f"\n处理URL: {url}")
            
            # 最简单的GET请求，模拟Postman
            response = requests.get(
                url,
                timeout=30,  # 长超时
                verify=False,  # 不验证SSL
                allow_redirects=True  # 允许重定向
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应大小: {len(response.content)} 字节")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            if response.status_code == 200:
                # 尝试多种编码
                content = None
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1', 'iso-8859-1']:
                    try:
                        content = response.content.decode(encoding)
                        print(f"使用 {encoding} 解码成功")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    content = response.content.decode('utf-8', errors='ignore')
                    print("使用utf-8 (ignore errors) 解码")
                
                # 保存原始内容用于调试
                with open("TMP/raw_content.txt", "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"原始内容已保存到 TMP/raw_content.txt")
                
                # 解析内容
                parse_m3u_content(content, all_channels)
            else:
                print(f"请求失败: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                
                # 尝试显示响应内容
                try:
                    error_content = response.content.decode('utf-8', errors='ignore')
                    print(f"错误响应前100字符: {error_content[:100]}")
                except:
                    pass
                
        except requests.exceptions.Timeout:
            print(f"请求超时")
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
        except Exception as e:
            print(f"其他错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 保存结果
    save_channels(all_channels, output_file_path)

def parse_m3u_content(content, all_channels):
    """解析M3U内容"""
    lines = content.splitlines()
    print(f"解析到 {len(lines)} 行")
    
    current_group = "未分组"
    current_name = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            continue
        
        # 显示前几行用于调试
        if i < 5:
            print(f"行 {i+1}: {line}")
        
        if line.startswith('#EXTINF'):
            # 提取分组
            group_match = re.search(r'group-title="([^"]+)"', line)
            if group_match:
                current_group = group_match.group(1)
            else:
                group_match = re.search(r'group-title=([^\s,]+)', line)
                if group_match:
                    current_group = group_match.group(1).strip('"\'')
            
            # 提取名称
            name_match = re.search(r'tvg-name="([^"]+)"', line)
            if name_match:
                current_name = name_match.group(1)
            else:
                # 从末尾获取名称
                if ',' in line:
                    current_name = line.split(',')[-1].strip()
                else:
                    current_name = f"频道_{i}"
            
            print(f"  找到频道: {current_name} (分组: {current_group})")
            
        elif line.startswith('http://') or line.startswith('https://'):
            if current_name:
                all_channels[current_group].append((current_name, line))
                print(f"  添加URL: {line[:50]}...")
                current_name = ""

def save_channels(all_channels, output_file_path):
    """保存频道数据"""
    # 创建目录
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    total_channels = sum(len(channels) for channels in all_channels.values())
    print(f"\n解析结果: {len(all_channels)} 个分组, {total_channels} 个频道")
    
    if total_channels == 0:
        print("警告: 没有解析到任何频道，创建空文件")
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write("# 没有获取到数据\n")
        return
    
    # 写入文件
    with open(output_file_path, "w", encoding="utf-8") as f:
        for group, channels in all_channels.items():
            if group and channels:
                f.write(f"{group},#genre#\n")
                for name, url in channels:
                    f.write(f"{name},{url}\n")
                f.write("\n")
    
    print(f"数据已保存到: {output_file_path}")
    
    # 验证文件
    with open(output_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    print(f"文件行数: {len(lines)}")
    print(f"文件内容预览:")
    for i in range(min(10, len(lines))):
        print(f"  {i+1}: {lines[i].strip()}")

def test_direct_get(url):
    """直接测试GET请求"""
    print(f"\n测试直接GET请求: {url}")
    
    try:
        # 最简单直接的请求
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应大小: {len(response.content)}")
        
        # 显示响应头
        print("响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # 显示响应内容前200字符
        try:
            content_preview = response.content.decode('utf-8', errors='ignore')[:200]
            print(f"内容预览: {content_preview}")
        except:
            print("无法解码内容")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"请求失败: {e}")
        return False

if __name__ == "__main__":
    # 目标URL
    urls = [
        'https://live.hacks.tools/iptv/categories/movies.m3u',
    ]
    
    output_file = "TMP/temp.txt"
    
    print("=" * 60)
    print("直接GET请求测试")
    print("=" * 60)
    
    # 创建TMP目录
    os.makedirs("TMP", exist_ok=True)
    
    # 测试直接请求
    for url in urls:
        success = test_direct_get(url)
        if not success:
            print(f"警告: {url} 直接请求失败")
    
    # 执行获取和保存
    print("\n" + "=" * 60)
    print("开始获取并保存数据")
    print("=" * 60)
    
    simple_get_and_save(urls, output_file)
    
    # 最终验证
    print("\n" + "=" * 60)
    print("最终验证")
    print("=" * 60)
    
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"✓ 文件已创建: {output_file}")
        print(f"文件大小: {len(content)} 字符")
        
        if len(content.strip()) > 0:
            lines = content.splitlines()
            print(f"文件行数: {len(lines)}")
            
            # 统计
            groups = sum(1 for line in lines if line.endswith(',#genre#'))
            channels = sum(1 for line in lines if ',' in line and not line.endswith(',#genre#'))
            
            print(f"分组数: {groups}")
            print(f"频道数: {channels}")
            
            if channels == 0:
                print("警告: 文件为空或没有解析到频道")
        else:
            print("警告: 文件内容为空")
    else:
        print(f"✗ 文件未创建: {output_file}")
