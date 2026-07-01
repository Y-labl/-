# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\thread\device_android_thread.py
import time
from PyQt5.QtCore import QThread, pyqtSignal
from common.util.adb_util import adbUtil

class DeviceAndroidThread(QThread):
    result_signal = pyqtSignal(list)

    def __init__(self):
        super(DeviceAndroidThread, self).__init__()
        self.isGetOne = True

    def run(self):
        isScreenshot = False
        while True:
            if self.isGetOne:
                deviceModels = adbUtil.getDeviceModels(isScreenshot=isScreenshot)
                self.result_signal.emit(deviceModels)
                self.isGetOne = False
            if isScreenshot is False:
                isScreenshot = True
                deviceModels = adbUtil.getDeviceModels(isScreenshot=isScreenshot)
                self.result_signal.emit(deviceModels)
            time.sleep(1)

    def setGetOne(self):
        self.isGetOne = True
