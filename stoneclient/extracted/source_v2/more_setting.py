from PyQt5.QtCore import pyqtSignal, QRegExp
from PyQt5.QtGui import QFont, QIcon, QRegExpValidator
from PyQt5.QtWidgets import QMainWindow, QLabel, QRadioButton, QWidget, QGridLayout, QButtonGroup, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton
from const import VmLeidian, VmXiaoyao, BuyTime1, BuyTime2, Buy120140, Buy120, BuyAuto

class MoreSettingWin(QMainWindow):
    buytime_signal = pyqtSignal(str)
    buytype_signal = pyqtSignal(str)
    gxtimems_signal = pyqtSignal(str)

    def __init__(self, buyTime, buyType, gxTimeMs, x, y):
        super(MoreSettingWin, self).__init__()
        self.mBuyTime = buyTime
        self.mBuyType = buyType
        self.mGxTimeMs = gxTimeMs
        self.setGeometry(x, y + 100, 360, 420)
        self.setWindowTitle("设置更多")
        self.setWindowIcon(QIcon(":/logo.ico"))
        fontSize10 = QFont()
        fontSize14 = QFont()
        fontSize16 = QFont()
        fontSize20 = QFont()
        fontSize10.setPointSize(10)
        fontSize14.setPointSize(14)
        fontSize16.setPointSize(16)
        fontSize20.setPointSize(20)
        self.console_radio_widget = QWidget()
        self.console_radio_layout = QGridLayout()
        self.console_radio_widget.setLayout(self.console_radio_layout)
        self.setCentralWidget(self.console_radio_widget)

        self.winLabel2 = QLabel("1.设置选中商品的时长", self)
        self.winLabel3 = QLabel("(若提示至少选择一件商品或只抢120却抢140，选150ms)", self)
        self.winLabel2.setFont(fontSize16)
        self.winLabel3.setStyleSheet("QLabel{color:rgb(225,22,173,255);font-size:12px;font-weight:normal;font-family:Arial;}")
        self.radioBtn4 = QRadioButton(BuyTime1, self)
        self.radioBtn5 = QRadioButton(BuyTime2, self)
        self.console_radio_layout.addWidget(self.winLabel2, 0, 0, 1, 3)
        self.console_radio_layout.addWidget(self.winLabel3, 1, 0, 1, 3)
        self.console_radio_layout.addWidget(self.radioBtn4, 2, 0, 1, 1)
        self.console_radio_layout.addWidget(self.radioBtn5, 2, 1, 1, 1)
        self.radioGroup2 = QButtonGroup(self)
        self.radioGroup2.addButton(self.radioBtn4, 1)
        self.radioGroup2.addButton(self.radioBtn5, 2)
        self.radioGroup2.buttonClicked.connect(self.radioBtnSelect2)
        if self.mBuyTime == BuyTime1:
            self.radioBtn4.setChecked(True)
        elif self.mBuyTime == BuyTime2:
            self.radioBtn5.setChecked(True)

        self.winLabel4 = QLabel("2.设置抢购模式", self)
        self.winLabel5 = QLabel("都抢:发现就买 | 只抢120:判断价格 | 智能:1个买/2个挑120", self)
        self.winLabel4.setFont(fontSize16)
        self.winLabel5.setStyleSheet("QLabel{color:rgb(225,22,173,255);font-size:12px;font-weight:normal;font-family:Arial;}")
        self.radioBtn7 = QRadioButton("都抢", self)
        self.radioBtn8 = QRadioButton("只抢120", self)
        self.radioBtn9 = QRadioButton("智能抢", self)
        self.console_radio_layout.addWidget(self.winLabel4, 3, 0, 1, 3)
        self.console_radio_layout.addWidget(self.winLabel5, 4, 0, 1, 3)
        self.console_radio_layout.addWidget(self.radioBtn7, 5, 0, 1, 1)
        self.console_radio_layout.addWidget(self.radioBtn8, 5, 1, 1, 1)
        self.console_radio_layout.addWidget(self.radioBtn9, 5, 2, 1, 1)
        self.radioGroup3 = QButtonGroup(self)
        self.radioGroup3.addButton(self.radioBtn7, 1)
        self.radioGroup3.addButton(self.radioBtn8, 2)
        self.radioGroup3.addButton(self.radioBtn9, 3)
        self.radioGroup3.buttonClicked.connect(self.radioBtnSelect3)
        if self.mBuyType == Buy120140:
            self.radioBtn7.setChecked(True)
        elif self.mBuyType == Buy120:
            self.radioBtn8.setChecked(True)
        elif self.mBuyType == BuyAuto:
            self.radioBtn9.setChecked(True)

        self.winLabel6 = QLabel("3.设置点击兑换功勋时间", self)
        self.winLabel7 = QLabel("(只能设置910-979ms)", self)
        self.winLabel6.setFont(fontSize16)
        self.winLabel7.setStyleSheet("QLabel{color:rgb(225,22,173,255);font-size:12px;font-weight:normal;font-family:Arial;}")
        self.gxBoxWidget = QWidget()
        self.gxBoxLayout = QHBoxLayout()
        self.gxBoxWidget.setLayout(self.gxBoxLayout)
        self.gxMsInputTip1 = QLabel("11:59:59 ", self)
        self.gxMsInputTip1.setFont(fontSize14)
        self.gxMsInput = QLineEdit(str(self.mGxTimeMs))
        self.gxMsInput.textChanged.connect(self.updateGxTimeMs)
        self.gxMsInput.setMinimumHeight(35)
        self.gxMsInput.setContentsMargins(10, 0, 10, 0)
        self.gxMsInput.setFont(fontSize16)
        gxMsExp = QRegExp("^9[1-7][0-9]")
        gxMsExpVa = QRegExpValidator(gxMsExp)
        self.gxMsInput.setValidator(gxMsExpVa)
        self.gxMsInputTip2 = QLabel("ms", self)
        self.gxMsInputTip2.setFont(fontSize14)
        self.gxBoxLayout.addWidget(self.gxMsInputTip1)
        self.gxBoxLayout.addWidget(self.gxMsInput)
        self.gxBoxLayout.addWidget(self.gxMsInputTip2)
        self.console_radio_layout.addWidget(self.winLabel6, 6, 0, 1, 3)
        self.console_radio_layout.addWidget(self.winLabel7, 7, 0, 1, 3)
        self.console_radio_layout.addWidget(self.gxBoxWidget, 8, 0, 1, 3)

    def updateGxTimeMs(self, text):
        if len(text) == 3:
            self.gxtimems_signal.emit(text)

    def radioBtnSelect3(self):
        checkId = self.radioGroup3.checkedId()
        if checkId == 1:
            self.buytype_signal.emit(Buy120140)
        elif checkId == 2:
            self.buytype_signal.emit(Buy120)
        elif checkId == 3:
            self.buytype_signal.emit(BuyAuto)

    def radioBtnSelect2(self):
        checkId = self.radioGroup2.checkedId()
        if checkId == 1:
            self.buytime_signal.emit(BuyTime1)
        elif checkId == 2:
            self.buytime_signal.emit(BuyTime2)
