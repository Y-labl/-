"""检查 pyc/marshal 文件头"""
import os, struct

BASE = r"D:\Program Files\mhxy\stoneclient\extracted\modules"

files = [
    "login.pyc", "login.marshal",
    "findstone_thread.pyc", "findstone_thread.marshal",
]

for fname in files:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"{fname}: 不存在")
        continue
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        h = f.read(16)
    print(f"{fname}: size={size}, header={h.hex()} {' '.join(chr(b) if 32<=b<127 else '.' for b in h)}")
