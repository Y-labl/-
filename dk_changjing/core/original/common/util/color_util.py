# -*- coding: utf-8 -*-
"""颜色检测模块 - 完整原版实现 + scrcpy 帧源"""

import random, time
import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
from loguru import logger
from common.util.scrcpy_util import scrcpyUtil
from common.util.click_util import click


def _get_frame(deviceId):
    try:
        return scrcpyUtil.getFrame(deviceId)
    except:
        return None


# ========== 颜色判断函数 ==========

def getColorFromFrame(frame, point):
    """从帧中获取指定点的颜色"""
    try:
        if frame is None:
            return QColor(0, 0, 0)
        if isinstance(point, QPoint):
            x, y = point.x(), point.y()
        elif isinstance(point, (list, tuple)):
            x, y = int(point[0]), int(point[1])
        else:
            return QColor(0, 0, 0)
        if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
            if len(frame.shape) == 3:
                b, g, r = frame[y, x]
                return QColor(int(r), int(g), int(b))
            else:
                v = frame[y, x]
                return QColor(int(v), int(v), int(v))
    except:
        pass
    return QColor(0, 0, 0)


def isWhiteTextColor(color):
    """判断是否为白色文字颜色"""
    if isinstance(color, QColor):
        r, g, b = color.red(), color.green(), color.blue()
    elif isinstance(color, (list, tuple)):
        r, g, b = color[0], color[1], color[2]
    else:
        return False
    if r > 200:
        if g > 200:
            if b > 200:
                return True
    return False


def isDarkWhiteColor(color):
    """判断暗白色（地图名颜色）"""
    if isinstance(color, QColor):
        r, g, b = color.red(), color.green(), color.blue()
    elif isinstance(color, (list, tuple)):
        r, g, b = color[0], color[1], color[2]
    else:
        return False
    if r > 135:
        if g > 150:
            if b > 150:
                return True
    return False


def _isAreaBlackColor(color):
    """判断是否为区域黑色（地图名背景色）"""
    if isinstance(color, QColor):
        red = color.red()
        green = color.green()
        blue = color.blue()
    elif isinstance(color, (list, tuple)):
        red, green, blue = color[0], color[1], color[2]
    else:
        return False
    if red < 80:
        if green < 80:
            if blue < 120:
                return True
    return False


def __isPositionNumColor(color):
    """判断坐标数字颜色 - 放宽阈值匹配新版点卡服浅色字体"""
    if isinstance(color, QColor):
        red = color.red()
        green = color.green()
        blue = color.blue()
    elif isinstance(color, (list, tuple)):
        red, green, blue = color[0], color[1], color[2]
    else:
        return False
    # 新版点卡服位置栏数字颜色范围 R=100~230 G=110~230 B=100~230
    # 中间段像素可深至 B=118 (原阈值 B>135 太严)
    if red >= 100 and green >= 100 and blue >= 100:
        # 不能太亮（背景白）也不能太暗
        if red < 240 and green < 240 and blue < 240:
            # R+G+B 不能太低（纯灰背景）
            if (red + green + blue) > 350:
                return True
    return False


def isPageBlackColor(color):
    if isinstance(color, QColor):
        return color.red() < 30 and color.green() < 30 and color.blue() < 30
    elif isinstance(color, (list, tuple)):
        return all(c < 30 for c in color)
    return False


def isNeedWuYiColor(deviceId):
    """??????????????????"""
    from common.util.color_util import isPointColor
    return not isPointColor(scrcpyUtil.getFrame(deviceId), QPoint(586, 30), QColor(241, 144, 26), rongCuo=15)


def isPointColor(frame, point, color, rongCuo=30):
    actual = getColorFromFrame(frame, point)
    if isinstance(color, QColor):
        return (abs(actual.red() - color.red()) <= rongCuo and
                abs(actual.green() - color.green()) <= rongCuo and
                abs(actual.blue() - color.blue()) <= rongCuo)
    elif isinstance(color, (list, tuple)):
        return (abs(actual.red() - color[0]) <= rongCuo and
                abs(actual.green() - color[1]) <= rongCuo and
                abs(actual.blue() - color[2]) <= rongCuo)
    return False


def isLineColor(frame, startP, color, lineType="h", direct=1, step=1, distance=100, rongCuo=30):
    if isinstance(startP, QPoint):
        x, y = startP.x(), startP.y()
    else:
        x, y = startP[0], startP[1]
    count = 0
    total = distance // step
    for i in range(total):
        px, py = (x + i * step * direct, y) if lineType == "h" else (x, y + i * step * direct)
        if isPointColor(frame, QPoint(px, py), color, rongCuo):
            count += 1
    return count >= total * 0.8


