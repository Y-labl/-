"""
投屏控件 — 实时显示模拟器画面
"""
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QApplication
import win32gui


class ScreenMirror(QWidget):
    """实时投屏控件：截取模拟器窗口画面并在 QLabel 中显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vms = []           # VM 对象列表
        self.current_hwnd = None  # 当前投屏的窗口句柄
        self.fps = 10            # 刷新率（帧/秒）
        self.scale = 0.4         # 缩放比例

        # UI
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # 切换模拟器的下拉框
        self.vm_selector = QComboBox()
        self.vm_selector.currentIndexChanged.connect(self._on_vm_changed)
        self.layout.addWidget(self.vm_selector)

        # 画面显示区域
        self.screen_label = QLabel("等待刷新...")
        self.screen_label.setAlignment(Qt.AlignCenter)
        self.screen_label.setMinimumSize(320, 240)
        self.screen_label.setStyleSheet(
            "QLabel { background-color: #1a1a2e; color: #666; "
            "border: 1px solid #333; font-size: 14px; }"
        )
        self.layout.addWidget(self.screen_label, 1)

        # 刷新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(int(1000 / self.fps))

        # 状态
        self.frame_count = 0
        self.error_count = 0

    def set_vms(self, vms):
        """设置可投屏的 VM 列表"""
        self.vms = vms
        self.vm_selector.blockSignals(True)
        self.vm_selector.clear()
        for i, vm in enumerate(vms):
            label = f"[{i+1}] {vm.winName}"
            self.vm_selector.addItem(label, i)
        self.vm_selector.blockSignals(False)
        if vms:
            self.vm_selector.setCurrentIndex(0)
            self._on_vm_changed(0)

    def refresh_vm_list(self, vms):
        """刷新 VM 列表（保留当前选中项）"""
        current_idx = self.vm_selector.currentIndex()
        self.set_vms(vms)
        if current_idx < len(vms):
            self.vm_selector.setCurrentIndex(current_idx)

    def _on_vm_changed(self, index):
        """切换投屏目标"""
        if index < 0 or index >= len(self.vms):
            self.current_hwnd = None
            self.screen_label.setText("无可用窗口")
            return
        self.current_hwnd = self.vms[index].parent
        self.error_count = 0

    def _refresh(self):
        """定时截取并更新画面"""
        self.frame_count += 1
        if self.current_hwnd is None:
            return

        if not win32gui.IsWindow(self.current_hwnd):
            self.error_count += 1
            if self.error_count == 1:
                self.screen_label.setText("窗口已关闭")
            return

        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                return

            pixmap = screen.grabWindow(self.current_hwnd)
            if pixmap is None or pixmap.isNull():
                return

            # 缩放
            w = int(pixmap.width() * self.scale)
            h = int(pixmap.height() * self.scale)
            if w > 0 and h > 0:
                pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.screen_label.setPixmap(pixmap)
            self.error_count = 0
        except Exception:
            self.error_count += 1
            if self.error_count > 10:
                self.timer.stop()
                self.screen_label.setText("截取失败(已停)\n请检查模拟器窗口")

    def set_fps(self, fps):
        """设置刷新率"""
        self.fps = max(1, min(30, fps))
        self.timer.setInterval(int(1000 / self.fps))

    def set_scale(self, scale):
        """设置缩放比例"""
        self.scale = max(0.1, min(1.0, scale))

    def stop(self):
        """停止投屏"""
        self.timer.stop()

    def start(self):
        """开始投屏"""
        self.timer.start(int(1000 / self.fps))
