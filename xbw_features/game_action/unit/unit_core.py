# -*- coding: utf-8 -*-
# Assembled from decompiled bytecode of unit_core.pyc

import os
import random
import time
import inspect
from loguru import logger
from xbw_features.common.util.img_util import findPic, waitAssertImgOk, waitAssertFuncOk
from xbw_features.common.util.math_util import isframeSame
from xbw_features.common.util.scrcpy_util import scrcpyUtil, DeviceWidth
from inspect import signature

def checkStatusOk(func):
    func.__signature__ = signature(func)

    def wrapper(*args, **kwargs):
        bound_args = (func.__signature__.bind)(*args, **kwargs)
        bound_args.apply_defaults()
        params = bound_args.arguments
        deviceId = params.get("deviceId")
        preImgName = params.get("preImgName")
        middleImgNames = params.get("middleImgNames")
        middleFunc = params.get("middleFunc")
        nextImgName = params.get("nextImgName")
        preFunc = params.get("preFunc")
        nextFunc = params.get("nextFunc")
        isClickPreImg = params.get("isClickPreImg")
        isClickNextImg = params.get("isClickNextImg")
        isDoubleClickPreImg = params.get("isDoubleClickPreImg")
        isClosePopTry = params.get("isClosePopTry")
        preTotalT = params.get("preTotalT")
        prePerT = params.get("prePerT")
        nextTotalT = params.get("nextTotalT")
        nextPerT = params.get("nextPerT")
        isNotFirstCheckNext = params.get("isNotFirstCheckNext")
        left = params.get("left")
        width = params.get("width")
        if left is None:
            left = 0
        elif width is None:
            width = DeviceWidth
        else:
            logger.debug(f"{deviceId} 方法 {func.__name__} 执行,参数： preImgName = {preImgName} middleImgNames={middleImgNames}  middleFunc={middleFunc} nextImgName ={nextImgName} preFunc ={preFunc} nextFunc ={nextFunc} isClickPreImg={isClickPreImg} isDoubleClickPreImg={isDoubleClickPreImg} isClosePopTry={isClosePopTry} nextTotalT={nextTotalT} isNotFirstCheckNext={isNotFirstCheckNext}")
            if not isNotFirstCheckNext:
                if nextImgName:
                    isOk = findPic(deviceId, nextImgName)
                    if isOk:
                        return True
                if nextFunc:
                    isOk = nextFunc()
                    if isOk:
                        return True
            isPreOk = True
            if preFunc:
                isOk = waitAssertFuncOk(deviceId, preFunc, perT=prePerT, totalT=preTotalT)
                if not isOk:
                    isPreOk = False
            if preImgName:
                isOk = waitAssertImgOk(deviceId, preImgName, left=left, width=width, withClick=(isClickPreImg is True), withDoubleClick=(isDoubleClickPreImg is True))
                if not isOk:
                    isPreOk = False
            if preFunc is None:
                if preImgName is None:
                    isPreOk = True
            if not isPreOk:
                if isClosePopTry:
                    logger.debug(f"{deviceId} 没达到预期(前置检查不通过): 关闭所有弹窗重试当前方法(common_unit):{func.__name__}")
                    closePopAndReRunCommonUnit(deviceId, wrapper, bound_args)
                else:
                    logger.debug(f"{deviceId} 没达到预期(前置检查不通过): 检查网络/卡死后 重启游戏重新运行application_action；否则关闭弹窗 重新运行")
                    finalDealException(deviceId)
            else:
                result = func(*args, **kwargs)
                isNextOk = True
                if nextImgName:
                    isOk = waitAssertImgOk(deviceId, nextImgName, left=left, width=width, withClick=(isClickNextImg is True), middleImgNames=middleImgNames, middleFunc=middleFunc)
                    if not isOk:
                        isNextOk = False
                if nextFunc:
                    isOk = waitAssertFuncOk(deviceId, nextFunc, middleImgNames=middleImgNames, middleFunc=middleFunc, perT=nextPerT, totalT=nextTotalT)
                    if not isOk:
                        isNextOk = False
                if nextFunc is None:
                    if nextImgName is None:
                        isNextOk = True
                    if isNextOk:
                        return result
                    if isClosePopTry:
                        logger.debug(f"{deviceId} 没达到预期(前置检查通过 且 动作后检查不通过): 关闭所有弹窗重试当前方法(common_unit):{func.__name__}")
                        closePopAndReRunCommonUnit(deviceId, wrapper, bound_args)
                else:
                    logger.debug(f"{deviceId} 没达到预期(前置检查通过 且 动作后检查不通过): 检查网络/卡死后 重启游戏重新运行application_action方法；否则关闭弹窗 重新运行")
            finalDealException(deviceId)


    return wrapper


