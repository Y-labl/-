"""窗口辅助工具 - 主入口"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Windows 底层崩溃捕获 ──
import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
EXCEPTION_CONTINUE_SEARCH = 0
EXCEPTION_EXECUTE_HANDLER = 1

LONG = ctypes.c_long
PVOID = ctypes.c_void_p
class EXCEPTION_RECORD(ctypes.Structure):
    pass
PEXCEPTION_RECORD = ctypes.POINTER(EXCEPTION_RECORD)
class CONTEXT(ctypes.Structure):
    pass
PCONTEXT = ctypes.POINTER(CONTEXT)
class EXCEPTION_POINTERS(ctypes.Structure):
    _fields_ = [("ExceptionRecord", PEXCEPTION_RECORD), ("ContextRecord", PCONTEXT)]
PEXCEPTION_POINTERS = ctypes.POINTER(EXCEPTION_POINTERS)
VectoredHandler = ctypes.WINFUNCTYPE(LONG, PEXCEPTION_POINTERS)

@VectoredHandler
def crash_handler(exc_ptrs):
    """捕获 C 层访问违例等崩溃"""
    try:
        import traceback, datetime
        code = exc_ptrs.contents.ExceptionRecord.contents.ExceptionCode
        msg = f"[{datetime.datetime.now()}] C-Level Crash: code=0x{code:08X}\n"
        msg += traceback.format_exc() if sys.exc_info()[0] else "No Python traceback\n"
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(msg)
        ctypes.windll.user32.MessageBoxW(0, msg[:500], "窗口辅助工具 崩溃(C层)", 0x10)
    except:
        pass
    return EXCEPTION_CONTINUE_SEARCH

kernel32.AddVectoredExceptionHandler(1, crash_handler)

# ── Windows DPI 感知 ──
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import traceback, io

def _log_exception(exc_type, exc_value, exc_tb):
    msg = io.StringIO()
    traceback.print_exception(exc_type, exc_value, exc_tb, file=msg)
    err_text = msg.getvalue()
    try:
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(err_text)
    except:
        pass
    try:
        ctypes.windll.user32.MessageBoxW(0, err_text[:500], "窗口辅助工具 崩溃(Python层)", 0x10)
    except:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _log_exception

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

def main():


    app = QApplication(sys.argv)
    app.setApplicationName("窗口辅助工具")

    from ui.main_window import MainWindow, STYLE_DARK
    window = MainWindow()

    use_light = "--light" in sys.argv
    if not use_light:
        window.setStyleSheet(STYLE_DARK)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()