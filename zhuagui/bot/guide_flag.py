from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Literal, Optional

import cv2
import numpy as np
from PIL import Image

from .cursor_align import align_pointer_to_window_target, park_mouse_in_window, park_mouse_in_window_norm
from .input_ctrl import InputController
from .settings import BotSettings, CursorSettings, GuideFlagSettings
from .window import GameWindow
from .yolo_client import YoloNpcClient

Dest = Literal["mafujiang", "yizhan"]


def guide_flag_slot_window_xy(win: GameWindow, gf: GuideFlagSettings) -> tuple[int, int]:
    """长安导标旗所在物品格中心，窗口像素坐标（与截图坐标系一致）。"""
    r = win.rect()
    if not r:
        return 0, 0
    _l, _t, w, h = r
    gx, gy = gf.first_slot_center_norm
    step = gf.slot_spacing_x_norm
    idx = gf.changan_slot_index
    wx = int(w * (gx + idx * step))
    wy = int(h * gy)
    return wx, wy


def open_inventory_from_settings(
    gf: GuideFlagSettings,
    win: GameWindow,
    inp: InputController,
    cursor: CursorSettings,
) -> None:
    """先移鼠标到窗口配置比例（默认中心附近）、点一下确保焦点，再 Alt+E 打开道具栏。"""
    nx, ny = gf.park_before_inventory_norm
    park_mouse_in_window_norm(win, cursor, (float(nx), float(ny)))

    # 点一下任务追踪区域（右侧 inert UI），确保游戏拿到焦点（否则 Alt+E 会发到终端）
    r = win.rect()
    if r:
        wx = int(r[2] * 0.82)
        wy = int(r[3] * 0.25)
        inp.click_window(win, wx, wy)
        time.sleep(0.2)

    # 梦幻西游：Alt+E 打开道具栏
    hk = gf.open_inventory
    if len(hk) >= 2 and hk[0].lower() == "alt":
        inp.hotkey("alt", hk[1].lower())
    else:
        inp.hotkey(*[k.lower() for k in hk])
    time.sleep(gf.after_open_inventory_s)

    if gf.open_inventory_use_icon_click:
        r = win.rect()
        if r:
            nx, ny = gf.inventory_icon_click_norm
            inp.click_window(win, int(r[2] * nx), int(r[3] * ny))
            time.sleep(0.2)


def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def _match_best_score(screen_bgr: np.ndarray, template_bgr: np.ndarray) -> tuple[float, float]:
    """返回彩色与灰度匹配的最高分（不设阈值），用于诊断。"""
    th, tw = template_bgr.shape[:2]
    sh, sw = screen_bgr.shape[:2]
    if th > sh or tw > sw:
        return 0.0, 0.0
    r1 = cv2.matchTemplate(screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)
    _, best_c, _, _ = cv2.minMaxLoc(r1)
    search_g = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY) if screen_bgr.ndim == 3 else screen_bgr
    tpl_g = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY) if template_bgr.ndim == 3 else template_bgr
    r2 = cv2.matchTemplate(search_g, tpl_g, cv2.TM_CCOEFF_NORMED)
    _, best_g, _, _ = cv2.minMaxLoc(r2)
    return float(best_c), float(best_g)


def _match_template(
    screen_bgr: np.ndarray, template_bgr: np.ndarray, threshold: float, grayscale: bool = False
) -> Optional[tuple[int, int, float]]:
    th, tw = template_bgr.shape[:2]
    sh, sw = screen_bgr.shape[:2]
    if th > sh or tw > sw:
        return None
    search = screen_bgr
    tpl = template_bgr
    if grayscale:
        search = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY) if screen_bgr.ndim == 3 else screen_bgr
        tpl = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY) if template_bgr.ndim == 3 else template_bgr
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    _min_v, max_v, _min_loc, max_loc = cv2.minMaxLoc(res)
    if max_v < threshold:
        return None
    cx = int(max_loc[0] + tw / 2)
    cy = int(max_loc[1] + th / 2)
    return cx, cy, float(max_v)


