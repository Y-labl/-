# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\adb_util.py
import random, re, subprocess, time, webbrowser
from PyQt5.QtCore import QObject, QPoint
from adbutils import adb
from loguru import logger
from common.model.device_android_model import DeviceAndroidModel
from common.util.log_util import logUtil

class AdbUtil(QObject):

    def __init__(self):
        super().__init__()

    def getDeviceModels(self, isScreenshot=False):
        device_model_list = []
        try:
            devices = adb.device_list()
            for device in devices:
                deviceId = device.serial
                if "-" in deviceId:
                    break
                deviceXy = ""
                thumbBytes = None
                try:
                    wmsize = device.shell("wm size")
                    if "Override size" in wmsize:
                        deviceXy = wmsize.split("Override size: ")[1]
                    else:
                        if "size" in wmsize:
                            deviceXy = wmsize.split("size: ")[1]
                        elif deviceXy != "1920x1080" and deviceXy != "1080x1920":
                            updateRes = self.modifyDeviceXY(deviceId)
                            if "WRITE_SECURE_SETTING" in updateRes:
                                webbrowser.open("http://localhost:3000/adb-tools (本地开发模式)")
                            time.sleep(2)
                        if isScreenshot:
                            thumbBytes = device.screenshot()
                except Exception as e:
                    try:
                        logger.debug("getDeviceModels异常：{}".format(e))
                    finally:
                        e = None
                        del e

                else:
                    device_android_model = DeviceAndroidModel(deviceId, deviceXy, thumbBytes)
                    device_model_list.append(device_android_model)

        except Exception as e:
            try:
                logger.debug(e)
            finally:
                e = None
                del e

        else:
            return device_model_list

    def isDeviceExist(self, deviceId):
        try:
            device = adb.device(deviceId)
            info = device.info
        except:
            return False

        return True

    def getGameVersion(self, deviceId):
        # [Decompilation incomplete - returning placeholder]
        return (None, None)

    def getDeviceXy(self, deviceId):
        deviceXy = ""
        try:
            device = adb.device(deviceId)
            wmsize = device.shell("wm size")
            if "Override size" in wmsize:
                deviceXy = wmsize.split("Override size: ")[1]
            else:
                if "size" in wmsize:
                    deviceXy = wmsize.split("size: ")[1]
        except:
            pass
        else:
            return deviceXy

    def modifyDeviceXY(self, deviceId):
        # [Decompilation incomplete - returning placeholder]
        return None

    def disUpdate(self):
        # [Decompilation incomplete]
        pass

    def runAdbShell(self, deviceId):
        adbShell = subprocess.Popen([
         "adb", "-s", deviceId, "shell"],
          stdin=(subprocess.PIPE),
          stdout=(subprocess.PIPE),
          stderr=(subprocess.PIPE),
          encoding="utf-8")
        return adbShell

    def stopAdbShell(self, adbShell):
        if adbShell is not None:
            try:
                try:
                    adbShell.stdin.close()
                    adbShell.terminate()
                    adbShell.wait(timeout=2)
                except Exception as e:
                    try:
                        logger.debug(f"关闭ADB长连接出错：{e}")
                    finally:
                        e = None
                        del e

            finally:
                adbShell = None

    def reBackDeviceXY(self, deviceId):
        # [Decompilation incomplete]
        pass

    def isScreen90or270(self, deviceId):
        # [Decompilation incomplete]
        return False

    # [Decompilation error - skipped]

    # [Decompilation error - skipped]

    # [Decompilation error - skipped]

    # [Decompilation error - skipped]

    # [Decompilation error - skipped]

    # [Decompilation error - skipped]

    def compareDeviceAndroidModel(self, modelListNeedIgnoreLeidian, modelList2):
        modelList1 = []
        for model in modelListNeedIgnoreLeidian:
            if "(64)" not in model.deviceId:
                modelList1.append(model)
        else:
            if len(modelList1) != len(modelList2):
                return False

        for index in range(len(modelList1)):
            model1 = modelList1[index]
            model2 = modelList2[index]
            if model1.deviceId != model2.deviceId:
                    return False
            if model1.deviceXy != model2.deviceXy:
                    return False
            return True


adbUtil = AdbUtil()