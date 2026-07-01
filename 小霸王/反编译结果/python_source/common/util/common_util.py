# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\common_util.py
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont
from pyqt_toast import Toast
import wmi
c = wmi.WMI()

def toast(self, text, duration=2):
    t = Toast(text=("   " + text + "   "), duration=duration, parent=self)
    fontSize16 = QFont()
    fontSize16.setPointSize(16)
    t.setFont(fontSize16)
    t.setOpacity(1.0)
    t.show()


def getDeviceId():
    for board_info in c.Win32_BaseBoard():
        motherboard_id = board_info.SerialNumber
        if motherboard_id:
            return motherboard_id


app_data = QSettings("config.ini", QSettings.IniFormat)
app_data.setIniCodec("UTF-8")
