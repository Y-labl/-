# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: robot_thread.py
import time, win32gui
from PyQt5.QtCore import QThread, QPoint, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication
from color_util import isResultPopShow, islvtongResultPopShow, isLvtongText
from const import lvtongResultPopShowPoints
from const import VmXiaoyao, VmScrcpy
from mouse_util import mouseUtil, MouseInfo

class RobotThread(QThread):
    lvtong_signal = pyqtSignal(str)

    def __init__(self, vm, type, parentPath):
        super(RobotThread, self).__init__()
        self.parent = vm.parent
        self.child = vm.child
        self.type = type
        self.winName = vm.winName
        self.parentPath = parentPath

    def run(self):
        if self.type == "startMhRepair":
            self.startMhRepair()
        elif self.type == "enterMh":
            self.enterMh()
        elif self.type == "openClock":
            self.openClock()
        elif self.type == "openGx":
            self.openGx()
        elif self.type == "openPackage":
            self.openPackage()
        elif self.type == "lvtongClick":
            self.lvtongClick()

    def startMhRepair(self):
        if win32gui.IsWindow(self.parent):
            mouseUtil.click(self.parent, MouseInfo(QPoint(127, 160), ""))
            time.sleep(3)
            mouseUtil.click(self.parent, MouseInfo(QPoint(32, 140), ""))
            time.sleep(2)
            mouseUtil.click(self.parent, MouseInfo(QPoint(740, 450), ""))
            time.sleep(2)
            mouseUtil.click(self.parent, MouseInfo(QPoint(740, 387), ""))
            time.sleep(12)
            mouseUtil.click(self.parent, MouseInfo(QPoint(750, 150), ""))
            time.sleep(2)
            mouseUtil.click(self.parent, MouseInfo(QPoint(490, 350), ""))
            time.sleep(4)
            mouseUtil.click(self.parent, MouseInfo(QPoint(740, 387), ""))
            time.sleep(3)
            mouseUtil.click(self.parent, MouseInfo(QPoint(600, 310), ""))
            time.sleep(3)
            mouseUtil.click(self.parent, MouseInfo(QPoint(740, 387), ""))
            time.sleep(6)
            mouseUtil.click(self.parent, MouseInfo(QPoint(500, 330), ""))

    def enterMh(self):
        mouseUtil.click(self.parent, MouseInfo(QPoint(400, 410), ""))

    def openClock(self):
        mouseUtil.click(self.parent, MouseInfo(QPoint(713, 476), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(425, 430), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(482, 437), ""))
        time.sleep(2)
        mouseUtil.click(self.parent, MouseInfo(QPoint(640, 366), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(611, 476), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(179, 312), ""))
        time.sleep(1)
        mouseUtil.click(self.parent, MouseInfo(QPoint(179, 312), ""))
        time.sleep(1)
        mouseUtil.click(self.parent, MouseInfo(QPoint(179, 312), ""))
        time.sleep(1)
        mouseUtil.click(self.parent, MouseInfo(QPoint(179, 312), ""))
        time.sleep(1)
        mouseUtil.click(self.parent, MouseInfo(QPoint(278, 154), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(680, 91), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(650, 84), ""))

    def openGx(self):
        from vmdiff_util import VmGxPoint, VmBuyPoint
        from const import VmXiaoyao, VmXiaoyaoOtherType, VmLeidian, VmScrcpy
        class_name = win32gui.GetClassName(self.parent)
        if class_name in (VmXiaoyao, VmXiaoyaoOtherType, VmLeidian, VmScrcpy):
            vm_type = class_name
        else:
            vm_type = VmScrcpy
        # 逍遥模拟器：多步导航
        if class_name in (VmXiaoyao, VmXiaoyaoOtherType):
            mouseUtil.click(self.parent, MouseInfo(QPoint(24, 181), ""))
            time.sleep(2)
            mouseUtil.click(self.parent, MouseInfo(QPoint(28, 408), ""))
            time.sleep(2)
        # 点击兑换功勋按钮（使用实测坐标，不缩放）
        gx_point = VmGxPoint(vm_type)
        time.sleep(0.5)  # 等待窗口焦点
        mouseUtil.click(self.parent, MouseInfo(gx_point, "兑换功勋(" + str(gx_point.x()) + "," + str(gx_point.y()) + ")"))
        time.sleep(2)
        # 注意：不自动点确认，因为弹窗坐标和主界面不同
        # 请使用"测试点击确认按钮"来单独测试确认位置

    def openPackage(self):
        mouseUtil.click(self.parent, MouseInfo(QPoint(712, 476), ""))
        time.sleep(1.5)
        mouseUtil.click(self.parent, MouseInfo(QPoint(651, 94), ""))

    def lvtongClick(self):
        mouseUtil.click(self.parent, MouseInfo(QPoint(700, 350), ""))
        time.sleep(0.3)
        while True:
            screen = QApplication.primaryScreen()
            img = screen.grabWindow(self.parent).toImage()
            if islvtongResultPopShow(img):
                if isLvtongText(img):
                    self.lvtong_signal.emit("{}抢到了绿通".format(self.winName))
                else:
                    self.lvtong_signal.emit("{}没抢到绿通".format(self.winName))
                return
            time.sleep(0.2)
