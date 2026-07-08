# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\color_util.py
import random, time, cv2
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
from loguru import logger
from common.util.click_util import click
from common.util.math_util import isframeSame
from common.util.scrcpy_util import scrcpyUtil
import const
resultPopShowPointsAvoidChengJiu1 = [
 QPoint(165, 406), QPoint(200, 428)]
resultPopShowPointsAvoidChengJiu2 = [QPoint(680, 406), QPoint(715, 428)]
resultPopShowHasButtonPoints = [QPoint(595, 286), QPoint(600, 286), QPoint(605, 286), QPoint(610, 286), QPoint(615, 286), QPoint(620, 286)]
hideEnterShowPoints = [
 QPoint(16, 163), QPoint(16, 164), QPoint(16, 165), QPoint(16, 166), QPoint(17, 162), QPoint(17, 163), QPoint(17, 164), QPoint(17, 165), QPoint(17, 166), QPoint(18, 164), QPoint(18, 165), QPoint(18, 166), QPoint(19, 164), QPoint(19, 165), QPoint(19, 166), QPoint(20, 163), QPoint(20, 164), QPoint(20, 166), QPoint(21, 152), QPoint(21, 162), QPoint(21, 166), QPoint(30, 163), QPoint(30, 166), QPoint(31, 163), QPoint(31, 164), QPoint(31, 165), QPoint(31, 166), QPoint(32, 152), QPoint(32, 164), QPoint(32, 165), QPoint(32, 166), QPoint(33, 163), QPoint(33, 164), QPoint(33, 165), QPoint(33, 166), QPoint(34, 163), QPoint(34, 164), QPoint(34, 165), QPoint(34, 166)]
hidePlayerOpenPoints = [QPoint(11, 231), QPoint(11, 232), QPoint(18, 210), QPoint(19, 206), QPoint(19, 230), QPoint(20, 193), QPoint(20, 230), QPoint(21, 192), QPoint(22, 204), QPoint(23, 204), QPoint(24, 201), QPoint(24, 205), QPoint(24, 206), QPoint(25, 200), QPoint(25, 206), QPoint(25, 232), QPoint(26, 200), QPoint(31, 190), QPoint(33, 230), QPoint(34, 200), QPoint(35, 200), QPoint(35, 201), QPoint(36, 201), QPoint(37, 190), QPoint(39, 204), QPoint(40, 205), QPoint(40, 206), QPoint(40, 207), QPoint(41, 207), QPoint(46, 231), QPoint(48, 230), QPoint(52, 230)]
hideTanweiOpenPoints = [QPoint(7, 293), QPoint(10, 293), QPoint(11, 293), QPoint(11, 294), QPoint(18, 257), QPoint(19, 256), QPoint(20, 255), QPoint(20, 270), QPoint(21, 254), QPoint(21, 264), QPoint(21, 270), QPoint(22, 266), QPoint(23, 252), QPoint(23, 267), QPoint(24, 267), QPoint(24, 268), QPoint(25, 268), QPoint(25, 269), QPoint(25, 294), QPoint(25, 295), QPoint(26, 264), QPoint(26, 269), QPoint(26, 270), QPoint(27, 264), QPoint(27, 265), QPoint(27, 271), QPoint(28, 262), QPoint(28, 264), QPoint(28, 265), QPoint(28, 266), QPoint(28, 267), QPoint(29, 262), QPoint(29, 264), QPoint(29, 265), QPoint(29, 266), QPoint(29, 267), QPoint(30, 262), QPoint(30, 264), QPoint(30, 265), QPoint(30, 266), QPoint(30, 267), QPoint(31, 252), QPoint(31, 262), QPoint(31, 264), QPoint(31, 265), QPoint(31, 266), QPoint(31, 267), QPoint(32, 262), QPoint(32, 264), QPoint(32, 265), QPoint(32, 266), QPoint(32, 267), QPoint(32, 294), QPoint(33, 264), QPoint(33, 265), QPoint(33, 266), QPoint(33, 267),
 QPoint(34, 263), QPoint(34, 264), QPoint(34, 265), QPoint(34, 266), QPoint(34, 267), QPoint(35, 263), QPoint(35, 264), QPoint(35, 265), QPoint(35, 266), QPoint(35, 267), QPoint(36, 252), QPoint(36, 264), QPoint(36, 265), QPoint(36, 266), QPoint(36, 267), QPoint(36, 268), QPoint(36, 269), QPoint(36, 270), QPoint(36, 271), QPoint(36, 272), QPoint(36, 273), QPoint(37, 264), QPoint(37, 265), QPoint(37, 267), QPoint(37, 268), QPoint(37, 269), QPoint(37, 270), QPoint(37, 271), QPoint(37, 272), QPoint(37, 273), QPoint(37, 294), QPoint(38, 266), QPoint(38, 268), QPoint(38, 269), QPoint(38, 294), QPoint(39, 266), QPoint(39, 267), QPoint(40, 256), QPoint(40, 268), QPoint(40, 269), QPoint(40, 270), QPoint(40, 271), QPoint(41, 269), QPoint(41, 270), QPoint(41, 271), QPoint(41, 272), QPoint(41, 273), QPoint(41, 294), QPoint(41, 295)]
