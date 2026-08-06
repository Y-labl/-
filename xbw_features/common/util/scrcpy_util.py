# -*- coding: utf-8 -*-
# 反编译 scrcpy_util.py 适配版：不再依赖 pyscrcpy 客户端，
# 取帧 / 取色 / 手机边界全部通过 xbw_features.backend（ADB 或引擎注入）。

from xbw_features.qtcompat import QPoint, QColor
from xbw_features import backend
from loguru import logger

DeviceWidth = 800
DeviceHeight = 448


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
        # 原实现返回 scrcpy 客户端；适配层无客户端，保留方法供兼容
        return None

    def getPointColor(self, deviceId, point):
        try:
            frame = self.getFrame(deviceId)
            if frame is None:
                return QColor()
            pixel_bgr = frame[point.y(), point.x()]
            return QColor(pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])
        except Exception as e:
            logger.debug(f"获取颜色异常:{e}")
            return QColor()

    def getFrame(self, deviceId):
        return backend.get_frame(deviceId)

    def getSize(self, deviceId):
        frame = self.getFrame(deviceId)
        if frame is None:
            return QPoint(DeviceWidth, DeviceHeight)
        h, w = frame.shape[:2]
        return QPoint(w, h)

    def isLandscape(self, deviceId):
        sizePoint = self.getSize(deviceId)
        return sizePoint.x() == DeviceWidth

    def getNewMOffset(self, deviceId):
        offsetX = self.deviceNewMOffsetMap.get(deviceId)
        if offsetX is not None:
            return offsetX
        from xbw_features.common.util.color_util import culNewMobileXOffset
        offsetX = culNewMobileXOffset(deviceId)
        self.deviceNewMOffsetMap[deviceId] = offsetX
        logger.debug(f"{deviceId} 设置手机边界：{offsetX}")
        return offsetX

    def stop(self, deviceId):
        backend.clear_cache(deviceId)


scrcpyUtil = ScrcpyUtil()