def _is_guide_map_open(screen_bgr: np.ndarray, marker_tpl: np.ndarray, threshold: float = 0.60) -> bool:
    """判断导标地图面板是否已弹出。"""
    th, tw = marker_tpl.shape[:2]
    sh, sw = screen_bgr.shape[:2]
    if th > sh or tw > sw:
        return False
    res = cv2.matchTemplate(screen_bgr, marker_tpl, cv2.TM_CCOEFF_NORMED)
    _min_v, max_v, _min_loc, _max_loc = cv2.minMaxLoc(res)
    return bool(max_v >= threshold)


def _find_dest_marker_by_color(
    screen_bgr: np.ndarray,
    dest: Dest,
) -> Optional[tuple[int, int, float]]:
    """
    在右侧地图交互区域内，按颜色阈值找目标传送点（glow 节点）。

    返回窗口内坐标 (wx, wy, score)，其中 score 仅用于挑选更“像”的候选点。
    """
    h, w = screen_bgr.shape[:2]
    # 传送点通常出现在右侧地图交互区域；限制 ROI 可显著减少误检
    x0 = int(w * 0.42)
    y0 = int(h * 0.30)
    x1 = int(w * 0.98)
    y1 = int(h * 0.95)
    x0 = max(0, min(x0, w - 1))
    y0 = max(0, min(y0, h - 1))
    x1 = max(x0 + 1, min(x1, w))
    y1 = max(y0 + 1, min(y1, h))

    roi = screen_bgr[y0:y1, x0:x1]
    if roi.size == 0:
        return None

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # HSV: H in [0,179]
    # mafujiang 通常偏青蓝/蓝色节点；yizhan 常见偏橙黄/金色节点。
    if dest == "mafujiang":
        primary = [((75, 60, 60), (120, 255, 255))]  # cyan/blue
        secondary = [((0, 60, 60), (40, 255, 255))]  # orange/yellow
    else:
        primary = [((0, 60, 60), (40, 255, 255))]  # orange/yellow
        secondary = [((75, 60, 60), (120, 255, 255))]  # cyan/blue

    candidates: list[tuple[int, int, float]] = []

    def _collect(color_ranges: list[tuple[tuple[int, int, int], tuple[int, int, int]]], weight: float) -> None:
        mask = None
        for lo, hi in color_ranges:
            m = cv2.inRange(hsv, lo, hi)
            mask = m if mask is None else cv2.bitwise_or(mask, m)
        if mask is None:
            return
        # 轻微形态学处理，合并发光片
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return
        min_area = (w * h) * 0.00008  # 相对面积阈值
        for c in contours:
            area = float(cv2.contourArea(c))
            if area < min_area:
                continue
            M = cv2.moments(c)
            if M.get("m00", 0) == 0:
                continue
            cx = int(M["m10"] / M["m00"]) + x0
            cy = int(M["m01"] / M["m00"]) + y0
            candidates.append((cx, cy, area * weight))

    _collect(primary, 1.0)
    if not candidates:
        _collect(secondary, 0.8)

    if not candidates:
        return None

    # 选 area 最大的候选
    candidates.sort(key=lambda t: t[2], reverse=True)
    return candidates[0]