# ========== 偏移支持（原版多点找色用） ==========

OFFSET_SEQUENCE0_1 = [
    QPoint(0, 0),
    QPoint(0, -1), QPoint(0, 1),
    QPoint(-1, 0), QPoint(1, 0),
    QPoint(-1, -1), QPoint(-1, 1),
    QPoint(1, -1), QPoint(1, 1)]

OFFSET_SEQUENCE0_2 = [
    QPoint(0, 0),
    QPoint(0, -1), QPoint(0, 1),
    QPoint(-1, 0), QPoint(1, 0),
    QPoint(-1, -1), QPoint(-1, 1),
    QPoint(1, -1), QPoint(1, 1),
    QPoint(0, -2), QPoint(0, 2),
    QPoint(-2, 0), QPoint(2, 0),
    QPoint(-1, -2), QPoint(-1, 2),
    QPoint(1, -2), QPoint(1, 2),
    QPoint(-2, -1), QPoint(2, -1),
    QPoint(-2, 1), QPoint(2, 1),
    QPoint(-2, -2), QPoint(-2, 2),
    QPoint(2, -2), QPoint(2, 2)]


def matchPointColors(frame, pointsList, texts=None, colorFuc=None,
                     isOffsetTwo=True, errorSimilar=0.1):
    """多点颜色匹配 - 完整原版实现（支持偏移）

    pointsList: [[QPoint, QPoint, ...], [QPoint, ...], ...]
    texts:      [str, str, ...]
    colorFuc:   颜色判断函数

    返回匹配的地图名称，或 True/False
    """
    if frame is None or colorFuc is None:
        return None if texts is not None else False

    if isOffsetTwo:
        for offsetPoint in OFFSET_SEQUENCE0_2:
            resText = _matchPointColorsInner(frame, pointsList, texts, colorFuc, offsetPoint, errorSimilar)
            if resText:
                return resText
        return None if texts is not None else False
    else:
        return _matchPointColorsInner(frame, pointsList, texts, colorFuc, QPoint(0, 0), errorSimilar)


def _matchPointColorsInner(frame, pointsList, texts, colorFuc, offsetPoint, errorSimilar):
    """内层多点颜色匹配"""
    for index in range(len(pointsList)):
        points = pointsList[index]
        if not points:
            continue
        errorCount = 0
        sim = errorSimilar
        # 东海湾/东海渊需要更严格匹配
        if texts and index < len(texts) and (texts[index] == "东海湾" or texts[index] == "东海渊"):
            sim = 0.05
        for point in points:
            if isinstance(point, QPoint):
                x = offsetPoint.x() + point.x()
                y = offsetPoint.y() + point.y()
            elif isinstance(point, (list, tuple)):
                x = offsetPoint.x() + int(point[0])
                y = offsetPoint.y() + int(point[1])
            else:
                continue
            color = getColorFromFrame(frame, QPoint(x, y))
            if not colorFuc(color):
                errorCount += 1
            if errorCount >= sim * len(points):
                break

        if errorCount < sim * len(points):
            if texts is not None and index < len(texts):
                return texts[index]
            return True
    return None if texts is not None else False


def isAutoChuanSongColor(deviceId):
    frame = _get_frame(deviceId)
    if frame is None:
        return False
    points = [(400, 300), (400, 320), (400, 340)]
    try:
        return all(frame[y, x][2] > 100 for x, y in points)
    except:
        return False


def culNewMobileXOffset(deviceId):
    from common.util.img_util import findPic
    result = findPic(deviceId, "手机边界", similar=0.7)
    if result:
        return result.x()
    return 0


def isJumpPageGray(deviceId, topPoint=None):
    frame = _get_frame(deviceId)
    if frame is None:
        return False
    if topPoint:
        c = getColorFromFrame(frame, topPoint)
        return 80 < c.red() < 180 and 80 < c.green() < 180 and 80 < c.blue() < 180
    return False


# ========== 数字识别 ==========

typeNum1_0_Points = [
    QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 5), QPoint(0, 6), QPoint(0, 7),
    QPoint(1, 0), QPoint(1, 8), QPoint(2, 0), QPoint(2, 8), QPoint(3, 0), QPoint(3, 8),
    QPoint(4, 1), QPoint(4, 7), QPoint(4, 8), QPoint(5, 2), QPoint(5, 3), QPoint(5, 4),
    QPoint(5, 5), QPoint(5, 6)]

