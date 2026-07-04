# -*- coding: utf-8 -*-
"""点卡场景 v3 - 主界面（参照小霸王原版 DKChangJingConfigWin + DetailWin 布局）"""
import os, sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QComboBox, QLabel, QTextEdit, QCheckBox,
    QSpinBox, QStatusBar, QMessageBox, QApplication, QSlider, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from core.adb_util import AdbUtil
from core.screenshot import ScreenCapture
from ui.device_dialog import DeviceSelectDialog
from core.dk_thread import DKChangJingThread
from xiao_xitian import XiaoXiTianThread
from config.dk_config import DKConfig, ADD_XUE_MODES, ADD_LAN_MODES

# ---- 暗色主题 ----
STYLE = """
QMainWindow,QWidget{background:#1e1e1e;color:#d4d4d4;font-family:"Microsoft YaHei";font-size:13px}
QGroupBox{border:1px solid #444;border-radius:8px;margin-top:12px;padding-top:20px;font-weight:bold;color:#aaa}
QGroupBox::title{subcontrol-origin:margin;left:14px;padding:0 8px}
QPushButton{background:#333;border:1px solid #555;border-radius:5px;padding:7px 16px;color:#d4d4d4}
QPushButton:hover{background:#444} QPushButton:pressed{background:#555} QPushButton:disabled{color:#666;background:#2a2a2a}
QPushButton#btnStart{background:#1a7a3a;color:#fff;border:none;font-weight:bold;font-size:14px}
QPushButton#btnStart:hover{background:#23994a}
QPushButton#btnStop{background:#b5302a;color:#fff;border:none;font-weight:bold;font-size:14px}
QPushButton#btnStop:hover{background:#d43a33}
QPushButton#btnSave{background:#2a5fa8;color:#fff;border:none}
QPushButton#btnSave:hover{background:#3575c8}
QPushButton#btnBind{background:#1a6a9a;color:#fff;border:none}
QPushButton#btnBind:hover{background:#2080b8}
QComboBox{background:#333;border:1px solid #555;border-radius:4px;padding:4px 8px;color:#d4d4d4;min-height:22px}
QComboBox::drop-down{border:none;width:20px}
QComboBox QAbstractItemView{background:#333;color:#d4d4d4;selection-background-color:#4a9eff}
QSpinBox{background:#333;border:1px solid #555;border-radius:4px;padding:3px;color:#d4d4d4}
QLabel{color:#d4d4d4}
QLabel#titleLabel{font-size:15px;font-weight:bold;color:#fff}
QLabel#sectionTitle{font-size:13px;font-weight:bold;color:#aaa;padding:4px 0}
QTextEdit{background:#1a1a1a;border:1px solid #444;border-radius:4px;color:#b0b0b0;font-family:Consolas;font-size:12px}
QCheckBox{color:#d4d4d4;spacing:8px;font-size:13px}
QCheckBox::indicator{width:18px;height:18px}
QSlider::groove:horizontal{background:#333;height:8px;border-radius:4px}
QSlider::handle:horizontal{background:#4a9eff;width:18px;margin:-5px 0;border-radius:9px}
QSlider::sub-page:horizontal#hpSlider{background:rgb(255,20,147);border-radius:4px}
QSlider::sub-page:horizontal#mpSlider{background:rgb(30,144,255);border-radius:4px}
QStatusBar{background:#111;color:#888}
QFrame#card{border:1px solid #444;border-radius:8px;background:#252525;padding:8px}
QFrame#sep{background:#444;max-height:1px}
"""

