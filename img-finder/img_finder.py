"""
图像定位器 - 在指定窗口中查找目标图片的位置
返回的是窗口内坐标（相对于窗口左上角），不是屏幕坐标
"""

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import os
from typing import Optional, Tuple, Dict


class WindowManager:
    """窗口管理类"""

    def __init__(self, window_title: str):
        self.window_title = window_title
        self.window = None

    def find_window(self) -> bool:
        """查找窗口"""
        windows = gw.getWindowsWithTitle(self.window_title)
        if not windows:
            return False

        valid_windows = [w for w in windows if w.width > 100 and w.height > 100]
        if not valid_windows:
            return False

        self.window = valid_windows[0]
        return True

    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口矩形 (left, top, width, height)"""
        if not self.window:
            return None
        return (self.window.left, self.window.top, self.window.width, self.window.height)

    def capture_window(self) -> Optional[np.ndarray]:
        """截取窗口截图，返回 BGR 格式 numpy 数组"""
        rect = self.get_window_rect()
        if not rect:
            return None

        left, top, width, height = rect
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


class ImageFinder:
    """图像查找器 - 在窗口截图中定位目标图片"""

    def __init__(self, window_title: str):
        self.window_manager = WindowManager(window_title)

    def _load_template(self, template_path: str) -> Optional[np.ndarray]:
        """使用 Pillow 加载模板图片（支持中文路径）"""
        try:
            from PIL import Image
            pil_image = Image.open(template_path)
            template = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return template
        except Exception as e:
            print(f"[错误] 加载图片失败: {e}")
            return None

    def find_image(
        self,
        template_path: str,
        confidence: float = 0.8
    ) -> Optional[Dict]:
        """
        在窗口中查找目标图片，返回窗口内坐标

        :param template_path: 目标图片路径
        :param confidence: 匹配置信度阈值 (0-1)
        :return: {
            'x': 窗口内左上角x,
            'y': 窗口内左上角y,
            'center_x': 窗口内中心x,
            'center_y': 窗口内中心y,
            'width': 匹配宽度,
            'height': 匹配高度,
            'confidence': 匹配置信度
        } 或 None
        """
        if not self.window_manager.find_window():
            print(f"[错误] 未找到窗口: {self.window_manager.window_title}")
            return None

        window_img = self.window_manager.capture_window()
        if window_img is None:
            print("[错误] 无法截取窗口截图")
            return None

        if not os.path.exists(template_path):
            print(f"[错误] 图片文件不存在: {template_path}")
            return None

        template = self._load_template(template_path)
        if template is None:
            print(f"[错误] 无法读取图片: {template_path}")
            return None

        screen_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        th, tw = template_gray.shape[:2]

        if th > screen_gray.shape[0] or tw > screen_gray.shape[1]:
            print("[错误] 模板图片大于窗口截图")
            return None

        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val < confidence:
            print(f"[未找到] 最高置信度 {max_val:.3f} 低于阈值 {confidence}")
            return None

        match_x, match_y = max_loc
        center_x = match_x + tw // 2
        center_y = match_y + th // 2

        result_info = {
            'x': match_x,
            'y': match_y,
            'center_x': center_x,
            'center_y': center_y,
            'width': tw,
            'height': th,
            'confidence': round(max_val, 4)
        }

        print(f"[找到] 窗口内坐标: 左上角({match_x}, {match_y}), "
              f"中心({center_x}, {center_y}), 尺寸{tw}x{th}, 置信度{max_val:.4f}")

        return result_info

    def find_all_images(
        self,
        template_path: str,
        confidence: float = 0.8
    ) -> list:
        """在窗口中查找所有匹配的目标图片"""
        if not self.window_manager.find_window():
            return []

        window_img = self.window_manager.capture_window()
        if window_img is None:
            return []

        template = self._load_template(template_path)
        if template is None:
            return []

        screen_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        th, tw = template_gray.shape[:2]

        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)

        matches = []
        for pt in zip(*locations[::-1]):
            match_x, match_y = pt
            matches.append({
                'x': int(match_x),
                'y': int(match_y),
                'center_x': int(match_x + tw // 2),
                'center_y': int(match_y + th // 2),
                'width': tw,
                'height': th,
                'confidence': round(float(result[pt[1], pt[0]]), 4)
            })

        matches = self._remove_duplicates(matches)
        print(f"[找到] {len(matches)} 个匹配项")
        return matches

    @staticmethod
    def _remove_duplicates(matches: list, min_distance: int = 10) -> list:
        """去除距离过近的重复匹配"""
        if not matches:
            return matches
        filtered = [matches[0]]
        for m in matches[1:]:
            if any(abs(m['center_x'] - f['center_x']) < min_distance and
                   abs(m['center_y'] - f['center_y']) < min_distance
                   for f in filtered):
                continue
            filtered.append(m)
        return filtered