hideJiemianOpenPoints = [QPoint(9, 355), QPoint(10, 355), QPoint(11, 355), QPoint(12, 355), QPoint(13, 325), QPoint(15, 323), QPoint(16, 322), QPoint(19, 319), QPoint(20, 318), QPoint(21, 317), QPoint(21, 355), QPoint(21, 356), QPoint(21, 357), QPoint(22, 329), QPoint(22, 355), QPoint(22, 357), QPoint(23, 330), QPoint(23, 357), QPoint(24, 314), QPoint(24, 331), QPoint(25, 313), QPoint(25, 332), QPoint(25, 355), QPoint(25, 357), QPoint(26, 313), QPoint(26, 332), QPoint(26, 333), QPoint(26, 338), QPoint(26, 355), QPoint(26, 357), QPoint(27, 334), QPoint(27, 357), QPoint(28, 328), QPoint(28, 329), QPoint(28, 335), QPoint(28, 357), QPoint(29, 357), QPoint(30, 332), QPoint(30, 337), QPoint(31, 332), QPoint(31, 337), QPoint(32, 333), QPoint(32, 338), QPoint(33, 329), QPoint(33, 330), QPoint(33, 334), QPoint(34, 330), QPoint(35, 330), QPoint(35, 331), QPoint(36, 314), QPoint(36, 330), QPoint(36, 332), QPoint(36, 333), QPoint(37, 331), QPoint(37, 333), QPoint(37, 334), QPoint(37, 335),
 QPoint(37, 336), QPoint(37, 337), QPoint(37, 338), QPoint(38, 332), QPoint(38, 333), QPoint(39, 317), QPoint(39, 332), QPoint(39, 333), QPoint(39, 356), QPoint(39, 357), QPoint(40, 317), QPoint(41, 318), QPoint(41, 319), QPoint(45, 322), QPoint(48, 355), QPoint(49, 355), QPoint(50, 327), QPoint(50, 355), QPoint(51, 355), QPoint(51, 358), QPoint(52, 355), QPoint(53, 355), QPoint(53, 357), QPoint(54, 355), QPoint(55, 355), QPoint(56, 355), QPoint(56, 358), QPoint(57, 355)]

def getColorFromFrame(frame, point: QPoint) -> QColor:
    try:
        pixel_bgr = frame[(point.y(), point.x())]
        return QColor(pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])
    except Exception as e:
        logger.debug(f"getColorFromFrame异常: {e}")
        return QColor()


def isWhiteTextColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 200:
        if green > 200:
            if blue > 200:
                return True
        return False


def isDarkWhiteColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 135:
        if green > 150:
            if blue > 150:
                return True
        return False


def __isPositionNumColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red >= 100:
        if green > 125:
            if blue > 135:
                return True
        return False


# [Decompilation error - skipped]


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

