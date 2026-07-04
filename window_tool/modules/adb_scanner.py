"""ADB 设备扫描模块"""
from PySide6.QtCore import QObject, Signal, QThread


class AdbScanner(QObject):
    """扫描 ADB 连接的 Android 设备（仅获取基本信息，不截图）"""
    devices_found = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None

    def scan(self):
        if self._thread and self._thread.isRunning():
            return
        self._thread = _ScanThread(self)
        self._thread.finished_signal.connect(self._on_scan_done)
        self._thread.start()

    def _on_scan_done(self, devices):
        self.devices_found.emit(devices)

    def stop(self):
        """停止扫描"""
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait(3000)


class _ScanThread(QThread):
    """后台 ADB 扫描线程"""
    finished_signal = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        devices = []
        try:
            from adbutils import adb
            for device in adb.device_list():
                serial = device.serial
                resolution = ""
                try:
                    wmsize = device.shell("wm size")
                    if "Override size:" in wmsize:
                        resolution = wmsize.split("Override size:")[1].strip()
                    elif "Physical size:" in wmsize:
                        resolution = wmsize.split("Physical size:")[1].strip()
                except:
                    pass
                devices.append({
                    "serial": serial,
                    "resolution": resolution,
                })
        except Exception:
            pass
        self.finished_signal.emit(devices)