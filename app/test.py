# test_oss_fixed.py
import requests
import os
import time
from datetime import datetime


def generate_unique_filename(original_ext="jpeg"):
    """生成唯一文件名"""
    timestamp = int(time.time() * 1000)
    return f"test_{timestamp}.{original_ext}"


def test_complete_upload_flow():
    """
    完整的上传流程测试
    """

    # 配置
    IMAGE_PATH = r"E:\devsoftware\code\资料\图片\food.jpeg"  # 你的测试图片
    BACKEND_URL = "http://127.0.0.1:8001/api/v1/oss/presign"  # 注意端口改为8001

    if not os.path.exists(IMAGE_PATH):
        print(f"❌ 找不到图片文件: {IMAGE_PATH}")
        return

    # 步骤1: 生成唯一的文件名
    filename = generate_unique_filename("jpeg")
    print(f"📁 使用文件名: {filename}")

    # 步骤2: 获取新的预签名URL
    print("🔄 从后端获取新的预签名URL...")
    try:
        response = requests.get(BACKEND_URL, params={"filename": filename})

        if response.status_code != 200:
            print(f"❌ 获取预签名URL失败 (状态码: {response.status_code}):")
            print(response.text)
            return

        presign_data = response.json()
        print(f"✅ 获取到预签名数据: {presign_data}")

        upload_url = presign_data["uploadUrl"]
        content_type = presign_data.get("contentType", "image/jpeg")
        access_url = presign_data.get("accessUrl")

    except Exception as e:
        print(f"❌ 获取预签名URL时出错: {e}")
        return

    # 步骤3: 准备文件数据
    print(f"📦 读取图片文件: {IMAGE_PATH}")
    try:
        with open(IMAGE_PATH, 'rb') as f:
            file_data = f.read()
        file_size = len(file_data)
        print(f"  文件大小: {file_size} 字节")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # 步骤4: 准备上传头
    headers = {
        'x-oss-content-sha256': 'UNSIGNED-PAYLOAD',  # V4签名必需
        'Content-Type': content_type,
    }

    print(f"🚀 开始上传到OSS...")
    print(f"  URL: {upload_url[:100]}...")

    # 步骤5: 执行上传
    try:
        response = requests.put(
            upload_url,
            data=file_data,
            headers=headers
        )

        print(f"📊 上传响应:")
        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            print("🎉 上传成功！")
            print(f"📷 图片访问地址: {access_url}")
        else:
            print(f"❌ 上传失败 (状态码: {response.status_code})")
            print(f"错误详情: {response.text}")

    except Exception as e:
        print(f"❌ 上传过程中出错: {e}")


if __name__ == "__main__":
    print("阿里云OSS上传测试脚本 (端口: 8001)")
    print("=" * 60)
    test_complete_upload_flow()