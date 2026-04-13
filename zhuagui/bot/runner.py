from __future__ import annotations

import logging
import time
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from .cursor_align import park_mouse_in_window
from .input_ctrl import InputController
from .models import GhostTaskInfo
from .ocr_task import is_empty_task_tracker, parse_task_from_image
from .requirement_doc import log_pipeline_vs_doc
from .pathfind import PathfindService
from .settings import BotSettings
from .window import GameWindow
from .yolo_client import YoloNpcClient

_ZHUAGUI_ROOT = Path(__file__).resolve().parent.parent


class GhostState(Enum):
    INIT = auto()
    PARSE_TASK = auto()
    GOTO_TARGET = auto()
    COMBAT = auto()
    TURN_IN = auto()
    NEXT_ROUND = auto()
    STOP = auto()


class GhostRunner:
    """状态机：可选前置（领双→驿站→国境→钟馗领抓鬼）→ OCR 任务栏 → 寻路/战斗占位 → 回钟馗。"""

    def __init__(self, settings: BotSettings):
        self._log = logging.getLogger(__name__)
        self.cfg = settings
        self.win = GameWindow(settings)
        self.inp = InputController(settings)
        self.path = PathfindService(settings, self.win, self.inp)
        self.yolo = YoloNpcClient(settings)
        self.state = GhostState.INIT
        self.round_index = 0
        self._current_task: Optional[GhostTaskInfo] = None
        self._live_dir: Optional[Path] = None
        self._live_seq = 0

    def _live(self, tag: str, **extra: object) -> None:
        if not self.cfg.live_observe.enabled or self._live_dir is None:
            return
        from .live_observe import write_step

        write_step(
            self.cfg,
            self.win,
            self._live_dir,
            self._live_seq,
            tag,
            round_idx=self.round_index,
            state_name=self.state.name,
            extra=dict(extra) if extra else None,
        )
        self._live_seq += 1

    def run(self) -> None:
        if not self.win.find():
            self.state = GhostState.STOP
            return
        self.win.activate()
        time.sleep(0.3)
        park_mouse_in_window(self.win, self.cfg.cursor)

        from .live_observe import new_session_dir

        self._live_dir = new_session_dir(_ZHUAGUI_ROOT, self.cfg)
        if self._live_dir is not None:
            self._live_seq = 0
            self._log.info("实时截图目录: %s（每步写入 manifest.jsonl）", self._live_dir)
            self._live(
                "run_start",
                dry_run=self.cfg.strategy.dry_run,
                auto_ghost_prep=self.cfg.strategy.auto_ghost_prep,
            )

        log_pipeline_vs_doc(self._log)

        if self.cfg.strategy.dry_run:
            self._log.warning(
                "\n"
                "========== dry_run=true（默认安全模式）==========\n"
                "本运行不会对游戏发送「领双、开背包导标、点驿站、地府对话、Alt+G 寻路、战斗点怪」等操作，"
                "所以角色在画面里看起来会「完全不动」——这是预期行为。\n"
                "当前只会：激活窗口、鼠标 park、截图、OCR、写 debug_run/manifest.jsonl。\n"
                "需要角色真的动起来：在 config 里设 strategy.dry_run: false，并确认 Alt+G 等与你客户端一致。\n"
                "================================================\n"
            )

        if not self.cfg.strategy.assume_party_ready:
            self._log.warning("第一版请先将 assume_party_ready 设为 true，或自行扩展组队模块")
            self._live("stopped_assume_party_false")
            self.state = GhostState.STOP
            return

        if self.cfg.strategy.auto_ghost_prep and not self.cfg.strategy.dry_run:
            if not self._run_auto_ghost_prep():
                self._log.error("抓鬼前置（领双/领任务）失败，已停止")
                self._live("prep_failed")
                self.state = GhostState.STOP
                return
            self._live("after_prep_ok")
            if self.cfg.strategy.enable_tianyan:
                self._log.warning(
                    "需求文档 §2.1 步骤8（天眼通符）尚未实现，将直接进入步骤9 OCR；"
                    "若玩法依赖天眼，请先手动使用或后续接模块。"
                )
        elif self.cfg.strategy.auto_ghost_prep and self.cfg.strategy.dry_run:
            self._log.warning(
                "dry_run=true：跳过文档步骤2～7（领双、驿站国境、地府、鬼王、钟馗领任务），"
                "与步骤9 OCR 顺序不一致；要领任务后再识别请设 strategy.dry_run: false"
            )
            self._live("prep_skipped_dry_run")

        self.state = GhostState.PARSE_TASK
        while self.state != GhostState.STOP:
            self._step()
        self._live("run_end")
        self._log.info("状态机结束")

    def _run_auto_ghost_prep(self) -> bool:
        from .prep_changan import ChanganPrepFlow
        from .prep_ghost_task import GhostQuestAcceptFlow

        root = _ZHUAGUI_ROOT
        dbg = root / "debug_fly"
        flow = ChanganPrepFlow(
            self.cfg, self.win, self.inp, self.path, self.yolo, debug_dir=dbg
        )
        if not flow.run():
            return False
        accept_flow = GhostQuestAcceptFlow(
            self.cfg, self.win, self.inp, self.path, self.yolo
        )
        return accept_flow.run()

    def _step(self) -> None:
        if self.state == GhostState.PARSE_TASK:
            self._do_parse_task()
        elif self.state == GhostState.GOTO_TARGET:
            self._do_goto_target()
        elif self.state == GhostState.COMBAT:
            self._do_combat()
        elif self.state == GhostState.TURN_IN:
            self._do_turn_in()
        elif self.state == GhostState.NEXT_ROUND:
            self._do_next_round()
        else:
            self.state = GhostState.STOP

    def _do_parse_task(self) -> None:
        self.round_index += 1
        x0, y0, x1, y1 = self.cfg.roi.task_tracker
        img = self.win.capture_roi_norm(x0, y0, x1, y1)
        self._current_task = parse_task_from_image(img, task_number=self.round_index)
        self._log.info(
            "任务解析: loc=%s xy=%s ghost=%s conf=%.2f raw=%r",
            self._current_task.location,
            self._current_task.coordinates,
            self._current_task.ghost_type,
            self._current_task.confidence,
            self._current_task.raw_text[:80],
        )
        raw = self._current_task.raw_text or ""
        ghost_tokens = ("抓鬼", "鬼王", "钟馗", "索命")
        if raw.strip() and is_empty_task_tracker(raw):
            self._log.error(
                "任务追踪为空（OCR 与截图一致）。按《抓鬼任务需求文档》§2.1，须先完成步骤1～7 再执行步骤9。"
                "请设 strategy.dry_run: false 跑 auto_ghost_prep，或手动领抓鬼后再运行。"
            )
            self._live(
                "parse_tracker_empty",
                ocr_excerpt=raw[:400],
                has_target=False,
            )
            self.state = GhostState.STOP
            return
        if raw.strip() and "师门" in raw and not any(t in raw for t in ghost_tokens):
            self._log.error(
                "已从任务栏 OCR 识别为师门等非抓鬼追踪（与当前窗口画面一致时请勿强行跑抓鬼）。"
                "请先完成或取消师门；要领抓鬼请设 strategy.dry_run: false 并保证 auto_ghost_prep 与地府流程可用。"
            )
            self._live(
                "parse_blocked_shimen",
                ocr_excerpt=raw[:400],
                has_target=False,
            )
            self.state = GhostState.STOP
            return
        if self._current_task.has_target:
            self._live(
                "after_parse_ok",
                ocr_excerpt=raw[:400],
                has_target=True,
                location=self._current_task.location,
                xy=list(self._current_task.coordinates),
                ghost_type=self._current_task.ghost_type,
            )
            self.state = GhostState.GOTO_TARGET
        else:
            hint = (
                "任务栏有字但无地图坐标（可能非抓鬼描述或 OCR 漏字；对照 debug_run/*_task.png 与 manifest.jsonl）"
                if raw.strip()
                else "任务栏 OCR 无文本（请检查 ROI、PaddleOCR 是否可用，或运行 python run_bot.py --probe-state）"
            )
            self._log.error("无有效目标，停止。%s", hint)
            self._live(
                "parse_no_target",
                ocr_excerpt=raw[:400],
                has_target=False,
                hint=hint[:200],
            )
            self.state = GhostState.STOP

    def _do_goto_target(self) -> None:
        assert self._current_task is not None
        x, y = self._current_task.coordinates
        if not self.cfg.paths.enable_coordinate_hotkey_path:
            self._log.error(
                "已解析目标坐标 (%s,%s)，但未开启坐标热键寻路（端游 Alt+G 为「给予」）。"
                "请手动前往或后续接入任务追踪/小地图寻路后再跑。",
                x,
                y,
            )
            self._live("goto_target_blocked_no_coordinate_hotkey", goto_xy=[x, y])
            self.state = GhostState.STOP
            return
        self.path.goto_xy(x, y)
        self._live("after_goto_target", goto_xy=[x, y])
        self.state = GhostState.COMBAT

    def _do_combat(self) -> None:
        if self.cfg.strategy.dry_run:
            self._log.info("[dry_run] 战斗阶段占位：请在此接入 YOLO 点主怪 + 自动法术")
        else:
            pt = self.yolo.find_center_click(self.win, class_filter={"主鬼"}, conf=0.35)
            if pt:
                self.inp.click_window(self.win, pt[0], pt[1])
            else:
                self._log.warning("未检测到主鬼，仍尝试进入回合（需完善战斗逻辑）")
        time.sleep(1.0)
        self._live("after_combat", dry_run=self.cfg.strategy.dry_run)
        self.state = GhostState.TURN_IN

    def _do_turn_in(self) -> None:
        if self.path.goto_npc_config("钟馗"):
            self._log.info("已发钟馗坐标寻路，对话交任务需后续模板/OCR")
        self._live("after_turn_in_zhongkui")
        self.state = GhostState.NEXT_ROUND

    def _do_next_round(self) -> None:
        if self.round_index >= self.cfg.strategy.max_rounds:
            self._log.info("已达 max_rounds=%s，停止", self.cfg.strategy.max_rounds)
            self._live("stopped_max_rounds", max_rounds=self.cfg.strategy.max_rounds)
            self.state = GhostState.STOP
            return
        self._live("next_round_to_parse")
        self.state = GhostState.PARSE_TASK
