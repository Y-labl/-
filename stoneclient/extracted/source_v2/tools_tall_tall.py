# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: tools\tall\tall.py
import sys, time
from PyQt5.QtCore import Qt
import win32api, win32con, win32gui
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit

class TallWin(QMainWindow):

    def __init__(self):
        super(TallWin, self).__init__()
        self.setFixedSize(340, 700)
        self.setWindowTitle("自动喊话")
        self.window = []
        self.btn = QPushButton("刷新窗口")
        self.btn.clicked.connect(self.click)
        self.autoTxtTip = QLabel("1.自动喊话内容：")
        self.autoTxt = QLineEdit("神器任务抢晶石交流群++++++++++++++++++++++++++++++++++++")
        self.boardTxtTip = QLabel("2.推广内容：")
        self.boardTxt = QLineEdit("326646683这是微+后邀请进群")
        self.secondTxtTip = QLabel("3.喊话频率：(s)")
        self.secondTxt = QLineEdit("9")
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout()
        self.contentLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.contentWidget.setLayout(self.contentLayout)
        self.childWidget = QWidget()
        self.childLayout = QVBoxLayout()
        self.childLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.childWidget.setLayout(self.childLayout)
        self.contentLayout.addWidget(self.btn)
        self.contentLayout.addWidget(self.autoTxtTip)
        self.contentLayout.addWidget(self.autoTxt)
        self.contentLayout.addWidget(self.boardTxtTip)
        self.contentLayout.addWidget(self.boardTxt)
        self.contentLayout.addWidget(self.secondTxtTip)
        self.contentLayout.addWidget(self.secondTxt)
        self.contentLayout.addWidget(self.childWidget)
        self.setCentralWidget(self.contentWidget)

    def click(self):
        self.contentLayout.removeWidget(self.childWidget)
        self.childWidget = QWidget()
        self.childLayout = QVBoxLayout()
        self.childLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.childWidget.setLayout(self.childLayout)
        self.contentLayout.addWidget(self.childWidget)
        win32gui.EnumWindows(self.getMHWinList, 0)

    def getMHWinList(self, hwnd, mouse):
        self.window = []
        if win32gui.IsWindow(hwnd):
            if win32gui.IsWindowEnabled(hwnd):
                if win32gui.IsWindowVisible(hwnd):
                    if win32gui.GetClassName(hwnd) == "WSGAME":
                        winName = win32gui.GetWindowText(hwnd)
                        winClass = win32gui.GetClassName(hwnd)
                        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                        print("找到窗口{}({}) 窗口信息{}, {}, {}, {}, width:{}, height:{}".format(winName, winClass, left, top, right, bottom, right - left, bottom - top))
                        self.window.append(hwnd)
                        timer = QTimer()
                        timer.timeout.connect(lambda: self.dotall(hwnd))
                        childWidget = QWidget()
                        childLayout = QHBoxLayout()
                        childWidget.setLayout(childLayout)
                        titleTxt = winName
                        if "-" in winName:
                            titleTxt = winName.split("-")[2]
                        title = QLabel(titleTxt)
                        btn1 = QPushButton("启动")
                        btn1.clicked.connect(lambda: self.clickStart(timer, hwnd))
                        btn2 = QPushButton("停止")
                        btn2.clicked.connect(lambda: self.clickEnd(timer))
                        btn3 = QPushButton("推广")
                        btn3.clicked.connect(lambda: self.clickBroad(hwnd))
                        childLayout.addWidget(title)
                        childLayout.addWidget(btn1)
                        childLayout.addWidget(btn2)
                        childLayout.addWidget(btn3)
                        self.childLayout.addWidget(childWidget)

    def clickStart(self, timer, hwnd):
        self.dotall(hwnd)
        timer.start(int(self.secondTxt.text()) * 1000)

    def clickEnd(self, timer: QTimer):
        timer.stop()

    def clickBroad(self, hwnd):
        if win32gui.IsWindow(hwnd):
            txt = self.boardTxt.text()
            for t in txt:
                win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(t), 0)

    def dotall(self, hwnd):
        if win32gui.IsWindow(hwnd):
            txt = self.autoTxt.text()
            for t in txt:
                win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(t), 0)
            else:
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TallWin()
    win.show()
    sys.exit(app.exec_())
