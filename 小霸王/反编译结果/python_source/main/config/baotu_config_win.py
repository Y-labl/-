# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\config\baotu_config_win.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import BodyLabel, TransparentToolButton, FluentIcon, PushButton, CardWidget, CheckBox
from common.model.baotu_config_model import json2BaoTuConfigModel

class BaoTuConfigWin(CardWidget):

    def __init__(self, dealOrder):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.saveBtn = PushButton(FluentIcon.SAVE, "保存配置")
        self.saveBtn.setFixedWidth(120)
        self.layout.addWidget(self.saveBtn)
        self.dealOrder = dealOrder
        self.baotuConfig = json2BaoTuConfigModel(self.dealOrder.baotuconfig)
        self.initUI()

    def initUI(self):
        self.isWaQiLinShanCheckBox = CheckBox("挖麒麟山宝图")
        self.isWaQiLinShanCheckBox.setChecked(self.baotuConfig.isWaQiLinShan)
        self.layout.addWidget(self.isWaQiLinShanCheckBox)
