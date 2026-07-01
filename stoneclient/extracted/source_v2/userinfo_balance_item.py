from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QListWidgetItem, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from const import PerStoneBalance


class UserInfoBalanceItem(QListWidgetItem):

    def __init__(self, balanceRecord):
        super().__init__()

        fontSize10 = QFont()
        fontSize14 = QFont()
        fontSize16 = QFont()
        fontSize20 = QFont()

        fontSize10.setPointSize(10)
        fontSize14.setPointSize(14)
        fontSize16.setPointSize(16)
        fontSize20.setPointSize(20)

        red = "QLabel{color:rgb(255,20,147,255);font-size:16px;font-weight:normal;font-family:Arial;}"
        blue = "QLabel{color:rgb(65,105,225,255);font-size:16px;font-weight:normal;font-family:Arial;}"
        grey = "QLabel{color:rgb(190,190,190,255);font-size:16px;font-weight:normal;font-family:Arial;}"

        redBorder = "QLabel{color:rgb(255,20,147,255);font-size:14px;font-weight:normal;font-family:Arial;border:2px solid rgb(255,20,147,255)}"
        green = "QLabel{color:rgb(63,81,181,255);font-size:14px;font-weight:normal;font-family:Arial;border:2px solid rgb(63,81,181,255)}"
        purple = "QLabel{color:rgb(156,39,176,255);font-size:14px;font-weight:normal;font-family:Arial;border:2px solid rgb(156,39,176,255)}"
        indigo = "QLabel{color:rgb(63,81,181,255);font-size:14px;font-weight:normal;font-family:Arial;border:2px solid rgb(63,81,181,255)}"

        self.wrapper = QWidget()

        self.widget = QWidget()
        self.widget.setFixedHeight(65)

        self.timeLabel = QLabel()
        self.timeLabel.setText(balanceRecord.createdAt)
        self.timeLabel.setFont(fontSize14)

        self.balanceLabel = QLabel()
        balanceStr = ""
        if balanceRecord.balance > 0:
            self.balanceLabel.setStyleSheet(red)
            balanceStr = "\u5145\u503c" + str(balanceRecord.balance) + "\u5c0f\u77f3\u5934"
        else:
            balanceStr = ""
            if balanceRecord.wincount > 0:
                self.balanceLabel.setStyleSheet(blue)
                balanceStr = "[{}\u5f00{}]".format(balanceRecord.wincount, balanceRecord.buytype)
            balanceStr += "\u62a2\u5230"
            balanceStr += str(abs(balanceRecord.balance))
            balanceStr += "\u4e2a\u6676\u77f3"
            tip = "\u5f53\u524d\u4f59\u989d" + str(balanceRecord.userbalance) + "R"
            # rmb label logic could follow...

        if balanceRecord.balance != 0:
            self.balanceLabel.setText(balanceStr)
        self.balanceLabel.setFont(fontSize16)

        self.typeLabel = QLabel()
        if balanceRecord.type == 0:
            self.typeLabel.setStyleSheet(redBorder)
            self.typeLabel.setText("\u6b63\u5e38\u5145\u503c")
        elif balanceRecord.type == 1:
            self.typeLabel.setStyleSheet(green)
            self.typeLabel.setText("\u65b0\u7528\u6237")
        elif balanceRecord.type == 2:
            self.typeLabel.setStyleSheet(purple)
            self.typeLabel.setText("\u63a8\u5e7f")
        elif balanceRecord.type == 3:
            self.typeLabel.setStyleSheet(indigo)
            self.typeLabel.setText("\u5176\u4ed6")

        self.rightWidget = QWidget()
        self.rightWidget.setFixedHeight(65)

        self.vbox2 = QVBoxLayout()
        self.vbox2.addWidget(self.balanceLabel, 0, Qt.AlignTop | Qt.AlignCenter)
        if balanceRecord.type in (0, 1, 2, 3):
            self.vbox2.addWidget(self.typeLabel, 0, Qt.AlignBottom | Qt.AlignCenter)
        self.rightWidget.setLayout(self.vbox2)

        self.line = QWidget()
        self.line.setFixedHeight(1)
        self.line.setStyleSheet("QWidget{background-color:#66CCFF;}")

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.timeLabel, 0, Qt.AlignLeft | Qt.AlignCenter)
        self.hbox.addWidget(self.rightWidget, 0, Qt.AlignRight | Qt.AlignCenter)
        self.widget.setLayout(self.hbox)

        self.vbox1 = QVBoxLayout()
        self.vbox1.addWidget(self.widget, 0, Qt.AlignTop)
        self.vbox1.addWidget(self.line, 0, Qt.AlignBottom)
        self.wrapper.setLayout(self.vbox1)

        self.setSizeHint(self.wrapper.sizeHint())
