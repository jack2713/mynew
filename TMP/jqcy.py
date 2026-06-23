import requests

def fetch_and_save():
    url = "http://nas.jqcykj.com:88"
    output_file = "jqcy.txt"
    
    try:
        # 发送GET请求，设置超时
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        # 尝试自动检测编码，或使用常见编码
        if response.encoding is None:
            response.encoding = 'utf-8'
        content = response.text
        
        # 按行分割
        lines = content.splitlines()
        
        # 过滤掉包含 '#genre#' 的行（不区分大小写）
        filtered_lines = [line for line in lines if '#genre#' not in line.lower()]
        
        # 写入文件，第一行固定为 "jqcy,#genre#"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("jqcy,#genre#\n")
            for line in filtered_lines:
                f.write(line + '\n')
        
        print(f"成功保存到 {output_file}，共写入 {len(filtered_lines) + 1} 行。")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    fetch_and_save()
