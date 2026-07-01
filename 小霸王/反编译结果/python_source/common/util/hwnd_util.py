# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\hwnd_util.py
import base64, os, uuid, win32con, win32gui
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication

class HWNDUtil(QObject):

    def __init__(self):
        super().__init__()

    def findWinsByNames(self, finWinNames):
        wins = []
        win32gui.EnumWindows(lambda hwnd, mouse: self.getMHWinList(hwnd, mouse, finWinNames, wins), 0)
        return wins

    def getMHWinList(self, hwnd, mouse, finWinNames, wins):
        if win32gui.IsWindow(hwnd):
            if win32gui.IsWindowEnabled(hwnd):
                if win32gui.IsWindowVisible(hwnd):
                    winName = win32gui.GetWindowText(hwnd)
                    if win32gui.GetClassName(hwnd) == "Qt5152QWindowIcon":
                        for finName in finWinNames:
                            if finName in winName and winName not in wins:
                                wins.append(winName)

    def disable_minimize(self, hwnd):
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        new_style = style & ~win32con.WS_MINIMIZEBOX
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED)


hwndUtil = HWNDUtil()
