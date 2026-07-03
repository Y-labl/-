"""窗口辅助工具 - 主入口"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Windows DPI 感知：确保 Win32 API（GetCursorPos/ClientToScreen）使用物理像素坐标 ──
try:
    import ctypes
    # 尝试 Win8.1+ 的 Per-Monitor DPI Awareness
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        # 回退到 WinVista+ 的系统 DPI Awareness
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

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
