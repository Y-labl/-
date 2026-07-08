"""主窗口 - 所有功能模块的集成界面"""

import sys
import os
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QComboBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QGroupBox, QTextEdit, QStatusBar,
    QMessageBox, QApplication, QCheckBox, QMenu, QFileDialog,
    QScrollArea, QSizePolicy, QTabWidget, QDialog, QFrame
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QThread
from PySide6.QtGui import (
    QIcon,
    QPixmap, QImage, QPainter, QColor, QPen, QFont,
    QMouseEvent, QClipboard, QCursor, QAction
)

from modules.window_binder import WindowBinder, WindowInfo, get_window_under_cursor
from modules.adb_scanner import AdbScanner
from modules.screenshot import ScreenCapture
from modules.color_picker import ColorPicker, ColorPoint
from modules.color_verifier import ColorVerifier
from modules.coordinate import CoordinateTracker
from modules.template_matcher import TemplateMatcher, TemplateMatch


# ─── 颜色常量 ───
COLOR_FOUND = QColor(0, 200, 80)
COLOR_NOT_FOUND = QColor(240, 60, 60)
COLOR_PENDING = QColor(180, 180, 180)
COLOR_BG = "#2b2b2b"
COLOR_SURFACE = "#3c3c3c"
COLOR_TEXT = "#e0e0e0"
COLOR_ACCENT = "#4a9eff"

STYLE_DARK = """
QMainWindow, QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
    color: #ccc;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 14px;
    color: #e0e0e0;
}
QPushButton:hover { background-color: #4a4a4a; }
QPushButton:pressed { background-color: #555; }
QPushButton:disabled { color: #777; }
QPushButton#btnPrimary {
    background-color: #4a9eff;
    color: #fff;
    border: none;
    font-weight: bold;
}
QPushButton#btnPrimary:hover { background-color: #3a8eef; }
QPushButton#btnDanger {
    background-color: #d64545;
    color: #fff;
    border: none;
}
QPushButton#btnDanger:hover { background-color: #c53535; }
QPushButton#btnSuccess {
    background-color: #2d8c4a;
    color: #fff;
    border: none;
}
QPushButton#btnSuccess:hover { background-color: #247a3d; }
QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #e0e0e0;
    selection-background-color: #4a9eff;
}
QTableWidget {
    background-color: #333;
    alternate-background-color: #3a3a3a;
    border: 1px solid #555;
    border-radius: 4px;
    gridline-color: #555;
    color: #e0e0e0;
}
QTableWidget::item:selected {
    background-color: #4a9eff;
    color: #fff;
}
QHeaderView::section {
    background-color: #3c3c3c;
    border: 1px solid #555;
    padding: 4px;
    font-weight: bold;
}
QSpinBox {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 3px;
    color: #e0e0e0;
}
QLabel { color: #e0e0e0; }
QTextEdit {
    background-color: #333;
    border: 1px solid #555;
    border-radius: 4px;
    color: #d0d0d0;
}
QScrollArea {
    border: none;
    background-color: #222;
}
QStatusBar {
    background-color: #222;
    color: #aaa;
}
QSplitter::handle {
    background-color: #555;
    width: 2px;
}
QTabWidget::pane {
    border: 1px solid #555;
    background-color: #2b2b2b;
}
QTabBar::tab {
    background-color: #333;
    border: 1px solid #555;
    border-bottom: none;
    padding: 6px 14px;
    color: #aaa;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #3c3c3c;
    color: #4a9eff;
    font-weight: bold;
}
QTabBar::tab:hover {
    color: #e0e0e0;
}
"""