typeNum1_1_Points = [
    QPoint(1, 1), QPoint(2, 0), QPoint(2, 1), QPoint(2, 2), QPoint(2, 3), QPoint(2, 4),
    QPoint(2, 5), QPoint(2, 6), QPoint(2, 7), QPoint(2, 8)]

typeNum1_2_Points = [
    QPoint(0, 1), QPoint(0, 8), QPoint(1, 0), QPoint(1, 6), QPoint(1, 7), QPoint(1, 8),
    QPoint(2, 0), QPoint(2, 6), QPoint(2, 8), QPoint(3, 0), QPoint(3, 5), QPoint(3, 8),
    QPoint(4, 0), QPoint(4, 4), QPoint(4, 8), QPoint(5, 1), QPoint(5, 2), QPoint(5, 8)]

typeNum1_3_Points = [
    QPoint(0, 1), QPoint(0, 7), QPoint(0, 8), QPoint(1, 0), QPoint(1, 8), QPoint(2, 0),
    QPoint(2, 4), QPoint(3, 0), QPoint(3, 4), QPoint(3, 8), QPoint(4, 0), QPoint(4, 3),
    QPoint(4, 4), QPoint(4, 5), QPoint(4, 8), QPoint(5, 1), QPoint(5, 2), QPoint(5, 5),
    QPoint(5, 6), QPoint(5, 7)]

typeNum1_4_Points = [
    QPoint(0, 5), QPoint(0, 6), QPoint(1, 4), QPoint(1, 6), QPoint(2, 3), QPoint(2, 6),
    QPoint(3, 1), QPoint(3, 2), QPoint(3, 6), QPoint(4, 0), QPoint(4, 1), QPoint(4, 2),
    QPoint(4, 3), QPoint(4, 4), QPoint(4, 5), QPoint(4, 6), QPoint(4, 7), QPoint(4, 8)]

typeNum1_5_Points = [
    QPoint(0, 1), QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 7), QPoint(1, 0),
    QPoint(1, 3), QPoint(1, 8), QPoint(2, 0), QPoint(2, 3), QPoint(2, 8), QPoint(3, 0),
    QPoint(3, 3), QPoint(3, 8), QPoint(4, 0), QPoint(4, 4), QPoint(4, 8), QPoint(5, 6)]

typeNum1_6_Points = [
    QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 5), QPoint(0, 6), QPoint(1, 0),
    QPoint(1, 4), QPoint(1, 8), QPoint(2, 0), QPoint(2, 3), QPoint(3, 0), QPoint(3, 3),
    QPoint(3, 8), QPoint(4, 0), QPoint(4, 4), QPoint(4, 8), QPoint(5, 5), QPoint(5, 6)]

typeNum1_7_Points = [
    QPoint(0, 0), QPoint(1, 0), QPoint(2, 0), QPoint(2, 4), QPoint(2, 5), QPoint(2, 6),
    QPoint(2, 7), QPoint(2, 8), QPoint(3, 0), QPoint(3, 2), QPoint(3, 3), QPoint(4, 0),
    QPoint(4, 1)]

typeNum1_8_Points = [
    QPoint(0, 1), QPoint(0, 2), QPoint(0, 5), QPoint(0, 6), QPoint(0, 7), QPoint(0, 8),
    QPoint(1, 0), QPoint(1, 3), QPoint(1, 4), QPoint(1, 8), QPoint(2, 0), QPoint(2, 4),
    QPoint(2, 8), QPoint(3, 0), QPoint(3, 4), QPoint(3, 8), QPoint(4, 1), QPoint(4, 3),
    QPoint(4, 4), QPoint(4, 8), QPoint(5, 2), QPoint(5, 6), QPoint(5, 7)]

typeNum1_9_Points = [
    QPoint(0, 1), QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 7), QPoint(1, 0),
    QPoint(1, 5), QPoint(1, 8), QPoint(2, 0), QPoint(2, 5), QPoint(3, 0), QPoint(3, 5),
    QPoint(3, 8), QPoint(4, 1), QPoint(4, 4), QPoint(4, 5), QPoint(4, 7), QPoint(4, 8),
    QPoint(5, 3), QPoint(5, 4), QPoint(5, 5), QPoint(5, 6)]

