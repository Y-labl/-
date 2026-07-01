# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\infobar_util.py
from qfluentwidgets import InfoBar, InfoBarPosition
from PyQt5.QtCore import Qt, QObject

class InfoBarUtil(QObject):

    def __init__(self):
        super().__init__()

    def success(self, content, duration=3000, parent=None):
        info = InfoBar.success("", content, duration=duration, parent=parent)
        info.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        info.show()

    def warning(self, content, duration=3000, parent=None):
        info = InfoBar.warning(" ", content, duration=duration, parent=parent)
        info.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        info.show()

    def error(self, content, duration=3000, parent=None):
        info = InfoBar.error("", content, duration=duration, parent=parent)
        info.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        info.show()


infoBarUtil = InfoBarUtil()