class GuideFlagChangan:
    """长安导标旗：打开道具栏 → 右键指定格 → 模板匹配地图上的红点 → 左键传送。"""

    def __init__(self, settings: BotSettings, window: GameWindow, inp: InputController):
        self._log = logging.getLogger(__name__)
        self._cfg = settings
        self._win = window
        self._inp = inp
        self._gf = settings.guide_flag
        self._yolo = YoloNpcClient(settings)

    def _verify_dest_npc(self, dest: Dest) -> bool:
        """点击传送点后，校验是否已到达对应 NPC（用 YOLO 做存在性验证）。"""
        if not self._yolo.available:
            return True
        class_filter = {"马副将"} if dest == "mafujiang" else {"驿站老板"}
        dets = self._yolo.detect_in_window(self._win, conf=self._cfg.prep_changan.yolo_npc_conf)
        return any(name in class_filter for name, _box, _cf in dets)

    def _close_guide_map_if_open(
        self,
        marker_tpl: Optional[np.ndarray],
        max_esc: int = 8,
    ) -> None:
        """如果导标地图面板仍未关闭，循环按 ESC 直到关闭或达到上限。"""
        if marker_tpl is None:
            for _ in range(self._gf.close_ui_esc_presses):
                self._inp.press("esc")
                time.sleep(0.15)
            return
        for _ in range(max_esc):
            img = self._win.capture()
            if not img:
                break
            screen_now = _pil_to_bgr(img)
            if not _is_guide_map_open(screen_now, marker_tpl, threshold=0.50):
                return
            self._inp.press("esc")
            time.sleep(0.25)

    def _template_path(self, dest: Dest) -> Path:
        root = Path(__file__).resolve().parent.parent
        name = self._gf.template_mafujiang if dest == "mafujiang" else self._gf.template_yizhan
        p = Path(name)
        if not p.is_absolute():
            p = root / p
        return p

    def _slot_center_window_xy(self) -> tuple[int, int]:
        return guide_flag_slot_window_xy(self._win, self._gf)

    def _find_flag_icon_screen_xy(self) -> Optional[tuple[int, int]]:
        """在背包区域内用模板匹配找导标旗图标中心，返回屏幕坐标；未找到返回 None。"""
        root = Path(__file__).resolve().parent.parent
        tpl_path = root / self._gf.template_icon
        if not tpl_path.is_file():
            return None
        r = self._win.rect()
        if not r:
            return None
        left, top, w, h = r
        # 仅在背包「物品格子区」内搜导标旗，避免误匹配到头像/场景元素
        inv_x0 = int(w * 0.04)
        inv_y0 = int(h * 0.46)
        inv_w = int(w * 0.34)
        inv_h = int(h * 0.42)

        # 一次性截图并在窗口坐标系里完成 matchTemplate，避免多候选“选错格子”
        img = self._win.capture()
        if not img:
            return None
        screen_bgr = _pil_to_bgr(img)
        sh, sw = screen_bgr.shape[:2]
        inv_x0 = max(0, min(inv_x0, sw - 1))
        inv_y0 = max(0, min(inv_y0, sh - 1))
        inv_w = max(1, min(inv_w, sw - inv_x0))
        inv_h = max(1, min(inv_h, sh - inv_y0))

        roi = screen_bgr[inv_y0 : inv_y0 + inv_h, inv_x0 : inv_x0 + inv_w]
        if roi.size == 0:
            return None

        tpl = cv2.imread(str(tpl_path), cv2.IMREAD_COLOR)
        if tpl is None:
            return None
        th, tw = tpl.shape[:2]
        if th > roi.shape[0] or tw > roi.shape[1]:
            return None

        # color match
        res_c = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_v_c, _, max_loc_c = cv2.minMaxLoc(res_c)

        # grayscale match
        roi_g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        tpl_g = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
        res_g = cv2.matchTemplate(roi_g, tpl_g, cv2.TM_CCOEFF_NORMED)
        _, max_v_g, _, max_loc_g = cv2.minMaxLoc(res_g)

        use_gray = max_v_g > max_v_c
        max_v = float(max_v_g if use_gray else max_v_c)
        max_loc = max_loc_g if use_gray else max_loc_c

        if max_v < self._gf.icon_match_threshold:
            return None

        cx = left + inv_x0 + int(max_loc[0]) + tw // 2
        cy = top + inv_y0 + int(max_loc[1]) + th // 2
        self._log.info(
            "导标旗图标模板 match 成功 conf=%.3f gray=%s at 屏幕(%s,%s)",
            max_v,
            use_gray,
            cx,
            cy,
        )
        return cx, cy

    def _open_inventory(self) -> None:
        open_inventory_from_settings(self._gf, self._win, self._inp, self._cfg.cursor)

    def fly_to(self, dest: Dest, debug_dir: Optional[Path] = None) -> bool:
        tpl_path = self._template_path(dest)
        tpl = cv2.imread(str(tpl_path))
        if tpl is None:
            self._log.error("无法读取模板图: %s", tpl_path)
            return False
        root = Path(__file__).resolve().parent.parent
        map_marker_path = root / "assets" / "guide_flag" / "map_close_btn_marker.png"
        map_marker_tpl = cv2.imread(str(map_marker_path))
        if map_marker_tpl is None:
            self._log.warning("未找到地图面板模板: %s（将不做地图弹出校验）", map_marker_path)

        park_mouse_in_window(self._win, self._cfg.cursor)

        for _ in range(self._gf.pre_fly_esc_presses):
            self._inp.press("esc")
            time.sleep(0.12)

        max_inv = int(getattr(self._gf, "max_inventory_open_attempts", 3))
        esc_retry = int(getattr(self._gf, "esc_before_reopen_inventory", 1))
        flag_xy = None
        for inv_attempt in range(max_inv):
            if inv_attempt > 0:
                self._log.info(
                    "第 %s 次仍未找到导标旗，先按 ESC×%s 再重新打开道具栏",
                    inv_attempt,
                    esc_retry,
                )
                for _ in range(max(0, esc_retry)):
                    self._inp.press("esc")
                    time.sleep(0.12)
            self._open_inventory()
            time.sleep(self._gf.after_open_inventory_s)
            flag_xy = self._find_flag_icon_screen_xy()
            if flag_xy:
                break
        dur = getattr(self._gf, "move_to_flag_duration_s", 0.35)
        if flag_xy:
            sx, sy = flag_xy
            r = self._win.rect()
            use_align = bool(getattr(self._gf, "align_after_move_to_flag", False))
        else:
            wx, wy = self._slot_center_window_xy()
            sx, sy = self._win.window_to_screen(wx, wy)
            r = self._win.rect()
            use_align = False
            self._log.info("未匹配到图标，改用比例名义坐标 (%s,%s) 右键", wx, wy)

        # 右键导标旗并校验地图是否弹出；未弹出则小范围偏移重试
        max_rc = int(getattr(self._gf, "max_flag_right_click_attempts", 5))
        offsets = [(0, 0), (8, 0), (-8, 0), (0, 8), (0, -8)]
        img: Optional[Image.Image] = None
        map_open = False
        for i in range(max(1, max_rc)):
            dx, dy = offsets[i % len(offsets)]
            tx, ty = sx + dx, sy + dy
            if use_align and r:
                left, top, _, _ = r
                wx2, wy2 = tx - left, ty - top
                self._log.info("右键导标旗第 %s 次：先缓慢移到(%s,%s)+偏移后对齐再右键", i + 1, sx, sy)
                self._inp.move_to_screen_point(tx, ty, duration=dur)
                time.sleep(0.12)
                align_pointer_to_window_target(self._win, self._cfg.cursor, self._log, wx2, wy2)
                time.sleep(0.08)
                self._inp.right_click_at_current()
            else:
                self._log.info("右键导标旗第 %s 次：屏幕(%s,%s)", i + 1, tx, ty)
                self._inp.right_click_screen(tx, ty, move_duration=dur if i == 0 else 0.08)
            time.sleep(self._gf.after_right_click_flag_s)
            # 截图前把鼠标移开，避免“坐标提示/鼠标尖端”遮挡地图面板标题导致误判未弹出
            r_check = self._win.rect()
            if r_check:
                safe_wx = int(r_check[2] * 0.20)
                safe_wy = int(r_check[3] * 0.18)
                self._inp.move_to_window(self._win, safe_wx, safe_wy)
                time.sleep(0.15)
            img = self._win.capture()
            if not img:
                continue
            if map_marker_tpl is None:
                # 无法校验时按原逻辑继续后续匹配
                map_open = True
                break
            screen_now = _pil_to_bgr(img)
            if _is_guide_map_open(screen_now, map_marker_tpl, threshold=0.60):
                map_open = True
                self._log.info("导标地图已弹出（第 %s 次右键）", i + 1)
                break
            self._log.warning("第 %s 次右键后未检测到导标地图，继续重试", i + 1)

        if not img:
            self._log.error("截图失败")
            return False
        if not map_open:
            self._log.error("连续右键后仍未弹出导标地图，请检查鼠标对齐/背包格配置")
            if debug_dir:
                debug_dir.mkdir(parents=True, exist_ok=True)
                img.save(debug_dir / f"fly_changan_map_not_open_{dest}.png")
            return False
        if debug_dir:
            debug_dir.mkdir(parents=True, exist_ok=True)
            img.save(debug_dir / f"fly_changan_before_match_{dest}.png")

        screen = _pil_to_bgr(img)
        # 只在地图面板右侧区域做传送点模板匹配，减少误匹配到其它元素
        h, w = screen.shape[:2]
        roi_x0 = int(w * 0.42)
        roi_y0 = int(h * 0.18)
        roi_x1 = int(w * 0.98)
        roi_y1 = int(h * 0.92)
        roi_x0 = max(0, min(roi_x0, w - 1))
        roi_y0 = max(0, min(roi_y0, h - 1))
        roi_x1 = max(roi_x0 + 1, min(roi_x1, w))
        roi_y1 = max(roi_y0 + 1, min(roi_y1, h))
        screen_roi = screen[roi_y0:roi_y1, roi_x0:roi_x1]

        # 传送点点击重试：地图上会显示鼠标当前坐标，可能遮挡/影响点击。
        # 因此：每次重试都重新截图并重新定位传送点；同时对点击点做小偏移。
        max_click_attempts = int(getattr(self._gf, "max_dest_click_attempts", 6))
        click_offsets = getattr(
            self._gf,
            "dest_click_offsets_px",
            [(0, 0), (0, -6), (0, 6), (-6, 0), (6, 0)],
        )

        for attempt in range(max_click_attempts):
            # 避免鼠标坐标提示遮住传送点：每轮先把鼠标移开，再截图重检
            r_now = self._win.rect()
            if r_now:
                safe_wx = int(r_now[2] * 0.20)
                safe_wy = int(r_now[3] * 0.18)
                self._inp.move_to_window(self._win, safe_wx, safe_wy)
                time.sleep(0.20)

            img_now = self._win.capture()
            if not img_now:
                continue
            screen_now = _pil_to_bgr(img_now)
            h2, w2 = screen_now.shape[:2]
            roi_x0_now = min(roi_x0, w2 - 1)
            roi_x1_now = min(roi_x1, w2)
            roi_y0_now = min(roi_y0, h2 - 1)
            roi_y1_now = min(roi_y1, h2)
            screen_roi_now = screen_now[roi_y0_now:roi_y1_now, roi_x0_now:roi_x1_now]

            # 1) 优先模板匹配
            hit_now = _match_template(screen_roi_now, tpl, self._gf.match_threshold, grayscale=False)
            if not hit_now and getattr(self._gf, "match_grayscale_fallback", True):
                hit_now = _match_template(screen_roi_now, tpl, self._gf.match_threshold, grayscale=True)
            if not hit_now:
                bc, bg = _match_best_score(screen_roi_now, tpl)
                self._log.info(
                    "传送点模板未达阈值：本帧 ROI 最高分 color=%.3f gray=%.3f（阈值 %.3f），可略降 guide_flag.match_threshold 或重截 changan_map_*.png",
                    bc,
                    bg,
                    self._gf.match_threshold,
                )
            if hit_now:
                cx, cy, conf = hit_now
                cx = cx + roi_x0_now
                cy = cy + roi_y0_now
                self._log.info("尝试点击传送点 attempt=%s conf=%.3f at (%s,%s)", attempt + 1, conf, cx, cy)
                for ox, oy in click_offsets:
                    tx, ty = cx + int(ox), cy + int(oy)
                    # 关键：强制按游戏内鼠标“尖端热点”对齐后再点击
                    self._inp.click_window(self._win, tx, ty, force_align=True)
                    self._inp.sleep_map()
                    time.sleep(self._gf.after_teleport_extra_s)
                    # 2) 若地图面板不再显示，认为传送成功
                    img_chk = self._win.capture()
                    if map_marker_tpl is None:
                        self._log.warning(
                            "未配置 assets/guide_flag/map_close_btn_marker.png，无法检测地图是否关闭；"
                            "已按传送点模板点击，假定传送已触发。请从本机导标地图截一张「关闭/角落」小图放入该路径以提高判定可靠性。"
                        )
                        self._close_guide_map_if_open(None, max_esc=2)
                        return True
                    if img_chk and map_marker_tpl is not None:
                        screen_chk = _pil_to_bgr(img_chk)
                        if not _is_guide_map_open(screen_chk, map_marker_tpl, threshold=0.60):
                            self._log.info("导标地图已关闭，判定传送成功（attempt=%s）", attempt + 1)
                            # 额外再兜底按 ESC，确保不残留菜单
                            self._close_guide_map_if_open(map_marker_tpl, max_esc=2)
                            return True
                continue

            # 3) 模板找不到：YOLO / 颜色兜底也同样要在重试框架内进行
            if self._yolo.available:
                yolo_classes = {"马副将"} if dest == "mafujiang" else {"驿站老板"}
                pt = self._yolo.find_center_click(
                    self._win,
                    class_filter=yolo_classes,
                    conf=self._cfg.prep_changan.yolo_npc_conf,
                )
                if pt:
                    self._log.info("YOLO 找到 %s，尝试点击 (%s,%s)", dest, pt[0], pt[1])
                    self._inp.click_window(self._win, pt[0], pt[1])
                    self._inp.sleep_map()
                    time.sleep(self._gf.after_teleport_extra_s)
                    img_chk = self._win.capture()
                    if map_marker_tpl is None:
                        self._log.warning(
                            "YOLO 点击后无 map_close_btn_marker 模板，假定传送已触发（请补该 PNG）"
                        )
                        self._close_guide_map_if_open(None, max_esc=2)
                        return True
                    if img_chk and map_marker_tpl is not None:
                        screen_chk = _pil_to_bgr(img_chk)
                        if not _is_guide_map_open(screen_chk, map_marker_tpl, threshold=0.60):
                            return True

            color_hit = _find_dest_marker_by_color(screen_now, dest)
            if color_hit:
                cx, cy, score = color_hit
                self._log.info("颜色定位传送点 attempt=%s score=%.1f at (%s,%s)", attempt + 1, score, cx, cy)
                self._inp.click_window(self._win, cx, cy)
                self._inp.sleep_map()
                time.sleep(self._gf.after_teleport_extra_s)
                img_chk = self._win.capture()
                if map_marker_tpl is None:
                    self._log.warning(
                        "颜色兜底点击后无 map_close_btn_marker 模板，假定传送已触发（请补该 PNG）"
                    )
                    self._close_guide_map_if_open(None, max_esc=2)
                    return True
                if img_chk and map_marker_tpl is not None:
                    screen_chk = _pil_to_bgr(img_chk)
                    if not _is_guide_map_open(screen_chk, map_marker_tpl, threshold=0.60):
                        return True

        # 全部重试仍失败
        if debug_dir:
            img.save(debug_dir / f"fly_changan_match_fail_{dest}.png")
        self._log.error(
            "传送点点击重试失败：dest=%s，仍未能关闭导标地图面板（可能点击仍被遮挡）",
            dest,
        )
        return False


