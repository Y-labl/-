# -*- coding: utf-8 -*-
"""图像识别 - OpenCV 模板匹配 + 颜色检测（参考小霸王 img_util.py）"""
import time
import numpy as np
import cv2

# ---- 中文路径兼容 ----

def _imread(filepath):
    """cv2.imread 不支持中文路径，用 np.fromfile + imdecode 代替"""
    try:
        return cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception:
        return None

# ---- 模板匹配 ----

def find_template(frame_bgr, template_path, threshold=0.75, region=None):
    """在截图中查找模板，返回 (x, y, confidence) 或 None"""
    template = _imread(template_path)
    if template is None or frame_bgr is None:
        return None
    if region:
        rx, ry, rw, rh = region
        frame_bgr = frame_bgr[ry:ry+rh, rx:rx+rw]
        ox, oy = rx, ry
    else:
        ox, oy = 0, 0
    th, tw = template.shape[:2]
    sh, sw = frame_bgr.shape[:2]
    if th > sh or tw > sw:
        return None
    result = cv2.matchTemplate(frame_bgr, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        return (max_loc[0] + ox, max_loc[1] + oy, float(max_val))
    return None

def find_all_templates(frame_bgr, template_path, threshold=0.75, region=None):
    """查找所有匹配位置（NMS去重）"""
    template = _imread(template_path)
    if template is None or frame_bgr is None:
        return []
    if region:
        rx, ry, rw, rh = region
        frame_bgr = frame_bgr[ry:ry+rh, rx:rx+rw]
        ox, oy = rx, ry
    else:
        ox, oy = 0, 0
    th, tw = template.shape[:2]
    result = cv2.matchTemplate(frame_bgr, template, cv2.TM_CCOEFF_NORMED)
    locs = np.where(result >= threshold)
    points = []
    for pt in zip(*locs[::-1]):
        x, y = pt[0] + ox, pt[1] + oy
        conf = float(result[pt[1], pt[0]])
        if not any(abs(x-px) < tw//2 and abs(y-py) < th//2 for px, py, _ in points):
            points.append((x, y, conf))
    return points

# ---- 颜色工具 ----

def get_color(frame_bgr, x, y):
    """获取像素颜色 (R, G, B)"""
    try:
        if frame_bgr is not None and 0 <= y < frame_bgr.shape[0] and 0 <= x < frame_bgr.shape[1]:
            b, g, r = frame_bgr[y, x]
            return (int(r), int(g), int(b))
    except: pass
    return (0, 0, 0)

def match_colors(frame_bgr, points, check_fn, error_ratio=0.3):
    """多点颜色匹配"""
    if frame_bgr is None: return False
    ok = sum(1 for x, y in points if check_fn(*get_color(frame_bgr, x, y)))
    return ok >= len(points) * (1 - error_ratio)
