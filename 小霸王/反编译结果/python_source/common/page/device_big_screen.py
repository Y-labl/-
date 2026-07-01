# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\page\device_big_screen.py
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from common.util.widget_util import showPilImage

class DeviceBigScreen(QMainWindow):

    def __init__(self, deviceId, thumbBytes):
        super(DeviceBigScreen, self).__init__()
        self.setWindowTitle(deviceId)
        self.container = QWidget()
        self.containerLayout = QVBoxLayout()
        self.container.setLayout(self.containerLayout)
        self.imgLabel = QLabel()
        showPilImage(thumbBytes, (self.imgLabel), scale=2)
        self.containerLayout.addWidget(self.imgLabel)
        self.setCentralWidget(self.container)
