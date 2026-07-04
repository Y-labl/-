"""坐标定位模块"""
import time
import win32gui
import win32api
import win32con
from PySide6.QtCore import QObject, Signal, QTimer


class CoordinateTracker(QObject):
    mouse_position = Signal(int, int)
    tracking_started = Signal()
    tracking_stopped = Signal()
    status_message = Signal(str)
    right_click_captured = Signal(int, int)  # 右键捕获坐标
    auto_save_coord = Signal(int, int)       # 停留3秒自动保存

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_hwnd = None
        self._tracking = False
        self._right_click_enabled = False
        self._rbutton_pressed = False
        # 停留检测：鼠标在同位置超过3秒自动保存
        self._idle_x = -1
        self._idle_y = -1
        self._idle_start = 0.0
        self._idle_saved = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_mouse)

    def set_target(self, hwnd):
        self._target_hwnd = hwnd

    def set_right_click_enabled(self, enabled: bool):
        self._right_click_enabled = enabled

    def start_tracking(self):
        if self._tracking:
            return
        self._tracking = True
        self._idle_x = -1
        self._idle_y = -1
        self._idle_saved = False
        self._timer.start(33)
        self.tracking_started.emit()
        self.status_message.emit("坐标追踪已启动")

    def stop_tracking(self):
        self._tracking = False
        self._timer.stop()
        self.tracking_stopped.emit()
        self.status_message.emit("坐标追踪已停止")

    def _poll_mouse(self):
        if not self._tracking or not self._target_hwnd:
            return
        try:
            cursor_pos = win32gui.GetCursorPos()
            screen_x, screen_y = cursor_pos
            from modules.window_binder import get_window_rect_screen
            rect = get_window_rect_screen(self._target_hwnd)
            rel_x = screen_x - rect[0]
            rel_y = screen_y - rect[1]
            self.mouse_position.emit(rel_x, rel_y)

            # 停留检测：鼠标在同一位置超过3秒自动保存
            now = time.time()
            if rel_x == self._idle_x and rel_y == self._idle_y:
                if not self._idle_saved and now - self._idle_start >= 3.0:
                    self._idle_saved = True
                    self.auto_save_coord.emit(rel_x, rel_y)
            else:
                self._idle_x = rel_x
                self._idle_y = rel_y
                self._idle_start = now
                self._idle_saved = False

            # 右键保存坐标：检测右键按下边沿
            if self._right_click_enabled:
                rbutton_state = win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000
                if rbutton_state and not self._rbutton_pressed:
                    self._rbutton_pressed = True
                    self.right_click_captured.emit(rel_x, rel_y)
                elif not rbutton_state:
                    self._rbutton_pressed = False
        except Exception:
            pass

    def test_click(self, x: int, y: int, double_click: bool = False):
        """
        在绑定窗口内模拟点击指定相对坐标
        :param x: 相对于窗口的 X 坐标
        :param y: 相对于窗口的 Y 坐标
        :param double_click: 是否双击
        """
        if not self._target_hwnd:
            self.status_message.emit("请先绑定窗口")
            return False
        try:
            from modules.window_binder import get_window_rect_screen
            rect = get_window_rect_screen(self._target_hwnd)
            if not rect:
                self.status_message.emit("无法获取窗口位置")
                return False

            target_x = rect[0] + x
            target_y = rect[1] + y

            win32api.SetCursorPos((target_x, target_y))
            time.sleep(0.02)

            if double_click:
                for _ in range(2):
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(0.01)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    time.sleep(0.05)
                self.status_message.emit(f"测试双击 -> ({x}, {y}) 完成")
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                self.status_message.emit(f"测试点击 -> ({x}, {y}) 完成")
            return True
        except Exception as e:
            self.status_message.emit(f"测试点击失败: {e}")
            return False

    @property
    def is_tracking(self):
        return self._tracking
