from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np
import pyautogui
from PIL import Image

if TYPE_CHECKING:
    from .settings import CursorSettings
    from .window import GameWindow

# 对齐思路参考用户备份：在目标点附近截小区域做模板匹配 + 分象限用 move 渐进修正
# （修正 pyautogui.screenshot(region=) 须为 left,top,width,height，备份里用四角坐标易错）


def _zhuagui_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_template_path(rel: str) -> Path:
    p = Path(rel)
    if not p.is_absolute():
        p = _zhuagui_root() / p
    return p


def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def _read_template_bgra(path: Path) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """返回 (BGR 三通道, mask 或 None)。支持带 Alpha 的 PNG（matchTemplate 用 mask）。"""
    tpl = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if tpl is None:
        return None, None
    if len(tpl.shape) == 2:
        return cv2.cvtColor(tpl, cv2.COLOR_GRAY2BGR), None
    if tpl.shape[2] == 4:
        return tpl[:, :, :3], tpl[:, :, 3]
    return tpl, None


def find_cursor_hotspot(
    screen_bgr: np.ndarray,
    template_bgr: np.ndarray,
    hotspot_tx: int,
    hotspot_ty: int,
    threshold: float,
    mask: Optional[np.ndarray] = None,
) -> Optional[tuple[int, int, float]]:
    """返回热点在「当前 screen_bgr 坐标系」中的 (x, y) 及匹配分。"""
    th, tw = template_bgr.shape[:2]
    sh, sw = screen_bgr.shape[:2]
    if th > sh or tw > sw:
        return None
    if mask is not None:
        res = cv2.matchTemplate(
            screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED, mask=mask
        )
    else:
        res = cv2.matchTemplate(screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)
    _mv, max_v, _ml, max_loc = cv2.minMaxLoc(res)
    if max_v < threshold:
        return None
    hx = int(max_loc[0] + hotspot_tx)
    hy = int(max_loc[1] + hotspot_ty)
    return hx, hy, float(max_v)


def find_cursor_hotspot_best_on_bgr(
    screen_bgr: np.ndarray,
    cursor: "CursorSettings",
) -> Optional[tuple[int, int, float, int, int, str]]:
    htx, hty = cursor.hotspot_in_template
    paths: list[str] = [cursor.template_path]
    alt = (cursor.template_path_alt or "").strip()
    if alt and alt not in paths:
        paths.append(alt)

    best: Optional[tuple[int, int, float, int, int, str]] = None
    for rel in paths:
        p = _resolve_template_path(rel)
        tpl_bgr, mask = _read_template_bgra(p)
        if tpl_bgr is None:
            continue
        hit = find_cursor_hotspot(
            screen_bgr, tpl_bgr, htx, hty, cursor.match_threshold, mask
        )
        if hit is None:
            continue
        hx, hy, conf = hit
        th, tw = tpl_bgr.shape[:2]
        if best is None or conf > best[2]:
            best = (hx, hy, conf, tw, th, rel)
    return best


def find_cursor_hotspot_best(
    screen_bgr: np.ndarray,
    cursor: "CursorSettings",
) -> Optional[tuple[int, int, float, int, int, str]]:
    """全图最优模板（与 find_cursor_hotspot_best_on_bgr 同名兼容）。"""
    return find_cursor_hotspot_best_on_bgr(screen_bgr, cursor)


def find_cursor_hotspot_best_in_roi(
    screen_bgr: np.ndarray,
    roi_x0: int,
    roi_y0: int,
    roi_w: int,
    roi_h: int,
    cursor: "CursorSettings",
) -> Optional[tuple[int, int, float, int, int, str]]:
    """在窗口截图的子矩形内匹配，返回热点在「整图」坐标系下的位置。"""
    h, w = screen_bgr.shape[:2]
    x0 = max(0, min(roi_x0, w - 1))
    y0 = max(0, min(roi_y0, h - 1))
    x1 = min(w, x0 + max(1, roi_w))
    y1 = min(h, y0 + max(1, roi_h))
    crop = screen_bgr[y0:y1, x0:x1]
    if crop.size == 0:
        return None
    det = find_cursor_hotspot_best_on_bgr(crop, cursor)
    if det is None:
        return None
    hx, hy, conf, tw, th, which = det
    return hx + x0, hy + y0, conf, tw, th, which


def _roi_around_target(
    win_w: int, win_h: int, tx: int, ty: int, pad: int
) -> tuple[int, int, int, int]:
    x0 = max(0, tx - pad)
    y0 = max(0, ty - pad)
    x1 = min(win_w, tx + pad)
    y1 = min(win_h, ty + pad)
    rw, rh = x1 - x0, y1 - y0
    if rw < 24 or rh < 24:
        return 0, 0, win_w, win_h
    return x0, y0, rw, rh


