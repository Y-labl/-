# -*- coding: utf-8 -*-
"""
本地四小人识别测试工具：对上传的游戏截图做识别并标注。

用法（供 GUI 测试页签调用）：
    from xbw_features.four_person.tester import analyze_four_person_image
    result = analyze_four_person_image(frame_bgr)
    # result["frame"] 为标注后的 BGR 图，result 含最佳槽位/置信度/点击点
"""

import cv2

from xbw_features.common.util.cnn_util import cnnUtil
from xbw_features.cw_changjing.cw_changjing_util import findFourPersonDetectArea
from xbw_features.four_person.detector import CONF_THRESHOLD

DEFAULT_ROI = (227, 80, 360, 150)


def _normalize_800x448(frame_bgr):
    """转正并缩放到 800x448 流分辨率（与游戏画面一致）。"""
    if frame_bgr is None:
        return None
    fh, fw = frame_bgr.shape[:2]
    if fh > fw:
        frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
    if frame_bgr.shape[1] != 800 or frame_bgr.shape[0] != 448:
        frame_bgr = cv2.resize(frame_bgr, (800, 448), interpolation=cv2.INTER_LINEAR)
    return frame_bgr


def analyze_four_person_image(frame_bgr, device_id="local"):
    """
    对上传截图做四小人本地识别：
      1) 归一化到 800x448；
      2) 候选 ROI = 默认标准区域(227,80,360,150) + “在/请”字检测区域；
      3) 每组 ROI 切 4 个 90 宽槽位做 CNN 打分，取最高分；
      4) 在图上标注 4 个槽位框、最佳槽位与点击点。

    :return: dict(success, roi, best_index, best_prob, slots, click_point, frame=标注图)
    """
    frame = _normalize_800x448(frame_bgr)
    if frame is None:
        return {"success": False, "error": "图片为空", "frame": None}

    # “在/请”字检测区域（与线上流程一致）
    try:
        det_roi = findFourPersonDetectArea(device_id, curframe=frame)
    except Exception:
        det_roi = (0, 0, 0, 0)

    det_roi = det_roi if (det_roi and det_roi[0] != 0) else DEFAULT_ROI
    best_roi, best_index, best_prob, best_slots = cnnUtil.best_four_person_roi(
        frame, det_roi[0], det_roi[1], det_roi[2], det_roi[3])
    if best_roi is None:
        return {"success": False, "error": "候选 ROI 均无法评分", "frame": frame}

    l, t, w, h = best_roi
    annotated = frame.copy()
    for i in range(4):
        x0, y0 = l + i * 90, t
        color = (0, 220, 0) if i == best_index else (0, 140, 255)
        cv2.rectangle(annotated, (x0, y0), (x0 + 90, t + h), color, 2)
        prob_i = best_slots[i][1]
        cv2.putText(annotated, f"slot{i} {prob_i:.2f}", (x0, max(14, y0 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

    click_x = l + 90 * best_index + 45
    click_y = t + int(h * 0.65)   # 与线上一致：槽位高度 65% 处，适配较矮 NPC
    cv2.circle(annotated, (click_x, click_y), 7, (0, 0, 255), -1)
    label = f"BEST slot{best_index} prob={best_prob:.4f} click({click_x},{click_y}) ROI({l},{t},{w},{h})"
    cv2.putText(annotated, label, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

    return {
        "success": best_prob > CONF_THRESHOLD,
        "roi": (l, t, w, h),
        "best_index": best_index,
        "best_prob": best_prob,
        "slots": [(i, p) for i, p in best_slots],
        "click_point": (click_x, click_y),
        "frame": annotated,
    }
