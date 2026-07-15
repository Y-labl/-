"""主窗口 - 左侧功能导航 + 右侧操作面板"""

import sys
import os
import time
from io import BytesIO
from PIL import Image as PILImage

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QComboBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QGroupBox, QTextEdit, QStatusBar,
    QMessageBox, QApplication, QCheckBox, QMenu, QFileDialog,
    QScrollArea, QSizePolicy, QTabWidget, QDialog, QFrame,
    QStackedWidget, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QRect, QPoint, QThread
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QPen, QFont, QFontMetrics,
    QMouseEvent, QClipboard, QCursor, QAction, QPalette
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
COLOR_YELLOW = QColor(255, 210, 0)
COLOR_RECT = QColor(0, 200, 255)

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
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
}
QLineEdit:focus { border-color: #4a9eff; }
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
QListWidget {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    color: #ccc;
    outline: none;
}
QListWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #333;
}
QListWidget::item:selected {
    background-color: #1e3a5f;
    color: #4a9eff;
    border-left: 3px solid #4a9eff;
}
QListWidget::item:hover {
    background-color: #2a2a2a;
}
"""


# ═══════════════════════════════════════════════════════════
# 增强版 ClickableLabel：支持拖拽裁剪、标注点、矩形框
# ═══════════════════════════════════════════════════════════

class ClickableLabel(QLabel):
    """可交互的图片预览标签，支持：
    - 缩放/平移
    - 悬停坐标显示
    - 拖拽裁剪（mousedown → 拖拽矩形 → mouseup 裁剪）
    - 黄色标注点叠加
    - 矩形定位框叠加
    """
    clicked = Signal(int, int)           # 左键点击
    hovered = Signal(int, int)           # 悬停
    zoom_changed = Signal(float)
    drag_started = Signal(int, int)      # 拖拽开始
    drag_moved = Signal(int, int, int, int)  # 拖拽移动 (x,y,w,h)
    drag_finished = Signal(int, int, int, int)  # 拖拽结束 (x,y,w,h)
    crop_finished = Signal(object)       # 裁剪完成 → PIL Image
    rect_finalized = Signal(int, int, int, int)  # 矩形编辑完成 (x,y,w,h)
    rect_changed = Signal(int, int, int, int)    # 矩形实时变化 (x,y,w,h)
    upload_requested = Signal()                  # 无图片时点击请求上传

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumSize(320, 240)
        self.setStyleSheet("background-color: #222; border: 1px solid #555;")
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)

        self._pixmap_original = None
        self._zoom_level = 0.0
        self._fit_scale = 1.0
        self._scale_factor = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._panning = False
        self._pan_start = None
        self._pan_offset_x = 0
        self._pan_offset_y = 0

        # 拖拽裁剪状态
        self._drag_mode = False
        self._dragging = False
        self._drag_start = None       # 图片坐标
        self._drag_current = None     # 图片坐标
        self._drag_rect = None        # QRect (图片坐标)

        # 标注叠加
        self._annotations = []
        # 黄色标注点 (x, y)
        self._marker_point = None
        # 矩形定位框 (x, y, w, h)
        self._locator_rect = None
        # 模板匹配结果矩形 [(x, y, w, h, confidence), ...]
        self._match_rects = []

        # 额外 PIL 图片引用（用于裁剪）
        self._pil_image = None

        # 交互式矩形编辑（框选定位）
        self._rect_interactive = False
        self._rect_state = None          # None | 'drawing' | 'move' | 'resize_*'
        self._rect_anchor = None         # 拖拽锚点 (img_x, img_y)
        self._rect_orig = None           # 拖拽前的原始矩形 (x, y, w, h)
        self._rect_drag_pressed = False  # 鼠标按下但尚未拖拽
        self._rect_press_pos = None      # 鼠标按下位置 (img_x, img_y)

    # ── 缩放控制 ──
    def set_zoom(self, level: float):
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
        if self._pixmap_original is None:
            return 100
        return int(self._scale_factor * 100)

    # ── 图片 / 标注 / 标记点设置 ──
    def set_image(self, pixmap: QPixmap, pil_img=None):
        self._pixmap_original = pixmap
        self._pil_image = pil_img
        self._annotations = []
        self._marker_point = None
        self._locator_rect = None
        self._drag_rect = None
        self._match_rects = []
        self._pan_offset_x = 0
        self._pan_offset_y = 0
        self.setCursor(Qt.CrossCursor)
        self._update_display()

    def set_annotations(self, annotations: list):
        self._annotations = annotations
        self._update_display()

    def set_marker_point(self, x: int, y: int):
        """设置黄色标注点"""
        self._marker_point = (x, y)
        self._update_display()

    def clear_marker(self):
        self._marker_point = None
        self._update_display()

    def set_match_rects(self, rects: list):
        """设置模板匹配结果矩形 [(x, y, w, h, confidence), ...]"""
        self._match_rects = rects
        self._update_display()

    def clear_match_rects(self):
        self._match_rects = []
        self._update_display()

    def get_marker_point(self):
        return self._marker_point

    def set_locator_rect(self, x: int, y: int, w: int, h: int):
        """设置矩形定位框"""
        if w > 0 and h > 0:
            self._locator_rect = (x, y, w, h)
            self._update_display()

    def clear_locator(self):
        self._locator_rect = None
        self._update_display()

    def set_drag_mode(self, enabled: bool):
        """启用/禁用拖拽裁剪模式"""
        self._drag_mode = enabled
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self._drag_rect = None
        if enabled:
            self._rect_interactive = False
        if not enabled:
            self._update_display()

    def set_rect_interactive(self, enabled: bool):
        """启用/禁用交互式矩形编辑模式（框选定位）"""
        self._rect_interactive = enabled
        self._rect_state = None
        self._rect_anchor = None
        self._rect_orig = None
        self._rect_drag_pressed = False
        self._rect_press_pos = None
        if enabled:
            self._drag_mode = False
        self.setCursor(Qt.CrossCursor)

    def _img_to_widget(self, img_x: int, img_y: int):
        """图片坐标 → 控件坐标"""
        wx = int(img_x * self._scale_factor + self._offset_x)
        wy = int(img_y * self._scale_factor + self._offset_y)
        return wx, wy

    def _widget_to_img(self, wx: float, wy: float):
        """控件坐标 → 图片坐标"""
        ix = int((wx - self._offset_x) / self._scale_factor)
        iy = int((wy - self._offset_y) / self._scale_factor)
        if self._pixmap_original:
            ix = max(0, min(ix, self._pixmap_original.width() - 1))
            iy = max(0, min(iy, self._pixmap_original.height() - 1))
        return ix, iy

    # ═══ 交互式矩形编辑（框选定位） ═══

    def _hit_test_rect(self, img_x: int, img_y: int):
        """检测鼠标在矩形上的位置，返回操作类型或 None"""
        if not self._locator_rect or self._locator_rect[2] <= 0 or self._locator_rect[3] <= 0:
            return None
        lx, ly, lw, lh = self._locator_rect
        margin = max(6, int(8 / max(self._scale_factor, 0.01)))  # 图片坐标下的容差

        # 检测四角
        corners = {
            'resize_nw': (lx, ly),
            'resize_ne': (lx + lw, ly),
            'resize_sw': (lx, ly + lh),
            'resize_se': (lx + lw, ly + lh),
        }
        for action, (cx, cy) in corners.items():
            if abs(img_x - cx) <= margin and abs(img_y - cy) <= margin:
                return action

        # 检测四边
        inside_x = lx <= img_x <= lx + lw
        inside_y = ly <= img_y <= ly + lh
        if inside_x:
            if abs(img_y - ly) <= margin:
                return 'resize_n'
            if abs(img_y - (ly + lh)) <= margin:
                return 'resize_s'
        if inside_y:
            if abs(img_x - lx) <= margin:
                return 'resize_w'
            if abs(img_x - (lx + lw)) <= margin:
                return 'resize_e'

        # 检测内部
        if inside_x and inside_y:
            return 'move'

        return None

    def _start_rect_interact(self, img_x: int, img_y: int):
        """开始交互式操作（拖拽开始）"""
        action = self._hit_test_rect(img_x, img_y)
        if action and action.startswith('resize_') and self._locator_rect:
            self._rect_state = action
            self._rect_anchor = (img_x, img_y)
            self._rect_orig = tuple(self._locator_rect)
        elif action == 'move' and self._locator_rect:
            self._rect_state = 'move'
            self._rect_anchor = (img_x, img_y)
            self._rect_orig = tuple(self._locator_rect)
        else:
            # 无矩形或点击在外部 → 绘制新矩形
            self._rect_state = 'drawing'
            self._rect_anchor = (img_x, img_y)
            self._rect_orig = (img_x, img_y, 0, 0)
            self._locator_rect = (img_x, img_y, 0, 0)

    def _do_rect_interact(self, curr_x: int, curr_y: int):
        """拖拽中实时更新矩形"""
        if self._rect_state == 'drawing':
            ax, ay = self._rect_anchor
            x = min(ax, curr_x)
            y = min(ay, curr_y)
            w = abs(curr_x - ax)
            h = abs(curr_y - ay)
            self._locator_rect = (x, y, w, h)
            self.rect_changed.emit(x, y, w, h)
        elif self._rect_state == 'move' and self._rect_orig:
            r = self._rect_orig
            ax, ay = self._rect_anchor
            dx, dy = curr_x - ax, curr_y - ay
            if self._pixmap_original:
                new_x = max(0, min(r[0] + dx, self._pixmap_original.width() - r[2]))
                new_y = max(0, min(r[1] + dy, self._pixmap_original.height() - r[3]))
            else:
                new_x, new_y = r[0] + dx, r[1] + dy
            self._locator_rect = (new_x, new_y, r[2], r[3])
            self.rect_changed.emit(new_x, new_y, r[2], r[3])
        elif self._rect_state.startswith('resize_') and self._rect_orig:
            self._do_rect_resize(curr_x, curr_y)

    def _do_rect_resize(self, curr_x: int, curr_y: int):
        """缩放矩形（拖拽边角）"""
        r = self._rect_orig
        pw = self._pixmap_original.width() if self._pixmap_original else 99999
        ph = self._pixmap_original.height() if self._pixmap_original else 99999
        state = self._rect_state
        MIN_SIZE = 5

        new_x, new_y, new_w, new_h = r

        if state == 'resize_nw':
            rb, bb = r[0] + r[2], r[1] + r[3]
            new_x = max(0, min(curr_x, rb - MIN_SIZE))
            new_y = max(0, min(curr_y, bb - MIN_SIZE))
            new_w = rb - new_x
            new_h = bb - new_y
        elif state == 'resize_ne':
            bb = r[1] + r[3]
            new_y = max(0, min(curr_y, bb - MIN_SIZE))
            new_w = max(MIN_SIZE, min(curr_x - r[0], pw - r[0]))
            new_h = bb - new_y
        elif state == 'resize_sw':
            rb = r[0] + r[2]
            new_x = max(0, min(curr_x, rb - MIN_SIZE))
            new_w = rb - new_x
            new_h = max(MIN_SIZE, min(curr_y - r[1], ph - r[1]))
        elif state == 'resize_se':
            new_w = max(MIN_SIZE, min(curr_x - r[0], pw - r[0]))
            new_h = max(MIN_SIZE, min(curr_y - r[1], ph - r[1]))
        elif state == 'resize_n':
            new_y = max(0, min(curr_y, r[1] + r[3] - MIN_SIZE))
            new_h = r[1] + r[3] - new_y
        elif state == 'resize_s':
            new_h = max(MIN_SIZE, min(curr_y - r[1], ph - r[1]))
        elif state == 'resize_w':
            new_x = max(0, min(curr_x, r[0] + r[2] - MIN_SIZE))
            new_w = r[0] + r[2] - new_x
        elif state == 'resize_e':
            new_w = max(MIN_SIZE, min(curr_x - r[0], pw - r[0]))

        self._locator_rect = (new_x, new_y, new_w, new_h)
        self.rect_changed.emit(new_x, new_y, new_w, new_h)

    def _finish_rect_interact(self):
        """完成拖拽操作"""
        if self._locator_rect and self._locator_rect[2] > 0 and self._locator_rect[3] > 0:
            self.rect_finalized.emit(*self._locator_rect)
        self._rect_state = None
        self._rect_anchor = None
        self._rect_orig = None
        self._rect_drag_pressed = False
        self._rect_press_pos = None
        self.setCursor(Qt.CrossCursor)

    def _update_display(self):
        if self._pixmap_original is None:
            # 无图片时显示上传提示
            avail_w = max(1, self.width() - 4)
            avail_h = max(1, self.height() - 4)
            placeholder = QPixmap(avail_w, avail_h)
            placeholder.fill(QColor(40, 40, 40))
            painter = QPainter(placeholder)
            painter.setRenderHint(QPainter.Antialiasing)
            # 虚线边框
            pen = QPen(QColor(100, 100, 100), 2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRoundedRect(8, 8, avail_w - 16, avail_h - 16, 8, 8)
            # 上传图标 (简单的 + 号)
            cx, cy = avail_w // 2, avail_h // 2
            painter.setPen(QPen(QColor(140, 140, 140), 2))
            icon_size = 24
            painter.drawLine(cx - icon_size, cy, cx + icon_size, cy)
            painter.drawLine(cx, cy - icon_size, cx, cy + icon_size)
            # 提示文字
            font = QFont("Microsoft YaHei", 12)
            painter.setFont(font)
            painter.setPen(QPen(QColor(160, 160, 160)))
            painter.drawText(0, cy + icon_size + 24, avail_w, 24,
                             Qt.AlignCenter, "点击上传图片")
            font_small = QFont("Microsoft YaHei", 9)
            painter.setFont(font_small)
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawText(0, cy + icon_size + 50, avail_w, 20,
                             Qt.AlignCenter, "或使用右侧工具栏截图")
            painter.end()
            self.setPixmap(placeholder)
            self.setCursor(Qt.PointingHandCursor)
            self._offset_x = 0
            self._offset_y = 0
            return
        pw = self._pixmap_original.width()
        ph = self._pixmap_original.height()

        avail_w = self.width() - 4
        avail_h = self.height() - 4
        if avail_w <= 0 or avail_h <= 0:
            return

        self._fit_scale = min(avail_w / pw, avail_h / ph)
        if self._zoom_level <= 0:
            self._scale_factor = self._fit_scale
        else:
            self._scale_factor = self._fit_scale * self._zoom_level

        new_w = max(1, int(pw * self._scale_factor))
        new_h = max(1, int(ph * self._scale_factor))

        self._pan_offset_x = max(0, min(self._pan_offset_x, max(0, new_w - avail_w)))
        self._pan_offset_y = max(0, min(self._pan_offset_y, max(0, new_h - avail_h)))

        smooth = self._scale_factor < 3.0
        scaled = self._pixmap_original.scaled(
            new_w, new_h, Qt.KeepAspectRatio,
            Qt.SmoothTransformation if smooth else Qt.FastTransformation)

        # 画所有叠加内容
        painter = QPainter(scaled)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 标注点 (颜色验证等)
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

        # 1.5 模板匹配结果矩形
        for mx, my, mw, mh, m_conf in self._match_rects:
            sx = int(mx * self._scale_factor)
            sy = int(my * self._scale_factor)
            sw = int(mw * self._scale_factor)
            sh = int(mh * self._scale_factor)

            # 半透明绿色填充
            painter.setBrush(QColor(0, 255, 80, 30))
            painter.setPen(QPen(QColor(0, 255, 100), 2))
            painter.drawRect(sx, sy, sw, sh)

            # 外描边（稍粗）
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 220, 80), 1))
            painter.drawRect(sx - 1, sy - 1, sw + 2, sh + 2)

            # 中心十字
            cx = sx + sw // 2
            cy = sy + sh // 2
            painter.setPen(QPen(QColor(0, 255, 100), 1))
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)

            # 置信度标签（圆角背景）
            label_text = f"{m_conf:.0%}"
            font_s = QFont("Consolas", 9, QFont.Bold)
            painter.setFont(font_s)
            fm = QFontMetrics(font_s)
            label_w = fm.horizontalAdvance(label_text) + 10
            label_h = 16
            label_x = sx + 2
            label_y = sy - label_h - 2 if sy > label_h + 4 else sy + sh + 2
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(label_x, label_y, label_w, label_h, 4, 4)
            painter.setPen(QPen(QColor(0, 255, 100)))
            painter.drawText(label_x, label_y, label_w, label_h,
                             Qt.AlignCenter, label_text)

        # 2. 黄色标注点
        if self._marker_point:
            mx, my = self._marker_point
            sx = int(mx * self._scale_factor)
            sy = int(my * self._scale_factor)

            # 外圈
            painter.setPen(QPen(COLOR_YELLOW, 3))
            painter.setBrush(Qt.NoBrush)
            r = 12
            painter.drawEllipse(sx - r, sy - r, r * 2, r * 2)
            # 十字线
            painter.drawLine(sx - 16, sy, sx + 16, sy)
            painter.drawLine(sx, sy - 16, sx, sy + 16)
            # 内圈实心
            painter.setBrush(QColor(255, 210, 0, 120))
            painter.drawEllipse(sx - 4, sy - 4, 8, 8)
            # 坐标标签
            painter.setPen(QPen(QColor(255, 255, 255)))
            font_s = QFont("Consolas", 9, QFont.Bold)
            painter.setFont(font_s)
            label_y = sy - 18 if sy > 20 else sy + 28
            painter.drawText(sx - 30, label_y, 60, 18,
                             Qt.AlignCenter, f"({mx}, {my})")

        # 3. 矩形定位框
        if self._locator_rect:
            lx, ly, lw, lh = self._locator_rect
            sx = int(lx * self._scale_factor)
            sy = int(ly * self._scale_factor)
            sw = int(lw * self._scale_factor)
            sh = int(lh * self._scale_factor)

            # 半透明填充
            painter.setBrush(QColor(0, 180, 255, 50))
            # 外框：实线、加粗、亮色
            pen = QPen(QColor(0, 220, 255), max(2, int(3 * self._scale_factor / self._fit_scale)))
            painter.setPen(pen)
            painter.drawRect(sx, sy, sw, sh)
            # 四角标记（增强可见性）
            corner_len = max(8, int(12 * self._scale_factor / self._fit_scale))
            painter.setPen(QPen(QColor(255, 230, 0), max(2, int(2 * self._scale_factor / self._fit_scale))))
            for cx, cy in [(sx, sy), (sx + sw, sy), (sx, sy + sh), (sx + sw, sy + sh)]:
                painter.drawLine(cx - corner_len, cy, cx + corner_len, cy)
                painter.drawLine(cx, cy - corner_len, cx, cy + corner_len)
            # 十字中心线
            painter.setPen(QPen(QColor(0, 220, 255, 120), 1, Qt.DashLine))
            painter.drawLine(sx + sw // 2, sy + 4, sx + sw // 2, sy + sh - 4)
            painter.drawLine(sx + 4, sy + sh // 2, sx + sw - 4, sy + sh // 2)
            # 信息标签（带背景）
            info_text = f"({lx},{ly}) {lw}x{lh}"
            font_s = QFont("Consolas", 10, QFont.Bold)
            painter.setFont(font_s)
            text_w = painter.fontMetrics().horizontalAdvance(info_text) + 10
            text_h = 20
            label_bg_x = sx
            label_bg_y = sy - text_h - 4
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(label_bg_x, label_bg_y, text_w, text_h, 4, 4)
            painter.setPen(QPen(QColor(0, 220, 255)))
            painter.drawText(label_bg_x + 5, label_bg_y + 14, info_text)

        # 4. 拖拽裁剪矩形
        if self._drag_rect:
            rx, ry, rw, rh = self._drag_rect
            sx = int(rx * self._scale_factor)
            sy = int(ry * self._scale_factor)
            sw = int(rw * self._scale_factor)
            sh = int(rh * self._scale_factor)

            # 半透明遮罩
            painter.setBrush(QColor(255, 255, 255, 40))
            pen = QPen(QColor(0, 255, 100), 2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(sx, sy, sw, sh)
            # 尺寸标签
            painter.setPen(QPen(QColor(255, 255, 255)))
            font_s = QFont("Consolas", 10, QFont.Bold)
            painter.setFont(font_s)
            label_text = f"{rw}x{rh}"
            label_y = sy - 8 if sy > 20 else sy + sh + 18
            painter.drawText(sx, label_y, sw, 18, Qt.AlignCenter, label_text)

        painter.end()

        # 裁剪显示区
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

    # ── 事件处理 ──
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
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = pos
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and not self._pixmap_original:
            self.upload_requested.emit()
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._pixmap_original:
            if self._scale_factor <= 0:
                return

            orig_x, orig_y = self._widget_to_img(pos.x(), pos.y())

            # 拖拽裁剪模式
            if self._drag_mode:
                self._dragging = True
                self._drag_start = (orig_x, orig_y)
                self._drag_current = (orig_x, orig_y)
                self._drag_rect = (orig_x, orig_y, 0, 0)
                self.drag_started.emit(orig_x, orig_y)
                self._update_display()
                event.accept()
                return

            # 交互式矩形编辑模式
            if self._rect_interactive:
                self._rect_drag_pressed = True
                self._rect_press_pos = (orig_x, orig_y)
                event.accept()
                return

            # 普通点击
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

        # 交互式矩形模式
        if self._rect_interactive and self._pixmap_original and self._scale_factor > 0:
            curr_x, curr_y = self._widget_to_img(pos.x(), pos.y())

            # 按下后开始拖拽（超过阈值）
            if self._rect_drag_pressed and self._rect_press_pos:
                px, py = self._rect_press_pos
                if abs(curr_x - px) > 3 or abs(curr_y - py) > 3:
                    self._start_rect_interact(px, py)
                    self._rect_drag_pressed = False

            # 拖拽中 → 实时更新矩形
            if self._rect_state:
                pw = self._pixmap_original.width()
                ph = self._pixmap_original.height()
                curr_x = max(0, min(curr_x, pw - 1))
                curr_y = max(0, min(curr_y, ph - 1))
                self._do_rect_interact(curr_x, curr_y)
                self._update_display()
                event.accept()
                return
            else:
                # 悬停时切换光标
                action = self._hit_test_rect(curr_x, curr_y)
                cursor_map = {
                    'resize_nw': Qt.SizeFDiagCursor,
                    'resize_se': Qt.SizeFDiagCursor,
                    'resize_ne': Qt.SizeBDiagCursor,
                    'resize_sw': Qt.SizeBDiagCursor,
                    'resize_n': Qt.SizeVerCursor,
                    'resize_s': Qt.SizeVerCursor,
                    'resize_e': Qt.SizeHorCursor,
                    'resize_w': Qt.SizeHorCursor,
                    'move': Qt.SizeAllCursor,
                }
                self.setCursor(cursor_map.get(action, Qt.CrossCursor))

        if self._dragging and self._pixmap_original and self._drag_start:
            # 拖拽中 → 更新矩形
            curr_x, curr_y = self._widget_to_img(pos.x(), pos.y())
            self._drag_current = (curr_x, curr_y)

            sx, sy = self._drag_start
            left = min(sx, curr_x)
            top = min(sy, curr_y)
            right = max(sx, curr_x)
            bottom = max(sy, curr_y)
            w = right - left
            h = bottom - top
            self._drag_rect = (left, top, w, h)
            self.drag_moved.emit(left, top, w, h)
            self._update_display()
            event.accept()
            return

        if self._pixmap_original and self._scale_factor > 0:
            orig_x, orig_y = self._widget_to_img(pos.x(), pos.y())
            if 0 <= orig_x < self._pixmap_original.width() and \
               0 <= orig_y < self._pixmap_original.height():
                self.hovered.emit(orig_x, orig_y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CrossCursor if not self._drag_mode else Qt.CrossCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            if self._drag_rect:
                left, top, w, h = self._drag_rect
                self.drag_finished.emit(left, top, w, h)

                # 执行裁剪
                if w >= 5 and h >= 5 and self._pil_image:
                    try:
                        cropped = self._pil_image.crop(
                            (left, top, left + w, top + h))
                        self.crop_finished.emit(cropped)
                    except Exception:
                        pass

                self._drag_rect = None
                self._drag_start = None
                self._drag_current = None
            event.accept()
            return

        # 交互式矩形释放
        if self._rect_interactive:
            if self._rect_state:
                self._finish_rect_interact()
                event.accept()
                return
            if self._rect_drag_pressed and self._rect_press_pos:
                # 纯点击（无拖拽）→ 保持原有点击行为
                self._rect_drag_pressed = False
                px, py = self._rect_press_pos
                self._rect_press_pos = None
                self.clicked.emit(px, py)
                event.accept()
                return
            self._rect_drag_pressed = False
            self._rect_press_pos = None
            event.accept()
            return

        super().mouseReleaseEvent(event)


# ═══════════════════════════════════════════════════════════
# 取色点表格
# ═══════════════════════════════════════════════════════════

class ColorPointTable(QTableWidget):
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



# ═══════════════════════════════════════════════════════════
# 可双击预览标签
# ═══════════════════════════════════════════════════════════

class ClickablePreviewLabel(QLabel):
    """支持双击查看原图的预览标签"""
    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self.double_clicked.emit()


# ═══════════════════════════════════════════════════════════
# 功能页面基类
# ═══════════════════════════════════════════════════════════

class FeaturePage(QWidget):
    """功能页面基类，提供 log 信号"""
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def log(self, msg):
        self.log_message.emit(msg)


# ═══════════════════════════════════════════════════════════
# 页面 0: 坐标工具
# ═══════════════════════════════════════════════════════════

class CoordToolPage(FeaturePage):
    """坐标工具：截图/上传图片 → 显示黄色标注点 → 手动输入X/Y移动"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── 图片操作 ──
        img_group = QGroupBox("图片")
        img_ops = QHBoxLayout(img_group)
        self._btn_screenshot = QPushButton("📷 截图")
        self._btn_screenshot.setObjectName("btnPrimary")
        self._btn_upload = QPushButton("📁 上传图片")
        self._btn_save = QPushButton("💾 保存")
        self._btn_crop_mode = QPushButton("✂ 裁剪")
        self._btn_crop_mode.setCheckable(True)
        self._btn_crop_mode.setToolTip("激活后在图片上拖拽框选区域进行裁剪")

        self._cb_client = QCheckBox("客户区")
        self._cb_client.setChecked(True)
        img_ops.addWidget(self._btn_screenshot)
        img_ops.addWidget(self._btn_upload)
        img_ops.addWidget(self._btn_save)
        img_ops.addWidget(self._btn_crop_mode)
        img_ops.addWidget(self._cb_client)
        img_ops.addStretch()
        layout.addWidget(img_group)

        # ── 坐标控制 ──
        coord_group = QGroupBox("黄色标注点")
        coord_layout = QVBoxLayout(coord_group)

        # 当前坐标显示
        coord_display = QHBoxLayout()
        self._lbl_marker_pos = QLabel("标注点坐标: (0, 0)")
        self._lbl_marker_pos.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #ffd200; padding: 4px;")
        self._lbl_hover = QLabel("鼠标: (--, --)")
        self._lbl_hover.setStyleSheet("color: #888; padding: 4px;")
        coord_display.addWidget(self._lbl_marker_pos)
        coord_display.addStretch()
        coord_display.addWidget(self._lbl_hover)
        coord_layout.addLayout(coord_display)

        # X / Y 手动输入
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("X:"))
        self._edit_x = QLineEdit("0")
        self._edit_x.setFixedWidth(80)
        self._edit_x.setAlignment(Qt.AlignCenter)
        self._edit_x.setStyleSheet("font-size: 14px; font-weight: bold;")
        input_row.addWidget(self._edit_x)

        input_row.addSpacing(12)
        input_row.addWidget(QLabel("Y:"))
        self._edit_y = QLineEdit("0")
        self._edit_y.setFixedWidth(80)
        self._edit_y.setAlignment(Qt.AlignCenter)
        self._edit_y.setStyleSheet("font-size: 14px; font-weight: bold;")
        input_row.addWidget(self._edit_y)

        self._btn_move = QPushButton("📍 移动标注点")
        self._btn_move.setObjectName("btnPrimary")
        input_row.addSpacing(12)
        input_row.addWidget(self._btn_move)

        self._btn_copy = QPushButton("📋 复制坐标")
        input_row.addWidget(self._btn_copy)
        input_row.addStretch()
        coord_layout.addLayout(input_row)

        layout.addWidget(coord_group)

        # ── 快捷操作 ──
        quick_group = QGroupBox("快捷操作")
        quick_layout = QHBoxLayout(quick_group)
        self._btn_click_marker = QPushButton("🖱 点击标注点")
        self._btn_click_marker.setToolTip("在绑定窗口上点击标注点位置")
        self._btn_right_click_marker = QPushButton("🖱🖱 右键标注点")
        self._btn_right_click_marker.setToolTip("在绑定窗口上右键点击标注点位置")
        quick_layout.addWidget(self._btn_click_marker)
        quick_layout.addWidget(self._btn_right_click_marker)
        quick_layout.addStretch()
        layout.addWidget(quick_group)

        # ── 缩放 ──
        zoom_group = QGroupBox("视图")
        zoom_layout = QHBoxLayout(zoom_group)
        self._btn_zoom_out = QPushButton("🔍-")
        self._btn_zoom_out.setFixedWidth(40)
        self._lbl_zoom = QLabel("100%")
        self._lbl_zoom.setFixedWidth(50)
        self._lbl_zoom.setAlignment(Qt.AlignCenter)
        self._lbl_zoom.setStyleSheet("font-weight: bold; color: #4a9eff;")
        self._btn_zoom_in = QPushButton("🔍+")
        self._btn_zoom_in.setFixedWidth(40)
        self._btn_zoom_fit = QPushButton("📐 适合")
        zoom_layout.addWidget(self._btn_zoom_out)
        zoom_layout.addWidget(self._lbl_zoom)
        zoom_layout.addWidget(self._btn_zoom_in)
        zoom_layout.addWidget(self._btn_zoom_fit)
        zoom_layout.addStretch()
        layout.addWidget(zoom_group)

        # ── 日志 ──
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMinimumHeight(70)
        self._log_text.setFont(QFont("Consolas", 8))
        self._log_text.setPlaceholderText("📍 坐标工具日志...")
        layout.addWidget(self._log_text)


