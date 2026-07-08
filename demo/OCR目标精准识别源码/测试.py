import os, cv2, sys

test_path = r"D:\Program Files\mhxy-project\demo\OCR目标精准识别源码\00.bmp"

print(f"[诊断] Python检测文件存在: {os.path.exists(test_path)}")
print(f"[诊断] 文件大小: {os.path.getsize(test_path) if os.path.exists(test_path) else 'N/A'} bytes")

# 尝试用二进制模式读取（绕过OpenCV，测试纯文件系统权限）
try:
    with open(test_path, 'rb') as f:
        data = f.read(16)
    print(f"[诊断] Python二进制读取成功, 前16字节: {data[:8].hex()}")
except PermissionError:
    print("[ERROR] ❌ 权限被拒绝！Python无法读取该文件")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] ❌ 读取异常: {e}")
    sys.exit(1)

# 最后才测试OpenCV
img = cv2.imread(test_path)
print(f"[诊断] OpenCV读取结果: {'✅ 成功' if img is not None else '❌ 失败'}")