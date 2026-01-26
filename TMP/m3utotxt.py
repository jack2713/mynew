name: synczb

on:
  schedule:
    - cron: '0 */4 * * *'  # 每4小时运行一次
  workflow_dispatch:
    inputs:
      urls:
        description: '要处理的M3U URL（用逗号分隔）'
        required: false
        default: 'https://live.hacks.tools/iptv/categories/movies.m3u'

permissions:
  contents: write

jobs:
  fetch_streams:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # 获取完整历史记录
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests urllib3
    
    - name: Create directories
      run: |
        mkdir -p TMP
        mkdir -p logs
    
    - name: Run main script
      id: run-script
      run: |
        echo "开始执行脚本..."
        python main.py
        echo "脚本执行完成"
        echo "current_time=$(date +'%Y-%m-%d %H:%M:%S')" >> $GITHUB_ENV
      env:
        PYTHONUNBUFFERED: 1  # 确保实时输出
    
    - name: Verify output
      run: |
        echo "=== 验证输出文件 ==="
        if [ -f "TMP/temp.txt" ]; then
          echo "✓ 文件存在"
          echo "文件信息:"
          ls -lh TMP/temp.txt
          echo -e "\n前10行内容:"
          head -10 TMP/temp.txt
          echo -e "\n统计信息:"
          echo "总行数: $(wc -l < TMP/temp.txt)"
          echo "分组数量: $(grep -c ',#genre#$' TMP/temp.txt || echo 0)"
          echo "频道数量: $(grep -c '^http' TMP/temp.txt || echo 0)"
        else
          echo "✗ 文件不存在!"
          echo "TMP目录内容:"
          ls -la TMP/ 2>/dev/null || echo "TMP目录不存在"
          exit 1
        fi
    
    - name: Configure Git
      run: |
        git config --global user.name "github-actions[bot]"
        git config --global user.email "github-actions[bot]@users.noreply.github.com"
    
    - name: Check for changes
      id: check-changes
      run: |
        echo "检查文件变化..."
        git add TMP/temp.txt
        if git diff --cached --quiet; then
          echo "没有变化"
          echo "has_changes=false" >> $GITHUB_ENV
        else
          echo "检测到变化"
          echo "has_changes=true" >> $GITHUB_ENV
        fi
    
    - name: Commit and push changes
      if: env.has_changes == 'true'
      run: |
        echo "提交更改..."
        git commit -m "📺 更新频道列表 - ${{ env.current_time }}"
        echo "拉取最新代码..."
        git pull --rebase origin main
        echo "推送更改..."
        git push origin main
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: iptv-channels
        path: |
          TMP/temp.txt
        retention-days: 7
    
    - name: Create summary
      if: always()
      run: |
        echo "## 执行结果" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        if [ -f "TMP/temp.txt" ]; then
          echo "✅ **成功生成文件**" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "- 文件: TMP/temp.txt" >> $GITHUB_STEP_SUMMARY
          echo "- 大小: $(stat -c%s TMP/temp.txt) 字节" >> $GITHUB_STEP_SUMMARY
          echo "- 行数: $(wc -l < TMP/temp.txt)" >> $GITHUB_STEP_SUMMARY
          echo "- 分组: $(grep -c ',#genre#$' TMP/temp.txt || echo 0)" >> $GITHUB_STEP_SUMMARY
          echo "- 频道: $(grep -c '^http' TMP/temp.txt || echo 0)" >> $GITHUB_STEP_SUMMARY
        else
          echo "❌ **文件生成失败**" >> $GITHUB_STEP_SUMMARY
        fi
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "执行时间: ${{ env.current_time }}" >> $GITHUB_STEP_SUMMARY