def _nudge_quadrant(
    cwx: int,
    cwy: int,
    twx: int,
    twy: int,
    min_px: int,
    half_thresh: int,
) -> tuple[int, int]:
    """按检测热点与目标象限，计算 pyautogui.move 的相对步长（与用户备份一致）。"""
    adx = abs(twx - cwx)
    ady = abs(twy - cwy)
    mx = max(min_px, adx // 2) if adx > half_thresh else min_px
    my = max(min_px, ady // 2) if ady > half_thresh else min_px
    if cwx <= twx and cwy <= twy:
        return mx, my
    if cwx <= twx and cwy >= twy:
        return mx, -my
    if cwx > twx and cwy < twy:
        return -mx, my
    return -mx, -my


def load_cursor_template_bgr(cursor: "CursorSettings") -> Optional[np.ndarray]:
    p = _resolve_template_path(cursor.template_path)
    bgr, _mask = _read_template_bgra(p)
    return bgr


def park_mouse_in_window(win: "GameWindow", cursor: "CursorSettings") -> None:
    r = win.rect()
    if not r:
        return
    _l, _t, w, h = r
    nx, ny = cursor.park_in_window_norm
    wx, wy = int(w * nx), int(h * ny)
    sx, sy = win.window_to_screen(wx, wy)
    pyautogui.moveTo(sx, sy, duration=0.06)
    time.sleep(cursor.park_delay_s)


def park_mouse_in_window_norm(
    win: "GameWindow", cursor: "CursorSettings", norm: tuple[float, float]
) -> None:
    """将系统鼠标移到窗口内指定比例位置（与截图坐标系一致）。"""
    r = win.rect()
    if not r:
        return
    _l, _t, w, h = r
    wx, wy = int(w * norm[0]), int(h * norm[1])
    sx, sy = win.window_to_screen(wx, wy)
    d = max(0.0, cursor.move_to_point_duration_s)
    pyautogui.moveTo(sx, sy, duration=d)
    time.sleep(cursor.park_delay_s)


def _cursor_templates_readable(cursor: "CursorSettings") -> bool:
    for rel in [cursor.template_path, (cursor.template_path_alt or "").strip()]:
        if not rel:
            continue
        bgr, _ = _read_template_bgra(_resolve_template_path(rel))
        if bgr is not None:
            return True
    return False


def align_pointer_to_window_target(
    win: "GameWindow",
    cursor: "CursorSettings",
    log: logging.Logger,
    target_wx: int,
    target_wy: int,
) -> bool:
    """
    将系统鼠标渐进移动到使游戏内指针热点接近 (target_wx, target_wy)。
    优先在目标点附近 ROI 内匹配指针模板；失败则全图再试；修正用 move 分象限步进。
    """
    if not _cursor_templates_readable(cursor):
        log.warning("未加载任何光标模板，跳过对齐")
        sx, sy = win.window_to_screen(target_wx, target_wy)
        pyautogui.moveTo(sx, sy, duration=0)
        return False

    park_mouse_in_window(win, cursor)

    sx0, sy0 = win.window_to_screen(target_wx, target_wy)
    pyautogui.moveTo(sx0, sy0, duration=0)

    r = win.rect()
    if not r:
        return False
    win_w, win_h = r[2], r[3]
    pad = max(32, cursor.align_search_padding_px)
    min_px = max(1, cursor.align_nudge_min_px)
    half_th = max(0, cursor.align_nudge_half_threshold_px)
    nudge_dur = max(0.0, cursor.align_nudge_duration_s)

    last_dx, last_dy = 0, 0
    for step in range(cursor.max_align_steps):
        pyautogui.PAUSE = 0
        time.sleep(cursor.settle_delay_s)

        img = win.capture()
        if not img:
            log.warning("对齐光标：截图失败")
            return False
        screen = _pil_to_bgr(img)

        rx, ry, rw, rh = _roi_around_target(win_w, win_h, target_wx, target_wy, pad)
        det = find_cursor_hotspot_best_in_roi(screen, rx, ry, rw, rh, cursor)
        if det is None:
            det = find_cursor_hotspot_best_on_bgr(screen, cursor)
        if det is None:
            log.warning(
                "对齐光标：第 %s 步未匹配到游戏鼠标（阈值 %.2f）",
                step + 1,
                cursor.match_threshold,
            )
            pyautogui.moveTo(sx0, sy0, duration=0)
            return False

        cwx, cwy, conf, _tw, _th, which = det
        last_dx = target_wx - cwx
        last_dy = target_wy - cwy
        log.debug(
            "光标对齐 step=%s tpl=%s 热点=(%s,%s) 目标=(%s,%s) Δ=(%s,%s) conf=%.3f roi=(%s,%s,%s,%s)",
            step + 1,
            which,
            cwx,
            cwy,
            target_wx,
            target_wy,
            last_dx,
            last_dy,
            conf,
            rx,
            ry,
            rw,
            rh,
        )
        if abs(last_dx) <= cursor.tolerance_px and abs(last_dy) <= cursor.tolerance_px:
            return True

        rx_step, ry_step = _nudge_quadrant(
            cwx, cwy, target_wx, target_wy, min_px, half_th
        )
        pyautogui.move(rx_step, ry_step, duration=nudge_dur)

    ok = abs(last_dx) <= cursor.tolerance_px * 2 and abs(last_dy) <= cursor.tolerance_px * 2
    if not ok:
        log.warning(
            "光标对齐未收敛：最后偏差 Δ=(%s,%s)，将仍尝试点击",
            last_dx,
            last_dy,
        )
    return ok
