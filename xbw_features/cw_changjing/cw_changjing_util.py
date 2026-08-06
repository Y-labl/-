# -*- coding: utf-8 -*-
# Assembled from decompiled bytecode of cw_changjing_util.pyc

import random
from xbw_features.qtcompat import QPoint
from loguru import logger
from xbw_features.common.util.log_util import orderLog
from xbw_features.common.util.math_util import distance_between_points
from xbw_features.common.util.click_util import click
from xbw_features.common.util.color_util import findTextPosition, isRedBaoBaoTextColor, isWhiteTextColor, isWhiteZaiColor, jinshenRedPoints, jinglingRedPoints, zaiTextPoints, qingTextPoints, chaoLiangBaoJiRedPoints, wenYiRedPoints, baozhaRedPoints, jingyingRedPoints, toulingRedPoints, huyouRedPoints, baobaoRedPoints
from xbw_features.game_action.map_action import AreaParams, _isReturnTrueFuc
from xbw_features.qtcompat import QColor

def randomClickMap(deviceId, mapParams):
    if mapParams is None:
        mapParams = defaultMapParams
    clickMapX, clickMapY = getRadomMapPoint(mapParams)
    click(deviceId, QPoint(clickMapX, clickMapY))


def getRadomMapPoint(mapParams):
        clickMapX = random.randint(mapParams.mapLeftBottomPoint.x() + 50, mapParams.mapLeftBottomPoint.x() + mapParams.xyWidthHeight.x() - 50)
        clickMapY = 0
        if mapParams.area == "丝绸之路":
            clickMapX = random.randint(395, 530)
            clickMapY = random.randint(mapParams.mapLeftBottomPoint.y() + mapParams.xyWidthHeight.y() - 10, mapParams.mapLeftBottomPoint.y() - 10)
        elif mapParams.area == "银华境":
            clickMapY = random.randint(mapParams.mapLeftBottomPoint.y() + mapParams.xyWidthHeight.y() - 10, mapParams.mapLeftBottomPoint.y() - 10)
        else:
            clickMapY = random.randint(mapParams.mapLeftBottomPoint.y() + mapParams.xyWidthHeight.y() - 50, mapParams.mapLeftBottomPoint.y() - 50)
        if "龙窟" in mapParams.area:
            if 240 < clickMapX < 340 and clickMapY > 277:
                return getRadomMapPoint(mapParams)
            if clickMapX > 515 and clickMapY < 140:
                return getRadomMapPoint(mapParams)
            if 330 < clickMapX < 450 and clickMapY > 270:
                return getRadomMapPoint(mapParams)
            if clickMapX > 482 and clickMapY < 165:
                return getRadomMapPoint(mapParams)
        elif mapParams.area == "子母河底":
            if clickMapX < 250 and clickMapY > 295:
                return getRadomMapPoint(mapParams)
            if 325 < clickMapX < 425 and clickMapY < 125:
                return getRadomMapPoint(mapParams)
        elif mapParams.area == "凤巢四层":
            if clickMapX < 215 and clickMapY < 170:
                return getRadomMapPoint(mapParams)
            if 345 < clickMapX < 420 and clickMapY < 130:
                return getRadomMapPoint(mapParams)
        elif mapParams.area == "麒麟山":
            if clickMapX < 215 and clickMapY < 120:
                return getRadomMapPoint(mapParams)
            if 250 < clickMapX < 320 and clickMapY > 340:
                return getRadomMapPoint(mapParams)
            if clickMapX > 450 and clickMapY > 330:
                return getRadomMapPoint(mapParams)
        elif mapParams.area == "狮驼岭":
            if clickMapX > 470 and clickMapY < 120:
                return getRadomMapPoint(mapParams)
        elif mapParams.area == "银华境":
            if clickMapY < 308:
                return getRadomMapPoint(mapParams)
        return (clickMapX, clickMapY)


def randomClickMap_CiChouZhiLu(deviceId, turpleXRange):
    clickMapX = random.randint(turpleXRange[0], turpleXRange[1])
    clickMapY = random.randint(185, 260)
    click(deviceId, QPoint(clickMapX, clickMapY))


def correctGongJiPoint(clickPoint):
    nearPoint = None
    minDistance = 800
    for gongJiP in gongJiPoints:
        if distance_between_points(gongJiP, clickPoint) < minDistance:
            minDistance = distance_between_points(gongJiP, clickPoint)
            nearPoint = gongJiP
        return nearPoint


def findFourPersonDetectArea(deviceId, curframe=None):
    zaiPoint = findTextPosition(deviceId, zaiTextPoints, 250, 55, 60, 68, curframe=curframe, isColorFunc=(lambda color: isWhiteZaiColor(color)))
    if zaiPoint:
        logger.debug(f"{deviceId}找到四小人-在的坐标{zaiPoint}")
        return (zaiPoint.x() - 40, zaiPoint.y() + 35, 360, 100)
    qingPoint = findTextPosition(deviceId, qingTextPoints, 220, 55, 50, 55, curframe=curframe, isColorFunc=(lambda color: isWhiteTextColor(color, value=120)))
    if qingPoint:
        logger.debug(f"{deviceId}找到四小人-请的坐标{qingPoint}")
        return (qingPoint.x(), qingPoint.y() + 45, 360, 100)
    return (0, 0, 0, 0)


def findRedTextPosition(deviceId, frame, positionIndex, left, top, width):
    redTextPointsList = [
     chaoLiangBaoJiRedPoints, wenYiRedPoints, baozhaRedPoints, jingyingRedPoints, 
     jinglingRedPoints, jinshenRedPoints, toulingRedPoints, huyouRedPoints, baobaoRedPoints]
    redTexts = ['超量暴击', '瘟疫', '爆炸', '精英', '精灵', '金身', ' 头领', '护佑', '宝宝']
    if width == 30:
        redTextPointsList = [
         jinglingRedPoints, baobaoRedPoints]
        redTexts = ["精灵", "宝宝"]
    res_text = None
    res_pos = None
    for index in range(len(redTextPointsList)):
        redTextPoints = redTextPointsList[index]
        rongCuo = 0.08
        if redTexts[index] == "金身":
            rongCuo = 0.15
        res_pos = findTextPosition(deviceId, redTextPoints, left, top, width, 20, isColorFunc=isRedBaoBaoTextColor, curframe=frame, rongCuo=0.08)
        if res_pos:
            res_text = redTexts[index]
            break
        orderLog(deviceId, f"识别位置{positionIndex}:文字({res_text}), 坐标{res_pos}")
        return (res_text, res_pos)

