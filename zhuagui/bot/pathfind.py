from __future__ import annotations

import logging

from .cursor_align import park_mouse_in_window
from .input_ctrl import InputController
from .settings import BotSettings
from .window import GameWindow


class PathfindService:
    """
    可选：通过配置的热键弹出「输入坐标寻路」（若存在）。
    梦幻西游端游默认 Alt+G 为「给予」，不是坐标寻路；务必将 enable_coordinate_hotkey_path 保持 false，
    除非你已在 hotkeys.open_goto 中改成客户端真实的寻路热键。
    """

    def __init__(self, settings: BotSettings, window: GameWindow, inp: InputController):
        self._log = logging.getLogger(__name__)
        self._cfg = settings
        self._win = window
        self._inp = inp

    def goto_xy(self, x: int, y: int) -> None:
        if not self._cfg.paths.enable_coordinate_hotkey_path:
            self._log.warning(
                "已跳过坐标热键寻路 (%s,%s)：paths.enable_coordinate_hotkey_path=false。"
                "（端游 Alt+G 为「给予」勿乱开；请用任务追踪/导标落地后点地面前往）",
                x,
                y,
            )
            return
        park_mouse_in_window(self._win, self._cfg.cursor)
        keys = self._cfg.hotkeys.open_goto
        if len(keys) >= 2 and keys[0].lower() == "alt":
            self._inp.hotkey("alt", keys[1].lower())
        else:
            self._inp.hotkey(*[k.lower() for k in keys])
        self._inp.type_text(f"{x} {y}")
        for k in self._cfg.hotkeys.confirm_keys:
            self._inp.press(k.lower())
        self._inp.sleep_map()
        self._log.info("寻路指令已发送: (%s, %s)", x, y)

    def goto_npc_config(self, name: str) -> bool:
        coords = self._cfg.npc_coords.get(name)
        if not coords:
            self._log.error("配置中无 NPC 坐标: %s", name)
            return False
        self.goto_xy(int(coords["x"]), int(coords["y"]))
        return True
