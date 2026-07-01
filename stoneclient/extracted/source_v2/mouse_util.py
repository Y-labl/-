# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: mouse_util.py
import queue, threading, time, win32api, win32con, win32gui
from PyQt5.QtCore import pyqtSignal, QObject

class MouseInfo:

    def __init__(self, point, tip):
        self.mPoint = point
        self.mTip = tip


class MouseUtil(QObject):
    mouse_log_singal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def click(self, hwnd, mouseInfo: MouseInfo):
        if win32gui.IsWindow(hwnd):
            self.mouse_log_singal.emit(mouseInfo.mTip)
            position = win32api.MAKELONG(mouseInfo.mPoint.x(), mouseInfo.mPoint.y())
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)
        else:
            self.mouse_log_singal.emit("窗口无效:" + mouseInfo.mTip)

    def doubleClick(self, hwnd, mouseInfo: MouseInfo):
        if win32gui.IsWindow(hwnd):
            self.mouse_log_singal.emit(mouseInfo.mTip)
            position = win32api.MAKELONG(mouseInfo.mPoint.x(), mouseInfo.mPoint.y())
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)
            time.sleep(0.1)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)
        else:
            self.mouse_log_singal.emit("窗口无效:" + mouseInfo.mTip)


mouseUtil = MouseUtil()
