#!/usr/bin/env python3
"""入口：在 zhuagui 目录执行 python run_bot.py"""
from __future__ import annotations

import sys
from pathlib import Path

# DPI 感知：避免 pygetwindow 与 pyautogui 在缩放屏上坐标不一致
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    # 日志与 print 中文：避免 PowerShell 默认代码页下乱码
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# 保证可导入 bot
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bot.main import main

if __name__ == "__main__":
    raise SystemExit(main())