# ═══════════════════════════════════════════════════════════
# 页面 1: 框选定位
# ═══════════════════════════════════════════════════════════

class RectLocatorPage(FeaturePage):
    """框选定位：手动输入 X/Y/W/H，在图片上绘制矩形定位框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── 矩形参数 ──
        rect_group = QGroupBox("矩形定位参数")
        rect_layout = QVBoxLayout(rect_group)

        # 当前矩形信息
        self._lbl_rect_info = QLabel("矩形区域: 未设置")
        self._lbl_rect_info.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #00c8ff; padding: 4px;")
        rect_layout.addWidget(self._lbl_rect_info)

        # X / Y / W / H 输入
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("X:"))
        self._edit_rx = QLineEdit("0")
        self._edit_rx.setFixedWidth(70)
        self._edit_rx.setAlignment(Qt.AlignCenter)
        self._edit_rx.setStyleSheet("font-size: 14px; font-weight: bold;")
        input_row.addWidget(self._edit_rx)

        input_row.addWidget(QLabel("Y:"))
        self._edit_ry = QLineEdit("0")
        self._edit_ry.setFixedWidth(70)
        self._edit_ry.setAlignment(Qt.AlignCenter)
        self._edit_ry.setStyleSheet("font-size: 14px; font-weight: bold;")
        input_row.addWidget(self._edit_ry)

        input_row.addWidget(QLabel("宽:"))
        self._edit_rw = QLineEdit("100")
        self._edit_rw.setFixedWidth(70)
        self._edit_rw.setAlignment(Qt.AlignCenter)
        self._edit_rw.setStyleSheet("font-size: 14px; font-weight: bold;")
        input_row.addWidget(self._edit_rw)

        input_row.addWidget(QLabel("高:"))
        self._edit_rh = QLineEdit("100")
        self._edit_rh.setFixedWidth(70)
        self._edit_rh.setAlignment(Qt.AlignCenter)
        self._edit_rh.setStyleSheet("font-size: 14px; font-weight: bold;")
        input_row.addWidget(self._edit_rh)

        input_row.addStretch()
        rect_layout.addLayout(input_row)

        # 操作按钮
        btn_row = QHBoxLayout()
        self._btn_draw_rect = QPushButton("🔲 绘制矩形框")
        self._btn_draw_rect.setObjectName("btnPrimary")
        self._btn_clear_rect = QPushButton("清空矩形")
        self._btn_copy_rect = QPushButton("📋 复制参数")
        self._btn_click_center = QPushButton("🖱 点击中心")
        self._btn_click_center.setToolTip("点击矩形中心点")
        btn_row.addWidget(self._btn_draw_rect)
        btn_row.addWidget(self._btn_clear_rect)
        btn_row.addWidget(self._btn_copy_rect)
        btn_row.addWidget(self._btn_click_center)
        btn_row.addStretch()
        rect_layout.addLayout(btn_row)

        layout.addWidget(rect_group)

        # ── 图片操作 ──
        img_group = QGroupBox("图片")
        img_ops = QHBoxLayout(img_group)
        self._btn_screenshot = QPushButton("📷 截图")
        self._btn_screenshot.setObjectName("btnPrimary")
        self._btn_upload = QPushButton("📁 上传图片")
        self._btn_save = QPushButton("💾 保存")
        self._btn_crop_mode = QPushButton("✂ 裁剪")
        self._btn_crop_mode.setCheckable(True)
        self._btn_crop_mode.setToolTip("激活后在图片上拖拽框选区域进行裁剪")
        self._cb_client = QCheckBox("客户区")
        self._cb_client.setChecked(True)
        img_ops.addWidget(self._btn_screenshot)
        img_ops.addWidget(self._btn_upload)
        img_ops.addWidget(self._btn_save)
        img_ops.addWidget(self._btn_crop_mode)
        img_ops.addWidget(self._cb_client)
        img_ops.addStretch()
        layout.addWidget(img_group)

        # ── 缩放 ──
        zoom_group = QGroupBox("视图")
        zoom_layout = QHBoxLayout(zoom_group)
        self._btn_zoom_out = QPushButton("🔍-")
        self._btn_zoom_out.setFixedWidth(40)
        self._lbl_zoom = QLabel("100%")
        self._lbl_zoom.setFixedWidth(50)
        self._lbl_zoom.setAlignment(Qt.AlignCenter)
        self._lbl_zoom.setStyleSheet("font-weight: bold; color: #4a9eff;")
        self._btn_zoom_in = QPushButton("🔍+")
        self._btn_zoom_in.setFixedWidth(40)
        self._btn_zoom_fit = QPushButton("📐 适合")
        zoom_layout.addWidget(self._btn_zoom_out)
        zoom_layout.addWidget(self._lbl_zoom)
        zoom_layout.addWidget(self._btn_zoom_in)
        zoom_layout.addWidget(self._btn_zoom_fit)
        zoom_layout.addStretch()
        layout.addWidget(zoom_group)

        # ── 日志 ──
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMinimumHeight(70)
        self._log_text.setFont(QFont("Consolas", 8))
        self._log_text.setPlaceholderText("🔲 框选定位日志...")
        layout.addWidget(self._log_text)




# ═══════════════════════════════════════════════════════════
# 页面 2: 取色验证
# ═══════════════════════════════════════════════════════════

class ColorVerifyPage(FeaturePage):
    """取色验证页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

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
        layout.addWidget(points_group)

        verify_group = QGroupBox("颜色验证")
        verify_layout = QVBoxLayout(verify_group)
        verify_row1 = QHBoxLayout()
        verify_row1.addWidget(QLabel("容差:"))
        self._spin_tolerance = QSpinBox()
        self._spin_tolerance.setRange(0, 100)
        self._spin_tolerance.setValue(5)
        verify_row1.addWidget(self._spin_tolerance)
        verify_row1.addWidget(QLabel("搜索范围:"))
        self._spin_scope = QSpinBox()
        self._spin_scope.setRange(0, 200)
        self._spin_scope.setValue(15)
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
        layout.addWidget(verify_group)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMinimumHeight(70)
        self._log_text.setFont(QFont("Consolas", 8))
        self._log_text.setPlaceholderText("🎨 取色验证日志...")
        layout.addWidget(self._log_text)


