# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\detail_win.py
import re
from datetime import timedelta
import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox
from loguru import logger
from qfluentwidgets import CardWidget, TitleLabel, BodyLabel, SwitchButton, PrimaryToolButton, FluentIcon, TransparentToolButton, MessageBox, SubtitleLabel, PushButton, ComboBox, HyperlinkButton
from common.model.deal_order_model import dict2DealOrderList
from common.page.device_win import DeviceWin
from common.page.frame_window import FrameWindow
from common.page.one_input_dialog import OneInputDialog
from common.page.single_select_dialog import SingleSelectDialog
from common.util.adb_util import adbUtil
from common.util.common_util import getDeviceId
from common.util.debounce_util import qt_debounce
from common.util.eventbus_util import eventBusUtil, EVENTBUS_ORDER_LIST, EVENTBUS_ORDER_REMOVE, EVENTBUS_REFRESH_BALANCE
from common.util.file_util import selectPngPath
from common.util.infobar_util import infoBarUtil
from common.util.math_util import isSameBi, getPerBi
from common.util.net_util import NetUtil
from common.util.scrcpy_util import scrcpyUtil
from common.util.time_util import expireTimeShow, isExpire, getNow
from common.util.widget_util import clear_layout
from const import API_DEALORDER_INFO, API_DEALORDER_DELETE, API_DEALORDER_UPDATE, API_USER_REDUCEB, ORDER_TYPE_MAPS, TYPE_BAOTU, REVERSE_ORDER_TYPE_MAPS, TYPE_CW_CHANGJING, TYPE_PAOYU, TYPE_GENDUI, TYPE_DK_CHANGJING
from main.config.baotu_config_win import BaoTuConfigWin
from main.config.changjing_config_win import ChangJingConfigWin
from main.config.cw_jingjing_config_win import CWChangJingConfigWin
from main.config.dk_changjing_config_win import DKChangJingConfigWin
from main.config.gendui_config_win import GenDuiConfigWin
from main.config.paoyu_config_win import PaoYuConfigWin
from threads.thread_manager import threadManager

