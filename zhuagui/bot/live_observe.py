"""主流程实时截图：每步保存游戏窗口与任务栏 ROI，并追加 manifest.jsonl 供对照分析。"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

from .settings import BotSettings
from .window import GameWindow

_log = logging.getLogger(__name__)


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    return str(obj)


def write_step(
    cfg: BotSettings,
    win: GameWindow,
    session_dir: Path,
    seq: int,
    tag: str,
    *,
    round_idx: int,
    state_name: str,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """保存 *_full.png、*_task.png（可配置关闭），并追加一行 JSON 到 manifest.jsonl。"""
    lo = cfg.live_observe
    if not lo.enabled:
        return
    clock = time.strftime("%H%M%S")
    base = f"{seq:04d}_{tag}_{clock}"
    row: dict[str, Any] = {
        "seq": seq,
        "tag": tag,
        "unix_t": time.time(),
        "round": round_idx,
        "state": state_name,
    }
    r = win.rect()
    if r:
        row["window_rect_xywh"] = [r[0], r[1], r[2], r[3]]
    wobj = win.hwnd_window
    if wobj:
        row["window_title"] = wobj.title[:200]

    if lo.save_full_window:
        full = win.capture()
        if full:
            full.save(session_dir / f"{base}_full.png")
            row["saved_full"] = f"{base}_full.png"
        else:
            row["saved_full"] = None
            _log.warning("live_observe: 全窗截图失败 tag=%s", tag)

    if lo.save_task_tracker_roi:
        x0, y0, x1, y1 = cfg.roi.task_tracker
        roi_img = win.capture_roi_norm(x0, y0, x1, y1)
        if roi_img:
            roi_img.save(session_dir / f"{base}_task.png")
            row["saved_task_roi"] = f"{base}_task.png"
        else:
            row["saved_task_roi"] = None

    if extra:
        row["extra"] = _json_safe(extra)

    line = json.dumps(row, ensure_ascii=False)
    manifest = session_dir / "manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def new_session_dir(zhuagui_root: Path, cfg: BotSettings) -> Optional[Path]:
    if not cfg.live_observe.enabled:
        return None
    import datetime

    parent = zhuagui_root / cfg.live_observe.dir
    parent.mkdir(parents=True, exist_ok=True)
    sid = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    d = parent / sid
    d.mkdir(parents=True, exist_ok=True)
    return d
