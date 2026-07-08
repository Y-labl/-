
import base64, json, random, time, numpy as np
from PyQt5.QtCore import QPoint
from loguru import logger
import const
from common.util.click_util import click
from common.util.color_util import isShowPopColorDK, isShowRoleAvatar
from common.util.log_util import logUtil
from common.util.math_util import distance_between_points
from common.util.scrcpy_util import scrcpyUtil, DeviceWidth, DeviceHeight
from common.util.tuling_client import detect_npc_position
import cv2

def findPic(deviceId, imgName, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, withDoubleClick=False, similar=0.8, clickWaitT=0.3):
    return None

def findPics(deviceId, imgNames, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, withDoubleClick=False, similar=0.8, clickWaitT=0.3):
    return []

def findOneFromPics(deviceId, imgNames, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, similar=0.8, perT=0.5, totalT=10):
    return (None, None)

def waitAssertImgOk(deviceId, imgName, left=0, top=0, width=DeviceWidth, height=DeviceHeight, withClick=False, withDoubleClick=False, middleImgNames=None, middleFunc=None, similar=0.8, perT=0.5, totalT=10):
    return False

def waitAssertFuncOk(deviceId, func, top=0, left=0, width=DeviceWidth, height=DeviceHeight, middleImgNames=None, middleFunc=None, perT=0.5, totalT=10):
    return False

def getImgSize(img):
    if img is not None:
        return img.shape[:2][::-1]
    return (0, 0)

def isInPk(deviceId):
    return False

def isShowFourPerson(deviceId):
    return False

def findFourPersonAndClick(deviceId, left=227, top=80, width=360, height=150):
    pass

def checkAtDaoJu(deviceId):
    return True

def cv_imread(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), -1)
