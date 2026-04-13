from __future__ import annotations

import logging
import time
from pathlib import Path

import cv2
import numpy as np

from .cursor_align import park_mouse_in_window
from .guide_flag import GuideFlagChangan
from .input_ctrl import InputController
from .pathfind import PathfindService
from .settings import BotSettings
from .window import GameWindow
from .yolo_client import YoloNpcClient


class ChanganPrepFlow:
    """
    抓鬼前置：长安导标旗 → 马副将 / 驿站传送人（驿站老板）。
    顺序：飞马副将 → ALT+G 到配置坐标 → 点击 NPC；再飞驿站点 → ALT+G → 点击驿站老板。
    """

    def __init__(
        self,
        settings: BotSettings,
        window: GameWindow,
        inp: InputController,
        path: PathfindService,
        yolo: YoloNpcClient,
        debug_dir: Path | None = None,
    ):
        self._log = logging.getLogger(__name__)
        self._cfg = settings
        self._pc = settings.prep_changan
        self.win = window
        self.inp = inp
        self.path = path
        self.yolo = yolo
        self._debug = debug_dir
        self._flyer = GuideFlagChangan(settings, window, inp)

    def _click_npc(
        self,
        log_name: str,
        npc_key: str,
        yolo_classes: set[str],
        f9_retry: bool = False,
    ) -> bool:
        if self.yolo.available:
            pt = self.yolo.find_center_click(
                self.win,
                class_filter=yolo_classes,
                conf=self._pc.yolo_npc_conf,
            )
            if pt:
                self.inp.click_window(self.win, pt[0], pt[1])
                self._log.info("YOLO 点击 %s 窗口(%s,%s)", log_name, pt[0], pt[1])
                return True
            self._log.warning("YOLO 未检出 %s，尝试兜底坐标", log_name)

            if f9_retry:
                # 你提到的机制：先关闭干扰后（这里用 F9 隐藏其他玩家），再二次识别
                self._log.warning("F9 隐藏其他玩家后再识别 %s", log_name)
                self.inp.press("f9")
                time.sleep(0.6)
                pt2 = self.yolo.find_center_click(
                    self.win,
                    class_filter=yolo_classes,
                    conf=self._pc.yolo_npc_conf,
                )
                if pt2:
                    self.inp.click_window(self.win, pt2[0], pt2[1])
                    self._log.info("F9 后 YOLO 点击 %s 窗口(%s,%s)", log_name, pt2[0], pt2[1])
                    return True

        fb = self._pc.fallback_click_norm.get(npc_key)
        r = self.win.rect()
        if fb and r:
            wx = int(r[2] * fb[0])
            wy = int(r[3] * fb[1])
            self.inp.click_window(self.win, wx, wy)
            self._log.info("比例兜底点击 %s 窗口(%s,%s)", log_name, wx, wy)
            return True

        self._log.error(
            "无法点击 %s：未配置 prep_changan.fallback_click_norm[%r] 且 YOLO 无结果",
            log_name,
            npc_key,
        )
        return False

    def _toggle_inventory_by_hotkey(self, n: int = 2) -> None:
        """
        用“同一个热键”切换道具栏（默认 Alt+E 同时用于打开/关闭）。
        目标是：驿站落地后保证道具栏真的关掉，避免遮挡“驿站老板/按钮”识别。
        """
        hk = self._cfg.guide_flag.open_inventory
        if len(hk) < 2:
            return
        for _ in range(max(1, n)):
            if hk[0].lower() == "alt":
                self.inp.hotkey("alt", hk[1].lower())
            else:
                self.inp.hotkey(*[k.lower() for k in hk])
            time.sleep(0.35)

    def _press_confirm_keys(self, n: int = 1) -> None:
        keys = self._cfg.hotkeys.confirm_keys
        if not keys:
            return
        # 取第一个确认键（通常 enter）
        k = keys[0]
        for _ in range(max(1, n)):
            self.inp.press(k)
            time.sleep(0.25)

    def _click_mafujiang_with_f9_retry(self) -> bool:
        """
        点击马副将，并按需求处理：
        - 如果 YOLO 没识别到马副将，先按 F9 隐藏其他玩家，再识别
        - 仍识别不到则用 prep_changan.fallback_click_norm 兜底
        - 如你之后希望“仍识别不到则 alt+g 到坐标”，也可以在这里继续扩展
        """
        if self.yolo.available:
            pt = self.yolo.find_center_click(
                self.win,
                class_filter={"马副将"},
                conf=self._pc.yolo_npc_conf,
            )
            if pt:
                self.inp.click_window(self.win, pt[0], pt[1])
                self._log.info("YOLO 点击 马副将 窗口(%s,%s)", pt[0], pt[1])
                return True

            # F9 隐藏其他玩家，再试一次
            self._log.warning("YOLO 未检出 马副将，按 F9 隐藏其他玩家再识别")
            self.inp.press("f9")
            time.sleep(0.6)
            pt2 = self.yolo.find_center_click(
                self.win,
                class_filter={"马副将"},
                conf=self._pc.yolo_npc_conf,
            )
            if pt2:
                self.inp.click_window(self.win, pt2[0], pt2[1])
                self._log.info("F9 后 YOLO 点击 马副将 窗口(%s,%s)", pt2[0], pt2[1])
                return True

        # 兜底：比例坐标点击
        fb = self._pc.fallback_click_norm.get("马副将")
        r = self.win.rect()
        if fb and r:
            wx = int(r[2] * fb[0])
            wy = int(r[3] * fb[1])
            self.inp.click_window(self.win, wx, wy)
            self._log.info("比例兜底点击 马副将 窗口(%s,%s)", wx, wy)
            return True
        self._log.error("无法点击 马副将：缺少 YOLO 结果且未配置 fallback_click_norm")
        return False

    def _claim_double_reward(self) -> None:
        """
        点击马副将对话后领取双倍奖励。
        当前实现：点击 NPC 后按确认键（默认 enter）若干次。
        如果你下一步给我“领取双倍奖励”按钮/对话截图，我可以把这里升级为模板或 OCR 定位点击。
        """
        # 给对话框一点打开时间，并做小循环：按钮模板出现则点击，不出现则用 Enter 推进对话
        time.sleep(0.8)
        for attempt in range(6):
            if self._click_template_in_window("assets/prep_changan/double_reward_4h.png", threshold=0.23):
                time.sleep(0.35)
                self._press_confirm_keys(n=1)
                time.sleep(1.0)
                return
            self._log.warning("领取双倍模板未出现，attempt=%s，按 Enter 推进对话", attempt + 1)
            self._press_confirm_keys(n=1)
            time.sleep(0.7)
        # 最后兜底
        self._press_confirm_keys(n=2)
        time.sleep(1.0)

    def _click_template_in_window(self, template_rel: str, threshold: float = 0.23) -> bool:
        root = Path(__file__).resolve().parent.parent
        tpath = root / template_rel
        if not tpath.is_file():
            return False
        img = self.win.capture()
        if not img:
            return False
        screen = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        tpl = cv2.imread(str(tpath))
        if tpl is None:
            return False
        # 仅在中部对话区域查找，减少误检
        sh, sw = screen.shape[:2]
        rx0, ry0 = int(sw * 0.18), int(sh * 0.20)
        rx1, ry1 = int(sw * 0.85), int(sh * 0.82)
        roi = screen[ry0:ry1, rx0:rx1]
        if roi.size == 0:
            return False
        th, tw = tpl.shape[:2]
        rh, rw = roi.shape[:2]
        if th > rh or tw > rw:
            return False
        # 同时做彩色与灰度匹配，取更高分
        res_c = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        _min_v, max_v_c, _min_l, max_l_c = cv2.minMaxLoc(res_c)
        roi_g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        tpl_g = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
        res_g = cv2.matchTemplate(roi_g, tpl_g, cv2.TM_CCOEFF_NORMED)
        _min_v2, max_v_g, _min_l2, max_l_g = cv2.minMaxLoc(res_g)
        if max_v_g > max_v_c:
            max_v = max_v_g
            max_l = max_l_g
            mode = "gray"
        else:
            max_v = max_v_c
            max_l = max_l_c
            mode = "color"
        if max_v < threshold:
            self._log.warning("模板 %s(%s) 匹配分数 %.3f 低于阈值 %.2f", template_rel, mode, max_v, threshold)
            return False
        cx = int(rx0 + max_l[0] + tw / 2)
        cy = int(ry0 + max_l[1] + th / 2)
        self.inp.click_window(self.win, cx, cy)
        self._log.info("模板点击成功 %s(%s) conf=%.3f 窗口(%s,%s)", template_rel, mode, max_v, cx, cy)
        return True

    def _after_goto_npc(self, npc_key: str) -> None:
        if self._cfg.paths.enable_coordinate_hotkey_path:
            if not self.path.goto_npc_config(npc_key):
                self._log.warning("npc_coords 缺少 %s，跳过坐标寻路", npc_key)
        else:
            self._log.info(
                "未开启坐标热键寻路（避免 Alt+G「给予」）；导标落地后等待 %.1fs 再点 NPC",
                self._pc.after_altg_walk_s,
            )
        time.sleep(self._pc.after_altg_walk_s)

    def _segment_mafujiang(self) -> bool:
        self._log.info("—— 长安旗 → 马副将 ——")
        if not self._flyer.fly_to("mafujiang", debug_dir=self._debug):
            return False
        time.sleep(self._pc.after_fly_sleep_s)
        self._after_goto_npc("马副将")
        if not self._click_mafujiang_with_f9_retry():
            return False
        if self._cfg.strategy.enable_double_exp:
            self._claim_double_reward()
        else:
            self._log.info("enable_double_exp=false，跳过马副将领取双倍对话")
            time.sleep(0.5)
        return True

    def _segment_yizhan(self) -> bool:
        self._log.info("—— 长安旗 → 驿站 ——")
        if not self._flyer.fly_to("yizhan", debug_dir=self._debug):
            return False
        time.sleep(self._pc.after_fly_sleep_s)
        self._toggle_inventory_by_hotkey(n=2)
        self._after_goto_npc("驿站老板")
        if not self._click_npc(
            "驿站传送人(驿站老板)",
            "驿站老板",
            {"驿站老板"},
            f9_retry=True,
        ):
            return False
        # 驿站传送到大唐国境：优先按你提供的按钮模板点击
        time.sleep(0.8)
        if self._click_template_in_window(
            "assets/prep_changan/yizhan_to_datang.png", threshold=0.23
        ):
            time.sleep(0.35)
            self._press_confirm_keys(n=1)
        else:
            # 兜底：连点确认键
            self._press_confirm_keys(n=2)
        time.sleep(1.0)
        return True

    def run(self) -> bool:
        self._log.info("需求文档 §2.1 步骤2～4：马副将(领双) → 导标飞驿站 → 驿站老板传送大唐国境")
        park_mouse_in_window(self.win, self._cfg.cursor)
        if not self._segment_mafujiang():
            self._log.error("马副将段失败，已中止（见 debug_fly）")
            return False
        time.sleep(self._pc.between_steps_sleep_s)
        if not self._segment_yizhan():
            self._log.error("驿站段失败，已中止（见 debug_fly）")
            return False
        self._log.info("长安准备流程执行完毕（导标 + 寻路 + 点击）")
        return True

    def run_continue_after_mafujiang(self) -> bool:
        """
        继续执行：假设你已经通过 --ghost-step1 飞到马副将附近。
        按需求：点击马副将领取双倍（必要时 F9 隐藏再识别），再导标旗飞驿站→点击传送人→去大唐国境。
        """
        self._log.info("—— 继续：马副将双倍领取 → 驿站传送人 → 大唐国境 ——")
        # 若当前并未在马副将附近（YOLO 识别不到），先补做“长安旗→马副将”完整段
        if self.yolo.available:
            pt = self.yolo.find_center_click(
                self.win,
                class_filter={"马副将"},
                conf=self._pc.yolo_npc_conf,
            )
            if not pt:
                self._log.warning("继续流程中未检出 马副将，先补做完整马副将段")
                if not self._segment_mafujiang():
                    return False
                time.sleep(self._pc.between_steps_sleep_s)
        # 若已经在马副将附近，则执行领取双倍 + 后续驿站段
        if not self._click_mafujiang_with_f9_retry():
            return False
        if self._cfg.strategy.enable_double_exp:
            self._claim_double_reward()
        else:
            self._log.info("enable_double_exp=false，跳过马副将领取双倍对话")
            time.sleep(0.5)
        time.sleep(self._pc.between_steps_sleep_s)
        if not self._segment_yizhan():
            self._log.error("驿站段失败，已中止")
            return False
        self._log.info("前置继续流程执行完毕（双倍领取 + 驿站传送）")
        return True
