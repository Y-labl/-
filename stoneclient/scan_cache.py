"""扫描 __pycache__ 中的 .pyc 文件"""
import marshal
import os

CACHE = r"D:\Program Files\mhxy\stoneclient\extracted\source_v2\__pycache__"
TARGETS = ["color_util", "index", "login", "robot_thread"]

for fname in sorted(os.listdir(CACHE)):
    if not fname.endswith('.pyc'):
        continue
    match = any(fname.startswith(t) for t in TARGETS)
    if not match:
        continue

    path = os.path.join(CACHE, fname)
    with open(path, 'rb') as f:
        data = f.read()

    print(f"\n{fname}: {len(data)} bytes")
    print(f"  前 20 字节: {data[:20].hex()}")

    # 尝试标准 .pyc 格式 (offset 16)
    found = False
    for offset in range(0, min(64, len(data))):
        try:
            code = marshal.loads(data[offset:])
            if hasattr(code, 'co_name'):
                funcs = [c.co_name for c in code.co_consts if hasattr(c, 'co_name')]
                print(f"  -> 偏移 {offset}: OK! co_name={code.co_name}")
                print(f"     函数: {funcs}")
                found = True
                break
        except Exception:
            pass

    if not found:
        print(f"  -> 所有偏移均失败，可能也是加密的")
