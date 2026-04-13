"""与《抓鬼任务需求文档》§2.1 主流程对齐的说明（日志 / 自检，非游戏内硬编码流程）。"""

from __future__ import annotations

import logging

# 文档 §2.1 步骤编号 → 程序侧对应关系（便于对照截图与 debug_run）
STEPS_S21: tuple[tuple[int, str], ...] = (
    (1, "组队 5 人 — strategy.assume_party_ready"),
    (2, "马副将领双倍 — ChanganPrep + enable_double_exp"),
    (3, "长安导标飞驿站 — guide_flag"),
    (4, "驿站老板→大唐国境 — ChanganPrep._segment_yizhan"),
    (5, "国境→地府 — prep_ghost.manual_travel_to_difu_s / 人工跑图或飞行符"),
    (6, "黑无常鬼王（可选）— strategy.enable_guowang"),
    (7, "钟馗领抓鬼 — GhostQuestAcceptFlow"),
    (8, "天眼通符（可选）— strategy.enable_tianyan（代码未接时仅告警）"),
    (9, "OCR 任务栏 — PARSE_TASK"),
    (10, "坐标寻路 — GOTO_TARGET（端游 Alt+G 为给予，默认关；需另接任务追踪/小地图等）"),
    (11, "战斗 — COMBAT"),
    (12, "回钟馗/下一轮 — TURN_IN + NEXT_ROUND"),
)


def log_pipeline_vs_doc(logger: logging.Logger) -> None:
    lines = ["《抓鬼任务需求文档》§2.1 步骤 ↔ 当前程序："]
    for n, desc in STEPS_S21:
        lines.append(f"  {n:2d}. {desc}")
    logger.info("\n".join(lines))
