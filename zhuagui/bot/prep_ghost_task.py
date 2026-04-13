from __future__ import annotations

import logging
import time

from .input_ctrl import InputController
from .pathfind import PathfindService
from .settings import BotSettings
from .window import GameWindow
from .yolo_client import YoloNpcClient


class GhostQuestAcceptFlow:
    """
    在长安前置（驿站→国境）完成后执行：可选黑无常鬼王 → 钟馗领抓鬼。
    需角色最终位于地府（或能 Alt+G 走到 npc_coords 所指坐标）；国境到地府若未自动化，请用 manual_travel_to_difu_s 留时间手动跑图。
    """

    def __init__(
        self,
        settings: BotSettings,
        window: GameWindow,
        inp: InputController,
        path: PathfindService,
        yolo: YoloNpcClient,
    ):
        self._log = logging.getLogger(__name__)
        self._cfg = settings
        self._pg = settings.prep_ghost
        self.win = window
        self.inp = inp
        self.path = path
        self.yolo = yolo

    def _press_confirm(self, n: int = 1) -> None:
        keys = self._cfg.hotkeys.confirm_keys
        if not keys:
            return
        k = str(keys[0]).lower()
        for _ in range(max(1, n)):
            self.inp.press(k)
            time.sleep(0.28)

    def _spam_dialog(self) -> None:
        n = max(1, self._pg.dialog_enter_presses)
        self._press_confirm(n=n)

    def _click_npc(
        self,
        log_name: str,
        npc_key: str,
        yolo_classes: set[str],
        f9_retry: bool = False,
    ) -> bool:
        conf = self._pg.yolo_npc_conf
        if self.yolo.available:
            pt = self.yolo.find_center_click(
                self.win,
                class_filter=yolo_classes,
                conf=conf,
            )
            if pt:
                self.inp.click_window(self.win, pt[0], pt[1])
                self._log.info("YOLO 点击 %s 窗口(%s,%s)", log_name, pt[0], pt[1])
                return True
            self._log.warning("YOLO 未检出 %s，尝试兜底比例", log_name)
            if f9_retry:
                self.inp.press("f9")
                time.sleep(0.6)
                pt2 = self.yolo.find_center_click(
                    self.win,
                    class_filter=yolo_classes,
                    conf=conf,
                )
                if pt2:
                    self.inp.click_window(self.win, pt2[0], pt2[1])
                    self._log.info("F9 后 YOLO 点击 %s", log_name)
                    return True

        fb = self._pg.fallback_click_norm.get(npc_key)
        r = self.win.rect()
        if fb and r:
            wx = int(r[2] * fb[0])
            wy = int(r[3] * fb[1])
            self.inp.click_window(self.win, wx, wy)
            self._log.info("比例兜底点击 %s 窗口(%s,%s)", log_name, wx, wy)
            return True

        self._log.error("无法点击 %s：无 YOLO 且未配置 prep_ghost.fallback_click_norm[%r]", log_name, npc_key)
        return False

    def run(self) -> bool:
        self._log.info(
            "需求文档 §2.1 步骤5：国境→地府（脚本未全自动跑图；请已在地府或增大 manual_travel_to_difu_s 人工进地府）"
        )
        time.sleep(max(0.0, self._pg.post_guojing_delay_s))
        wait = max(0.0, self._pg.manual_travel_to_difu_s)
        if wait > 0:
            self._log.warning(
                "manual_travel_to_difu_s=%s：请在等待期间手动从国境进入地府", wait
            )
            time.sleep(wait)

        if self._cfg.strategy.enable_guowang:
            self._log.info("需求文档 §2.1 步骤6：黑无常领取鬼王（可选）")
            if self._cfg.paths.enable_coordinate_hotkey_path:
                if not self.path.goto_npc_config("黑无常"):
                    return False
            else:
                self._log.info("跳过坐标热键走向黑无常；请角色已在附近，等待 %.1fs", self._pg.after_altg_heiwuchang_walk_s)
            time.sleep(self._pg.after_altg_heiwuchang_walk_s)
            if not self._click_npc("黑无常", "黑无常", {"黑无常"}, f9_retry=True):
                return False
            time.sleep(0.6)
            self._spam_dialog()

        self._log.info("需求文档 §2.1 步骤7：钟馗领取抓鬼任务")
        if self._cfg.paths.enable_coordinate_hotkey_path:
            if not self.path.goto_npc_config("钟馗"):
                return False
        else:
            self._log.info("跳过坐标热键走向钟馗；请角色已在地府钟馗附近，等待 %.1fs", self._pg.after_altg_zhongkui_walk_s)
        time.sleep(self._pg.after_altg_zhongkui_walk_s)
        if not self._click_npc("钟馗", "钟馗", {"钟馗"}, f9_retry=True):
            return False
        time.sleep(0.7)
        self._spam_dialog()
        self._log.info("步骤7 对话已用 Enter 推进；随后进入需求文档步骤9（OCR 任务追踪栏）")
        return True
