# -*- coding: utf-8 -*-
# Assembled from decompiled bytecode of map_action.pyc

import math
import random
import time
from xbw_features.qtcompat import QPoint
from loguru import logger
from xbw_features.common.util.log_util import orderLog
from xbw_features import const
from xbw_features.common.util.click_util import click
from xbw_features.common.util.color_util import isShowPopColorDK, waitCropFrameChange
from xbw_features.common.util.detect_position_util import detectPosition
from xbw_features.common.util.img_util import checkAtDaoJu, findPic, findPics, waitAssertFuncOk, findOneFromPics, waitAssertImgOk
from xbw_features.common.util.math_util import calculate_per_color, distance_between_points, isframeSame
from xbw_features.common.util.scrcpy_util import DeviceWidth, DeviceHeight, scrcpyUtil
from xbw_features.game_action.application_action import openHideAction
from xbw_features.game_action.unit.common_unit import doubleClickProduct, clickFlyMap, clickOpenPkg, hideMapLocation, clickOpenMap, closePop, clickMapOpenShaiXuan, waitToMapPosition, clickNpcPerson, clickNpcDialog, clickChuanSong, clickNpcTaskPerson

def _jianYeMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 453, 106, 10, 10)
    if abs(r - 150) < 20:
        if abs(g - 163) < 20:
            if abs(b - 130) < 20:
                return True
    return False


def _changAnMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 295, 190, 10, 10)
    if abs(r - 181) < 20:
        if abs(g - 166) < 20:
            if abs(b - 139) < 20:
                return True
    return False


def _changShouCunMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 365, 155, 5, 1)
    if abs(r - 224) < 30:
        if abs(g - 197) < 30:
            if abs(b - 190) < 30:
                return True
    return False


def _xiLiangNvGuoMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 428, 175, 10, 10)
    if abs(r - 214) < 20:
        if abs(g - 199) < 20:
            if abs(b - 189) < 20:
                return True
    return False


def _baoXiangGuoMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 231, 242, 4, 4)
    if abs(r - 245) < 20:
        if abs(g - 209) < 20:
            if abs(b - 146) < 20:
                return True
    return False


def _zhuZiGuoMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 251, 114, 5, 5)
    if abs(r - 226) < 20:
        if abs(g - 187) < 20:
            if abs(b - 103) < 20:
                return True
    return False


def _aoLaiMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 137, 360, 5, 5)
    if abs(r - 70) < 20:
        if abs(g - 165) < 20:
            if abs(b - 160) < 20:
                return True
    return False


def _changShouJiaoWaiMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 237, 315, 10, 10)
    if abs(r - 235) < 20:
        if abs(g - 198) < 20:
            if abs(b - 150) < 20:
                return True
    return False


def _daTangJingWaiMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 210, 189, 5, 5)
    if abs(r - 229) < 20:
        if abs(g - 164) < 20:
            if abs(b - 84) < 20:
                return True
    return False


def _moWangZhaiMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 339, 294, 5, 5)
    if abs(r - 185) < 20:
        if abs(g - 164) < 20:
            if abs(b - 117) < 20:
                return True
    return False


def _zhanSHenShanMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 340, 108, 5, 5)
    if abs(r - 254) < 20:
        if abs(g - 230) < 20:
            if abs(b - 208) < 20:
                return True
    return False


def _shenMuLinMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 346, 204, 3, 3)
    if abs(r - 242) < 20:
        if abs(g - 243) < 20:
            if abs(b - 230) < 20:
                return True
    return False


def _fuRongGuoMapIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 481, 335, 4, 4)
    if abs(r - 250) < 40:
        if abs(b - 148) < 40:
            return True
    return False


def _huaShengSiIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 300, 266, 2, 2)
    if abs(r - 173) < 20:
        if abs(g - 178) < 20:
            if abs(b - 133) < 20:
                return True
    return False


def _diFuIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 341, 312, 2, 2)
    if abs(r - 222) < 20:
        if abs(g - 140) < 20:
            if abs(b - 66) < 20:
                return True
    return False


def _daTangGuoJingIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 232, 221, 2, 2)
    if abs(r - 205) < 20:
        if abs(g - 170) < 20:
            if abs(b - 107) < 20:
                return True
    return False


def _puTuoShanIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 362, 94, 2, 2)
    if abs(r - 150) < 20:
        if abs(g - 203) < 20:
            if abs(b - 245) < 20:
                return True
    return False


def _jieYangShanIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 154, 219, 2, 2)
    if abs(r - 210) < 20:
        if abs(g - 232) < 20:
            if abs(b - 242) < 20:
                return True
    return False


def _huaGuoShanIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 504, 80, 2, 2)
    if abs(r - 180) < 20:
        if abs(g - 220) < 20:
            if abs(b - 232) < 20:
                return True
    return False


def _huanJingHuaGuoShanShanIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 177, 371, 2, 2)
    if abs(r - 235) < 20:
        if abs(g - 239) < 20:
            if abs(b - 245) < 20:
                return True
    return False


def _wanZiShanShanIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 300, 95, 2, 2)
    if abs(r - 233) < 20:
        if abs(g - 243) < 20:
            if abs(b - 245) < 20:
                return True
    return False


def _nvErCunIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 228, 402, 1, 1)
    if abs(r - 185) < 20:
        if abs(g - 224) < 20:
            if abs(b - 211) < 20:
                return True
    return False


def _dongHaiWanIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 445, 209, 2, 2)
    if abs(r - 57) < 20:
        if abs(g - 187) < 20:
            if abs(b - 200) < 20:
                return True
    return False


def _jiangNanYeWaiIsLightDK(deviceId):
    r, g, b = calculate_per_color(deviceId, 445, 209, 2, 2)
    if abs(r - 57) < 20:
        if abs(g - 187) < 20:
            if abs(b - 200) < 20:
                return True
    return False


def _isReturnTrueFuc(deviceId):
    return True


class AreaParams:
    def __init__(self, area, isFlyMap, isMapLightFunc, mapLeftBottomPoint, xyRange, xyWidthHeight):
        self.area = area
        self.isFlyMap = isFlyMap
        self.isMapLightFunc = isMapLightFunc
        self.mapLeftBottomPoint = mapLeftBottomPoint
        self.xyRange = xyRange
        self.xyWidthHeight = xyWidthHeight

def _changAnMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 271, 198, 10, 10)
    if abs(r - 184) < 20:
        if abs(g - 170) < 20:
            if abs(b - 143) < 20:
                return True
    return False


def _aoLaiMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 115, 364, 4, 4)
    if abs(r - 77) < 20:
        if abs(g - 165) < 20:
            if abs(b - 159) < 20:
                return True
    return False


def _huaGuoShanMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 521, 354, 4, 4)
    if abs(r - 14) < 20:
        if abs(g - 117) < 20:
            if abs(b - 164) < 20:
                return True
    return False


def _beiJuLuZhouMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 513, 87, 4, 4)
    if abs(r - 194) < 20:
        if abs(g - 211) < 20:
            if abs(b - 234) < 20:
                return True
    return False


def _longKuYiCengMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 93, 140, 2, 2)
    if abs(r - 240) < 20:
        if abs(g - 248) < 20:
            if abs(b - 254) < 20:
                return True
    return False


def _pengLaiXianDaoMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 518, 101, 4, 4)
    if abs(r - 225) < 20:
        if abs(g - 232) < 20:
            if abs(b - 245) < 20:
                return True
    return False


def _qiLinShanMapIsLightCW(deviceId):
    r, g, b = calculate_per_color(deviceId, 360, 102, 2, 2)
    if abs(r - 220) < 20:
        if abs(g - 210) < 20:
            if abs(b - 225) < 20:
                return True
    return False


def getMapParams(area):
    if const.gameType == "点卡服":
        for mapParams in mapParamsListDK:
            if mapParams.area == area:
                return mapParams

    else:
        if const.gameType == "畅玩服":
            for mapParams in mapParamsListCW:
                if mapParams.area == area:
                    return mapParams


