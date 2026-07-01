# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\page\one_input_dialog.py
from PyQt5.QtWidgets import QButtonGroup, QVBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import MessageBoxBase, SubtitleLabel, RadioButton, LineEdit

class OneInputDialog(MessageBoxBase):
    __doc__ = " 通用单选对话框 "

    def __init__(self, title, defaultInput, parent=None):
        super().__init__(parent)
        self.title_label = SubtitleLabel(title)
        self.viewLayout.addWidget(self.title_label)
        self.lineEdit = LineEdit()
        self.lineEdit.setClearButtonEnabled(True)
        if defaultInput:
            self.lineEdit.setText(defaultInput)
        self.viewLayout.addWidget(self.lineEdit)
        self.yesButton.setText("确认")
        self.cancelButton.setText("取消")

    def get_result(self):
        """ 获取最终选中的文本 """
        return self.lineEdit.text()
