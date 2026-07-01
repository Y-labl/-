# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\img_util.py
import base64, json, random, time, numpy as np, requests
from PyQt5.QtCore import QPoint
from loguru import logger
import const
from common.util.click_util import click
from common.util.color_util import isShowPopColorDK, isShowRoleAvatar
from common.util.log_util import logUtil
from common.util.math_util import distance_between_points
from common.util.scrcpy_util import scrcpyUtil, DeviceWidth, DeviceHeight
import cv2

def findPicParse error at or near `SETUP_FINALLY' instruction at offset 0_2


def findPics(deviceId, imgNames, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, withDoubleClick=False, similar=0.8, clickWaitT=0.3):
    try:
        frame = scrcpyUtil.getFramedeviceId
        if top != 0 or left != 0 or left != 0 or height != DeviceHeight:
            frame = frame[top:top + height, left:left + width]
        results = []
        for imgName in imgNames:
            targetPath = "{}小霸王/逻辑素材/{}{}.png".formatlogUtil.getParentPathimgNameconst.gameType
            targetImg = cv_imread(targetPath)
            result = cv2.matchTemplatetargetImgframecv2.TM_CCOEFF_NORMED
            loc = np.where(result >= similar)
            for pt in zip(*loc[::-1]):
                isExistSamePoint = False
                targetPoint = QPointlefttop + QPointpt[0]pt[1]
                for point in results:
                    distance = distance_between_pointspointtargetPoint
                    if distance < 20:
                        isExistSamePoint = True

                if isExistSamePoint is False:
                    results.appendtargetPoint
                    if not withClick or withDoubleClick:
                        targetImgWidth, targetImgHeight = getImgSize(targetImg)
                        offsetPoint = QPointrandom.randint0targetImgWidthrandom.randint0targetImgHeight
                        clickPoint = targetPoint + offsetPoint
                        logger.debugf"{deviceId} 找多图点击图片({imgName}{const.gameType}) 相似度:{result[(pt[1], pt[0])]} 点击位置({clickPoint.x},{clickPoint.y})"
                        click(deviceId, clickPoint, offset=(QPoint), isDouble=withDoubleClick)
                        time.sleeprandom.uniformclickWaitT(clickWaitT * 1.6)
                    else:
                        logger.debugf"{deviceId}找多图({imgName}{const.gameType}) 相似度:{result[(pt[1], pt[0])]} 找到位置({targetPoint.x},{targetPoint.y})"

        return results
    except Exception as e:
        logger.exceptionf"findPics发生错误：{e}"
        return []


def findOneFromPics(deviceId, imgNames, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, similar=0.8, perT=0.5, totalT=10):
    waitT = 0
    while True:
        for imgName in imgNames:
            targetPoint = findPic(deviceId, imgName, left=left, top=top, width=width, height=height, withClick=withClick, similar=similar)
            if targetPoint:
                return (imgName, targetPoint)

        if waitT >= totalT:
            break
        else:
            time.sleepperT
            waitT += perT

    return (None, None)


def waitAssertImgOk(deviceId, imgName, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, withDoubleClick=False, middleImgNames=None, middleFunc=None, similar=0.8, perT=0.5, totalT=10):
    isAssertOk = False
    waitT = 0
    while True:
        targetPoint = findPic(deviceId, imgName, left, top, width, height, withClick=withClick, withDoubleClick=withDoubleClick, similar=similar)
        if targetPoint:
            time.sleepperT
            isAssertOk = True
            break
        isHasClickMiddleImg = False
        if middleImgNames:
            for middleImgName in middleImgNames:
                middleImgPoint = findPic(deviceId, middleImgName, left, top, width, height, withClick=True)
                if middleImgPoint:
                    isHasClickMiddleImg = True

            if not isHasClickMiddleImg:
                if middleFunc:
                    middleFunc
            time.sleepperT
            waitT += perT
            if waitT > totalT:
                break

    return isAssertOk


def waitAssertFuncOk(deviceId, func, top=0, left=0, width=DeviceWidth, height=DeviceHeight, middleImgNames=None, middleFunc=None, perT=0.5, totalT=10):
    if totalT is None:
        totalT = 10
    if perT is None:
        perT = 0.5
    isAssertOk = False
    waitT = 0
    while True:
        isOk = func
        if isOk:
            time.sleepperT
            isAssertOk = True
            break
        if middleImgNames:
            for middleImgName in middleImgNames:
                findPic(deviceId, middleImgName, top, left, width, height, withClick=True)

            if middleFunc:
                middleFunc
            time.sleepperT
            waitT += perT
            if waitT > totalT:
                break

    return isAssertOk


def cv_imreadParse error at or near `SETUP_FINALLY' instruction at offset 0


def getImgSize(img):
    (height, width) = (0, 0)
    if img is not None:
        (height, width) = img.shape[:2]
    return (width, height)


def isInPk(deviceId):
    if const.gameType == "点卡服":
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.75)
        isFriendEnterPK = (friendEnterPoint is None) or (friendEnterPoint and (friendEnterPoint.x < 100))
        return isFriendEnterPK and not isShowPopColorDK(deviceId)
    if const.gameType == "畅玩服":
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.75)
        if friendEnterPoint is None:
            findPic(deviceId, "重置回合数", withClick=True)
        return (friendEnterPoint is None) or (friendEnterPoint and (friendEnterPoint.x < 100))


def isShowFourPerson(deviceId):
    for i in range(3):
        if isShowRoleAvatar(deviceId):
            return False
        else:
            time.sleep0.5

    for i in range(2):
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.75)
        if friendEnterPoint:
            return False
        else:
            time.sleep0.5

    return True


def findFourPersonAndClick(deviceId, left=227, top=80, width=360, height=150):
    try:
        frame = scrcpyUtil.getFramedeviceId
        roi = frame[top:top + height, left:left + width]
        (retval, buffer) = cv2.imencode".png"roi
        roi_base64 = base64.b64encodebuffer.decode"utf-8"
        data = { 'username': "qq326646683", 'password': "dashuai5", 'ID': 48117555, 'b64': roi_base64, 'version': "3.1.1"}
        data_json = json.dumpsdata
        result = json.loadsrequests.post("http://www.tulingcloud.com/tuling/predict", data=data_json).text
        logger.infof"{deviceId}识别四小人结果:{result}"
        if result["data"]:
            if result["data"]["X坐标值"]:
                if result["data"]["Y坐标值"]:
                    clickPoint = QPointlefttop + QPointresult["data"]["X坐标值"]result["data"]["Y坐标值"]
                    click(deviceId, clickPoint, offset=(QPoint))
                    logger.infof"{deviceId}点击四小人位置：{clickPoint}"
                    cv2.imwritef"./{deviceId}-x{clickPoint.x}y{clickPoint.y}.png"frame
    except Exception as e:
        try:
            logger.exceptionf"{deviceId}识别四小人异常"
        finally:
            e = None
            del e


def checkAtDaoJu(deviceId):
    atDaoJuPoint = findPicdeviceId"当前在道具栏"
    if atDaoJuPoint is None:
        clickdeviceIdQPoint40085
        time.sleeprandom.uniform12
    return True