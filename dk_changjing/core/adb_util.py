# -*- coding: utf-8 -*-
"""ADB 设备工具"""
import os
import time

from adbutils import adb


class AdbUtil:

    @staticmethod
    def list_devices():
        devices = []
        try:
            for d in adb.device_list():
                info = {"serial": d.serial}
                try:
                    wmsize = d.shell("wm size")
                    for line in wmsize.strip().split("\n"):
                        line = line.strip()
                        if "Override size:" in line:
                            info["resolution"] = line.split("Override size:")[-1].strip()
                        elif "Physical size:" in line:
                            info["resolution"] = line.split("Physical size:")[-1].strip()
                except Exception:
                    info["resolution"] = ""
                devices.append(info)
        except Exception as e:
            print(f"[ADB] 扫描设备失败: {e}")
        return devices

    @staticmethod
    def tap(serial, x, y):
        try:
            d = adb.device(serial)
            d.shell(f"input tap {x} {y}")
            return True
        except Exception as e:
            print(f"[ADB] 点击失败: {e}")
            return False

    @staticmethod
    def swipe(serial, x1, y1, x2, y2, duration=300):
        try:
            d = adb.device(serial)
            d.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
            return True
        except Exception as e:
            print(f"[ADB] 滑动失败: {e}")
            return False

    @staticmethod
    def screenshot(serial, save_path=None):
        try:
            d = adb.device(serial)
            data = d.screenshot()
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(data)
            return data
        except Exception as e:
            print(f"[ADB] 截图失败: {e}")
            return None

    @staticmethod
    def get_resolution(serial):
        try:
            d = adb.device(serial)
            wmsize = d.shell("wm size")
            for line in wmsize.strip().split("\n"):
                line = line.strip()
                if "Override size:" in line:
                    parts = line.split("Override size:")[-1].strip().split("x")
                    return int(parts[0]), int(parts[1])
                elif "Physical size:" in line:
                    parts = line.split("Physical size:")[-1].strip().split("x")
                    return int(parts[0]), int(parts[1])
        except Exception:
            pass
        return 1080, 1920

    @staticmethod
    def keyevent(serial, keycode):
        try:
            d = adb.device(serial)
            d.shell(f"input keyevent {keycode}")
            return True
        except Exception:
            return False