# ═══════════════════════════════════════════════════════════
# 页面 3: 模板匹配
# ═══════════════════════════════════════════════════════════


class TemplateMatchPage(FeaturePage):
    """图片定位（模板匹配）页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        tmpl_group = QGroupBox("模板选取")
        tmpl_layout = QHBoxLayout(tmpl_group)
        tmpl_layout.setSpacing(8)

        # 左侧：按钮 + 提示
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(0, 0, 0, 0)

        btn_rows = QVBoxLayout()
        btn_rows.setSpacing(6)
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self._btn_pick_template = QPushButton("🎯 截图选模板")
        self._btn_pick_template.setCheckable(True)
        self._btn_paste_template = QPushButton("📋 粘贴模板")
        self._btn_load_template = QPushButton("📁 加载图片")
        row1.addWidget(self._btn_pick_template)
        row1.addWidget(self._btn_paste_template)
        row1.addWidget(self._btn_load_template)
        row1.addStretch()
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        self._btn_clear_template = QPushButton("清空")
        self._btn_save_template = QPushButton("💾 保存模板")
        self._btn_save_template.setEnabled(False)
        row2.addWidget(self._btn_clear_template)
        row2.addWidget(self._btn_save_template)
        row2.addStretch()
        btn_rows.addLayout(row1)
        btn_rows.addLayout(row2)
        left_layout.addLayout(btn_rows)

        self._lbl_template_hint = QLabel("未选取模板")
        self._lbl_template_hint.setStyleSheet("color: #888;")
        left_layout.addWidget(self._lbl_template_hint)
        left_layout.addStretch()

        tmpl_layout.addLayout(left_layout, 1)
        tmpl_layout.addStretch(1)

        # 右侧：模板预览
        self._lbl_template_preview = ClickablePreviewLabel()
        self._lbl_template_preview.setFixedSize(120, 90)
        self._lbl_template_preview.setToolTip("双击查看原图")
        self._lbl_template_preview.setAlignment(Qt.AlignCenter)
        self._lbl_template_preview.setStyleSheet(
            "background-color: #222; border: 1px solid #555;")
        tmpl_layout.addWidget(self._lbl_template_preview)

        layout.addWidget(tmpl_group)


        match_settings = QGroupBox("匹配设置")
        ms_layout = QVBoxLayout(match_settings)
        ms_row = QHBoxLayout()
        ms_row.addWidget(QLabel("相似度阈值:"))
        self._spin_match_thresh = QSpinBox()
        self._spin_match_thresh.setRange(50, 99)
        self._spin_match_thresh.setValue(75)
        self._spin_match_thresh.setSuffix("%")
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
        layout.addWidget(match_settings)

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
        layout.addLayout(match_act)

        result_group = QGroupBox("匹配结果")
        result_layout = QVBoxLayout(result_group)
        self._table_matches = QTableWidget()
        self._table_matches.setColumnCount(7)
        self._table_matches.setHorizontalHeaderLabels(
            ["#", "X", "Y", "宽", "高", "中心坐标", "相似度"])
        mh = self._table_matches.horizontalHeader()
        mh.setSectionResizeMode(0, QHeaderView.Fixed)
        mh.setSectionResizeMode(1, QHeaderView.Fixed)
        mh.setSectionResizeMode(2, QHeaderView.Fixed)
        mh.setSectionResizeMode(3, QHeaderView.Fixed)
        mh.setSectionResizeMode(4, QHeaderView.Fixed)
        mh.setSectionResizeMode(5, QHeaderView.Stretch)
        mh.setSectionResizeMode(6, QHeaderView.Fixed)
        self._table_matches.setColumnWidth(0, 30)
        self._table_matches.setColumnWidth(1, 48)
        self._table_matches.setColumnWidth(2, 48)
        self._table_matches.setColumnWidth(3, 40)
        self._table_matches.setColumnWidth(4, 40)
        self._table_matches.setColumnWidth(6, 52)
        self._table_matches.setSelectionBehavior(QTableWidget.SelectRows)
        self._table_matches.setAlternatingRowColors(True)
        self._table_matches.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_matches.verticalHeader().setVisible(False)
        result_btns = QHBoxLayout()
        self._btn_click_match = QPushButton("🖱 点击选中位置")
        self._btn_copy_match = QPushButton("复制全部坐标")
        self._btn_clear_matches = QPushButton("清空结果")
        result_btns.addWidget(self._btn_click_match)
        result_btns.addWidget(self._btn_copy_match)
        result_btns.addWidget(self._btn_clear_matches)
        result_btns.addStretch()
        result_layout.addWidget(self._table_matches)
        result_layout.addLayout(result_btns)
        layout.addWidget(result_group)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMinimumHeight(70)
        self._log_text.setFont(QFont("Consolas", 8))
        self._log_text.setPlaceholderText("🔍 图片定位日志...")
        layout.addWidget(self._log_text)




# ═══════════════════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """主窗口 - 左侧导航 + 右侧操作"""

    NAV_COORD = 0
    NAV_RECT = 1
    NAV_COLOR = 2
    NAV_MATCH = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("窗口辅助工具 v2.0")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        self.binder = WindowBinder(self)
        self.capture = ScreenCapture(self)
        self.picker = ColorPicker(self)
        self.verifier = ColorVerifier(self)
        self.tracker = CoordinateTracker(self)
        self.matcher = TemplateMatcher(threshold=0.75, max_results=20)
        self._saved_coords = []
        self._template_image = None
        self._template_crop_active = False
        self._match_original_img = None
        self._match_results = []
        self.adb_scanner = AdbScanner(self)
        self._adb_serial = None

        self._setup_ui()
        self._setup_connections()
        self._setup_menus()

        QTimer.singleShot(300, self.binder.enumerate_windows)

    # ═══ UI 构建 ═══

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── 顶部窗口绑定 ──
        bind_group = QGroupBox("窗口绑定")
        bind_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bind_layout = QHBoxLayout(bind_group)
        bind_layout.setContentsMargins(8, 10, 8, 10)

        self._btn_refresh = QPushButton("🔄 刷新列表")
        self._combo_windows = QComboBox()
        self._combo_windows.setMinimumWidth(300)
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
        self._btn_adb = QPushButton("绑定设备")

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

        # ── 主体：左侧导航 + 右侧操作 ──
        body_splitter = QSplitter(Qt.Horizontal)

        # 左侧：导航列表
        left_panel = QWidget()
        left_panel.setFixedWidth(180)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 导航标题
        nav_title = QLabel("  功能导航")
        nav_title.setStyleSheet(
            "background-color: #222; color: #aaa; font-size: 13px; "
            "font-weight: bold; padding: 10px 14px; border-bottom: 1px solid #444;")
        left_layout.addWidget(nav_title)

        self._nav_list = QListWidget()
        self._nav_list.addItem("📍 坐标工具")
        self._nav_list.addItem("🔲 框选定位")
        self._nav_list.addItem("🎨 取色验证")
        self._nav_list.addItem("🔍 模板匹配")
        self._nav_list.setCurrentRow(0)
        self._nav_list.setSpacing(0)
        left_layout.addWidget(self._nav_list)

        body_splitter.addWidget(left_panel)

        # 中间：图片预览
        self._screenshot_label = ClickableLabel()
        self._screenshot_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body_splitter.addWidget(self._screenshot_label)

        # 右侧：操作面板 QStackedWidget
        right_panel = QWidget()
        right_panel.setMinimumWidth(440)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._stack = QStackedWidget()

        # 页面 0: 坐标工具
        self._page_coord = CoordToolPage()
        self._stack.addWidget(self._page_coord)

        # 页面 1: 框选定位
        self._page_rect = RectLocatorPage()
        self._stack.addWidget(self._page_rect)

        # 页面 2: 取色验证
        self._page_color = ColorVerifyPage()
        self._stack.addWidget(self._page_color)

        # 页面 3: 模板匹配
        self._page_match = TemplateMatchPage()
        self._stack.addWidget(self._page_match)

        right_layout.addWidget(self._stack)
        body_splitter.addWidget(right_panel)

        body_splitter.setStretchFactor(0, 0)
        body_splitter.setStretchFactor(1, 1)
        body_splitter.setStretchFactor(2, 0)
        main_layout.addWidget(body_splitter)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("就绪")
        self._status_bar.addWidget(self._status_label)

    # ═══ 信号连接 ═══

    def _setup_connections(self):
        # 导航切换
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)

        # 窗口绑定
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

        # 截图
        self.capture.screenshot_taken.connect(self._on_screenshot)
        self.capture.screenshot_error.connect(self._log)

        # ClickableLabel
        self._screenshot_label.hovered.connect(self._on_preview_hovered)
        self._screenshot_label.clicked.connect(self._on_preview_clicked)
        self._screenshot_label.zoom_changed.connect(self._on_zoom_changed)
        self._screenshot_label.crop_finished.connect(self._on_crop_finished)
        self._screenshot_label.rect_finalized.connect(self._on_rect_finalized)
        self._screenshot_label.rect_changed.connect(self._on_rect_changed)
        self._screenshot_label.upload_requested.connect(self._on_upload_image)

        # ── 坐标工具页面连接 ──
        p = self._page_coord
        p._btn_screenshot.clicked.connect(self._on_full_screenshot)
        p._btn_upload.clicked.connect(self._on_upload_image)
        p._btn_save.clicked.connect(self._on_save_screenshot)
        p._btn_crop_mode.toggled.connect(
            lambda v: self._screenshot_label.set_drag_mode(v))
        p._btn_move.clicked.connect(self._on_move_marker)
        p._btn_copy.clicked.connect(self._on_copy_marker)
        p._btn_click_marker.clicked.connect(
            lambda: self._on_click_marker(False))
        p._btn_right_click_marker.clicked.connect(
            lambda: self._on_click_marker(True))
        p._btn_zoom_in.clicked.connect(self._screenshot_label.zoom_in)
        p._btn_zoom_out.clicked.connect(self._screenshot_label.zoom_out)
        p._btn_zoom_fit.clicked.connect(self._screenshot_label.zoom_fit)
        p._edit_x.textChanged.connect(self._on_marker_input_changed)
        p._edit_y.textChanged.connect(self._on_marker_input_changed)

        # ── 框选定位页面连接 ──
        r = self._page_rect
        r._btn_screenshot.clicked.connect(self._on_full_screenshot)
        r._btn_upload.clicked.connect(self._on_upload_image)
        r._btn_save.clicked.connect(self._on_save_screenshot)
        r._btn_crop_mode.toggled.connect(
            lambda v: self._screenshot_label.set_drag_mode(v))
        r._btn_draw_rect.clicked.connect(self._on_draw_rect)
        r._btn_clear_rect.clicked.connect(self._on_clear_rect)
        r._btn_copy_rect.clicked.connect(self._on_copy_rect_params)
        r._btn_click_center.clicked.connect(self._on_click_rect_center)
        r._btn_zoom_in.clicked.connect(self._screenshot_label.zoom_in)
        r._btn_zoom_out.clicked.connect(self._screenshot_label.zoom_out)
        r._btn_zoom_fit.clicked.connect(self._screenshot_label.zoom_fit)

        # ── 取色验证页面连接 ──
        cv = self._page_color
        cv._btn_delete_pt.clicked.connect(self._on_delete_points)
        cv._btn_clear_pt.clicked.connect(self._on_clear_points)
        cv._btn_copy_json.clicked.connect(lambda: self._copy_points("json"))
        cv._btn_copy_csv.clicked.connect(lambda: self._copy_points("csv"))
        cv._btn_paste.clicked.connect(self._on_paste_points)
        cv._btn_verify.clicked.connect(self._on_verify)
        cv._spin_tolerance.valueChanged.connect(
            lambda v: setattr(self.verifier, 'tolerance', v))
        cv._spin_scope.valueChanged.connect(
            lambda v: setattr(self.verifier, 'search_scope', v))
        cv._table_points.points_deleted.connect(
            lambda indices: self.picker.remove_selected(indices))
        self.picker.list_changed.connect(self._update_points_table)
        self.verifier.verification_done.connect(self._on_verify_done)
        self.verifier.verification_error.connect(self._log)

        # ── 模板匹配页面连接 ──
        tm = self._page_match
        tm._btn_pick_template.toggled.connect(self._on_toggle_template_pick)
        tm._btn_paste_template.clicked.connect(self._on_paste_template)
        tm._btn_load_template.clicked.connect(self._on_load_template)
        tm._btn_clear_template.clicked.connect(self._on_clear_template)
        tm._btn_save_template.clicked.connect(self._on_save_template)
        tm._btn_match.clicked.connect(self._on_match_template)
        tm._btn_click_match.clicked.connect(self._on_click_match_result)
        tm._btn_copy_match.clicked.connect(self._on_copy_match_results)
        tm._btn_clear_matches.clicked.connect(self._on_clear_match_results)
        tm._lbl_template_preview.double_clicked.connect(self._on_view_template_full)
        tm._spin_match_thresh.valueChanged.connect(
            lambda v: setattr(self.matcher, 'threshold', v / 100.0))
        tm._spin_max_results.valueChanged.connect(
            lambda v: setattr(self.matcher, 'max_results', v))

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
            "窗口辅助工具 v2.0\n\n"
            "功能：坐标工具 · 框选定位 · 取色验证 · 图片定位\n\n"
            "基于 PySide6 构建"))
        help_menu.addAction(act_about)

    # ═══ 导航切换 ═══

    def _on_nav_changed(self, index: int):
        prev = self._stack.currentIndex()
        self._stack.setCurrentIndex(index)
        # 切换页面时清除裁剪模式
        self._screenshot_label.set_drag_mode(False)
        self._page_coord._btn_crop_mode.setChecked(False)
        self._page_rect._btn_crop_mode.setChecked(False)
        # 模板裁剪模式：离开模板匹配页时取消
        if prev == self.NAV_MATCH and self._template_crop_active:
            self._template_crop_active = False
            self._page_match._btn_pick_template.setChecked(False)
            self._page_match._lbl_template_hint.setText(
                "未选取模板" if self._template_image is None else "模板已就绪")
            self._page_match._lbl_template_hint.setStyleSheet(
                "color: #4a9eff;" if self._template_image else "color: #888;")
        # 交互式矩形编辑：仅在框选定位页启用
        self._screenshot_label.set_rect_interactive(index == self.NAV_RECT)
        # 清除矩形定位框（非框选定位页时）
        if index != self.NAV_RECT:
            self._screenshot_label.clear_locator()
        # 黄色标注点仅在坐标工具页生效，离开时清除，进入时恢复
        if prev == self.NAV_COORD and index != self.NAV_COORD:
            self._screenshot_label.clear_marker()
        elif index == self.NAV_COORD:
            try:
                mx = int(self._page_coord._edit_x.text())
                my = int(self._page_coord._edit_y.text())
                self._screenshot_label.set_marker_point(mx, my)
            except (ValueError, AttributeError):
                self._screenshot_label.clear_marker()

        names = ["坐标工具", "框选定位", "取色验证", "模板匹配"]
        if 0 <= index < len(names):
            self._log(f"切换到: {names[index]}")

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

    def _on_unbound(self):
        self._btn_bind.setEnabled(True)
        self._btn_unbind.setEnabled(False)
        self._lbl_bound_info.setText("未绑定窗口")
        self._lbl_bound_info.setStyleSheet("color: #888; padding: 0 8px;")
        self.tracker.stop_tracking()

    def _on_unbind_window(self):
        self.binder.unbind_window()

    # ═══ 截图 / 上传 ═══

    def _on_full_screenshot(self):
        if self._adb_serial:
            self._log(f"正在通过 ADB 截取设备 {self._adb_serial} 画面...")
            try:
                from adbutils import adb
                d = adb.device(self._adb_serial)
                data = d.screenshot()
                if data:
                    self.capture._cached_image = data
                    self.capture.screenshot_taken.emit(data)
                    return
                else:
                    self._log("ADB 截图返回空，回退到窗口截图")
            except Exception as e:
                self._log(f"ADB 截图失败: {e}，回退到窗口截图")

        if not self.binder.is_bound:
            self._log("请先绑定目标窗口")
            QMessageBox.warning(self, "提示", "请先绑定目标窗口")
            return

        self._log("正在截取窗口...")
        client_area = True
        # 根据当前页面判断用哪个 cb_client
        nav = self._nav_list.currentRow()
        if nav == self.NAV_COORD:
            client_area = self._page_coord._cb_client.isChecked()
        elif nav == self.NAV_RECT:
            client_area = self._page_rect._cb_client.isChecked()
        else:
            client_area = True

        img = self.capture.capture_window(
            self.binder.target_window.hwnd, client_area=client_area)
        if img:
            self.capture.screenshot_taken.emit(img)
        else:
            self._log("截图失败！")

    def _on_screenshot(self, img):
        buf = BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg)
        self._screenshot_label.set_image(pixmap, pil_img=img.copy())
        self._log(f"截图成功: {img.width}x{img.height}")

        # 根据当前页面初始化标注/矩形
        nav = self._nav_list.currentRow()
        if nav == self.NAV_COORD:
            cx, cy = img.width // 2, img.height // 2
            self._screenshot_label.set_marker_point(cx, cy)
            self._page_coord._edit_x.setText(str(cx))
            self._page_coord._edit_y.setText(str(cy))
        elif nav == self.NAV_RECT:
            # 截图后自动根据输入值绘制矩形框
            try:
                rx = int(self._page_rect._edit_rx.text())
                ry = int(self._page_rect._edit_ry.text())
                rw = int(self._page_rect._edit_rw.text())
                rh = int(self._page_rect._edit_rh.text())
                if rw > 0 and rh > 0:
                    rx = max(0, min(rx, img.width - 1))
                    ry = max(0, min(ry, img.height - 1))
                    rw = min(rw, img.width - rx)
                    rh = min(rh, img.height - ry)
                    self._screenshot_label.set_locator_rect(rx, ry, rw, rh)
                    self._page_rect._lbl_rect_info.setText(
                        f"矩形区域: ({rx}, {ry}) {rw}x{rh}")
            except ValueError:
                pass

    def _on_upload_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "上传图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)")
        if not path:
            return
        try:
            img = PILImage.open(path)
            if img.width < 5 or img.height < 5:
                QMessageBox.warning(self, "提示", "图片太小")
                return
            img = img.convert('RGB')
            self.capture._cached_image = img
            self.capture.screenshot_taken.emit(img)
            self._log(f"已加载图片: {os.path.basename(path)} ({img.width}x{img.height})")
        except Exception as e:
            self._log(f"加载图片失败: {e}")

    def _on_save_screenshot(self):
        img = self.capture.cached_image
        if img is None:
            QMessageBox.warning(self, "提示", "没有可保存的截图")
            return
        from datetime import datetime
        default_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存截图", default_name,
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;所有文件 (*.*)")
        if not filepath:
            return
        ext = os.path.splitext(filepath)[1].lower()
        fmt_map = {".jpg": "JPEG", ".jpeg": "JPEG", ".bmp": "BMP", ".png": "PNG"}
        save_format = fmt_map.get(ext, "PNG")
        try:
            img.save(filepath, save_format)
            self._log("截图已保存: " + filepath)
        except Exception as e:
            QMessageBox.warning(self, "保存失败", "保存截图失败:\n" + str(e))

    # ═══ 拖拽裁剪 ═══

    def _on_crop_finished(self, cropped_img):
        """拖拽裁剪完成"""
        if cropped_img is None:
            return

        # 模板匹配页截图选模：将裁剪结果作为模板，不替换主图
        if self._template_crop_active:
            self._template_crop_active = False
            self._screenshot_label.set_drag_mode(False)
            self._page_match._btn_pick_template.setChecked(False)
            self._template_image = cropped_img
            # 恢复原始截图（裁剪操作已从 label 的 _pil_image 中切出，需还原）
            orig = self.capture.cached_image
            buf = BytesIO()
            orig.save(buf, format="PNG")
            qimg = QImage()
            qimg.loadFromData(buf.getvalue())
            pixmap = QPixmap.fromImage(qimg)
            self._screenshot_label.set_image(pixmap, pil_img=orig.copy())
            # 更新模板预览
            self._update_template_preview()
            self._page_match._btn_match.setEnabled(True)
            self._page_match._lbl_template_hint.setText(
                f"模板: {cropped_img.width}x{cropped_img.height} 就绪")
            self._page_match._lbl_template_hint.setStyleSheet(
                "color: #4aff4a; font-weight: bold;")
            self._log(f"模板已选取: {cropped_img.width}x{cropped_img.height}")
            return

        self.capture._cached_image = cropped_img
        buf = BytesIO()
        cropped_img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg)
        self._screenshot_label.set_image(pixmap, pil_img=cropped_img.copy())
        self._screenshot_label.set_drag_mode(False)

        # 重置裁剪按钮状态
        self._page_coord._btn_crop_mode.setChecked(False)
        self._page_rect._btn_crop_mode.setChecked(False)

        # 更新标注点到新图片中心
        cx, cy = cropped_img.width // 2, cropped_img.height // 2
        self._screenshot_label.set_marker_point(cx, cy)
        self._page_coord._edit_x.setText(str(cx))
        self._page_coord._edit_y.setText(str(cy))
        self._log(f"裁剪完成: {cropped_img.width}x{cropped_img.height}")

    # ═══ 缩放 ═══

    def _on_zoom_changed(self, factor: float):
        pct = int(factor * 100)
        self._page_coord._lbl_zoom.setText(f"{pct}%")
        self._page_rect._lbl_zoom.setText(f"{pct}%")

    # ═══ 预览交互 ═══

    def _on_preview_hovered(self, x: int, y: int):
        nav = self._nav_list.currentRow()
        if nav == self.NAV_COORD:
            self._page_coord._lbl_hover.setText(f"鼠标: ({x}, {y})")

    def _on_preview_clicked(self, x: int, y: int):
        nav = self._nav_list.currentRow()
        if nav == self.NAV_COLOR:
            self._on_pick_color(x, y)
        elif nav == self.NAV_MATCH:
            pass  # 模板匹配页使用拖拽选取，单击不处理
        elif nav == self.NAV_COORD:
            # 点击图片 → 移动标注点
            self._move_marker_to(x, y)
        elif nav == self.NAV_RECT:
            # 点击图片 → 移动矩形定位框起始点
            self._move_rect_to(x, y)

    # ═══ 坐标工具：黄色标注点 ═══

    def _move_marker_to(self, x: int, y: int):
        self._screenshot_label.set_marker_point(x, y)
        self._page_coord._edit_x.setText(str(x))
        self._page_coord._edit_y.setText(str(y))

    def _on_move_marker(self):
        try:
            x = int(self._page_coord._edit_x.text())
            y = int(self._page_coord._edit_y.text())
        except ValueError:
            self._log("请输入有效的整数坐标")
            return
        img = self.capture.cached_image
        if img:
            x = max(0, min(x, img.width - 1))
            y = max(0, min(y, img.height - 1))
        self._screenshot_label.set_marker_point(x, y)
        self._page_coord._edit_x.setText(str(x))
        self._page_coord._edit_y.setText(str(y))
        self._log(f"标注点移动到: ({x}, {y})")

    def _on_marker_input_changed(self):
        """输入变化时实时更新标注点"""
        try:
            x = int(self._page_coord._edit_x.text())
            y = int(self._page_coord._edit_y.text())
            img = self.capture.cached_image
            if img:
                x = max(0, min(x, img.width - 1))
                y = max(0, min(y, img.height - 1))
            self._screenshot_label.set_marker_point(x, y)
        except ValueError:
            pass

    def _on_copy_marker(self):
        pt = self._screenshot_label.get_marker_point()
        if pt:
            text = f"({pt[0]}, {pt[1]})"
            QApplication.clipboard().setText(text)
            self._log(f"已复制坐标: {text}")

    def _on_click_marker(self, right_click=False):
        pt = self._screenshot_label.get_marker_point()
        if not pt:
            self._log("没有标注点")
            return
        if right_click:
            import win32api, win32con
            if self.binder.is_bound:
                from modules.window_binder import get_window_rect_screen
                rect = get_window_rect_screen(self.binder.target_window.hwnd)
                tx, ty = rect[0] + pt[0], rect[1] + pt[1]
            else:
                tx, ty = pt[0], pt[1]
            win32api.SetCursorPos((tx, ty))
            time.sleep(0.02)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(0.02)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            self._log(f"右键点击: ({pt[0]}, {pt[1]})")
        else:
            self.tracker.test_click(pt[0], pt[1], double_click=False)
            self._log(f"点击标注点: ({pt[0]}, {pt[1]})")

    # ═══ 框选定位 ═══

    def _move_rect_to(self, x: int, y: int):
        """点击图片移动矩形框起始点（保持宽高不变）"""
        old = self._screenshot_label._locator_rect
        if old:
            w, h = old[2], old[3]
        else:
            w, h = 100, 100
        img = self.capture.cached_image
        if img:
            x = max(0, min(x, img.width - w))
            y = max(0, min(y, img.height - h))
        self._screenshot_label.set_locator_rect(x, y, w, h)
        self._page_rect._edit_rx.setText(str(x))
        self._page_rect._edit_ry.setText(str(y))
        self._page_rect._edit_rw.setText(str(w))
        self._page_rect._edit_rh.setText(str(h))
        self._page_rect._lbl_rect_info.setText(
            f"矩形区域: ({x}, {y}) {w}x{h}")

    def _on_draw_rect(self):
        try:
            x = int(self._page_rect._edit_rx.text())
            y = int(self._page_rect._edit_ry.text())
            w = int(self._page_rect._edit_rw.text())
            h = int(self._page_rect._edit_rh.text())
        except ValueError:
            self._log("请输入有效的整数")
            return
        if w <= 0 or h <= 0:
            self._log("宽高必须大于0")
            return
        img = self.capture.cached_image
        if img:
            x = max(0, min(x, img.width - 1))
            y = max(0, min(y, img.height - 1))
            w = min(w, img.width - x)
            h = min(h, img.height - y)
        self._screenshot_label.set_locator_rect(x, y, w, h)
        self._page_rect._lbl_rect_info.setText(
            f"矩形区域: ({x}, {y}) {w}x{h}")
        self._log(f"绘制矩形框: ({x}, {y}) {w}x{h}")

    def _on_clear_rect(self):
        self._screenshot_label.clear_locator()
        self._page_rect._lbl_rect_info.setText("矩形区域: 未设置")
        self._log("已清空矩形框")

    def _on_copy_rect_params(self):
        r = self._screenshot_label._locator_rect
        if r:
            text = f"x={r[0]} y={r[1]} w={r[2]} h={r[3]}"
        else:
            try:
                x = self._page_rect._edit_rx.text()
                y = self._page_rect._edit_ry.text()
                w = self._page_rect._edit_rw.text()
                h = self._page_rect._edit_rh.text()
                text = f"x={x} y={y} w={w} h={h}"
            except:
                text = ""
        if text:
            QApplication.clipboard().setText(text)
            self._log(f"已复制矩形参数: {text}")

    def _on_rect_finalized(self, x: int, y: int, w: int, h: int):
        """拖拽矩形完成 → 同步输入框和标签"""
        self._page_rect._edit_rx.setText(str(x))
        self._page_rect._edit_ry.setText(str(y))
        self._page_rect._edit_rw.setText(str(w))
        self._page_rect._edit_rh.setText(str(h))
        self._page_rect._lbl_rect_info.setText(
            f"矩形区域: ({x}, {y}) {w}x{h}")
        self._log(f"矩形定位完成: ({x}, {y}) {w}x{h}")

    def _on_rect_changed(self, x: int, y: int, w: int, h: int):
        """拖拽中实时更新输入框"""
        self._page_rect._edit_rx.setText(str(x))
        self._page_rect._edit_ry.setText(str(y))
        self._page_rect._edit_rw.setText(str(w))
        self._page_rect._edit_rh.setText(str(h))
        self._page_rect._lbl_rect_info.setText(
            f"矩形区域: ({x}, {y}) {w}x{h}")

    def _on_click_rect_center(self):
        r = self._screenshot_label._locator_rect
        if not r:
            # 尝试从输入框读取
            try:
                x = int(self._page_rect._edit_rx.text())
                y = int(self._page_rect._edit_ry.text())
                w = int(self._page_rect._edit_rw.text())
                h = int(self._page_rect._edit_rh.text())
            except ValueError:
                QMessageBox.warning(self, "提示", "请先绘制矩形或输入有效参数")
                return
        else:
            x, y, w, h = r

        cx, cy = x + w // 2, y + h // 2
        self.tracker.test_click(cx, cy, double_click=False)
        self._log(f"点击矩形中心: ({cx}, {cy})")

    # ═══ 取色 ═══

    def _on_pick_color(self, x, y):
        img = self.capture.cached_image
        if img is None:
            self._log("请先截图")
            return
        point = self.picker.pick_color(x, y, img)
        if point:
            self._log(f"取色: ({x},{y}) RGB{point.rgb_str} {point.hex_color}")

    def _update_points_table(self):
        self._page_color._table_points.set_points(self.picker.get_points())

    def _on_delete_points(self):
        rows = set()
        for item in self._page_color._table_points.selectedItems():
            rows.add(item.row())
        if rows:
            indices = [int(self._page_color._table_points.item(r, 0).text())
                       for r in rows]
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
            self.binder.target_window.hwnd, client_area=True)
        if img is None:
            self._log("截图失败，无法验证")
            return
        self._on_screenshot(img)
        self._page_color._lbl_verify_result.setText("验证中...")
        self._page_color._btn_verify.setEnabled(False)
        self.verifier.verify_async(img, self.picker.get_points())

    def _on_verify_done(self, results, annotated):
        self._page_color._btn_verify.setEnabled(True)
        found_count = sum(1 for r in results if r["found"])
        total = len(results)
        self._page_color._lbl_verify_result.setText(
            f"结果: {found_count}/{total} 匹配 "
            f"(容差={self.verifier.tolerance} 范围=±{self.verifier.search_scope})")
        color = "#4aff4a" if found_count == total else \
                "#ffaa44" if found_count > 0 else "#ff4444"
        self._page_color._lbl_verify_result.setStyleSheet(
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

    # ═══ 模板匹配 ═══

    def _on_toggle_template_pick(self, checked):
        if checked:
            if self.capture.cached_image is None:
                self._page_match._btn_pick_template.setChecked(False)
                self._log("请先截图，再选取模板")
                QMessageBox.warning(self, "提示", "请先执行完整截图")
                return
            self._template_crop_active = True
            self._screenshot_label.set_drag_mode(True)
            self._page_match._lbl_template_hint.setText("拖动鼠标框选模板区域...")
            self._page_match._lbl_template_hint.setStyleSheet(
                "color: #ffaa00; font-weight: bold;")
        else:
            self._template_crop_active = False
            self._screenshot_label.set_drag_mode(False)
            self._page_match._lbl_template_hint.setText(
                "未选取模板" if self._template_image is None else "模板已就绪")
            self._page_match._lbl_template_hint.setStyleSheet(
                "color: #4a9eff;" if self._template_image else "color: #888;")

    def _update_template_preview(self):
        if self._template_image is None:
            self._page_match._lbl_template_preview.clear()
            self._page_match._lbl_template_preview.setText("无")
            self._page_match._btn_save_template.setEnabled(False)
            return
        self._page_match._btn_save_template.setEnabled(True)
        img = self._template_image.copy()
        img.thumbnail((96, 76))
        if img.mode == "RGBA":
            qimg = QImage(img.tobytes("raw", "RGBA"),
                           img.width, img.height, QImage.Format_RGBA8888)
        else:
            qimg = QImage(img.tobytes("raw", "RGB"),
                           img.width, img.height, QImage.Format_RGB888)
        # 保持比例缩放，裁剪边缘以填满预览区域
        preview_label = self._page_match._lbl_template_preview
        preview_size = preview_label.size()
        pixmap = QPixmap.fromImage(qimg).scaled(
            preview_size.width(), preview_size.height(),
            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        preview_label.setPixmap(pixmap)


    def _on_load_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "加载模板图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)")
        if not path:
            return
        try:
            img = PILImage.open(path)
            if img.width < 5 or img.height < 5:
                QMessageBox.warning(self, "提示", "图片太小")
                return
            dpr = QApplication.instance().primaryScreen().devicePixelRatio()
            if dpr > 1.001:
                new_w = int(img.width / dpr)
                new_h = int(img.height / dpr)
                img = img.resize((new_w, new_h), PILImage.LANCZOS)
            self._template_image = img.convert('RGB')
            self._update_template_preview()
            self._page_match._btn_match.setEnabled(True)
            self._page_match._lbl_template_hint.setText(
                f"模板: {img.width}x{img.height} (文件) ✅")
            self._page_match._lbl_template_hint.setStyleSheet(
                "color: #4aff4a; font-weight: bold;")
            self._log(f"已加载模板图片: {os.path.basename(path)} ({img.width}x{img.height})")
        except Exception as e:
            self._log(f"加载模板失败: {e}")

    def _on_save_template(self):
        if self._template_image is None:
            QMessageBox.warning(self, "提示", "没有可保存的模板")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存模板图片", "",
            "PNG 图片 (*.png);;JPEG 图片 (*.jpg);;所有文件 (*.*)")
        if not path:
            return
        try:
            save_img = self._template_image
            if path.lower().endswith(".jpg") or path.lower().endswith(".jpeg"):
                if save_img.mode == "RGBA":
                    save_img = save_img.convert("RGB")
            save_img.save(path)
            self._page_match._lbl_template_hint.setText(f"已保存: {os.path.basename(path)}")
            self._page_match._lbl_template_hint.setStyleSheet("color: #4aff4a;")
            self._log(f"模板已保存: {path}")
        except Exception as e:
            self._log(f"保存模板失败: {e}")
            QMessageBox.warning(self, "保存失败", f"保存模板失败:\n{e}")

    def _on_view_template_full(self):
        """双击模板预览，弹窗查看原图"""
        if self._template_image is None:
            return
        img = self._template_image
        # 限制弹窗最大尺寸
        screen = QApplication.primaryScreen()
        if screen:
            max_w = int(screen.geometry().width() * 0.75)
            max_h = int(screen.geometry().height() * 0.75)
        else:
            max_w, max_h = 1200, 900
        display = img.copy()
        if img.width > max_w or img.height > max_h:
            ratio = min(max_w / img.width, max_h / img.height)
            display = img.resize(
                (int(img.width * ratio), int(img.height * ratio)),
                PILImage.LANCZOS)
        buf = BytesIO()
        display.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"模板原图 ({img.width}x{img.height})")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowMaximizeButtonHint)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel()
        lbl.setPixmap(pixmap)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background-color: #111;")
        layout.addWidget(lbl)
        dlg.resize(pixmap.width() + 4, pixmap.height() + 4)
        dlg.exec()

    def _on_paste_template(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasImage():
            qimg = clipboard.image()
            if qimg.isNull():
                self._log("剪贴板中无有效图片")
                QMessageBox.warning(self, "提示", "剪贴板中没有图片数据")
                return
            qimg = qimg.convertToFormat(QImage.Format_RGBA8888)
            width, height = qimg.width(), qimg.height()
            ptr = qimg.bits()
            img = PILImage.frombytes("RGBA", (width, height),
                                     bytes(ptr), "raw", "RGBA")
        else:
            self._log("剪贴板中无图片")
            QMessageBox.warning(
                self, "提示",
                "剪贴板中没有图片。\n\n请在QQ/微信中截图后按 Ctrl+C 复制，再点击此按钮。")
            return
        if img.width < 5 or img.height < 5:
            QMessageBox.warning(self, "提示", "图片太小")
            return
        dpr = QApplication.instance().primaryScreen().devicePixelRatio()
        if dpr > 1.001:
            new_w = int(img.width / dpr)
            new_h = int(img.height / dpr)
            img = img.resize((new_w, new_h), PILImage.LANCZOS)
        self._template_image = img.convert('RGB')
        self._update_template_preview()
        self._page_match._btn_match.setEnabled(True)
        self._page_match._lbl_template_hint.setText(
            f"模板: {img.width}x{img.height} (粘贴) ✅")
        self._page_match._lbl_template_hint.setStyleSheet(
            "color: #4aff4a; font-weight: bold;")
        self._log(f"已从剪贴板粘贴模板: {img.width}x{img.height}")

    def _on_clear_template(self):
        self._template_image = None
        self._page_match._lbl_template_preview.clear()
        self._page_match._lbl_template_preview.setText("无")
        self._page_match._btn_save_template.setEnabled(False)
        self._page_match._btn_match.setEnabled(False)
        self._page_match._lbl_template_hint.setText("未选取模板")
        self._page_match._lbl_template_hint.setStyleSheet("color: #888;")
        self._page_match._table_matches.setRowCount(0)
        self._page_match._lbl_match_status.setText("")
        self._log("已清除模板")

    def _on_match_template(self):
        if self._template_image is None:
            self._log("请先选取模板")
            return
        img = None
        if self._adb_serial:
            self._log("正在通过 ADB 截图...")
            try:
                from adbutils import adb
                d = adb.device(self._adb_serial)
                img = d.screenshot()
            except Exception as e:
                self._log(f"ADB 截图失败: {e}")
        # 优先使用缓存的图片（当前屏幕上显示的），确保从同一张图截的模板能匹配到
        if img is None and self.capture.cached_image is not None:
            img = self.capture.cached_image
            self._log("使用缓存图片进行匹配")
        if img is None and self.binder.is_bound:
            img = self.capture.capture_window(
                self.binder.target_window.hwnd, client_area=True)
        if img is None:
            self._log("没有可用的截图")
            QMessageBox.warning(self, "提示", "请先执行完整截图")
            return
        self._on_screenshot(img)
        self._page_match._lbl_match_status.setText("匹配中...")
        self._page_match._btn_match.setEnabled(False)
        QTimer.singleShot(50, lambda: self._do_match(img))

    def _do_match(self, img):
        try:
            results, elapsed = self.matcher.match(img, self._template_image)
        except Exception as e:
            self._log(f"匹配失败: {e}")
            self._page_match._btn_match.setEnabled(True)
            self._page_match._lbl_match_status.setText("匹配失败")
            return
        self._page_match._btn_match.setEnabled(True)
        if not results:
            w, h = self._template_image.width, self._template_image.height
            self._page_match._lbl_match_status.setText(
                f"未找到匹配 (阈值={self.matcher.threshold:.0%})")
            self._page_match._table_matches.setRowCount(0)
            self._screenshot_label.set_annotations([])
            self._log(
                f"模板匹配: 未找到 (模板{w}x{h}) "
                f"最高分={self.matcher._max_score:.2%} "
                f"阈值={self.matcher.threshold:.0%} "
                f"步长={max(1, min(w, h) // 4)}")
            return

        # 保存原始图片用于后续恢复
        self._match_original_img = img.copy()
        self._match_results = results

        self._page_match._lbl_match_status.setText(
            f"找到 {len(results)} 个匹配 ({elapsed:.2f}s)")
        self._page_match._lbl_match_status.setStyleSheet(
            "color: #4aff4a; padding: 0 8px; font-weight: bold;")
        self._log(f"模板匹配完成: {len(results)} 个结果, 耗时 {elapsed:.2f}s")

        self._page_match._table_matches.setRowCount(len(results))
        for i, m in enumerate(results):
            self._page_match._table_matches.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._page_match._table_matches.setItem(i, 1, QTableWidgetItem(str(m.x)))
            self._page_match._table_matches.setItem(i, 2, QTableWidgetItem(str(m.y)))
            self._page_match._table_matches.setItem(i, 3, QTableWidgetItem(str(m.template_w)))
            self._page_match._table_matches.setItem(i, 4, QTableWidgetItem(str(m.template_h)))
            cx, cy = m.center
            self._page_match._table_matches.setItem(i, 5, QTableWidgetItem(f"({cx}, {cy})"))
            conf_item = QTableWidgetItem(f"{m.confidence:.1%}")
            if m.confidence >= 0.9:
                conf_item.setForeground(QColor(0, 255, 0))
            elif m.confidence >= 0.8:
                conf_item.setForeground(QColor(180, 255, 0))
            else:
                conf_item.setForeground(QColor(255, 200, 0))
            self._page_match._table_matches.setItem(i, 6, conf_item)

        # 叠加层标注匹配矩形（不修改原图，一键清除即可恢复）
        match_rects = [(m.x, m.y, m.template_w, m.template_h, m.confidence) for m in results]
        self._screenshot_label.set_match_rects(match_rects)


        # 同时叠加标注点
        annotations = []
        for m in results:
            annotations.append((m.x, m.y, "found", f"{m.confidence:.0%}"))
        self._screenshot_label.set_annotations(annotations)

    def _on_click_match_result(self):
        if not self.binder.is_bound:
            QMessageBox.warning(self, "提示", "请先绑定目标窗口")
            return
        rows = set()
        for item in self._page_match._table_matches.selectedItems():
            rows.add(item.row())
        if not rows:
            QMessageBox.information(self, "提示", "请在结果列表中选择一个匹配项")
            return
        for row in rows:
            try:
                x = int(self._page_match._table_matches.item(row, 1).text())
                y = int(self._page_match._table_matches.item(row, 2).text())
                cx = x + self._template_image.width // 2
                cy = y + self._template_image.height // 2
                self.tracker.test_click(cx, cy, double_click=False)
                self._log(f"点击匹配位置: ({cx}, {cy})")
            except Exception:
                pass

    def _on_copy_match_results(self):
        if self._page_match._table_matches.rowCount() == 0:
            QMessageBox.information(self, "提示", "没有匹配结果")
            return
        lines = []
        for row in range(self._page_match._table_matches.rowCount()):
            x = self._page_match._table_matches.item(row, 1).text()
            y = self._page_match._table_matches.item(row, 2).text()
            conf = self._page_match._table_matches.item(row, 4).text()
            lines.append(f"({x}, {y})  [{conf}]")
        QApplication.clipboard().setText("\n".join(lines))
        self._log(f"已复制 {len(lines)} 个匹配结果坐标")

    def _on_clear_match_results(self):
        self._page_match._table_matches.setRowCount(0)
        self._page_match._lbl_match_status.setText("")
        self._screenshot_label.set_annotations([])
        self._screenshot_label.clear_match_rects()
        self._match_results = []
        self._log("已清空匹配结果")

    # ═══ 日志 ═══

    def _log(self, msg):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"

        # 写入各页面的日志区
        nav = self._nav_list.currentRow()
        pages = [self._page_coord, self._page_rect, self._page_color, self._page_match]
        for i, p in enumerate(pages):
            p._log_text.append(line)
        self._status_label.setText(msg)

    # ═══ ADB 相关 ═══

    def _on_scan_adb_devices(self):
        self._btn_adb.setEnabled(False)
        self._btn_adb.setText("扫描中...")
        self._log("正在扫描 ADB 设备...")
        self.adb_scanner.scan()

    def _on_adb_devices_found(self, devices):
        self._btn_adb.setEnabled(True)
        self._btn_adb.setText("绑定设备")
        if not devices:
            self._log("未发现 ADB 设备")
            QMessageBox.information(self, "ADB 扫描",
                "未检测到已连接的 Android 设备")
            return
        self._log(f"发现 {len(devices)} 台 ADB 设备")
        dialog = _AdbDeviceDialog(devices, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_device:
            self._bind_adb_device(dialog.selected_device)

    def _bind_adb_device(self, device):
        serial = device["serial"]
        self._adb_serial = serial
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
                if any(kw in title for kw in ["投屏", "镜像", "scrcpy", "QtScrcpy", "android"]):
                    all_candidates.append((hwnd, title, cls, w, h))
                    if not target_hwnd[0]:
                        target_hwnd[0] = hwnd
                        target_info[0] = (hwnd, title, cls, w, h)
                if "tauri window" in cls_lower:
                    all_candidates.append((hwnd, title, cls, w, h))
                    if not target_hwnd[0]:
                        target_hwnd[0] = hwnd
                        target_info[0] = (hwnd, title, cls, w, h)
                return True
            except:
                return True

        win32gui.EnumWindows(find_cb, None)

        if not target_hwnd[0]:
            self._log(f"未找到投屏窗口")
            QMessageBox.warning(self, "提示", "未找到投屏窗口\n请先启动 scrcpy 或其他投屏工具")
            return

        hwnd, title, cls, w, h = target_info[0]
        self._log(f"投屏窗口: [{cls}] {title!r} {w}x{h}")

        child_windows = self.binder.enumerate_child_windows(hwnd)
        phone_child = None
        for child in child_windows:
            cw, ch = child.width, child.height
            if cw > 200 and ch > 200:
                if phone_child is None or (cw * ch) > (phone_child.width * phone_child.height):
                    phone_child = child

        self.binder.bind_window(hwnd)
        info = f"ADB: {serial}"
        if resolution:
            info += f"  |  {resolution}"
        self._lbl_bound_info.setText(info)
        self._lbl_bound_info.setStyleSheet(
            "color: #4FC3F7; padding: 0 8px; font-weight: bold;")
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)
        except Exception:
            pass

        if phone_child:
            main_rect = win32gui.GetWindowRect(hwnd)
            offset_x = phone_child.rect[0] - main_rect[0]
            offset_y = phone_child.rect[1] - main_rect[1]
            self._log(f"检测到子窗口: offset=({offset_x},{offset_y}) "
                     f"size={phone_child.width}x{phone_child.height}")
        elif resolution and "x" in resolution.lower():
            self._log(f"设备分辨率: {resolution}")
        self._log(f"ADB设备绑定完成! 序列号: {serial}")

    def closeEvent(self, event):
        self.tracker.stop_tracking()
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════════
# ADB 辅助类（与原版保持一致）
# ═══════════════════════════════════════════════════════════

class _ScreenshotLoader(QThread):
    screenshot_ready = Signal(str, object)

    def __init__(self, serials):
        super().__init__()
        self.serials = serials

    def run(self):
        import time
        from adbutils import adb
        for serial in self.serials:
            try:
                d = adb.device(serial)
                try:
                    power_info = d.shell("dumpsys power")
                    if "mWakefulness=Asleep" in power_info:
                        d.shell("input keyevent 26")
                        time.sleep(0.5)
                except:
                    pass
                img = d.screenshot()
                self.screenshot_ready.emit(serial, img)
            except Exception:
                self.screenshot_ready.emit(serial, None)


class _AdbDeviceDialog(QDialog):
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

        title = QLabel(f"发现 <b>{len(devices)}</b> 台 ADB 设备，点击选中要绑定的设备:")
        title.setTextFormat(Qt.RichText)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #444; background: #1a1a1a; border-radius: 6px; }")
        scroll_widget = QWidget()
        self._scroll_layout = QVBoxLayout(scroll_widget)
        self._scroll_layout.setContentsMargins(4, 4, 4, 4)
        self._scroll_layout.setSpacing(6)
        self._scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        self._lbl_status = QLabel("正在加载设备截图...")
        self._lbl_status.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._lbl_status)

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

        for d in devices:
            card = self._create_device_card(d)
            self._scroll_layout.insertWidget(
                self._scroll_layout.count() - 1, card)

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
            'QFrame#deviceCard[selected="true"] { border: 2px solid #4FC3F7; background: #1e2d3d; }')
        card.setProperty("device_serial", dev["serial"])

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        thumb = QLabel("加载中...")
        thumb.setFixedSize(120, 72)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setStyleSheet(
            "background: #1a1a1a; border: 1px solid #333; border-radius: 4px;"
            "color: #666; font-size: 11px;")
        layout.addWidget(thumb)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        lbl_serial = QLabel(dev["serial"])
        lbl_serial.setStyleSheet(
            "color: #4FC3F7; font-weight: bold; font-size: 13px;")
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

        lbl_check = QLabel("○")
        lbl_check.setFixedWidth(30)
        lbl_check.setAlignment(Qt.AlignCenter)
        lbl_check.setStyleSheet("color: #555; font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl_check)

        card.mousePressEvent = lambda e, s=dev["serial"]: self._select_device(s)
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
                buf = BytesIO()
                img.save(buf, format="PNG")
                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                scaled = pix.scaled(118, 70, Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation)
                thumb.setPixmap(scaled)
                thumb.setStyleSheet(
                    "background: #111; border: 1px solid #333; border-radius: 4px;")
                self._thumb_labels[serial + "_full"] = img
            except Exception:
                thumb.setText("加载失败")
        else:
            thumb.setText("无画面")
            thumb.setStyleSheet(
                "background: #1a1a1a; border: 1px solid #333; border-radius: 4px;"
                "color: #ffaa00; font-size: 11px;")

    def _on_all_loaded(self):
        self._lbl_status.setText("截图加载完成，请选择设备")
        self._lbl_status.setStyleSheet("color: #6a6; font-size: 12px;")

    def _select_device(self, serial):
        self.selected_device = None
        self._btn_confirm.setEnabled(True)
        for s, card in self._cards.items():
            chk = card.property("check_label")
            if s == serial:
                self.selected_device = {"serial": s}
                card.setProperty("selected", "true")
                card.setStyleSheet(
                    'QFrame#deviceCard[selected="true"]'
                    "{ border: 2px solid #4FC3F7; background: #1e2d3d; border-radius: 8px; }")
                if chk:
                    chk.setText("●")
                    chk.setStyleSheet(
                        "color: #4FC3F7; font-size: 22px; font-weight: bold;")
            else:
                card.setProperty("selected", "false")
                card.setStyleSheet(
                    "QFrame#deviceCard { background: #252525; "
                    "border: 2px solid #444; border-radius: 8px; }")
                if chk:
                    chk.setText("○")
                    chk.setStyleSheet("color: #555; font-size: 22px; font-weight: bold;")

    def _show_preview(self, serial):
        full_key = serial + "_full"
        if full_key not in self._thumb_labels:
            return
        img = self._thumb_labels[full_key]
        if img is None:
            return
        try:
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
                    pix = pix.scaled(max_w, max_h, Qt.KeepAspectRatio,
                                     Qt.SmoothTransformation)
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
