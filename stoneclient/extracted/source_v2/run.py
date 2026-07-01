import sys, traceback, os
from PyQt5.QtWidgets import QApplication

# Global error logging
def log_exception(exc_type, exc_value, exc_tb):
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_tb)
sys.excepthook = log_exception

from login import LoginWin

os.chdir(os.path.dirname(os.path.abspath(__file__)))
app = QApplication(sys.argv)
win = LoginWin()
win.show()
sys.exit(app.exec_())
