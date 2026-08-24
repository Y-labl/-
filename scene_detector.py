# -*- coding: utf-8 -*-
"""
场景检测（小地图颜色 + 特征点颜色）—— OCR 场景名识别的降级方案。

使用方式:
    from scene_detector import detect_position
    name, method = detect_position(serial, frame, scale_x, scale_y, ocr_map_name)

说明:
    - detect_position 优先返回 OCR 给出的地图名（method="ocr"）；
    - OCR 无结果时，才尝试按小地图/特征点颜色识别场景（method="color_l1"/"color_l2"）；
    - 颜色指纹基于 screenshots/旧/ 六张主界面截图标定（子母河底/凤巢三层/龙窟三层/
      女娲神迹/小雷音寺/小西天），其他场景未被标定，颜色路径不会命中
      （返回 None，调用方按"检测失败"处理）。
"""

import cv2
import numpy as np


# ========== 小地图颜色检测（OCR 失败时的降级路径） ==========
# 采样点：800x448 流坐标下画面中右部的一个 10x10 色块（历史遗留坐标，实测可区分场景主色调）。
# 指纹来源：screenshots/旧/ 下"战斗结束后主界面"截图采样
#   - 2026_07_29_009.png            -> 子母河底
#   - 2026_07_30_007.png            -> 凤巢三层
#   - 2026_07_30_009.png            -> 龙窟三层
#   - 2026_07_30_004.png            -> 女娲神迹
#   - 2026_07_29_008.png            -> 小雷音寺
#   - screenshot_20260712_235102.png -> 小西天
# 注意：指纹为单帧采样，角色移动到同图其他位置时颜色可能漂移；且仅覆盖上述六场景，
#       未标定的场景（如龙窟五层、凤巢四层）不会被颜色路径命中（返回 None，
#       由调用方按"检测失败"处理，不会误匹配到已标定场景）。
MINIMAP_SAMPLE = {"x": 453, "y": 106, "w": 10, "h": 10}

SCENE_COLOR_FINGERPRINTS = {
    "子母河底": [(5, 124, 114, 25)],
    "凤巢三层": [(245, 150, 44, 25)],
    "龙窟三层": [(14, 52, 100, 25)],
    "女娲神迹": [(84, 163, 44, 25)],
    "小雷音寺": [(141, 114, 69, 25)],
    "小西天": [(105, 81, 25, 25)],
}

# ========== 特征点颜色检测（OCR 失败时的降级路径） ==========
# 每个场景若干特征点 (x, y, r, g, b, 容差)，x/y 为 800x448 流坐标。
# 与 SCENE_COLOR_FINGERPRINTS 同源标定（六张主界面截图）。
SCENE_POINT_FINGERPRINTS = {
    "子母河底": [(200, 150, 14, 63, 121, 25), (350, 250, 51, 128, 129, 25), (500, 300, 50, 94, 107, 25)],
    "凤巢三层": [(200, 150, 130, 80, 21, 25), (350, 250, 139, 89, 38, 25), (500, 300, 61, 7, 3, 25)],
    "龙窟三层": [(200, 150, 23, 104, 161, 25), (350, 250, 4, 104, 166, 25), (500, 300, 12, 64, 123, 25)],
    "女娲神迹": [(200, 150, 203, 206, 182, 25), (350, 250, 163, 170, 136, 25), (500, 300, 88, 87, 72, 25)],
    "小雷音寺": [(200, 150, 162, 134, 84, 25), (350, 250, 190, 123, 44, 25), (500, 300, 227, 193, 139, 25)],
    "小西天": [(200, 150, 165, 160, 72, 25), (350, 250, 64, 54, 47, 25), (500, 300, 113, 108, 43, 25)],
}


