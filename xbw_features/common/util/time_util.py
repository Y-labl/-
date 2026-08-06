# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: common\util\time_util.py
import time
from datetime import datetime, timedelta
from loguru import logger
sysTDur = 0

def getNow():
    return datetime.now() - timedelta(milliseconds=sysTDur)


def isExpire(expireTime):
    if expireTime is None:
        return True
    nowTime = getNow()
    autoPingTimerTime = datetime.strptime(expireTime, "%Y-%m-%d %H:%M:%S")
    return (autoPingTimerTime - nowTime).total_seconds() < 0


def expireTimeShow(expireTimeStr):
    expireText = "无"
    if expireTimeStr:
        dt = datetime.strptime(expireTimeStr, "%Y-%m-%d %H:%M:%S")
        if isExpire(expireTimeStr):
            expireText = "{}(已过期)".format(dt.strftime("%m-%d %H:%M"))
        else:
            expireText = dt.strftime("%m-%d %H:%M")
    return expireText


def getLogTime():
    return getNow().strftime("%m-%d-%H-%M-%S-%f")[:-3]


def getLogTimeHour():
    return getNow().strftime("%m-%d-%H")


def durationSeconds(startT, endT):
    duration = 0
    if endT > startT:
        duration = (endT - startT).total_seconds()
    else:
        duration = -(startT - endT).total_seconds()
    return round(duration, 1)


def callTime(func):

    def wrapper(*args, **kwargs):
        start_time = getNow()
        result = func(*args, **kwargs)
        end_time = getNow()
        cost_time = end_time - start_time
        logger.debug(f"方法{func.__name__}耗时: {cost_time.total_seconds()}s")
        return result

    return wrapper
