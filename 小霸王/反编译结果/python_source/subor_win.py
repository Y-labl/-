# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: subor_win.py
import locale, os, sys
from PyQt5.QtCore import QRegExp, Qt, QLocale, pyqtSignal
from PyQt5.QtGui import QFont, QRegExpValidator
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit, QApplication
from qfluentwidgets import FluentTranslator
from common.model.user import dict2User
from common.util.common_util import toast, app_data
from common.util.hwnd_util import hwndUtil
from common.util.log_util import logUtil
from common.util.net_util import NetUtil
from const import AppVersion, API_LOGIN, TYPE_PING, API_UPDATE_USERINFO, TYPE_BAOTU
from main.main_win import MainWin
from ping.ping_win import PingWin

class SuborWin(QMainWindow):

    def __init__(self, config):
        super(SuborWin, self).__init__()
        self.configList = []
        for numStr in config.split("."):
            self.configList.append(int(numStr))

        self.setFixedSize(550, 200)
        self.setWindowTitle("小霸王合集")
        fontSize10 = QFont()
        fontSize14 = QFont()
        fontSize16 = QFont()
        fontSize20 = QFont()
        fontSize10.setPointSize(10)
        fontSize14.setPointSize(14)
        fontSize16.setPointSize(16)
        fontSize20.setPointSize(20)
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(5, 0, 5, 0)
        self.mainWidget.setLayout(self.mainLayout)
        self.loginedWidget = QWidget()
        self.loginedWidget.hide()
        self.loginedLayout = QHBoxLayout()
        self.loginedLayout.setContentsMargins(0, 0, 5, 0)
        self.loginedWidget.setLayout(self.loginedLayout)
        self.loginedTitle = QLabel()
        self.loginedTitle.setFont(fontSize14)
        self.loginChangeBtn = QPushButton("切换账号")
        self.loginChangeBtn.setFixedSize(100, 30)
        self.loginChangeBtn.setFont(fontSize14)
        self.loginChangeBtn.clicked.connect(self.changeLogin)
        self.loginedLayout.addWidget(self.loginedTitle)
        self.loginedLayout.addWidget(self.loginChangeBtn)
        self.loginWidget = QWidget()
        self.loginLayout = QHBoxLayout()
        self.loginLayout.setContentsMargins(0, 0, 0, 0)
        self.loginWidget.setLayout(self.loginLayout)
        self.phoneTip = QLabel("手机:")
        self.phoneTip.setFont(fontSize16)
        self.phone = QLineEdit()
        self.phone.setFont(fontSize16)
        phoneExp = QRegExp("^1(3\\d|4[4-9]|5[0-35-9]|6[67]|7[013-8]|8[0-9]|9[0-9])\\d{8}$")
        phoneExpVa = QRegExpValidator(phoneExp)
        self.phone.setValidator(phoneExpVa)
        self.passwordTip = QLabel("密码:")
        self.passwordTip.setFont(fontSize16)
        self.password = QLineEdit()
        self.password.setFont(fontSize16)
        self.password.setEchoMode(QLineEdit.Password)
        passwordExp = QRegExp("[0-9A-Za-z]{8,16}$")
        passwordExpVa = QRegExpValidator(passwordExp)
        self.password.setValidator(passwordExpVa)
        self.passwordTip2 = QLabel("*至少6位长度")
        self.passwordTip2.setStyleSheet("QLabel{color:rgb(225,22,173);font-size:12px;font-weight:normal;font-family:Arial;}")
        self.login = QPushButton("登录")
        self.login.setFixedSize(50, 30)
        self.login.setFont(fontSize16)
        self.login.clicked.connect(self.autoLogin)
        self.loginLayout.addWidget(self.phoneTip)
        self.loginLayout.addWidget(self.phone)
        self.loginLayout.addWidget(self.passwordTip)
        self.loginLayout.addWidget(self.password)
        self.loginLayout.addWidget(self.passwordTip2)
        self.loginLayout.addWidget(self.login)
        self.mainLayout.addWidget(self.loginedWidget)
        self.mainLayout.addWidget(self.loginWidget)
        self.setCentralWidget(self.mainWidget)
        self.home1Widget = QWidget()
        self.home1WidgetLayout = QHBoxLayout()
        self.home1WidgetLayout.setAlignment(Qt.AlignLeft)
        self.home1WidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.home1Widget.setLayout(self.home1WidgetLayout)
        self.pingEnterBtn = QPushButton("测试")
        self.pingEnterBtn.setFixedSize(65, 25)
        self.pingEnterBtn.setStyleSheet("color:white;font-size:12pt;font-family:楷体;background-color:#1A55D3;border-radius:5px;border:2px groove #8B8682;border-style:outset;")
        self.pingEnterBtn.clicked.connect(lambda: self.uploadLoginType("抢平转", TYPE_PING, 199))
        self.heJiEnterBtn1 = QPushButton("小霸王1-10")
        self.heJiEnterBtn1.setFixedSize(90, 25)
        self.heJiEnterBtn1.setStyleSheet("color:white;font-size:12pt;font-family:楷体;background-color:#1A55D3;border-radius:5px;border:2px groove #8B8682;border-style:outset;")
        self.heJiEnterBtn1.clicked.connect(lambda: self.uploadLoginType("小霸王1-10", TYPE_BAOTU, 200))
        self.heJiEnterBtn2 = QPushButton("小霸王11-20")
        self.heJiEnterBtn2.setFixedSize(90, 25)
        self.heJiEnterBtn2.setStyleSheet("color:white;font-size:12pt;font-family:楷体;background-color:#1A55D3;border-radius:5px;border:2px groove #8B8682;border-style:outset;")
        self.heJiEnterBtn2.clicked.connect(lambda: self.uploadLoginType("小霸王11-20", TYPE_BAOTU, 201))
        self.heJiEnterBtn3 = QPushButton("小霸王21-30")
        self.heJiEnterBtn3.setFixedSize(90, 25)
        self.heJiEnterBtn3.setStyleSheet("color:white;font-size:12pt;font-family:楷体;background-color:#1A55D3;border-radius:5px;border:2px groove #8B8682;border-style:outset;")
        self.heJiEnterBtn3.clicked.connect(lambda: self.uploadLoginType("小霸王21-30", TYPE_BAOTU, 202))
        self.home1WidgetLayout.addWidget(self.pingEnterBtn)
        self.home1WidgetLayout.addWidget(self.heJiEnterBtn1)
        self.home1WidgetLayout.addWidget(self.heJiEnterBtn2)
        self.home1WidgetLayout.addWidget(self.heJiEnterBtn3)
        self.mainLayout.addWidget(self.home1Widget)
        self.statusBar().showMessage("当前版本号:" + str(AppVersion))
        app_path = os.path.dirname(sys.executable)
        pathList = app_path.split("\\")
        self.parentPath = ""
        for i in range(len(pathList)):
            if i != len(pathList) - 1:
                self.parentPath += pathList[i] + "/"
            logUtil.setParentPath(self.parentPath)
            tmpPath = self.parentPath + "小霸王/临时文件"

        if not os.path.isdir(tmpPath):
            os.mkdir(tmpPath)
        locale.setlocale(locale.LC_CTYPE, "Chinese")
        self.netUtil2 = None
        self.netUtil3 = None
        phoneValue = app_data.value("phone")
        passwordValue = app_data.value("password")
        self.phone.setText(phoneValue)
        self.password.setText(passwordValue)
        self.autoLogin()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def changeLogin(self):
        self.loginWidget.show()
        self.loginedWidget.hide()

    def autoLogin(self):
        phone = self.phone.text()
        password = self.password.text()
        if phone == "" or password == "":
            toast(self, "请登录")
            self.loginWidget.show()
            return
        if len(phone) != 11:
            toast(self, "手机号不合法")
            self.loginWidget.show()
            return
        if len(password) < 6:
            toast(self, "密码长度不够")
            self.loginWidget.show()
            return
        uuid = ""
        try:
            uuid = os.popen("wmic csproduct get uuid").read()
            uuid = uuid.strip().replace("\n", "").replace("\r", "").split(" ")
            uuid = uuid[len(uuid) - 1]
            if len(uuid) > 10:
                uuid = uuid[0:8]
        except:
            pass
        else:
            postParam = {
              'phone': phone,
              'password': password,
              'version': AppVersion,
              'uuid': uuid}
            self.netUtil2 = NetUtil()
            self.netUtil2.postRequest(self, API_LOGIN, postParam)
            self.netUtil2.callback.connect(self._dealPostRes)

    def _dealPostRes(self, responseJson):
        if responseJson is not None:
            user = dict2User(responseJson["obj"])
            app_data.setValue("token", "Bearer " + user.token)
            app_data.setValue("phone", self.phone.text())
            app_data.setValue("password", self.password.text())
            app_data.setValue("email", user.email)
            self.loginedTitle.setText("已登录，手机：{}".format(self.phone.text()))
            self.loginedWidget.show()
            self.loginWidget.hide()
        else:
            self.loginWidget.show()
            self.loginedWidget.hide()

    def uploadLoginType(self, winTitle, loginType, parth):
        if "已登录" not in self.loginedTitle.text():
            toast(self, "请登录")
            return
        if loginType not in self.configList:
            toast(self, "对应功能未开放")
            return
        postParam = {"logintype": loginType}
        self.netUtil3 = NetUtil()
        self.netUtil3.postRequest(self, API_UPDATE_USERINFO, postParam)
        self.netUtil3.callback.connect(lambda responseJson: self._dealUploadLoginTypeRes(responseJson, winTitle, loginType, parth))

    def _dealUploadLoginTypeRes(self, responseJson, winTitle, loginType, parth=200):
        if responseJson is not None:
            winNames = [
             winTitle]
            dealWinHwnds = hwndUtil.findWinsByNames(winNames)
            if len(dealWinHwnds) >= 1:
                toast(self, "应用已经打开")
                self.close()
                return
            if loginType == TYPE_PING:
                self.pingWin = PingWin(self.phone.text())
                self.pingWin.show()
            elif loginType == TYPE_BAOTU:
                self.mainWin = MainWin(self.phone.text(), parth)
                self.mainWin.show()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    translator = FluentTranslator(QLocale(QLocale.Chinese, QLocale.China))
    app.installTranslator(translator)
    dbb = SuborWin("1.20")
    dbb.show()
    sys.exit(app.exec_())
