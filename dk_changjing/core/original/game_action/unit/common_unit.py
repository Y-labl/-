# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: game_action\unit\common_unit.py
import random, time
from PyQt5.QtCore import QPoint
from loguru import logger
import const
from common.util.click_util import click
from common.util.color_util import isShowPopColorDK
from common.util.img_util import findPic, findPics
from common.util.scrcpy_util import DeviceHeight, DeviceWidth, scrcpyUtil
from game_action.unit.unit_core import checkStatusOk

@checkStatusOk
def clickOpenPkg(deviceId, preImgName="道具", middleImgNames=["道具-道具栏"], nextImgName="物品锁", preFunc=None, nextFunc=None, isClickPreImg=True, isClosePopTry=True):
    """打开道具栏背包 - 图像识别点击"""
    if isClosePopTry:
        closePop(deviceId)
    if preFunc:
        preFunc()
    if isClickPreImg:
        found = findPic(deviceId, preImgName, similar=0.75, withClick=True)
        if found:
            time.sleep(random.uniform(0.3, 0.5))
    if middleImgNames:
        for name in middleImgNames:
            if findPic(deviceId, name, similar=0.75):
                break
    if nextFunc:
        nextFunc()


@checkStatusOk
def clickClosePkg(deviceId, preImgName='物品锁'):
    logger.info("运行clickClosePkg内部函数")
    closePop(deviceId, isOneTime=True)
    return


@checkStatusOk
def clickBaiTan(deviceId, preImgName="摆摊按钮", middleImgNames=["普通摊位按钮", "坚持摆摊按钮"], nextImgName="收摊普通摊位", isClickPreImg=True):
    logger.info("运行clickBaiTan内部函数")
    return


@checkStatusOk
def doubleClickProduct(deviceId, preImgName=None, preFunc=None, nextImgName=None, isDoubleClickPreImg=True):
    """双击使用道具 - 图像识别查找并双击"""
    if preFunc:
        preFunc()
    if preImgName and isDoubleClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withDoubleClick=True)
        time.sleep(random.uniform(0.3, 0.5))
    if nextImgName:
        time.sleep(random.uniform(0.3, 0.5))


@checkStatusOk
def hideMapLocation(deviceId, preImgName="地图-筛选", nextFunc=None, middleFunc=None):
    """隐藏地图位置筛选"""
    if middleFunc:
        middleFunc()
    if nextFunc:
        nextFunc()


@checkStatusOk
def clickFlyMap(deviceId, preImgName=None, nextFunc=None, isClickPreImg=True):
    logger.info("clickFlyMap内部函数")
    clickClosePkg(deviceId)
    return


@checkStatusOk
def clickOpenMap(deviceId, preImgName="打开地图", nextImgName="地图-筛选", isClickPreImg=True):
    """打开地图 - 图像识别点击"""
    if isClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withClick=True)
        time.sleep(random.uniform(0.5, 0.8))


@checkStatusOk
def clickMapOpenShaiXuan(deviceId, preImgName="地图-筛选", nextImgName="地图-筛选-全部", isClickPreImg=True):
    """打开地图筛选"""
    if isClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withClick=True)
        time.sleep(random.uniform(0.3, 0.5))


@checkStatusOk
def waitToMapPosition(deviceId, nextFunc=None, nextTotalT=30):
    """等待到达地图位置 - 循环检测位置"""
    from common.util.detect_position_util import detectPosition
    import time
    waited = 0
    while waited < nextTotalT:
        time.sleep(1)
        waited += 1
        if nextFunc:
            try:
                if nextFunc():
                    return True
            except:
                pass
    return True


@checkStatusOk
def clickNpcPerson(deviceId, clickPoint, nextImgName=None, middleImgNames=None, middleFunc=None, nextPerT=0.2):
    logger.info("clickNpc内部函数")
    if clickPoint != QPoint():
        click(deviceId, clickPoint)
    return


@checkStatusOk
def clickNpcDialog(deviceId, preImgName=None, nextImgName=None, nextFunc=None, isClickPreImg=True, isNotFirstCheckNext=True):
    """点击NPC对话框选项"""
    if preImgName and isClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withClick=True)
        time.sleep(random.uniform(0.3, 0.5))
    if nextFunc:
        nextFunc()


