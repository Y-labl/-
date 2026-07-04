# -*- coding: utf-8 -*-
"""点击工具 - 通过 ADB 在设备上模拟点击（参考小霸王 click_util.py）"""
import random, time
from core.adb_util import AdbUtil

def tap(serial, x, y, offset=5):
    """随机偏移点击"""
    cx = random.randint(x - offset, x + offset)
    cy = random.randint(y - offset, y + offset)
    return AdbUtil.tap(serial, cx, cy)

def click(serial, point_or_x, y=None, offset=5, isDouble=False):
    """通用点击（兼容 QPoint 和 x,y）"""
    if y is None:
        x, y = point_or_x.x(), point_or_x.y()
    else:
        x = point_or_x
    cx = random.randint(x - offset, x + offset)
    cy = random.randint(y - offset, y + offset)
    if isDouble:
        AdbUtil.tap(serial, cx, cy)
        time.sleep(random.uniform(0.1, 0.2))
        return AdbUtil.tap(serial, cx, cy)
    return AdbUtil.tap(serial, cx, cy)

def drag(serial, x1, y1, x2, y2, duration=300):
    """滑动"""
    return AdbUtil.swipe(serial, x1, y1, x2, y2, duration)

def random_sleep(min_s=0.3, max_s=0.8):
    time.sleep(random.uniform(min_s, max_s))
