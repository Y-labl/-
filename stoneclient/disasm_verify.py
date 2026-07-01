"""
字节码反汇编工具 v4 — 正确区分 .pyc 和 .marshal
"""
import dis
import marshal
import struct
import sys
import os
import zlib

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "disasm_output.txt")
TARGETS = ["color_util", "index", "login", "robot_thread"]


def load_module_file(path):
    """根据扩展名正确加载 .pyc 或 .marshal 文件"""
    with open(path, 'rb') as f:
        data = f.read()

    # .marshal 文件是被加密/混淆的，只有 .pyc 可用
    if path.endswith('.marshal'):
        # marshal 文件在此项目中是加密的，无法直接加载
        return None

    if not path.endswith('.pyc'):
        return None

    # .pyc 格式: magic(4) + flags(4) + timestamp(4) + src_size(4) + marshal_code
    offset = 16
    if offset >= len(data):
        return None

    return marshal.loads(data[offset:])


def extract_all_from_pyz(pyz_path):
    """从 PyInstaller PYZ 提取模块"""
    results = {}
    with open(pyz_path, 'rb') as f:
        data = f.read()

    if data[:4] != b'PYZ\0':
        return results

    # 策略: 遍历整个文件，找到所有可被 marshal.loads 解出的 code 对象
    # PYZ 格式: magic + zlib(TOC) + 多个 zlib(module)
    # 每个压缩块: 2字节可能是zlib头 x\x9c 或类似
    pos = 4
    raw_blocks = []

    # 提取所有 zlib 压缩块
    i = 4
    while i < len(data) - 4:
        # 找 zlib 头 (78 9c 或 78 01 或 78 da)
        if data[i] == 0x78 and data[i+1] in (0x01, 0x9c, 0xda, 0x5e):
            start = i
            try:
                dobj = zlib.decompressobj()
                decompressed = dobj.decompress(data[start:])
                if decompressed:
                    raw_blocks.append(decompressed)
            except Exception:
                pass
        i += 1

    # 尝试对每个块解析 TOC 和模块
    for block in raw_blocks:
        # 尝试作为 TOC 解析
        try:
            toc_str = block.decode('utf-8', errors='replace')
            if '|' in toc_str:
                for line in toc_str.strip().split('\n'):
                    parts = line.rsplit('|', 2)
                    if len(parts) == 3 and parts[0] in TARGETS:
                        pass  # TOC found, but we need offset info
        except Exception:
            pass

        # 尝试作为 marshal code 解析
        try:
            code = marshal.loads(block)
            if hasattr(code, 'co_name'):
                # 根据 co_consts 中的文件名推断模块名
                for const in code.co_consts:
                    if hasattr(const, 'co_name'):
                        pass
                # 简单策略: co_name 可能就是模块名
                results[code.co_name] = code
        except Exception:
            pass

    return results


def dis_code(code, label, out):
    out.write(f"{'='*80}\n")
    out.write(f"模块: {label}\n")
    out.write(f"函数列表: {[c.co_name for c in code.co_consts if hasattr(c, 'co_name')]}\n")
    out.write(f"{'='*80}\n\n")
    out.write(dis.Bytecode(code).dis())
    out.write("\n\n\n")


def find_and_dis(module_name, out, pyz_modules):
    if module_name in pyz_modules:
        dis_code(pyz_modules[module_name], f"{module_name} (PYZ)", out)
        return

    # modules/ 目录
    mod_dir = os.path.join(BASE, "extracted", "modules")
    for fname in [module_name + '.pyc', module_name + '.marshal']:
        p = os.path.join(mod_dir, fname)
        if os.path.exists(p):
            code = load_module_file(p)
            if code:
                dis_code(code, f"{module_name} ({fname})", out)
                return
            else:
                out.write(f"!!! {module_name}: {fname} 存在但无法解析（.marshal 加密或 .pyc 损坏）\n\n")
                return

    # __pycache__ 回退
    cache = os.path.join(BASE, "extracted", "source_v2", "__pycache__")
    if os.path.isdir(cache):
        for fname in os.listdir(cache):
            if fname.startswith(module_name) and fname.endswith('.pyc'):
                p = os.path.join(cache, fname)
                code = load_module_file(p)
                if code:
                    dis_code(code, f"{module_name} (__pycache__)", out)
                    return

    out.write(f"!!! {module_name}: 未找到可用 bytecode\n\n")


def main():
    print("正在反汇编...")

    pyz_path = os.path.join(BASE, "extracted", "PYZ-00.pyz")
    pyz_modules = {}
    if os.path.exists(pyz_path):
        print("扫描 PYZ-00.pyz...")
        pyz_modules = extract_all_from_pyz(pyz_path)
        print(f"  PYZ 中找到 {len(pyz_modules)} 个代码对象")
        for k, v in pyz_modules.items():
            print(f"    {k}: {[c.co_name for c in v.co_consts if hasattr(c, 'co_name')]}")

    # 直接尝试 modules/ 下的 .pyc
    mod_dir = os.path.join(BASE, "extracted", "modules")
    print(f"\nmodules/ 目录:")
    for fname in os.listdir(mod_dir):
        if fname.endswith('.pyc') or fname.endswith('.marshal'):
            p = os.path.join(mod_dir, fname)
            code = load_module_file(p)
            if code:
                print(f"  {fname}: OK (co_name={code.co_name})")
            else:
                print(f"  {fname}: 无法加载")

    # __pycache__ 检查
    cache = os.path.join(BASE, "extracted", "source_v2", "__pycache__")
    if os.path.isdir(cache):
        print(f"\n__pycache__/ 中的目标文件:")
        for fname in sorted(os.listdir(cache)):
            if any(fname.startswith(t) for t in TARGETS) and fname.endswith('.pyc'):
                p = os.path.join(cache, fname)
                code = load_module_file(p)
                if code:
                    print(f"  {fname}: OK")
                else:
                    print(f"  {fname}: 无法加载")

    with open(OUTPUT, 'w', encoding='utf-8') as out:
        out.write("字节码反汇编输出 v4\n")
        out.write(f"Python: {sys.version}\n\n")

        for mod in TARGETS:
            find_and_dis(mod, out, pyz_modules)

    print(f"\n输出: {OUTPUT}")


if __name__ == "__main__":
    main()
