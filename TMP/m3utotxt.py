import requests
import os
import time
from pathlib import Path

# 设置URL和目标文件路径
url = "https://live.hacks.tools/iptv/categories/movies.m3u"
tmp_dir = "TMP"
file_path = os.path.join(tmp_dir, "temp.txt")

# 创建TMP目录（如果不存在）
Path(tmp_dir).mkdir(parents=True, exist_ok=True)

print("开始获取内容...")
print(f"目标URL: {url}")

# 尝试不同的方法
methods = [
    # 方法1: 完全不设置headers
    {"headers": {}},
    
    # 方法2: 模拟浏览器的headers
    {"headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }},
    
    # 方法3: 使用更简单的headers
    {"headers": {
        "Accept": "*/*",
    }},
]

success = False

for i, method_config in enumerate(methods, 1):
    print(f"\n尝试方法 {i}...")
    headers = method_config.get("headers", {})
    
    try:
        # 发送GET请求
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✓ 内容已保存到: {file_path}")
            
            # 显示转换后的多行日志
            print("\n内容预览（前10行）:")
            lines = response.text.split('\n')
            for j, line in enumerate(lines[:10]):
                print(f"行 {j+1}: {line}")
            
            print(f"... 总共 {len(lines)} 行")
            success = True
            break
        else:
            print(f"× 方法 {i} 失败，状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"× 方法 {i} 请求失败: {e}")
    
    # 在尝试之间添加延迟
    if i < len(methods):
        time.sleep(1)

if not success:
    print("\n所有方法都失败了。尝试使用requests的默认headers...")
    try:
        # 让requests使用其默认headers
        response = requests.get(url, timeout=10)
        print(f"使用默认headers的状态码: {response.status_code}")
        
        if response.status_code == 200:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"✓ 使用默认headers成功保存文件")
        else:
            print(f"× 仍然失败，状态码: {response.status_code}")
            print("服务器可能完全阻止了直接访问。")
            print("可能需要：")
            print("1. 使用代理服务器")
            print("2. 检查是否需要cookies或session")
            print("3. 联系网站管理员获取访问权限")
    except Exception as e:
        print(f"最终尝试失败: {e}")

print("\n操作完成。")