type1NumPointsList = [
    typeNum1_4_Points, typeNum1_2_Points, typeNum1_8_Points, typeNum1_9_Points,
    typeNum1_3_Points, typeNum1_6_Points, typeNum1_5_Points, typeNum1_7_Points,
    typeNum1_0_Points, typeNum1_1_Points]

numResList = [4, 2, 8, 9, 3, 6, 5, 7, 0, 1]


def getType1Num(frame, startX, endX, startY, colorFunc=__isPositionNumColor):
    """识别坐标数字 - 完整原版实现（模板点匹配）"""
    if frame is None:
        return None
    try:
        resultNumStr = ""
        numLen = max(1, round((endX - startX) / 2.0))
        for numTh in range(numLen):
            found = False
            for index in range(len(type1NumPointsList)):
                points = type1NumPointsList[index]
                num = numResList[index]
                for offset in OFFSET_SEQUENCE0_1:
                    isOk = True
                    wrongCount = 0
                    for point in points:
                        x = startX + offset.x() + 8 * numTh + point.x()
                        y = startY + offset.y() + point.y()
                        if x > endX or x < 0 or y < 0:
                            break
                        if y >= frame.shape[0] or x >= frame.shape[1]:
                            break
                        color = getColorFromFrame(frame, QPoint(x, y))
                        if not colorFunc(color):
                            wrongCount += 1
                        if wrongCount > 0:
                            isOk = False
                            break

                    if isOk:
                        if numTh == 0:
                            resultNumStr = str(num)
                        else:
                            resultNumStr += str(num)
                        found = True
                        break
                if found:
                    break

        if len(resultNumStr) < numLen or resultNumStr == "":
            cv2.imwrite("./getType1Num_error.png", frame)
            return None
        return resultNumStr
    except:
        return None


def isframeSame(frame1, frame2, similar=0.9):
    if frame1 is None or frame2 is None:
        return False
    try:
        diff = cv2.absdiff(frame1, frame2)
        non_zero = np.count_nonzero(diff)
        total = frame1.size
        return (1 - non_zero / total) >= similar
    except:
        return False


# ========== 弹窗检测 ==========

resultPopShowPointsAvoidChengJiu1 = [QPoint(301, 147), QPoint(371, 199)]
resultPopShowPointsAvoidChengJiu2 = [QPoint(411, 147), QPoint(481, 199)]


def isShowPopColorDK(deviceId, withClickDismiss=False):
    result = _isShowPopColor(deviceId)
    if result:
        if withClickDismiss:
            if _isShowPopColor(deviceId):
                click(deviceId, QPoint(400, 224))
                time.sleep(random.uniform(0.5, 0.8))
            return True
        return True
    return False


def _isShowPopColor(deviceId):
    """检测战斗结算弹窗（原版颜色检测）"""
    frame = scrcpyUtil.getFrame(deviceId)
    if frame is None:
        return False
    try:
        for x in range(resultPopShowPointsAvoidChengJiu1[0].x(), resultPopShowPointsAvoidChengJiu1[1].x()):
            for y in range(resultPopShowPointsAvoidChengJiu1[0].y(), resultPopShowPointsAvoidChengJiu1[1].y()):
                if x >= frame.shape[1] or y >= frame.shape[0]:
                    continue
                color = getColorFromFrame(frame, QPoint(x, y))
                if not _isResultPopColor(color):
                    return False
        for x in range(resultPopShowPointsAvoidChengJiu2[0].x(), resultPopShowPointsAvoidChengJiu2[1].x()):
            for y in range(resultPopShowPointsAvoidChengJiu2[0].y(), resultPopShowPointsAvoidChengJiu2[1].y()):
                if x >= frame.shape[1] or y >= frame.shape[0]:
                    continue
                color = getColorFromFrame(frame, QPoint(x, y))
                if not _isResultPopColor(color):
                    return False
        return True
    except:
        return False


def _isResultPopColor(color):
    if isinstance(color, QColor):
        red = color.red()
        green = color.green()
        blue = color.blue()
    elif isinstance(color, (list, tuple)):
        red, green, blue = color[0], color[1], color[2]
    else:
        return False
    if red < 52:
        if 13 < green < 73:
            if 25 < blue < 85:
                return True
    return False


def isShowRoleAvatar(deviceId):
    """????????????????????????????"""
    from common.util.img_util import findPic
    result = findPic(deviceId, "好友入口", similar=0.70)
    return result is not None
