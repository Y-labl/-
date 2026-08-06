# -*- coding: utf-8 -*-
# Assembled from decompiled bytecode of img_util.pyc

import base64
import json
import random
import time
import numpy as np
import requests
from xbw_features.qtcompat import QPoint
from loguru import logger
from xbw_features.common.util.file_util import cv_save_img
from xbw_features.common.util.time_util import getLogTime, getLogTimeHour
from xbw_features import const
from xbw_features.common.util.click_util import click
from xbw_features.common.util.color_util import isShowPopColorDK, isShowRoleAvatar
from xbw_features.common.util.log_util import logTmpPath, logUtil, orderLog
from xbw_features.common.util.math_util import distance_between_points
from xbw_features.common.util.scrcpy_util import scrcpyUtil, DeviceWidth, DeviceHeight
import cv2

def findPic(deviceId, imgName, left=0, top=0, width=800, height=448, withClick=False, withDoubleClick=False, curFrame=None, similar=0.8):
    try:
        frame = None
        if curFrame is not None:
            frame = curFrame
        else:
            frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            return None
        if top != 0 or left != 0 or width != DeviceWidth or height != DeviceHeight:
            left = int(left)
            top = int(top)
            width = int(width)
            height = int(height)
            frame = frame[top:top + height, left:left + width]
        targetImg = _load_template(imgName)
        if targetImg is None:
            logger.debug(f"{deviceId}模板不存在: {imgName}{const.gameType}")
            return None
        result = cv2.matchTemplate(frame, targetImg, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        curSimilar = similar
        if "幽" in imgName:
            curSimilar = 0.7
        if max_val > curSimilar:
            x, y = max_loc
            targetPoint = QPoint(x + left, y + top)
            logger.debug(f"{deviceId}找图片({imgName}{const.gameType}) 相似度:{max_val} 找到位置({targetPoint.x()},{targetPoint.y()})")
            if withClick or withDoubleClick:
                targetImgWidth, targetImgHeight = getImgSize(targetImg)
                offsetPoint = QPoint(random.randint(0, targetImgWidth), random.randint(0, targetImgHeight))
                clickPoint = targetPoint + offsetPoint
                logger.debug(f"{deviceId} 找图点击图片({imgName}{const.gameType}) 点击位置({clickPoint.x()},{clickPoint.y()})")
                click(deviceId, clickPoint, offset=QPoint(), isDouble=withDoubleClick)
                time.sleep(random.uniform(0.3, 0.5))
            return targetPoint
        logger.debug(f"{deviceId}找图片({imgName}{const.gameType}) 相似度:{max_val} 未找到")
        return None
    except Exception as e:
        logger.exception(f"findPic发生错误：{e}")
        return None


def findPics(deviceId, imgNames, left=0, top=0, width=800, height=448, withClick=False, withDoubleClick=False, curFrame=None, similar=0.8, clickWaitT=0.3):
    try:
        frame = None
        if curFrame is not None:
            frame = curFrame
        else:
            frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            return []
        if top != 0 or left != 0 or width != DeviceWidth or height != DeviceHeight:
            frame = frame[top:top + height, left:left + width]
        results = []
        for imgName in imgNames:
            targetImg = _load_template(imgName)
            if targetImg is None:
                continue
            result = cv2.matchTemplate(frame, targetImg, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= similar)
            for pt in zip(*loc[::-1]):
                isExistSamePoint = False
                targetPoint = QPoint(left, top) + QPoint(pt[0], pt[1])
                for point in results:
                    distance = distance_between_points(point, targetPoint)
                    if distance < 20:
                        isExistSamePoint = True
                if isExistSamePoint is False:
                    results.append(targetPoint)
                    if withClick or withDoubleClick:
                        targetImgWidth, targetImgHeight = getImgSize(targetImg)
                        offsetPoint = QPoint(random.randint(0, targetImgWidth), random.randint(0, targetImgHeight))
                        clickPoint = targetPoint + offsetPoint
                        logger.debug(f"{deviceId} 找多图点击图片({imgName}{const.gameType}) 相似度:{result[pt[1], pt[0]]} 点击位置({clickPoint.x()},{clickPoint.y()})")
                        click(deviceId, clickPoint, offset=QPoint(), isDouble=withDoubleClick)
                        time.sleep(random.uniform(clickWaitT, clickWaitT * 1.6))
                    logger.debug(f"{deviceId}找多图({imgName}{const.gameType}) 相似度:{result[pt[1], pt[0]]} 找到位置({targetPoint.x()},{targetPoint.y()})")
        return results
    except Exception as e:
        logger.exception(f"findPics发生错误：{e}")
        return []


def findOneFromPics(deviceId, imgNames, left=0, top=0, width=800, height=448, withClick=False, curFrame=None, similar=0.8, perT=0.5, totalT=10, oneSimilarMap=None):
    waitT = 0
    for imgName in imgNames:
        curSimilar = similar
        if oneSimilarMap:
            if imgName in oneSimilarMap:
                curSimilar = oneSimilarMap[imgName]
        targetPoint = findPic(deviceId, imgName, left=left, top=top, width=width, height=height, withClick=withClick, curFrame=curFrame, similar=curSimilar)
        if targetPoint:
            return (
             imgName, targetPoint)
        if waitT >= totalT:
            break
        time.sleep(perT)
        waitT += perT
    else:
        return (None, None)


def waitAssertImgOk(deviceId, imgName, left=0, top=0, width=800, height=448, withClick=False, withDoubleClick=False, middleImgNames=None, middleFunc=None, similar=0.8, perT=0.5, totalT=10):
    isAssertOk = False
    waitT = 0
    while True:
        targetPoint = findPic(deviceId, imgName, left, top, width, height, withClick=withClick, withDoubleClick=withDoubleClick, similar=similar)
        if targetPoint:
            time.sleep(perT)
            isAssertOk = True
            break
        isHasClickMiddleImg = False
        if middleImgNames:
            for middleImgName in middleImgNames:
                middleImgPoint = findPic(deviceId, middleImgName, left, top, width, height, withClick=True)
                if middleImgPoint:
                    isHasClickMiddleImg = True
        if not isHasClickMiddleImg and middleFunc:
            middleFunc()
        time.sleep(perT)
        waitT += perT
        if waitT > totalT:
            break
    return isAssertOk


def waitAssertFuncOk(deviceId, func, top=0, left=0, width=800, height=448, middleImgNames=None, middleFunc=None, perT=0.5, totalT=10):
    if totalT is None:
        totalT = 10
    if perT is None:
        perT = 0.5
    isAssertOk = False
    waitT = 0
    while True:
        isOk = func()
        if isOk:
            time.sleep(perT)
            isAssertOk = True
            break
        if middleImgNames:
            for middleImgName in middleImgNames:
                findPic(deviceId, middleImgName, top, left, width, height, withClick=True)
        if middleFunc:
            middleFunc()
        time.sleep(perT)
        waitT += perT
        if waitT > totalT:
            break
    return isAssertOk


def cv_imread(file_path):
    try:
        import numpy as np
        cv_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        return cv_img
    except Exception as e:
        logger.debug(f"cv_imread发生错误：{e}")
        return None


def _load_template(imgName):
    """按本工程模板目录加载 {imgName}{gameType}.png / {imgName}.png。"""
    import os as _os
    for d in const.TEMPLATE_DIRS:
        for suffix in (const.gameType, ""):
            path = _os.path.join(d, f"{imgName}{suffix}.png")
            img = cv_imread(path)
            if img is not None:
                return img
    # 兼容旧路径：logUtil.parentPath + 小霸王/逻辑素材/
    legacy = '{}小霸王/逻辑素材/{}{}.png'.format(logUtil.getParentPath(), imgName, const.gameType)
    if legacy.startswith("小霸王") or _os.path.exists(legacy):
        img = cv_imread(legacy)
        if img is not None:
            return img
    return None


def getImgSize(img):
    height, width = (0, 0)
    if img is not None:
            height, width = img.shape[:2]
    return (
     width, height)


def isInPk(deviceId):
    if const.gameType == "点卡服":
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.8)
        isFriendEnterPK = friendEnterPoint is None or friendEnterPoint and friendEnterPoint.x() < 100
        return isFriendEnterPK and not isShowPopColorDK(deviceId)
    if const.gameType == "畅玩服":
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.75)
        if friendEnterPoint is None:
            findPic(deviceId, "重置回合数", withClick=True)
        return friendEnterPoint is None or friendEnterPoint and friendEnterPoint.x() < 100


