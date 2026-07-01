# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\page\frame_window.py
import cv2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap
from common.util.scrcpy_util import scrcpyUtil
FRAME_UPDATE_INTERVAL = 200

class FrameWindow(QMainWindow):

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
        self.setWindowTitle(f"设备实时画面 - {self.device_id}")
        self.setFixedSize(800, 448)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(FRAME_UPDATE_INTERVAL)

    def update_frame(self):
        """定时刷新画面到 PyQt 窗口"""
        current_frame = scrcpyUtil.getFrame(self.device_id)
        if current_frame is None:
            return
        frame_rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(pixmap)
