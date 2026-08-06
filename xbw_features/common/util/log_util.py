# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: common\util\log_util.py
import sys
from datetime import datetime
import os, traceback
from loguru import logger
from xbw_features.common.util.time_util import getNow, getLogTime
from xbw_features import const

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
    return os.path.join(const.PROJECT_DIR, "有效日志")


def logTmpPath():
    return os.path.join(const.PROJECT_DIR, "临时文件")


def initLog():
    logger.remove()
    logger.add(f"{logRootPath()}/runtime_{getLogTime()}.log",
      encoding="utf-8",
      rotation="1 day",
      retention="15 days",
      compression="zip",
      format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    def exception_handler(record):
        return True

    logger.add((sys.stderr), enqueue=True)
    sys.excepthook = handle_exception


def getLogPath(deviceId):
    deviceId = deviceId.replace(":", "")
    logPathWithDate = logRootPath() + "/" + deviceId + "/" + datetime.now().strftime("%Y-%m-%d")
    if not os.path.isdir(logRootPath() + "/" + deviceId):
        os.makedirs(logRootPath() + "/" + deviceId, exist_ok=True)
    if not os.path.isdir(logPathWithDate):
        os.mkdir(logPathWithDate)
    return logPathWithDate


def orderLog(deviceId, content, isWrite=True):
    logger.info(f"{deviceId}:{content}")
    from xbw_features import backend as _backend
    _backend.log(deviceId, content)
    now = getNow()
    timeStr = now.strftime("%Y-%m-%d %H:%M:%S秒%f")[:-3] + ": "
    content = timeStr + content + "\n"
    if isWrite:
        with open((getLogPath(deviceId) + "\\" + now.strftime("%H时") + ".txt"), "a", encoding="utf-8") as f:
            f.write(content)


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    捕获未处理异常，并写入本地 crash 日志文件
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    LOG_FILE = checkAndCreateCrashLog()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f'\n{"============================================================"}\n')
        f.write(f"Crash Time: {timestamp}\n")
        f.write(f"Exception Type: {exc_type.__name__}\n")
        f.write(f"Exception Value: {exc_value}\n")
        f.write("Traceback:\n")
        f.write(error_msg)
        f.write(f'{"============================================================"}\n')
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("程序发生致命异常，即将崩溃")


def checkAndCreateCrashLog():
    if not os.path.isdir("./报错日志"):
        os.mkdir("./报错日志")
    errorLogFile = "./报错日志/报错日志{}.log".format(datetime.now().strftime("%Y-%m-%d-%H"))
    if not os.path.exists(errorLogFile):
        with open(errorLogFile, "w") as file2:
            file2.write("Hello World!\n")
    return errorLogFile
