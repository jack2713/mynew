import os
import re
import sys

def convert_and_overwrite():
    """
    直接将M3U格式转换为txt格式并覆盖原文件
    输入输出都是: TMP/temp.txt
    """
    
    input_file = "TMP/temp.txt"
    
    print(f"开始转换文件: {input_file}")
    print(f"文件路径: {os.path.abspath(input_file)}")
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 文件 {input_file} 不存在")
        print("当前目录内容:")
        os.system("ls -la")
        return False
    
    try:
        # 读取文件内容
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"原始文件大小: {len(content)} 字符")
        
        # 如果是空文件，直接返回
        if not content.strip():
            print("文件为空，无需转换")
            return True
        
        # 判断文件格式
        if content.strip().startswith('#EXTM3U'):
            print("检测到M3U格式，转换为txt格式")
            result = m3u_to_txt(content)
        else:
            print("检测到txt格式，保持原样或优化格式")
            result = optimize_txt(content)
        
        # 写回原文件
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"转换完成！文件已更新")
        
        # 验证结果
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"新文件行数: {len(lines)}")
            
            # 统计信息
            groups = sum(1 for line in lines if line.strip().endswith(',#genre#'))
            channels = sum(1 for line in lines if line.strip().startswith('http'))
            
            print(f"分组数量: {groups}")
            print(f"频道数量: {channels}")
            
            # 显示前几行
            if lines:
                print("\n转换后文件前10行:")
                for i in range(min(10, len(lines))):
                    print(f"  {i+1}: {lines[i].rstrip()}")
        
        return True
        
    except Exception as e:
        print(f"转换过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def m3u_to_txt(content):
    """将M3U格式转换为txt格式"""
    lines = content.splitlines()
    output_lines = []
    
    current_group = "未分组"
    current_name = ""
    
    for i in range(len(lines)):
        line = lines[i].strip()
        
        if not line:
            continue
        
        if line.startswith('#EXTM3U'):
            # 文件头，跳过
            continue
            
        elif line.startswith('#EXTINF'):
            # 解析分组信息
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                current_group = group_match.group(1)
            else:
                # 尝试其他格式
                alt_match = re.search(r'group-title=([^,\s]+)', line)
                if alt_match:
                    current_group = alt_match.group(1).strip('"\'')
            
            # 解析频道名称
            name_match = re.search(r'tvg-name="([^"]*)"', line)
            if name_match:
                current_name = name_match.group(1)
            else:
                # 从最后一部分获取名称
                parts = line.split(',')
                if len(parts) > 1:
                    current_name = parts[-1].strip()
                else:
                    current_name = f"频道_{len(output_lines)+1}"
            
            # 清理名称
            current_name = re.sub(r'\[\d+\]$', '', current_name)
            current_name = current_name.split('|')[0].strip()
            
        elif line.startswith(('http://', 'https://')):
            # 这是URL行
            if current_name:
                url = line
                
                # 检查是否需要添加分组行
                if not output_lines or not output_lines[-1].endswith(',#genre#'):
                    output_lines.append(f"{current_group},#genre#")
                
                output_lines.append(f"{current_name},{url}")
                current_name = ""
    
    # 如果没有解析到任何内容，尝试备用解析方法
    if not output_lines:
        output_lines = backup_parse(lines)
    
    return '\n'.join(output_lines) + '\n'

def backup_parse(lines):
    """备用解析方法"""
    output_lines = []
    current_group = "默认分组"
    channels_found = False
    
    for i in range(len(lines)):
        line = lines[i].strip()
        
        if not line or line.startswith('#EXTM3U'):
            continue
        
        if line.startswith('#EXTINF'):
            # 尝试提取名称
            if ',' in line:
                name = line.split(',')[-1].strip()
                name = re.sub(r'\[\d+\]', '', name)
                
                # 查找下一个URL
                for j in range(i+1, min(i+3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith(('http://', 'https://')):
                        url = next_line
                        if not channels_found:
                            output_lines.append(f"{current_group},#genre#")
                            channels_found = True
                        output_lines.append(f"{name},{url}")
                        break
    
    return output_lines

def optimize_txt(content):
    """优化txt格式，确保标准格式"""
    lines = content.splitlines()
    output_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 如果已经是分组行格式，保留
        if line.endswith(',#genre#'):
            output_lines.append(line)
        # 如果是频道行，确保格式正确
        elif ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                name, url = parts
                name = name.strip()
                url = url.strip()
                
                # 如果URL在前，交换位置
                if url.startswith(('http://', 'https://')) and not name.startswith(('http://', 'https://')):
                    output_lines.append(f"{name},{url}")
                elif name.startswith(('http://', 'https://')) and not url.startswith(('http://', 'https://')):
                    output_lines.append(f"{url},{name}")
                else:
                    output_lines.append(line)
            else:
                output_lines.append(line)
        else:
            # 可能是孤立的URL，添加默认名称
            if line.startswith(('http://', 'https://')):
                output_lines.append(f"频道_{len(output_lines)+1},{line}")
            else:
                output_lines.append(line)
    
    # 如果没有分组行，添加默认分组
    if output_lines and not any(line.endswith(',#genre#') for line in output_lines):
        output_lines.insert(0, "默认分组,#genre#")
    
    return '\n'.join(output_lines) + '\n'

def main():
    """主函数"""
    print("=" * 60)
    print("M3U/TXT格式转换器")
    print("=" * 60)
    
    # 确保TMP目录存在
    if not os.path.exists("TMP"):
        print("创建TMP目录")
        os.makedirs("TMP")
    
    # 执行转换
    success = convert_and_overwrite()
    
    if success:
        print("\n✅ 转换完成！")
        print(f"文件已保存到: {os.path.abspath('TMP/temp.txt')}")
    else:
        print("\n❌ 转换失败！")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
