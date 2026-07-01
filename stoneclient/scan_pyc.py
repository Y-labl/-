"""扫描 .pyc 文件找到 marshal code 对象的正确偏移"""
import marshal
import os

BASE = r"D:\Program Files\mhxy\stoneclient\extracted\modules"

# 测试 files
files = {
    "login.pyc": os.path.join(BASE, "login.pyc"),
    "findstone_thread.pyc": os.path.join(BASE, "findstone_thread.pyc"),
}

for name, path in files.items():
    print(f"\n{'='*60}")
    print(f"文件: {name}")
    with open(path, 'rb') as f:
        data = f.read()
    print(f"大小: {len(data)} bytes")

    # 显示前 32 字节
    print(f"前 32 字节 hex: {data[:32].hex()}")

    # 尝试从不同偏移 marshal.loads
    for offset in range(0, min(64, len(data))):
        try:
            code = marshal.loads(data[offset:])
            if hasattr(code, 'co_name'):
                print(f"  -> 偏移 {offset}: 成功! co_name={code.co_name}, "
                      f"consts={len(code.co_consts)} items")
                # 列出函数
                funcs = [c.co_name for c in code.co_consts if hasattr(c, 'co_name')]
                if funcs:
                    print(f"     内嵌函数: {funcs}")
        except Exception:
            pass

    # 也尝试找 'c' (TYPE_CODE) 字节
    for i, b in enumerate(data[:64]):
        if b == 0x63:  # 'c' = TYPE_CODE
            try:
                code = marshal.loads(data[i:])
                if hasattr(code, 'co_name'):
                    print(f"  -> 从 0x63 偏移 {i}: co_name={code.co_name}")
            except Exception:
                pass
