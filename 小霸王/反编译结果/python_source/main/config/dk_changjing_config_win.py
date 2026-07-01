# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\config\dk_changjing_config_win.py
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import SwitchButton, BodyLabel, HyperlinkButton, FluentIcon, PushButton, CardWidget, CheckBox, ComboBox, ProgressBar, RangeSettingCard, Slider
from common.model.cw_changjing_config_model import json2CWChangJingConfigModel, cWChangJingConfig2Json
from common.model.deal_order_model import DealOrderModel
from common.model.dk_changjing_config_model import dkChangJingConfig2Json, json2DKChangJingConfigModel
from common.model.gendui_config_model import genDuiConfig2Json, json2GenDuiConfigModel
from common.util.common_util import toast
from common.util.net_util import NetUtil
from const import API_DEALORDER_UPDATE
from main.config.dialog.tou_setting_dialog import TouSettingDialog
addXueModes = [
 "秘制", "红碗", "酒肆"]
addLanModes = ["秘制", "蓝碗", "酒肆"]

class DKChangJingConfigWin(CardWidget):
    refresh_info_singal = pyqtSignal(DealOrderModel)

    def __init__(self, dealOrder):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.saveBtn = PushButton(FluentIcon.SAVE, "保存配置")
        self.saveBtn.clicked.connect(self.saveConfig)
        self.saveBtn.setFixedWidth(120)
        self.roleContainer = CardWidget()
        self.roleContainerLayout = QVBoxLayout()
        self.roleContainer.setLayout(self.roleContainerLayout)
        self.layout.addWidget(self.saveBtn)
        self.dealOrder = dealOrder
        self.dkChangJingConfig = json2DKChangJingConfigModel(self.dealOrder.dkchangjingconfig)
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
        self.roleAddXueModeComboBox.setCurrentText(self.dkChangJingConfig.roleAddXueMode)
        self.roleAddXueContainerLayout.addWidget(self.roleAddXueTip)
        self.roleAddXueContainerLayout.addWidget(self.roleAddXueModeComboBox)
        self.roleAddXueContainerLayout.addSpacing(30)
        self.roleAddLanTip = BodyLabel("人物加蓝方式：")
        self.roleAddLanModeComboBox = ComboBox(self)
        self.roleAddLanModeComboBox.setFixedWidth(80)
        self.roleAddLanModeComboBox.addItems(addLanModes)
        self.roleAddLanModeComboBox.setCurrentText(self.dkChangJingConfig.roleAddLanMode)
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
        self.roleXuePercentBar.setValue(int(self.dkChangJingConfig.roleXuePercent))
        self.roleAddLanPercentTip = BodyLabel("人物蓝量低于时补充：")
        self.roleLanPercentBar = Slider(Qt.Horizontal)
        self.roleLanPercentBar.setThemeColor(QColor(30, 144, 255), QColor(30, 144, 255))
        self.roleLanPercentBar.setRange(0, 100)
        self.roleLanPercentBar.setValue(int(self.dkChangJingConfig.roleLanPercent))
        self.roleXuePercentContainerLayout.addWidget(self.roleAddXuePercentTip)
        self.roleXuePercentContainerLayout.addWidget(self.roleXuePercentBar)
        self.roleAddXueContainerLayout.addSpacing(30)
        self.roleXuePercentContainerLayout.addWidget(self.roleAddLanPercentTip)
        self.roleXuePercentContainerLayout.addWidget(self.roleLanPercentBar)
        self.layout.addWidget(self.roleContainer)
        self.roleContainerLayout.addWidget(self.roleAddXueContainer)
        self.roleContainerLayout.addWidget(self.roleXuePercentContainer)
        self.bottomSettingContainer = QWidget()
        self.bottomSettingContainerLayout = QHBoxLayout()
        self.bottomSettingContainer.setLayout(self.bottomSettingContainerLayout)
        self.roleOperateContiner = CardWidget()
        self.roleOperateContiner.setMaximumWidth(240)
        self.roleOperateContinerLayout = QVBoxLayout()
        self.roleOperateContinerLayout.setAlignment(Qt.AlignLeft)
        self.roleOperateContiner.setLayout(self.roleOperateContinerLayout)
        self.roleOperateTitle = BodyLabel("人物战斗操作：")
        self.isBuZhuoSwitch = SwitchButton("一、捕捉")
        self.isBuZhuoSwitch.setOnText("一、捕捉")
        self.isBuZhuoSwitch.setChecked(self.dkChangJingConfig.isZhua)
        self.isTouContainer = QWidget()
        self.isTouContainerLayout = QHBoxLayout()
        self.isTouContainerLayout.setAlignment(Qt.AlignLeft)
        self.isTouContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.isTouContainer.setLayout(self.isTouContainerLayout)
        self.isTouSwitch = SwitchButton("二、妙手空空")
        self.isTouSwitch.setOnText("二、妙手空空")
        self.isTouSwitch.setChecked(self.dkChangJingConfig.isTou)
        self.touSettingBtn = HyperlinkButton("", "设置")
        self.touSettingBtn.clicked.connect(lambda: self.showTouSettingDialog())
        self.isTouContainerLayout.addWidget(self.isTouSwitch)
        self.isTouContainerLayout.addWidget(self.touSettingBtn)
        self.isRoleDoJiNengSwitch = SwitchButton("三、1.点选技能后自动战斗")
        self.isRoleDoJiNengSwitch.setOnText("三、1.点选技能后自动战斗")
        self.isRoleDoJiNengSwitch.setChecked(self.dkChangJingConfig.isPkJiNeng)
        self.isRoleDoJiNengSwitch.checkedChanged.connect(lambda checked: self.rolePkHuChi("isPkJiNeng", checked))
        self.isRoleGongJiSwitch = SwitchButton("       2.普通攻击后自动战斗")
        self.isRoleGongJiSwitch.setOnText("       2.普通攻击后自动战斗")
        self.isRoleGongJiSwitch.setChecked(self.dkChangJingConfig.isPkPuGong)
        self.isRoleGongJiSwitch.checkedChanged.connect(lambda checked: self.rolePkHuChi("isPkPuGong", checked))
        self.isRoleFangYuSwitch = SwitchButton("       3.防御后自动战斗")
        self.isRoleFangYuSwitch.setOnText("       3.防御后自动战斗")
        self.isRoleFangYuSwitch.setChecked(self.dkChangJingConfig.isPkFangYu)
        self.isRoleFangYuSwitch.checkedChanged.connect(lambda checked: self.rolePkHuChi("isPkFangYu", checked))
        self.isRoleAutoSwitch = SwitchButton("       4.直接自动战斗")
        self.isRoleAutoSwitch.setOnText("       4.直接自动战斗")
        self.isRoleAutoSwitch.setChecked(self.dkChangJingConfig.isPkAuto)
        self.isRoleAutoSwitch.checkedChanged.connect(lambda checked: self.rolePkHuChi("isPkAuto", checked))
        self.isRoleTaoPaoSwitch = SwitchButton("       5.逃跑")
        self.isRoleTaoPaoSwitch.setOnText("       5.逃跑")
        self.isRoleTaoPaoSwitch.setChecked(self.dkChangJingConfig.isPkTaoPao)
        self.isRoleTaoPaoSwitch.checkedChanged.connect(lambda checked: self.rolePkHuChi("isPkTaoPao", checked))
        self.roleOperateContinerLayout.addWidget(self.roleOperateTitle)
        self.roleOperateContinerLayout.addWidget(self.isBuZhuoSwitch)
        self.roleOperateContinerLayout.addWidget(self.isTouContainer)
        self.roleOperateContinerLayout.addWidget(self.isRoleDoJiNengSwitch)
        self.roleOperateContinerLayout.addWidget(self.isRoleGongJiSwitch)
        self.roleOperateContinerLayout.addWidget(self.isRoleFangYuSwitch)
        self.roleOperateContinerLayout.addWidget(self.isRoleAutoSwitch)
        self.roleOperateContinerLayout.addWidget(self.isRoleTaoPaoSwitch)
        self.bottomSettingContainerLayout.addWidget(self.roleOperateContiner)
        self.otherSettingContiner = CardWidget()
        self.otherSettingContinerLayout = QVBoxLayout()
        self.otherSettingContinerLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.otherSettingContiner.setLayout(self.otherSettingContinerLayout)
        self.isDuiZhangSwitch = SwitchButton("自动寻路")
        self.isDuiZhangSwitch.setOnText("自动寻路")
        self.isDuiZhangSwitch.setChecked(self.dkChangJingConfig.isDuiZhang)
        self.otherSettingContinerLayout.addWidget(self.isDuiZhangSwitch)
        self.bottomSettingContainerLayout.addWidget(self.otherSettingContiner)
        self.layout.addWidget(self.bottomSettingContainer)

    def rolePkHuChi(self, ziDuan, checked):
        if checked:
            if "isPkJiNeng" != ziDuan:
                self.isRoleDoJiNengSwitch.setChecked(False)
            if "isPkPuGong" != ziDuan:
                self.isRoleGongJiSwitch.setChecked(False)
            if "isPkFangYu" != ziDuan:
                self.isRoleFangYuSwitch.setChecked(False)
            if "isPkAuto" != ziDuan:
                self.isRoleAutoSwitch.setChecked(False)
            if "isPkTaoPao" != ziDuan:
                self.isRoleTaoPaoSwitch.setChecked(False)

    def showTouSettingDialog(self):
        touSettingDialog = TouSettingDialog(self)
        if touSettingDialog.exec():
            pass

    def saveConfig(self):
        roleAddXueMode = self.roleAddXueModeComboBox.text()
        roleAddLanMode = self.roleAddLanModeComboBox.text()
        roleXuePercent = self.roleXuePercentBar.value()
        roleLanPercent = self.roleLanPercentBar.value()
        updateConfigModelDic = {'roleAddXueMode':roleAddXueMode, 
         'roleAddLanMode':roleAddLanMode, 
         'roleXuePercent':roleXuePercent, 
         'roleLanPercent':roleLanPercent, 
         'isZhua':(self.isBuZhuoSwitch.isChecked)(), 
         'isTou':(self.isTouSwitch.isChecked)(), 
         'isPkJiNeng':(self.isRoleDoJiNengSwitch.isChecked)(), 
         'isPkPuGong':(self.isRoleGongJiSwitch.isChecked)(), 
         'isPkFangYu':(self.isRoleFangYuSwitch.isChecked)(), 
         'isPkAuto':(self.isRoleAutoSwitch.isChecked)(), 
         'isPkTaoPao':(self.isRoleTaoPaoSwitch.isChecked)(), 
         'isDuiZhang':(self.isDuiZhangSwitch.isChecked)()}
        postParam = {'id':(self.dealOrder).id, 
         'dkchangjingconfig':dkChangJingConfig2Json(updateConfigModelDic)}
        self.netUtil1 = NetUtil()
        self.netUtil1.postRequest(self, API_DEALORDER_UPDATE, postParam)
        self.netUtil1.callback.connect(lambda reponse: self._dealPostRes(reponse, updateConfigModelDic))

    def _dealPostRes(self, responseJson, updateConfigModelDic):
        if responseJson is not None:
            toast(self, "设置成功,需要重新启动生效")
            self.dealOrder.dkchangjingconfig = dkChangJingConfig2Json(updateConfigModelDic)
            self.refresh_info_singal.emit(self.dealOrder)