def _stream_sample(frame, x, y, w, h, scale_x=1.0, scale_y=1.0):
    """在 frame 上按流坐标采样一个区域。

    frame 已是 800x448 流坐标时直接用流坐标；否则（防御性）按 scale 放大换算。
    历史实现里用 x/scale_x 除法换算，在 800x448 帧上会把采样点缩到错误位置，
    这里修正为乘法。
    """
    fh, fw = frame.shape[:2]
    if (fw, fh) == (800, 448):
        sx, sy, sw, sh = x, y, w, h
    else:
        sx, sy = int(x * scale_x), int(y * scale_y)
        sw, sh = max(1, int(w * scale_x)), max(1, int(h * scale_y))
    if sx < 0 or sy < 0 or sx + sw > fw or sy + sh > fh:
        return None
    roi = frame[sy:sy + sh, sx:sx + sw]
    if roi.size == 0:
        return None
    return roi


def _calculate_per_color(roi):
    """取 ROI 平均色，返回 RGB 顺序（cv2.mean 返回 BGR，这里转成 RGB 与指纹数据一致）。"""
    if roi is None:
        return 0, 0, 0
    m = cv2.mean(roi)
    return m[2], m[1], m[0]


def detect_by_minimap_color(frame, scale_x=1.0, scale_y=1.0):
    """按小地图采样点颜色识别场景；返回 (场景名, 置信度) 或 (None, 0.0)。"""
    if frame is None:
        return None, 0.0
    roi = _stream_sample(frame, MINIMAP_SAMPLE["x"], MINIMAP_SAMPLE["y"],
                         MINIMAP_SAMPLE["w"], MINIMAP_SAMPLE["h"], scale_x, scale_y)
    r, g, b = _calculate_per_color(roi)
    best_match = None
    best_score = 0.0
    for scene_name, fingerprints in SCENE_COLOR_FINGERPRINTS.items():
        for fr, fg, fb, tol in fingerprints:
            dr = abs(r - fr)
            dg = abs(g - fg)
            db = abs(b - fb)
            if dr < tol and dg < tol and db < tol:
                score = max(0.0, 1.0 - (dr + dg + db) / (tol * 3))
                if score > best_score:
                    best_score = score
                    best_match = scene_name
    return best_match, best_score


def _match_point_colors(frame, area_points_list, scale_x=1.0, scale_y=1.0):
    """按多特征点颜色识别场景；返回 (场景名, 置信度) 或 (None, 0.0)。"""
    if frame is None:
        return None, 0.0
    best_name = None
    best_score = 0.0
    for scene_name, points in area_points_list.items():
        match_count = 0
        total_score = 0.0
        for px, py, pr, pg, pb, ptol in points:
            roi = _stream_sample(frame, px, py, 1, 1, scale_x, scale_y)
            if roi is None:
                continue
            pixel = roi[0, 0]
            dr = abs(int(pixel[2]) - pr)
            dg = abs(int(pixel[1]) - pg)
            db = abs(int(pixel[0]) - pb)
            if dr < ptol and dg < ptol and db < ptol:
                match_count += 1
                score = max(0.0, 1.0 - (dr + dg + db) / (ptol * 3))
                total_score += score
        if match_count > 0:
            avg_score = total_score / len(points)
            if avg_score > best_score:
                best_score = avg_score
                best_name = scene_name
    return best_name, best_score


def detect_by_point_colors(frame, scale_x=1.0, scale_y=1.0):
    return _match_point_colors(frame, SCENE_POINT_FINGERPRINTS, scale_x, scale_y)


def detect_position(serial, frame, scale_x=1.0, scale_y=1.0, ocr_map_name=None):
    """场景检测总入口：优先用 OCR 场景名；无 OCR 结果时降级到颜色识别。

    返回 (场景名, 识别方式)，识别方式为 "ocr" / "color_l1" / "color_l2"；
    都未命中时返回 (None, None)。
    """
    if ocr_map_name:
        return ocr_map_name, "ocr"
    name_l1, conf_l1 = detect_by_minimap_color(frame, scale_x, scale_y)
    if name_l1 and conf_l1 > 0.7:
        return name_l1, "color_l1"
    name_l2, conf_l2 = detect_by_point_colors(frame, scale_x, scale_y)
    if name_l2 and conf_l2 > 0.5:
        return name_l2, "color_l2"
    return None, None
