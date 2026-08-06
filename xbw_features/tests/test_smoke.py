# -*- coding: utf-8 -*-
"""
小霸王三功能合并包冒烟测试（不依赖真机/ADB）

运行：
    cd D:\mhxy-auto-fight
    .venv\Scripts\python.exe xbw_features\tests\test_smoke.py
"""

import os
import sys

import cv2
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_DIR)

from xbw_features import backend, const, QPoint, QColor

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


# ============ 1. qtcompat ============
def test_qtcompat():
    print("[1] qtcompat QPoint/QColor")
    p = QPoint(3, 4)
    check("QPoint.x/y", p.x() == 3 and p.y() == 4)
    check("QPoint 加法", (p + QPoint(1, 2)) == QPoint(4, 6))
    check("QPoint 减法", (p - QPoint(1, 2)) == QPoint(2, 2))
    check("QPoint 乘法", (p * 2) == QPoint(6, 8))
    c = QColor(10, 20, 30, 255)
    check("QColor rgb", c.red() == 10 and c.green() == 20 and c.blue() == 30)
    check("QColor 相等", c == QColor(10, 20, 30))
    check("QColor 不等", c != QColor(1, 2, 3))


# ============ 2. 本地四小人（ONNX 模型） ============
def test_detector():
    print("[2] 本地四小人 ONNX 检测器")
    check("模型文件存在", os.path.exists(const.FOURPERSON_CNN_PATH),
          const.FOURPERSON_CNN_PATH)
    from xbw_features.four_person.detector import SingleImageDetector, IMG_TARGET_SIZE
    det = SingleImageDetector()
    img = np.zeros((100, 90, 3), dtype=np.uint8)
    prob = det.predict_img(img)
    check("推理返回 0~1 概率", 0.0 <= prob <= 1.0, str(prob))
    check("输入尺寸 90x90", IMG_TARGET_SIZE == 90)
    check("阈值 0.8", __import__("xbw_features.four_person.detector", fromlist=["CONF_THRESHOLD"]).CONF_THRESHOLD == 0.8)

    from xbw_features.common.util.cnn_util import cnnUtil
    taps = []
    logs = []
    backend.setup(
        screencap_fn=lambda d: white_frame(),
        tap_fn=lambda d, x, y, is_double=False: taps.append((x, y)),
        log_fn=lambda d, m: logs.append(m),
        cache_seconds=0,
    )
    try:
        cnnUtil.findFourPersonLocal("test-device", curFrame=np.random.randint(0, 255, (448, 800, 3), dtype=np.uint8))
        check("findFourPersonLocal 不抛异常", True)
    except Exception as e:
        check("findFourPersonLocal 不抛异常", False, repr(e))
    check("findFourPersonLocal 有日志", len(logs) > 0, str(logs[:2]))


# ============ 3. findPic 模板匹配（修正参数顺序后） ============
def test_find_pic():
    print("[3] findPic 模板匹配")
    from xbw_features.common.util.img_util import findPic, _load_template
    tmpl = _load_template("装备条件")
    check("装备条件模板可加载", tmpl is not None)
    tmpl_card = _load_template("怪物卡片")
    check("怪物卡片模板可加载", tmpl_card is not None)
    if tmpl is not None:
        frame = white_frame()
        th, tw = tmpl.shape[:2]
        x0, y0 = 300, 120
        frame[y0:y0 + th, x0:x0 + tw] = tmpl
        pt = findPic("test-device", "装备条件", curFrame=frame, similar=0.7)
        check("findPic 命中粘贴位置", pt is not None, str(pt))
        if pt is not None:
            check("命中坐标接近 (300,120)", abs(pt.x() - x0) < 40 and abs(pt.y() - y0) < 40,
                  f"{pt.x()},{pt.y()}")
        pt2 = findPic("test-device", "怪物卡片", curFrame=frame, similar=0.9)
        check("无目标时不误报", pt2 is None, str(pt2))


# ============ 4. 行囊 20 格占用检测 + diff ============
def test_backpack_grid():
    print("[4] 行囊 20 格占用检测 + diff")
    from xbw_features.common.util.color_util import getHasProductPoints, PKG_CENTER_CUR_PKG
    from xbw_features.common.util.math_util import get_diff_points
    from xbw_features.qtcompat import QPoint

    empty_color = (216, 173, 185)  # BGR 与 QColor(185,173,216) 对应
    frame = np.full((448, 800, 3), empty_color, dtype=np.uint8)
    backend.setup(screencap_fn=lambda d: frame.copy(), tap_fn=lambda *a, **k: None,
                  log_fn=lambda *a, **k: None, cache_seconds=0)
    pts = getHasProductPoints("test-device", firstCenterPoint=PKG_CENTER_CUR_PKG)
    check("空背包 -> 0 个占用槽", len(pts) == 0, str(len(pts)))

    # 在第 3 格（index 2）放一个不透明色块
    slot = QPoint(400, 135) + QPoint(57 * 2, 56 * 0)
    frame[slot.y() - 10:slot.y() + 10, slot.x() - 10:slot.x() + 10] = (80, 80, 80)
    pts2 = getHasProductPoints("test-device", firstCenterPoint=PKG_CENTER_CUR_PKG)
    check("放入 1 格 -> 1 个占用槽", len(pts2) == 1, str([(p.x(), p.y()) for p in pts2]))
    added = get_diff_points(pts, pts2)
    check("diff 新增 1 槽", len(added) == 1, str(len(added)))


