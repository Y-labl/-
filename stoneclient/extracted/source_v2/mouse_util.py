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
            try:
                # 1. 获取窗口左上角屏幕坐标
                rect = win32gui.GetWindowRect(hwnd)
                # 2. 计算绝对屏幕坐标（窗口左上角 + 窗口内相对偏移）
                abs_x = rect[0] + mouseInfo.mPoint.x()
                abs_y = rect[1] + mouseInfo.mPoint.y()
                self.mouse_log_singal.emit(mouseInfo.mTip + " abs=(" + str(abs_x) + "," + str(abs_y) + ") rect=" + str(rect))
                # 3. 移动鼠标到绝对坐标
                win32api.SetCursorPos((abs_x, abs_y))
                time.sleep(0.1)
                # 4. 模拟鼠标点击
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            except Exception as e:
                position = win32api.MAKELONG(mouseInfo.mPoint.x(), mouseInfo.mPoint.y())
                win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
                win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)
        else:
            self.mouse_log_singal.emit("窗口无效:" + mouseInfo.mTip)

    def doubleClick(self, hwnd, mouseInfo: MouseInfo):
        if win32gui.IsWindow(hwnd):
            self.mouse_log_singal.emit(mouseInfo.mTip)
            try:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.15)
                rect = win32gui.GetWindowRect(hwnd)
                abs_x = rect[0] + mouseInfo.mPoint.x()
                abs_y = rect[1] + mouseInfo.mPoint.y()
                win32api.SetCursorPos((abs_x, abs_y))
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.1)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            except:
                position = win32api.MAKELONG(mouseInfo.mPoint.x(), mouseInfo.mPoint.y())
                win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
                win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)
                time.sleep(0.1)
                win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
                win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)
        else:
            self.mouse_log_singal.emit("窗口无效:" + mouseInfo.mTip)


mouseUtil = MouseUtil()
