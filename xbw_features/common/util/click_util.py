# -*- coding: utf-8 -*-
# 反编译 click_util.py 适配版：原实现走 scrcpy 客户端注入点击，
# 合并后统一走 xbw_features.backend（默认 ADB input tap，或引擎注入）。

import math
import random
import time

from loguru import logger
from xbw_features.qtcompat import QPoint
from xbw_features import backend


def click(deviceId, clickPoint, offset=QPoint(5, 5), isDouble=False):
    try:
        clickX = random.randint(clickPoint.x() - offset.x(), clickPoint.x() + offset.x())
        clickY = random.randint(clickPoint.y() - offset.y(), clickPoint.y() + offset.y())
        backend.tap(deviceId, clickX, clickY, is_double=isDouble)
    except Exception as e:
        try:
            logger.error(e)
        finally:
            e = None
            del e


def drag(deviceId, touchPoints):
    try:
        smoothPoints = getSmoothPoints(touchPoints)
        for index in range(len(smoothPoints)):
            touchPoint = smoothPoints[index]
            backend.tap(deviceId, touchPoint.x(), touchPoint.y())
            time.sleep(0.05)
    except Exception as e:
        try:
            logger.error(e)
        finally:
            e = None
            del e


def getSmoothPoints(points, step: float=3.0):
    """
    对整条点序列路径重采样平滑
    鼠标模拟特性：起点终点点位密集，中间稀疏（缓入缓出）
    :param points: 原始轨迹点列表 [QPoint,...]
    :param step: 【中间最大间距】像素
    :return: 插值后的密集点列表
    """
    result = []
    if not points:
        return result
    result.append(points[0])
    for i in range(1, len(points)):
        p_prev = points[i - 1]
        p_curr = points[i]
        seg_points = split_segment_mouse_move(p_prev, p_curr, step)
        result.extend(seg_points[1:])
    return result


def split_segment_mouse_move(p1: QPoint, p2: QPoint, max_step: float=3.0):
    """
    模拟真人鼠标移动插值：两端密集，中间稀疏（缓入缓出 ease-in-out）
    :param p1: 起点
    :param p2: 终点
    :param max_step: 路径【中间区域】允许的最大点间距
    :return: 包含起点、终点的点位列表
    """
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    total_dist = math.hypot(dx, dy)
    if total_dist < 0.1:
        return [p1, p2]
    seg_count = max(2, math.ceil(total_dist / max_step))
    point_list = []
    for i in range(seg_count + 1):
        t = i / seg_count
        s = 0.5 * (1.0 - math.cos(math.pi * t))
        x = p1.x() + dx * s
        y = p1.y() + dy * s
        point_list.append(QPoint(round(x), round(y)))
    return point_list
