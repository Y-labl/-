"""
===========================================================================
小霸王 - Python字节码反编译脚本
===========================================================================
用于反编译 PyInstaller 打包中的 .pyc 文件
运行方式: python decompile_pyc.py

依赖: pip install uncompyle6 pycdc (或 decompyle3)
===========================================================================
"""
import os
import sys
import subprocess
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INTERNAL_DIR = SCRIPT_DIR  # _internal 目录
DECOMPILE_OUTPUT = os.path.join(SCRIPT_DIR, "python_decompiled")


def find_pyc_files():
    """查找所有 .pyc 文件"""
    pyc_files = []
    for root, dirs, files in os.walk(INTERNAL_DIR):
        for f in files:
            if f.endswith('.pyc'):
                full = os.path.join(root, f)
                pyc_files.append(full)
    return pyc_files


def decompile_with_uncompyle6(pyc_path, output_dir):
    """使用 uncompyle6 反编译"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'uncompyle6', '-o', output_dir, pyc_path],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


def decompile_with_pycdc(pyc_path, output_dir):
    """使用 pycdc 反编译"""
    try:
        # pycdc 是 C++ 工具，需要编译好的可执行文件
        result = subprocess.run(
            ['pycdc', pyc_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            # 手动写入文件
            rel_path = os.path.relpath(pyc_path, INTERNAL_DIR)
            out_path = os.path.join(output_dir, rel_path.replace('.pyc', '.py'))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            return True
    except Exception:
        pass
    return False


def decompile_with_decompyle3(pyc_path, output_dir):
    """使用 decompyle3 反编译"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'decompyle3', '-o', output_dir, pyc_path],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


def main():
    print("=" * 60)
    print("  小霸王 Python 字节码反编译工具")
    print("=" * 60)
    print()

    pyc_files = find_pyc_files()
    print(f"找到 {len(pyc_files)} 个 .pyc 文件")
    print()

    if not pyc_files:
        print("未找到 .pyc 文件")
        print()
        print("注意: PyInstaller 打包的应用，Python源码可能:")
        print("  1. 编译为 .pyc 存储在 _internal/ 目录")
        print("  2. 嵌入在 .exe 文件的 PYZ 归档中")
        print("  3. 使用 Cython 编译为 .pyd 原生扩展(无法反编译)")
        print()
        print("对于情况2，可使用 pyinstxtractor 提取:")
        print("  python pyinstxtractor.py 小霸王.exe")
        return

    os.makedirs(DECOMPILE_OUTPUT, exist_ok=True)

    # 尝试不同工具
    success_count = 0
    for pyc in pyc_files:
        rel = os.path.relpath(pyc, INTERNAL_DIR)
        print(f"  反编译: {rel} ... ", end='')

        if decompile_with_uncompyle6(pyc, DECOMPILE_OUTPUT):
            print("✅ (uncompyle6)")
            success_count += 1
        elif decompile_with_pycdc(pyc, DECOMPILE_OUTPUT):
            print("✅ (pycdc)")
            success_count += 1
        elif decompile_with_decompyle3(pyc, DECOMPILE_OUTPUT):
            print("✅ (decompyle3)")
            success_count += 1
        else:
            print("❌ 失败")

    print()
    print(f"成功反编译: {success_count}/{len(pyc_files)}")
    print(f"输出目录: {DECOMPILE_OUTPUT}")

    if success_count == 0:
        print()
        print("所有反编译工具均失败，请安装工具:")
        print("  pip install uncompyle6 decompyle3")
        print("  pip install pycdc  # 或从 https://github.com/zrax/pycdc 编译")


if __name__ == '__main__':
    main()
