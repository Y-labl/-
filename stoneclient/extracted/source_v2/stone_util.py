# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: stone_util.py
# Compiled at: 2026-07-01 07:28:40
# Size of source mod 2**32: 595 bytes
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont
from pyqt_toast import Toast

def toast(self, text):
    t = Toast(text=("   " + text + "   "), duration=2.5, parent=self)
    fontSize16 = QFont()
    fontSize16.setPointSize(16)
    t.setFont(fontSize16)
    t.setOpacity(1.0)
    t.show()


app_data = QSettings("config.ini", QSettings.IniFormat)
app_data.setIniCodec("UTF-8")
