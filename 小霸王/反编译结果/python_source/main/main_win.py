# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: main\main_win.py
from PyQt5.QtCore import Qt, QEvent, QPoint, QLocale
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenu, QApplication
from qfluentwidgets import FluentWindow, CardWidget, BodyLabel, TitleLabel, SwitchButton, Theme, setTheme, PushButton, DropDownPushButton, RoundMenu, Action, MessageBox, FluentTranslator, ImageLabel, TransparentToolButton, FluentIcon
import const
from common.model.baotu_config_model import baoTuConfig2Json, defaultBaoTuConfigModelDic
from common.model.cw_changjing_config_model import cWChangJingConfig2Json, defaultCWChangJingConfigModelDic
from common.model.deal_order_model import dict2DealOrderList
from common.model.gendui_config_model import genDuiConfig2Json, defaultGenDuiConfigModelDic
from common.model.paoyu_config_model import defaultPaoYuConfigModelDic, paoYuConfig2Json
from common.model.user import dict2User
from common.util.common_util import app_data, getDeviceId
from common.util.eventbus_util import eventBusUtil, EVENTBUS_ORDER_LIST, EVENTBUS_ORDER_REMOVE, EVENTBUS_REFRESH_BALANCE
from common.util.net_util import NetUtil
from common.util.infobar_util import InfoBar, infoBarUtil
from const import API_DEALORDER_LIST, API_USERINFO, TYPE_BAOTU, API_DEALORDER_CREATE
from main.detail_win import DetailWin

