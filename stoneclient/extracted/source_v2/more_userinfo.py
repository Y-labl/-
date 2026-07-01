# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: more_userinfo.py
# Compiled at: 2026-07-01 07:28:43
# Size of source mod 2**32: 2477 bytes
import requests
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QMainWindow, QLabel, QRadioButton, QWidget, QGridLayout, QButtonGroup, QHBoxLayout, QVBoxLayout, QListWidget
from balance_record import dict2BalanceRecordList
from const import API_HOST, API_MYBALANCE_LIST, PerStoneBalance
from stone_util import toast, app_data
from userinfo_balance_item import UserInfoBalanceItem

class MoreUserInfoWin(QMainWindow):
    gxtime_signal = pyqtSignal(str)

    def __init__(self, x, y):
        super(MoreUserInfoWin, self).__init__()
        self.setGeometry(x, y, 480, 750)
        self.setWindowTitle("小石头记录")
        self.setWindowIcon(QIcon(":/logo.ico"))
        fontSize10 = QFont()
        fontSize14 = QFont()
        fontSize16 = QFont()
        fontSize20 = QFont()
        fontSize10.setPointSize(10)
        fontSize14.setPointSize(14)
        fontSize16.setPointSize(16)
        fontSize20.setPointSize(20)
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout()
        self.contentWidget.setLayout(self.contentLayout)
        self.setCentralWidget(self.contentWidget)
        self.balanceTitle = QLabel()
        self.balanceTitle.setFont(fontSize16)
        self.balanceListWidget = QListWidget()
        self.contentLayout.addWidget(self.balanceTitle)
        self.contentLayout.addWidget(self.balanceListWidget)
        self.getMyBalance()

    def getMyBalance(self):
        token = app_data.value("token")
        response = requests.request(url=(API_HOST + API_MYBALANCE_LIST), method="get", headers={'content-type':"application/json", 
         'Authorization':token})
        if response.status_code == 200:
            if response.json()["status"] == "success":
                myBalanceList = dict2BalanceRecordList(response.json()["objs"])
                addBalance = 0
                reduceBalance = 0
                for balanceRecord in myBalanceList:
                    item = UserInfoBalanceItem(balanceRecord)
                    self.balanceListWidget.addItem(item)
                    self.balanceListWidget.setItemWidget(item, item.wrapper)
                    if balanceRecord.balance > 0:
                        addBalance += balanceRecord.balance
                    else:
                        reduceBalance -= balanceRecord.balance
                else:
                    self.balanceTitle.setText("总计充值{}小石头,抢到了{}个".format(addBalance, reduceBalance, int(reduceBalance / PerStoneBalance)))

            else:
                toast(self, response.json()["msg"])
        else:
            toast(self, "网络请求失败")
