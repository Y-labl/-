# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: vmdiff_util.py
from PyQt5.QtCore import QPoint
from const import VmXiaoyao, VmLeidian, VmXiaoyaoOtherType, VmScrcpy

def VmWinType(className):
    if className == "Qt5QWindowIcon":
        return VmXiaoyao
    if className == VmXiaoyaoOtherType:
        return VmXiaoyao
    if className == "LDPlayerMainFrame":
        return VmLeidian
    if className == "SDL_app":
        return VmScrcpy


def VmPointOffset(vmType):
    if vmType == VmXiaoyao:
        return QPoint(0, -2)
    if vmType == VmScrcpy:
        return QPoint(0, 0)  # scrcpy 无窗口边框偏移
    return QPoint(0, 0)


def VmGxPoint(vmType):
    if vmType == VmXiaoyao:
        return QPoint(680, 235)
    if vmType == VmScrcpy:
        return QPoint(680, 235)  # scrcpy 与逍遥坐标一致
    return QPoint(680, 204)


def VmBuyPoint(vmType):
    if vmType == VmXiaoyao:
        return QPoint(580, 435)
    if vmType == VmScrcpy:
        return QPoint(580, 435)  # scrcpy 与逍遥坐标一致
    return QPoint(580, 404)
