import sys
print("Python 路径:")
for path in sys.path:
    print(f"  {path}")

# 检查当前工作目录
import os
print(f"\n当前工作目录: {os.getcwd()}")