def matchPointColors(frame, pointsList, texts, colorFuc, isOffsetTwo=True, errorSimilar=0.1):
    resText = None
    if isOffsetTwo:
        for offsetPoint in OFFSET_SEQUENCE0_2:
            resText = _matchPointClolrs(frame, pointsList, texts, colorFuc, offsetPoint, errorSimilar)
            if resText:
                break

    else:
        resText = _matchPointClolrs(frame, pointsList, texts, colorFuc, QPoint, errorSimilar)
    return resText


def _matchPointClolrs(frame, pointsList, texts, colorFuc, offsetPoint, errorSimilar):
    resText = None
    for index in range(len(pointsList)):
        points = pointsList[index]
        errorCount = 0
        if texts[index] == "东海湾" or texts[index] == "东海渊":
            errorSimilar = 0.05
        for point in points:
            x = offsetPoint.x() + point.x()
            y = offsetPoint.y() + point.y()
            color = getColorFromFrame(frame, QPoint(x, y))
            isColorOk = colorFuc(color)
            if not isColorOk:
                errorCount += 1
            if errorCount >= errorSimilar * len(points):
                break

        if errorCount < errorSimilar * len(points):
            resText = texts[index]
            break
        return resText


typeNum1_0_Points = [
 QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 5), QPoint(0, 6), QPoint(0, 7), QPoint(1, 0), QPoint(1, 8), QPoint(2, 0), QPoint(2, 8), QPoint(3, 0), QPoint(3, 8), QPoint(4, 1), QPoint(4, 7), QPoint(4, 8), QPoint(5, 2), QPoint(5, 3), QPoint(5, 4), QPoint(5, 5), QPoint(5, 6)]
typeNum1_1_Points = [QPoint(1, 1), QPoint(2, 0), QPoint(2, 1), QPoint(2, 2), QPoint(2, 3), QPoint(2, 4), QPoint(2, 5), QPoint(2, 6), QPoint(2, 7), QPoint(2, 8)]
typeNum1_2_Points = [QPoint(0, 1), QPoint(0, 8), QPoint(1, 0), QPoint(1, 6), QPoint(1, 7), QPoint(1, 8), QPoint(2, 0), QPoint(2, 6), QPoint(2, 8), QPoint(3, 0), QPoint(3, 5), QPoint(3, 8), QPoint(4, 0), QPoint(4, 4), QPoint(4, 8), QPoint(5, 1), QPoint(5, 2), QPoint(5, 8)]
typeNum1_3_Points = [QPoint(0, 1), QPoint(0, 7), QPoint(0, 8), QPoint(1, 0), QPoint(1, 8), QPoint(2, 0), QPoint(2, 4), QPoint(3, 0), QPoint(3, 4), QPoint(3, 8), QPoint(4, 0), QPoint(4, 3), QPoint(4, 4), QPoint(4, 5), QPoint(4, 8), QPoint(5, 1), QPoint(5, 2), QPoint(5, 5), QPoint(5, 6), QPoint(5, 7)]
typeNum1_4_Points = [QPoint(0, 5), QPoint(0, 6), QPoint(1, 4), QPoint(1, 6), QPoint(2, 3), QPoint(2, 6), QPoint(3, 1), QPoint(3, 2), QPoint(3, 6), QPoint(4, 0), QPoint(4, 1), QPoint(4, 2), QPoint(4, 3), QPoint(4, 4), QPoint(4, 5), QPoint(4, 6), QPoint(4, 7), QPoint(4, 8)]
typeNum1_5_Points = [QPoint(0, 1), QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 7), QPoint(1, 0), QPoint(1, 3), QPoint(1, 8), QPoint(2, 0), QPoint(2, 3), QPoint(2, 8), QPoint(3, 0), QPoint(3, 3), QPoint(3, 8), QPoint(4, 0), QPoint(4, 4), QPoint(4, 8), QPoint(5, 6)]
typeNum1_6_Points = [QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 5), QPoint(0, 6), QPoint(1, 0), QPoint(1, 4), QPoint(1, 8), QPoint(2, 0), QPoint(2, 3), QPoint(3, 0), QPoint(3, 3), QPoint(3, 8), QPoint(4, 0), QPoint(4, 4), QPoint(4, 8), QPoint(5, 5), QPoint(5, 6)]
typeNum1_7_Points = [QPoint(0, 0), QPoint(1, 0), QPoint(2, 0), QPoint(2, 4), QPoint(2, 5), QPoint(2, 6), QPoint(2, 7), QPoint(2, 8), QPoint(3, 0), QPoint(3, 2), QPoint(3, 3), QPoint(4, 0), QPoint(4, 1)]
typeNum1_8_Points = [QPoint(0, 1), QPoint(0, 2), QPoint(0, 5), QPoint(0, 6), QPoint(0, 7), QPoint(0, 8), QPoint(1, 0), QPoint(1, 3), QPoint(1, 4), QPoint(1, 8), QPoint(2, 0), QPoint(2, 4), QPoint(2, 8), QPoint(3, 0), QPoint(3, 4), QPoint(3, 8), QPoint(4, 1), QPoint(4, 3), QPoint(4, 4), QPoint(4, 8), QPoint(5, 2), QPoint(5, 6), QPoint(5, 7)]
typeNum1_9_Points = [QPoint(0, 1), QPoint(0, 2), QPoint(0, 3), QPoint(0, 4), QPoint(0, 7), QPoint(1, 0), QPoint(1, 5), QPoint(1, 8), QPoint(2, 0), QPoint(2, 5), QPoint(3, 0), QPoint(3, 5), QPoint(3, 8), QPoint(4, 1), QPoint(4, 4), QPoint(4, 5), QPoint(4, 7), QPoint(4, 8), QPoint(5, 3), QPoint(5, 4), QPoint(5, 5), QPoint(5, 6)]
type1NumPointsList = [
 typeNum1_4_Points,typeNum1_2_Points,typeNum1_8_Points,typeNum1_9_Points,typeNum1_3_Points,typeNum1_6_Points,typeNum1_5_Points,typeNum1_7_Points,typeNum1_0_Points,typeNum1_1_Points]
