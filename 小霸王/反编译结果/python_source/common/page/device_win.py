# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\page\device_win.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox, QScrollArea
from common.page.device_big_screen import DeviceBigScreen
from common.thread.device_android_thread import DeviceAndroidThread
from common.util.adb_util import adbUtil
from common.util.file_util import selectPngPath
from common.util.scrcpy_util import scrcpyUtil
from common.util.widget_util import clear_layout, showPilImage
from common.widget.wrap_layout import WrapLayout
import cv2

class DeviceWin(QWidget):
    selectDeviceIdsSignal = pyqtSignal(list)

    def __init__(self, isSingle=False):
        super(DeviceWin, self).__init__()
        self.isSingle = isSingle
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle("小霸王设备列表")
        self.setMinimumWidth(1800)
        self.setMinimumHeight(950)
        self.showAllDeviceBtn = QPushButton("刷新设备中...")
        self.showAllDeviceBtn.setFixedSize(140, 30)
        self.showAllDeviceBtn.setStyleSheet("margin: 0px; padding-left: 15px; padding-right: 15px; padding-top: 4px; padding-bottom: 4px;")
        self.showAllDeviceBtn.clicked.connect(self.startShowAllDevice)
        self.clearSelectDeviceBtn = QPushButton("全选/反选")
        self.clearSelectDeviceBtn.setFixedSize(120, 30)
        self.clearSelectDeviceBtn.setStyleSheet("margin: 0px; padding-left: 15px; padding-right: 15px; padding-top: 4px; padding-bottom: 4px;")
        self.clearSelectDeviceBtn.clicked.connect(self.clearSelectDevice)
        if self.isSingle:
            self.clearSelectDeviceBtn.setEnabled(False)
            self.clearSelectDeviceBtn.setToolTip("单选模式下禁用全选/反选")
        self.sureSelectDeviceBtn = QPushButton("确认选择")
        self.sureSelectDeviceBtn.setFixedSize(120, 30)
        self.sureSelectDeviceBtn.setStyleSheet("margin: 0px; padding-left: 15px; padding-right: 15px; padding-top: 4px; padding-bottom: 4px; background-color: #FF69B4; border-radius: 4px")
        self.sureSelectDeviceBtn.clicked.connect(self.sureSelectDevice)
        self.topBtnContainer = QWidget()
        self.topBtnContainer.setFixedHeight(30)
        self.topBtnContainerLayout = QHBoxLayout()
        self.topBtnContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.topBtnContainerLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.topBtnContainer.setLayout(self.topBtnContainerLayout)
        self.topBtnContainerLayout.addWidget(self.showAllDeviceBtn)
        self.topBtnContainerLayout.addWidget(self.clearSelectDeviceBtn)
        self.topBtnContainerLayout.addWidget(self.sureSelectDeviceBtn)
        self.devicesWidget = QWidget()
        self.devicesLayout = WrapLayout(isSingle=(self.isSingle))
        self.devicesWidget.setLayout(self.devicesLayout)
        self.devicesLayout.right_menu_clicked.connect(self.right_menu_clicked)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.devicesWidget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.topBtnContainer)
        layout.addLayout((self.topBtnContainerLayout), stretch=0)
        layout.addWidget((self.scroll_area), stretch=1)
        self.mData = []
        self.deviceAndroidThread = DeviceAndroidThread()
        self.deviceAndroidThread.result_signal.connect(self.refreshUI)
        self.deviceAndroidThread.start()
        self.deviceBigScreen = None

    def startShowAllDevice(self):
        self.showAllDeviceBtn.setText("刷新设备中...")
        self.deviceAndroidThread.setGetOne()

    def clearSelectDevice(self):
        selected_texts = self.devicesLayout.get_selected_texts()
        if selected_texts:
            self.devicesLayout.clear_selection()
        else:
            self.devicesLayout.select_all()

    def sureSelectDevice(self):
        selected_texts = self.devicesLayout.get_selected_texts()
        if selected_texts:
            self.selectDeviceIdsSignal.emit(selected_texts)
            self.close()
        else:
            QMessageBox.information(self, "选中结果({}个)".format(len(selected_texts)), "暂无选中条目")

    def refreshUI(self, deviceModels):
        self.showAllDeviceBtn.setText("刷新设备")
        if len(deviceModels) == len(self.mData):
            self.mData = deviceModels
            self.devicesLayout.updateThumb(deviceModels)
        else:
            self.mData = deviceModels
            clear_layout(self.devicesLayout)
            for index in range(len(self.mData)):
                deviceModel = self.mData[index]
                itemWidget = QWidget()
                itemWidget.setStyleSheet("\n                                QWidget {\n                                    background-color: #D3D3D3;\n                                    border-radius: 4px;\n                                    padding: 0px;\n                                    font-size: 14px;\n                                }\n                            ")
                itemLayout = QVBoxLayout()
                itemLayout.setAlignment(Qt.AlignCenter)
                itemWidget.setLayout(itemLayout)
                thumbIndex = QLabel("{}".format(index + 1))
                thumbIndex.setFixedSize(30, 30)
                thumbIndex.setAlignment(Qt.AlignCenter)
                thumbIndex.setStyleSheet('\n                    QLabel {\n                        /* 圆形背景核心 */\n                        background-color: #FFB6C1;  /* 浅黄色（也可用rgb(255,250,205)） */\n                        border-radius: 15px;        /* 圆角半径=宽/高的一半（80/2=40），实现正圆 */\n                        font-family: "微软雅黑";\n                        \n                        /* 字体设置 */\n                        color: black;              /* 字体白色 */\n                        font-size: 15px;           /* 字号30 */\n                        font-weight: bold;         /* 可选：字体加粗，更醒目 */\n                    }\n                ')
                showThumb = QLabel()
                showThumb.setFixedSize(320, 180)
                showThumb.setAlignment(Qt.AlignCenter)
                showPilImage(deviceModel.thumbBytes, showThumb)
                showDeviceId = QLabel(deviceModel.deviceId)
                showDeviceId.setStyleSheet("QLabel { font-size: 18px; }")
                itemLayout.addWidget(thumbIndex)
                itemLayout.addWidget(showThumb)
                itemLayout.addWidget(showDeviceId)
                self.devicesLayout.addWidget(itemWidget)

    def right_menu_clicked(self, index, deviceId):
        if index == 1:
            if self.deviceBigScreen is not None:
                self.deviceBigScreen.close()
            self.deviceBigScreen = DeviceBigScreen(deviceId, self.getThumbBytes(deviceId))
            self.deviceBigScreen.show()
        else:
            if index == 2:
                adbUtil.reBackDeviceXY(deviceId)
            else:
                if index == 3:
                    filePath = selectPngPath(self)
                    if filePath:
                        frame = scrcpyUtil.getFrame(deviceId)
                        cv2.imwrite(filePath, frame)

    def getThumbBytes(self, deviceId):
        for deviceModel in self.mData:
            if deviceModel.deviceId == deviceId:
                return deviceModel.thumbBytes
            return

    def closeEvent(self, event):
        try:
            if self.deviceAndroidThread is not None:
                self.deviceAndroidThread.stop()
                self.deviceAndroidThread.wait(2000)
        except Exception:
            pass
        else:
            super().closeEvent(event)
