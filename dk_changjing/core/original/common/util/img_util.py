# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\img_util.py
import base64, json, random, time, os, numpy as np, requests
from PyQt5.QtCore import QPoint
from loguru import logger
import const
from common.util.click_util import click
from common.util.color_util import isShowPopColorDK, isShowRoleAvatar
from common.util.log_util import logUtil
from common.util.math_util import distance_between_points
from common.util.scrcpy_util import scrcpyUtil, DeviceWidth, DeviceHeight
import cv2

def cv_imread(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        stream = open(file_path, "rb")
        bytes_data = bytearray(stream.read())
        numpyarray = np.asarray(bytes_data, dtype=np.uint8)
        return cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)
    except:
        return cv2.imread(file_path)

def getImgSize(img):
    (height, width) = (0, 0)
    if img is not None:
        (height, width) = img.shape[:2]
    return (width, height)

def findPic(deviceId, imgName, left=0, top=0, width=None, height=None, withClick=False, withDoubleClick=False, similar=0.8):
    try:
        frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            return None
        l = int(left) if left else 0
        t = int(top) if top else 0
        w = int(width) if width is not None else DeviceWidth
        h = int(height) if height is not None else DeviceHeight
        if t != 0 or l != 0 or w != DeviceWidth or h != DeviceHeight:
            t = max(0, t)
            l = max(0, l)
            b = min(frame.shape[0], t + h)
            r = min(frame.shape[1], l + w)
            if b > t and r > l:
                frame = frame[t:b, l:r]
        targetPath = os.path.join(logUtil.getParentPath(), "小霸王", "逻辑素材", imgName + const.gameType + ".png")
        targetImg = cv_imread(targetPath)
        if targetImg is None:
            logger.debug("模板不存在: {}".format(targetPath))
            return None
        if len(targetImg.shape) == 3 and targetImg.shape[2] == 4:
            targetImg = cv2.cvtColor(targetImg, cv2.COLOR_BGRA2BGR)
        result = cv2.matchTemplate(targetImg, frame, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > similar:
            x, y = max_loc
            targetPoint = QPoint(x + l, y + t)
            logger.debug("{}找图片({}{}) 相似度:{} 找到位置({},{})".format(deviceId, imgName, const.gameType, max_val, targetPoint.x(), targetPoint.y()))
            if withClick or withDoubleClick:
                targetImgWidth, targetImgHeight = getImgSize(targetImg)
                offsetPoint = QPoint(random.randint(0, max(1, targetImgWidth)), random.randint(0, max(1, targetImgHeight)))
                clickPoint = targetPoint + offsetPoint
                logger.debug("{} 找图点击图片({}{}) 点击位置({},{})".format(deviceId, imgName, const.gameType, clickPoint.x(), clickPoint.y()))
                click(deviceId, clickPoint, QPoint(), isDouble=withDoubleClick)
                time.sleep(random.uniform(0.3, 0.5))
            return targetPoint
        logger.debug("{}找图片({}{}) 相似度:{} 未找到".format(deviceId, imgName, const.gameType, max_val))
        return None
    except Exception as e:
        logger.exception("findPic发生错误：{}".format(e))
        return None

def findPics(deviceId, imgNames, left=0, top=0, width=None, height=None, withClick=False, withDoubleClick=False, similar=0.8, clickWaitT=0.3):
    try:
        frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            return []
        w = int(width) if width is not None else DeviceWidth
        h = int(height) if height is not None else DeviceHeight
        l = int(left) if left else 0
        t = int(top) if top else 0
        if t != 0 or l != 0 or w != DeviceWidth or h != DeviceHeight:
            t = max(0, t)
            l = max(0, l)
            b = min(frame.shape[0], t + h)
            r = min(frame.shape[1], l + w)
            if b > t and r > l:
                frame = frame[t:b, l:r]
        results = []
        for imgName in imgNames:
            targetPath = os.path.join(logUtil.getParentPath(), "小霸王", "逻辑素材", imgName + const.gameType + ".png")
            targetImg = cv_imread(targetPath)
            if targetImg is None:
                continue
            if len(targetImg.shape) == 3 and targetImg.shape[2] == 4:
                targetImg = cv2.cvtColor(targetImg, cv2.COLOR_BGRA2BGR)
            result = cv2.matchTemplate(targetImg, frame, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= similar)
            for pt in zip(*loc[::-1]):
                isExistSamePoint = False
                targetPoint = QPoint(l, t) + QPoint(pt[0], pt[1])
                for point in results:
                    distance = distance_between_points(point, targetPoint)
                    if distance < 20:
                        isExistSamePoint = True
                if isExistSamePoint is False:
                    results.append(targetPoint)
                    if withClick or withDoubleClick:
                        targetImgWidth, targetImgHeight = getImgSize(targetImg)
                        offsetPoint = QPoint(random.randint(0, max(1, targetImgWidth)), random.randint(0, max(1, targetImgHeight)))
                        clickPoint = targetPoint + offsetPoint
                        logger.debug("{} 找多图点击图片({}{}) 相似度:{} 点击位置({},{})".format(deviceId, imgName, const.gameType, result[(pt[1], pt[0])], clickPoint.x(), clickPoint.y()))
                        click(deviceId, clickPoint, QPoint(), isDouble=withDoubleClick)
                        time.sleep(random.uniform(clickWaitT, clickWaitT * 1.6))
                    else:
                        logger.debug("{}找多图({}{}) 相似度:{} 找到位置({},{})".format(deviceId, imgName, const.gameType, result[(pt[1], pt[0])], targetPoint.x(), targetPoint.y()))
        return results
    except Exception as e:
        logger.exception("findPics发生错误：{}".format(e))
        return []

def findOneFromPics(deviceId, imgNames, left=0, top=0, width=None, height=None, withClick=False, similar=0.8, perT=0.5, totalT=10):
    waitT = 0
    while True:
        for imgName in imgNames:
            targetPoint = findPic(deviceId, imgName, left=left, top=top, width=width, height=height, withClick=withClick, similar=similar)
            if targetPoint:
                return (imgName, targetPoint)
        if waitT >= totalT:
            break
        else:
            time.sleep(perT)
            waitT += perT
    return (None, None)

def waitAssertImgOk(deviceId, imgName, left=0, top=0, width=None, height=None, withClick=False, withDoubleClick=False, middleImgNames=None, middleFunc=None, similar=0.8, perT=0.5, totalT=10):
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
            if not isHasClickMiddleImg:
                if middleFunc:
                    middleFunc()
            time.sleep(perT)
            waitT += perT
            if waitT > totalT:
                break
    return isAssertOk

def waitAssertFuncOk(deviceId, func, top=0, left=0, width=None, height=None, middleImgNames=None, middleFunc=None, perT=0.5, totalT=10):
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

def isInPk(deviceId):
    if const.gameType == "点卡服":
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.70)
        isFriendEnterPK = (friendEnterPoint is None) or (friendEnterPoint and (friendEnterPoint.x() < 100))
        return isFriendEnterPK and not isShowPopColorDK(deviceId)
    if const.gameType == "畅玩服":
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.70)
        if friendEnterPoint is None:
            findPic(deviceId, "重置回合数", withClick=True)
        return (friendEnterPoint is None) or (friendEnterPoint and (friendEnterPoint.x() < 100))

