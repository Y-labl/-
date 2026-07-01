# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\config\cw_jingjing_config_win.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import BodyLabel, TransparentToolButton, FluentIcon, PushButton, CardWidget, CheckBox
from common.model.baotu_config_model import json2BaoTuConfigModel
from common.model.cw_changjing_config_model import json2CWChangJingConfigModel, cWChangJingConfig2Json
from common.model.deal_order_model import DealOrderModel
from common.util.common_util import toast
from common.util.net_util import NetUtil
from const import API_DEALORDER_UPDATE

class CWChangJingConfigWin(CardWidget):
    refresh_info_singal = pyqtSignal(DealOrderModel)

    def __init__(self, dealOrder):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.saveBtn = PushButton(FluentIcon.SAVE, "保存配置")
        self.saveBtn.clicked.connect(self.saveConfig)
        self.saveBtn.setFixedWidth(120)
        self.layout.addWidget(self.saveBtn)
        self.dealOrder = dealOrder
        self.cwChangJingConfig = json2CWChangJingConfigModel(self.dealOrder.cwchangjingconfig)
        self.initUI()
        self.netUtil1 = None

    def initUI(self):
        self.isWaQiLinShanCheckBox = CheckBox("是队长")
        self.isWaQiLinShanCheckBox.setChecked(self.cwChangJingConfig.isDuiZhang)

    def saveConfig(self):
        isDuiZhang = self.isWaQiLinShanCheckBox.checkState() == 2
        updateConfigModelDic = {"isDuiZhang": isDuiZhang}
        postParam = {'id':(self.dealOrder).id, 
         'cwchangjingconfig':cWChangJingConfig2Json(updateConfigModelDic)}
        self.netUtil1 = NetUtil()
        self.netUtil1.postRequest(self, API_DEALORDER_UPDATE, postParam)
        self.netUtil1.callback.connect(lambda reponse: self._dealPostRes(reponse, updateConfigModelDic))

    def _dealPostRes(self, responseJson, updateConfigModelDic):
        if responseJson is not None:
            toast(self, "设置成功")
            self.dealOrder.cwchangjingconfig = cWChangJingConfig2Json(updateConfigModelDic)
            self.refresh_info_singal.emit(self.dealOrder)
