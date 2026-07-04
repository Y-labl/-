# -*- coding: utf-8 -*-
"""屏幕截图模块 - 截取效卫投屏窗口（使用 win32gui）"""
import ctypes
import numpy as np

import win32gui
import win32ui
import win32con
from PIL import Image


class ScreenCapture:
    """截取指定窗口画面"""

    def __init__(self):
        self._hwnd = None
        self._crop_region = None  # (x, y, w, h)

    def find_window(self, title_keywords=None, class_keywords=None):
        """查找匹配的窗口"""
        if title_keywords is None:
            title_keywords = ["效卫", "投屏", "scrcpy", "QtScrcpy"]
        if class_keywords is None:
            class_keywords = ["Tauri Window", "Qt"]

        found = [None]

        def callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                title = win32gui.GetWindowText(hwnd)
                cls = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                w, h = rect[2] - rect[0], rect[3] - rect[1]
                if w < 200 or h < 200:
                    return True
                title_lower = title.lower()
                cls_lower = cls.lower()
                for kw in title_keywords:
                    if kw.lower() in title_lower:
                        found[0] = hwnd
                        return False
                for kw in class_keywords:
                    if kw.lower() in cls_lower:
                        found[0] = hwnd
                        return False
            except Exception:
                pass
            return True

        win32gui.EnumWindows(callback, None)
        return found[0]

    def bind(self, hwnd=None):
        """绑定窗口"""
        if hwnd is None:
            hwnd = self.find_window()
        if hwnd and win32gui.IsWindow(hwnd):
            self._hwnd = hwnd
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            w, h = rect[2] - rect[0], rect[3] - rect[1]
            print(f"[截图] 已绑定窗口: [{cls}] {title!r} {w}x{h}")
            return True
        return False

    def set_crop(self, x, y, w, h):
        """设置裁剪区域"""
        self._crop_region = (x, y, w, h)

    @property
    def is_bound(self):
        return self._hwnd is not None and win32gui.IsWindow(self._hwnd)

    def capture(self):
        """截取窗口画面，返回 PIL Image"""
        if not self.is_bound:
            return None

        try:
            hwnd = self._hwnd
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                return None

            # 获取窗口 DC
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # 创建位图
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)

            # 使用 PrintWindow 截图（比 BitBlt 更可靠）
            result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
            if result == 0:
                # 回退到 BitBlt
                ctypes.windll.gdi32.BitBlt(
                    save_dc.GetSafeHdc(), 0, 0, width, height,
                    mfc_dc.GetSafeHdc(), 0, 0, win32con.SRCCOPY
                )

            # 转换为 PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                "RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                bmpstr, "raw", "BGRX", 0, 1
            )

            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            # 应用裁剪
            if self._crop_region:
                cx, cy, cw, ch = self._crop_region
                if cw > 0 and ch > 0:
                    img = img.crop((
                        max(0, cx), max(0, cy),
                        min(width, cx + cw), min(height, cy + ch)
                    ))

            return img

        except Exception as e:
            print(f"[截图] 截取失败: {e}")
            return None

    def capture_array(self):
        """截取并返回 numpy array (BGR, for OpenCV)"""
        img = self.capture()
        if img is None:
            return None
        return np.array(img)[:, :, ::-1].copy()  # RGB -> BGR

    @property
    def hwnd(self):
        return self._hwnd
