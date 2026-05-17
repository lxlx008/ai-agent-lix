import os
import re

static_dir = r"e:\devsoftware\code\ai_agent\app\static\_next\static\chunks"
backend_url = "https://web-production-2ad77.up.railway.app"

# 查找包含 localhost 的文件
files_to_fix = []
for filename in os.listdir(static_dir):
    if filename.endswith('.js'):
        filepath = os.path.join(static_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'localhost:8001' in content:
                files_to_fix.append(filepath)
                print(f"Found: {filename}")
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# 安全替换 - 用实际后端 URL
for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 http://localhost:8001 为实际 URL
    new_content = content.replace('http://localhost:8001', backend_url)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Fixed: {os.path.basename(filepath)}")

print("\nDone! Replaced with:", backend_url)