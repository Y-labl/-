# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: game_action\application_action.py
import random, time
from xbw_features.qtcompat import QPoint
from loguru import logger
from xbw_features import const
from xbw_features.common.util.click_util import click
from xbw_features.common.util.color_util import isShowHideEnter, isOpenHidePlayerColor, isOpenHideTanWeiColor, isOpenHideJieMianColor
from xbw_features.common.util.img_util import findPics, findPic, waitAssertImgOk
from xbw_features.game_action.unit.common_unit import clickBaiTan, clickLogout, clickOpenPkg, clickOpenHide, clickHidePlayer, clickHideTanwei, clickHideJiemian, clickCloseHide, clickOpenSetting, openSwitchRolePop
from xbw_features.game_action.unit.unit_core import checkLandscape
from xbw_features.common.util.scrcpy_util import scrcpyUtil


def clickHidePaoyuLanFromShouQi(deviceId):
    """跑玉为占位功能，直接跳过（原 paoyu 模块不在三功能范围内）。"""
    return None

def tanweiAction(deviceId, isOpen=True, curTryT=0):
    logger.debug(f"{deviceId} 开始摆摊 isOpen={isOpen}")
    try:
        clickOpenPkg(deviceId)
        clickBaiTan(deviceId)
    except Exception as e:
        try:
            pass
        finally:
            e = None
            del e


def openHideAction(deviceId, curTryT=0):
    try:
        isHasFuGai = findPic(deviceId, "跑玉栏标题")
        if isHasFuGai:
            clickHidePaoyuLanFromShouQi(deviceId)
        clickOpenHide(deviceId)
        clickHidePlayer(deviceId, preFunc=(lambda: not isOpenHidePlayerColor(deviceId)), nextFunc=(lambda: isOpenHidePlayerColor(deviceId)))
        clickHideTanwei(deviceId, preFunc=(lambda: not isOpenHideTanWeiColor(deviceId)), nextFunc=(lambda: isOpenHideTanWeiColor(deviceId)))
        clickHideJiemian(deviceId, preFunc=(lambda: isOpenHideJieMianColor(deviceId)), nextFunc=(lambda: not isOpenHideJieMianColor(deviceId)))
    except RuntimeError:
        curTryT += 1
        logger.warning(f"位置移动goToPositionAction异常，第{curTryT}次重试")
        if curTryT <= 10:
            openHideAction(deviceId, curTryT=curTryT)
    except Exception as e:
        try:
            logger.debug(f"openHideAction Exception: {e}")
        finally:
            e = None
            del e


def closeHideAction(deviceId, curTryT=0):
    try:
        clickCloseHide(deviceId, nextFunc=(lambda: findPic(deviceId, "左下角返回") is None))
    except RuntimeError:
        curTryT += 1
        logger.warning(f"关闭隐藏closeHideAction异常，第{curTryT}次重试")
        if curTryT <= 10:
            closeHideAction(deviceId, curTryT=curTryT)
    except Exception as e:
        try:
            logger.debug(f"closeHideAction: {e}")
        finally:
            e = None
            del e


def logoutAction(deviceId, curTryT=0):
    try:
        clickOpenSetting(deviceId)
        clickLogout(deviceId)
    except RuntimeError:
        curTryT += 1
        logger.warning(f"退出登录logoutAction异常，第{curTryT}次重试")
        if curTryT <= 10:
            logoutAction(deviceId, curTryT=curTryT)
    except Exception as e:
        try:
            logger.debug(f"logoutAction: {e}")
        finally:
            e = None
            del e


def logoutSwitchRoleAction(deviceId, index, curTry=0):
    try:
        clickOpenSetting(deviceId)
        clickLogout(deviceId)
        time.sleep(random.uniform(2.5, 4.8))
        isLand = scrcpyUtil.isLandscape(deviceId)
        logger.debug(f"{deviceId}检查是否退出, 确认是横屏: {isLand}")
        if not isLand:
            logger.debug(f"{deviceId}不是横屏, 发现游戏退出, 尝试进入游戏")
            isShowEnterPoint = waitAssertImgOk(deviceId, "进入梦幻互通", totalT=300)
            if isShowEnterPoint:
                openSwitchRolePop(deviceId)
                if index == 2:
                    click(deviceId, (QPoint(616, 172)), offset=(QPoint(50, 50)))
                else:
                    if index == 3:
                        click(deviceId, (QPoint(414, 355)), offset=(QPoint(50, 50)))
                    else:
                        if index == 4:
                            click(deviceId, (QPoint(616, 355)), offset=(QPoint(50, 50)))
                        else:
                            time.sleep(random.uniform(1.5, 2.8))
                            waitAssertImgOk(deviceId, "进入梦幻互通", withClick=True)
                            isChatEnter = waitAssertImgOk(deviceId, "喊话入口上", totalT=300)
                            if isChatEnter:
                                logger.debug(f"{deviceId}成功进入游戏, 关闭所有弹窗")
                                time.sleep(random.uniform(2.5, 4.8))
                                from xbw_features.game_action.unit.common_unit import closePop
                                closePop(deviceId)
                            else:
                                logger.debug(f"{deviceId} 5分钟未发现喊话入口")
            else:
                logger.debug(f"{deviceId} 5分钟未发现进入梦幻互通")
    except RuntimeError:
        curTryT += 1
        logger.warning(f"登出切号logoutSwitchRoleAction异常，第{curTryT}次重试")
        if curTryT <= 10:
            logoutSwitchRoleAction(deviceId, index, curTryT=curTryT)
    except Exception as e:
        try:
            logger.debug(f"logoutSwitchRole: {e}")
        finally:
            e = None
            del e
