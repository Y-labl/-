# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\config\changjing_config_win.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from loguru import logger
from qfluentwidgets import BodyLabel, PushButton, FluentIcon

class ChangJingConfigWin(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.saveBtn = PushButton(FluentIcon.SAVE, "保存配置")
        self.saveBtn.setFixedWidth(120)
        layout.addWidget(self.saveBtn)
        logger.info("场景配置init")