numResList = [4,2,8,9,3,6,5,7,0,1]

def getType1Num(frame, startX, endX, startY, colorFunc=__isPositionNumColor):
    resultNumStr = ""
    numLen = round((endX - startX) / 7.5)
    for numTh in range(numLen):
        for index in range(len(type1NumPointsList)):
            points = type1NumPointsList[index]
            num = numResList[index]
            rightOffset = None
            for offset in OFFSET_SEQUENCE0_1:
                isOk = True
                wrongCount = 0
                for point in points:
                    x = startX + offset.x() + 8 * numTh + point.x()
                    y = startY + offset.y() + point.y()
                    if x > endX:
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
                    rightOffset = offset
                    break
                if rightOffset is not None:
                    break

    if len(resultNumStr) < numLen or resultNumStr == "":
        cv2.imwrite("./getType1Num_error.png", frame)
        return resultNumStr


def isShowPopColorDK(deviceId, withClickDismiss=False):
    if _isShowPopColor(deviceId):
        if withClickDismiss:
            if _isShowPopColor(deviceId):
                click(deviceId, QPoint(400, 224))
                time.sleep(random.uniform(0.5, 0.8))
            return True
        return False


def _isShowPopColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    for x in range(resultPopShowPointsAvoidChengJiu1[0].x(), resultPopShowPointsAvoidChengJiu1[1].x()):
        for y in range(resultPopShowPointsAvoidChengJiu1[0].y(), resultPopShowPointsAvoidChengJiu1[1].y()):
            color = getColorFromFrame(frame, QPoint(x, y))
            if not _isResultPopColor(color):
                return False

    for x in range(resultPopShowPointsAvoidChengJiu2[0].x(), resultPopShowPointsAvoidChengJiu2[1].x()):
        for y in range(resultPopShowPointsAvoidChengJiu2[0].y(), resultPopShowPointsAvoidChengJiu2[1].y()):
            color = getColorFromFrame(frame, QPoint(x, y))
            if not _isResultPopColor(color):
                return False

        return True


def _isResultPopColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < 52:
        if 13 < green < 73:
            if 25 < blue < 85:
                return True
        return False


