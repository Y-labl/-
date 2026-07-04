# -*- coding: utf-8 -*-
"""点击工具 - 通过 scrcpy ADB 点击屏幕"""

import random, time, math
from PyQt5.QtCore import QPoint
from loguru import logger
from common.util.scrcpy_util import scrcpyUtil
from pyscrcpy.const import ACTION_DOWN, ACTION_UP


def click(deviceId, point, offset=None, isDouble=False, offsetPoint=None):
    """点击屏幕 - 原版接口
    
    Args:
        deviceId: 设备ID
        point: QPoint 坐标
        offset: 偏移
        isDouble: 是否双击
        offsetPoint: 额外偏移点
    """
    try:
        client = scrcpyUtil.getClient(deviceId)
        if client is None or not client.alive:
            logger.debug("scrcpy client 不可用")
            return
        
        # 计算点击坐标
        x = point.x() if isinstance(point, QPoint) else point[0]
        y = point.y() if isinstance(point, QPoint) else point[1]
        
        if offset and isinstance(offset, QPoint):
            x += offset.x()
            y += offset.y()
        elif offset and isinstance(offset, (list, tuple)):
            x += offset[0]
            y += offset[1]
        
        if offsetPoint and isinstance(offsetPoint, QPoint):
            x += offsetPoint.x()
            y += offsetPoint.y()
        
        x = max(0, int(x))
        y = max(0, int(y))
        
        logger.debug("点击: ({}, {})".format(x, y))
        client.control.touch(x, y, ACTION_DOWN)
        client.control.touch(x, y, ACTION_UP)
        
        if isDouble:
            time.sleep(random.uniform(0.05, 0.1))
            client.control.touch(x, y, ACTION_DOWN)
            client.control.touch(x, y, ACTION_UP)
    except Exception as e:
        logger.debug("点击失败: {}".format(e))


def drag(deviceId, touchPoints, duration=500):
    """滑动/拖拽 - 使用 ADB swipe
    
    Args:
        deviceId: 设备ID
        touchPoints: [(x1,y1), (x2,y2)] 起终点
        duration: 滑动持续时间(ms)
    """
    try:
        client = scrcpyUtil.getClient(deviceId)
        if client is None or not client.alive:
            return
        
        if len(touchPoints) >= 2:
            x1 = touchPoints[0].x() if isinstance(touchPoints[0], QPoint) else touchPoints[0][0]
            y1 = touchPoints[0].y() if isinstance(touchPoints[0], QPoint) else touchPoints[0][1]
            x2 = touchPoints[-1].x() if isinstance(touchPoints[-1], QPoint) else touchPoints[-1][0]
            y2 = touchPoints[-1].y() if isinstance(touchPoints[-1], QPoint) else touchPoints[-1][1]
            
            # 使用 ADB swipe 实现拖拽
            cmd = "input swipe {} {} {} {} {}".format(
                int(x1), int(y1), int(x2), int(y2), int(duration))
            client.control.adbutil_devices.shell(cmd)
    except Exception as e:
        logger.debug("拖拽失败: {}".format(e))


def getSmoothPoints(touchPoints, step=10):
    """生成平滑路径点"""
    if len(touchPoints) < 2:
        return touchPoints
    result = []
    for i in range(len(touchPoints) - 1):
        p1 = touchPoints[i]
        p2 = touchPoints[i + 1]
        x1 = p1.x() if isinstance(p1, QPoint) else p1[0]
        y1 = p1.y() if isinstance(p1, QPoint) else p1[1]
        x2 = p2.x() if isinstance(p2, QPoint) else p2[0]
        y2 = p2.y() if isinstance(p2, QPoint) else p2[1]
        
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        steps = max(1, int(dist / step))
        for s in range(steps):
            t = s / steps
            result.append(QPoint(int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t)))
    result.append(touchPoints[-1] if isinstance(touchPoints[-1], QPoint) 
                  else QPoint(touchPoints[-1][0], touchPoints[-1][1]))
    return result