from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes
from typing import Optional

import pyautogui
import pygetwindow as gw
from PIL import Image

pyautogui.PAUSE = 0

from .settings import BotSettings

_SW_RESTORE = 9
_VK_MENU = 0x12
_KEYEVENTF_KEYUP = 0x0002


def _activate_hwnd_force(hwnd: int) -> bool:
    """SetForegroundWindow 常被系统拒绝；AttachThreadInput + Alt 轻敲为常见 workaround。"""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    fg = user32.GetForegroundWindow()
    pid = wintypes.DWORD(0)
    tid_fg = user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
    tid_cur = kernel32.GetCurrentThreadId()
    user32.ShowWindow(hwnd, _SW_RESTORE)
    # 部分环境下可解除前台限制（与 pyautogui.hotkey 思路类似，不依赖 pyautogui）
    user32.keybd_event(_VK_MENU, 0, 0, 0)
    user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
    if not fg or tid_fg == tid_cur:
        return bool(user32.SetForegroundWindow(hwnd))
    user32.AttachThreadInput(tid_fg, tid_cur, True)
    try:
        return bool(user32.SetForegroundWindow(hwnd))
    finally:
        user32.AttachThreadInput(tid_fg, tid_cur, False)


class GameWindow:
    def __init__(self, settings: BotSettings):
        self._log = logging.getLogger(__name__)
        self._cfg = settings
        self._win: Optional[gw.Win32Window] = None

    @property
    def hwnd_window(self) -> Optional[gw.Win32Window]:
        return self._win

    def find(self) -> bool:
        sub = self._cfg.window.title_substring
        mw, mh = self._cfg.window.min_width, self._cfg.window.min_height
        ew, eh = self._cfg.window.expected_width, self._cfg.window.expected_height
        candidates: list[gw.Win32Window] = []
        for w in gw.getAllWindows():
            if not w.title or sub not in w.title:
                continue
            if w.width >= mw and w.height >= mh:
                candidates.append(w)
        if not candidates:
            self._log.error("未找到标题包含 %r 且尺寸>= %sx%s 的窗口", sub, mw, mh)
            return False
        if ew > 0 and eh > 0:

            def score(win: gw.Win32Window) -> int:
                return abs(win.width - ew) + abs(win.height - eh)

            self._win = min(candidates, key=score)
            if self._win.width != ew or self._win.height != eh:
                self._log.warning(
                    "选中窗口尺寸为 %sx%s，与 expected %sx%s 不完全一致（多开时请核对）",
                    self._win.width,
                    self._win.height,
                    ew,
                    eh,
                )
        else:
            self._win = candidates[0]
        self._log.info("找到窗口: %s (%sx%s)", self._win.title, self._win.width, self._win.height)
        return True

    def activate(self) -> bool:
        if not self._win:
            return False
        try:
            self._win.activate()
            return True
        except Exception as e:
            self._log.warning("pygetwindow.activate 失败 (%s)，尝试 AttachThreadInput 回退", e)
            ok = _activate_hwnd_force(int(self._win._hWnd))
            if not ok:
                self._log.warning(
                    "无法将游戏窗口置于前台（截图仍可用；若要点游戏内坐标请先手动点一下游戏窗口）"
                )
            return ok

    def rect(self) -> Optional[tuple[int, int, int, int]]:
        if not self._win:
            return None
        return self._win.left, self._win.top, self._win.width, self._win.height

    def capture(self, region_window_xywh: Optional[tuple[int, int, int, int]] = None) -> Optional[Image.Image]:
        r = self.rect()
        if not r:
            return None
        left, top, w, h = r
        try:
            if region_window_xywh:
                rx, ry, rw, rh = region_window_xywh
                box = (left + rx, top + ry, rw, rh)
                return pyautogui.screenshot(region=box)
            return pyautogui.screenshot(region=(left, top, w, h))
        except Exception as e:
            self._log.error("截图失败: %s", e)
            return None

    def capture_roi_norm(self, x0: float, y0: float, x1: float, y1: float) -> Optional[Image.Image]:
        r = self.rect()
        if not r:
            return None
        _, _, w, h = r
        wx0 = int(w * x0)
        wy0 = int(h * y0)
        wx1 = int(w * x1)
        wy1 = int(h * y1)
        return self.capture((wx0, wy0, max(1, wx1 - wx0), max(1, wy1 - wy0)))

    def window_to_screen(self, x: int, y: int) -> tuple[int, int]:
        r = self.rect()
        if not r:
            return x, y
        left, top, _, _ = r
        return left + x, top + y
