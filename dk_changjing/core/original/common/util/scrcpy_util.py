# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\scrcpy_util.py
import time
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
from pyscrcpy import Client
from loguru import logger
DeviceWidth = 1080
DeviceHeight = 1920

class ScrcpyUtil(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = (object.__new__)(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.deviceClientMap = {}
        self.deviceNewMOffsetMap = {}

    def getClient(self, deviceId):
        client = self.deviceClientMap.get(deviceId)
        if client:
            if client.alive:
                return client
            client.stop()
        logger.debug(f"{deviceId} 设备开始初始化")
        client = Client(deviceId, bitrate=8000000, max_fps=10, max_size=1920)
        try:
            client.start(threaded=True)
        except Exception as e:
            logger.debug(f"{deviceId} scrcpy start 异常: {e}")
            return None

        if not client.alive:
            logger.debug(f"设备{deviceId}不在线, 重试连接设备")
            time.sleep(3)
            return self.getClient(deviceId)

        # 等待 resolution 就绪（stream_loop 收到首帧后设置）
        for _ in range(20):
            if client.resolution is not None:
                break
            time.sleep(0.25)

        if client.resolution is None:
            logger.warning(f"{deviceId} scrcpy 连接成功但未收到视频帧")
        else:
            self.deviceClientMap[deviceId] = client
            logger.debug(f"{deviceId} 设备初始化完成: 分辨率({client.resolution[0]}, {client.resolution[1]})")
        return client

    def getPointColor(self, deviceId, point: QPoint) -> QColor:
        try:
            scrcpyClient = self.getClient(deviceId)
            pixel_bgr = scrcpyClient.last_frame[(point.y(), point.x())]
            return QColor(pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])
        except Exception as e:
            logger.debug(f"获取颜色异常:{e}")
            return QColor()

    def getFrame(self, deviceId):
        scrcpyClient = self.getClient(deviceId)
        return scrcpyClient.last_frame

    def getSize(self, deviceId):
        client = self.getClient(deviceId)
        if client is None:
            return QPoint(DeviceWidth, DeviceHeight)
        resolution = client.resolution
        if resolution is None:
            return QPoint(DeviceWidth, DeviceHeight)
        return QPoint(resolution[0], resolution[1])

    def isLandscape(self, deviceId):
        sizePoint = self.getSize(deviceId)
        isLand = sizePoint.x() == DeviceWidth
        return isLand

    def getNewMOffset(self, deviceId):
        offsetX = self.deviceNewMOffsetMap.get(deviceId)
        if offsetX is not None:
            return offsetX
        from common.util.color_util import culNewMobileXOffset
        offsetX = culNewMobileXOffset(deviceId)
        self.deviceNewMOffsetMap[deviceId] = offsetX
        logger.debug(f"{deviceId} 设置手机边界：{offsetX}")
        return offsetX

    def stop(self, deviceId):
        client = self.deviceClientMap.get(deviceId)
        if client:
            client.stop()


scrcpyUtil = ScrcpyUtil()
