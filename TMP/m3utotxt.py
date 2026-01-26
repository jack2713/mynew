import requests
import os
from pathlib import Path

# 设置URL和目标文件路径
url = "https://live.hacks.tools/iptv/categories/movies.m3u"
tmp_dir = "TMP"
file_path = os.path.join(tmp_dir, "temp.txt")

# 创建TMP目录（如果不存在）
Path(tmp_dir).mkdir(parents=True, exist_ok=True)

print("开始获取内容...")
print(f"目标URL: {url}")

try:
    # 发送GET请求，不使用User-Agent
    response = requests.get(url, headers={})
    response.raise_for_status()  # 检查HTTP错误
    
    print(f"HTTP状态码: {response.status_code}")
    print(f"内容长度: {len(response.content)} 字节")
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"内容已保存到: {file_path}")
    
    # 显示转换后的多行日志
    print("\n内容预览（前10行）:")
    lines = response.text.split('\n')
    for i, line in enumerate(lines[:10]):
        print(f"行 {i+1}: {line}")
    
    print(f"... 总共 {len(lines)} 行")
    
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except IOError as e:
    print(f"文件操作失败: {e}")
except Exception as e:
    print(f"发生未知错误: {e}")