# ============ 4.5 findTextPosition 回归（曾因 wrongCount 未定义崩溃） ============
def test_find_text_position():
    print("[4.5] findTextPosition 点阵匹配")
    from xbw_features.common.util.color_util import findTextPosition, zaiTextPoints

    def white():
        return np.full((448, 800, 3), 255, dtype=np.uint8)

    backend.setup(screencap_fn=lambda d: white(), tap_fn=lambda *a, **k: None,
                  log_fn=lambda *a, **k: None, cache_seconds=0)
    # 无匹配（用户线上报错路径）：纯白帧找“在”字 -> None 且不抛 UnboundLocalError
    try:
        r = findTextPosition("t", zaiTextPoints, 250, 55, 60, 68,
                             isColorFunc=lambda c: c.red() > 110 and c.green() > 110 and c.blue() > 100)
        check("无匹配返回 None 不崩溃", r is None, str(r))
    except Exception as e:
        check("无匹配返回 None 不崩溃", False, repr(e))

    # 有匹配：2x2 黑色点阵贴在 (100,100) -> 返回 (100,100)
    from xbw_features.qtcompat import QPoint
    pts = [QPoint(0, 0), QPoint(1, 0), QPoint(0, 1), QPoint(1, 1)]
    frame = white()
    frame[100:103, 100:103] = (0, 0, 0)
    backend.setup(screencap_fn=lambda d: frame, tap_fn=lambda *a, **k: None,
                  log_fn=lambda *a, **k: None, cache_seconds=0)
    r2 = findTextPosition("t", pts, 50, 50, 200, 200, isColorFunc=lambda c: c.red() < 50)
    check("点阵匹配返回锚点 (100,100)", r2 == QPoint(100, 100), str(r2))


# ============ 5. 切换场参数完整性 ============
def test_map_params():
    print("[5] 切换场参数完整性")
    from xbw_features.game_action import map_action as m
    check("点卡地图 67 个", len(m.mapParamsListDK) == 67, str(len(m.mapParamsListDK)))
    check("畅玩地图 7 个", len(m.mapParamsListCW) == 7, str(len(m.mapParamsListCW)))
    check("dianXiangAreas 11 个", len(m.dianXiangAreas) == 11, str(len(m.dianXiangAreas)))
    mp = m.getMapParams("小西天")
    check("getMapParams(小西天) 有效", mp is not None and mp.area == "小西天")
    check("goToMapAction 可调用", callable(m.goToMapAction))
    check("goToPositionAction 可调用", callable(m.goToPositionAction))
    # 回归：_gen_click_points 曾因反编译残留 (-click_cnt)[:None] 直接崩溃，
    # 导致“打开地图后不点击位置就关闭”
    try:
        pts = m._gen_click_points(300, 200)
        check("_gen_click_points 返回 4~5 个点击点", 4 <= len(pts) <= 5, str(pts))
    except Exception as e:
        check("_gen_click_points 返回 4~5 个点击点", False, repr(e))
    # 回归：_findBestNearRedPoint 曾因 return 在循环内只返回第一个点
    best = m._findBestNearRedPoint(
        [QPoint(100, 100), QPoint(280, 190), QPoint(500, 400)], QPoint(290, 200))
    check("_findBestNearRedPoint 选最近红点", best == QPoint(280, 190), str(best))
    from xbw_features.common.util.detect_position_util import detectPosition
    area, x, y = detectPosition("test-device")
    check("detectPosition 白图返回空", area is None, str(area))


# ============ 6. 环/卡计数解析与切场条件 ============
def test_switch_condition():
    print("[6] 环/卡计数解析与切场条件")
    from xbw_features.threads.dk_changjing import parse_require, should_switch_scene
    check("得3个环 -> 3", parse_require("得3个环") == 3)
    check("得2张卡片 -> 2", parse_require("得2张卡片") == 2)
    check("满180分钟 -> 180", parse_require("满180分钟") == 180)
    check("无要求 -> None", parse_require("无要求") is None)
    check("None -> None", parse_require(None) is None)
    check("环达标触发", should_switch_scene("得3个环", "无要求", 3, 0) is True)
    check("卡达标触发", should_switch_scene("无要求", "得2张卡片", 0, 2) is True)
    check("未达标不触发", should_switch_scene("得3个环", "得2张卡片", 1, 1) is False)


# ============ 7. isShowFourPerson（模板判定，白图） ============
def test_is_show_four_person():
    print("[7] isShowFourPerson 模板判定")
    from xbw_features.common.util.img_util import isShowFourPerson
    backend.setup(screencap_fn=lambda d: white_frame(), tap_fn=lambda *a, **k: None,
                  log_fn=lambda *a, **k: None, cache_seconds=0)
    try:
        ret = isShowFourPerson("test-device")
        check("白图无好友入口 -> 判定为四小人界面", ret is True, str(ret))
    except Exception as e:
        check("isShowFourPerson 不抛异常", False, repr(e))


if __name__ == "__main__":
    test_qtcompat()
    test_detector()
    test_find_pic()
    test_backpack_grid()
    test_find_text_position()
    test_map_params()
    test_switch_condition()
    test_is_show_four_person()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)
