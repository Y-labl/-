# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: 小霸王.py
import os, sys
from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator
from common.util.log_util import initLog
from enter_win import EnterWin
if not os.path.isdir("./有效日志"):
    os.mkdir("./有效日志")
initLog()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    translator = FluentTranslator(QLocale(QLocale.Chinese, QLocale.China))
    app.installTranslator(translator)
    dbb = EnterWin()
    dbb.show()
    sys.exit(app.exec_())
