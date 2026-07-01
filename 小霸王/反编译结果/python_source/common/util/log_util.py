# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\log_util.py
import sys
from datetime import datetime
import os
from loguru import logger
from common.util.time_util import getNow, getLogTime

class LogUtil(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = (object.__new__)(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.parentPath = ""

    def getParentPath(self):
        return self.parentPath

    def setParentPath(self, parentPath):
        self.parentPath = parentPath


logUtil = LogUtil()

def logRootPath():
    return logUtil.getParentPath() + "小霸王/有效日志"


def initLog():
    logger.remove()
    logger.add((sys.stdout),
      format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
      colorize=True)
    logger.add(f"{logRootPath()}/runtime{getLogTime()}.log",
      encoding="utf-8",
      rotation="1 day",
      retention="15 days",
      compression="zip",
      format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")


def getLogPath(orderId):
    logPathWithDate = logRootPath() + "/" + orderId + "/" + datetime.now().strftime("%Y-%m-%d")
    if not os.path.isdir(logRootPath() + "/" + orderId):
        os.mkdir(logRootPath() + "/" + orderId)
    if not os.path.isdir(logPathWithDate):
        os.mkdir(logPathWithDate)
    return logPathWithDate


def orderLog(order, content, isWrite=True):
    orderId = ""
    if order is not None:
        orderId = order.id
    now = getNow()
    timeStr = now.strftime("%Y-%m-%d %H:%M:%S秒%f")[None[:-3]] + ": "
    content = timeStr + content + "\n"
    if isWrite:
        with open((getLogPath(orderId) + "\\" + now.strftime("%H时") + ".txt"), "a", encoding="utf-8") as f:
            f.write(content)