class DetailWin(QWidget):

    def __init__(self, mainWin, orderId):
        super().__init__()
        self.setObjectName(f"orderdetail_page_{orderId}")
        self.mainWin = mainWin
        self.orderId = orderId
        self.netUtil1 = None
        self.netUtil2 = None
        self.netUtil3 = None
        self.netUtil4 = None
        self.netUtil5 = None
        self.netUtil6 = None
        self.dealOrder = None
        self.initUI()
        self.isFirstFetched = False
        self.curRunType = None

    def showEvent(self, event):
        super().showEvent(event)
        self.fetchOrderDetail()

    def fetchOrderDetail(self, isRefresh=False):
        if self.isFirstFetched is False or isRefresh:
            self.isFirstFetched = True
            logger.debug(f"拉取单子{self.orderId}详情")
            self.netUtil1 = NetUtil()
            self.netUtil1.getRequest(self, API_DEALORDER_INFO + "?id=" + self.orderId)
            self.netUtil1.callback.connect(lambda responseJson: self._dealFetchRes(responseJson, isRefresh))

    def _dealFetchRes(self, responseJson, isRefresh):
        if responseJson is not None:
            if responseJson["obj"] is not None:
                if isRefresh:
                    infoBarUtil.success("刷新单子详情成功", parent=self)
                self.dealOrder = dict2DealOrderList(responseJson["obj"])
                self.setUIData()
            else:
                infoBarUtil.error("拉数据失败", parent=self)

    def initUI(self):
        layout = QVBoxLayout(self)
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignJustify)
        self.title_layout = QHBoxLayout()
        self.left_layout = QHBoxLayout()
        self.left_layout.setAlignment(Qt.AlignLeft)
        self.left_layout.setSpacing(12)
        self.startBtn = PrimaryToolButton(FluentIcon.PLAY)
        self.startBtn.clicked.connect(lambda: self.clickStart())
        self.refreshBtn = TransparentToolButton(FluentIcon.SYNC)
        self.refreshBtn.clicked.connect(lambda: self.fetchOrderDetail(True))
        self.orderTitle = SubtitleLabel("加载中...")
        self.remarkBtn = HyperlinkButton("", "备注")
        self.remarkBtn.clicked.connect(lambda: self.showSetRemark())
        self.deleteBtn = TransparentToolButton(FluentIcon.DELETE)
        self.deleteBtn.clicked.connect(lambda: self.deleteOrder())
        self.left_layout.addWidget(self.startBtn)
        self.left_layout.addWidget(self.refreshBtn)
        self.left_layout.addWidget(self.orderTitle)
        self.left_layout.addWidget(self.remarkBtn)
        self.title_layout.addLayout(self.left_layout, 1)
        self.title_layout.addWidget((self.deleteBtn), alignment=(Qt.AlignRight))
        self.subtitle_layout = QHBoxLayout()
        self.winname_layout = QHBoxLayout()
        self.winnameLabel = BodyLabel()
        self.bindDeviceBtn = PushButton("绑设备")
        self.bindDeviceBtn.clicked.connect(self.clickBind)
        self.jietuDeviceBtn = PushButton("截图")
        self.jietuDeviceBtn.clicked.connect(self.clickJieTu)
        self.reviewBtn = PushButton("观看")
        self.reviewBtn.clicked.connect(self.clickReview)
        self.deviceGameInfoLabel = BodyLabel()
        self.deviceGameInfoLabel.setTextColor(QColor(169, 169, 169), QColor(69, 169, 169))
        self.winname_layout.setAlignment(Qt.AlignLeft)
        self.winname_layout.addWidget(self.winnameLabel)
        self.winname_layout.addWidget(self.bindDeviceBtn)
        self.winname_layout.addWidget(self.jietuDeviceBtn)
        self.winname_layout.addWidget(self.reviewBtn)
        self.winname_layout.addWidget(self.deviceGameInfoLabel)
        self.expireTip = BodyLabel()
        self.subtitle_layout.addLayout(self.winname_layout, 1)
        self.subtitle_layout.addWidget(self.expireTip)
        card_layout.addLayout(self.title_layout)
        card_layout.addLayout(self.subtitle_layout)
        self.selectTypeTip = BodyLabel("选择项目：")
        self.runTypeComboBox = ComboBox(self)
        self.runTypeComboBox.setFixedWidth(200)
        self.runTypeComboBox.addItems(ORDER_TYPE_MAPS.keys())
        self.runTypeComboBox.currentIndexChanged.connect(self.on_type_selected)
        self.isRunTypeLabel = BodyLabel()
        self.runStateLayout = QHBoxLayout()
        self.runStateLayout.setAlignment(Qt.AlignLeft)
        self.runStateLayout.setContentsMargins(10, 0, 0, 0)
        self.runStateLayout.addWidget(self.selectTypeTip)
        self.runStateLayout.addWidget(self.runTypeComboBox)
        self.runStateLayout.addWidget(self.isRunTypeLabel)
        self.configLayout = QVBoxLayout()
        layout.addWidget(card)
        layout.addLayout(self.runStateLayout)
        layout.addLayout(self.configLayout)
        layout.setAlignment(Qt.AlignTop)

    def setUIData(self):
        self.orderTitle.setText(f"单子{self.dealOrder.id}详情")
        self.expireTip.setText(f"过期时间：{expireTimeShow(self.dealOrder.expiretime)}")
        self.startBtn.setIcon(FluentIcon.POWER_BUTTON if self.dealOrder.isruning else FluentIcon.PLAY)
        self.winnameLabel.setText(f'当前设备：{self.dealOrder.winname or "请绑定"}')
        if self.dealOrder.winname:
            gameInfo, _ = adbUtil.getGameVersion(self.dealOrder.winname)
            self.deviceGameInfoLabel.setText(gameInfo)
        if self.dealOrder.remark:
            self.remarkBtn.setText(self.dealOrder.remark)
        self.curRunType = self.dealOrder.type
        self.setConfigShow()
        typeName = REVERSE_ORDER_TYPE_MAPS[self.dealOrder.type]
        self.runTypeComboBox.setCurrentText(typeName)
        self.isRunTypeLabel.setText(f"【{typeName}】项目运行中..." if self.dealOrder.isruning else "")

    def clickStart(self):
        targetIsRuning = not (self.dealOrder.isruning or False)
        if getDeviceId() != self.dealOrder.deviceid:
            infoBarUtil.warning("单子和绑定的电脑不匹配", parent=self)
            return
        if not self.dealOrder.winname:
            infoBarUtil.warning("请绑定手机", parent=self)
            return
        if not adbUtil.isDeviceExist(self.dealOrder.winname):
            infoBarUtil.warning("绑定的手机未连接电脑", parent=self)
            return
        _, isInstallGame = adbUtil.getGameVersion(self.dealOrder.winname)
        if not isInstallGame:
            infoBarUtil.warning("梦幻互通未安装", parent=self)
            return
        if targetIsRuning:
            if isExpire(self.dealOrder.expiretime):
                radioTxt = "续{}天时间(消耗{}个币)"
                perB = getPerBi(REVERSE_ORDER_TYPE_MAPS[self.curRunType])
                selectTexts = [radioTxt.format(1, 1 * perB), radioTxt.format(2, 2 * perB), radioTxt.format(3, 3 * perB), radioTxt.format(4, 4 * perB), radioTxt.format(5, 5 * perB), radioTxt.format(6, 6 * perB), radioTxt.format(7, 7 * perB), radioTxt.format(30, 30 * perB)]
                dialog = SingleSelectDialog("请选择续费时间", selectTexts, self)
                if dialog.exec():
                    selected = dialog.get_result()
                    resultMatch = re.search("续(\\d+)天时间.*消耗(\\d+\\.?\\d*)个币", selected)
                    day, b = int(resultMatch.group(1)), resultMatch.group(2)
                    expiretime = (getNow() + timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
                    postParam = {'orderid':(self.dealOrder).id,  'b':b,  'expiretime':expiretime,  'type':self.curRunType}
                    self.netUtil4 = NetUtil()
                    self.netUtil4.postRequest(self, API_USER_REDUCEB, postParam)
                    self.netUtil4.callback.connect(lambda responseJson: self._chargeTimePostRes(responseJson, expiretime))
                return
        postParam = {'id':(self.dealOrder).id, 
         'isruning':targetIsRuning, 
         'type':self.curRunType}
        self.netUtil5 = NetUtil()
        self.netUtil5.postRequest(self, API_DEALORDER_UPDATE, postParam)
        self.startBtn.setIcon(FluentIcon.MORE)
        self.netUtil5.callback.connect(lambda responseJson: self.runRequestRes(responseJson, targetIsRuning))

    def runRequestRes(self, responseJson, targetIsRuning):
        if responseJson is not None:
            self.dealOrder.isruning = targetIsRuning
            self.startBtn.setIcon(FluentIcon.POWER_BUTTON if self.dealOrder.isruning else FluentIcon.PLAY)
            self.dealOrder.type = self.curRunType
            typeName = REVERSE_ORDER_TYPE_MAPS[self.curRunType]
            self.isRunTypeLabel.setText(f"{typeName}项目运行中" if self.dealOrder.isruning else "")
            if targetIsRuning:
                adbUtil.openMHHT(self.dealOrder.winname)
                infoBarUtil.success(f"单子{self.dealOrder.id}---{typeName}启动成功", parent=self)
                threadManager.startThread(self.dealOrder)
            else:
                infoBarUtil.success(f"单子{self.dealOrder.id}---项目已停止", parent=self)
                isRunningThread = self.getCurRunningThread()
                if isRunningThread is not None:
                    isRunningThread.stop()

    def getCurRunningThread(self):
        isRunningThread = None
        if self.dealOrder.type == TYPE_BAOTU:
            isRunningThread = threadManager.getBaoTuThreadWithoutNew(self.dealOrder)
        elif self.dealOrder.type == TYPE_CW_CHANGJING:
            isRunningThread = threadManager.getCWChangJingThreadWithoutNew(self.dealOrder)
        elif self.dealOrder.type == TYPE_PAOYU:
            isRunningThread = threadManager.getPaoYuThreadWithoutNew(self.dealOrder)
        elif self.dealOrder.type == TYPE_GENDUI:
            isRunningThread = threadManager.getGenDuiThreadWithoutNew(self.dealOrder)
        elif self.dealOrder.type == TYPE_DK_CHANGJING:
            isRunningThread = threadManager.getDKChangJingThreadWithoutNew(self.dealOrder)
        return isRunningThread

    def deleteOrder(self):
        dialog = MessageBox("提醒", "确定删除当前单子？", self.window())
        if dialog.exec():
            postParam = {"id": (self.dealOrder.id)}
            self.netUtil2 = NetUtil()
            self.netUtil2.postRequest(self, API_DEALORDER_DELETE, postParam)
            self.netUtil2.callback.connect(lambda responseJson: self._deleteDealOrderRes(responseJson))

    def _deleteDealOrderRes(self, responseJson):
        if responseJson is not None:
            eventBusUtil.eventBus.emit(EVENTBUS_ORDER_REMOVE, self)

    def showSetRemark(self):
        remarkDialog = OneInputDialog("设置单子备注", self.dealOrder.remark, self)
        if remarkDialog.exec():
            postParam = {'id':(self.dealOrder).id,  'remark':(remarkDialog.get_result)()}
            self.netUtil6 = NetUtil()
            self.netUtil6.postRequest(self, API_DEALORDER_UPDATE, postParam)
            self.netUtil6.callback.connect(lambda responseJson: self._saveRemarkRes(responseJson, remarkDialog.get_result()))

    def _saveRemarkRes(self, responseJson, remark):
        if responseJson is not None:
            self.remarkBtn.setText(remark)
            infoBarUtil.success("备注设置成功", parent=self)

    def clickBind(self):
        self.deviceWin = DeviceWin(isSingle=True)
        self.deviceWin.selectDeviceIdsSignal.connect(self.selectDevices)
        self.deviceWin.show()

    def clickJieTu(self):
        if not self.dealOrder.winname:
            infoBarUtil.warning("未绑定设备", parent=self)
            return
        filePath = selectPngPath(self)
        if filePath:
            frame = scrcpyUtil.getFrame(self.dealOrder.winname)
            cv2.imwrite(filePath, frame)

    def clickReview(self):
        if not self.dealOrder.winname:
            infoBarUtil.warning("未绑定设备", parent=self)
            return
        self.frameWin = FrameWindow(self.dealOrder.winname)
        self.frameWin.show()

    def selectDevices(self, deviceIds):
        postParam = {'id':(self.dealOrder).id, 
         'winname':deviceIds[0]}
        self.netUtil3 = NetUtil()
        self.netUtil3.postRequest(self, API_DEALORDER_UPDATE, postParam)
        self.netUtil3.callback.connect(lambda responseJson: self._clickBindRes(responseJson, deviceIds[0]))

    def _clickBindRes(self, responseJson, bindText):
        if responseJson is not None:
            self.winnameLabel.setText(f"当前设备：{bindText}")
            self.dealOrder.winname = bindText
            infoBarUtil.success(f"绑定设备{bindText}成功", parent=self)
            (gameInfo, _) = adbUtil.getGameVersion(self.dealOrder.winname)
            self.deviceGameInfoLabel.setText(gameInfo)

    def _chargeTimePostRes(self, responseJson, expiretime):
        if responseJson is not None:
            self.dealOrder.expiretime = expiretime
            self.expireTip.setText(f"过期时间：{expireTimeShow(self.dealOrder.expiretime)}")
            eventBusUtil.eventBus.emit(EVENTBUS_REFRESH_BALANCE, self)

    def on_type_selected(self, index):
        if not isExpire(self.dealOrder.expiretime):
            runTypeName = REVERSE_ORDER_TYPE_MAPS[self.dealOrder.type]
            show_text = self.runTypeComboBox.currentText()
            if not isSameBi(runTypeName, show_text):
                self.runTypeComboBox.setCurrentText(runTypeName)
                infoBarUtil.warning("只能同价项目可以切换", parent=self)
                return
        show_text = self.runTypeComboBox.currentText()
        real_value = ORDER_TYPE_MAPS[show_text]
        self.curRunType = real_value
        self.setConfigShow()

    def setConfigShow(self):
        clear_layout(self.configLayout)
        if self.curRunType == TYPE_BAOTU:
            self.configLayout.addWidget(BaoTuConfigWin(self.dealOrder))
        elif self.curRunType == TYPE_CW_CHANGJING:
            self.configWin = CWChangJingConfigWin(self.dealOrder)
            self.configWin.refresh_info_singal.connect(lambda dealOrder: self.updateDealOrder(dealOrder))
            self.configLayout.addWidget(self.configWin)
        elif self.curRunType == TYPE_PAOYU:
            self.configLayout.addWidget(PaoYuConfigWin(self.dealOrder))
        elif self.curRunType == TYPE_GENDUI:
            self.configWin = GenDuiConfigWin(self.dealOrder)
            self.configWin.refresh_info_singal.connect(lambda dealOrder: self.updateDealOrder(dealOrder))
            self.configLayout.addWidget(self.configWin)
        elif self.curRunType == TYPE_DK_CHANGJING:
            self.configWin = DKChangJingConfigWin(self.dealOrder)
            self.configWin.refresh_info_singal.connect(lambda dealOrder: self.updateDealOrder(dealOrder))
            self.configLayout.addWidget(self.configWin)

    def updateDealOrder(self, dealOrder):
        self.dealOrder = dealOrder
