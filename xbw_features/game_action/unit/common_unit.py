# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: game_action\unit\common_unit.py
import random, time
from xbw_features.qtcompat import QPoint
from loguru import logger
from xbw_features import const
from xbw_features.common.util.click_util import click
from xbw_features.common.util.color_util import isShowPopColorDK
from xbw_features.common.util.img_util import findPic, findPics
from xbw_features.common.util.scrcpy_util import DeviceHeight, DeviceWidth, scrcpyUtil
from xbw_features.game_action.unit.unit_core import checkStatusOk

def clickOpenPkg(deviceId, preImgName="道具", middleImgNames=["道具-道具栏"], nextImgName="物品锁", preFunc=None, nextFunc=None, isClickPreImg=True, isClosePopTry=True):
    """打开背包：优先点“道具”模板（找不到兜底固定坐标），等待“物品锁”出现确认打开。
    （原反编译为 checkStatusOk 装饰 + 空函数体，而 checkStatusOk 主逻辑因参数
      分支问题从不执行，导致背包从未打开、背包检测恒为 0；这里改为直接实现。）"""
    if isClosePopTry:
        closePop(deviceId, isOneTime=True)
    p = findPic(deviceId, preImgName, similar=0.8)
    if p is None:
        p = findPic(deviceId, preImgName, similar=0.7)
    if p:
        click(deviceId, p)
    else:
        # 兜底固定坐标：道具按钮（800x448 流坐标）
        click(deviceId, QPoint(704, 396))
    # 等待背包打开（“物品锁”出现），最多等 4 秒
    for _ in range(8):
        if findPic(deviceId, nextImgName, similar=0.8):
            return True
        time.sleep(0.5)
    logger.warning(f"{deviceId} 点击道具后未找到{nextImgName}，背包未打开")
    return False


def clickClosePkg(deviceId, preImgName='物品锁'):
    """
    关闭背包：背包已关则直接返回；否则优先点关闭模板，其次固定右上角关闭位。
    （原反编译为 checkStatusOk 装饰 + 空函数体，后置断言逻辑反转会导致
      关闭后等待“物品锁”出现而失败，这里改为稳妥的普通实现。）
    """
    if findPic(deviceId, "物品锁", similar=0.8) is None:
        return True
    for name in ("关闭弹窗", "左下角返回"):
        p = findPic(deviceId, name, similar=0.75)
        if p:
            click(deviceId, p)
            time.sleep(random.uniform(0.5, 1.0))
            return True
    click(deviceId, QPoint(668, 38), offset=QPoint(15, 10))
    time.sleep(random.uniform(0.5, 1.0))
    return True


@checkStatusOk
def clickBaiTan(deviceId, preImgName="摆摊按钮", middleImgNames=["普通摊位按钮", "坚持摆摊按钮"], nextImgName="收摊普通摊位", isClickPreImg=True):
    logger.info("运行clickBaiTan内部函数")
    return


@checkStatusOk
def doubleClickProduct(deviceId, preImgName=None, preFunc=None, nextImgName=None, isDoubleClickPreImg=True):
    logger.info("doubleClickUseProuct内部函数")
    return


@checkStatusOk
def hideMapLocation(deviceId, preImgName='地图-筛选', nextFunc=None, middleFunc=None):
    logger.info("hideMapLocation内部函数")
    return


@checkStatusOk
def clickFlyMap(deviceId, preImgName=None, nextFunc=None, isClickPreImg=True):
    logger.info("clickFlyMap内部函数")
    clickClosePkg(deviceId)
    return


@checkStatusOk
def clickOpenMap(deviceId, preImgName='打开地图', nextImgName='地图-筛选', isClickPreImg=True):
    logger.info("运行clickOpenMap内部函数")
    return


@checkStatusOk
def clickMapOpenShaiXuan(deviceId, preImgName='地图-筛选', nextImgName='地图-筛选-全部', isClickPreImg=True):
    logger.info("clickOpenShaiXuan内部函数")
    return


