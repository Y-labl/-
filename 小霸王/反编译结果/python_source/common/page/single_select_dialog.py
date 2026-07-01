# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\page\single_select_dialog.py
from PyQt5.QtWidgets import QButtonGroup, QVBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import MessageBoxBase, SubtitleLabel, RadioButton

class SingleSelectDialog(MessageBoxBase):
    __doc__ = " 通用单选对话框 "

    def __init__(self, title, texts, parent=None):
        super().__init__(parent)
        self.selected_text = None
        self.title_label = SubtitleLabel(title)
        self.viewLayout.addWidget(self.title_label)
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.radio_layout = QVBoxLayout()
        self.radio_layout.setAlignment(Qt.AlignTop)
        self.radio_layout.setSpacing(12)
        for i, text in enumerate(texts):
            btn = RadioButton(text)
            if i == 0:
                btn.setChecked(True)
                self.selected_text = text
            self.btn_group.addButton(btn)
            self.radio_layout.addWidget(btn)
        else:
            self.viewLayout.addLayout(self.radio_layout)
            self.btn_group.buttonToggled.connect(self._on_toggled)
            self.widget.setMinimumWidth(380)
            self.yesButton.setText("确认")
            self.cancelButton.setText("取消")

    def _on_toggled(self, btn):
        """ 切换选项时保存选中值 """
        if btn.isChecked():
            self.selected_text = btn.text()

    def get_result(self):
        """ 获取最终选中的文本 """
        return self.selected_text