def isShowFourPerson(deviceId):
    for i in range(3):
        if isShowRoleAvatar(deviceId):
            return False
        else:
            time.sleep(0.5)
    for i in range(2):
        friendEnterPoint = findPic(deviceId, "好友入口", similar=0.70)
        if friendEnterPoint:
            return False
        else:
            time.sleep(0.5)
    return True

def findFourPersonAndClick(deviceId, left=227, top=80, width=360, height=150):
    try:
        frame = scrcpyUtil.getFrame(deviceId)
        roi = frame[top:top + height, left:left + width]
        (retval, buffer) = cv2.imencode(".png", roi)
        roi_base64 = base64.b64encode(buffer).decode("utf-8")
        data = {'username': "qq326646683", 'password': "dashuai5", 'ID': 48117555, 'b64': roi_base64, 'version': "3.1.1"}
        data_json = json.dumps(data)
        result = json.loads(requests.post("http://www.tulingcloud.com/tuling/predict", data=data_json).text)
        logger.info("{}识别四小人结果:{}".format(deviceId, result))
        if result["data"]:
            if result["data"]["X坐标值"]:
                if result["data"]["Y坐标值"]:
                    clickPoint = QPoint(left, top) + QPoint(result["data"]["X坐标值"], result["data"]["Y坐标值"])
                    click(deviceId, clickPoint, QPoint())
                    logger.info("{}点击四小人位置：{}".format(deviceId, clickPoint))
                    cv2.imwrite("./{}-x{}y{}.png".format(deviceId, clickPoint.x(), clickPoint.y()), frame)
    except Exception as e:
        try:
            logger.exception("{}识别四小人异常".format(deviceId))
        finally:
            e = None
            del e

def checkAtDaoJu(deviceId):
    atDaoJuPoint = findPic(deviceId, "当前在道具栏")
    if atDaoJuPoint is None:
        click(deviceId, QPoint(400, 85))
        time.sleep(random.uniform(1, 2))
    return True