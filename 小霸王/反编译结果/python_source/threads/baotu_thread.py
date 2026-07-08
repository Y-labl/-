
from PyQt5.QtCore import QThread
class BaoTuThread(QThread):
    def __init__(self):
        super().__init__()
        self.dealOrder = None
    def setDealOrder(self, order):
        self.dealOrder = order
    def run(self):
        pass
