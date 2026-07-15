# -*- coding: utf-8 -*-
"""
?????? - ???????????? + ??????
"""

import cv2
import numpy as np


# ========== ???????????? ==========

MINIMAP_SAMPLE = {"x": 453, "y": 106, "w": 10, "h": 10}

SCENE_COLOR_FINGERPRINTS = {
    "???": [(148, 138, 118, 25)],
    "????": [(170, 155, 145, 25)],
    "??": [(100, 115, 65, 20)],
    "?????": [(135, 142, 100, 20)],
}


SCENE_POINT_FINGERPRINTS = {
    "???": [(200, 150, 148, 138, 118, 25), (350, 250, 145, 135, 115, 25), (500, 300, 150, 140, 120, 25)],
    "????": [(200, 150, 170, 155, 145, 25), (350, 250, 165, 150, 140, 25), (500, 300, 175, 160, 150, 25)],
}


def _calculate_per_color(frame, x, y, w, h):
    roi = frame[y:y+h, x:x+w]
    if roi.size == 0:
        return 0, 0, 0
    mean = cv2.mean(roi)
    return mean[0], mean[1], mean[2]


def detect_by_minimap_color(frame, scale_x=1.0, scale_y=1.0):
    if frame is None:
        return None, 0.0
    h, w = frame.shape[:2]
    sx = int(MINIMAP_SAMPLE["x"] / scale_x)
    sy = int(MINIMAP_SAMPLE["y"] / scale_y)
    sw = max(1, int(MINIMAP_SAMPLE["w"] / scale_x))
    sh = max(1, int(MINIMAP_SAMPLE["h"] / scale_y))
    if sx + sw > w or sy + sh > h:
        return None, 0.0
    r, g, b = _calculate_per_color(frame, sx, sy, sw, sh)
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
    if frame is None:
        return None, 0.0
    fh, fw = frame.shape[:2]
    best_name = None
    best_score = 0.0
    for scene_name, points in area_points_list.items():
        match_count = 0
        total_score = 0.0
        for px, py, pr, pg, pb, ptol in points:
            sx = int(px / scale_x)
            sy = int(py / scale_y)
            if sx >= fw or sy >= fh or sx < 0 or sy < 0:
                continue
            pixel = frame[sy, sx]
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
    if ocr_map_name:
        return ocr_map_name, "ocr"
    name_l1, conf_l1 = detect_by_minimap_color(frame, scale_x, scale_y)
    if name_l1 and conf_l1 > 0.7:
        return name_l1, "color_l1"
    name_l2, conf_l2 = detect_by_point_colors(frame, scale_x, scale_y)
    if name_l2 and conf_l2 > 0.5:
        return name_l2, "color_l2"
    return None, None