class ClickableLabel(QLabel):
    """可点击的截图预览标签，支持缩放/平移/取色/悬停坐标"""
    clicked = Signal(int, int)      # 左键点击 → (图片坐标x, 图片坐标y)
    hovered = Signal(int, int)       # 鼠标悬停 → (图片坐标x, 图片坐标y)
    zoom_changed = Signal(float)     # 缩放变化 → 当前缩放比率(相对原图)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumSize(320, 240)
        self.setStyleSheet("background-color: #222; border: 1px solid #555;")
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self._pixmap_original = None
        self._zoom_level = 0.0       # 0 = 自适应窗口, >0 = 相对自适应的倍率
        self._fit_scale = 1.0        # 自适应窗口时的适合比率
        self._scale_factor = 1.0     # 最终渲染比率 = fit_scale * zoom_level
        self._offset_x = 0
        self._offset_y = 0
        self._annotations = []
        self._panning = False
        self._pan_start = None
        self._pan_offset_x = 0
        self._pan_offset_y = 0

    # ── 缩放控制 ──
    def set_zoom(self, level: float):
        """level=0 → 自适应, >0 → 指定倍率(相对自适应的倍数)"""
        self._zoom_level = max(0.0, min(level, 12.0))
        self._pan_offset_x = 0
        self._pan_offset_y = 0
        self._update_display()

    def zoom_in(self):
        if self._zoom_level <= 0:
            self._zoom_level = 1.0
        self.set_zoom(min(self._zoom_level * 1.3, 12.0))

    def zoom_out(self):
        if self._zoom_level <= 0:
            self._zoom_level = 1.0
        self.set_zoom(max(self._zoom_level / 1.3, 0.125))

    def zoom_fit(self):
        self.set_zoom(0.0)

    @property
    def current_zoom_pct(self) -> int:
        """当前缩放百分比(相对原图)"""
        if self._pixmap_original is None:
            return 100
        return int(self._scale_factor * 100)

    # ── 图片设置 ──
    def set_image(self, pixmap: QPixmap):
        self._pixmap_original = pixmap
        self._annotations = []
        self._pan_offset_x = 0
        self._pan_offset_y = 0
        self._update_display()

    def set_annotations(self, annotations: list):
        self._annotations = annotations
        self._update_display()

    def _update_display(self):
        if self._pixmap_original is None:
            return
        pw = self._pixmap_original.width()
        ph = self._pixmap_original.height()

        avail_w = self.width() - 4
        avail_h = self.height() - 4
        if avail_w <= 0 or avail_h <= 0:
            return

        # 自适应比率
        self._fit_scale = min(avail_w / pw, avail_h / ph)
        if self._zoom_level <= 0:
            self._scale_factor = self._fit_scale
        else:
            self._scale_factor = self._fit_scale * self._zoom_level

        # 缩放后原图尺寸
        new_w = max(1, int(pw * self._scale_factor))
        new_h = max(1, int(ph * self._scale_factor))

        # 限制平移范围(不能移出图片边界)
        self._pan_offset_x = max(0, min(self._pan_offset_x, max(0, new_w - avail_w)))
        self._pan_offset_y = max(0, min(self._pan_offset_y, max(0, new_h - avail_h)))

        # 缩放原图
        smooth = self._scale_factor < 3.0
        scaled = self._pixmap_original.scaled(
            new_w, new_h, Qt.KeepAspectRatio,
            Qt.SmoothTransformation if smooth else Qt.FastTransformation)

        # 画标注到缩放后的图上
        if self._annotations:
            painter = QPainter(scaled)
            painter.setRenderHint(QPainter.Antialiasing)
            font = QFont("Microsoft YaHei", 10)
            painter.setFont(font)
            for ann_x, ann_y, color_name, label in self._annotations:
                sx = int(ann_x * self._scale_factor)
                sy = int(ann_y * self._scale_factor)
                cr = 6
                if color_name == "found":
                    painter.setPen(QPen(QColor(0, 255, 0), 2))
                    painter.drawEllipse(sx - cr, sy - cr, cr * 2, cr * 2)
                    painter.drawLine(sx - 8, sy, sx + 8, sy)
                    painter.drawLine(sx, sy - 8, sx, sy + 8)
                elif color_name == "not_found":
                    painter.setPen(QPen(QColor(255, 0, 0), 2))
                    painter.drawLine(sx - 6, sy - 6, sx + 6, sy + 6)
                    painter.drawLine(sx + 6, sy - 6, sx - 6, sy + 6)
                elif color_name == "flash":
                    painter.setPen(QPen(QColor(255, 200, 0), 2))
                    painter.drawEllipse(sx - cr, sy - cr, cr * 2, cr * 2)
                    painter.drawLine(sx - 10, sy, sx + 10, sy)
                    painter.drawLine(sx, sy - 10, sx, sy + 10)
                if label:
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    painter.drawText(sx + cr + 3, sy + 4, str(label))
            painter.end()

        # 如果缩放后的图超出可视区 → 只显示可视部分(平移支持)
        if new_w > avail_w or new_h > avail_h:
            display = QPixmap(avail_w, avail_h)
            display.fill(QColor(34, 34, 34))
            dp = QPainter(display)
            dp.drawPixmap(-self._pan_offset_x, -self._pan_offset_y, scaled)
            dp.end()
            self.setPixmap(display)
        else:
            self.setPixmap(scaled)

        self._offset_x = -self._pan_offset_x
        self._offset_y = -self._pan_offset_y
        self.zoom_changed.emit(self._scale_factor)

    # ── 事件 ──
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()

    def wheelEvent(self, event):
        if self._pixmap_original is None:
            super().wheelEvent(event)
            return
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()
        # 中键拖拽平移
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = pos
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        # 左键取色/点击
        if event.button() == Qt.LeftButton and self._pixmap_original:
            if self._scale_factor > 0:
                orig_x = int((pos.x() - self._offset_x) / self._scale_factor)
                orig_y = int((pos.y() - self._offset_y) / self._scale_factor)
                orig_x = max(0, min(orig_x, self._pixmap_original.width() - 1))
                orig_y = max(0, min(orig_y, self._pixmap_original.height() - 1))
                self.clicked.emit(orig_x, orig_y)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        if self._panning:
            delta = pos - self._pan_start
            self._pan_offset_x -= int(delta.x())
            self._pan_offset_y -= int(delta.y())
            self._pan_start = pos
            self._update_display()
            event.accept()
            return
        if self._pixmap_original and self._scale_factor > 0:
            orig_x = int((pos.x() - self._offset_x) / self._scale_factor)
            orig_y = int((pos.y() - self._offset_y) / self._scale_factor)
            if 0 <= orig_x < self._pixmap_original.width() and 0 <= orig_y < self._pixmap_original.height():
                self.hovered.emit(orig_x, orig_y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CrossCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ColorPointTable(QTableWidget):
    """取色点列表表格"""
    points_deleted = Signal(list)

    COL_INDEX = 0
    COL_X = 1
    COL_Y = 2
    COL_COLOR = 3
    COL_HEX = 4
    COL_STATUS = 5
    COL_FOUND_XY = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            ["序号", "X", "Y", "RGB", "HEX", "验证", "匹配位置"])
        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_INDEX, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_X, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_Y, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_COLOR, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_HEX, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_FOUND_XY, QHeaderView.Stretch)
        self.setColumnWidth(self.COL_INDEX, 50)
        self.setColumnWidth(self.COL_X, 55)
        self.setColumnWidth(self.COL_Y, 55)
        self.setColumnWidth(self.COL_COLOR, 45)
        self.setColumnWidth(self.COL_HEX, 80)
        self.setColumnWidth(self.COL_STATUS, 50)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.verticalHeader().setVisible(False)

    def set_points(self, points):
        self.setRowCount(0)
        for p in points:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, self.COL_INDEX, QTableWidgetItem(str(p.index)))
            self.setItem(row, self.COL_X, QTableWidgetItem(str(p.x)))
            self.setItem(row, self.COL_Y, QTableWidgetItem(str(p.y)))
            color_item = QTableWidgetItem("  ")
            color_item.setBackground(QColor(*p.color_rgb))
            self.setItem(row, self.COL_COLOR, color_item)
            self.setItem(row, self.COL_HEX, QTableWidgetItem(p.hex_color))
            if p.found is True:
                status = QTableWidgetItem("✓ 找到")
                status.setForeground(COLOR_FOUND)
            elif p.found is False:
                status = QTableWidgetItem("✗ 未找到")
                status.setForeground(COLOR_NOT_FOUND)
            else:
                status = QTableWidgetItem("-")
                status.setForeground(COLOR_PENDING)
            self.setItem(row, self.COL_STATUS, status)
            if p.found is True:
                self.setItem(row, self.COL_FOUND_XY,
                              QTableWidgetItem(f"({p.found_x}, {p.found_y})"))
            else:
                self.setItem(row, self.COL_FOUND_XY, QTableWidgetItem(""))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            rows = set()
            for item in self.selectedItems():
                rows.add(item.row())
            if rows:
                indices = [int(self.item(r, self.COL_INDEX).text()) for r in rows]
                self.points_deleted.emit(indices)
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("窗口辅助工具 v1.0 - 取色 · 验证 · 坐标")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self.binder = WindowBinder(self)
        self.capture = ScreenCapture(self)
        self.picker = ColorPicker(self)
        self.verifier = ColorVerifier(self)
        self.tracker = CoordinateTracker(self)
        self.matcher = TemplateMatcher(threshold=0.75, max_results=20)
        self._saved_coords = []  # 右键保存的坐标列表 [(x, y), ...]
        self._template_image = None  # PIL Image: 当前选取的模板
        self._template_region_start = None  # (x, y): 模板选取起点
        self._custom_screenshot_start = None  # (x, y): 区域截图框选起点
        self.adb_scanner = AdbScanner(self)
        self._adb_serial = None  # ADB 绑定的设备序列号

        self._setup_ui()
        self._setup_connections()
        self._setup_menus()

        QTimer.singleShot(300, self.binder.enumerate_windows)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── 窗口绑定区域 (紧凑) ──
        bind_group = QGroupBox("窗口绑定")
        bind_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bind_layout = QHBoxLayout(bind_group)
        bind_layout.setContentsMargins(8, 10, 8, 10)

        self._btn_refresh = QPushButton("🔄 刷新列表")
        self._combo_windows = QComboBox()
        self._combo_windows.setMinimumWidth(320)
        self._combo_windows.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn_pick = QPushButton("🎯 点选窗口")
        self._btn_bind = QPushButton("绑定")
        self._btn_bind.setObjectName("btnPrimary")
        self._btn_unbind = QPushButton("解绑")
        self._btn_unbind.setObjectName("btnDanger")
        self._btn_unbind.setEnabled(False)
        self._lbl_bound_info = QLabel("未绑定窗口")
        self._lbl_bound_info.setStyleSheet("color: #888; padding: 0 8px;")
        self._btn_enum_children = QPushButton("子窗口")
        self._btn_enum_children.setToolTip("枚举选中窗口的子窗口")
        self._btn_adb = QPushButton("绑定设备")
        self._btn_adb.setToolTip("扫描 ADB 连接的 Android 设备")

        bind_layout.addWidget(self._btn_refresh)
        bind_layout.addWidget(self._combo_windows)
        bind_layout.addWidget(self._btn_pick)
        bind_layout.addWidget(self._btn_enum_children)
        bind_layout.addWidget(self._btn_adb)
        bind_layout.addWidget(self._btn_bind)
        bind_layout.addWidget(self._btn_unbind)
        bind_layout.addWidget(self._lbl_bound_info)
        bind_layout.addStretch()
        main_layout.addWidget(bind_group)

        # ── 主体分割区域 ──
        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._screenshot_label = ClickableLabel()
        self._screenshot_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 截图工具栏：操作 + 缩放 + 坐标显示
        ss_bar = QHBoxLayout()
        self._btn_full_ss = QPushButton("📷 完整截图")
        self._btn_full_ss.setObjectName("btnPrimary")
        self._btn_custom_ss = QPushButton("✂ 区域截图")
        self._btn_custom_ss.setCheckable(True)
        self._btn_custom_ss.setToolTip("激活后在截图上框选区域，裁剪为新的截图")
        self._btn_save_ss = QPushButton("💾 保存")
        self._cb_client_area = QCheckBox("客户区")
        self._cb_client_area.setChecked(True)
        self._cb_client_area.setToolTip("仅截取客户区（不含标题栏）")

        ss_bar.addWidget(self._btn_full_ss)
        ss_bar.addWidget(self._btn_custom_ss)
        ss_bar.addWidget(self._btn_save_ss)
        ss_bar.addWidget(self._cb_client_area)

        # 缩放控件
        ss_bar.addSpacing(12)
        self._btn_zoom_out = QPushButton("🔍-")
        self._btn_zoom_out.setFixedWidth(36)
        self._btn_zoom_out.setToolTip("缩小 (滚轮下滚)")
        self._lbl_zoom = QLabel("100%")
        self._lbl_zoom.setFixedWidth(45)
        self._lbl_zoom.setAlignment(Qt.AlignCenter)
        self._lbl_zoom.setStyleSheet("font-weight: bold; color: #4a9eff;")
        self._btn_zoom_in = QPushButton("🔍+")
        self._btn_zoom_in.setFixedWidth(36)
        self._btn_zoom_in.setToolTip("放大 (滚轮上滚)")
        self._btn_zoom_fit = QPushButton("📐 适合")
        self._btn_zoom_fit.setToolTip("自适应窗口大小")
        ss_bar.addWidget(self._btn_zoom_out)
        ss_bar.addWidget(self._lbl_zoom)
        ss_bar.addWidget(self._btn_zoom_in)
        ss_bar.addWidget(self._btn_zoom_fit)

        # 悬停坐标显示
        ss_bar.addSpacing(12)
        self._lbl_hover_coord = QLabel("截图坐标: --")
        self._lbl_hover_coord.setStyleSheet("color: #aaa; font-size: 11px; padding: 0 6px;")
        ss_bar.addWidget(self._lbl_hover_coord)

        # 截图点击 → 窗口真实点击 开关
        self._cb_click_through = QCheckBox("截图↦窗口点击")
        self._cb_click_through.setToolTip(
            "勾选后：在截图上左键 = 对真实窗口的对应位置执行单击\n"
            "不勾选：在截图上左键 = 取色")
        ss_bar.addWidget(self._cb_click_through)
        ss_bar.addStretch()
        left_layout.addLayout(ss_bar)
        left_layout.addWidget(self._screenshot_label)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(3)

        self._tab_widget = QTabWidget()

        # ═══ 共享日志（每个标签页底部的迷你日志，始终可见）═══
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(90)
        self._log_text.setFont(QFont("Consolas", 9))
        self._log_text.setPlaceholderText("操作日志将显示在此处...")

        # ═══ 页签 1: 坐标工具 ═══
        tab_coord = QWidget()
        tab_coord_layout = QVBoxLayout(tab_coord)
        tab_coord_layout.setContentsMargins(6, 8, 6, 6)
        tab_coord_layout.setSpacing(6)

        # 坐标信息
        coord_group = QGroupBox("坐标信息")
        coord_layout = QVBoxLayout(coord_group)
        coord_row1 = QHBoxLayout()
        self._lbl_coord = QLabel("实时坐标: (--, --)")
        self._lbl_coord.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #4a9eff; padding: 4px;")
        self._lbl_click = QLabel("最后点击: (--, --)")
        self._lbl_click.setStyleSheet("padding: 4px;")
        coord_row1.addWidget(self._lbl_coord)
        coord_row1.addStretch()
        coord_row1.addWidget(self._lbl_click)
        coord_row2 = QHBoxLayout()
        self._btn_track = QPushButton("▶ 开始追踪")
        self._btn_track.setCheckable(True)
        self._btn_copy_coord = QPushButton("复制坐标")
        self._cb_right_click_save = QCheckBox("右键保存坐标")
        self._cb_right_click_save.setToolTip("追踪时在绑定窗口上右键自动保存坐标")
        coord_row2.addWidget(self._btn_track)
        coord_row2.addWidget(self._btn_copy_coord)
        coord_row2.addWidget(self._cb_right_click_save)
        coord_row2.addStretch()
        coord_layout.addLayout(coord_row1)
        coord_layout.addLayout(coord_row2)
        tab_coord_layout.addWidget(coord_group)

        # 已保存坐标
        saved_coords_group = QGroupBox("已保存坐标")
        saved_coords_layout = QVBoxLayout(saved_coords_group)
        saved_btns = QHBoxLayout()
        self._btn_clear_coords = QPushButton("清空列表")
        self._btn_copy_saved = QPushButton("复制全部")
        self._btn_paste_coords = QPushButton("📋 粘贴坐标")
        self._btn_paste_coords.setObjectName("btnSuccess")
        saved_btns.addWidget(self._btn_clear_coords)
        saved_btns.addWidget(self._btn_copy_saved)
        saved_btns.addWidget(self._btn_paste_coords)
        saved_btns.addStretch()
        self._saved_coords_text = QTextEdit()
        self._saved_coords_text.setReadOnly(True)
        self._saved_coords_text.setMaximumHeight(70)
        self._saved_coords_text.setPlaceholderText("右键保存的坐标将显示在此处...")
        self._saved_coords_text.setFont(QFont("Consolas", 9))
        saved_coords_layout.addLayout(saved_btns)
        saved_coords_layout.addWidget(self._saved_coords_text)
        tab_coord_layout.addWidget(saved_coords_group)

        # 测试点击
        test_click_group = QGroupBox("测试点击")
        test_click_layout = QVBoxLayout(test_click_group)
        test_input_row = QHBoxLayout()
        self._edit_test_coords = QTextEdit()
        self._edit_test_coords.setPlaceholderText("粘贴坐标，格式: (x, y)\n或每行一个: 100 200")
        self._edit_test_coords.setMaximumHeight(50)
        self._edit_test_coords.setFont(QFont("Consolas", 9))
        test_input_row.addWidget(self._edit_test_coords)
        test_btn_row = QHBoxLayout()
        self._btn_test_click = QPushButton("🖱 单点测试")
        self._btn_test_click.setObjectName("btnPrimary")
        self._btn_test_click.setToolTip("对输入坐标依次执行单击")
        self._btn_test_dblclick = QPushButton("🖱🖱 双击测试")
        self._btn_test_dblclick.setToolTip("对输入坐标依次执行双击")
        test_btn_row.addWidget(self._btn_test_click)
        test_btn_row.addWidget(self._btn_test_dblclick)
        test_btn_row.addStretch()
        test_click_layout.addLayout(test_input_row)
        test_click_layout.addLayout(test_btn_row)
        tab_coord_layout.addWidget(test_click_group)

        # ── 坐标标签页迷你日志 ──
        coord_log = QTextEdit()
        coord_log.setReadOnly(True)
        coord_log.setMaximumHeight(70)
        coord_log.setFont(QFont("Consolas", 8))
        coord_log.setPlaceholderText("📍 坐标工具日志...")
        coord_log.setObjectName("coordLog")
        tab_coord_layout.addWidget(coord_log)

        self._tab_widget.addTab(tab_coord, "📍 坐标工具")

        # ═══ 页签 2: 取色验证 ═══
        tab_color = QWidget()
        tab_color_layout = QVBoxLayout(tab_color)
        tab_color_layout.setContentsMargins(6, 8, 6, 6)
        tab_color_layout.setSpacing(6)

        # 取色点列表
        points_group = QGroupBox("取色点列表")
        points_layout = QVBoxLayout(points_group)
        self._table_points = ColorPointTable()
        points_btns = QHBoxLayout()
        self._btn_delete_pt = QPushButton("删除选中")
        self._btn_clear_pt = QPushButton("清空全部")
        self._btn_copy_json = QPushButton("复制 JSON")
        self._btn_copy_csv = QPushButton("复制 CSV")
        self._btn_paste = QPushButton("📋 粘贴导入")
        self._btn_paste.setObjectName("btnSuccess")
        points_btns.addWidget(self._btn_delete_pt)
        points_btns.addWidget(self._btn_clear_pt)
        points_btns.addWidget(self._btn_copy_json)
        points_btns.addWidget(self._btn_copy_csv)
        points_btns.addWidget(self._btn_paste)
        points_layout.addWidget(self._table_points)
        points_layout.addLayout(points_btns)
        tab_color_layout.addWidget(points_group)

        # 颜色验证
        verify_group = QGroupBox("颜色验证")
        verify_layout = QVBoxLayout(verify_group)
        verify_row1 = QHBoxLayout()
        verify_row1.addWidget(QLabel("容差:"))
        self._spin_tolerance = QSpinBox()
        self._spin_tolerance.setRange(0, 100)
        self._spin_tolerance.setValue(5)
        self._spin_tolerance.setToolTip("颜色匹配容差 (0-255)")
        verify_row1.addWidget(self._spin_tolerance)
        verify_row1.addWidget(QLabel("搜索范围:"))
        self._spin_scope = QSpinBox()
        self._spin_scope.setRange(0, 200)
        self._spin_scope.setValue(15)
        self._spin_scope.setToolTip("在原始坐标周围 ±N 像素范围内搜索")
        verify_row1.addWidget(self._spin_scope)
        verify_row1.addStretch()
        verify_row2 = QHBoxLayout()
        self._btn_verify = QPushButton("🔍 开始验证")
        self._btn_verify.setObjectName("btnPrimary")
        self._btn_verify.setMinimumHeight(32)
        self._lbl_verify_result = QLabel("")
        self._lbl_verify_result.setStyleSheet("padding: 0 8px;")
        verify_row2.addWidget(self._btn_verify)
        verify_row2.addWidget(self._lbl_verify_result)
        verify_row2.addStretch()
        verify_layout.addLayout(verify_row1)
        verify_layout.addLayout(verify_row2)
        tab_color_layout.addWidget(verify_group)

        # ── 取色标签页迷你日志 ──
        color_log = QTextEdit()
        color_log.setReadOnly(True)
        color_log.setMaximumHeight(70)
        color_log.setFont(QFont("Consolas", 8))
        color_log.setPlaceholderText("🎨 取色验证日志...")
        color_log.setObjectName("colorLog")
        tab_color_layout.addWidget(color_log)

        self._tab_widget.addTab(tab_color, "🎨 取色验证")

        # ═══ 页签 3: 图片定位 ═══
        tab_match = QWidget()
        tab_match_layout = QVBoxLayout(tab_match)
        tab_match_layout.setContentsMargins(6, 8, 6, 6)
        tab_match_layout.setSpacing(6)

        # 模板选取
        tmpl_group = QGroupBox("模板选取")
        tmpl_layout = QVBoxLayout(tmpl_group)
        tmpl_row = QHBoxLayout()
        self._btn_pick_template = QPushButton("🎯 截图选模板")
        self._btn_pick_template.setCheckable(True)
        self._btn_pick_template.setToolTip(
            "激活后在截图上点击两个点来框选模板区域")
        self._btn_paste_template = QPushButton("📋 粘贴模板")
        self._btn_paste_template.setToolTip(
            "从剪贴板粘贴图片作为模板（QQ/微信截图后 Ctrl+C，再点此按钮）")
        self._btn_load_template = QPushButton("📁 加载图片")
        self._btn_clear_template = QPushButton("清空")
        self._lbl_template_hint = QLabel("未选取模板")
        self._lbl_template_hint.setStyleSheet("color: #888;")
        self._lbl_template_preview = QLabel()
        self._lbl_template_preview.setFixedSize(100, 80)
        self._lbl_template_preview.setAlignment(Qt.AlignCenter)
        self._lbl_template_preview.setStyleSheet(
            "background-color: #222; border: 1px solid #555;")
        tmpl_row.addWidget(self._btn_pick_template)
        tmpl_row.addWidget(self._btn_paste_template)
        tmpl_row.addWidget(self._btn_load_template)
        tmpl_row.addWidget(self._btn_clear_template)
        tmpl_row.addWidget(self._lbl_template_hint)
        tmpl_row.addWidget(self._lbl_template_preview)
        tmpl_row.addStretch()
        tmpl_layout.addLayout(tmpl_row)
        tab_match_layout.addWidget(tmpl_group)

        # 匹配设置
        match_settings = QGroupBox("匹配设置")
        ms_layout = QVBoxLayout(match_settings)
        ms_row = QHBoxLayout()
        ms_row.addWidget(QLabel("相似度阈值:"))
        self._spin_match_thresh = QSpinBox()
        self._spin_match_thresh.setRange(50, 99)
        self._spin_match_thresh.setValue(75)
        self._spin_match_thresh.setSuffix("%")
        self._spin_match_thresh.setToolTip("越高越严格，仅匹配相似度高的位置")
        self._spin_match_thresh.setFixedWidth(80)
        ms_row.addWidget(self._spin_match_thresh)
        ms_row.addSpacing(16)
        ms_row.addWidget(QLabel("最大结果:"))
        self._spin_max_results = QSpinBox()
        self._spin_max_results.setRange(1, 50)
        self._spin_max_results.setValue(20)
        self._spin_max_results.setFixedWidth(60)
        ms_row.addWidget(self._spin_max_results)
        ms_row.addStretch()
        ms_layout.addLayout(ms_row)
        tab_match_layout.addWidget(match_settings)

        # 执行匹配
        match_act = QHBoxLayout()
        self._btn_match = QPushButton("🔍 查找模板")
        self._btn_match.setObjectName("btnPrimary")
        self._btn_match.setMinimumHeight(32)
        self._btn_match.setEnabled(False)
        self._lbl_match_status = QLabel("")
        self._lbl_match_status.setStyleSheet("padding: 0 8px;")
        match_act.addWidget(self._btn_match)
        match_act.addWidget(self._lbl_match_status)
        match_act.addStretch()
        tab_match_layout.addLayout(match_act)

        # 结果表格
        result_group = QGroupBox("匹配结果")
        result_layout = QVBoxLayout(result_group)
        self._table_matches = QTableWidget()
        self._table_matches.setColumnCount(5)
        self._table_matches.setHorizontalHeaderLabels(
            ["#", "X", "Y", "中心坐标", "相似度"])
        mh = self._table_matches.horizontalHeader()
        mh.setSectionResizeMode(0, QHeaderView.Fixed)
        mh.setSectionResizeMode(1, QHeaderView.Fixed)
        mh.setSectionResizeMode(2, QHeaderView.Fixed)
        mh.setSectionResizeMode(3, QHeaderView.Stretch)
        mh.setSectionResizeMode(4, QHeaderView.Fixed)
        self._table_matches.setColumnWidth(0, 35)
        self._table_matches.setColumnWidth(1, 55)
        self._table_matches.setColumnWidth(2, 55)
        self._table_matches.setColumnWidth(4, 60)
        self._table_matches.setSelectionBehavior(QTableWidget.SelectRows)
        self._table_matches.setAlternatingRowColors(True)
        self._table_matches.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_matches.verticalHeader().setVisible(False)
        result_btns = QHBoxLayout()
        self._btn_click_match = QPushButton("🖱 点击选中位置")
        self._btn_click_match.setToolTip("对选中结果的位置执行窗口点击")
        self._btn_copy_match = QPushButton("复制全部坐标")
        self._btn_clear_matches = QPushButton("清空结果")
        result_btns.addWidget(self._btn_click_match)
        result_btns.addWidget(self._btn_copy_match)
        result_btns.addWidget(self._btn_clear_matches)
        result_btns.addStretch()
        result_layout.addWidget(self._table_matches)
        result_layout.addLayout(result_btns)
        tab_match_layout.addWidget(result_group)

        # ── 图片定位迷你日志 ──
        match_log = QTextEdit()
        match_log.setReadOnly(True)
        match_log.setMaximumHeight(70)
        match_log.setFont(QFont("Consolas", 8))
        match_log.setPlaceholderText("🔍 图片定位日志...")
        match_log.setObjectName("matchLog")
        tab_match_layout.addWidget(match_log)

        self._tab_widget.addTab(tab_match, "🔍 图片定位")

        right_layout.addWidget(self._tab_widget)
        right_layout.addWidget(self._log_text)

        # 保存引用以便 _log 写入
        self._coord_log = coord_log
        self._color_log = color_log
        self._match_log = match_log

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("就绪")
        self._status_bar.addWidget(self._status_label)

    def _setup_connections(self):
        self._btn_refresh.clicked.connect(self._on_refresh_windows)
        self._btn_bind.clicked.connect(self._on_bind_window)
        self._btn_unbind.clicked.connect(self._on_unbind_window)
        self._btn_pick.clicked.connect(self._on_pick_window)
        self._btn_enum_children.clicked.connect(self._on_enum_children)
        self._btn_adb.clicked.connect(self._on_scan_adb_devices)
        self.adb_scanner.devices_found.connect(self._on_adb_devices_found)

        self.binder.window_list_updated.connect(self._on_window_list)
        self.binder.window_bound.connect(self._on_bound)
        self.binder.window_unbound.connect(self._on_unbound)
        self.binder.status_message.connect(self._log)

        self._btn_full_ss.clicked.connect(self._on_full_screenshot)
        self._btn_custom_ss.toggled.connect(self._on_toggle_custom_screenshot)
        self._btn_save_ss.clicked.connect(self._on_save_screenshot)
        self.capture.screenshot_taken.connect(self._on_screenshot)
        self.capture.screenshot_error.connect(self._log)

        # 缩放
        self._btn_zoom_in.clicked.connect(self._screenshot_label.zoom_in)
        self._btn_zoom_out.clicked.connect(self._screenshot_label.zoom_out)
        self._btn_zoom_fit.clicked.connect(self._screenshot_label.zoom_fit)
        self._screenshot_label.zoom_changed.connect(self._on_zoom_changed)
        self._screenshot_label.hovered.connect(self._on_screenshot_hovered)

        self._screenshot_label.clicked.connect(self._on_screenshot_clicked)
        self._btn_delete_pt.clicked.connect(self._on_delete_points)
        self._btn_clear_pt.clicked.connect(self._on_clear_points)
        self._btn_copy_json.clicked.connect(lambda: self._copy_points("json"))
        self._btn_copy_csv.clicked.connect(lambda: self._copy_points("csv"))
        self._btn_paste.clicked.connect(self._on_paste_points)
        self.picker.list_changed.connect(self._update_points_table)

        self._btn_verify.clicked.connect(self._on_verify)
        self._spin_tolerance.valueChanged.connect(
            lambda v: setattr(self.verifier, 'tolerance', v))
        self._spin_scope.valueChanged.connect(
            lambda v: setattr(self.verifier, 'search_scope', v))
        self.verifier.verification_done.connect(self._on_verify_done)
        self.verifier.verification_error.connect(self._log)

        self._btn_track.toggled.connect(self._on_toggle_tracking)
        self._btn_copy_coord.clicked.connect(self._on_copy_coord)
        self._cb_right_click_save.toggled.connect(self.tracker.set_right_click_enabled)
        self.tracker.mouse_position.connect(self._on_mouse_pos)
        self.tracker.right_click_captured.connect(self._on_right_click_save)
        self.tracker.status_message.connect(self._log)

        self._btn_clear_coords.clicked.connect(self._on_clear_saved_coords)
        self._btn_copy_saved.clicked.connect(self._on_copy_saved_coords)
        self._btn_paste_coords.clicked.connect(self._on_paste_saved_coords)
        self._btn_test_click.clicked.connect(lambda: self._on_test_click(False))
        self._btn_test_dblclick.clicked.connect(lambda: self._on_test_click(True))

        self._table_points.points_deleted.connect(
            lambda indices: self.picker.remove_selected(indices))

        # 图片定位
        self._btn_pick_template.toggled.connect(self._on_toggle_template_pick)
        self._btn_paste_template.clicked.connect(self._on_paste_template)
        self._btn_load_template.clicked.connect(self._on_load_template)
        self._btn_clear_template.clicked.connect(self._on_clear_template)
        self._btn_match.clicked.connect(self._on_match_template)
        self._btn_click_match.clicked.connect(self._on_click_match_result)
        self._btn_copy_match.clicked.connect(self._on_copy_match_results)
        self._btn_clear_matches.clicked.connect(self._on_clear_match_results)
        self._spin_match_thresh.valueChanged.connect(self._on_match_thresh_changed)
        self._spin_max_results.valueChanged.connect(self._on_max_results_changed)

    def _setup_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件(&F)")
        act_save_ss = QAction("保存截图...", self)
        act_save_ss.triggered.connect(self._on_save_screenshot)
        file_menu.addAction(act_save_ss)
        act_export = QAction("导出取色数据...", self)
        act_export.triggered.connect(self._on_export_data)
        file_menu.addAction(act_export)
        file_menu.addSeparator()
        act_exit = QAction("退出", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        view_menu = menubar.addMenu("视图(&V)")
        act_dark = QAction("深色主题", self, checkable=True, checked=True)
        act_dark.triggered.connect(
            lambda checked: self.setStyleSheet(STYLE_DARK if checked else ""))
        view_menu.addAction(act_dark)

        help_menu = menubar.addMenu("帮助(&H)")
        act_about = QAction("关于...", self)
        act_about.triggered.connect(lambda: QMessageBox.about(
            self, "关于",
            "窗口辅助工具 v1.0\n\n"
            "功能：窗口绑定 · 灵活截图 · 多点取色 · 颜色验证 · 坐标定位\n\n"
            "基于 PySide6 构建"))
        help_menu.addAction(act_about)

    # ═══ 窗口绑定 ═══

    def _on_refresh_windows(self):
        self._log("正在枚举窗口...")
        self.binder.enumerate_windows()

    def _on_window_list(self, windows):
        self._combo_windows.clear()
        target_kw = ["效卫", "投屏", "手机", "镜像"]
        sorted_wins = sorted(windows,
            key=lambda w: (
                not any(k in w.title or k in w.class_name for k in target_kw),
                w.title))
        for w in sorted_wins:
            self._combo_windows.addItem(w.display_name, w.hwnd)
        self._log(f"枚举到 {len(windows)} 个可见窗口")

    def _on_bind_window(self):
        idx = self._combo_windows.currentIndex()
        if idx < 0:
            return
        hwnd = self._combo_windows.currentData()
        self.binder.bind_window(hwnd)

    def _on_pick_window(self):
        self._log("点选模式：请在 3 秒内点击目标窗口...")
        self.hide()
        QTimer.singleShot(300, self._do_pick_window)

    def _do_pick_window(self):
        QTimer.singleShot(2000, self._pick_callback)

    def _pick_callback(self):
        try:
            hwnd = get_window_under_cursor()
            if hwnd:
                self.show()
                self.binder.bind_window(hwnd)
        except Exception as e:
            self.show()
            self._log(f"点选失败: {e}")

    def _on_enum_children(self):
        idx = self._combo_windows.currentIndex()
        if idx < 0:
            self._log("请先在列表中选择一个父窗口")
            return
        hwnd = self._combo_windows.currentData()
        children = self.binder.enumerate_child_windows(hwnd)
        if children:
            menu = QMenu(self)
            for c in children:
                action = menu.addAction(c.display_name)
                action.setData(c.hwnd)
            action = menu.exec(QCursor.pos())
            if action:
                self.binder.bind_window(action.data())
        else:
            self._log("未找到符合条件的子窗口")

    def _on_bound(self, winfo):
        self._btn_bind.setEnabled(False)
        self._btn_unbind.setEnabled(True)
        self._lbl_bound_info.setText(
            f"已绑定: {winfo.title[:40]} | {winfo.class_name} | {winfo.width}x{winfo.height}")
        self._lbl_bound_info.setStyleSheet(
            "color: #4a9eff; padding: 0 8px; font-weight: bold;")
        self.tracker.set_target(winfo.hwnd)
        self._log(f"窗口绑定成功: {winfo.title}")

    def _on_unbound(self):
        self._btn_bind.setEnabled(True)
        self._btn_unbind.setEnabled(False)
        self._lbl_bound_info.setText("未绑定窗口")
        self._lbl_bound_info.setStyleSheet("color: #888; padding: 0 8px;")
        self.tracker.stop_tracking()
        self._btn_track.setChecked(False)

    def _on_unbind_window(self):
        self.binder.unbind_window()

    # ═══ 截图 ═══

    def _on_full_screenshot(self):
        # ADB 设备截图优先（直接走 adb screencap）
        if self._adb_serial:
            self._log(f"正在通过 ADB 截取设备 {self._adb_serial} 画面...")
            try:
                from adbutils import adb
                from io import BytesIO
                from PIL import Image
                d = adb.device(self._adb_serial)
                data = d.screenshot()  # PIL Image
                if data:
                    self.capture._cached_image = data
                    self.capture.screenshot_taken.emit(data)
                    return
                else:
                    self._log("ADB 截图返回空，回退到窗口截图")
            except Exception as e:
                self._log(f"ADB 截图失败: {e}，回退到窗口截图")
        # 窗口截图
        if not self.binder.is_bound:
            self._log("请先绑定目标窗口")
            QMessageBox.warning(self, "提示", "请先绑定目标窗口")
            return
        self._log("正在截取窗口...")
        img = self.capture.capture_window(
            self.binder.target_window.hwnd,
            client_area=self._cb_client_area.isChecked())
        if img:
            self.capture.screenshot_taken.emit(img)
        else:
            self._log("截图失败！尝试全屏截图...")
            img = ScreenCapture.capture_region()
            if img:
                self.capture.screenshot_taken.emit(img)

    def _on_screenshot(self, img):
        # 使用 PNG 编码/解码，避免 raw bytes 格式不匹配导致变形
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg)
        self._screenshot_label.set_image(pixmap)
        self._log(f"截图成功: {img.width}x{img.height}")

    def _on_save_screenshot(self):
        img = self.capture.cached_image
        if img is None:
            QMessageBox.warning(self, "提示", "没有可保存的截图")
            return

        from datetime import datetime
        default_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filters = "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;所有文件 (*.*)"
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self, "保存截图", default_name, filters)
        if not filepath:
            return  # 用户取消

        # 根据扩展名或过滤器确定格式
        ext = os.path.splitext(filepath)[1].lower()
        fmt_map = {".jpg": "JPEG", ".jpeg": "JPEG", ".bmp": "BMP", ".png": "PNG"}
        save_format = fmt_map.get(ext, "PNG")

        try:
            img.save(filepath, save_format)
            self._log("截图已保存: " + filepath)
        except Exception as e:
            QMessageBox.warning(self, "保存失败", "保存截图失败:\n" + str(e))

    def _on_zoom_changed(self, factor: float):
        pct = int(factor * 100)
        self._lbl_zoom.setText(f"{pct}%")

    def _on_screenshot_hovered(self, x: int, y: int):
        """鼠标在截图上悬停 → 显示图片坐标 + 窗口坐标"""
        self._lbl_hover_coord.setText(f"截图坐标: ({x}, {y})")

    def _on_screenshot_clicked(self, x: int, y: int):
        """截图点击处理: 区域截图 > 模板选取 > 穿透窗口点击 > 取色"""
        # 区域截图模式
        if self._btn_custom_ss.isChecked():
            self._on_custom_screenshot_click(x, y)
            return
        # 模板选取模式
        if self._btn_pick_template.isChecked():
            self._on_template_pick_click(x, y)
            return

        if self._cb_click_through.isChecked() and self.binder.is_bound:
            # 截图坐标 = 窗口相对坐标 (客户区模式)
            self.tracker.test_click(x, y, double_click=False)
            self._log(f"截图↦窗口点击: ({x}, {y})")
            self._lbl_click.setText(f"最后点击: ({x}, {y})")
        else:
            # 取色流程
            self._on_pick_color(x, y)

    # ═══ 取色 ═══

    def _on_pick_color(self, x, y):
        img = self.capture.cached_image
        if img is None:
            self._log("请先截图")
            return
        point = self.picker.pick_color(x, y, img)
        if point:
            self._log(f"取色: ({x},{y}) RGB{point.rgb_str} {point.hex_color}")
            self._lbl_click.setText(f"最后点击: ({x}, {y})")
        else:
            self._log(f"取色失败: 坐标 ({x},{y}) 超出图片范围")

    def _update_points_table(self):
        self._table_points.set_points(self.picker.get_points())

    def _on_delete_points(self):
        rows = set()
        for item in self._table_points.selectedItems():
            rows.add(item.row())
        if rows:
            indices = [int(self._table_points.item(r, 0).text()) for r in rows]
            self.picker.remove_selected(indices)

    def _on_clear_points(self):
        if self.picker.count() == 0:
            return
        reply = QMessageBox.question(
            self, "确认", f"确定要清空全部 {self.picker.count()} 个取色点吗？",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.picker.clear_all()
            self._log("已清空全部取色点")

    def _copy_points(self, fmt):
        if self.picker.count() == 0:
            QMessageBox.information(self, "提示", "没有取色数据")
            return
        text = self.picker.to_json() if fmt == "json" else self.picker.to_csv()
        QApplication.clipboard().setText(text)
        self._log(f"已复制 {self.picker.count()} 个取色点 ({fmt.upper()})")

    def _on_paste_points(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text.strip():
            self._log("剪贴板为空")
            return
        points = self.picker.parse_from_clipboard(text)
        self._log(f"粘贴导入 {len(points)} 个取色点")
        if len(points) > 0 and self.binder.is_bound:
            self._log("自动触发验证...")
            QTimer.singleShot(500, self._on_verify)

    def _on_export_data(self):
        if self.picker.count() == 0:
            QMessageBox.information(self, "提示", "没有取色数据")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出取色数据", "color_data.json",
            "JSON (*.json);;CSV (*.csv);;所有文件 (*.*)")
        if path:
            ext = os.path.splitext(path)[1].lower()
            text = self.picker.to_csv() if ext == ".csv" else self.picker.to_json()
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._log(f"数据导出到: {path}")

    # ═══ 颜色验证 ═══

    def _on_verify(self):
        if self.picker.count() == 0:
            self._log("没有取色点，无法验证")
            return
        if not self.binder.is_bound:
            self._log("请先绑定目标窗口")
            return
        self._log("正在截图以进行颜色验证...")
        img = self.capture.capture_window(
            self.binder.target_window.hwnd,
            client_area=self._cb_client_area.isChecked())
        if img is None:
            self._log("截图失败，无法验证")
            return
        self._on_screenshot(img)
        self._lbl_verify_result.setText("验证中...")
        self._btn_verify.setEnabled(False)
        self.verifier.verify_async(img, self.picker.get_points())

    def _on_verify_done(self, results, annotated):
        self._btn_verify.setEnabled(True)
        found_count = sum(1 for r in results if r["found"])
        total = len(results)
        self._lbl_verify_result.setText(
            f"结果: {found_count}/{total} 匹配 "
            f"(容差={self.verifier.tolerance} 范围=±{self.verifier.search_scope})")
        color = "#4aff4a" if found_count == total else "#ffaa44" if found_count > 0 else "#ff4444"
        self._lbl_verify_result.setStyleSheet(
            f"color: {color}; padding: 0 8px; font-weight: bold;")
        self.picker.update_verification_results(results)

        annotations = []
        for r in results:
            if r["found"]:
                annotations.append((r["found_x"], r["found_y"], "found", str(r["index"])))
            else:
                annotations.append((r["original_x"], r["original_y"], "not_found", str(r["index"])))
        self._screenshot_label.set_annotations(annotations)
        self._update_annotation_display(annotated)
        filepath = self.verifier.save_and_open(annotated)
        self._log(f"验证完成: {found_count}/{total} 匹配 → {os.path.basename(filepath)}")

    def _update_annotation_display(self, annotated):
        if annotated.mode == "RGBA":
            qimg = QImage(annotated.tobytes("raw", "RGBA"),
                           annotated.width, annotated.height, QImage.Format_RGBA8888)
        else:
            qimg = QImage(annotated.tobytes("raw", "RGB"),
                           annotated.width, annotated.height, QImage.Format_RGB888)
        self._screenshot_label.set_image(QPixmap.fromImage(qimg))

    # ═══ 坐标追踪 ═══

    def _on_toggle_tracking(self, checked):
        if checked:
            if not self.binder.is_bound:
                self._btn_track.setChecked(False)
                QMessageBox.warning(self, "提示", "请先绑定目标窗口")
                return
            self.tracker.start_tracking()
            self._btn_track.setText("⏸ 停止追踪")
        else:
            self.tracker.stop_tracking()
            self._btn_track.setText("▶ 开始追踪")

    def _on_mouse_pos(self, x, y):
        self._lbl_coord.setText(f"实时坐标: ({x}, {y})")

    def _on_copy_coord(self):
        import re
        text = self._lbl_coord.text()
        match = re.search(r'\(.*?\)', text)
        if match:
            QApplication.clipboard().setText(match.group(0))
            self._log(f"已复制坐标: {match.group(0)}")

    def _on_right_click_save(self, x, y):
        """追踪时右键点击保存坐标，同时在截图上标记位置"""
        self._saved_coords.append((x, y))
        idx = len(self._saved_coords)
        self._update_saved_coords_display()
        self._log(f"右键保存坐标: ({x}, {y})  共 {idx} 个")

        # 在截图预览上闪烁标记，方便确认坐标位置是否准确
        annotations = list(self._screenshot_label._annotations)
        flash_marker = (x, y, "flash", str(idx))
        annotations.append(flash_marker)
        self._screenshot_label.set_annotations(annotations)
        # 1.5 秒后清除闪烁标记
        QTimer.singleShot(1500, lambda: self._clear_flash_marker(flash_marker))

    def _clear_flash_marker(self, marker):
        """清除单个闪烁标记"""
        if marker in self._screenshot_label._annotations:
            new_annotations = [a for a in self._screenshot_label._annotations if a != marker]
            self._screenshot_label.set_annotations(new_annotations)

    def _on_clear_saved_coords(self):
        if not self._saved_coords:
            return
        reply = QMessageBox.question(
            self, "确认", f"确定清空 {len(self._saved_coords)} 个已保存坐标？",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._saved_coords.clear()
            self._update_saved_coords_display()
            self._log("已清空所有保存坐标")

    def _on_copy_saved_coords(self):
        if not self._saved_coords:
            QMessageBox.information(self, "提示", "没有保存的坐标")
            return
        lines = [f"({x}, {y})" for x, y in self._saved_coords]
        QApplication.clipboard().setText("\n".join(lines))
        self._log(f"已复制 {len(self._saved_coords)} 个坐标到剪贴板")

    def _on_paste_saved_coords(self):
        text = QApplication.clipboard().text()
        if text.strip():
            self._edit_test_coords.setPlainText(text)
            self._log(f"已粘贴坐标到测试区")
        else:
            self._log("剪贴板为空")

    def _update_saved_coords_display(self):
        lines = []
        for i, (x, y) in enumerate(self._saved_coords, 1):
            lines.append(f"#{i:02d}  ({x:4d}, {y:4d})")
        self._saved_coords_text.setPlainText("\n".join(lines))

    def _parse_coords_from_text(self, text):
        """从文本解析坐标，支持 (x, y) 或 x y 格式"""
        import re
        coords = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # 格式: (x, y) 或 (x,y)
            match = re.search(r'\(\s*(-?\d+)\s*[,，]\s*(-?\d+)\s*\)', line)
            if match:
                coords.append((int(match.group(1)), int(match.group(2))))
                continue
            # 格式: x y 或 x, y
            parts = re.findall(r'-?\d+', line)
            if len(parts) >= 2:
                coords.append((int(parts[0]), int(parts[1])))
        return coords

    def _on_test_click(self, double_click=False):
        if not self.binder.is_bound:
            QMessageBox.warning(self, "提示", "请先绑定目标窗口")
            return

        text = self._edit_test_coords.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "提示", "请先输入或粘贴要测试的坐标")
            return

        coords = self._parse_coords_from_text(text)
        if not coords:
            QMessageBox.warning(self, "提示", "无法解析坐标，请使用格式: (x, y) 或 x y")
            return

        action = "双击" if double_click else "单击"
        self._log(f"开始测试{action}，共 {len(coords)} 个坐标...")
        for x, y in coords:
            self.tracker.test_click(x, y, double_click=double_click)
            # 每个点击之间短暂延时，让效果可见
            time.sleep(0.3)
        self._log(f"测试{action}完成，{len(coords)} 个坐标已全部执行")

    # ═══ 日志 ═══

    def _log(self, msg):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        self._log_text.append(line)
        self._coord_log.append(line)
        self._color_log.append(line)
        self._match_log.append(line)
        self._status_label.setText(msg)

    # ═══ 区域截图 ═══

    def _on_toggle_custom_screenshot(self, checked):
        """激活/取消区域截图框选模式"""
        if checked:
            if self.capture.cached_image is None:
                # 没有截图先自动截一张
                self._on_full_screenshot()
                # 延迟后进入框选
                QTimer.singleShot(500, self._enter_custom_pick)
                return
            self._enter_custom_pick()
        else:
            self._custom_screenshot_start = None
            self._screenshot_label.setCursor(Qt.CrossCursor)
            self._log("区域截图模式已取消")

    def _enter_custom_pick(self):
        """进入区域框选状态"""
        self._btn_custom_ss.setChecked(True)
        self._custom_screenshot_start = None
        self._screenshot_label.setCursor(Qt.CrossCursor)
        self._log("区域截图：请在截图上框选要保留的区域 (点击对角两点)")

    def _on_custom_screenshot_click(self, x: int, y: int):
        """区域截图框选的两点处理"""
        if self._custom_screenshot_start is None:
            # 第一点：记录起点
            self._custom_screenshot_start = (x, y)
            self._log(f"区域截图起点: ({x}, {y}) → 请点击对角点")
            # 标记起点
            annotations = list(self._screenshot_label._annotations)
            annotations.append((x, y, "flash", "↖"))
            self._screenshot_label.set_annotations(annotations)
        else:
            # 第二点：裁剪区域
            x0, y0 = self._custom_screenshot_start
            x1, y1 = x, y
            left, right = min(x0, x1), max(x0, x1)
            top, bottom = min(y0, y1), max(y0, y1)
            w, h = right - left, bottom - top

            if w < 5 or h < 5:
                self._log("选区太小 (最小 5x5 像素)，请重新框选")
                self._custom_screenshot_start = None
                return

            img = self.capture.cached_image
            if img is None:
                self._log("缓存截图丢失，请先截图")
                self._btn_custom_ss.setChecked(False)
                return

            # 裁剪
            cropped = img.crop((left, top, right, bottom))
            self._custom_screenshot_start = None
            self._btn_custom_ss.setChecked(False)

            # 更新截图显示
            from io import BytesIO
            buf = BytesIO()
            cropped.save(buf, format="PNG")
            qimg = QImage()
            qimg.loadFromData(buf.getvalue())
            pixmap = QPixmap.fromImage(qimg)
            self._screenshot_label.set_image(pixmap)
            self.capture._cached_image = cropped  # 同步缓存
            self._log(f"区域截图完成: ({left},{top}) → ({right},{bottom}) 尺寸 {w}x{h}")

    # ═══ 图片定位 (模板匹配) ═══

    def _on_toggle_template_pick(self, checked):
        if checked:
            if self.capture.cached_image is None:
                self._btn_pick_template.setChecked(False)
                self._log("请先截图，再选取模板")
                QMessageBox.warning(self, "提示", "请先执行完整截图")
                return
            self._template_region_start = None
            self._lbl_template_hint.setText("请在截图上点击第一个角...")
            self._lbl_template_hint.setStyleSheet("color: #ffaa00; font-weight: bold;")
            self._screenshot_label.setCursor(Qt.CrossCursor)
            self._log("模板选取模式已激活，请在截图上框选区域")
        else:
            self._template_region_start = None
            self._lbl_template_hint.setText("未选取模板" if self._template_image is None else "模板已就绪")
            self._lbl_template_hint.setStyleSheet(
                "color: #4a9eff;" if self._template_image else "color: #888;")

    def _on_template_pick_click(self, x: int, y: int):
        """模板选取模式的截图点击"""
        if self._template_region_start is None:
            # 第一点：记录起点
            self._template_region_start = (x, y)
            self._lbl_template_hint.setText(f"起点({x},{y}) → 请点击对角点...")
            self._log(f"模板选区起点: ({x}, {y})")
            # 在截图上临时标记起点
            annotations = list(self._screenshot_label._annotations)
            annotations.append((x, y, "flash", "P1"))
            self._screenshot_label.set_annotations(annotations)
        else:
            # 第二点：提取模板
            x0, y0 = self._template_region_start
            x1, y1 = x, y
            # 标准化矩形
            left, right = min(x0, x1), max(x0, x1)
            top, bottom = min(y0, y1), max(y0, y1)
            w, h = right - left, bottom - top

            if w < 5 or h < 5:
                self._log("选区太小 (最小 5x5 像素)，请重新选择")
                self._template_region_start = None
                self._lbl_template_hint.setText("选区太小，请在截图上重新框选...")
                self._lbl_template_hint.setStyleSheet("color: #ff4444; font-weight: bold;")
                return

            # 从缓存图片中裁剪模板
            img = self.capture.cached_image
            if img is None:
                self._log("缓存截图丢失，请重新截图")
                self._btn_pick_template.setChecked(False)
                return

            template = img.crop((left, top, right + 1, bottom + 1))
            self._template_image = template
            self._template_region_start = None

            # 更新预览
            self._update_template_preview()
            self._btn_match.setEnabled(True)
            self._btn_pick_template.setChecked(False)
            self._lbl_template_hint.setText(f"模板: {w}x{h} 就绪 ✅")
            self._lbl_template_hint.setStyleSheet("color: #4aff4a; font-weight: bold;")
            self._log(f"模板已选取: ({left},{top}) → ({right},{bottom}) 尺寸 {w}x{h}")

    def _update_template_preview(self):
        """更新模板预览标签"""
        if self._template_image is None:
            self._lbl_template_preview.clear()
            self._lbl_template_preview.setText("无")
            return
        img = self._template_image.copy()
        # 缩放到预览尺寸
        img.thumbnail((96, 76))
        if img.mode == "RGBA":
            qimg = QImage(img.tobytes("raw", "RGBA"),
                           img.width, img.height, QImage.Format_RGBA8888)
        else:
            qimg = QImage(img.tobytes("raw", "RGB"),
                           img.width, img.height, QImage.Format_RGB888)
        self._lbl_template_preview.setPixmap(QPixmap.fromImage(qimg))

    def _on_load_template(self):
        """从文件加载模板图片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "加载模板图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)")
        if not path:
            return
        try:
            from PIL import Image as PILImage
            img = PILImage.open(path)
            if img.width < 5 or img.height < 5:
                QMessageBox.warning(self, "提示", "图片太小，至少需要 5x5 像素")
                return
            # 统一缩放到逻辑像素
            dpr = QApplication.instance().primaryScreen().devicePixelRatio()
            if dpr > 1.001:
                new_w = int(img.width / dpr)
                new_h = int(img.height / dpr)
                img = img.resize((new_w, new_h), Image.LANCZOS)
            self._template_image = img.convert('RGB')
            self._update_template_preview()
            self._btn_match.setEnabled(True)
            self._lbl_template_hint.setText(
                f"模板: {img.width}x{img.height} (文件) ✅")
            self._lbl_template_hint.setStyleSheet("color: #4aff4a; font-weight: bold;")
            self._log(f"已加载模板图片: {os.path.basename(path)} ({img.width}x{img.height})")
        except Exception as e:
            self._log(f"加载模板失败: {e}")

    def _on_paste_template(self):
        """从剪贴板粘贴图片作为模板（QQ/微信截图后 Ctrl+C 复制即可）

        粘贴后自动根据当前屏幕 DPI 缩放到逻辑像素，
        与截图（也是逻辑像素）保持一致，确保模板匹配准确。
        """
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        if mime.hasImage():
            qimg = clipboard.image()
            if qimg.isNull():
                self._log("剪贴板中无有效图片")
                QMessageBox.warning(self, "提示", "剪贴板中没有图片数据")
                return
            # QImage → PIL Image
            qimg = qimg.convertToFormat(QImage.Format_RGBA8888)
            width, height = qimg.width(), qimg.height()
            ptr = qimg.bits()
            from PIL import Image as PILImage
            img = PILImage.frombytes("RGBA", (width, height),
                                     bytes(ptr), "raw", "RGBA")
        else:
            self._log("剪贴板中无图片（请先在QQ/微信中截图并 Ctrl+C 复制）")
            QMessageBox.warning(
                self, "提示",
                "剪贴板中没有图片。\n\n请在QQ/微信中截图后按 Ctrl+C 复制，再点击此按钮。")
            return

        if img.width < 5 or img.height < 5:
            QMessageBox.warning(self, "提示", "图片太小，至少需要 5x5 像素")
            return

        # 统一缩放到逻辑像素（与截图坐标系一致）
        dpr = QApplication.instance().primaryScreen().devicePixelRatio()
        if dpr > 1.001:
            new_w = int(img.width / dpr)
            new_h = int(img.height / dpr)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        self._template_image = img.convert('RGB')
        self._update_template_preview()
        self._btn_match.setEnabled(True)
        self._lbl_template_hint.setText(
            f"模板: {img.width}x{img.height} (粘贴) ✅")
        self._lbl_template_hint.setStyleSheet("color: #4aff4a; font-weight: bold;")
        self._log(f"已从剪贴板粘贴模板: {img.width}x{img.height} (dpr={dpr:.2f})")

    def _on_clear_template(self):
        """清除当前模板"""
        self._template_image = None
        self._lbl_template_preview.clear()
        self._lbl_template_preview.setText("无")
        self._btn_match.setEnabled(False)
        self._lbl_template_hint.setText("未选取模板")
        self._lbl_template_hint.setStyleSheet("color: #888;")
        self._table_matches.setRowCount(0)
        self._lbl_match_status.setText("")
        self._log("已清除模板")

    def _on_match_thresh_changed(self, val):
        self.matcher.threshold = val / 100.0

    def _on_max_results_changed(self, val):
        self.matcher.max_results = val

    def _on_match_template(self):
        """执行模板匹配"""
        if self._template_image is None:
            self._log("请先选取模板")
            return

        # 重新截图确保图片最新
        img = None
        if self._adb_serial:
            self._log("正在通过 ADB 截图以进行模板匹配...")
            try:
                from adbutils import adb
                d = adb.device(self._adb_serial)
                img = d.screenshot()
            except Exception as e:
                self._log(f"ADB 截图失败: {e}")
        if img is None and self.binder.is_bound:
            self._log("正在截取窗口以进行模板匹配...")
            img = self.capture.capture_window(
                self.binder.target_window.hwnd,
                client_area=self._cb_client_area.isChecked())
        if img is None:
            img = self.capture.cached_image

        if img is None:
            self._log("没有可用的截图，请先截图")
            QMessageBox.warning(self, "提示", "请先执行完整截图")
            return

        # 更新截图显示
        self._on_screenshot(img)

        self._lbl_match_status.setText("匹配中...")
        self._btn_match.setEnabled(False)

        # 后台匹配 (用 QTimer 避免阻塞 UI)
        QTimer.singleShot(50, lambda: self._do_match(img))

    def _do_match(self, img):
        """在后台执行匹配并更新结果"""
        try:
            results, elapsed = self.matcher.match(img, self._template_image)
        except Exception as e:
            self._log(f"匹配失败: {e}")
            self._btn_match.setEnabled(True)
            self._lbl_match_status.setText("匹配失败")
            self._lbl_match_status.setStyleSheet("color: #ff4444; padding: 0 8px;")
            return

        self._btn_match.setEnabled(True)
        if not results:
            self._lbl_match_status.setText(
                f"未找到匹配 (阈值={self.matcher.threshold:.0%})")
            self._lbl_match_status.setStyleSheet("color: #ff4444; padding: 0 8px;")
            self._log(f"未找到匹配: {len(results)} 个结果 ({elapsed:.2f}s)")
            self._table_matches.setRowCount(0)
            return

        self._lbl_match_status.setText(
            f"找到 {len(results)} 个匹配 ({elapsed:.2f}s)")
        self._lbl_match_status.setStyleSheet("color: #4aff4a; padding: 0 8px; font-weight: bold;")
        self._log(f"模板匹配完成: {len(results)} 个结果, 耗时 {elapsed:.2f}s")

        # 填充结果表格
        self._table_matches.setRowCount(len(results))
        for i, m in enumerate(results):
            self._table_matches.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._table_matches.setItem(i, 1, QTableWidgetItem(str(m.x)))
            self._table_matches.setItem(i, 2, QTableWidgetItem(str(m.y)))
            cx, cy = m.center
            self._table_matches.setItem(i, 3, QTableWidgetItem(f"({cx}, {cy})"))
            conf_item = QTableWidgetItem(f"{m.confidence:.1%}")
            if m.confidence >= 0.9:
                conf_item.setForeground(QColor(0, 255, 0))
            elif m.confidence >= 0.8:
                conf_item.setForeground(QColor(180, 255, 0))
            else:
                conf_item.setForeground(QColor(255, 200, 0))
            self._table_matches.setItem(i, 4, conf_item)

        # 在截图上标记所有匹配
        annotations = []
        for m in results:
            annotations.append((m.x, m.y, "found", f"{m.confidence:.0%}"))
        self._screenshot_label.set_annotations(annotations)

    def _on_click_match_result(self):
        """点击选中匹配结果的位置 → 发送到窗口"""
        if not self.binder.is_bound:
            QMessageBox.warning(self, "提示", "请先绑定目标窗口")
            return
        rows = set()
        for item in self._table_matches.selectedItems():
            rows.add(item.row())
        if not rows:
            QMessageBox.information(self, "提示", "请在结果列表中选择一个匹配项")
            return
        for row in rows:
            try:
                x = int(self._table_matches.item(row, 1).text())
                y = int(self._table_matches.item(row, 2).text())
                cx, cy = x + self._template_image.width // 2, y + self._template_image.height // 2
                self.tracker.test_click(cx, cy, double_click=False)
                self._log(f"点击匹配位置: ({cx}, {cy}) 行#{row+1}")
                self._lbl_click.setText(f"最后点击: ({cx}, {cy})")
            except Exception:
                pass

    def _on_copy_match_results(self):
        """复制全部匹配结果坐标"""
        if self._table_matches.rowCount() == 0:
            QMessageBox.information(self, "提示", "没有匹配结果")
            return
        lines = []
        for row in range(self._table_matches.rowCount()):
            x = self._table_matches.item(row, 1).text()
            y = self._table_matches.item(row, 2).text()
            conf = self._table_matches.item(row, 4).text()
            lines.append(f"({x}, {y})  [{conf}]")
        QApplication.clipboard().setText("\n".join(lines))
        self._log(f"已复制 {len(lines)} 个匹配结果坐标")

    def _on_clear_match_results(self):
        self._table_matches.setRowCount(0)
        self._lbl_match_status.setText("")
        # 清除截图标注
        self._screenshot_label.set_annotations([])
        self._log("已清空匹配结果")


    # ============================================================
    # ADB 扫描与绑定 (投屏窗口)
    # ============================================================

    def _on_scan_adb_devices(self):
        """扫描 ADB 设备"""
        self._btn_adb.setEnabled(False)
        self._btn_adb.setText("扫描中...")
        self._log("正在扫描 ADB 设备...")
        self.adb_scanner.scan()

    def _on_adb_devices_found(self, devices):
        """ADB 设备扫描完成 - 弹出设备选择对话框"""
        self._btn_adb.setEnabled(True)
        self._btn_adb.setText("绑定设备")
        if not devices:
            self._log("未发现 ADB 设备")
            QMessageBox.information(self, "ADB 扫描", "未检测到已连接的 Android 设备\n请确认 USB 调试已开启且已通过 USB 连接")
            return

        self._log(f"发现 {len(devices)} 台 ADB 设备")

        # 弹出设备选择对话框
        dialog = _AdbDeviceDialog(devices, self)
        if dialog.exec() == QMessageBox.Accepted and dialog.selected_device:
            self._bind_adb_device(dialog.selected_device)

    def _bind_adb_device(self, device):
        """绑定 ADB 设备: 自动识别投屏窗口并设置裁剪区域"""
        serial = device["serial"]
        self._adb_serial = serial  # 记录 ADB 设备，截图时走 ADB
        resolution = device.get("resolution", "")
        self._log(f"正在绑定设备: {serial}")

        import win32gui
        target_hwnd = [None]
        target_info = [None]
        all_candidates = []

        def find_cb(hwnd, _):
            try:
                title = win32gui.GetWindowText(hwnd)
                cls = win32gui.GetClassName(hwnd)
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                rect = win32gui.GetWindowRect(hwnd)
                w, h = rect[2] - rect[0], rect[3] - rect[1]
                if w < 200 or h < 200:
                    return True
                title_lower = title.lower()
                cls_lower = cls.lower()
                matched = False
                if any(kw in title for kw in ["投屏", "镜像", "scrcpy", "QtScrcpy", "android"]):
                    matched = True
                if "tauri window" in cls_lower:
                    matched = True
                if "qt" in cls_lower and "qwindow" in cls_lower:
                    if any(kw in title_lower for kw in ["投屏", "镜像", "scrcpy"]):
                        matched = True
                if matched:
                    all_candidates.append((hwnd, title, cls, w, h))
                    if not target_hwnd[0]:
                        target_hwnd[0] = hwnd
                        target_info[0] = (hwnd, title, cls, w, h)
                return True
            except:
                return True

        win32gui.EnumWindows(find_cb, None)

        if not target_hwnd[0]:
            self._log(f"未找到投屏窗口，候选窗口 {len(all_candidates)} 个")
            for hwnd, title, cls, w, h in all_candidates:
                self._log(f"  候选: [{cls}] {title!r} {w}x{h}")
            QMessageBox.warning(self, "提示",
                "未找到投屏窗口\n请先启动 scrcpy 或其他投屏工具")
            return

        hwnd, title, cls, w, h = target_info[0]
        self._log(f"投屏窗口: [{cls}] {title!r} {w}x{h}")

        # 子窗口检测 - 自动裁剪区域
        child_windows = self.binder.enumerate_child_windows(hwnd)
        phone_child = None
        for child in child_windows:
            cw, ch = child.width, child.height
            if cw > 200 and ch > 200:
                if phone_child is None or (cw * ch) > (phone_child.width * phone_child.height):
                    phone_child = child
                self._log(f"  子窗口: [{child.class_name}] {child.title!r} {cw}x{ch} "
                         f"pos=({child.rect[0]},{child.rect[1]})")

        # 自动绑定 + 拉到前台确保截图可见
        self.binder.bind_window(hwnd)
        # 显示 ADB 设备信息
        info = f"ADB: {serial}"
        if resolution:
            info += f"  |  {resolution}"
        self._lbl_bound_info.setText(info)
        self._lbl_bound_info.setStyleSheet(
            "color: #4FC3F7; padding: 0 8px; font-weight: bold;")
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            self._log("已将投屏窗口拉到前台")
        except Exception:
            pass

        # 子窗口 / 分辨率信息
        if phone_child:
            main_rect = win32gui.GetWindowRect(hwnd)
            offset_x = phone_child.rect[0] - main_rect[0]
            offset_y = phone_child.rect[1] - main_rect[1]
            self._log(f"检测到子窗口区域: offset=({offset_x},{offset_y}) "
                     f"size={phone_child.width}x{phone_child.height}")
        elif resolution and "x" in resolution.lower():
            self._log(f"设备分辨率: {resolution}")

        self._log(f"ADB设备绑定完成! 序列号: {serial}")

class _ScreenshotLoader(QThread):
    """后台逐个加载设备截图，避免多设备同时 ADB 冲突"""
    screenshot_ready = Signal(str, object)  # serial, PIL Image or None

    def __init__(self, serials):
        super().__init__()
        self.serials = serials

    def run(self):
        import time
        from adbutils import adb
        for serial in self.serials:
            try:
                d = adb.device(serial)
                # 尝试唤醒屏幕
                try:
                    power_info = d.shell("dumpsys power")
                    if "mWakefulness=Asleep" in power_info:
                        d.shell("input keyevent 26")
                        time.sleep(0.5)
                except:
                    pass
                img = d.screenshot()  # 返回 PIL Image
                self.screenshot_ready.emit(serial, img)
            except Exception:
                self.screenshot_ready.emit(serial, None)


class _AdbDeviceDialog(QDialog):
    """ADB 设备选择对话框 — 截图异步加载"""

    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择 ADB 设备")
        self.setMinimumWidth(580)
        self.setMinimumHeight(420)
        self.selected_device = None
        self._cards = {}
        self._thumb_labels = {}
        self._loader = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 标题
        title = QLabel(f"发现 <b>{len(devices)}</b> 台 ADB 设备，点击选中要绑定的设备:")
        title.setTextFormat(Qt.RichText)
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #444; background: #1a1a1a; border-radius: 6px; }")
        scroll_widget = QWidget()
        self._scroll_layout = QVBoxLayout(scroll_widget)
        self._scroll_layout.setContentsMargins(4, 4, 4, 4)
        self._scroll_layout.setSpacing(6)
        self._scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # 状态标签
        self._lbl_status = QLabel("正在加载设备截图...")
        self._lbl_status.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._lbl_status)

        # 底部按钮
        footer = QHBoxLayout()
        footer.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self._on_cancel)
        footer.addWidget(cancel_btn)
        self._btn_confirm = QPushButton("确认绑定")
        self._btn_confirm.setObjectName("btnPrimary")
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.clicked.connect(self._on_confirm)
        footer.addWidget(self._btn_confirm)
        layout.addLayout(footer)

        # 创建设备卡片
        for d in devices:
            card = self._create_device_card(d)
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, card)

        # 启动截图加载线程
        serials = [d["serial"] for d in devices]
        if serials:
            self._loader = _ScreenshotLoader(serials)
            self._loader.screenshot_ready.connect(self._on_screenshot_loaded)
            self._loader.finished.connect(self._on_all_loaded)
            self._loader.start()

    def _create_device_card(self, dev):
        card = QFrame()
        card.setObjectName("deviceCard")
        card.setFixedHeight(90)
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet(
            "QFrame#deviceCard { background: #252525; border: 2px solid #444; border-radius: 8px; }"
            'QFrame#deviceCard[selected="true"] { border: 2px solid #4FC3F7; background: #1e2d3d; }'
        )
        card.setProperty("device_serial", dev["serial"])

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        # 缩略图占位
        thumb = QLabel("加载中...")
        thumb.setFixedSize(120, 72)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setStyleSheet(
            "background: #1a1a1a; border: 1px solid #333; border-radius: 4px;"
            "color: #666; font-size: 11px;"
        )
        layout.addWidget(thumb)

        # 设备信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        lbl_serial = QLabel(dev["serial"])
        lbl_serial.setStyleSheet("color: #4FC3F7; font-weight: bold; font-size: 13px;")
        info_layout.addWidget(lbl_serial)

        if dev.get("resolution"):
            lbl_res = QLabel(f"分辨率: {dev['resolution']}")
            lbl_res.setStyleSheet("color: #999; font-size: 12px;")
            info_layout.addWidget(lbl_res)

        lbl_hint = QLabel("点击选中此设备")
        lbl_hint.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(lbl_hint)
        info_layout.addStretch()
        layout.addLayout(info_layout, 1)

        # 选中标记
        lbl_check = QLabel("○")
        lbl_check.setFixedWidth(30)
        lbl_check.setAlignment(Qt.AlignCenter)
        lbl_check.setStyleSheet("color: #555; font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl_check)

        # 点击卡片选中
        card.mousePressEvent = lambda e, s=dev["serial"]: self._select_device(s)

        # 缩略图点击 → 大图预览
        thumb.mousePressEvent = lambda e, s=dev["serial"]: self._show_preview(s)

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
                from io import BytesIO
                buf = BytesIO()
                img.save(buf, format="PNG")
                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                scaled = pix.scaled(118, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb.setPixmap(scaled)
                thumb.setStyleSheet(
                    "background: #111; border: 1px solid #333; border-radius: 4px;"
                )
                # 保存原始图片供预览
                self._thumb_labels[serial + "_full"] = img
            except Exception:
                thumb.setText("加载失败")
                thumb.setStyleSheet(
                    "background: #1a1a1a; border: 1px solid #333; border-radius: 4px;"
                    "color: #ff6666; font-size: 11px;"
                )
        else:
            thumb.setText("无画面")
            thumb.setStyleSheet(
                "background: #1a1a1a; border: 1px solid #333; border-radius: 4px;"
                "color: #ffaa00; font-size: 11px;"
            )

    def _on_all_loaded(self):
        loaded = sum(1 for k in self._thumb_labels if not k.endswith("_full") and not self._thumb_labels[k].text())
        self._lbl_status.setText("截图加载完成，请选择设备")
        self._lbl_status.setStyleSheet("color: #6a6; font-size: 12px;")

    def _select_device(self, serial):
        """选中某台设备"""
        self.selected_device = None
        self._btn_confirm.setEnabled(True)
        for s, card in self._cards.items():
            chk = card.property("check_label")
            if s == serial:
                self.selected_device = {"serial": s}
                card.setProperty("selected", "true")
                card.setStyleSheet(
                    'QFrame#deviceCard[selected="true"]'
                    "{ border: 2px solid #4FC3F7; background: #1e2d3d; border-radius: 8px; }"
                )
                if chk:
                    chk.setText("●")
                    chk.setStyleSheet("color: #4FC3F7; font-size: 22px; font-weight: bold;")
            else:
                card.setProperty("selected", "false")
                card.setStyleSheet(
                    "QFrame#deviceCard { background: #252525; border: 2px solid #444; border-radius: 8px; }"
                )
                if chk:
                    chk.setText("○")
                    chk.setStyleSheet("color: #555; font-size: 22px; font-weight: bold;")

    def _show_preview(self, serial):
        """弹出大图预览"""
        full_key = serial + "_full"
        if full_key not in self._thumb_labels:
            return
        img = self._thumb_labels[full_key]
        if img is None:
            return
        try:
            from io import BytesIO
            buf = BytesIO()
            img.save(buf, format="PNG")
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())

            preview = QDialog(self)
            preview.setWindowTitle(f"设备截图 - {serial}")
            preview.setMinimumSize(300, 200)

            layout = QVBoxLayout(preview)
            layout.setContentsMargins(8, 8, 8, 8)

            scr = QScrollArea()
            scr.setWidgetResizable(False)
            scr.setStyleSheet("QScrollArea { border: none; background: #111; }")

            img_label = QLabel()
            screen = QApplication.primaryScreen()
            if screen:
                max_w = int(screen.availableGeometry().width() * 0.85)
                max_h = int(screen.availableGeometry().height() * 0.85)
                if pix.width() > max_w or pix.height() > max_h:
                    pix = pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pix)
            img_label.setAlignment(Qt.AlignCenter)
            scr.setWidget(img_label)
            layout.addWidget(scr)

            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(preview.accept)
            layout.addWidget(close_btn, 0, Qt.AlignCenter)

            preview.exec()
        except Exception:
            pass

    def _on_confirm(self):
        if self.selected_device:
            self.accept()

    def _on_cancel(self):
        if self._loader and self._loader.isRunning():
            self._loader.terminate()
        self.reject()
def closeEvent(self, event):
        self.tracker.stop_tracking()
        super().closeEvent(event)
