
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QThread

class PingWin(QMainWindow):
    def __init__(self, phone):
        super().__init__()
        self.phone = phone
        self.setWindowTitle("Test")
        self.resize(400, 200)

class PingThread(QThread):
    def __init__(self):
        super().__init__()
    def run(self):
        pass