def goToMapAction(deviceId, area, flyMapXY=None, curTryT=0):
        try:
            areaRes, xRes, yRes = detectPosition(deviceId)
            if area == areaRes:
                if flyMapXY is None:
                    return
                if distance_between_points(QPoint(xRes, yRes), flyMapXY) < 100:
                    return
            mapParams = getMapParams(area)
            if mapParams.isFlyMap:
                clickOpenPkg(deviceId)
                isArrive = False
                if flyMapXY:
                    isArrive = _feiXingQi(deviceId, area, flyMapXY)
                if not isArrive:
                    doubleClickProduct(deviceId, preImgName="飞行符", preFunc=lambda: checkAtDaoJu(deviceId), nextImgName="使用飞行符结果")
                    clickFlyMap(deviceId, preImgName=f"飞行符飞{area}", nextFunc=lambda: detectPosition(deviceId)[0] == area)
            if mapParams.area == "九黎城":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(171, 90))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickNpcAction(deviceId, getMapParams("大唐境外"), QPoint(176, 93), "点NPC对话-请引领我至九黎城", assertFunc=lambda: detectPosition(deviceId)[0] == "九黎城")
            elif mapParams.area == "长寿郊外":
                goToMapAction(deviceId, "长寿村", flyMapXY=QPoint(143, 5))
                goToPositionAction(deviceId, getMapParams("长寿村"), QPoint(143, 5))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "长寿郊外")
            elif mapParams.area == "大唐国境":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(10, 3))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐国境")
            elif mapParams.area == "魔王寨":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(5, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(55, 112))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "魔王寨")
            elif mapParams.area == "神木林":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(349, 69))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(349, 69))
                goToPositionAction(deviceId, getMapParams("战神山"), QPoint(17, 43))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "神木林")
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(350, 73), "点NPC对话-送我去战神山", assertFunc=lambda: detectPosition(deviceId)[0] == "战神山")
            elif mapParams.area == "芙蓉国":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(416, 270))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(416, 270))
            elif mapParams.area == "化生寺":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(509, 273))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(509, 273))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "化生寺")
            elif mapParams.area == "大唐官府":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(310, 273))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(310, 273))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐官府")
            elif mapParams.area == "地府":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(48, 325))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "地府")
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
            elif mapParams.area == "普陀山":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(221, 60))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐国境")
                clickNpcAction(deviceId, getMapParams("大唐国境"), QPoint(221, 60), "点NPC对话-送我到普陀山", assertFunc=lambda: detectPosition(deviceId)[0] == "普陀山")
            elif mapParams.area == "解阳山":
                goToMapAction(deviceId, "宝象国")
                goToPositionAction(deviceId, getMapParams("宝象国"), QPoint(131, 115))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "解阳山")
            elif mapParams.area == "花果山":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(215, 143))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "花果山")
            elif mapParams.area == "幻境花果山":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("花果山"), QPoint(142, 16))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "花果山")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "幻境花果山")
            elif mapParams.area == "无底洞":
                goToMapAction(deviceId, "宝象国")
                goToPositionAction(deviceId, getMapParams("宝象国"), QPoint(148, 9))
                goToPositionAction(deviceId, getMapParams("碗子山"), QPoint(26, 18))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "碗子山")
                clickNpcAction(deviceId, getMapParams("碗子山"), QPoint(26, 18), "点NPC对话-传送无底洞", assertFunc=lambda: detectPosition(deviceId)[0] == "无底洞")
            elif mapParams.area == "海底迷宫":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("花果山"), QPoint(100, 5))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "花果山")
                clickNpcAction(deviceId, getMapParams("花果山"), QPoint(100, 5), "点NPC对话-是的我要去", middleImgNames=['点NPC对话-我要做其他事情', '点NPC重叠-马猴'], assertFunc=lambda: detectPosition(deviceId)[0] == "花果山")
            elif mapParams.area == "地狱迷宫":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(48, 325))
                goToPositionAction(deviceId, getMapParams("地府"), QPoint(32, 108))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "地府")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "地府")
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
            elif mapParams.area == "女儿村":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(8, 141))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(8, 141))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "女儿村")
            elif mapParams.area == "东海渊":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(164, 15))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(165, 18))
                clickNpcAction(deviceId, getMapParams("傲来国"), QPoint(168, 16), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "东海湾")
            elif mapParams.area == "东海湾":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(164, 15))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(165, 18))
                clickNpcAction(deviceId, getMapParams("傲来国"), QPoint(168, 16), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "东海湾")
            elif mapParams.area == "月宫":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(52, 15))
                goToPositionAction(deviceId, getMapParams("长寿郊外"), QPoint(21, 58))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickNpcAction(deviceId, getMapParams("大唐境外"), QPoint(52, 15), "点NPC对话-是的我要去", middleImgNames=['点NPC对话-我要做其他事情'], assertFunc=lambda: detectPosition(deviceId)[0] == "长寿郊外")
                clickNpcAction(deviceId, getMapParams("长寿郊外"), QPoint(22, 59), "点NPC对话-是的我要去", middleImgNames=['点NPC对话-我要做其他事情'], assertFunc=lambda: detectPosition(deviceId)[0] == "天宫")
            elif mapParams.area == "龙宫":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(164, 15))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(165, 18))
                goToPositionAction(deviceId, getMapParams("东海湾"), QPoint(110, 91))
                clickNpcAction(deviceId, getMapParams("傲来国"), QPoint(168, 15), "点NPC对话-是的我要去", middleImgNames=['点NPC重叠-驿站老板'], assertFunc=lambda: detectPosition(deviceId)[0] == "东海湾")
                clickNpcAction(deviceId, getMapParams("东海湾"), QPoint(113, 88), "点NPC对话-送我到龙宫", assertFunc=lambda: detectPosition(deviceId)[0] == "龙宫")
            elif mapParams.area == "江南野外":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(541, 4))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(541, 4))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "江南野外")
            elif mapParams.area == "龙窟五层":
                goToMapAction(deviceId, "北俱芦洲")
                goToPositionAction(deviceId, getMapParams("北俱芦洲"), QPoint(12, 82))
                goToPositionAction(deviceId, getMapParams("龙窟一层"), QPoint(15, 70))
                goToPositionAction(deviceId, getMapParams("龙窟二层"), QPoint(22, 6))
                goToPositionAction(deviceId, getMapParams("龙窟三层"), QPoint(131, 26))
                goToPositionAction(deviceId, getMapParams("龙窟四层"), QPoint(125, 26))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
            elif mapParams.area == "龙窟六层":
                goToMapAction(deviceId, "北俱芦洲")
                goToPositionAction(deviceId, getMapParams("北俱芦洲"), QPoint(12, 82))
                goToPositionAction(deviceId, getMapParams("龙窟一层"), QPoint(15, 70))
                goToPositionAction(deviceId, getMapParams("龙窟二层"), QPoint(22, 6))
                goToPositionAction(deviceId, getMapParams("龙窟三层"), QPoint(131, 26))
                goToPositionAction(deviceId, getMapParams("龙窟四层"), QPoint(125, 26))
                goToPositionAction(deviceId, getMapParams("龙窟五层"), QPoint(51, 10))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
            elif mapParams.area == "龙窟一层":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("花果山"), QPoint(28, 98))
                goToPositionAction(deviceId, getMapParams("北俱芦洲"), QPoint(11, 80))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "花果山")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "龙窟一层")
                clickNpcAction(deviceId, getMapParams("花果山"), QPoint(28, 98), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "北俱芦洲")
            elif mapParams.area == "凤巢四层":
                goToMapAction(deviceId, "北俱芦洲")
                goToPositionAction(deviceId, getMapParams("北俱芦洲"), QPoint(85, 149))
                goToPositionAction(deviceId, getMapParams("凤巢一层"), QPoint(48, 6))
                goToPositionAction(deviceId, getMapParams("凤巢二层"), QPoint(122, 45))
                goToPositionAction(deviceId, getMapParams("凤巢三层"), QPoint(120, 5))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
            elif mapParams.area == "小西天":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(16, 100))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickNpcAction(deviceId, getMapParams("大唐境外"), QPoint(16, 106), "点NPC对话-快送我进去吧", assertFunc=lambda: detectPosition(deviceId)[0] == "小西天")
            elif mapParams.area == "子母河底":
                goToMapAction(deviceId, "西梁女国")
                goToPositionAction(deviceId, getMapParams("西梁女国"), QPoint(152, 12))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "子母河底")
            elif mapParams.area == "方寸山":
                goToMapAction(deviceId, "长寿村", flyMapXY=QPoint(108, 205))
                goToPositionAction(deviceId, getMapParams("长寿村"), QPoint(108, 205))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "方寸山")
            elif mapParams.area == "五庄观":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(8, 76))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(628, 75))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "五庄观")
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
            elif mapParams.area == "盘丝岭":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(8, 76))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(529, 112))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "盘丝岭")
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
            elif mapParams.area == "麒麟山":
                goToMapAction(deviceId, "朱紫国")
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(7, 109))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "麒麟山")
            elif mapParams.area == "青丘":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(154, 9))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐国境")
                clickNpcAction(deviceId, getMapParams("大唐国境"), QPoint(154, 9), "点NPC对话-好想去青丘看看哇", assertFunc=lambda: detectPosition(deviceId)[0] == "青丘")
            elif mapParams.area == "北俱芦洲":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(215, 143))
                goToPositionAction(deviceId, getMapParams("花果山"), QPoint(28, 98))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "花果山")
                clickNpcAction(deviceId, getMapParams("花果山"), QPoint(28, 98), "点NPC对话-是的我要去", middleImgNames=['点NPC重叠-花果山土地'], assertFunc=lambda: detectPosition(deviceId)[0] == "北俱芦洲")
            elif mapParams.area == "凌波城":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(170, 263))
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
                clickNpcAction(deviceId, getMapParams("大唐国境"), QPoint(174, 260), "点NPC对话-送我到凌波城", assertFunc=lambda: detectPosition(deviceId)[0] == "凌波城")
            elif mapParams.area == "狮驼岭":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(8, 49))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "狮驼岭")
            elif mapParams.area == "天机城":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(190, 9))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickNpcAction(deviceId, getMapParams("大唐境外"), QPoint(190, 9), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "天机城")
            elif mapParams.area == "五行山":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(48, 278))
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
                clickNpcAction(deviceId, getMapParams("大唐国境"), QPoint(48, 279), "点NPC对话-前往五行山", assertFunc=lambda: detectPosition(deviceId)[0] == "五行山")
            elif mapParams.area == "鬼市":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(48, 325))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "地府")
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
            elif mapParams.area == "伊阙龙门":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(541, 4))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(541, 4))
                goToPositionAction(deviceId, getMapParams("江南野外"), QPoint(146, 96))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "江南野外")
                clickNpcAction(deviceId, getMapParams("江南野外"), QPoint(146, 96), "点NPC对话-送我去伊阙龙门", assertFunc=lambda: detectPosition(deviceId)[0] == "伊阙龙门")
            elif mapParams.area == "女魃墓":
                goToMapAction(deviceId, "傲来国", flyMapXY=QPoint(164, 15))
                goToPositionAction(deviceId, getMapParams("傲来国"), QPoint(165, 18))
                clickNpcAction(deviceId, getMapParams("傲来国"), QPoint(168, 16), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "东海湾")
            elif mapParams.area == "墨家村":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(233, 110))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickNpcAction(deviceId, getMapParams("大唐境外"), QPoint(238, 112), "点NPC对话-送我到墨家村", assertFunc=lambda: detectPosition(deviceId)[0] == "墨家村")
            elif mapParams.area == "女娲神迹":
                goToMapAction(deviceId, "北俱芦洲")
                goToPositionAction(deviceId, getMapParams("北俱芦洲"), QPoint(17, 153))
                clickNpcAction(deviceId, getMapParams("北俱芦洲"), QPoint(14, 156), "点NPC对话-请送我进去", assertFunc=lambda: detectPosition(deviceId)[0] == "女娲神迹")
            elif mapParams.area == "小雷音寺":
                goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(4, 4))
                goToPositionAction(deviceId, getMapParams("大唐境外"), QPoint(16, 100))
                goToPositionAction(deviceId, getMapParams("小西天"), QPoint(26, 218))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐境外")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "小雷音寺")
                clickNpcAction(deviceId, getMapParams("大唐境外"), QPoint(16, 106), "点NPC对话-快送我进去吧", assertFunc=lambda: detectPosition(deviceId)[0] == "小西天")
            elif mapParams.area == "须弥东界":
                goToMapAction(deviceId, "宝象国")
                goToPositionAction(deviceId, getMapParams("宝象国"), QPoint(7, 61))
                goToPositionAction(deviceId, getMapParams("丝绸之路"), QPoint(214, 83))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "丝绸之路")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "须弥东界")
            elif mapParams.area == "银华境":
                goToMapAction(deviceId, "宝象国")
                goToPositionAction(deviceId, getMapParams("宝象国"), QPoint(7, 61))
                goToPositionAction(deviceId, getMapParams("丝绸之路"), QPoint(15, 6))
                goToPositionAction(deviceId, getMapParams("凌云渡"), QPoint(24, 11))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "丝绸之路")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "凌云渡")
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "银华境")
            elif mapParams.area == "弥勒山":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(10, 3))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(307, 92))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "大唐国境")
                clickNpcAction(deviceId, getMapParams("大唐国境"), QPoint(311, 93), "点NPC对话-麻烦小师父带路", assertFunc=lambda: detectPosition(deviceId)[0] == "弥勒山")
            elif mapParams.area == "无名鬼域":
                goToMapAction(deviceId, "长安城", flyMapXY=QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                goToPositionAction(deviceId, getMapParams("大唐国境"), QPoint(48, 325))
                goToPositionAction(deviceId, getMapParams("地府"), QPoint(29, 109))
                goToPositionAction(deviceId, getMapParams("地狱迷宫"), QPoint(11, 9))
                goToPositionAction(deviceId, getMapParams("地狱迷宫"), QPoint(112, 34))
                goToPositionAction(deviceId, getMapParams("地狱迷宫"), QPoint(110, 8))
                goToPositionAction(deviceId, getMapParams("地狱迷宫"), QPoint(96, 57))
                clickChuanSong(deviceId, nextFunc=lambda: detectPosition(deviceId)[0] == "地府")
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickChuanSong(deviceId, nextFunc=lambda: checkAtDaoJu(deviceId))
                clickNpcAction(deviceId, getMapParams("长安城"), QPoint(0, 0), "点NPC对话-是的我要去", assertFunc=lambda: detectPosition(deviceId)[0] == "大唐国境", isYiZhan=True)
                clickNpcAction(deviceId, getMapParams("地狱迷宫"), QPoint(92, 58), "点NPC对话-我就是来探险的请送我进去", assertFunc=lambda: detectPosition(deviceId)[0] == "无名鬼域")

        except RuntimeError:
            curTryT += 1
            logger.warning(f"去地图异常，第{curTryT}次重试")
            if curTryT <= 10:
                goToMapAction(deviceId, area, flyMapXY=flyMapXY, curTryT=curTryT)
        except Exception as e:
            logger.debug(f"goToMapDKAction Exception: {e}")


def goToPositionAction(deviceId, mapParams, point, curTryT=0):
        try:
            if _isNearToPoint(deviceId, point):
                if not (mapParams.area == "长安城" and point == QPoint(274, 43)):
                    return
            clickOpenMap(deviceId)
            doHideMapLocation(deviceId, mapParams)
            clickMap4_5Time(deviceId, point, mapParams)
            time.sleep(random.uniform(0.8, 3.0))
            closePop(deviceId, isOneTime=True)
            if mapParams.area == "大唐境外" and point == QPoint(628, 75):
                if findPic(deviceId, "地图-筛选"):
                    click(deviceId, QPoint(730, 120))
            waitToMapPosition(deviceId, nextFunc=lambda: _isNearToPoint(deviceId, point))
            waitAssertFuncOk(deviceId, func=lambda: _isNearToPoint(deviceId, point), perT=0.2, totalT=0.8)
        except RuntimeError:
            curTryT += 1
            logger.warning(f"位置移动goToPositionAction异常，第{curTryT}次重试")
            if curTryT <= 10:
                goToPositionAction(deviceId, mapParams, point, curTryT=curTryT)
        except Exception as e:
            logger.debug(f"goToPositionDK Exception: {e}")


def doHideMapLocation(deviceId, mapParams):
    area = mapParams.area
    map_set = hasCloseSaiXuanMaps.setdefault(deviceId, set())
    if area not in map_set:
        _doHideLocation(deviceId)
        if area != "龙窟六层":
            map_set.add(area)


def resetDeviceSaiXuanMap(deviceId):
    if hasCloseSaiXuanMaps and deviceId in hasCloseSaiXuanMaps:
        hasCloseSaiXuanMaps[deviceId].clear()
    else:
        hasCloseSaiXuanMaps[deviceId] = set()


def clickNpcAction(deviceId, mapParams, npcPoint, clickPopImgName, middleImgNames=["点NPC对话-我要做其他事情"], assertImgName=None, assertFunc=None, withClickDismiss=False, isYiZhan=False, curTryT=0):
    try:
        if not mapParams.area == "长安城" or isYiZhan:
            if mapParams.area == "长寿村":
                openHideAction(deviceId)
            if isYiZhan:
                goToPositionAction(deviceId, getMapParams("长安城"), QPoint(274, 43))
                findOneFromPics(deviceId, ["驿站老板1", "驿站老板2", "驿站老板3", "驿站老板4"], withClick=True, similar=0.75)
            if npcPoint.y() <= 13 or npcPoint.x() <= 23:
                time.sleep(1.5)
        clickPoint = _getNpcAbsolutePoint(deviceId, mapParams, npcPoint)
        clickNpcPerson(deviceId, clickPoint, middleImgNames=middleImgNames, middleFunc=(lambda: isShowPopColorDK(deviceId, withClickDismiss=withClickDismiss)), nextImgName=clickPopImgName)
        clickNpcDialog(deviceId, preImgName=clickPopImgName, nextImgName=assertImgName, nextFunc=assertFunc)
    except RuntimeError:
        curTryT += 1
        logger.warning(f"点NPC clickNpcAction异常，第{curTryT}次重试")
        if curTryT <= 10:
            clickNpcAction(deviceId, mapParams, npcPoint, clickPopImgName, middleImgNames=middleImgNames, assertImgName=assertImgName, assertFunc=assertFunc, withClickDismiss=withClickDismiss, isYiZhan=isYiZhan, curTryT=curTryT)
    except Exception as e:
        try:
            logger.debug(f"clickNpcAction Exception: {e}")
        finally:
            e = None
            del e


def _feiXingQi(deviceId, area, flyMapXY):
        if area == "宝象国" or area == "西梁女国" or area == "建邺城":
            return
        whatColor = ""
        if area == "长安城":
            whatColor = "红"
            if flyMapXY == QPoint(349, 69) or flyMapXY == QPoint(509, 273) or flyMapXY == QPoint(416, 270) or flyMapXY == QPoint(310, 273):
                whatColor = "蓝"
        elif area == "长寿村":
            whatColor = "绿"
        elif area == "傲来国":
            whatColor = "黄"
        elif area == "朱紫国":
            whatColor = "白"
        checkAtDaoJu(deviceId)
        isHasFeiXingQi = findPic(deviceId, f"飞行旗{whatColor}色")
        if isHasFeiXingQi:
            doubleClickProduct(deviceId, preImgName=f"飞行旗{whatColor}色", preFunc=lambda: checkAtDaoJu(deviceId), nextImgName="使用飞行旗结果")
            redPoints = findPics(deviceId, ["飞行旗红点"], similar=0.95)
            clickMapPoint = _getClickXYFromMapXY(flyMapXY, getMapParams(area))
            bestNearRedPoint = _findBestNearRedPoint(redPoints, clickMapPoint)
            click(deviceId, bestNearRedPoint + QPoint(5, 5))
            time.sleep(random.uniform(0.5, 0.8))
            findPic(deviceId, "飞行旗大红点", left=bestNearRedPoint.x() - 50, top=bestNearRedPoint.y() - 50,
                    width=min(150, 800 - (bestNearRedPoint.x() - 50)), height=min(150, 448 - (bestNearRedPoint.y() - 50)),
                    withClick=True, similar=0.9)
            closePop(deviceId, isOneTime=True)
            isArrive = waitAssertFuncOk(deviceId, lambda: detectPosition(deviceId)[0] == area)
            return isArrive
        return False


def _findBestNearRedPoint(redPoints, clickMapPoint):
    bestNearPoint = None
    minDistance = 10000
    for redP in redPoints:
        distance = distance_between_points(redP, clickMapPoint)
        if distance < minDistance:
            bestNearPoint = redP
            minDistance = distance
    return bestNearPoint


def _getNpcAbsolutePoint(deviceId, mapParams, npcPoint):
    area, x, y = detectPosition(deviceId)
    clickPoint = QPoint(DeviceWidth / 2, DeviceHeight / 2)
    if x:
        if y:
            xOffset = x - npcPoint.x()
            yOffset = y - npcPoint.y()
            clickX = clickPoint.x() - int(xOffset * 16.6)
            clickY = clickPoint.y() + int(yOffset * 16.6)
            if x <= 23:
                clickX = int(npcPoint.x() * 16.6)
            else:
                if x >= mapParams.xyRange.x() - 23:
                    clickX = DeviceWidth - int((mapParams.xyRange.x() - npcPoint.x()) * 16.6)
                elif y <= 13:
                    clickY = DeviceHeight - int(npcPoint.y() * 16.6)
                else:
                    if y >= mapParams.xyRange.y() - 13:
                        clickY = int((mapParams.xyRange.y() - npcPoint.y()) * 16.6)
            clickPoint = QPoint(clickX, clickY)
    return clickPoint


def _doHideLocation(deviceId):
    clickMapOpenShaiXuan(deviceId)
    quanBuPoint = findPic(deviceId, "地图-筛选-全部")
    findPics(deviceId, imgNames=["勾选框"], withClick=True, left=(quanBuPoint.x() - 55), top=(quanBuPoint.y() + 25), width=(800 - (quanBuPoint.x() - 55)), height=(440 - (quanBuPoint.y() + 25)), similar=0.9)
    click(deviceId, (QPoint(400, 225)), offset=(QPoint(50, 50)))
    time.sleep(random.uniform(0.3, 0.5))


def _isNearToPoint(deviceId, point):
    area, x, y = detectPosition(deviceId)
    if x:
        if abs(x - point.x()) <= 5:
            if y:
                if abs(y - point.y()) <= 5:
                    return True
    return False


def clickMap4_5Time(deviceId, point, mapParams):
    clickPoint = _getClickXYFromMapXY(point, mapParams)
    genPoints = _gen_click_points(clickPoint.x(), clickPoint.y())
    for index in range(len(genPoints)):
        genP = genPoints[index]
        click(deviceId, genP, offset=(QPoint()))
        waitLv = len(genPoints) - index
        time.sleep(random.uniform(0.12, 0.25) * waitLv)


def _getClickXYFromMapXY(point, mapParams):
    xMapLv = mapParams.xyWidthHeight.x() / mapParams.xyRange.x()
    yMapLv = mapParams.xyWidthHeight.y() / mapParams.xyRange.y()
    clickX = int(point.x() * xMapLv)
    clickY = -int(point.y() * yMapLv)
    clickPoint = mapParams.mapLeftBottomPoint + QPoint(clickX, clickY)
    return clickPoint


def _waitIsToPoint(deviceId, point):
        while True:
            area, x, y = detectPosition(deviceId)
            if x == point.x() and y == point.y():
                return True


def _gen_click_points(center_x, center_y):
    click_cnt = random.choice([4, 5])
    base_radius = [
     20, 8, 5, 3, 1]
    # 反编译残留：(-click_cnt)[:None] 对整数切片会 TypeError，
    # 原意为取倒数 click_cnt 个半径（4 次 -> [8,5,3,1]，5 次 -> 全部）
    target_r = base_radius[-click_cnt:]
    points = []
    for r in target_r:
        rand_r = round(r * random.uniform(0.8, 1.2))
        angle = random.uniform(0, 2 * math.pi)
        dx = rand_r * math.cos(angle)
        dy = rand_r * math.sin(angle)
        x = round(center_x + dx)
        y = round(center_y + dy)
        points.append(QPoint(x, y))
    return points


def isMapStopHuangDong(deviceId):
    isStopHuangDong = False
    lastFrame = None
    for i in range(2):
        curFrame = scrcpyUtil.getFrame(deviceId)[279:318, 744:783]
        if lastFrame is not None:
            if isframeSame(curFrame, lastFrame, similar=0.98):
                isStopHuangDong = True
                logger.info(f"{deviceId}地图没晃动了")
                break
            else:
                logger.info(f"{deviceId}地图晃动中")
        lastFrame = curFrame
        time.sleep(0.2)
    else:
        return isStopHuangDong


# module-level constants evaluated from bytecode

DeviceWidth = 800
DeviceHeight = 448
jianYeMapParamsDK = AreaParams(
 area="建邺城",
 isFlyMap=True,
 isMapLightFunc=_jianYeMapIsLightDK,
 mapLeftBottomPoint=QPoint(47, 366),
 xyRange=QPoint(287, 143),
 xyWidthHeight=QPoint(591, 294)
)
changAnChengMapParamsDK = AreaParams(
 area="长安城",
 isFlyMap=True,
 isMapLightFunc=_changAnMapIsLightDK,
 mapLeftBottomPoint=QPoint(53, 365),
 xyRange=QPoint(549, 279),
 xyWidthHeight=QPoint(578, 292)
)
changShouCunMapParamsDK = AreaParams(
 area="长寿村",
 isFlyMap=True,
 isMapLightFunc=_changShouCunMapIsLightDK,
 mapLeftBottomPoint=QPoint(226, 370),
 xyRange=QPoint(159, 209),
 xyWidthHeight=QPoint(233, 303)
)
xiLiangNvGuoMapParamsDK = AreaParams(
 area="西梁女国",
 isFlyMap=True,
 isMapLightFunc=_xiLiangNvGuoMapIsLightDK,
 mapLeftBottomPoint=QPoint(149, 364),
 xyRange=QPoint(163, 123),
 xyWidthHeight=QPoint(387, 290)
)
baoXiangGuoMapParamsDK = AreaParams(
 area="宝象国",
 isFlyMap=True,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(158, 357),
 xyRange=QPoint(159, 119),
 xyWidthHeight=QPoint(370, 276)
)
zhuZiGuoMapParamsDK = AreaParams(
 area="朱紫国",
 isFlyMap=True,
 isMapLightFunc=_zhuZiGuoMapIsLightDK,
 mapLeftBottomPoint=QPoint(102, 370),
 xyRange=QPoint(191, 119),
 xyWidthHeight=QPoint(482, 302)
)
aoLaiGuoMapParamsDK = AreaParams(
 area="傲来国",
 isFlyMap=True,
 isMapLightFunc=_aoLaiMapIsLightDK,
 mapLeftBottomPoint=QPoint(123, 366),
 xyRange=QPoint(223, 150),
 xyWidthHeight=QPoint(440, 295)
)
changShouJiaoWaiMapParamsDK = AreaParams(
 area="长寿郊外",
 isFlyMap=False,
 isMapLightFunc=_changShouJiaoWaiMapIsLightDK,
 mapLeftBottomPoint=QPoint(175, 365),
 xyRange=QPoint(191, 167),
 xyWidthHeight=QPoint(335, 292)
)
daTangJingWaiMapParamsDK = AreaParams(
 area="大唐境外",
 isFlyMap=False,
 isMapLightFunc=_daTangJingWaiMapIsLightDK,
 mapLeftBottomPoint=QPoint(78, 284),
 xyRange=QPoint(639, 118),
 xyWidthHeight=QPoint(641, 120)
)
moWangZhaiMapParamsDK = AreaParams(
 area="魔王寨",
 isFlyMap=False,
 isMapLightFunc=_moWangZhaiMapIsLightDK,
 mapLeftBottomPoint=QPoint(141, 370),
 xyRange=QPoint(119, 89),
 xyWidthHeight=QPoint(403, 302)
)
zhanShenShanMapParamsDK = AreaParams(
 area="战神山",
 isFlyMap=False,
 isMapLightFunc=_zhanSHenShanMapIsLightDK,
 mapLeftBottomPoint=QPoint(194, 401),
 xyRange=QPoint(127, 157),
 xyWidthHeight=QPoint(297, 365)
)
shenMuLinMapParamsDK = AreaParams(
 area="神木林",
 isFlyMap=False,
 isMapLightFunc=_shenMuLinMapIsLightDK,
 mapLeftBottomPoint=QPoint(255, 392),
 xyRange=QPoint(87, 174),
 xyWidthHeight=QPoint(175, 346)
)
fuRongGuoMapParamsDK = AreaParams(
 area="芙蓉国",
 isFlyMap=False,
 isMapLightFunc=_fuRongGuoMapIsLightDK,
 mapLeftBottomPoint=QPoint(78, 401),
 xyRange=QPoint(103, 71),
 xyWidthHeight=QPoint(529, 364)
)
huaShengSiMapParamsDK = AreaParams(
 area="化生寺",
 isFlyMap=False,
 isMapLightFunc=_huaShengSiIsLightDK,
 mapLeftBottomPoint=QPoint(146, 365),
 xyRange=QPoint(127, 95),
 xyWidthHeight=QPoint(393, 293)
)
daTangGuanFuMapParamsDK = AreaParams(
 area="大唐官府",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
diFuMapParamsDK = AreaParams(
 area="地府",
 isFlyMap=False,
 isMapLightFunc=_diFuIsLightDK,
 mapLeftBottomPoint=QPoint(146, 369),
 xyRange=QPoint(159, 119),
 xyWidthHeight=QPoint(403, 300)
)
daTangGuoJingMapParamsDK = AreaParams(
 area="大唐国境",
 isFlyMap=False,
 isMapLightFunc=_daTangGuoJingIsLightDK,
 mapLeftBottomPoint=QPoint(153, 399),
 xyRange=QPoint(351, 335),
 xyWidthHeight=QPoint(380, 360)
)
puTuoShanMapParamsDK = AreaParams(
 area="普陀山",
 isFlyMap=False,
 isMapLightFunc=_puTuoShanIsLightDK,
 mapLeftBottomPoint=QPoint(146, 366),
 xyRange=QPoint(95, 71),
 xyWidthHeight=QPoint(394, 295)
)
jieYangMapParamsDK = AreaParams(
 area="解阳山",
 isFlyMap=False,
 isMapLightFunc=_jieYangShanIsLightDK,
 mapLeftBottomPoint=QPoint(145, 368),
 xyRange=QPoint(127, 95),
 xyWidthHeight=QPoint(396, 297)
)
huaGuoShanMapParamsDK = AreaParams(
 area="花果山",
 isFlyMap=False,
 isMapLightFunc=_huaGuoShanIsLightDK,
 mapLeftBottomPoint=QPoint(148, 366),
 xyRange=QPoint(159, 119),
 xyWidthHeight=QPoint(390, 293)
)
huanJingHuaGuoShanMapParamsDK = AreaParams(
 area="幻境花果山",
 isFlyMap=False,
 isMapLightFunc=_huanJingHuaGuoShanShanIsLightDK,
 mapLeftBottomPoint=QPoint(154, 390),
 xyRange=QPoint(135, 123),
 xyWidthHeight=QPoint(377, 342)
)
wanZiShanMapParamsDK = AreaParams(
 area="碗子山",
 isFlyMap=False,
 isMapLightFunc=_wanZiShanShanIsLightDK,
 mapLeftBottomPoint=QPoint(260, 383),
 xyRange=QPoint(95, 191),
 xyWidthHeight=QPoint(165, 328)
)
wuDiDongMapParamsDK = AreaParams(
 area="无底洞",
 isFlyMap=False,
 isMapLightFunc=_wanZiShanShanIsLightDK,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
haiDiMiGongMapParamsDK = AreaParams(
 area="海底迷宫",
 isFlyMap=False,
 isMapLightFunc=_wanZiShanShanIsLightDK,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
diYuMiGongMapParamsDK = AreaParams(
 area="地狱迷宫",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(146, 366),
 xyRange=QPoint(119, 89),
 xyWidthHeight=QPoint(393, 294)
)
nvErCunMapParamsDK = AreaParams(
 area="女儿村",
 isFlyMap=False,
 isMapLightFunc=_nvErCunIsLightDK,
 mapLeftBottomPoint=QPoint(175, 406),
 xyRange=QPoint(127, 143),
 xyWidthHeight=QPoint(334, 374)
)
dongHaiYuanMapParamsDK = AreaParams(
 area="东海渊",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
dongHaiWanMapParamsDK = AreaParams(
 area="东海湾",
 isFlyMap=False,
 isMapLightFunc=_dongHaiWanIsLightDK,
 mapLeftBottomPoint=QPoint(195, 366),
 xyRange=QPoint(119, 119),
 xyWidthHeight=QPoint(294, 293)
)
yueGongMapParamsDK = AreaParams(
 area="月宫",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
longGongMapParamsDK = AreaParams(
 area="龙宫",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
jiangNanYeWaiMapParamsDK = AreaParams(
 area="江南野外",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(189, 332),
 xyRange=QPoint(159, 119),
 xyWidthHeight=QPoint(308, 227)
)
longKuWuCengMapParamsDK = AreaParams(
 area="龙窟五层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(71, 358),
 xyRange=QPoint(139, 71),
 xyWidthHeight=QPoint(543, 279)
)
longKuLiuCengMapParamsDK = AreaParams(
 area="龙窟六层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(73, 374),
 xyRange=QPoint(137, 79),
 xyWidthHeight=QPoint(539, 310)
)
longKuYiCengMapParamsDK = AreaParams(
 area="龙窟一层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(72, 369),
 xyRange=QPoint(165, 92),
 xyWidthHeight=QPoint(541, 301)
)
longKuErCengMapParamsDK = AreaParams(
 area="龙窟二层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(70, 365),
 xyRange=QPoint(135, 72),
 xyWidthHeight=QPoint(546, 292)
)
longKuSanCengMapParamsDK = AreaParams(
 area="龙窟三层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(69, 376),
 xyRange=QPoint(145, 83),
 xyWidthHeight=QPoint(548, 314)
)
longKuSiCengMapParamsDK = AreaParams(
 area="龙窟四层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(67, 356),
 xyRange=QPoint(141, 70),
 xyWidthHeight=QPoint(551, 274)
)
fengChaoSanCengMapParamsDK = AreaParams(
 area="凤巢三层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(126, 340),
 xyRange=QPoint(127, 71),
 xyWidthHeight=QPoint(434, 243)
)
fengChaoSiCengMapParamsDK = AreaParams(
 area="凤巢四层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(126, 340),
 xyRange=QPoint(127, 71),
 xyWidthHeight=QPoint(434, 243)
)
fengChaoErCengMapParamsDK = AreaParams(
 area="凤巢二层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(125, 340),
 xyRange=QPoint(127, 71),
 xyWidthHeight=QPoint(435, 243)
)
fengChaoYiCengMapParamsDK = AreaParams(
 area="凤巢一层",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(124, 341),
 xyRange=QPoint(127, 71),
 xyWidthHeight=QPoint(437, 245)
)
xiaoXiTianMapParamsDK = AreaParams(
 area="小西天",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(210, 417),
 xyRange=QPoint(159, 239),
 xyWidthHeight=QPoint(266, 397)
)
ziMuHeDiMapParamsDK = AreaParams(
 area="子母河底",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(146, 366),
 xyRange=QPoint(127, 95),
 xyWidthHeight=QPoint(393, 294)
)
fangCunShanParamsDK = AreaParams(
 area="方寸山",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
wuZhuangGuanParamsDK = AreaParams(
 area="五庄观",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
panSiLingParamsDK = AreaParams(
 area="盘丝岭",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
qiLinShanParamsDK = AreaParams(
 area="麒麟山",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(142, 364),
 xyRange=QPoint(190, 142),
 xyWidthHeight=QPoint(401, 291)
)
qingQiuParamsDK = AreaParams(
 area="青丘",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(219, 411),
 xyRange=QPoint(127, 199),
 xyWidthHeight=QPoint(247, 384)
)
beiJuLuZhouMapParamsDK = AreaParams(
 area="北俱芦洲",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(145, 367),
 xyRange=QPoint(227, 169),
 xyWidthHeight=QPoint(394, 297)
)
lingBoChengParamsDK = AreaParams(
 area="凌波城",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
shiTuoLingParamsDK = AreaParams(
 area="狮驼岭",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(143, 368),
 xyRange=QPoint(131, 97),
 xyWidthHeight=QPoint(399, 299)
)
tianJiChengParamsDK = AreaParams(
 area="天机城",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
wuXingShanParamsDK = AreaParams(
 area="五行山",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
guiShiParamsDK = AreaParams(
 area="鬼市",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
yiQueLongMengParamsDK = AreaParams(
 area="伊阙龙门",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(257, 364),
 xyRange=QPoint(53, 91),
 xyWidthHeight=QPoint(171, 290)
)
nvBaMuParamsDK = AreaParams(
 area="女魃墓",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
moJiaCunParamsDK = AreaParams(
 area="墨家村",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
jiuLiChengParamsDK = AreaParams(
 area="九黎城",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(0, 0),
 xyRange=QPoint(0, 0),
 xyWidthHeight=QPoint(0, 0)
)
changAnJiuDianParamsDK = AreaParams(
 area="长安酒店",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(154, 359),
 xyRange=QPoint(66, 49),
 xyWidthHeight=QPoint(377, 280)
)
nvWaShenJiParamsDK = AreaParams(
 area="女娲神迹",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(145, 366),
 xyRange=QPoint(191, 143),
 xyWidthHeight=QPoint(394, 295)
)
siChouZhiLuParamsDK = AreaParams(
 area="丝绸之路",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(93, 270),
 xyRange=QPoint(639, 95),
 xyWidthHeight=QPoint(612, 92)
)
xiaoLeiYinSiParamsDK = AreaParams(
 area="小雷音寺",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(92, 406),
 xyRange=QPoint(191, 143),
 xyWidthHeight=QPoint(501, 375)
)
xuMiDongJieParamsDK = AreaParams(
 area="须弥东界",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(237, 406),
 xyRange=QPoint(112, 200),
 xyWidthHeight=QPoint(211, 374)
)
yinHuaJingParamsDK = AreaParams(
 area="银华境",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(184, 398),
 xyRange=QPoint(202, 57),
 xyWidthHeight=QPoint(319, 92)
)
miLeShanParamsDK = AreaParams(
 area="弥勒山",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(134, 361),
 xyRange=QPoint(174, 119),
 xyWidthHeight=QPoint(417, 285)
)
lingYunDuParamsDK = AreaParams(
 area="凌云渡",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(246, 398),
 xyRange=QPoint(119, 223),
 xyWidthHeight=QPoint(193, 357)
)
wuMingGuiYuParamsDK = AreaParams(
 area="无名鬼域",
 isFlyMap=False,
 isMapLightFunc=_isReturnTrueFuc,
 mapLeftBottomPoint=QPoint(190, 334),
 xyRange=QPoint(191, 142),
 xyWidthHeight=QPoint(306, 230)
)
mapParamsListDK = [
 AreaParams(
  area="建邺城",
  isFlyMap=True,
  isMapLightFunc=_jianYeMapIsLightDK,
  mapLeftBottomPoint=QPoint(47, 366),
  xyRange=QPoint(287, 143),
  xyWidthHeight=QPoint(591, 294)
 ),
 AreaParams(
  area="九黎城",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="长安城",
  isFlyMap=True,
  isMapLightFunc=_changAnMapIsLightDK,
  mapLeftBottomPoint=QPoint(53, 365),
  xyRange=QPoint(549, 279),
  xyWidthHeight=QPoint(578, 292)
 ),
 AreaParams(
  area="长寿村",
  isFlyMap=True,
  isMapLightFunc=_changShouCunMapIsLightDK,
  mapLeftBottomPoint=QPoint(226, 370),
  xyRange=QPoint(159, 209),
  xyWidthHeight=QPoint(233, 303)
 ),
 AreaParams(
  area="西梁女国",
  isFlyMap=True,
  isMapLightFunc=_xiLiangNvGuoMapIsLightDK,
  mapLeftBottomPoint=QPoint(149, 364),
  xyRange=QPoint(163, 123),
  xyWidthHeight=QPoint(387, 290)
 ),
 AreaParams(
  area="宝象国",
  isFlyMap=True,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(158, 357),
  xyRange=QPoint(159, 119),
  xyWidthHeight=QPoint(370, 276)
 ),
 AreaParams(
  area="朱紫国",
  isFlyMap=True,
  isMapLightFunc=_zhuZiGuoMapIsLightDK,
  mapLeftBottomPoint=QPoint(102, 370),
  xyRange=QPoint(191, 119),
  xyWidthHeight=QPoint(482, 302)
 ),
 AreaParams(
  area="傲来国",
  isFlyMap=True,
  isMapLightFunc=_aoLaiMapIsLightDK,
  mapLeftBottomPoint=QPoint(123, 366),
  xyRange=QPoint(223, 150),
  xyWidthHeight=QPoint(440, 295)
 ),
 AreaParams(
  area="长寿郊外",
  isFlyMap=False,
  isMapLightFunc=_changShouJiaoWaiMapIsLightDK,
  mapLeftBottomPoint=QPoint(175, 365),
  xyRange=QPoint(191, 167),
  xyWidthHeight=QPoint(335, 292)
 ),
 AreaParams(
  area="大唐境外",
  isFlyMap=False,
  isMapLightFunc=_daTangJingWaiMapIsLightDK,
  mapLeftBottomPoint=QPoint(78, 284),
  xyRange=QPoint(639, 118),
  xyWidthHeight=QPoint(641, 120)
 ),
 AreaParams(
  area="魔王寨",
  isFlyMap=False,
  isMapLightFunc=_moWangZhaiMapIsLightDK,
  mapLeftBottomPoint=QPoint(141, 370),
  xyRange=QPoint(119, 89),
  xyWidthHeight=QPoint(403, 302)
 ),
 AreaParams(
  area="战神山",
  isFlyMap=False,
  isMapLightFunc=_zhanSHenShanMapIsLightDK,
  mapLeftBottomPoint=QPoint(194, 401),
  xyRange=QPoint(127, 157),
  xyWidthHeight=QPoint(297, 365)
 ),
 AreaParams(
  area="神木林",
  isFlyMap=False,
  isMapLightFunc=_shenMuLinMapIsLightDK,
  mapLeftBottomPoint=QPoint(255, 392),
  xyRange=QPoint(87, 174),
  xyWidthHeight=QPoint(175, 346)
 ),
 AreaParams(
  area="芙蓉国",
  isFlyMap=False,
  isMapLightFunc=_fuRongGuoMapIsLightDK,
  mapLeftBottomPoint=QPoint(78, 401),
  xyRange=QPoint(103, 71),
  xyWidthHeight=QPoint(529, 364)
 ),
 AreaParams(
  area="化生寺",
  isFlyMap=False,
  isMapLightFunc=_huaShengSiIsLightDK,
  mapLeftBottomPoint=QPoint(146, 365),
  xyRange=QPoint(127, 95),
  xyWidthHeight=QPoint(393, 293)
 ),
 AreaParams(
  area="地府",
  isFlyMap=False,
  isMapLightFunc=_diFuIsLightDK,
  mapLeftBottomPoint=QPoint(146, 369),
  xyRange=QPoint(159, 119),
  xyWidthHeight=QPoint(403, 300)
 ),
 AreaParams(
  area="大唐国境",
  isFlyMap=False,
  isMapLightFunc=_daTangGuoJingIsLightDK,
  mapLeftBottomPoint=QPoint(153, 399),
  xyRange=QPoint(351, 335),
  xyWidthHeight=QPoint(380, 360)
 ),
 AreaParams(
  area="普陀山",
  isFlyMap=False,
  isMapLightFunc=_puTuoShanIsLightDK,
  mapLeftBottomPoint=QPoint(146, 366),
  xyRange=QPoint(95, 71),
  xyWidthHeight=QPoint(394, 295)
 ),
 AreaParams(
  area="解阳山",
  isFlyMap=False,
  isMapLightFunc=_jieYangShanIsLightDK,
  mapLeftBottomPoint=QPoint(145, 368),
  xyRange=QPoint(127, 95),
  xyWidthHeight=QPoint(396, 297)
 ),
 AreaParams(
  area="花果山",
  isFlyMap=False,
  isMapLightFunc=_huaGuoShanIsLightDK,
  mapLeftBottomPoint=QPoint(148, 366),
  xyRange=QPoint(159, 119),
  xyWidthHeight=QPoint(390, 293)
 ),
 AreaParams(
  area="幻境花果山",
  isFlyMap=False,
  isMapLightFunc=_huanJingHuaGuoShanShanIsLightDK,
  mapLeftBottomPoint=QPoint(154, 390),
  xyRange=QPoint(135, 123),
  xyWidthHeight=QPoint(377, 342)
 ),
 AreaParams(
  area="碗子山",
  isFlyMap=False,
  isMapLightFunc=_wanZiShanShanIsLightDK,
  mapLeftBottomPoint=QPoint(260, 383),
  xyRange=QPoint(95, 191),
  xyWidthHeight=QPoint(165, 328)
 ),
 AreaParams(
  area="无底洞",
  isFlyMap=False,
  isMapLightFunc=_wanZiShanShanIsLightDK,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="海底迷宫",
  isFlyMap=False,
  isMapLightFunc=_wanZiShanShanIsLightDK,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="地狱迷宫",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(146, 366),
  xyRange=QPoint(119, 89),
  xyWidthHeight=QPoint(393, 294)
 ),
 AreaParams(
  area="女儿村",
  isFlyMap=False,
  isMapLightFunc=_nvErCunIsLightDK,
  mapLeftBottomPoint=QPoint(175, 406),
  xyRange=QPoint(127, 143),
  xyWidthHeight=QPoint(334, 374)
 ),
 AreaParams(
  area="东海渊",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="东海湾",
  isFlyMap=False,
  isMapLightFunc=_dongHaiWanIsLightDK,
  mapLeftBottomPoint=QPoint(195, 366),
  xyRange=QPoint(119, 119),
  xyWidthHeight=QPoint(294, 293)
 ),
 AreaParams(
  area="月宫",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="龙宫",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="江南野外",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(189, 332),
  xyRange=QPoint(159, 119),
  xyWidthHeight=QPoint(308, 227)
 ),
 AreaParams(
  area="龙窟五层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(71, 358),
  xyRange=QPoint(139, 71),
  xyWidthHeight=QPoint(543, 279)
 ),
 AreaParams(
  area="龙窟六层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(73, 374),
  xyRange=QPoint(137, 79),
  xyWidthHeight=QPoint(539, 310)
 ),
 AreaParams(
  area="凤巢三层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(126, 340),
  xyRange=QPoint(127, 71),
  xyWidthHeight=QPoint(434, 243)
 ),
 AreaParams(
  area="凤巢四层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(126, 340),
  xyRange=QPoint(127, 71),
  xyWidthHeight=QPoint(434, 243)
 ),
 AreaParams(
  area="小西天",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(210, 417),
  xyRange=QPoint(159, 239),
  xyWidthHeight=QPoint(266, 397)
 ),
 AreaParams(
  area="子母河底",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(146, 366),
  xyRange=QPoint(127, 95),
  xyWidthHeight=QPoint(393, 294)
 ),
 AreaParams(
  area="方寸山",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="五庄观",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="盘丝岭",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="麒麟山",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(142, 364),
  xyRange=QPoint(190, 142),
  xyWidthHeight=QPoint(401, 291)
 ),
 AreaParams(
  area="青丘",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(219, 411),
  xyRange=QPoint(127, 199),
  xyWidthHeight=QPoint(247, 384)
 ),
 AreaParams(
  area="北俱芦洲",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(145, 367),
  xyRange=QPoint(227, 169),
  xyWidthHeight=QPoint(394, 297)
 ),
 AreaParams(
  area="凌波城",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="狮驼岭",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(143, 368),
  xyRange=QPoint(131, 97),
  xyWidthHeight=QPoint(399, 299)
 ),
 AreaParams(
  area="大唐官府",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="天机城",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="五行山",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="鬼市",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="伊阙龙门",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(257, 364),
  xyRange=QPoint(53, 91),
  xyWidthHeight=QPoint(171, 290)
 ),
 AreaParams(
  area="女魃墓",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="墨家村",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(0, 0),
  xyRange=QPoint(0, 0),
  xyWidthHeight=QPoint(0, 0)
 ),
 AreaParams(
  area="长安酒店",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(154, 359),
  xyRange=QPoint(66, 49),
  xyWidthHeight=QPoint(377, 280)
 ),
 AreaParams(
  area="女娲神迹",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(145, 366),
  xyRange=QPoint(191, 143),
  xyWidthHeight=QPoint(394, 295)
 ),
 AreaParams(
  area="丝绸之路",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(93, 270),
  xyRange=QPoint(639, 95),
  xyWidthHeight=QPoint(612, 92)
 ),
 AreaParams(
  area="小雷音寺",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(92, 406),
  xyRange=QPoint(191, 143),
  xyWidthHeight=QPoint(501, 375)
 ),
 AreaParams(
  area="须弥东界",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(237, 406),
  xyRange=QPoint(112, 200),
  xyWidthHeight=QPoint(211, 374)
 ),
 AreaParams(
  area="银华境",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(184, 398),
  xyRange=QPoint(202, 57),
  xyWidthHeight=QPoint(319, 92)
 ),
 AreaParams(
  area="弥勒山",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(134, 361),
  xyRange=QPoint(174, 119),
  xyWidthHeight=QPoint(417, 285)
 ),
 AreaParams(
  area="龙窟三层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(69, 376),
  xyRange=QPoint(145, 83),
  xyWidthHeight=QPoint(548, 314)
 ),
 AreaParams(
  area="龙窟二层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(70, 365),
  xyRange=QPoint(135, 72),
  xyWidthHeight=QPoint(546, 292)
 ),
 AreaParams(
  area="龙窟一层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(72, 369),
  xyRange=QPoint(165, 92),
  xyWidthHeight=QPoint(541, 301)
 ),
 AreaParams(
  area="龙窟四层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(67, 356),
  xyRange=QPoint(141, 70),
  xyWidthHeight=QPoint(551, 274)
 ),
 AreaParams(
  area="凤巢一层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(124, 341),
  xyRange=QPoint(127, 71),
  xyWidthHeight=QPoint(437, 245)
 ),
 AreaParams(
  area="凤巢二层",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(125, 340),
  xyRange=QPoint(127, 71),
  xyWidthHeight=QPoint(435, 243)
 ),
 AreaParams(
  area="凌云渡",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(246, 398),
  xyRange=QPoint(119, 223),
  xyWidthHeight=QPoint(193, 357)
 ),
 AreaParams(
  area="无名鬼域",
  isFlyMap=False,
  isMapLightFunc=_isReturnTrueFuc,
  mapLeftBottomPoint=QPoint(190, 334),
  xyRange=QPoint(191, 142),
  xyWidthHeight=QPoint(306, 230)
 )
]
changAnMapParamsCW = AreaParams(
 area="长安城",
 isFlyMap=True,
 isMapLightFunc=_changAnMapIsLightCW,
 mapLeftBottomPoint=QPoint(39, 367),
 xyRange=QPoint(548, 278),
 xyWidthHeight=QPoint(568, 287)
)
aoLaiGuoMapParamsCW = AreaParams(
 area="傲来国",
 isFlyMap=True,
 isMapLightFunc=_aoLaiMapIsLightCW,
 mapLeftBottomPoint=QPoint(103, 371),
 xyRange=QPoint(222, 149),
 xyWidthHeight=QPoint(440, 295)
)
huaGuoShanMapParamsCW = AreaParams(
 area="花果山",
 isFlyMap=False,
 isMapLightFunc=_huaGuoShanMapIsLightCW,
 mapLeftBottomPoint=QPoint(148, 367),
 xyRange=QPoint(158, 118),
 xyWidthHeight=QPoint(385, 287)
)
beiJuLuZhouMapParamsCW = AreaParams(
 area="北俱芦洲",
 isFlyMap=False,
 isMapLightFunc=_beiJuLuZhouMapIsLightCW,
 mapLeftBottomPoint=QPoint(143, 372),
 xyRange=QPoint(226, 168),
 xyWidthHeight=QPoint(394, 297)
)
longKuYiCengMapParamsCW = AreaParams(
 area="龙窟一层",
 isFlyMap=False,
 isMapLightFunc=_longKuYiCengMapIsLightCW,
 mapLeftBottomPoint=QPoint(70, 374),
 xyRange=QPoint(164, 91),
 xyWidthHeight=QPoint(541, 301)
)
pengLaiXianDaoMapParamsCW = AreaParams(
 area="蓬莱仙岛",
 isFlyMap=False,
 isMapLightFunc=_pengLaiXianDaoMapIsLightCW,
 mapLeftBottomPoint=QPoint(141, 373),
 xyRange=QPoint(190, 143),
 xyWidthHeight=QPoint(397, 298)
)
qiLinShanMapParamsCW = AreaParams(
 area="麒麟山",
 isFlyMap=False,
 isMapLightFunc=_qiLinShanMapIsLightCW,
 mapLeftBottomPoint=QPoint(140, 369),
 xyRange=QPoint(189, 141),
 xyWidthHeight=QPoint(401, 291)
)
mapParamsListCW = [
 AreaParams(
  area="长安城",
  isFlyMap=True,
  isMapLightFunc=_changAnMapIsLightCW,
  mapLeftBottomPoint=QPoint(39, 367),
  xyRange=QPoint(548, 278),
  xyWidthHeight=QPoint(568, 287)
 ),
 AreaParams(
  area="傲来国",
  isFlyMap=True,
  isMapLightFunc=_aoLaiMapIsLightCW,
  mapLeftBottomPoint=QPoint(103, 371),
  xyRange=QPoint(222, 149),
  xyWidthHeight=QPoint(440, 295)
 ),
 AreaParams(
  area="花果山",
  isFlyMap=False,
  isMapLightFunc=_huaGuoShanMapIsLightCW,
  mapLeftBottomPoint=QPoint(148, 367),
  xyRange=QPoint(158, 118),
  xyWidthHeight=QPoint(385, 287)
 ),
 AreaParams(
  area="北俱芦洲",
  isFlyMap=False,
  isMapLightFunc=_beiJuLuZhouMapIsLightCW,
  mapLeftBottomPoint=QPoint(143, 372),
  xyRange=QPoint(226, 168),
  xyWidthHeight=QPoint(394, 297)
 ),
 AreaParams(
  area="龙窟一层",
  isFlyMap=False,
  isMapLightFunc=_longKuYiCengMapIsLightCW,
  mapLeftBottomPoint=QPoint(70, 374),
  xyRange=QPoint(164, 91),
  xyWidthHeight=QPoint(541, 301)
 ),
 AreaParams(
  area="蓬莱仙岛",
  isFlyMap=False,
  isMapLightFunc=_pengLaiXianDaoMapIsLightCW,
  mapLeftBottomPoint=QPoint(141, 373),
  xyRange=QPoint(190, 143),
  xyWidthHeight=QPoint(397, 298)
 ),
 AreaParams(
  area="麒麟山",
  isFlyMap=False,
  isMapLightFunc=_qiLinShanMapIsLightCW,
  mapLeftBottomPoint=QPoint(140, 369),
  xyRange=QPoint(189, 141),
  xyWidthHeight=QPoint(401, 291)
 )
]
dianXiangAreas = [
 "龙窟五层",
 "龙窟六层",
 "凤巢四层",
 "小西天",
 "小雷音寺",
 "女娲神迹",
 "弥勒山",
 "须弥东界",
 "银华境",
 "伊阙龙门",
 "无名鬼域"
]
hasCloseSaiXuanMaps = {}
