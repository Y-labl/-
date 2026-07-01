# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: pyqt_toast\toast.py
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QAbstractAnimation, QPoint
from PyQt5.QtGui import QFont, QColor
from pyqt_resource_helper import PyQtResourceHelper

class Toast(QWidget):

    def __init__(self, text, duration=2, parent=None):
        super().__init__(parent)
        self._Toast__initVal(parent, duration)
        self._Toast__initUi(text)

    def __initVal(self, parent, duration):
        self._Toast__parent = parent
        self._Toast__parent.installEventFilter(self)
        self.installEventFilter(self)
        self._Toast__timer = QTimer(self)
        self._Toast__duration = duration
        self._Toast__opacity = 0.5
        self._Toast__foregroundColor = "#EEEEEE"
        self._Toast__backgroundColor = "#444444"

    def __initUi(self, text):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._Toast__lbl = QLabel(text)
        self._Toast__lbl.setObjectName("popupLbl")
        PyQtResourceHelper.setStyleSheet([self._Toast__lbl], ["style/foreground.css"])
        self._Toast__lbl.setMinimumWidth(min(200, self._Toast__lbl.fontMetrics().boundingRect(text).width() * 2))
        self._Toast__lbl.setMinimumHeight(self._Toast__lbl.fontMetrics().boundingRect(text).height() * 2)
        self._Toast__lbl.setWordWrap(True)
        self._Toast__initAnimation()
        lay = QHBoxLayout()
        lay.addWidget(self._Toast__lbl)
        lay.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        PyQtResourceHelper.setStyleSheet([self], ["style/background.css"])
        self._Toast__setToastSizeBasedOnTextSize()
        self.setLayout(lay)

    def __setOpacity(self, opacity):
        opacity_effect = QGraphicsOpacityEffect(opacity=opacity)
        self.setGraphicsEffect(opacity_effect)

    def __initAnimation(self):
        self._Toast__animation = QPropertyAnimation(self, b'opacity')
        self._Toast__animation.setStartValue(0.0)
        self._Toast__animation.setDuration(200)
        self._Toast__animation.setEndValue(self._Toast__opacity)
        self._Toast__animation.valueChanged.connect(self._Toast__setOpacity)
        self.setGraphicsEffect(QGraphicsOpacityEffect(opacity=0.0))

    def __initTimeout(self):
        self._Toast__timer = QTimer(self)
        self._Toast__timer_to_wait = self._Toast__duration
        self._Toast__timer.setInterval(1000)
        self._Toast__timer.timeout.connect(self._Toast__changeContent)
        self._Toast__timer.start()

    def __changeContent(self):
        self._Toast__timer_to_wait -= 1
        if self._Toast__timer_to_wait <= 0:
            self._Toast__animation.setDirection(QAbstractAnimation.Backward)
            self._Toast__animation.start()
            self._Toast__timer.stop()

    def setPosition(self, pos):
        geo = self.geometry()
        geo.moveCenter(pos)
        self.setGeometry(geo)

    def setAlignment(self, alignment):
        self._Toast__lbl.setAlignment(alignment)

    def show(self):
        if self._Toast__timer.isActive():
            pass
        else:
            self._Toast__animation.setDirection(QAbstractAnimation.Forward)
            self._Toast__animation.start()
            self.raise_()
            self._Toast__initTimeout()
        return super().show()

    def isVisible(self) -> bool:
        return self._Toast__timer.isActive()

    def setFont(self, font: QFont):
        self._Toast__lbl.setFont(font)
        self._Toast__setToastSizeBasedOnTextSize()

    def __setToastSizeBasedOnTextSize(self):
        self.setFixedWidth(self._Toast__lbl.sizeHint().width() * 2)
        self.setFixedHeight(self._Toast__lbl.sizeHint().height() * 2)

    def setDuration(self, duration: int):
        self._Toast__duration = duration
        self._Toast__initAnimation()

    def setForegroundColor(self, color: QColor):
        if isinstance(color, str):
            color = QColor(color)
        self._Toast__foregroundColor = color.name()

    def setBackgroundColor(self, color: QColor):
        if isinstance(color, str):
            color = QColor(color)
        self._Toast__backgroundColor = color.name()

    def __setForegroundColor(self):
        self._Toast__lbl.setStyleSheet(f"QLabel#popupLbl {{ color: {self._Toast__foregroundColor}; padding: 5px; }}")

    def __setBackgroundColor(self):
        self.setStyleSheet(f"QWidget {{ background-color: {self._Toast__backgroundColor}; border-radius: 5px; }}")

    def setOpacity(self, opacity: float):
        self._Toast__opacity = opacity
        self._Toast__initAnimation()

    def eventFilter(self, obj, e):
        if e.type() == 14:
            self.setPosition(QPoint(self._Toast__parent.rect().center().x(), self._Toast__parent.rect().center().y()))
        else:
            if isinstance(obj, Toast) and e.type() == 75:
                self._Toast__setForegroundColor()
                self._Toast__setBackgroundColor()
        return super().eventFilter(obj, e)
