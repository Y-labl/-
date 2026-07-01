"""
启动检查脚本 — 检查依赖并尝试启动小石头系统
用法: python start_check.py
"""
import sys
import os

print("=" * 50)
print("小石头系统 - 启动检查")
print(f"Python: {sys.version}")
print(f"目录: {os.getcwd()}")
print("=" * 50)

# 1. 检查必需的第三方库
deps = {
    "PyQt5": "PyQt5",
    "requests": "requests",
    "psutil": "psutil",
    "pynvml": "pynvml",
    "win32api": "pywin32",
    "win32gui": "pywin32",
    "win32con": "pywin32",
}

missing = []
installed = []

for mod, pkg in deps.items():
    try:
        __import__(mod)
        installed.append(f"  + {pkg}")
    except ImportError:
        missing.append(f"  - {pkg} (pip install {pkg})")

print("\n已安装:")
if installed:
    for m in installed:
        print(m)
else:
    print("  无")

if missing:
    print("\n缺失! 请安装:")
    for m in missing:
        print(m)
    print("\n一键安装: pip install PyQt5 requests psutil pynvml pywin32")
    sys.exit(1)

print("\n依赖检查通过!")

# 2. 检查后端 API
import requests
print("\n检查后端 API (http://127.0.0.1:3000)...")
try:
    r = requests.get("http://127.0.0.1:3000", timeout=2)
    print(f"  后端状态: {r.status_code}")
except requests.ConnectionError:
    print("  后端未启动! 登录会失败，但可以看 UI")
except Exception as e:
    print(f"  后端异常: {e}")

# 3. 尝试启动
print("\n启动小石头系统...")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 设置全局异常捕获，写入 crash_log.txt
import traceback
def log_exception(exc_type, exc_value, exc_tb):
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    print(f"\n[崩溃] {exc_type.__name__}: {exc_value}")
    print(f"[详情已写入 crash_log.txt]")
sys.excepthook = log_exception

try:
    from PyQt5.QtWidgets import QApplication
    from login import LoginWin

    app = QApplication(sys.argv)
    win = LoginWin()
    win.show()
    print("GUI 已启动，请查看窗口")
    sys.exit(app.exec_())
except Exception as e:
    print(f"启动失败: {e}")
    traceback.print_exc()
