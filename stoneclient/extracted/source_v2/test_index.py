"""直接测试 IndexWindow — 跳过登录"""
import sys
import os
import traceback

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def log_exception(exc_type, exc_value, exc_tb):
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    print(f"\n[崩溃] {exc_type.__name__}: {exc_value}")
    print(f"[详情写入 crash_log.txt]")
sys.excepthook = log_exception

from PyQt5.QtWidgets import QApplication
from const import API_HOST, API_USERINFO

print("创建 QApplication...")
app = QApplication(sys.argv)

# 先注册用户
import requests
import json
print("注册测试用户...")
r = requests.post(f"{API_HOST}/users/login", json={
    "phone": "13800138000",
    "password": "123456",
    "version": 41,
    "uuid": "test"
})
if r.status_code == 200:
    data = r.json()
    token = "Bearer " + data["obj"]["token"]
    print(f"  Token: {token}")
else:
    print(f"  注册失败: {r.status_code} {r.text}")
    sys.exit(1)

# 注入 token
from stone_util import app_data
app_data.setValue("token", token)
app_data.setValue("phone", "13800138000")

print("创建 IndexWindow...")
from index import IndexWindow
win = IndexWindow()
print("显示窗口...")
win.show()
print("OK — 主窗口应该可见了")

sys.exit(app.exec_())
