import requests
import os
import re
import time
import json
from collections import defaultdict
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_with_cf_bypass(url):
    """绕过CloudFlare防护的GET请求"""
    
    # 完整的浏览器请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }
    
    # 使用session保持会话
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print(f"发送请求到: {url}")
        
        # 第一次请求，可能会被重定向到挑战页面
        response = session.get(url, timeout=30, verify=False, allow_redirects=True)
        
        print(f"第一次响应状态码: {response.status_code}")
        print(f"第一次响应大小: {len(response.content)} 字节")
        
        # 检查是否是CloudFlare挑战页面
        content = response.content.decode('utf-8', errors='ignore')
        
        if 'Just a moment' in content or 'CloudFlare' in content or 'cf-chl-bypass' in content:
            print("检测到CloudFlare挑战页面")
            
            # 保存挑战页面用于分析
            with open("TMP/cf_challenge.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("挑战页面已保存到 TMP/cf_challenge.html")
            
            # 尝试解析挑战页面
            return handle_cf_challenge(session, url, content)
        
        # 如果不是挑战页面，直接返回响应
        return response
        
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def handle_cf_challenge(session, url, challenge_content):
    """处理CloudFlare挑战"""
    
    print("尝试处理CloudFlare挑战...")
    
    # 方法1: 尝试使用 cloudscraper 库（如果安装）
    try:
        import cloudscraper
        print("使用 cloudscraper 绕过CloudFlare...")
        
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=30)
        
        print(f"cloudscraper 响应状态码: {response.status_code}")
        print(f"cloudscraper 响应大小: {len(response.content)} 字节")
        
        return response
    except ImportError:
        print("cloudscraper 未安装，尝试其他方法...")
    except Exception as e:
        print(f"cloudscraper 失败: {e}")
    
    # 方法2: 尝试使用 requests-html（如果需要JavaScript渲染）
    try:
        from requests_html import HTMLSession
        print("使用 requests-html 渲染页面...")
        
        html_session = HTMLSession()
        response = html_session.get(url, timeout=30)
        
        # 如果需要执行JavaScript
        response.html.render(timeout=30)
        
        print(f"requests-html 响应状态码: {response.status_code}")
        return response
    except ImportError:
        print("requests-html 未安装，尝试更简单的绕过方法...")
    except Exception as e:
        print(f"requests-html 失败: {e}")
    
    # 方法3: 简单的等待并重试
    print("等待5秒后重试...")
    time.sleep(5)
    
    try:
        # 更新请求头
        session.headers.update({
            'Referer': url,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        
        response = session.get(url, timeout=30, verify=False)
        
        print(f"重试响应状态码: {response.status_code}")
        print(f"重试响应大小: {len(response.content)} 字节")
        
        return response
    except Exception as e:
        print(f"重试失败: {e}")
        return None

def fetch_m3u_data(urls, output_file):
    """获取M3U数据并保存"""
    
    print(f"开始获取M3U数据...")
    print(f"输出文件: {output_file}")
    
    all_channels = defaultdict(list)
    
    for url in urls:
        print(f"\n{'='*60}")
        print(f"处理URL: {url}")
        print(f"{'='*60}")
        
        response = get_with_cf_bypass(url)
        
        if response and response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            
            # 检查是否是M3U格式
            if not content.strip().startswith('#EXTM3U'):
                print("警告: 响应内容不是M3U格式")
                
                # 保存响应内容用于调试
                with open("TMP/response_content.txt", "w", encoding="utf-8") as f:
                    f.write(content[:5000])  # 保存前5000字符
                print("响应内容已保存到 TMP/response_content.txt")
                
                # 检查是否是HTML页面
                if '<html' in content.lower() or '<!doctype' in content.lower():
                    print("响应是HTML页面，尝试查找M3U链接...")
                    
                    # 在HTML中查找M3U链接
                    m3u_links = re.findall(r'href="([^"]+\.m3u[^"]*)"', content)
                    m3u_links += re.findall(r"href='([^']+\.m3u[^']*)'", content)
                    
                    print(f"找到 {len(m3u_links)} 个可能的M3U链接")
                    
                    for m3u_link in m3u_links:
                        if not m3u_link.startswith('http'):
                            # 构建完整URL
                            if url.endswith('/'):
                                m3u_link = url + m3u_link.lstrip('/')
                            else:
                                base_url = '/'.join(url.split('/')[:-1])
                                m3u_link = base_url + '/' + m3u_link.lstrip('/')
                        
                        print(f"尝试获取M3U链接: {m3u_link}")
                        
                        try:
                            m3u_response = requests.get(m3u_link, timeout=15, verify=False)
                            if m3u_response.status_code == 200:
                                m3u_content = m3u_response.content.decode('utf-8', errors='ignore')
                                if m3u_content.strip().startswith('#EXTM3U'):
                                    print(f"✓ 成功获取M3U内容")
                                    content = m3u_content
                                    break
                        except Exception as e:
                            print(f"获取M3U链接失败: {e}")
            
            # 解析M3U内容
            parse_and_save_m3u(content, all_channels)
        else:
            print(f"获取失败: {response.status_code if response else '无响应'}")
    
    # 保存结果
    save_channels(all_channels, output_file)

def parse_and_save_m3u(content, all_channels):
    """解析M3U内容并添加到字典"""
    
    lines = content.splitlines()
    print(f"解析到 {len(lines)} 行")
    
    if len(lines) < 2:
        print("内容太少，可能是空文件或格式错误")
        return
    
    current_group = "未分组"
    current_name = ""
    channel_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            continue
        
        # 显示前几行用于调试
        if i < 3:
            print(f"行 {i+1}: {line[:100]}...")
        
        if line.startswith('#EXTM3U'):
            print("找到M3U文件头")
            continue
            
        elif line.startswith('#EXTINF'):
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
                    # 清理名称
                    current_name = re.sub(r'\[\d+\]$', '', current_name)
                    current_name = current_name.split('|')[0].strip()
                else:
                    current_name = f"频道_{channel_count + 1}"
            
        elif line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            if current_name:
                all_channels[current_group].append((current_name, line))
                channel_count += 1
                current_name = ""
    
    print(f"从该URL解析到 {channel_count} 个频道")

def save_channels(all_channels, output_file):
    """保存频道数据到文件"""
    
    # 创建目录
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    total_channels = sum(len(channels) for channels in all_channels.values())
    print(f"\n{'='*60}")
    print(f"解析结果: {len(all_channels)} 个分组, {total_channels} 个频道")
    print(f"{'='*60}")
    
    if total_channels == 0:
        print("警告: 没有解析到任何频道")
        
        # 创建示例数据
        create_sample_data(output_file)
        return
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        # 按分组大小排序
        sorted_groups = sorted(all_channels.items(), key=lambda x: len(x[1]), reverse=True)
        
        for group, channels in sorted_groups:
            if group and channels:
                f.write(f"{group},#genre#\n")
                # 按名称排序
                for name, url in sorted(channels, key=lambda x: x[0]):
                    f.write(f"{name},{url}\n")
                f.write("\n")
    
    print(f"✓ 数据已保存到: {output_file}")
    
    # 显示文件信息
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    print(f"文件行数: {len(lines)}")
    print(f"文件内容预览:")
    
    preview_lines = 0
    for i, line in enumerate(lines):
        if line.strip():
            print(f"  {i+1}: {line.strip()}")
            preview_lines += 1
            if preview_lines >= 10:
                break

def create_sample_data(output_file):
    """创建示例数据（当无法获取真实数据时）"""
    
    print("创建示例数据...")
    
    sample_content = """电影,#genre#
测试电影频道1,http://example.com/movie1.m3u8
测试电影频道2,http://example.com/movie2.m3u8
测试电影频道3,http://example.com/movie3.m3u8

电视剧,#genre#
测试电视剧频道1,http://example.com/tv1.m3u8
测试电视剧频道2,http://example.com/tv2.m3u8

体育,#genre#
测试体育频道1,http://example.com/sports1.m3u8
"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sample_content)
    
    print(f"示例数据已保存到: {output_file}")

def install_dependencies():
    """安装必要的依赖"""
    
    print("检查依赖...")
    
    # 尝试安装 cloudscraper
    try:
        import cloudscraper
        print("✓ cloudscraper 已安装")
    except ImportError:
        print("安装 cloudscraper...")
        os.system("pip install cloudscraper")
    
    # 确保 requests 已安装
    try:
        import requests
        print("✓ requests 已安装")
    except ImportError:
        print("安装 requests...")
        os.system("pip install requests")

if __name__ == "__main__":
    print("=" * 70)
    print("M3U数据获取工具 - 绕过CloudFlare版本")
    print("=" * 70)
    
    # 确保TMP目录存在
    os.makedirs("TMP", exist_ok=True)
    
    # 安装依赖（可选）
    install_dependencies()
    
    # 目标URL
    urls = [
        'https://live.hacks.tools/iptv/categories/movies.m3u',
    ]
    
    output_file = "TMP/temp.txt"
    
    # 执行获取
    fetch_m3u_data(urls, output_file)
    
    # 最终验证
    print(f"\n{'='*70}")
    print("最终验证")
    print(f"{'='*70}")
    
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        print(f"✓ 文件已创建: {output_file}")
        print(f"文件大小: {file_size} 字节")
        print(f"文件行数: {len(lines)}")
        
        if len(lines) > 0:
            groups = sum(1 for line in lines if line.strip().endswith(',#genre#'))
            channels = sum(1 for line in lines if ',' in line and not line.strip().endswith(',#genre#'))
            
            print(f"分组数: {groups}")
            print(f"频道数: {channels}")
            
            if channels == 0:
                print("⚠ 警告: 文件中没有频道数据")
        else:
            print("⚠ 警告: 文件为空")
    else:
        print(f"✗ 文件未创建: {output_file}")