class MainWin(FluentWindow):

    def __init__(self, phone, parth):
        super().__init__()
        self.mPhone = phone
        self.parth = parth
        self.resize(900, 600)
        themeType = app_data.value("themeType", Theme.LIGHT)
        setTheme(themeType)
        const.gameType = app_data.value(f"gameType_{parth}", "点卡服")
        self.navigationInterface.setExpandWidth(180)
        self.navigationInterface.setCollapsible(False)
        self.navigationInterface.setReturnButtonVisible(False)
        self.init_menu_bar()
        self.netUtil1 = None
        self.netUtil2 = None
        self.netUtil3 = None
        self.enter = None
        self.mData = []
        self.fetchListData(init=True)
        self.fetchBalance()
        eventBusUtil.eventBus.on(EVENTBUS_ORDER_LIST, self.fetchListData)
        eventBusUtil.eventBus.on(EVENTBUS_ORDER_REMOVE, self.removeOrderItem)
        eventBusUtil.eventBus.on(EVENTBUS_REFRESH_BALANCE, self.fetchBalance)

    def init_menu_bar(self):
        menu_layout = QHBoxLayout()
        menu_layout.setSpacing(5)
        menu_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        logoImg = ImageLabel("./logo.ico")
        logoImg.scaledToHeight(25)
        menu_layout.addWidget(logoImg)
        windowTitleBase = (self.parth - 200) * 10
        self.setWindowTitle(f"小霸王{windowTitleBase + 1}-{windowTitleBase + 10}")
        versionLabel = BodyLabel(f"V{const.AppVersion}")
        menu_layout.addWidget(versionLabel)
        create_btn = PushButton("创建")
        create_btn.setFixedSize(65, 30)
        create_btn.clicked.connect(lambda: self.createOrder())
        menu_layout.addWidget(create_btn)
        balance_menu = RoundMenu()
        balance_menu.addAction(Action("刷新余额", triggered=(lambda: self.fetchBalance(True))))
        self.balance_btn = DropDownPushButton("余额：")
        self.balance_btn.setFixedSize(160, 30)
        self.balance_btn.setMenu(balance_menu)
        menu_layout.addWidget(self.balance_btn)
        tutorial_menu = RoundMenu()
        tutorial_menu.addAction(Action("切换点卡服", triggered=(lambda: self.setGameType("点卡服"))))
        tutorial_menu.addAction(Action("切换畅玩服", triggered=(lambda: self.setGameType("畅玩服"))))
        self.tutorial_btn = DropDownPushButton(const.gameType)
        self.tutorial_btn.setFixedSize(90, 30)
        self.tutorial_btn.setMenu(tutorial_menu)
        menu_layout.addWidget(self.tutorial_btn)
        theme_setting_menu = RoundMenu()
        theme_setting_menu.addAction(Action("深色主题", triggered=(lambda: self.setThemeMode(Theme.DARK))))
        theme_setting_menu.addAction(Action("浅色主题", triggered=(lambda: self.setThemeMode(Theme.LIGHT))))
        theme_setting_btn = DropDownPushButton("设置")
        theme_setting_btn.setFixedSize(75, 30)
        theme_setting_btn.setMenu(theme_setting_menu)
        menu_layout.addWidget(theme_setting_btn)
        self.pinBtn = TransparentToolButton(FluentIcon.PIN)
        self.pinBtn.clicked.connect(lambda: self.clickSetPin())
        menu_layout.addWidget((self.pinBtn), stretch=10, alignment=(Qt.AlignRight))
        self.titleBar.layout().insertLayout(1, menu_layout)

    def setThemeMode(self, themeType):
        setTheme(themeType)
        app_data.setValue("themeType", themeType)

    def setGameType(self, gameType):
        self.tutorial_btn.setText(gameType)
        app_data.setValue(f"gameType_{self.parth}", gameType)
        const.gameType = gameType

    def clickSetPin(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.pinBtn.setIcon(FluentIcon.PIN)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.pinBtn.setIcon(FluentIcon.PIN.colored(QColor(50, 205, 50), QColor(50, 205, 50)))
        self.show()

    def fetchListData(self, isTip=False, init=False):
        self.netUtil1 = NetUtil()
        url = API_DEALORDER_LIST + "?parth=" + str(self.parth)
        if init:
            url += f"&init=true&deviceid={getDeviceId()}"
        self.netUtil1.getRequest(self, url)
        self.netUtil1.callback.connect(lambda responseJson: self._dealFetchRes(responseJson, isTip))

    def fetchBalance(self, isTip=False):
        self.netUtil2 = NetUtil()
        self.netUtil2.getRequest(self, API_USERINFO)
        self.netUtil2.callback.connect(lambda responseJson: self._dealFetchUserInfo(responseJson, isTip))

    def _dealFetchUserInfo(self, responseJson, isTip):
        if responseJson is not None:
            if isTip:
                infoBarUtil.success("刷新成功", parent=self)
            userInfo = dict2User(responseJson["obj"])
            self.balance_btn.setText("余额：{}币".format(userInfo.b))
            self.enter = userInfo.enter

    def _dealFetchRes(self, responseJson, isTip):
        if responseJson is not None:
            if isTip:
                infoBarUtil.success("刷新成功", parent=self)
            myDealOrderList = dict2DealOrderList(responseJson["objs"])
            self.mData = myDealOrderList
            for dealOrder in myDealOrderList:
                detailWin = DetailWin(self, dealOrder.id)
                title = f"单子{dealOrder.id}"
                if dealOrder.remark:
                    title = f"{dealOrder.remark}"
                self.addSubInterface(detailWin, icon="", text=title)

    def createOrder(self):
        if len(self.mData) >= 10:
            infoBarUtil.warning("每个模块不超过10个单子")
            return
        dialog = MessageBox("提醒", "创建的单子将和当前电脑绑定，确认创建？", self.window())
        if dialog.exec():
            postParam = {'type':TYPE_BAOTU,  'parth':self.parth, 
             'deviceid':getDeviceId(), 
             'baotuconfig':baoTuConfig2Json(defaultBaoTuConfigModelDic), 
             'paoyuconfig':paoYuConfig2Json(defaultPaoYuConfigModelDic), 
             'cwchangjingconfig':cWChangJingConfig2Json(defaultCWChangJingConfigModelDic), 
             'genduiconfig':genDuiConfig2Json(defaultGenDuiConfigModelDic)}
            self.createOrderRequest(postParam)

    def createOrderRequest(self, postParam):
        self.netUtil3 = NetUtil()
        self.netUtil3.postRequest(self, API_DEALORDER_CREATE, postParam)
        self.netUtil3.callback.connect(self._dealPostRes)

    def _dealPostRes(self, responseJson):
        if responseJson is not None:
            self.fetchListData()
            infoBarUtil.success("创建成功", parent=self)

    def removeOrderItem(self, order):
        self.removeInterface(order)
