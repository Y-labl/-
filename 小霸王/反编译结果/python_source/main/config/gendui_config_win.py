# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\config\gendui_config_win.py
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import BodyLabel, TransparentToolButton, FluentIcon, PushButton, CardWidget, CheckBox, ComboBox, ProgressBar, RangeSettingCard, Slider
from common.model.cw_changjing_config_model import json2CWChangJingConfigModel, cWChangJingConfig2Json
from common.model.deal_order_model import DealOrderModel
from common.model.gendui_config_model import genDuiConfig2Json, json2GenDuiConfigModel
from common.util.common_util import toast
from common.util.net_util import NetUtil
from const import API_DEALORDER_UPDATE
addXueModes = [
 "秘制", "红碗", "酒肆"]
addLanModes = ["秘制", "蓝碗", "酒肆"]

class GenDuiConfigWin(CardWidget):
    refresh_info_singal = pyqtSignal(DealOrderModel)

    def __init__(self, dealOrder):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.saveBtn = PushButton(FluentIcon.SAVE, "保存配置")
        self.saveBtn.clicked.connect(self.saveConfig)
        self.saveBtn.setFixedWidth(120)
        self.layout.addWidget(self.saveBtn)
        self.dealOrder = dealOrder
        self.genduiConfig = json2GenDuiConfigModel(self.dealOrder.genduiconfig)
        self.initUI()
        self.netUtil1 = None

    def initUI(self):
        self.roleAddXueContainer = QWidget()
        self.roleAddXueContainerLayout = QHBoxLayout()
        self.roleAddXueContainerLayout.setAlignment(Qt.AlignLeft)
        self.roleAddXueContainer.setLayout(self.roleAddXueContainerLayout)
        self.roleAddXueTip = BodyLabel("人物加血方式：")
        self.roleAddXueModeComboBox = ComboBox(self)
        self.roleAddXueModeComboBox.setFixedWidth(80)
        self.roleAddXueModeComboBox.addItems(addXueModes)
        self.roleAddXueModeComboBox.setCurrentText(self.genduiConfig.roleAddXueMode)
        self.roleAddXueContainerLayout.addWidget(self.roleAddXueTip)
        self.roleAddXueContainerLayout.addWidget(self.roleAddXueModeComboBox)
        self.roleAddXueContainerLayout.addSpacing(30)
        self.roleAddLanTip = BodyLabel("人物加蓝方式：")
        self.roleAddLanModeComboBox = ComboBox(self)
        self.roleAddLanModeComboBox.setFixedWidth(80)
        self.roleAddLanModeComboBox.addItems(addLanModes)
        self.roleAddLanModeComboBox.setCurrentText(self.genduiConfig.roleAddLanMode)
        self.roleAddXueContainerLayout.addWidget(self.roleAddLanTip)
        self.roleAddXueContainerLayout.addWidget(self.roleAddLanModeComboBox)
        self.roleXuePercentContainer = QWidget()
        self.roleXuePercentContainerLayout = QHBoxLayout()
        self.roleXuePercentContainerLayout.setAlignment(Qt.AlignLeft)
        self.roleXuePercentContainer.setLayout(self.roleXuePercentContainerLayout)
        self.roleAddXuePercentTip = BodyLabel("人物血量低于时补充：")
        self.roleXuePercentBar = Slider(Qt.Horizontal)
        self.roleXuePercentBar.setThemeColor(QColor(255, 20, 147), QColor(255, 20, 147))
        self.roleXuePercentBar.setRange(0, 100)
        self.roleXuePercentBar.setValue(int(self.genduiConfig.roleXuePercent))
        self.roleAddLanPercentTip = BodyLabel("人物蓝量低于时补充：")
        self.roleLanPercentBar = Slider(Qt.Horizontal)
        self.roleLanPercentBar.setThemeColor(QColor(30, 144, 255), QColor(30, 144, 255))
        self.roleLanPercentBar.setRange(0, 100)
        self.roleLanPercentBar.setValue(int(self.genduiConfig.roleLanPercent))
        self.roleXuePercentContainerLayout.addWidget(self.roleAddXuePercentTip)
        self.roleXuePercentContainerLayout.addWidget(self.roleXuePercentBar)
        self.roleAddXueContainerLayout.addSpacing(30)
        self.roleXuePercentContainerLayout.addWidget(self.roleAddLanPercentTip)
        self.roleXuePercentContainerLayout.addWidget(self.roleLanPercentBar)
        self.layout.addWidget(self.roleAddXueContainer)
        self.layout.addWidget(self.roleXuePercentContainer)

    def saveConfig(self):
        roleAddXueMode = self.roleAddXueModeComboBox.text()
        roleAddLanMode = self.roleAddLanModeComboBox.text()
        roleXuePercent = self.roleXuePercentBar.value()
        roleLanPercent = self.roleLanPercentBar.value()
        updateConfigModelDic = {
          'roleAddXueMode': roleAddXueMode,
          'roleAddLanMode': roleAddLanMode,
          'roleXuePercent': roleXuePercent,
          'roleLanPercent': roleLanPercent}
        postParam = {'id':(self.dealOrder).id, 
         'genduiconfig':genDuiConfig2Json(updateConfigModelDic)}
        self.netUtil1 = NetUtil()
        self.netUtil1.postRequest(self, API_DEALORDER_UPDATE, postParam)
        self.netUtil1.callback.connect(lambda reponse: self._dealPostRes(reponse, updateConfigModelDic))

    def _dealPostRes(self, responseJson, updateConfigModelDic):
        if responseJson is not None:
            toast(self, "设置成功")
            self.dealOrder.genduiconfig = genDuiConfig2Json(updateConfigModelDic)
            self.refresh_info_singal.emit(self.dealOrder)
