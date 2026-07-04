# -*- coding: utf-8 -*-
"""common_action_logic - 原版接口"""

from PyQt5.QtCore import QPoint
from common.util.click_util import click
from common.util.color_util import getColorFromFrame, isNeedWuYiColor, isShowPopColorDK
from common.util.detect_position_util import detectPosition
from common.util.img_util import findPic, waitAssertFuncOk
from game_action.map_action import getMapParams, goToMapAction, _isNearToPoint, goToPositionAction, clickNpcAction
from common.util.scrcpy_util import DeviceWidth, scrcpyUtil


def hideTaskAndChanel(deviceId):
    """隐藏任务栏和频道"""
    close_imgs = ["关闭聊天", "主界面-右侧任务", "跑玉栏收起", "跑玉面板缩小"]
    for img in close_imgs:
        findPic(deviceId, img, withClick=True, similar=0.7)


def findNpcAndClickLogic(deviceId, mapParams, npcPoint, dialogText,
                         withClickDismiss=True, assertFunc=None,
                         middleImgNames=None, isYiZhan=False,
                         curTryT=0):
    """查找NPC并点击对话 - 原版接口"""
    return clickNpcAction(deviceId, mapParams, npcPoint, dialogText,
                         middleImgNames=middleImgNames,
                         assertFunc=assertFunc,
                         withClickDismiss=withClickDismiss,
                         isYiZhan=isYiZhan,
                         curTryT=curTryT)
