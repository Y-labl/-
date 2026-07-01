"""最小化启动测试 — 逐步排查崩溃点"""
import sys
import os
import traceback

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def log_exception(exc_type, exc_value, exc_tb):
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    print(f"\n[崩溃] {exc_type.__name__}: {exc_value}")
sys.excepthook = log_exception

print("Step 1: 导入 PyQt5...")
from PyQt5.QtWidgets import QApplication
print("  OK")

print("Step 2: 导入 login...")
from login import LoginWin
print("  OK")

print("Step 3: 创建 QApplication...")
app = QApplication(sys.argv)
print("  OK")

print("Step 4: 创建 LoginWin...")
win = LoginWin()
print("  OK")

print("Step 5: 显示窗口...")
win.show()
print("  OK — 登录窗口应该可见了")

print("Step 6: 进入事件循环...")
sys.exit(app.exec_())
