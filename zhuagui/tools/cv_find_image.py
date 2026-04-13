"""
通用 OpenCV 模板匹配（参考桌面 代码备份.txt）。
region 格式为 (left, top, width, height)，符合 pyautogui.screenshot(region=) 要求。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pyautogui
from PIL import Image


def find_image_cv2(
    template_path: str | Path,
    confidence: float = 0.8,
    region: Optional[tuple[int, int, int, int]] = None,
    grayscale: bool = False,
) -> list[tuple[int, int]]:
    """
    在屏幕或指定区域中查找模板图像。

    :param template_path: 模板图片路径 (如 'button.png')
    :param confidence: 匹配阈值 (0~1)，越高要求越精确
    :param region: (left, top, width, height)，None 表示全屏
    :param grayscale: 是否转为灰度匹配（略快，某些场景更稳）
    :return: 匹配中心点列表 [(x, y), ...]，坐标系与 region 或全屏一致
    """
    if region:
        left, top, w, h = region
        screenshot = pyautogui.screenshot(region=(left, top, w, h))
    else:
        screenshot = pyautogui.screenshot()
        left, top = 0, 0

    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"无法加载模板图片: {template_path}")

    tpl_h, tpl_w = template.shape[:2]
    search_img = screenshot_cv
    tpl_img = template[:, :, :3] if template.ndim == 3 and template.shape[2] == 4 else template
    mask = None
    if template.ndim == 3 and template.shape[2] == 4:
        mask = template[:, :, 3]

    if grayscale:
        search_img = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)
        tpl_img = cv2.cvtColor(tpl_img, cv2.COLOR_BGR2GRAY) if tpl_img.ndim == 3 else tpl_img
        if mask is not None:
            result = cv2.matchTemplate(search_img, tpl_img, cv2.TM_CCOEFF_NORMED, mask=mask)
        else:
            result = cv2.matchTemplate(search_img, tpl_img, cv2.TM_CCOEFF_NORMED)
    else:
        if tpl_img.ndim == 2:
            tpl_img = cv2.cvtColor(tpl_img, cv2.COLOR_GRAY2BGR)
        if mask is not None:
            result = cv2.matchTemplate(search_img, tpl_img, cv2.TM_CCOEFF_NORMED, mask=mask)
        else:
            result = cv2.matchTemplate(search_img, tpl_img, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= confidence)
    points: list[tuple[int, int]] = []
    for pt in zip(*locations[::-1]):
        cx = int(pt[0]) + tpl_w // 2
        cy = int(pt[1]) + tpl_h // 2
        if region:
            cx += left
            cy += top
        points.append((cx, cy))

    return points


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "assets/ingame_cursor_template.png"
    conf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
    root = Path(__file__).resolve().parent.parent
    tpl = root / path
    if not tpl.is_file():
        print("用法: python cv_find_image.py <模板路径> [置信度]")
        sys.exit(1)
    pts = find_image_cv2(tpl, confidence=conf)
    print(f"找到 {len(pts)} 个匹配: {pts[:5]}{'...' if len(pts) > 5 else ''}")