def closePopAndReRunCommonUnit(deviceId, wrapper, bound_args):
    from xbw_features.game_action.unit.common_unit import closePop
    closePop(deviceId)
    params = bound_args.arguments
    new_kwargs = params.copy()
    new_kwargs["isClosePopTry"] = False
    return wrapper(**new_kwargs)


def finalDealException(deviceId):
    isHang = checkUiHang(deviceId)
    isNetError = checkNetErrorUI(deviceId)
    if isHang or isNetError:
        logger.debug(f"{deviceId}界面卡死{isHang},网络异常{isNetError}了,重启游戏")
        logger.debug(f"{deviceId}适配层不自动重启游戏，交由上层处理")
    else:
        logger.debug(f"{deviceId}没达到预期,关闭所有弹窗")
        from xbw_features.game_action.unit.common_unit import closePop
        closePop(deviceId)
    raise RuntimeError(f"{deviceId}流程中断，交由上层重试")


def checkLandscape(deviceId):
    isLand = scrcpyUtil.isLandscape(deviceId)
    logger.debug(f"{deviceId}检查是否退出, 确认是横屏: {isLand}")
    if not isLand:
        logger.debug(f"{deviceId}不是横屏, 发现游戏闪退, 尝试进入游戏")
        logger.debug(f"{deviceId}适配层不自动拉起游戏，交由上层处理")
        isClickEnter = waitAssertImgOk(deviceId, "进入梦幻互通", withClick=True, totalT=300)
        if isClickEnter:
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
    else:
        logger.debug(f"{deviceId}是横屏, 游戏正常未发现闪退")


def checkUiHang(deviceId):
    logger.debug(f"{deviceId} 没达到预期: 连续是否卡死(检测10次画面静止,认为卡死)")
    isHang = True
    lastFrame = None
    for i in range(11):
        newMOffset = scrcpyUtil.getNewMOffset(deviceId)
        curFrame = scrcpyUtil.getFrame(deviceId)[2:12, 86 + newMOffset:113 + newMOffset]
        if lastFrame is not None:
            if isframeSame(curFrame, lastFrame):
                logger.debug(f"{deviceId} 持续检查{11 - i}次是否卡死：是")
            else:
                logger.debug(f"{deviceId} 检查发现未卡死")
                isHang = False
                break
        lastFrame = curFrame
        time.sleep(3)
    else:
        return isHang


def checkNetErrorUI(deviceId):
    logger.debug(f"{deviceId} 没达到预期: 检查是否网络异常")
    netErrorPoint1 = findPic(deviceId, "网络连接失败")
    netErrorPoint2 = findPic(deviceId, "网络连接重试")
    return netErrorPoint1 is not None or netErrorPoint2 is not None


def clean_func_args(func, args_dict):
        try:
            sig = inspect.signature(func)
            valid_params = list(sig.parameters.keys())
            cleaned = {}
            for k, v in args_dict.items():
                if k in valid_params:
                    cleaned[k] = v
            return cleaned
        except Exception as e:
            logger.debug(f"clean_func_args exception: {e}")
            return None

