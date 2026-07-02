from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QImage, QColor
import vmdiff_util
from const import stoneTextPointList, pointList120_5or6, resultPopShowPoints, lvtongTextPointList, lvtongResultPopShowPoints


def isStone(img: QImage, point: QPoint):
    # 十字检测：竖线+横线各7像素，都>=3匹配才判定晶石
    x, y = point.x(), point.y()
    # 竖线
    v_match = 0
    for i in range(7):
        if __isStoneColor(img.pixelColor(x, y + i)):
            v_match += 1
    if v_match < 5:
        return False
    # 横线
    h_match = 0
    for i in range(-3, 4):
        if __isStoneColor(img.pixelColor(x + i, y + 3)):
            h_match += 1
    if h_match >= 5:
        return True
    return False


def __isStoneColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    # 晶石紫色：蓝主导，红中等，绿低
    if blue > 180 and blue - red > 60 and blue - green > 90:
        if red > 30 and red < 230 and green < 190:
            return True
    return False


def isStoneText(img: QImage, vmType):
    okPoint = 0
    for point in stoneTextPointList:
        x = point.x()
        isStoneTextColorCount = 0
        for i in range(10):
            color = img.pixelColor(x + 1, point.y() + vmdiff_util.VmPointOffset(vmType).y())
            if __isStoneTextColor(color):
                isStoneTextColorCount += 1
            if isStoneTextColorCount >= 7:
                okPoint += 1
                break
        if okPoint >= len(stoneTextPointList) - 1:
            return True
    return False


def __isStoneTextColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 200:
        if green > 200:
            if blue < 50:
                return True
    return False


def is120PointCount(img: QImage, vmType):
    okPoint120 = 0
    for point in pointList120_5or6:
        x = point.x()
        y = point.y() + vmdiff_util.VmPointOffset(vmType).y()
        color = img.pixelColor(x, y)
        if __isTwoFourTextColor(color):
            okPoint120 += 1
            print("命中'5 or 6' {}个像素".format(okPoint120))
    return okPoint120


def __isTwoFourTextColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < 50:
        if green < 50:
            if blue < 50:
                return True
    return False


def isResultPopShow(img: QImage, vmType):
    okPoint = 0
    for point in resultPopShowPoints:
        x = point.x()
        y = point.y() + vmdiff_util.VmPointOffset(vmType).y()
        color = img.pixelColor(x, y)
        if __isResultPopColor(color):
            okPoint += 1
        if okPoint >= len(stoneTextPointList):
            return True
    return False


def islvtongResultPopShow(img: QImage):
    okPoint = 0
    for point in lvtongResultPopShowPoints:
        x = point.x()
        y = point.y()
        color = img.pixelColor(x, y)
        if __isResultPopColor(color):
            okPoint += 1
        if okPoint >= len(lvtongResultPopShowPoints) - 1:
            return True
    return False


def isLvtongText(img: QImage):
    okPoint = 0
    for point in lvtongTextPointList:
        x = point.x()
        isLvtongTextColorCount = 0
        for i in range(10):
            color = img.pixelColor(x + 1, point.y())
            if __isStoneTextColor(color):
                isLvtongTextColorCount += 1
            if isLvtongTextColorCount >= 7:
                okPoint += 1
                break
        if okPoint >= len(lvtongTextPointList) - 1:
            return True
    return False


def __isResultPopColor(color: QColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red == 24:
        if green == 44:
            if blue == 56:
                return True
    return False
