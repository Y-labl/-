# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: game_action\common_action_logic.py
import random, time
from xbw_features.qtcompat import QPoint
from xbw_features.common.util.click_util import click
from xbw_features.common.util.color_util import getColorFromFrame, isNeedWuYiColor, isShowPopColorDK
from xbw_features.common.util.detect_position_util import detectPosition
from xbw_features.common.util.img_util import findPic, waitAssertFuncOk
from xbw_features.game_action.map_action import getMapParams, goToMapAction, _isNearToPoint, goToPositionAction, clickNpcAction
from xbw_features.common.util.scrcpy_util import DeviceWidth, scrcpyUtil

def findNpcAndClickLogic(deviceId, mapParams, npcPoint, clickPopImgName, middleImgNames=[
 "点NPC对话-我要做其他事情"], withClickDismiss=False, assertImgName=None, assertFunc=None):
    areaRes, xRes, yRes = detectPosition(deviceId)
    if areaRes != mapParams.area:
        goToMapAction(deviceId, (mapParams.area), flyMapXY=npcPoint)
    if not _isNearToPoint(deviceId, npcPoint):
        goToPositionAction(deviceId, mapParams, npcPoint)
    clickNpcAction(deviceId, mapParams, npcPoint, clickPopImgName, middleImgNames=middleImgNames, withClickDismiss=withClickDismiss, assertImgName=assertImgName, assertFunc=assertFunc)


def hideTaskAndChanel(deviceId):
    taskPoint = findPic(deviceId, "主界面-右侧任务")
    if taskPoint:
        click(deviceId, taskPoint + QPoint(-83, 56))
        time.sleep(random.uniform(0.8, 2))
    chatPoint = findPic(deviceId, "喊话入口上")
    if chatPoint:
        if chatPoint.y() < 350:
            click(deviceId, chatPoint + QPoint(212, 42))
            time.sleep(random.uniform(0.8, 2))


def check51AddXue(deviceId):
    xuePercent = 0
    lanPercent = 0
    frame = scrcpyUtil.getFrame(deviceId)
    for x in range(756, 799):
        color1 = getColorFromFrame(frame, QPoint(x, 6))
        if color1.red() > 200:
            if 34 < color1.green() < 98:
                if color1.blue() < 65:
                    xuePercent += 2.38
        color2 = getColorFromFrame(frame, QPoint(x, 14))
        if 87 > color2.red() > 10:
            if 120 < color2.green() < 175:
                if color2.blue() > 205:
                    lanPercent += 2.38
    else:
        baoBaoXuePercent = 0

    for x in range(654, 699):
        color1 = getColorFromFrame(frame, QPoint(x, 6))
        if color1.red() > 200:
            if 34 < color1.green() < 98:
                if color1.blue() < 65:
                    baoBaoXuePercent += 2.38
    else:
        if xuePercent < 85:
            click(deviceId, QPoint(775, 15))
            time.sleep(random.uniform(0.5, 0.8))
            findPic(deviceId, "PK-补充气血", withClick=True)
        elif lanPercent < 50:
            click(deviceId, QPoint(775, 15))
            time.sleep(random.uniform(0.5, 0.8))
            findPic(deviceId, "PK-补充魔法", withClick=True)
        elif baoBaoXuePercent < 85:
            click(deviceId, QPoint(670, 15))
            time.sleep(random.uniform(0.5, 0.8))
            findPic(deviceId, "PK-补充气血", withClick=True)
        isShowMaoEnter = findPic(deviceId, "小猫-召唤兽忠诚度") is not None
        if isShowMaoEnter:
            isNeedWuYi = waitAssertFuncOk(deviceId, (lambda: isNeedWuYiColor(deviceId)), perT=0.1, totalT=0.6)
            if isNeedWuYi and findPic(deviceId, "小猫-召唤兽忠诚度"):
                findNpcAndClickLogic(deviceId, (getMapParams("长寿村")), (QPoint(127, 115)), "点NPC对话-我要同时补满召唤兽", assertFunc=(lambda: isShowPopColorDK(deviceId, withClickDismiss=True)))
