"""深度反汇编 — 递归遍历所有嵌套函数"""
import dis
import marshal
import os

CACHE = r"D:\Program Files\mhxy\stoneclient\extracted\source_v2\__pycache__"
OUTPUT = r"D:\Program Files\mhxy\stoneclient\disasm_output.txt"
TARGETS = ["color_util", "index", "login", "robot_thread"]


def dis_all(code, out, indent=0):
    """递归反汇编 code 对象及其所有嵌套代码"""
    prefix = "  " * indent
    out.write(f"{prefix}=== {code.co_name} (line {code.co_firstlineno}) ===\n")
    out.write(dis.Bytecode(code).dis())
    out.write("\n")

    for const in code.co_consts:
        if hasattr(const, 'co_code'):
            dis_all(const, out, indent + 1)


def main():
    with open(OUTPUT, 'w', encoding='utf-8') as out:
        for fname in sorted(os.listdir(CACHE)):
            if any(fname.startswith(t) for t in TARGETS) and fname.endswith('.pyc'):
                path = os.path.join(CACHE, fname)
                with open(path, 'rb') as f:
                    data = f.read()
                code = marshal.loads(data[16:])
                out.write(f"\n{'#'*80}\n")
                out.write(f"# 模块: {fname}\n")
                out.write(f"{'#'*80}\n\n")
                dis_all(code, out)

    print(f"Done -> {OUTPUT}")


if __name__ == "__main__":
    main()
