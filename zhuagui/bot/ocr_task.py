from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

from PIL import Image

from .models import GhostTaskInfo

# 减轻首次联网检查耗时（可在外部环境变量覆盖）
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# 地图名 + 坐标；「境外/郊外/国境」须长于单字「境」，避免「大唐境外」被切成「大唐境」（见需求文档 §4.1.7 示例）
_MAP_SUFFIX = r"(?:村|洲|国境|境外|郊外|国|境|城|府|岛|山|洞|塔|岭|原|迷宫|地府|酆都)"
_LINE_RE = re.compile(
    rf"([\u4e00-\u9fff]{{2,16}}{_MAP_SUFFIX})\D{{0,8}}(\d{{1,3}})\s*[,，]?\s*(\d{{1,3}})"
)
# 文档示例：长寿村 200 150（空格分隔、无逗号）
_SPACE_XY_RE = re.compile(
    rf"([\u4e00-\u9fff]{{2,16}}{_MAP_SUFFIX})\s+(\d{{1,3}})\s+(\d{{1,3}})(?!\d)"
)
_FALLBACK_XY = re.compile(r"(\d{1,3})\s*[,，]\s*(\d{1,3})")
_GHOST_PATTERN = re.compile(r"(女鬼|男鬼|僵尸|骷髅|幽魂|牛头|马面|野鬼|吸血鬼)")
_LOC_STRIP_PREFIXES = ("前往", "去往", "到", "去", "飞向")


def _normalize_map_name(loc: str) -> str:
    s = loc.strip()
    for p in _LOC_STRIP_PREFIXES:
        if s.startswith(p) and len(s) > len(p):
            return s[len(p) :].strip()
    return s


def is_empty_task_tracker(text: str) -> bool:
    """任务栏明确显示「没有任何追踪任务」（与 debug_run 截图/OCR 对照用）。"""
    if not (text and text.strip()):
        return False
    compact = (
        text.replace(" ", "")
        .replace("\u3000", "")
        .replace("？", "?")
        .replace("?", "")
    )
    markers = (
        "当前追踪列表没有任务",
        "追踪列表没有任务",
        "列表没有任务",
        "没有任务",
        "暂无任务",
        "暂无追踪任务",
        "任务列表为空",
    )
    return any(m in compact for m in markers)


def parse_task_text(text: str, task_number: int = 0) -> GhostTaskInfo:
    log = logging.getLogger(__name__)
    text = text.replace("\n", " ").strip()
    info = GhostTaskInfo(task_number=task_number, raw_text=text, confidence=0.3)
    if not text:
        return info

    m = _LINE_RE.search(text)
    if m:
        loc, xs, ys = m.group(1), m.group(2), m.group(3)
        x, y = int(xs), int(ys)
        if 0 < x < 1000 and 0 < y < 1000:
            info.location = _normalize_map_name(loc)
            info.coordinates = (x, y)
            info.confidence = 0.8
    if not info.has_target:
        ms = _SPACE_XY_RE.search(text)
        if ms:
            loc, xs, ys = ms.group(1), ms.group(2), ms.group(3)
            x, y = int(xs), int(ys)
            if 0 < x < 1000 and 0 < y < 1000:
                info.location = _normalize_map_name(loc)
                info.coordinates = (x, y)
                info.confidence = max(info.confidence, 0.75)
    if not info.has_target:
        m2 = _FALLBACK_XY.search(text)
        if m2:
            x, y = int(m2.group(1)), int(m2.group(2))
            if 0 < x < 1000 and 0 < y < 1000:
                info.coordinates = (x, y)
                info.confidence = max(info.confidence, 0.5)

    gm = _GHOST_PATTERN.search(text)
    if gm:
        info.ghost_type = gm.group(1)
        info.confidence = min(0.95, info.confidence + 0.1)

    if not info.has_target:
        log.warning("未能从任务文本解析出有效坐标: %s", text[:120])
    return info


def _create_paddle_ocr():
    """兼容 PaddleOCR 2.x 与 3.x（3.x 不再支持 show_log 等旧参数）。"""
    from paddleocr import PaddleOCR  # type: ignore

    attempts: tuple[dict[str, Any], ...] = (
        {"lang": "ch"},
        {"lang": "ch", "use_textline_orientation": True},
        {"use_angle_cls": True, "lang": "ch", "show_log": False},
        {"use_angle_cls": True, "lang": "ch"},
    )
    last: Exception | None = None
    for kw in attempts:
        try:
            return PaddleOCR(**kw)
        except (TypeError, ValueError) as e:
            last = e
    assert last is not None
    raise last


def _lines_from_paddle_result(result: Any) -> list[str]:
    """解析 ocr()/predict() 返回值：支持 PP-OCRv3+ 的 rec_texts 与 2.x 的 [[[box], (txt, conf)], ...]。"""
    lines: list[str] = []
    if not result:
        return lines
    for page in result:
        if page is None:
            continue
        rec = None
        if isinstance(page, dict):
            rec = page.get("rec_texts")
        elif hasattr(page, "get"):
            rec = page.get("rec_texts")  # type: ignore[union-attr]
        if rec:
            lines.extend(str(t) for t in rec if t)
            continue
        if isinstance(page, (list, tuple)):
            for line in page:
                if not line or len(line) < 2:
                    continue
                item = line[1]
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    lines.append(str(item[0]))
                elif isinstance(item, str):
                    lines.append(item)
    return lines


def ocr_task_image(img: Image.Image, task_number: int = 0) -> GhostTaskInfo:
    text = ""
    log = logging.getLogger(__name__)
    try:
        import numpy as np

        ocr = _create_paddle_ocr()
        arr = np.array(img.convert("RGB"))
        try:
            result = ocr.ocr(arr, cls=True)
        except TypeError:
            result = ocr.predict(arr, use_textline_orientation=True)
        parts = _lines_from_paddle_result(result)
        text = " ".join(parts)
    except Exception as e:
        log.warning("PaddleOCR 不可用或失败: %s", e)

    return parse_task_text(text, task_number=task_number)


def parse_task_from_image(img: Optional[Image.Image], task_number: int = 0) -> GhostTaskInfo:
    if img is None:
        return GhostTaskInfo(task_number=task_number, raw_text="", confidence=0.0)
    return ocr_task_image(img, task_number=task_number)
