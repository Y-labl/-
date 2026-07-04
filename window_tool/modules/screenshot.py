"""截图模块 - 纯 ctypes 实现"""
import os, ctypes
from datetime import datetime
from PIL import Image
from PySide6.QtCore import QObject, Signal, QThread

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SRCCOPY = 0x00CC0020
CAPTUREBLT = 0x40000000
LOGPIXELSX = 88

def _debug(msg):
    try:
        with open("_screenshot_debug.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

def _get_screen_dpr() -> float:
    try:
        hdc = user32.GetDC(0)
        if hdc:
            try:
                dpi_x = gdi32.GetDeviceCaps(hdc, LOGPIXELSX)
                return dpi_x / 96.0
            finally:
                user32.ReleaseDC(0, hdc)
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
        dpr = _get_screen_dpr()
        _debug(f"capture_region: region={region}, dpr={dpr}")

        try:
            hwnd_desktop = user32.GetDesktopWindow()
            _debug(f"  GetDesktopWindow={hwnd_desktop}")
            
            hdc_screen = user32.GetWindowDC(hwnd_desktop)
            _debug(f"  GetWindowDC={hdc_screen}")
            
            hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            _debug(f"  CreateCompatibleDC={hdc_mem}")

            try:
                if region:
                    left, top, right, bottom = region
                    width, height = right - left, bottom - top
                else:
                    left = user32.GetSystemMetrics(0)
                    top = user32.GetSystemMetrics(1)
                    width = user32.GetSystemMetrics(78)
                    height = user32.GetSystemMetrics(79)

                _debug(f"  rect: ({left},{top}) {width}x{height}")

                if width <= 0 or height <= 0:
                    _debug(f"  BAD SIZE, returning None")
                    return None

                bmp = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
                gdi32.SelectObject(hdc_mem, bmp)
                gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, left, top, SRCCOPY | CAPTUREBLT)

                class BITMAPINFOHEADER(ctypes.Structure):
                    _fields_ = [
                        ("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                        ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                        ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                        ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                        ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                        ("biClrImportant", ctypes.c_uint32),
                    ]

                bi = BITMAPINFOHEADER()
                bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                bi.biWidth = width
                bi.biHeight = -height
                bi.biPlanes = 1
                bi.biBitCount = 32
                bi.biCompression = 0

                buf = ctypes.create_string_buffer(width * height * 4)
                gdi32.GetDIBits(hdc_mem, bmp, 0, height, buf, ctypes.byref(bi), 0)

                raw_img = Image.frombuffer("RGB", (width, height), buf, "raw", "BGRX", 0, 1)
                _debug(f"  frombuffer OK: {width}x{height}")

                gdi32.DeleteObject(bmp)
            finally:
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_desktop, hdc_screen)

            if dpr > 1.001:
                new_w = int(raw_img.width / dpr)
                new_h = int(raw_img.height / dpr)
                if new_w > 0 and new_h > 0:
                    raw_img = raw_img.resize((new_w, new_h), Image.LANCZOS)

            _debug(f"  SUCCESS: {raw_img.size}")
            return raw_img
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            _debug(f"  EXCEPTION: {err}")
            try:
                with open("crash_log.txt", "a", encoding="utf-8") as f:
                    f.write(err)
            except:
                pass
            print(err)
            return None

    def capture_window(self, hwnd, client_area=True):
        from modules.window_binder import get_window_rect_screen
        import win32gui
        _debug(f"capture_window: hwnd={hwnd}, client_area={client_area}")
        if client_area:
            rect = get_window_rect_screen(hwnd)
        else:
            rect = win32gui.GetWindowRect(hwnd)
        _debug(f"  rect={rect}")
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