@checkStatusOk
def waitToMapPosition(deviceId, nextFunc=None, nextTotalT=30):
    logger.info("waitToPosition内部函数")
    return


@checkStatusOk
def clickNpcPerson(deviceId, clickPoint, nextImgName=None, middleImgNames=None, middleFunc=None, nextPerT=0.2):
    logger.info("clickNpc内部函数")
    if clickPoint != QPoint():
        click(deviceId, clickPoint)
    return


@checkStatusOk
def clickNpcDialog(deviceId, preImgName=None, nextImgName=None, nextFunc=None, isClickPreImg=True, isNotFirstCheckNext=True):
    logger.info("clickNpcDialog内部函数")
    return


@checkStatusOk
def clickNpcTaskPerson(deviceId, preFunc=None, nextImgName=None, nextTotalT=None):
    logger.info("clickNpcTaskPerson内部函数")
    return


@checkStatusOk
def clickChuanSong(deviceId, preImgName='传送', nextFunc=None, isClickPreImg=True, isClosePopTry=True, isNotFirstCheckNext=True):
    logger.info("运行clickChuanSong内部函数")
    return


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
def clickCloseHide(deviceId, preImgName='左下角返回', isClickPreImg=True, nextFunc=None):
    logger.info("clickCloseHide内部函数")
    return


@checkStatusOk
def clickOpenLeftTopMenu(deviceId, preImgName="菜单入口-打开", middleImgNames=["跑玉面板缩小"], nextImgName="菜单-指引", isClickPreImg=True, width=650):
    logger.info("运行clickOpenLeftTopMenu内部函数")
    return


@checkStatusOk
def clickCloseLeftTopMenu(deviceId, preImgName='菜单-指引'):
    click(deviceId, (QPoint(15 + scrcpyUtil.getNewMOffset(deviceId), 78)), offset=(QPoint(5, 1)))
    logger.info("运行clickCloseLeftTopMenu内部函数")
    return


def closePop(deviceId, left=330, top=0, width=DeviceWidth - 330, height=DeviceHeight, isOneTime=False, tryT=0):
    """
    关闭弹窗：点 关闭弹窗/关闭聊天/关闭活动弹窗/左下角返回 模板，
    若无可关内容则直接返回。
    （原反编译 return 截断了函数体且引用了未定义变量，已按原意图重建。）
    """
    if tryT > 3:
        return
    if const.gameType == "畅玩服":
        closeImgNames = ["关闭弹窗1"]
    else:
        closeImgNames = ["关闭弹窗", "关闭聊天", "关闭活动弹窗", "左下角返回"]
    closePopList = findPics(deviceId, closeImgNames, left=left, top=top,
                            width=width, height=height, withClick=True, clickWaitT=0.6)
    isMenuShow = findPic(deviceId, "菜单-指引") is not None
    if isMenuShow:
        click(deviceId, QPoint(15 + scrcpyUtil.getNewMOffset(deviceId), 78), offset=QPoint(5, 1))
        time.sleep(random.uniform(0.5, 0.8))
    if not closePopList and not isMenuShow and not isShowPopColorDK(deviceId, withClickDismiss=True):
        return
    if not isOneTime:
        closePop(deviceId, left=left, top=top, width=width, height=height,
                 isOneTime=isOneTime, tryT=tryT + 1)


@checkStatusOk
def clickOpenSetting(deviceId, preImgName='底部菜单-系统', nextImgName='系统-退出游戏', isClickPreImg=True, isClosePopTry=True):
    logger.info("运行clickOpenSetting内部函数")
    return


@checkStatusOk
def clickLogout(deviceId, preImgName='系统-退出游戏', nextImgName='系统-确认登出', isClickPreImg=True, isClickNextImg=True, isClosePopTry=True):
    logger.info("运行clickLogout内部函数")
    return


@checkStatusOk
def openSwitchRolePop(deviceId, preImgName='切换角色入口', nextImgName='角色选择标题', isClickPreImg=True, isClosePopTry=True):
    logger.info("运行openSwitchRolePop内部函数")
    return