@checkStatusOk
def clickNpcTaskPerson(deviceId, preFunc=None, nextImgName=None, nextTotalT=None):
    logger.info("clickNpcTaskPerson内部函数")
    return


@checkStatusOk
def clickChuanSong(deviceId, preImgName="传送", nextFunc=None, isClickPreImg=True, isClosePopTry=True):
    """点击传送按钮"""
    if isClosePopTry:
        closePop(deviceId)
    if isClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withClick=True)
        time.sleep(random.uniform(0.3, 0.5))
    if nextFunc:
        nextFunc()


@checkStatusOk
def clickOpenHide(deviceId, nextImgName='左下角返回', isClosePopTry=True):
    logger.info("运行clickOpenHide内部函数")
    click(deviceId, QPoint(25 + scrcpyUtil.getNewMOffset(deviceId), 158))
    return


@checkStatusOk
def clickHidePlayer(deviceId, preFunc=None, nextFunc=None, isClosePopTry=True):
    logger.info("clickHidePlayer内部函数")
    click(deviceId, (QPoint(29 + scrcpyUtil.getNewMOffset(deviceId), 211)), offset=(QPoint(10, 10)))
    return


@checkStatusOk
def clickHideTanwei(deviceId, preFunc=None, nextFunc=None, isClosePopTry=True):
    logger.info("clickHideTanwei内部函数")
    click(deviceId, (QPoint(29 + scrcpyUtil.getNewMOffset(deviceId), 274)), offset=(QPoint(10, 10)))
    return


@checkStatusOk
def clickHideJiemian(deviceId, preFunc=None, nextFunc=None, isClosePopTry=True):
    logger.info("clickHideJiemian内部函数")
    click(deviceId, (QPoint(29 + scrcpyUtil.getNewMOffset(deviceId), 336)), offset=(QPoint(10, 10)))
    return


@checkStatusOk
def clickCloseHide(deviceId, preImgName="左下角返回", isClickPreImg=True, nextFunc=None):
    """关闭隐藏面板"""
    if isClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withClick=True)
        time.sleep(random.uniform(0.3, 0.5))
    if nextFunc:
        nextFunc()


@checkStatusOk
def clickOpenLeftTopMenu(deviceId, preImgName="菜单入口-打开", middleImgNames=["跑玉面板缩小"], nextImgName="菜单-指引", isClickPreImg=True, width=650):
    """打开左上角菜单"""
    if isClickPreImg:
        findPic(deviceId, preImgName, similar=0.75, withClick=True)
        time.sleep(random.uniform(0.3, 0.5))


@checkStatusOk
def clickCloseLeftTopMenu(deviceId, preImgName='菜单-指引'):
    click(deviceId, (QPoint(15 + scrcpyUtil.getNewMOffset(deviceId), 78)), offset=(QPoint(5, 1)))
    logger.info("运行clickCloseLeftTopMenu内部函数")
    return


def closePop(deviceId, left=330, top=0, width=None, height=None, isOneTime=False, tryT=0):
    if width is None:
        width = DeviceWidth - 330
    if height is None:
        height = DeviceHeight
    if tryT > 3:
        return
    tryT += 1
    closeImgNames = []
    if const.gameType == "点卡服":
        closeImgNames = ["关闭弹窗", "关闭聊天", "关闭活动弹窗", "左下角返回"]
    else:
        closeImgNames = ["关闭弹窗1"]
    closePopList = findPics(deviceId, closeImgNames, left=left, top=top, width=width, height=height, withClick=True, clickWaitT=0.6)
    isMenuShow = findPic(deviceId, "菜单-指引") is not None
    if isMenuShow:
        click(deviceId, QPoint(15 + scrcpyUtil.getNewMOffset(deviceId), 78), offset=QPoint(5, 1))
        time.sleep(random.uniform(0.3, 0.5))
    isHasPop = isShowPopColorDK(deviceId, withClickDismiss=True)
    if not isHasPop:
        if len(closePopList) <= 0:
            if not isMenuShow:
                return
    if not isOneTime:
        closePop(deviceId, left=left, top=top, width=width, height=height, isOneTime=isOneTime, tryT=tryT)

