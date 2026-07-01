"""
===========================================================================
小霸王 - PyInstaller EXE 提取脚本
===========================================================================
从 小霸王.exe 中提取 Python 字节码和资源文件
运行方式: python extract_exe.py

依赖: pip install pyinstxtractor
===========================================================================
"""
import os
import sys
import subprocess

EXE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "小霸王.exe")
EXTRACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exe_extracted")


def extract_with_pyinstxtractor():
    """使用 pyinstxtractor 提取"""
    print("[1] 尝试使用 pyinstxtractor...")
    try:
        import pyinstxtractor
        arch = pyinstxtractor.PyInstArchive(EXE_PATH)
        arch.open()
        arch.parse()
        arch.extract(EXTRACT_DIR)
        arch.close()
        print(f"      提取成功 -> {EXTRACT_DIR}")
        return True
    except ImportError:
        print("      pyinstxtractor 未安装")
    except Exception as e:
        print(f"      提取失败: {e}")
    return False


def extract_with_script():
    """使用 pyinstxtractor 脚本"""
    print("[2] 尝试使用 pyinstxtractor.py 脚本...")
    try:
        # 尝试下载 pyinstxtractor 脚本并运行
        script_path = os.path.join(os.path.dirname(__file__), "pyinstxtractor.py")

        if not os.path.exists(script_path):
            print("      未找到 pyinstxtractor.py")
            print(f"      请从 https://github.com/extremecoders-re/pyinstxtractor 下载")
            print(f"      放到: {script_path}")
            return False

        result = subprocess.run(
            [sys.executable, script_path, EXE_PATH],
            capture_output=True, text=True, timeout=60
        )
        print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
        if result.returncode == 0:
            print(f"      提取成功")
            return True
        else:
            print(f"      错误: {result.stderr[:500]}")
            return False

    except Exception as e:
        print(f"      失败: {e}")
        return False


def main():
    print("=" * 60)
    print("  小霸王 PyInstaller EXE 提取工具")
    print("=" * 60)
    print()

    if not os.path.exists(EXE_PATH):
        print(f"错误: 找不到 {EXE_PATH}")
        return

    os.makedirs(EXTRACT_DIR, exist_ok=True)

    extracted = extract_with_pyinstxtractor()
    if not extracted:
        extract_with_script()

    if not extracted:
        print()
        print("手动提取步骤:")
        print("  1. pip install pyinstxtractor")
        print("  2. 运行: python -m pyinstxtractor 小霸王.exe")
        print("  或:")
        print("  1. 下载 https://github.com/extremecoders-re/pyinstxtractor")
        print("  2. python pyinstxtractor.py 小霸王.exe")

    print()
    print(f"提取后，查找主要的 .pyc 文件 (通常是主脚本名或 struct):")
    print(f"  主脚本通常以 .pyc 格式存在提取目录中")
    print(f"  然后使用 decompile_pyc.py 反编译")


if __name__ == '__main__':
    main()