def _isResultBtnColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < 70:
        if 58 < green < 98:
            if 81 < blue < 121:
                return True
        return False


def isShowHideEnter(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hideEnterShowPoints:
        color = getColorFromFrame(frame, point)
        if _isHideEnterColor(color):
            okPoint += 1

    if okPoint >= len(hideEnterShowPoints) * 0.7:
        return True
    return False


def _isHideEnterColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 170:
        if green > 140:
            if blue > 80:
                return True
        return False


def isOpenHidePlayerColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hidePlayerOpenPoints:
        color = getColorFromFrame(frame, point)
        if _isHideOpenColor(color):
            okPoint += 1

    if okPoint >= len(hidePlayerOpenPoints) * 0.8:
        return True
    return False


def isOpenHideTanWeiColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hideTanweiOpenPoints:
        color = getColorFromFrame(frame, point)
        if _isHideOpenColor(color):
            okPoint += 1

    if okPoint >= len(hideTanweiOpenPoints) * 0.8:
        return True
    return False


def isOpenHideJieMianColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hideJiemianOpenPoints:
        color = getColorFromFrame(frame, point)
        if _isHideOpenColor(color):
            okPoint += 1

    if okPoint >= len(hideJiemianOpenPoints) * 0.8:
        return True
    return False


def _isHideOpenColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 160:
        if green > 190:
            if blue > 200:
                return True
        return False


def isShowRoleAvatar(deviceId):
    # [Decompilation incomplete]
    return False


def getPkgPointList(firstCenterPoint):
    pkgPoints = []
    for i in range(20):
        row = i // 5
        colum = i % 5
        targetPoint = firstCenterPoint + QPoint(57 * colum, 56 * row)
        pkgPoints.append(targetPoint)

    return pkgPoints


PKG_CENTER_GVN_NPC = QPoint(285, 129)

def getHasProductPoints(deviceId, firstCenterPoint=PKG_CENTER_GVN_NPC, isCareForbid=True):
    frame = scrcpyUtil.getFrame(deviceId)
    hasProductPoints = []
    centerPoints = getPkgPointList(firstCenterPoint)
    for index in range(len(centerPoints)):
        if not isEmptyProduct(frame, (centerPoints[index]), index=index, isCareForbid=isCareForbid):
            hasProductPoints.append(centerPoints[index])
        return hasProductPoints


def isEmptyProduct(frame, centerP, emptyColor=QColor(185, 173, 216), index=-1, isCareForbid=True):
    isEmpty = True
    radius1 = 45
    radius2 = 45
    if index == 0 or index == 19:
        radius1 = 8
    else:
        if index == 4 or index == 15:
            radius2 = 8
    for i in range(radius1):
        topLeftToBottomRightX = centerP.x() + i - radius1 / 2
        topLeftToBottomRightY = centerP.y() + i - radius1 / 2
        topLeftToBottomRightColor = getColorFromFrame(frame, QPoint(topLeftToBottomRightX, topLeftToBottomRightY))
        if __isEmptyColor(topLeftToBottomRightColor, emptyColor) is False:
            isEmpty = False
            break

    for i in range(radius2):
        bottomLeftToTopRightX = centerP.x() + i - radius2 / 2
        bottomLeftToTopRightY = centerP.y() - i + radius2 / 2
        bottomLeftToTopRightColor = getColorFromFrame(frame, QPoint(bottomLeftToTopRightX, bottomLeftToTopRightY))
        if __isEmptyColor(bottomLeftToTopRightColor, emptyColor) is False:
            isEmpty = False
            break

    return isEmpty or (isCareForbid and (isForbidProduct(frame, centerP)))


def isForbidProduct(frame, centerP):
    redPoints = [
     QPoint(11, -7), QPoint(8, -4), QPoint(4, 0), QPoint(1, 3), QPoint(-3, 7), QPoint(-7, 11), QPoint(-10, 14), QPoint(-7, 17), QPoint(-5, 19), QPoint(-2, 19), QPoint(4, 19), QPoint(9, 17), QPoint(15, 13), QPoint(17, 10), QPoint(18, 5), QPoint(18, 0), QPoint(18, -4), QPoint(16, -8)]
    redCount = 0
    for redP in redPoints:
        color = getColorFromFrame(frame, centerP + redP)
        if __isForbidColor(color):
            redCount += 1
            continue
        return redCount >= len(redPoints) * 0.85


def __isEmptyColor(color: QColor, emptyColor: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if abs(red - emptyColor.red()) < 20:
        if abs(green - emptyColor.green()) < 20:
            if abs(blue - emptyColor.blue()) < 20:
                return True
        return False


def __isForbidColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 110:
        if green < 145:
            if blue < 150:
                return True
        return False


def isPageBlackColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < 110:
        if green < 120:
            if blue < 140:
                return True
        return False


def waitCropFrameChange(frame1, deviceId, left, top, crop_width, crop_height, perT=0.5, totalT=10):
    waitT = 0
    roi1 = frame1[top:top + crop_height, left:left + crop_width]
    while True:
        frame2 = scrcpyUtil.getFrame(deviceId)
        roi2 = frame2[top:top + crop_height, left:left + crop_width]
        isSame = isframeSame(roi1, roi2)
        if not isSame:
            time.sleep(perT)
            break
        time.sleep(perT)
        waitT += perT
        if waitT > totalT:
            break


def isPointColor(frame, point, color, rongCuo=20):
    curColor = getColorFromFrame(frame, point)
    if abs(color.red() - curColor.red()) < rongCuo and abs(color.green() - curColor.green()) < rongCuo:
        if abs(color.blue() - curColor.blue()) < rongCuo:
            return True
        return False


# [Decompilation error - skipped]


ziDongTextPoints = [
 QPoint(351, 308), QPoint(351, 310), QPoint(351, 311), QPoint(351, 313), QPoint(351, 314), QPoint(352, 317), QPoint(353, 307), QPoint(353, 317), QPoint(354, 307), QPoint(355, 307), QPoint(356, 307), QPoint(357, 307), QPoint(359, 317), QPoint(360, 308), QPoint(360, 310), QPoint(360, 311), QPoint(360, 313), QPoint(360, 314), QPoint(364, 311), QPoint(364, 314), QPoint(364, 316), QPoint(365, 311), QPoint(366, 311), QPoint(367, 315), QPoint(368, 316), QPoint(369, 309), QPoint(369, 316), QPoint(370, 309), QPoint(370, 313), QPoint(371, 308), QPoint(371, 309), QPoint(372, 309), QPoint(372, 317), QPoint(373, 309), QPoint(373, 317), QPoint(374, 310), QPoint(374, 311), QPoint(374, 312), QPoint(374, 313), QPoint(374, 314), QPoint(374, 315)]

def isAutoChuanSongColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    for i in range(285, 295):
        for j in range(310, 320):
            color = getColorFromFrame(frame, QPoint(i, j))
            if not color.red() > 100:
                if not color.green() > 100:
                    if color.blue() > 100:
                        pass
            else:
                return False

    okCount = 0
    for point in ziDongTextPoints:
        color = getColorFromFrame(frame, point)
        if color.red() > 150:
            if color.green() > 150:
                if color.blue() > 150:
                    okCount += 1
                isShowAuto = okCount >= len(ziDongTextPoints) * 0.9

    if isShowAuto:
        time.sleep(15)
    return isShowAuto


JumpGray_ShangHui_OneDianPu = QPoint(182, 390)
JumpGray_ShangHui_AllDianPu = QPoint(245, 394)
JumpGray_Resp = QPoint(0, 0)

def isJumpPageGray(deviceId, topPoint=JumpGray_ShangHui_OneDianPu):
    frame = scrcpyUtil.getFrame(deviceId)
    for y in range(15):
        if not isPointColor(frame, (QPoint(topPoint.x() - 5, topPoint.y() + y)), (QColor(62, 62, 62)), rongCuo=10):
            return False
        return True


def isNeedWuYiColor(deviceId):
    return not isPointColor((scrcpyUtil.getFrame(deviceId)), (QPoint(586, 30)), (QColor(241, 144, 26)), rongCuo=15)