def run_probe_flag_slot(settings: BotSettings, out_root: Path) -> bool:
    """
    开道具栏 → 仅用名义坐标把鼠标移到导标格中心 → 截图标红圈，不右键。
    用于校准 guide_flag.first_slot_center_norm / slot_spacing_x_norm。
    """
    log = logging.getLogger(__name__)
    win = GameWindow(settings)
    if not win.find():
        return False
    win.activate()
    log.info("3 秒内请点一下游戏窗口；随后开背包并只移动鼠标到格子中心（不右键）")
    time.sleep(3.0)
    settings.strategy.dry_run = False
    inp = InputController(settings)
    park_mouse_in_window(win, settings.cursor)
    open_inventory_from_settings(settings.guide_flag, win, inp, settings.cursor)
    time.sleep(settings.guide_flag.after_open_inventory_s)
    gf = settings.guide_flag
    wx, wy = guide_flag_slot_window_xy(win, gf)
    log.info("目标格子窗口坐标 (%s,%s)", wx, wy)
    inp.move_to_window(win, wx, wy)
    time.sleep(0.35)
    img = win.capture()
    if not img:
        log.error("截图失败")
        return False
    bgr = _pil_to_bgr(img)
    cv2.circle(bgr, (wx, wy), 12, (0, 0, 255), 2)
    cv2.line(bgr, (wx - 18, wy), (wx + 18, wy), (0, 0, 255), 1)
    cv2.line(bgr, (wx, wy - 18), (wx, wy + 18), (0, 0, 255), 1)
    out = out_root / "bot_probe_flag_slot.png"
    cv2.imwrite(str(out), bgr)
    log.info("已保存 %s（红十字为配置计算的格子中心，请对准长安红旗）", out)
    return True


