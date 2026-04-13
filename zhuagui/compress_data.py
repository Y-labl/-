import shutil
import os

os.chdir(r'D:\Program Files\mhxy\zhuagui\dataset')

print("📦 正在压缩 annotation_100 为 ZIP 格式...")
shutil.make_archive('annotation_100', 'zip', '.', 'annotation_100')

print("✅ 压缩完成！")
print("📄 文件位置：annotation_100.zip")
print(f"📊 文件大小：{os.path.getsize('annotation_100.zip') / 1024 / 1024:.2f} MB")
