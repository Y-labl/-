# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: login.py
# Compiled at: 2026-07-01 07:28:36
# Size of source mod 2**32: 6726 bytes
import os, subprocess, sys, threading, socket
from PyQt5.QtCore import QRegExp, QJsonDocument, QSettings, pyqtSignal
from PyQt5.QtGui import QIcon, QPalette, QBrush, QPixmap, QRegExpValidator, QFont
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QWidget, QGridLayout, QApplication, QPushButton, QButtonGroup, QLabel, QRadioButton, QLineEdit
import requests, resource
from const import API_HOST, API_LOGIN, AppVersion
from index import IndexWindow
from stone_util import toast, app_data
from user import dict2User

class LoginWin(QMainWindow):
    updateVersionCheckSignal = pyqtSignal(dict)
    showStatusBarSingnal = pyqtSignal(str)

    def __init__(self):
        super(LoginWin, self).__init__()
        self.setFixedSize(340, 240)
        self.setWindowTitle("登录小石头系统")
        self.setWindowIcon(QIcon(":/logo.ico"))
        fontSize16 = QFont()
        fontSize16.setPointSize(16)
        self.main_widget = QWidget()
        # self.main_widget.hide()  -- disabled for local testing
        self.main_widget.setContentsMargins(20, 20, 20, 20)
        self.main_layout = QGridLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        self.phoneTip = QLabel("手机:")
        self.phoneTip.setFont(fontSize16)
        self.phone = QLineEdit()
        self.phone.setMinimumHeight(50)
        self.phone.setContentsMargins(10, 0, 10, 0)
        self.phone.setFont(fontSize16)
        phoneExp = QRegExp("^1(3\\d|4[4-9]|5[0-35-9]|6[67]|7[013-8]|8[0-9]|9[0-9])\\d{8}$")
        phoneExpVa = QRegExpValidator(phoneExp)
        self.phone.setValidator(phoneExpVa)
        self.passwordTip = QLabel("密码:")
        self.passwordTip.setFont(fontSize16)
        self.password = QLineEdit()
        self.password.setMinimumHeight(50)
        self.password.setContentsMargins(10, 0, 10, 0)
        self.password.setFont(fontSize16)
        passwordExp = QRegExp("[0-9A-Za-z]{8,16}$")
        passwordExpVa = QRegExpValidator(passwordExp)
        self.password.setValidator(passwordExpVa)
        self.passwordTip2 = QLabel("  *至少6位长度")
        self.passwordTip2.setStyleSheet("QLabel{color:rgb(225,22,173,255);font-size:12px;font-weight:normal;font-family:Arial;}")
        self.login = QPushButton("登录")
        self.login.setFont(fontSize16)
        self.login.setMinimumHeight(50)
        self.login.clicked.connect(self.clickLogin)
        self.main_layout.addWidget(self.phoneTip, 0, 0, 1, 1)
        self.main_layout.addWidget(self.phone, 0, 1, 1, 3)
        self.main_layout.addWidget(self.passwordTip, 1, 0, 1, 1)
        self.main_layout.addWidget(self.password, 1, 1, 1, 3)
        self.main_layout.addWidget(self.passwordTip2, 2, 1, 1, 3)
        self.main_layout.addWidget(self.login, 3, 0, 1, 4)
        phoneValue = app_data.value("phone")
        passwordValue = app_data.value("password")
        self.phone.setText(phoneValue)
        self.password.setText(passwordValue)
        self.statusBar().showMessage("版本检测中...")
        # mouseThread disabled for local test
        # mouseThread.start()
        self.updateVersionCheckSignal.connect(self.updateVersionCheck)
        self.showStatusBarSingnal.connect(self.showStatusBar)
        self.initVersion()

    def showStatusBar(self, msg):
        self.statusBar().showMessage(msg)

    def initVersion(self):
        self.main_widget.show()
        self.statusBar().showMessage("版本:" + str(AppVersion) + " (本地测试)")
    def updateVersionCheck(self, resposeData):
        newVersion = resposeData["newVersion"]
        forceVersion = resposeData["forceVersion"]
        content = resposeData["content"]
        downloadUrl = resposeData["downloadUrl"]
        if newVersion > AppVersion:
            userSelectBox = QMessageBox(QMessageBox.Question, "有新版本", "V{}更新内容:\n{}".format(newVersion, content))
            Qyes = userSelectBox.addButton(self.tr("更新"), QMessageBox.YesRole)
            if AppVersion >= forceVersion:
                Qno = userSelectBox.addButton(self.tr("稍后"), QMessageBox.NoRole)
            userSelectBox.exec_()
            if userSelectBox.clickedButton() == Qyes:
                mouseThread = threading.Thread(target=(lambda: self.startDownload(downloadUrl)))
                # mouseThread.start()
        elif userSelectBox.clickedButton() == Qno:
            self.main_widget.show()
        else:
            self.main_widget.show()

    def startDownload(self, downloadUrl):
        print(downloadUrl)
        resp = requests.request(method="GET", url=downloadUrl, stream=True)
        total = int(resp.headers.get("content-length", 0))
        app_path = os.path.dirname(sys.executable)
        pathList = app_path.split("\\")
        parentPath = ""
        for i in range(len(pathList)):
            if i != len(pathList) - 1:
                parentPath += pathList[i] + "\\"
            targetDownloadPath = parentPath + "stone.zip"
            print("appPath:" + app_path)
            print("targetDownloadPath:" + targetDownloadPath)
            curSize = 0
            with open(targetDownloadPath, "wb") as file:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    curSize += size
                    self.showStatusBarSingnal.emit("下载进度:{}/{}M".format("%.1f" % (curSize / 1024 / 1024), "%.1f" % (total / 1024 / 1024)))

            updaterExePath = parentPath + "stoneUpdater\\stoneUpdater.exe"
            subprocess.Popen(updaterExePath)
            app = QApplication.instance()
            app.quit()

    def clickLogin(self):
        import traceback
        try:
            phone = self.phone.text()
            password = self.password.text()
            if len(phone) != 11:
                toast(self, "手机号不合法")
                return
            if len(password) < 6:
                toast(self, "密码长度不够")
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

            postParam = {"phone": phone, "password": password, "version": AppVersion, "uuid": uuid}
            self.statusBar().showMessage("登录中...")
            response = requests.request(url=(API_HOST + API_LOGIN), method="post", json=postParam, headers={"content-type": "application/json"}, timeout=5)
            self.statusBar().showMessage("状态码: " + str(response.status_code))
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    user = dict2User(data["obj"])
                    app_data.setValue("phone", self.phone.text())
                    app_data.setValue("password", self.password.text())
                    app_data.setValue("token", "Bearer " + user.token)
                    toast(self, "登录成功")
                    self.statusBar().showMessage("正在加载主界面...")
                    try:
                        self.indexWin = IndexWindow()
                        self.indexWin.show()
                    except Exception as e:
                        self.statusBar().showMessage("加载主界面失败: " + str(e))
                        import traceback
                        traceback.print_exc()
                        return
                    # 延迟关闭登录窗口，等 Toast 动画结束（避免 C++ 层崩溃）
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(3000, self.close)
                else:
                    toast(self, data.get("msg", "登录失败"))
                    self.statusBar().showMessage("错误: " + str(data.get("msg", "")))
            else:
                toast(self, "网络请求失败")
                self.statusBar().showMessage("HTTP " + str(response.status_code))
        except Exception as e:
            toast(self, "异常: " + str(e))
            self.statusBar().showMessage("异常: " + str(e))