def run_probe_flag_icon(settings: BotSettings, out_root: Path) -> bool:
    """
    开道具栏 → 用 template_icon 在背包区域找导标旗 → 保存截图并标注匹配结果。
    用于校准 template_icon 或 icon_match_threshold。
    """
    log = logging.getLogger(__name__)
    win = GameWindow(settings)
    if not win.find():
        return False
    win.activate()
    log.info("3 秒内点一下游戏窗口，随后开背包并尝试匹配导标旗图标")
    time.sleep(3.0)
    settings.strategy.dry_run = False
    inp = InputController(settings)
    park_mouse_in_window(win, settings.cursor)
    open_inventory_from_settings(settings.guide_flag, win, inp, settings.cursor)
    time.sleep(settings.guide_flag.after_open_inventory_s)
    flyer = GuideFlagChangan(settings, win, inp)
    flag_xy = flyer._find_flag_icon_screen_xy()
    best_score = 0.0
    if not flag_xy:
        gf = settings.guide_flag
        root = Path(__file__).resolve().parent.parent
        tpl_path = root / gf.template_icon
        if tpl_path.is_file():
            img = win.capture()
            r = win.rect()
            if img and r:
                screen = _pil_to_bgr(img)
                tpl = cv2.imread(str(tpl_path))
                if tpl is not None:
                    _, _, w, h = r
                    rx, ry, rw, rh = int(w * 0.15), int(h * 0.25), int(w * 0.55), int(h * 0.65)
                    roi = screen[ry : ry + rh, rx : rx + rw]
                    if roi.size > 0 and tpl.shape[0] <= roi.shape[0] and tpl.shape[1] <= roi.shape[1]:
                        res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
                        _, best_score, _, _ = cv2.minMaxLoc(res)
                if best_score > 0:
                    log.warning("未匹配到导标旗图标，实际最高分=%.3f，可尝试将 icon_match_threshold 降到 %.2f", best_score, min(0.99, best_score - 0.05))
    img = win.capture()
    if not img:
        log.error("截图失败")
        return False
    r = win.rect()
    if not r:
        return False
    left, top, w, h = r
    bgr = _pil_to_bgr(img)
    inv_x0, inv_y0 = int(w * 0.15), int(h * 0.25)
    cv2.rectangle(bgr, (inv_x0, inv_y0), (inv_x0 + int(w * 0.55), inv_y0 + int(h * 0.65)), (0, 255, 0), 1)
    if flag_xy:
        lx, ly = flag_xy[0] - left, flag_xy[1] - top
        cv2.circle(bgr, (lx, ly), 15, (0, 255, 0), 2)
        log.info("匹配成功，图标中心窗口内约 (%s,%s)", lx, ly)
    else:
        log.warning("未匹配到导标旗图标，请检查 template_icon 或降低 icon_match_threshold（当前 %.2f）", settings.guide_flag.icon_match_threshold)
    out = out_root / "bot_probe_flag_icon.png"
    cv2.imwrite(str(out), bgr)
    log.info("已保存 %s（绿框为搜索区域，绿圈为匹配点）", out)
    return True


def run_guide_flag_fly_to(
    settings: BotSettings,
    dest: Dest,
    debug_dir: Optional[Path] = None,
) -> bool:
    """
    找窗 → 激活 → 鼠标移入窗口 → 开道具栏 → 右键长安旗格 → 模板匹配地图点 → 左键传送。
    供「抓鬼第一步」与 --fly-changan 复用。
    """
    log = logging.getLogger(__name__)
    win = GameWindow(settings)
    if not win.find():
        return False
    win.activate()
    # 脚本从终端启动时游戏常无焦点，Alt+E 会发到终端；给用户时间手动点一下游戏
    log.info("3 秒后开始操作，请先点一下游戏窗口确保在前台")
    time.sleep(3.0)
    park_mouse_in_window(win, settings.cursor)
    inp = InputController(settings)
    return GuideFlagChangan(settings, win, inp).fly_to(dest, debug_dir=debug_dir)
