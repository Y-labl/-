from __future__ import annotations

import logging
import random
import time

import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

from .cursor_align import align_pointer_to_window_target
from .settings import BotSettings


class InputController:
    def __init__(self, settings: BotSettings):
        self._log = logging.getLogger(__name__)
        self._cfg = settings

    def _sleep_action(self) -> None:
        lo = self._cfg.delays.action_min_ms / 1000.0
        hi = self._cfg.delays.action_max_ms / 1000.0
        time.sleep(random.uniform(lo, hi))

    def _move_to_window_point(self, win, wx: int, wy: int) -> None:
        self._move_to_window_point_maybe_align(win, wx, wy, force_align=None)

    def move_to_window(self, win, wx: int, wy: int) -> None:
        """仅把系统鼠标移到窗口内 (wx,wy)，使用名义坐标（不做模板对齐）。"""
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] move_to_window(%s, %s)", wx, wy)
            return
        sx, sy = win.window_to_screen(wx, wy)
        d = max(0.0, self._cfg.cursor.move_to_point_duration_s)
        pyautogui.moveTo(sx, sy, duration=d)
        self._log.info("鼠标移到窗口(%s,%s) 屏幕(%s,%s)", wx, wy, sx, sy)

    def move_to_screen_point(self, x: int, y: int, duration: float = 0) -> None:
        """仅移动系统鼠标到屏幕坐标（不点击）。"""
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] move_to_screen_point(%s, %s)", x, y)
            return
        pyautogui.moveTo(x, y, duration=max(0.0, duration))

    def right_click_at_current(self) -> None:
        """在当前鼠标位置右键（配合先 move 再对齐）。"""
        if self._cfg.strategy.dry_run:
            return
        self._sleep_action()
        pyautogui.click(button="right")

    def click_screen(self, x: int, y: int) -> None:
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] click_screen(%s, %s)", x, y)
            return
        self._sleep_action()
        pyautogui.moveTo(x, y, duration=0)
        self._sleep_action()
        pyautogui.click()
        self._log.debug("click %s,%s", x, y)

    def right_click_screen(
        self, x: int, y: int, move_duration: float | None = None
    ) -> None:
        """右键屏幕坐标；move_duration>0 时缓慢移动，便于游戏内光标同步。"""
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] right_click_screen(%s, %s)", x, y)
            return
        self._sleep_action()
        dur = move_duration if move_duration is not None else 0.0
        pyautogui.moveTo(x, y, duration=max(0.0, dur))
        time.sleep(0.15 if dur > 0 else 0.05)
        self._sleep_action()
        pyautogui.click(button="right")
        self._log.debug("right_click %s,%s", x, y)

    def click_window(
        self, win, wx: int, wy: int, force_align: bool | None = None
    ) -> None:
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] click_window(%s, %s)", wx, wy)
            return
        self._move_to_window_point_maybe_align(win, wx, wy, force_align)
        time.sleep(0.08)
        self._sleep_action()
        pyautogui.click()
        self._log.debug("click_window %s,%s", wx, wy)

    def _move_to_window_point_maybe_align(
        self, win, wx: int, wy: int, force_align: bool | None = None
    ) -> None:
        """移动到窗口坐标，force_align=True 时强制用模板对齐游戏内光标。"""
        if self._cfg.strategy.dry_run:
            return
        use_align = force_align if force_align is not None else self._cfg.cursor.align_before_click
        if use_align:
            align_pointer_to_window_target(win, self._cfg.cursor, self._log, wx, wy)
        else:
            self.move_to_window(win, wx, wy)

    def right_click_window(
        self, win, wx: int, wy: int, force_align: bool | None = None
    ) -> None:
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] right_click_window(%s, %s)", wx, wy)
            return
        self._move_to_window_point_maybe_align(win, wx, wy, force_align)
        time.sleep(0.12)
        self._sleep_action()
        pyautogui.click(button="right")
        self._log.debug("right_click_window %s,%s", wx, wy)

    def hotkey(self, *keys: str) -> None:
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] hotkey(%s)", keys)
            return
        self._sleep_action()
        pyautogui.hotkey(*keys, interval=0.05)
        self._log.debug("hotkey %s", keys)

    def type_text(self, text: str, interval: float = 0.03) -> None:
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] type_text(%r)", text)
            return
        self._sleep_action()
        pyautogui.write(text, interval=interval)
        self._log.debug("type %r", text)

    def press(self, key: str) -> None:
        if self._cfg.strategy.dry_run:
            self._log.info("[dry_run] press(%r)", key)
            return
        self._sleep_action()
        pyautogui.press(key)

    def sleep_map(self) -> None:
        time.sleep(self._cfg.delays.after_map_load_s)
