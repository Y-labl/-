# -*- coding: utf-8 -*-
"""
ADB / scrcpy 后端适配层

反编译代码原先通过 scrcpy 客户端拿实时画面（800x448 流分辨率）并注入点击。
合并进本工程后，所有取帧 / 点击 / 日志统一走这里的 Backend：

  - 默认实现：ADB screencap（自动转正、缩放到 800x448）+ adb input tap；
  - 引擎集成：AutoFightEngine 启动时注入自己的截图 / 点击 / 日志函数。

流坐标约定：800x448（与小霸王原工程一致）。
"""

import os
import random
import re
import subprocess
import time

import cv2
import numpy as np

STREAM_W = 800
STREAM_H = 448
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# ADB 可执行路径：优先项目虚拟环境自带，其次 adbutils，最后系统 PATH
_ADB_EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        ".venv", "Lib", "site-packages", "adbutils", "binaries", "adb.exe")
if not os.path.exists(_ADB_EXE):
    try:
        import adbutils
        _ADB_EXE = adbutils.adb_path()
    except Exception:
        _ADB_EXE = "adb"
ADB_EXE = _ADB_EXE


class StopTest(BaseException):
    """测试停止信号。

    继承 BaseException 而不是 Exception，这样 goToMapAction / 各动作函数里的
    `except Exception` 不会把它吞掉，能真正中断跑图/背包等长任务。
    """


def _device_size(deviceId):
    """查询设备分辨率（landscape），缓存避免反复查询。"""
    if not hasattr(_device_size, "_cache"):
        _device_size._cache = {}
    cached = _device_size._cache.get(deviceId)
    if cached:
        return cached
    try:
        r = subprocess.run([ADB_EXE, "-s", deviceId, "shell", "wm", "size"],
                           capture_output=True, text=True, timeout=5,
                           creationflags=CREATE_NO_WINDOW)
        m = re.search(r"(\d+)x(\d+)", r.stdout)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            if h > w:
                w, h = h, w
            _device_size._cache[deviceId] = (w, h)
            return (w, h)
    except Exception:
        pass
    return (1920, 1080)


def _normalize_frame(frame):
    """转正 + 缩放到 800x448 流分辨率。"""
    if frame is None:
        return None
    fh, fw = frame.shape[:2]
    if fh > fw:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        fh, fw = frame.shape[:2]
    if (fw, fh) != (STREAM_W, STREAM_H):
        frame = cv2.resize(frame, (STREAM_W, STREAM_H), interpolation=cv2.INTER_LINEAR)
    return frame


class _Backend(object):
    def __init__(self):
        self.screencap_fn = None       # fn(deviceId) -> BGR 帧（任意分辨率）
        self.tap_fn = None             # fn(deviceId, x, y, is_double=False)
        self.log_fn = None             # fn(deviceId, msg)
        self.cache_seconds = 0.25      # 帧缓存时长，避免同一帧重复 ADB 截图
        self._frame_cache = {}         # deviceId -> (ts, frame_800x448)
        self.stop_event = None         # threading.Event：功能测试页停止信号

    def check_stop(self):
        if self.stop_event is not None and self.stop_event.is_set():
            raise StopTest("测试已停止")

    def set(self, screencap_fn=None, tap_fn=None, log_fn=None, cache_seconds=None):
        if screencap_fn is not None:
            self.screencap_fn = screencap_fn
        if tap_fn is not None:
            self.tap_fn = tap_fn
        if log_fn is not None:
            self.log_fn = log_fn
        if cache_seconds is not None:
            self.cache_seconds = cache_seconds

    def _default_screencap(self, deviceId):
        r = subprocess.run([ADB_EXE, "-s", deviceId, "exec-out", "screencap", "-p"],
                           capture_output=True, timeout=12,
                           creationflags=CREATE_NO_WINDOW)
        if r.returncode != 0 or not r.stdout:
            return None
        frame = cv2.imdecode(np.frombuffer(r.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
        return _normalize_frame(frame)

    def _default_tap(self, deviceId, x, y, is_double=False):
        w, h = _device_size(deviceId)
        tx = int(x * w / STREAM_W)
        ty = int(y * h / STREAM_H)
        if is_double:
            for _ in range(2):
                subprocess.run([ADB_EXE, "-s", deviceId, "shell", "input", "tap", str(tx), str(ty)],
                               capture_output=True, timeout=5, creationflags=CREATE_NO_WINDOW)
                time.sleep(random.uniform(0.05, 0.12))
        else:
            subprocess.run([ADB_EXE, "-s", deviceId, "shell", "input", "tap", str(tx), str(ty)],
                           capture_output=True, timeout=5, creationflags=CREATE_NO_WINDOW)

    def get_frame(self, deviceId, fresh=False):
        """返回 800x448 BGR 帧；缓存时间内复用，减少 ADB 截图开销。"""
        self.check_stop()
        now = time.time()
        cached = self._frame_cache.get(deviceId)
        if not fresh and cached is not None and (now - cached[0]) < self.cache_seconds:
            return cached[1]
        fn = self.screencap_fn or self._default_screencap
        frame = fn(deviceId)
        frame = _normalize_frame(frame)
        if frame is not None:
            self._frame_cache[deviceId] = (now, frame)
        return frame

    def tap(self, deviceId, x, y, is_double=False):
        self.check_stop()
        fn = self.tap_fn or self._default_tap
        fn(deviceId, x, y, is_double=is_double)

    def clear_cache(self, deviceId=None):
        if deviceId is None:
            self._frame_cache.clear()
        else:
            self._frame_cache.pop(deviceId, None)

    def log(self, deviceId, msg):
        if self.log_fn is not None:
            try:
                self.log_fn(deviceId, msg)
            except Exception:
                pass


backend = _Backend()


def setup(screencap_fn=None, tap_fn=None, log_fn=None, cache_seconds=None):
    """引擎集成入口：注入自己的截图 / 点击 / 日志函数。"""
    backend.set(screencap_fn=screencap_fn, tap_fn=tap_fn,
                log_fn=log_fn, cache_seconds=cache_seconds)


def get_frame(deviceId, fresh=False):
    """模块级便捷入口，等价于 backend.get_frame。"""
    return backend.get_frame(deviceId, fresh=fresh)


def tap(deviceId, x, y, is_double=False):
    """模块级便捷入口，等价于 backend.tap。"""
    return backend.tap(deviceId, x, y, is_double=is_double)


def log(deviceId, msg):
    """模块级便捷入口，等价于 backend.log。"""
    return backend.log(deviceId, msg)


def clear_cache(deviceId=None):
    """模块级便捷入口，等价于 backend.clear_cache。"""
    return backend.clear_cache(deviceId)


def set_stop_event(ev):
    """设置停止信号（功能测试页停止按钮用）。"""
    backend.stop_event = ev


def clear_stop_event():
    """清除停止信号。"""
    backend.stop_event = None
