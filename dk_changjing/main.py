# -*- coding: utf-8 -*-
"""点卡场景自动化工具 - 入口"""
import os
import sys

# 确保项目根目录在 path 中
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 添加 core 目录（pyscrcpy 包在此）
core_path = os.path.join(project_dir, "core")
if os.path.exists(core_path) and core_path not in sys.path:
    sys.path.insert(0, core_path)

# 添加原版反编译模块路径
original_path = os.path.join(project_dir, "core", "original")
if os.path.exists(original_path) and original_path not in sys.path:
    sys.path.insert(0, original_path)

from ui.main_window import run

if __name__ == "__main__":
    run()