def isShowFourPerson(deviceId):
    for i in range(3):
        if isShowRoleAvatar(deviceId):
            return False
        time.sleep(0.5)
    for i in range(2):
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.8)
        if friendEnterPoint:
            return False
        time.sleep(0.5)
    isHasBackPoint = findPic(deviceId, "PK-撤销战斗操作", withClick=True)
    if isHasBackPoint:
        return False
    return True


def findFourPersonAndClick(deviceId, left=227, top=80, width=360, height=150, curFrame=None):
    try:
        frame = None
        if curFrame is not None:
            frame = curFrame
        else:
            frame = scrcpyUtil.getFrame(deviceId)
        roi = frame[top:top + height, left:left + width]
        retval, buffer = cv2.imencode(".png", roi)
        roi_base64 = base64.b64encode(buffer).decode("utf-8")
        data = {}
        for k, v in const.TULING_AUTH.items():
            data[k] = v
        data["b64"] = roi_base64
        data_json = json.dumps(data)
        result = json.loads(requests.post(const.TULING_API_URL, data=data_json).text)
        orderLog(deviceId, f"网络识别四小人结果:{result}")
        if result["data"]:
            if result["data"]["X坐标值"]:
                if result["data"]["Y坐标值"]:
                    clickPoint = QPoint(left, top) + QPoint(result["data"]["X坐标值"], result["data"]["Y坐标值"])
                    click(deviceId, clickPoint, offset=(QPoint()))
                    orderLog(deviceId, f"网络点击四小人位置：{clickPoint}")
                    cv_save_img(f"{logTmpPath()}/{getLogTimeHour()}/{deviceId}-{getLogTime()}-x{clickPoint.x()}y{clickPoint.y()}-FourPerson-Net.png", frame)
                    time.sleep(0.8)
                    from xbw_features.cw_changjing.cw_changjing_util import findFourPersonDetectArea
                    nextLeft, nextTop, _, _ = findFourPersonDetectArea(deviceId)
                    if abs(nextLeft - left) < 5:
                        if abs(nextTop - top) < 5:
                            orderLog(deviceId, f"网络-点了没变化，点击(重试)四小人位置：{clickPoint}")
                            click(deviceId, clickPoint)
                            time.sleep(0.8)
    except Exception as e:
        try:
            logger.exception(f"{deviceId}网络-识别四小人异常:{e}")
            orderLog(deviceId, f"网络-识别四小人异常:{e}")
        finally:
            e = None
            del e


def checkAtDaoJu(deviceId):
    atDaoJuPoint = findPic(deviceId, "当前在道具栏")
    if atDaoJuPoint is None:
        click(deviceId, QPoint(400, 85))
        time.sleep(random.uniform(1, 2))
    return True

