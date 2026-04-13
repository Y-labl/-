#!/usr/bin/env python3
"""
抓鬼项目自动化测试（无需游戏窗口、不启动 PaddleOCR 推理）。
在 zhuagui 目录执行: python run_tests.py
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(_ROOT / "tests"),
        pattern="test_*.py",
        top_level_dir=str(_ROOT),
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