# ---- 自定义开关按钮 ----
class ToggleSwitch(QPushButton):
    """模拟原版 SwitchButton 的开关按钮"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._checked = False
        self.setCheckable(True)
        self.setFixedHeight(32)
        self.setStyleSheet("""
            QPushButton { text-align:left; padding-left:12px; border:none; background:transparent; color:#aaa; font-size:13px }
            QPushButton:checked { color:#4aff4a; font-weight:bold }
        """)
        self.toggled.connect(lambda v: self._update())
        self._update()

    def _update(self):
        self._checked = self.isChecked()

    def setChecked(self, v):
        super().setChecked(v)
        self._update()

    def isChecked(self):
        return super().isChecked()


class DKChangJingWindow(QMainWindow):
    """点卡场景主窗口 - 参照小霸王原版 UI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("点卡场景 - 场景自动化")
        self.setMinimumSize(620, 700)
        self.resize(640, 750)

        self.capture = ScreenCapture()
        self.config = DKConfig()
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.thread = None
        self._devices = []
        self._selected_serial = None
        self._frame = None

        self._setup_ui()
        self._setup_connections()
        self._load_config()
        QTimer.singleShot(500, lambda: self._log("就绪 - 请点击「选择设备」查看设备列表"))

    # ================================================================
    # UI 布局（参照原版 DKChangJingConfigWin + DetailWin）
    # ================================================================

    def _setup_ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        L = QVBoxLayout(c)
        L.setContentsMargins(12, 12, 12, 12)
        L.setSpacing(8)

        # ---- 顶部控制栏（参照 DetailWin title_layout） ----
        top = QHBoxLayout()
        top.setSpacing(10)

        self._btn_start = QPushButton("▶  开始挂机")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setFixedSize(120, 36)

        self._btn_stop = QPushButton("■  停止")
        self._btn_stop.setObjectName("btnStop")
        self._btn_stop.setFixedSize(100, 36)
        self._btn_stop.setEnabled(False)

        self._lbl_title = QLabel("点卡场景")
        self._lbl_title.setObjectName("titleLabel")

        self._btn_save = QPushButton("保存配置")
        self._btn_save.setObjectName("btnSave")
        self._btn_save.setFixedWidth(90)

        top.addWidget(self._btn_start)
        top.addWidget(self._btn_stop)
        top.addWidget(self._lbl_title)
        top.addStretch()
        top.addWidget(self._btn_save)
        L.addLayout(top)

        # 分隔线
        sep = QFrame(); sep.setObjectName("sep"); sep.setFrameShape(QFrame.HLine)
        L.addWidget(sep)

        # ---- 设备绑定区 ----
        dev_group = QGroupBox("设备绑定")
        dev_layout = QHBoxLayout(dev_group)
        dev_layout.setContentsMargins(10, 12, 10, 8)
        dev_layout.setSpacing(8)

        self._btn_select_dev = QPushButton("选择设备")
        self._btn_select_dev.setObjectName("btnBind")
        self._btn_bind = QPushButton("绑定窗口")
        self._btn_bind.setObjectName("btnBind")
        self._lbl_dev = QLabel("未选择设备 | 未绑定窗口")
        self._lbl_dev.setStyleSheet("color:#888;padding:0 8px")

        dev_layout.addWidget(self._btn_select_dev)
        dev_layout.addWidget(self._btn_bind)
        dev_layout.addWidget(self._lbl_dev, 1)
        L.addWidget(dev_group)
        # ---- 场景选择 ----
        scene_group = QGroupBox("刷场景")
        scene_layout = QHBoxLayout(scene_group)
        scene_layout.setContentsMargins(10, 12, 10, 8)
        scene_layout.setSpacing(8)

        scene_layout.addWidget(QLabel("地点："))
        self._scene_combo = QComboBox()
        self._scene_combo.addItems(["小西天", "丝绸之路"])
        self._scene_combo.setFixedWidth(120)
        scene_layout.addWidget(self._scene_combo)
        scene_layout.addStretch()
        L.addWidget(scene_group)


        # ---- 角色设置 Card（参照原版 roleContainer） ----
        role_group = QGroupBox("角色设置")
        role_layout = QVBoxLayout(role_group)
        role_layout.setContentsMargins(10, 12, 10, 10)
        role_layout.setSpacing(8)

        # 加血加蓝方式行
        hpmp_row = QHBoxLayout()
        hpmp_row.setAlignment(Qt.AlignLeft)
        hpmp_row.setSpacing(20)

        hpmp_row.addWidget(QLabel("人物加血方式："))
        self._hp_mode = QComboBox()
        self._hp_mode.addItems(ADD_XUE_MODES)
        self._hp_mode.setFixedWidth(80)
        self._hp_mode.setCurrentText(self.config.role_add_xue_mode)
        hpmp_row.addWidget(self._hp_mode)

        hpmp_row.addWidget(QLabel("人物加蓝方式："))
        self._mp_mode = QComboBox()
        self._mp_mode.addItems(ADD_LAN_MODES)
        self._mp_mode.setFixedWidth(80)
        self._mp_mode.setCurrentText(self.config.role_add_lan_mode)
        hpmp_row.addWidget(self._mp_mode)
        hpmp_row.addStretch()
        role_layout.addLayout(hpmp_row)

        # 血蓝阈值滑动条行
        pct_row = QHBoxLayout()
        pct_row.setAlignment(Qt.AlignLeft)
        pct_row.setSpacing(20)

        pct_row.addWidget(QLabel("人物血量低于时补充："))
        self._hp_slider = QSlider(Qt.Horizontal)
        self._hp_slider.setObjectName("hpSlider")
        self._hp_slider.setRange(0, 100)
        self._hp_slider.setValue(self.config.role_xue_percent)
        self._hp_slider.setFixedWidth(160)
        self._hp_slider.setStyleSheet(
            "QSlider::sub-page:horizontal{background:rgb(220,30,100);border-radius:4px}"
        )
        self._hp_pct = QLabel(f"{self.config.role_xue_percent}%")
        self._hp_pct.setFixedWidth(36)
        pct_row.addWidget(self._hp_slider)
        pct_row.addWidget(self._hp_pct)

        pct_row.addWidget(QLabel("人物蓝量低于时补充："))
        self._mp_slider = QSlider(Qt.Horizontal)
        self._mp_slider.setObjectName("mpSlider")
        self._mp_slider.setRange(0, 100)
        self._mp_slider.setValue(self.config.role_lan_percent)
        self._mp_slider.setFixedWidth(160)
        self._mp_slider.setStyleSheet(
            "QSlider::sub-page:horizontal{background:rgb(30,144,255);border-radius:4px}"
        )
        self._mp_pct = QLabel(f"{self.config.role_lan_percent}%")
        self._mp_pct.setFixedWidth(36)
        pct_row.addWidget(self._mp_slider)
        pct_row.addWidget(self._mp_pct)
        pct_row.addStretch()
        role_layout.addLayout(pct_row)

        L.addWidget(role_group)

        # ---- 战斗操作 Card（参照原版 roleOperateContiner + otherSettingContiner 左右并排） ----
        battle_group = QGroupBox("战斗操作")
        battle_outer = QHBoxLayout(battle_group)
        battle_outer.setContentsMargins(10, 12, 10, 10)
        battle_outer.setSpacing(16)

        # ---- 左列：人物战斗操作 ----
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        left_layout.setAlignment(Qt.AlignTop)

        left_layout.addWidget(self._mk_section_title("人物战斗操作："))

        # 一、捕捉
        self._sw_zhua = ToggleSwitch("    一、捕捉")
        self._sw_zhua.setChecked(self.config.is_zhua)
        left_layout.addWidget(self._sw_zhua)

        # 二、妙手空空（带"设置"链接）
        tou_row = QHBoxLayout()
        tou_row.setContentsMargins(0, 0, 0, 0)
        tou_row.setSpacing(6)
        self._sw_tou = ToggleSwitch("    二、妙手空空")
        self._sw_tou.setChecked(self.config.is_tou)
        tou_row.addWidget(self._sw_tou)
        self._btn_tou_setting = QPushButton("设置")
        self._btn_tou_setting.setStyleSheet(
            "QPushButton{border:none;background:transparent;color:#1e90ff;padding:0 6px}"
            "QPushButton:hover{color:#4ab1ff;text-decoration:underline}"
        )
        self._btn_tou_setting.setCursor(Qt.PointingHandCursor)
        tou_row.addWidget(self._btn_tou_setting)
        tou_row.addStretch()
        left_layout.addLayout(tou_row)

        # 互斥 PK 区（参照原版: 三、1~5 编号）
        left_layout.addWidget(self._mk_section_title("遇怪操作（互斥）："))

        self._sw_skill = ToggleSwitch("    三、1.点选技能后自动战斗")
        self._sw_skill.setChecked(self.config.is_pk_jineng)
        left_layout.addWidget(self._sw_skill)

        self._sw_attack = ToggleSwitch("        2.普通攻击后自动战斗")
        self._sw_attack.setChecked(self.config.is_pk_pugong)
        left_layout.addWidget(self._sw_attack)

        self._sw_defend = ToggleSwitch("        3.防御后自动战斗")
        self._sw_defend.setChecked(self.config.is_pk_fangyu)
        left_layout.addWidget(self._sw_defend)

        self._sw_auto = ToggleSwitch("        4.直接自动战斗")
        self._sw_auto.setChecked(self.config.is_pk_auto)
        left_layout.addWidget(self._sw_auto)

        self._sw_flee = ToggleSwitch("        5.逃跑")
        self._sw_flee.setChecked(self.config.is_pk_taopao)
        left_layout.addWidget(self._sw_flee)

        # ---- 右列：其他设置 ----
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)
        right_layout.setAlignment(Qt.AlignTop)

        right_layout.addSpacing(18)  # 与左列"人物战斗操作"对齐

        self._sw_nav = ToggleSwitch("    自动寻路（队长模式）")
        self._sw_nav.setChecked(self.config.is_duizhang)
        right_layout.addWidget(self._sw_nav)

        self._sw_wuyi = ToggleSwitch("    自动巫医治疗")
        self._sw_wuyi.setChecked(self.config.is_wuyi)
        right_layout.addWidget(self._sw_wuyi)

        right_layout.addStretch()

        battle_outer.addWidget(left_col, 1)
        battle_outer.addWidget(right_col, 1)
        L.addWidget(battle_group)

        # ---- 运行状态 ----
        status_row = QHBoxLayout()
        status_row.setSpacing(16)
        self._lbl_status = QLabel("就绪")
        self._lbl_status.setStyleSheet("font-size:13px;font-weight:bold;color:#4a9eff")
        self._lbl_count = QLabel("战斗次数: 0")
        self._lbl_count.setStyleSheet("color:#aaa;font-size:12px")
        self._lbl_hp = QLabel("HP: --")
        self._lbl_hp.setStyleSheet("color:#ff6090;font-size:12px")
        self._lbl_mp = QLabel("MP: --")
        self._lbl_mp.setStyleSheet("color:#4a9eff;font-size:12px")
        status_row.addWidget(self._lbl_status)
        status_row.addWidget(self._lbl_count)
        status_row.addWidget(self._lbl_hp)
        status_row.addWidget(self._lbl_mp)
        status_row.addStretch()
        L.addLayout(status_row)

        # ---- 日志 ----
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(6, 8, 6, 6)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(150)
        self._log_text.setMinimumHeight(80)
        log_layout.addWidget(self._log_text)
        L.addWidget(log_group)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪 - 请点击「选择设备」并「绑定窗口」")

    # ================================================================
    # 信号连接
    # ================================================================

    def _setup_connections(self):
        self._btn_select_dev.clicked.connect(self._select_device)
        self._btn_bind.clicked.connect(self._bind_window)
        self._btn_start.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop)
        self._btn_save.clicked.connect(self._save_config)
        if hasattr(self, "_btn_tou_setting"):
            self._btn_tou_setting.clicked.connect(self._show_tou_setting)

        # HP/MP 滑动条
        self._hp_slider.valueChanged.connect(lambda v: self._hp_pct.setText(f"{v}%"))
        self._mp_slider.valueChanged.connect(lambda v: self._mp_pct.setText(f"{v}%"))

        # PK 互斥（参照原版 rolePkHuChi）
        for sw, field in [
            (self._sw_skill, "is_pk_jineng"),
            (self._sw_attack, "is_pk_pugong"),
            (self._sw_defend, "is_pk_fangyu"),
            (self._sw_auto, "is_pk_auto"),
            (self._sw_flee, "is_pk_taopao"),
        ]:
            sw.toggled.connect(lambda checked, s=sw, f=field: self._pk_mutex(s, f, checked))

    def _mk_section_title(self, text):
        """小节标题（图一风格：浅色加粗）"""
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#bbb;font-size:12px;font-weight:bold;padding:6px 0 2px 0")
        return lbl

    def _show_tou_setting(self):
        """妙手空空设置"""
        msg = (
            "妙手空空 - 偷窃模式\n\n"
            "功能说明：\n"
            "  开启后，进入战斗自动使用图像匹配\n"
            "  识别可偷窃的召唤兽并逐个偷取（最多4次）。\n\n"
            "支持场景及目标：\n"
            "  丝绸之路  - 蛟龙系列\n"
            "  碗子山    - 巡游天神、雨师\n"
            "  凤巢      - 蛟龙、天将、凤凰\n"
            "  小西天    - 噬天虎\n"
            "  小雷音寺  - 大力金刚\n"
            "  子母河底  - 蚌精、碧水夜叉、鲛人\n"
            "  解阳山    - 鼠先锋、金翼\n"
            "  麒麟山    - 百足将军、野猪精\n"
            "  龙窟      - 蛟龙、地狱战神\n"
            "  伊阙龙门  - 金饶僧、镜妖\n"
            "  女娲神迹  - 律法女娲、灵符女娲\n"
            "  须弥东界  - 持国巡守\n"
            "  银华镜    - 广目巡守\n"
            "  弥勒山    - 多闻巡守\n"
            "  九黎城    - 涂山瞳\n"
            "  墨家村    - 缘劫女娲\n"
            "  凌波城    - 泪妖\n"
            "  普陀山    - 灵鹤、炎魔神\n\n"
            "使用方式：勾选「妙手空空」开关即可，无需额外设置。"
        )
        QMessageBox.information(self, "妙手空空设置", msg)

    def _pk_mutex(self, current_sw, field, checked):
        """PK 选项互斥"""
        if checked:
            for sw in [self._sw_skill, self._sw_attack, self._sw_defend, self._sw_auto, self._sw_flee]:
                if sw is not current_sw:
                    sw.blockSignals(True)
                    sw.setChecked(False)
                    sw.blockSignals(False)

    # ================================================================
    # 日志
    # ================================================================

    def _log(self, msg):
        self._log_text.append(msg)
        lines = self._log_text.toPlainText().split("\n")
        if len(lines) > 300:
            self._log_text.setPlainText("\n".join(lines[-200:]))
        sb = self._log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ================================================================
    # 设备管理
    # ================================================================

    def _select_device(self):
        """打开设备选择弹窗"""
        dlg = DeviceSelectDialog(self)
        if dlg.exec() == DeviceSelectDialog.Accepted:
            serial = dlg.get_selected_serial()
            if serial:
                self._selected_serial = serial
                self._devices = AdbUtil.list_devices()
                for d in self._devices:
                    if d["serial"] == serial:
                        res = d.get("resolution", "")
                        self._lbl_dev.setText(f"已选: {serial} [{res}]")
                        self._lbl_dev.setStyleSheet("color:#4a9eff;padding:0 8px")
                        self._log(f"已选择设备: {serial} [{res}]")
                        return
                self._lbl_dev.setText(f"已选: {serial}")
                self._lbl_dev.setStyleSheet("color:#4a9eff;padding:0 8px")
                self._log(f"已选择设备: {serial}")

    def _bind_window(self):
        hwnd = self.capture.find_window()
        if hwnd and self.capture.bind(hwnd):
            import win32gui
            t = win32gui.GetWindowText(hwnd)
            self._lbl_dev.setText(f"已绑定: {t[:28]}")
            self._lbl_dev.setStyleSheet("color:#4aff4a;padding:0 8px")
            self._log(f"已绑定窗口: {t}")
        else:
            self._log("未找到投屏窗口，请先启动效卫安卓投屏")

    # ================================================================
    # 启停控制
    # ================================================================

    def _start(self):
        serial = self._selected_serial
        if not self._selected_serial:
            QMessageBox.warning(self, "提示", "请先选择ADB设备")
            return
        scene = self._scene_combo.currentText() if hasattr(self, "_scene_combo") else "小西天"
        # ??????? pyscrcpy ???????????
        if scene != "小西天":
            if not self.capture.is_bound:
                self._bind_window()
                if not self.capture.is_bound:
                    QMessageBox.warning(self, "提示", "请先绑定投屏窗口")
                    return

        self._update_config()
        self._log(f"刷场景地点: {scene}")

        if scene == "小西天":
            self.thread = XiaoXiTianThread(
                self._selected_serial, self.capture
            )
        else:
            self.thread = DKChangJingThread(
                self._selected_serial, self.config, self.capture
            )
        self.thread.add_callback("log", self._log)
        self.thread.add_callback("state_update", self._on_state)
        self.thread.start()

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._lbl_status.setText("运行中")
        self._lbl_status.setStyleSheet("font-size:13px;font-weight:bold;color:#4aff4a")
        self._status_bar.showMessage(f"运行中 - 设备 {self._selected_serial}")

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_stats)
        self._update_timer.start(1000)

    def _stop(self):
        if self.thread and self.thread.running:
            self.thread.stop()
            self.thread.join(timeout=3)
        self.thread = None
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()

        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._lbl_status.setText("已停止")
        self._lbl_status.setStyleSheet("font-size:13px;font-weight:bold;color:#ff4444")
        self._status_bar.showMessage("已停止")

    def _update_stats(self):
        if self.thread and self.thread.running:
            self._lbl_count.setText(f"战斗次数: {self.thread.battle_count}")
            self._lbl_status.setText(f"状态: {self.thread.state}")
            self._status_bar.showMessage(
                f"状态:{self.thread.state} | 战斗:{self.thread.battle_count}"
            )

    def _on_state(self, state, count=0):
        if count:
            self._lbl_count.setText(f"战斗次数: {count}")

    # ================================================================
    # 配置管理
    # ================================================================

    def _update_config(self):
        self.config.role_add_xue_mode = self._hp_mode.currentText()
        self.config.role_add_lan_mode = self._mp_mode.currentText()
        self.config.role_xue_percent = self._hp_slider.value()
        self.config.role_lan_percent = self._mp_slider.value()
        self.config.is_zhua = self._sw_zhua.isChecked()
        self.config.is_tou = self._sw_tou.isChecked()
        self.config.is_duizhang = self._sw_nav.isChecked()
        self.config.is_wuyi = self._sw_wuyi.isChecked()
        self.config.is_pk_jineng = self._sw_skill.isChecked()
        self.config.is_pk_pugong = self._sw_attack.isChecked()
        self.config.is_pk_fangyu = self._sw_defend.isChecked()
        self.config.is_pk_auto = self._sw_auto.isChecked()
        self.config.is_pk_taopao = self._sw_flee.isChecked()

    def _save_config(self):
        self._update_config()
        self.config.save(self.config_path)
        self._log("配置已保存")

    def _load_config(self):
        if os.path.exists(self.config_path):
            self.config = DKConfig.load(self.config_path)
            self._log("已加载保存的配置")
            # 更新 UI
            self._hp_mode.setCurrentText(self.config.role_add_xue_mode)
            self._mp_mode.setCurrentText(self.config.role_add_lan_mode)
            self._hp_slider.setValue(self.config.role_xue_percent)
            self._mp_slider.setValue(self.config.role_lan_percent)
            self._sw_zhua.setChecked(self.config.is_zhua)
            self._sw_tou.setChecked(self.config.is_tou)
            self._sw_nav.setChecked(self.config.is_duizhang)
            self._sw_wuyi.setChecked(self.config.is_wuyi)
            self._sw_skill.setChecked(self.config.is_pk_jineng)
            self._sw_attack.setChecked(self.config.is_pk_pugong)
            self._sw_defend.setChecked(self.config.is_pk_fangyu)
            self._sw_auto.setChecked(self.config.is_pk_auto)
            self._sw_flee.setChecked(self.config.is_pk_taopao)

    def closeEvent(self, e):
        if self.thread and self.thread.running:
            r = QMessageBox.question(
                self, "确认", "自动化正在运行，确定退出？",
                QMessageBox.Yes | QMessageBox.No
            )
            if r == QMessageBox.No:
                e.ignore()
                return
            self._stop()
        super().closeEvent(e)


def run():
    a = QApplication(sys.argv)
    a.setStyleSheet(STYLE)
    w = DKChangJingWindow()
    w.show()
    sys.exit(a.exec())


if __name__ == "__main__":
    run()
