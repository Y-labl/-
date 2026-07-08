# -*- coding: utf-8 -*-
"""灏忚タ澶╁満鏅?automation - 鍏ュ彛"""
import os, sys
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
core_path = os.path.join(project_dir, "core")
if os.path.exists(core_path) and core_path not in sys.path:
    sys.path.insert(0, core_path)
original_path = os.path.join(project_dir, "core", "original")
if os.path.exists(original_path) and original_path not in sys.path:
    sys.path.insert(0, original_path)

from ui.xiaoxitian_window import run

if __name__ == "__main__":
    run()
