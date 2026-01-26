import requests
import os
from pathlib import Path

def download_m3u_file():
    """模拟Postman下载M3U文件"""
    url = "https://live.hacks.tools/iptv/categories/movies.m3u"
    tmp_dir = "TMP"
    file_path = os.path.join(tmp_dir, "temp.txt")
    
    # 创建TMP目录（如果不存在）
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    
    print("模拟Postman下载M3U文件...")
    print(f"目标URL: {url}")
    print(f"保存到: {file_path}")
    
    try:
        # 模拟Postman：不设置User-Agent，使用requests默认headers
        response = requests.get(url, timeout=30)
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应头信息:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        if response.status_code == 200:
            # 保存原始M3U文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(file_path)
            print(f"\n✓ 文件下载成功")
            print(f"  文件大小: {file_size} 字节")
            print(f"  保存位置: {file_path}")
            
            # 解析M3U文件内容
            parse_m3u_file(file_path)
        else:
            print(f"× 下载失败，状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("× 请求超时，请检查网络连接")
    except requests.exceptions.RequestException as e:
        print(f"× 请求失败: {e}")
    except Exception as e:
        print(f"× 发生未知错误: {e}")

def parse_m3u_file(file_path):
    """解析M3U文件内容"""
    print("\n" + "="*50)
    print("解析M3U文件内容...")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        print(f"文件总行数: {len(lines)}")
        
        # 检查M3U文件格式
        if not lines or not lines[0].startswith('#EXTM3U'):
            print("⚠ 警告：文件可能不是标准的M3U格式")
        
        # 统计信息
        extinf_count = 0
        url_count = 0
        channels = []
        
        print("\n频道列表:")
        print("-" * 80)
        
        for i, line in enumerate(lines[:100], 1):  # 只显示前100行避免过多输出
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#EXTINF'):
                extinf_count += 1
                # 解析频道信息
                parts = line.split(',', 1)
                if len(parts) > 1:
                    channel_name = parts[1].strip()
                    channels.append(channel_name)
                    print(f"[频道 {extinf_count}] {channel_name}")
            elif line.startswith('http://') or line.startswith('https://'):
                url_count += 1
                # 显示简化的URL（避免过长）
                if len(line) > 60:
                    print(f"  URL: {line[:60]}...")
                else:
                    print(f"  URL: {line}")
            elif line.startswith('#EXTM3U'):
                print(f"✓ M3U文件头: {line}")
            elif line.startswith('#'):
                # 其他扩展信息
                if len(line) > 60:
                    print(f"  扩展信息: {line[:60]}...")
                else:
                    print(f"  扩展信息: {line}")
            elif line:
                print(f"  数据行: {line[:60]}..." if len(line) > 60 else f"  数据行: {line}")
        
        # 显示统计信息
        print("\n" + "="*50)
        print("统计信息:")
        print(f"  M3U文件头: {'找到' if lines and lines[0].startswith('#EXTM3U') else '未找到'}")
        print(f"  #EXTINF标签数量: {extinf_count}")
        print(f"  URL数量: {url_count}")
        print(f"  解析的频道数量: {len(channels)}")
        
        # 显示前10个频道名称
        if channels:
            print(f"\n前10个频道名称:")
            for i, channel in enumerate(channels[:10], 1):
                print(f"  {i}. {channel}")
            
            if len(channels) > 10:
                print(f"  ... 还有 {len(channels) - 10} 个频道")
        
        # 保存解析结果到另一个文件
        if channels:
            summary_path = os.path.join(os.path.dirname(file_path), "channels_summary.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"M3U文件解析报告\n")
                f.write(f"文件: {file_path}\n")
                f.write(f"总频道数: {len(channels)}\n")
                f.write(f"总URL数: {url_count}\n")
                f.write(f"总行数: {len(lines)}\n\n")
                f.write("频道列表:\n")
                for i, channel in enumerate(channels, 1):
                    f.write(f"{i}. {channel}\n")
            
            print(f"\n✓ 解析报告已保存到: {summary_path}")
        
        # 如果行数超过100，显示提示
        if len(lines) > 100:
            print(f"\n注意：只显示了前100行，完整内容查看文件: {file_path}")
        
    except UnicodeDecodeError:
        print("× 文件编码错误，尝试其他编码...")
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            print("✓ 使用GBK编码成功读取")
            print(f"文件大小: {len(content)} 字符")
        except:
            print("× 无法读取文件，可能不是文本文件")
    except Exception as e:
        print(f"× 解析文件时出错: {e}")

def main():
    """主函数"""
    print("="*60)
    print("M3U文件下载与解析工具")
    print("模拟Postman GET请求行为")
    print("="*60)
    
    download_m3u_file()
    
    print("\n" + "="*60)
    print("操作完成")

if __name__ == "__main__":
    main()
