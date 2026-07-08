# -*- coding: utf-8 -*-
"""小西天场景 UI"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QComboBox, QLabel, QTextEdit, QStatusBar,
    QMessageBox, QApplication, QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import QTimer
from core.adb_util import AdbUtil

STYLE = """
QMainWindow,QWidget{background:#1e1e1e;color:#d4d4d4;font-family:Microsoft YaHei;font-size:13px}
QGroupBox{border:1px solid #444;border-radius:8px;margin-top:12px;padding-top:20px;font-weight:bold;color:#aaa}
QGroupBox::title{subcontrol-origin:margin;left:14px;padding:0 8px}
QPushButton{background:#333;border:1px solid #555;border-radius:5px;padding:7px 16px;color:#d4d4d4}
QPushButton:hover{background:#444} QPushButton:pressed{background:#555} QPushButton:disabled{color:#666;background:#2a2a2a}
QPushButton#btnStart{background:#1a7a3a;color:#fff;border:none;font-weight:bold;font-size:14px}
QPushButton#btnStart:hover{background:#23994a}
QPushButton#btnStop{background:#b5302a;color:#fff;border:none;font-weight:bold;font-size:14px}
QPushButton#btnStop:hover{background:#d43a33}
QComboBox{background:#333;border:1px solid #555;border-radius:4px;padding:4px 8px;color:#d4d4d4}
QComboBox::drop-down{border:none;width:20px}
QComboBox QAbstractItemView{background:#333;color:#d4d4d4;selection-background-color:#4a9eff}
QLabel{color:#d4d4d4}
QTextEdit{background:#1a1a1a;border:1px solid #444;border-radius:4px;color:#b0b0b0;font-family:Consolas;font-size:12px}
QRadioButton{color:#d4d4d4;spacing:6px;font-size:13px}
QStatusBar{background:#111;color:#888}
"""

MODES = [("auto","自动"),("skill","技能"),("capture","捕捉"),("steal","偷窃"),("escape","逃跑")]


class XiaoXiTianWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小西天场景")
        self.setMinimumSize(480,520)
        self.resize(500,550)
        self._thread = None
        self._serial = None
        self._battle_mode = "auto"
        self._setup_ui()

    def _setup_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        lo = QVBoxLayout(cw); lo.setSpacing(8); lo.setContentsMargins(12,12,12,12)

        gb1 = QGroupBox("设备")
        r1 = QHBoxLayout()
        self._cb = QComboBox(); self._cb.setMinimumWidth(300); r1.addWidget(self._cb)
        b1 = QPushButton("刷新"); b1.clicked.connect(self._refresh); r1.addWidget(b1)
        gb1.setLayout(r1); lo.addWidget(gb1)

        gb2 = QGroupBox("战斗模式")
        r2 = QHBoxLayout()
        self._bg = QButtonGroup(self)
        for i,(k,lb) in enumerate(MODES):
            rb = QRadioButton(lb); rb.setChecked(i==0)
            rb.toggled.connect(lambda c,k=k: self._on_mode(k) if c else None)
            self._bg.addButton(rb); r2.addWidget(rb)
        gb2.setLayout(r2); lo.addWidget(gb2)

        gb3 = QGroupBox("控制")
        r3 = QHBoxLayout()
        self._btn1 = QPushButton("开始"); self._btn1.setObjectName("btnStart"); self._btn1.clicked.connect(self._start); r3.addWidget(self._btn1)
        self._btn2 = QPushButton("停止"); self._btn2.setObjectName("btnStop"); self._btn2.setEnabled(False); self._btn2.clicked.connect(self._stop); r3.addWidget(self._btn2)
        self._lbl = QLabel("就绪"); r3.addWidget(self._lbl); r3.addStretch()
        gb3.setLayout(r3); lo.addWidget(gb3)

        gb4 = QGroupBox("日志")
        r4 = QVBoxLayout()
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True); r4.addWidget(self._log_box)
        gb4.setLayout(r4); lo.addWidget(gb4)

        self._bar = QStatusBar(); self.setStatusBar(self._bar); self._bar.showMessage("就绪")
        QTimer.singleShot(300, self._refresh)

    def _on_mode(self,m):
        self._battle_mode = m
        self._log(f"模式: {dict(MODES).get(m,m)}")
        if self._thread and getattr(self._thread,"_battle",None):
            self._thread._battle.set_mode(m)

    def _refresh(self):
        self._cb.clear()
        try:
            for d in AdbUtil.list_devices():
                self._cb.addItem(f"{d['serial']} ({d.get('resolution','?')})", d["serial"])
            if self._cb.count(): self._cb.setCurrentIndex(0); self._log(f"{self._cb.count()} 个设备")
            else: self._log("未发现设备")
        except Exception as e: self._log(f"设备错误: {e}")

    def _start(self):
        if self._cb.count()==0: QMessageBox.warning(self,"提示","请刷新设备"); return
        self._serial = self._cb.currentData()
        if not self._serial: return
        from xiaoxitianchangjing import XiaoXiTianChangJingThread
        self._thread = XiaoXiTianChangJingThread(self._serial, debug_win=False)
        self._thread.add_callback("log", self._log_box)
        self._thread.add_callback("state_update", lambda s: self._lbl.setText(s))
        self._thread.start()
        QTimer.singleShot(2000, lambda: self._sync())
        self._btn1.setEnabled(False); self._btn2.setEnabled(True)
        self._lbl.setText("运行中"); self._lbl.setStyleSheet("font-weight:bold;color:#4aff4a")
        self._bar.showMessage(f"运行中 - {self._serial}")

    def _sync(self):
        if self._thread and getattr(self._thread,"_battle",None):
            self._thread._battle.set_mode(self._battle_mode)

    def _stop(self):
        if self._thread: self._thread.stop(); self._thread.join(timeout=3)
        self._thread = None
        self._btn1.setEnabled(True); self._btn2.setEnabled(False)
        self._lbl.setText("已停止"); self._lbl.setStyleSheet("font-weight:bold;color:#ff4444")

    def _log(self, msg):
        self._log_box.append(msg)
        v = self._log_box.verticalScrollBar()
        v.setValue(v.maximum())

    def closeEvent(self, e):
        if self._thread and self._thread.running:
            r = QMessageBox.question(self,"确认","正在运行，退出？",QMessageBox.Yes|QMessageBox.No)
            if r==QMessageBox.No: e.ignore(); return
            self._stop()
        super().closeEvent(e)


def run():
    a = QApplication(sys.argv)
    a.setStyleSheet(STYLE)
    w = XiaoXiTianWindow()
    w.show()
    sys.exit(a.exec_())


if __name__=="__main__":
    run()
