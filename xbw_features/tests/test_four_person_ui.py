# -*- coding: utf-8 -*-
"""
四小人界面判定与识别区域测试（不依赖真机）

覆盖本次还原的关键点：
  1. 普通界面（可见“好友入口”）-> 判定为非四小人界面（避免跑图误判）；
  2. 无好友入口/无头像的界面 -> 判定为四小人界面；
  3. findFourPersonDetectArea 返回的 ROI 宽度为 360（4 x 90 槽位）。

运行：
    .venv\Scripts\python.exe xbw_features\tests\test_four_person_ui.py
"""

import os
import sys

import numpy as np

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_DIR)

from xbw_features import backend
from xbw_features.common.util.img_util import _load_template, isShowFourPerson
from xbw_features.cw_changjing.cw_changjing_util import findFourPersonDetectArea

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [OK] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def white_frame():
    return np.full((448, 800, 3), 255, dtype=np.uint8)


def main():
    # 1) 纯白帧：无好友入口、无头像 -> 判定为四小人界面
    backend.setup(screencap_fn=lambda d: white_frame(), tap_fn=lambda *a, **k: None,
                  log_fn=lambda *a, **k: None, cache_seconds=0)
    print("[1] 无好友入口界面")
    check("isShowFourPerson=True", isShowFourPerson("t") is True)
    area = findFourPersonDetectArea("t")
    check("detectArea 返回 (left,top,360,100)", area[2] == 360 and area[3] == 100, str(area))

    # 2) 粘贴“好友入口”模板 -> 判定为非四小人界面（关键：消除跑图误判）
    print("[2] 有好友入口界面")
    tmpl = _load_template("好友入口")
    check("好友入口模板可加载", tmpl is not None)
    if tmpl is not None:
        frame = white_frame()
        th, tw = tmpl.shape[:2]
        frame[100:100 + th, 100:100 + tw] = tmpl
        backend.setup(screencap_fn=lambda d: frame.copy(), tap_fn=lambda *a, **k: None,
                      log_fn=lambda *a, **k: None, cache_seconds=0)
        check("isShowFourPerson=False", isShowFourPerson("t") is False)

    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
