# -*- coding: utf-8 -*-
"""设备选择弹窗 - 显示ADB设备列表及画面预览"""

import os, time
from io import BytesIO

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QWidget, QFrame,
    QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QFont

from adbutils import adb

DLG_STYLE = """
QDialog{background:#1e1e1e;color:#d4d4d4;font-family:"Microsoft YaHei";font-size:13px}
QPushButton{background:#333;border:1px solid #555;border-radius:5px;padding:6px 14px;color:#d4d4d4}
QPushButton:hover{background:#444}
QPushButton#btnRefresh{background:#1a6a9a;color:#fff;border:none;font-weight:bold}
QPushButton#btnRefresh:hover{background:#2080b8}
QPushButton#btnConfirm{background:#1a7a3a;color:#fff;border:none;font-weight:bold;font-size:14px}
QPushButton#btnConfirm:hover{background:#23994a}
QPushButton#btnCancel{background:#555;color:#fff;border:none}
QPushButton#btnCancel:hover{background:#666}
QLabel{color:#d4d4d4}
QLabel#lblTitle{font-size:15px;font-weight:bold;color:#fff}
QScrollArea{background:#1a1a1a;border:1px solid #333;border-radius:6px}
QFrame#deviceCard{background:#252525;border:2px solid #444;border-radius:8px}
QFrame#deviceCard[selected="true"]{border:2px solid #4a9eff;background:#2a3040}
"""


class ScreenshotLoader(QThread):
    """后台逐个加载设备截图（避免多线程ADB冲突）"""
    result = Signal(str, object)

    def __init__(self, serials):
        super().__init__()
        self.serials = serials

    def run(self):
        for serial in self.serials:
            try:
                d = adb.device(serial)
                img = d.screenshot()
                self.result.emit(serial, img)
            except Exception as e:
                print(f"[ScreenshotLoader] {serial}: {e}")
                self.result.emit(serial, None)


class DeviceSelectDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择ADB设备")
        self.setMinimumSize(500, 400)
        self.resize(580, 520)
        self.setStyleSheet(DLG_STYLE)
        self.setModal(True)

        self._selected_serial = None
        self._devices = []
        self._cards = {}
        self._thumb_labels = {}
        self._loader = None

        self._setup_ui()
        self._refresh_devices()

    def _setup_ui(self):
        L = QVBoxLayout(self)
        L.setContentsMargins(16, 16, 16, 16)
        L.setSpacing(10)

        header = QHBoxLayout()
        lbl = QLabel("ADB设备列表")
        lbl.setObjectName("lblTitle")
        header.addWidget(lbl)
        header.addStretch()
        btn_refresh = QPushButton("刷新设备")
        btn_refresh.setObjectName("btnRefresh")
        btn_refresh.setFixedWidth(100)
        btn_refresh.clicked.connect(self._refresh_devices)
        header.addWidget(btn_refresh)
        L.addLayout(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(4, 4, 4, 4)
        self._container_layout.setSpacing(8)
        self._container_layout.addStretch()
        self._scroll.setWidget(self._container)
        L.addWidget(self._scroll, 1)

        self._lbl_status = QLabel("正在扫描设备...")
        self._lbl_status.setStyleSheet("color:#888")
        L.addWidget(self._lbl_status)

        footer = QHBoxLayout()
        footer.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.setFixedWidth(80)
        btn_cancel.clicked.connect(self.reject)
        footer.addWidget(btn_cancel)
        self._btn_confirm = QPushButton("确认绑定")
        self._btn_confirm.setObjectName("btnConfirm")
        self._btn_confirm.setFixedWidth(120)
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.clicked.connect(self._on_confirm)
        footer.addWidget(self._btn_confirm)
        L.addLayout(footer)

    def _refresh_devices(self):
        """扫描ADB设备并加载截图"""
        self._lbl_status.setText("正在扫描设备...")
        self._lbl_status.setStyleSheet("color:#888")
        QApplication.processEvents()

        self._selected_serial = None
        self._btn_confirm.setEnabled(False)
        self._cards.clear()
        self._thumb_labels.clear()

        if self._loader and self._loader.isRunning():
            self._loader.terminate()
            self._loader.wait(2000)

        while self._container_layout.count() > 1:
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._devices = []
        try:
            for d in adb.device_list():
                serial = d.serial
                resolution = ""
                try:
                    wmsize = d.shell("wm size")
                    for line in wmsize.strip().split("\n"):
                        line = line.strip()
                        if "Override size:" in line:
                            resolution = line.split("Override size:")[-1].strip()
                        elif "Physical size:" in line:
                            resolution = line.split("Physical size:")[-1].strip()
                except Exception:
                    pass
                self._devices.append({"serial": serial, "resolution": resolution})
        except Exception as e:
            self._lbl_status.setText("扫描失败: " + str(e))
            self._lbl_status.setStyleSheet("color:#ff4444")
            return

        if not self._devices:
            self._lbl_status.setText("未发现ADB设备")
            self._lbl_status.setStyleSheet("color:#ffaa00")
            return

        self._lbl_status.setText("发现 %d 个设备，加载画面中..." % len(self._devices))

        for dev in self._devices:
            card = self._create_device_card(dev)
            self._container_layout.insertWidget(self._container_layout.count() - 1, card)

        serials = [d["serial"] for d in self._devices]
        if serials:
            self._loader = ScreenshotLoader(serials)
            self._loader.result.connect(self._on_screenshot_loaded)
            self._loader.start()

    def _create_device_card(self, dev):
        card = QFrame()
        card.setObjectName("deviceCard")
        card.setFixedHeight(100)
        card.setCursor(Qt.PointingHandCursor)
        card.setProperty("device_serial", dev["serial"])

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        thumb = QLabel("加载中...")
        thumb.setFixedSize(120, 80)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setStyleSheet("background:#1a1a1a;border:1px solid #333;border-radius:4px;color:#666;font-size:11px")
        layout.addWidget(thumb)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        lbl_serial = QLabel("序列号: " + dev["serial"])
        lbl_serial.setFont(QFont("Consolas", 10))
        lbl_serial.setStyleSheet("color:#ddd;font-weight:bold")
        info_layout.addWidget(lbl_serial)

        if dev["resolution"]:
            lbl_res = QLabel("分辨率: " + dev["resolution"])
            lbl_res.setStyleSheet("color:#999;font-size:12px")
            info_layout.addWidget(lbl_res)

        lbl_hint = QLabel("点击选中此设备")
        lbl_hint.setStyleSheet("color:#666;font-size:11px")
        info_layout.addWidget(lbl_hint)
        info_layout.addStretch()
        layout.addLayout(info_layout, 1)

        lbl_check = QLabel("O")
        lbl_check.setFixedWidth(30)
        lbl_check.setAlignment(Qt.AlignCenter)
        lbl_check.setStyleSheet("color:#666;font-size:20px;font-weight:bold")
        layout.addWidget(lbl_check)

        card.mousePressEvent = lambda e, s=dev["serial"]: self._select_device(s)

        self._cards[dev["serial"]] = card
        self._thumb_labels[dev["serial"]] = thumb
        card.setProperty("check_label", lbl_check)
        return card

    def _on_screenshot_loaded(self, serial, img):
        if serial not in self._thumb_labels:
            return
        thumb = self._thumb_labels[serial]
        if img is not None:
            try:
                buf = BytesIO()
                img.save(buf, format="PNG")
                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                scaled = pix.scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb.setPixmap(scaled)
            except Exception:
                thumb.setText("加载失败")
        else:
            thumb.setText("无画面")
        thumb.setStyleSheet("background:#1a1a1a;border:1px solid #333;border-radius:4px")

    def _select_device(self, serial):
        self._selected_serial = serial
        self._btn_confirm.setEnabled(True)
        for s, card in self._cards.items():
            if s == serial:
                card.setProperty("selected", "true")
                card.setStyleSheet(
                    'QFrame#deviceCard[selected="true"]'
                    "{border:2px solid #4a9eff;background:#2a3040;border-radius:8px}"
                )
                chk = card.property("check_label")
                if chk:
                    chk.setText(".")
                    chk.setStyleSheet("color:#4a9eff;font-size:20px;font-weight:bold")
            else:
                card.setProperty("selected", "false")
                card.setStyleSheet(
                    "QFrame#deviceCard{background:#252525;border:2px solid #444;border-radius:8px}"
                )
                chk = card.property("check_label")
                if chk:
                    chk.setText("O")
                    chk.setStyleSheet("color:#666;font-size:20px;font-weight:bold")

    def _on_confirm(self):
        if self._selected_serial:
            self.accept()

    def get_selected_serial(self):
        return self._selected_serial

    def closeEvent(self, e):
        if self._loader and self._loader.isRunning():
            self._loader.terminate()
        super().closeEvent(e)
