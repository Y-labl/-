# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: enter_win.py
import json, os, subprocess, sys, threading
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QWidget, QGridLayout, QApplication
import requests
from common.model.version_control_model import dict2VersionControlList, VersionControlModel
from common.util.net_util import NetUtil
from const import OpenId, AppVersion, API_DEALORDER_INFO, API_VERSIONCONTROL_LIST
from subor_win import SuborWin

class EnterWin(QMainWindow):
    updateVersionCheckSignal = pyqtSignal(VersionControlModel)
    showStatusBarSingnal = pyqtSignal(str)

    def __init__(self):
        super(EnterWin, self).__init__()
        self.setFixedSize(500, 300)
        self.setWindowTitle("欢迎进入小霸王")
        fontSize16 = QFont()
        fontSize16.setPointSize(16)
        self.main_widget = QWidget()
        self.main_widget.hide()
        self.main_widget.setContentsMargins(20, 20, 20, 20)
        self.main_layout = QGridLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        self.netUtil1 = None
        self.statusBar().showMessage("版本检测中...")
        mouseThread = threading.Thread(target=(self.initVersion))
        mouseThread.start()
        self.updateVersionCheckSignal.connect(self.updateVersionCheck)
        self.showStatusBarSingnal.connect(self.showStatusBar)

    def showStatusBar(self, msg):
        self.statusBar().showMessage(msg)

    def initVersion(self):
        self.netUtil1 = NetUtil()
        self.netUtil1.callback.connect(self._dealFetchRes)
        self.netUtil1.getRequest(self, API_VERSIONCONTROL_LIST)

    def _dealFetchRes(self, responseJson):
        print("responseJson")
        print(responseJson)
        if responseJson is not None:
            targetVc = None
            vcList = dict2VersionControlList(responseJson["objs"])
            for vc in vcList:
                if vc.openId == OpenId:
                    targetVc = vc
                    break
            else:
                if targetVc:
                    version = targetVc.version
                    if version > AppVersion:
                        self.statusBar().showMessage("当前版本太低，请手动下载更新版本")
                elif version <= AppVersion:
                    self.statusBar().showMessage("当前版本号:" + str(AppVersion))
                    self.updateVersionCheckSignal.emit(targetVc)
                else:
                    self.statusBar().showMessage("版本获取异常")

        else:
            self.statusBar().showMessage("网络连接失败")

    def updateVersionCheck(self, vc):
        newVersion = vc.newVersion
        forceVersion = vc.forceVersion
        content = vc.content
        downloadUrl = vc.downloadUrl
        config = vc.config
        if newVersion > AppVersion:
            userSelectBox = QMessageBox(QMessageBox.Question, "有新版本", "V{}更新内容:\n{}".format(newVersion, content))
            Qyes = userSelectBox.addButton(self.tr("更新"), QMessageBox.YesRole)
            if AppVersion >= forceVersion:
                Qno = userSelectBox.addButton(self.tr("稍后"), QMessageBox.NoRole)
            userSelectBox.exec_()
            if userSelectBox.clickedButton() == Qyes:
                mouseThread = threading.Thread(target=(lambda: self.startDownload(downloadUrl)))
                mouseThread.start()
        elif userSelectBox.clickedButton() == Qno:
            self.enterSuborWin(config)
        else:
            self.enterSuborWin(config)

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
            targetDownloadPath = parentPath + "小霸王安装器.exe"
            print("appPath:" + app_path)
            print("targetDownloadPath:" + targetDownloadPath)
            subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], shell=False)
            curSize = 0
            with open(targetDownloadPath, "wb") as file:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    curSize += size
                    self.showStatusBarSingnal.emit("下载进度:{}/{}M".format("%.1f" % (curSize / 1024 / 1024), "%.1f" % (total / 1024 / 1024)))

            updaterExePath = parentPath + "小霸王安装器.exe"
            subprocess.Popen(updaterExePath)
            subprocess.run(["taskkill", "/F", "/IM", "小霸王.exe"], shell=False)
            app = QApplication.instance()
            app.quit()

    def enterSuborWin(self, config):
        self.suborWin = SuborWin(config)
        self.suborWin.show()
        self.close()
