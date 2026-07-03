"""窗口绑定模块"""

import win32gui
import win32process
from PySide6.QtCore import QObject, Signal, QTimer
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class WindowInfo:
    hwnd: int
    title: str
    class_name: str
    rect: tuple = (0, 0, 0, 0)
    pid: int = 0
    process_name: str = ""
    is_visible: bool = False

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]

    @property
    def display_name(self) -> str:
        name = self.title.strip() if self.title.strip() else "[无标题]"
        return f"{name}  ({self.class_name})"


class WindowBinder(QObject):
    window_list_updated = Signal(list)
    window_bound = Signal(WindowInfo)
    window_unbound = Signal()
    window_moved = Signal(WindowInfo)
    picker_mode_changed = Signal(bool)
    status_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_window = None
        self._picker_active = False
        self._all_windows = []
        self._last_rect = None

        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._check_window_position)
        self._monitor_timer.setInterval(200)

    def _check_window_position(self):
        if not self._target_window:
            return
        try:
            hwnd = self._target_window.hwnd
            if not win32gui.IsWindow(hwnd):
                self.unbind_window()
                self.status_message.emit("目标窗口已关闭，已自动解绑")
                return
            rect = win32gui.GetWindowRect(hwnd)
            if self._last_rect != rect:
                self._last_rect = rect
                self._target_window.rect = rect
                self.window_moved.emit(self._target_window)
        except Exception:
            pass

    def enumerate_windows(self):
        windows = []

        def callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                    return True
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                width, height = rect[2] - rect[0], rect[3] - rect[1]
                if width < 50 or height < 50:
                    return True
                if class_name in ("Progman", "WorkerW", "Shell_TrayWnd",
                                   "Button", "Windows.UI.Core.CoreWindow"):
                    return True
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = ""
                try:
                    import psutil
                    proc_name = psutil.Process(pid).name()
                except Exception:
                    pass
                windows.append(WindowInfo(
                    hwnd=hwnd, title=title, class_name=class_name,
                    rect=rect, pid=pid, process_name=proc_name, is_visible=True))
            except Exception:
                pass
            return True

        win32gui.EnumWindows(callback, None)
        self._all_windows = windows
        self.window_list_updated.emit(windows)
        return windows

    def enumerate_child_windows(self, parent_hwnd):
        children = []

        def callback(hwnd, _):
            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                w, h = rect[2] - rect[0], rect[3] - rect[1]
                if w > 50 and h > 50:
                    children.append(WindowInfo(
                        hwnd=hwnd, title=title, class_name=class_name,
                        rect=rect, is_visible=win32gui.IsWindowVisible(hwnd)))
            except Exception:
                pass
            return True

        try:
            win32gui.EnumChildWindows(parent_hwnd, callback, None)
        except Exception:
            pass
        return children

    def bind_window(self, hwnd):
        try:
            if not win32gui.IsWindow(hwnd):
                self.status_message.emit("无效的窗口句柄")
                return None
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = ""
            try:
                import psutil
                proc_name = psutil.Process(pid).name()
            except Exception:
                pass
            self._target_window = WindowInfo(
                hwnd=hwnd, title=title, class_name=class_name,
                rect=rect, pid=pid, process_name=proc_name, is_visible=True)
            self._last_rect = rect
            if self._monitor_timer and not self._monitor_timer.isActive():
                self._monitor_timer.start()
            self.window_bound.emit(self._target_window)
            self.status_message.emit(f"已绑定窗口: {title} ({class_name})")
            return self._target_window
        except Exception as e:
            self.status_message.emit(f"绑定窗口失败: {str(e)}")
            return None

    def unbind_window(self):
        self._target_window = None
        self._last_rect = None
        if self._monitor_timer:
            self._monitor_timer.stop()
        self.window_unbound.emit()
        self.status_message.emit("已解绑窗口")

    @property
    def target_window(self):
        return self._target_window

    @property
    def is_bound(self):
        return self._target_window is not None

    def start_picker_mode(self):
        self._picker_active = True
        self.picker_mode_changed.emit(True)
        self.status_message.emit("进入窗口点选模式，请点击目标窗口...")

    def stop_picker_mode(self):
        self._picker_active = False
        self.picker_mode_changed.emit(False)

    def find_window_by_title(self, keyword):
        self.enumerate_windows()
        return [w for w in self._all_windows if keyword.lower() in w.title.lower()]

    def find_window_by_process(self, process_name):
        self.enumerate_windows()
        return [w for w in self._all_windows
                if process_name.lower() in w.process_name.lower()]


def get_window_rect_screen(hwnd):
    try:
        rect = win32gui.GetWindowRect(hwnd)
        try:
            client_rect = win32gui.GetClientRect(hwnd)
            pt = win32gui.ClientToScreen(hwnd, (0, 0))
            return (pt[0], pt[1], pt[0] + client_rect[2], pt[1] + client_rect[3])
        except Exception:
            pass
        return rect
    except Exception:
        return (0, 0, 0, 0)


def get_window_under_cursor():
    from win32gui import GetCursorPos, WindowFromPoint
    x, y = GetCursorPos()
    return WindowFromPoint((x, y))
