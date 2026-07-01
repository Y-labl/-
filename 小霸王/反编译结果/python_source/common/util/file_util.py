# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\file_util.py
from PyQt5.QtWidgets import QFileDialog
from common.util.time_util import getLogTime

def selectPngPath(self):
    file_path, _ = QFileDialog.getSaveFileName(parent=self,
      caption="保存 PNG 截图",
      directory=f"./{getLogTime()}.png",
      filter="PNG 图片 (*.png)")
    if not file_path:
        return
    if not file_path.endswith(".png"):
        file_path += ".png"
    return file_path
