"""截图模块 - 统一使用逻辑像素坐标系（自动处理 Windows DPI 缩放）"""
import os, io, ctypes
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image
from PySide6.QtCore import QObject, Signal, QThread

try:
    import mss, mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import win32gui, win32ui, win32con, win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


def _get_screen_dpr() -> float:
    """获取主屏幕的 DPI 缩放比例 (1.0 = 100%, 1.25 = 125%, 1.5 = 150%)"""
    try:
        # Win8.1+ Per-Monitor DPI
        hdc = ctypes.windll.user32.GetDC(0)
        if hdc:
            try:
                dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                return dpi_x / 96.0
            finally:
                ctypes.windll.user32.ReleaseDC(0, hdc)
    except Exception:
        pass
    return 1.0


class ScreenshotWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, region=None, parent=None):
        super().__init__(parent)
        self.region = region

    def run(self):
        try:
            img = ScreenCapture.capture_region(self.region)
            if img:
                self.finished.emit(img)
            else:
                self.error.emit("截图失败")
        except Exception as e:
            self.error.emit(f"截图异常: {e}")


class ScreenCapture(QObject):
    screenshot_taken = Signal(object)
    screenshot_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cached_image = None
        self._worker = None

    @staticmethod
    def capture_region(region=None):
        """截取屏幕区域，返回 PIL Image (RGB)，已缩放到逻辑像素"""
        dpr = _get_screen_dpr()
        raw_img = None
        use_mss = True

        if HAS_MSS:
            try:
                raw_img = ScreenCapture._capture_mss(region)
            except Exception:
                pass
        if raw_img is None and HAS_WIN32:
            try:
                raw_img = ScreenCapture._capture_gdi(region)
                use_mss = False
            except Exception:
                pass
        if raw_img is None:
            return None

        # 如果 DPI 缩放不是 100%，将物理像素图像缩放到逻辑像素
        # 这样 Qt 显示、鼠标坐标、模板匹配都在统一的逻辑像素空间
        if dpr > 1.001:
            new_w = int(raw_img.width / dpr)
            new_h = int(raw_img.height / dpr)
            if new_w > 0 and new_h > 0:
                raw_img = raw_img.resize((new_w, new_h), Image.LANCZOS)

        return raw_img

    @staticmethod
    def _capture_mss(region=None):
        with mss.mss() as sct:
            if region:
                left, top, right, bottom = region
                monitor = {"top": top, "left": left, "width": right - left, "height": bottom - top}
            else:
                monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    @staticmethod
    def _capture_gdi(region=None):
        from ctypes import windll
        hwnd_desktop = win32gui.GetDesktopWindow()
        hdc_desktop = win32gui.GetWindowDC(hwnd_desktop)
        hdc_mem = win32gui.CreateCompatibleDC(hdc_desktop)
        try:
            if region:
                left, top, right, bottom = region
                width, height = right - left, bottom - top
            else:
                left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
                top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
                width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(hdc_desktop, width, height)
            hdc_mem.SelectObject(bmp)
            windll.gdi32.BitBlt(hdc_mem.GetSafeHdc(), 0, 0, width, height,
                                 hdc_desktop.GetSafeHdc(), left, top,
                                 win32con.SRCCOPY | 0x40000000)
            bmp_bytes = bmp.GetBitmapBits(True)
            bmp_info = bmp.GetInfo()
            return Image.frombuffer("RGB", (bmp_info["bmWidth"], bmp_info["bmHeight"]),
                                     bmp_bytes, "raw", "BGRX", 0, 1)
        finally:
            hdc_mem.DeleteDC()
            win32gui.ReleaseDC(hwnd_desktop, hdc_desktop)

    def capture_window(self, hwnd, client_area=True):
        from modules.window_binder import get_window_rect_screen
        if client_area:
            rect = get_window_rect_screen(hwnd)
        else:
            rect = win32gui.GetWindowRect(hwnd)
        img = ScreenCapture.capture_region(rect)
        if img is not None:
            self._cached_image = img
        return img

    def save_screenshot(self, img, filename=None, directory=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        if filename is None:
            filename = f"screenshot_{timestamp}.png"
        if directory is None:
            directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        img.save(filepath, "PNG")
        return filepath

    @property
    def cached_image(self):
        return self._cached_image
