# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\click_util.py
import math, random, time
from datetime import datetime
from PyQt5.QtCore import QPoint
from loguru import logger
from common.util.scrcpy_util import scrcpyUtil
from pyscrcpy import const

def click(deviceId, clickPoint, offset=QPoint(5, 5), isDouble=False):
    try:
        scrcpyClient = scrcpyUtil.getClient(deviceId)
        clickX = random.randint(clickPoint.x() - offset.x(), clickPoint.x() + offset.x())
        clickY = random.randint(clickPoint.y() - offset.y(), clickPoint.y() + offset.y())
        if isDouble:
            scrcpyClient.control.touch(clickX, clickY)
            scrcpyClient.control.touch(clickX, clickY, action=(const.ACTION_UP))
            time.sleep(random.uniform(0.1, 0.2))
            scrcpyClient.control.touch(clickX, clickY)
            scrcpyClient.control.touch(clickX, clickY, action=(const.ACTION_UP))
        else:
            scrcpyClient.control.touch(clickX, clickY)
            scrcpyClient.control.touch(clickX, clickY, action=(const.ACTION_UP))
    except Exception as e:
        try:
            logger.error(e)
        finally:
            e = None
            del e


def drag(deviceId, touchPoints):
    try:
        scrcpyClient = scrcpyUtil.getClient(deviceId)
        smoothPoints = getSmoothPoints(touchPoints)
        for index in range(len(smoothPoints)):
            touchPoint = smoothPoints[index]
            action = const.ACTION_MOVE
            if index == 0:
                action = const.ACTION_DOWN
            elif index == len(smoothPoints) - 1:
                action = const.ACTION_UP
            scrcpyClient.control.touch(touchPoint.x(), touchPoint.y(), action)
            time.sleep(0.05)

    except Exception as e:
        try:
            logger.error(e)
        finally:
            e = None
            del e


def getSmoothPoints(points, step=3):
    """
        对整个点列表进行平滑拆分，所有长线段都按 step 长度分段
        """
    result = []
    if not points:
        return result
    result.append(points[0])
    for i in range(1, len(points)):
        prev = points[i - 1]
        curr = points[i]
        segment = split_segment_by_distance(prev, curr, step)
        result.extend(segment[1:])

    return result


def split_segment_by_distance(p1, p2, step=3):
    """
    把 p1 -> p2 这条线段，按每段 step 的长度均匀拆分，返回所有中间点（包含起点和终点）
    """
    points = []
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    distance = math.hypot(dx, dy)
    if distance <= step:
        return [p1, p2]
    count = int(distance / step)
    unit_dx = dx / distance
    unit_dy = dy / distance
    for i in range(count + 1):
        x = p1.x() + unit_dx * step * i
        y = p1.y() + unit_dy * step * i
        points.append(QPoint(round(x), round(y)))

    return points
