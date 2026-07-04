# -*- coding: utf-8 -*-
"""pyscrcpy ControlSender - 从 .pyc 重建（反编译失败）
基于 pyscrcpy 开源实现 + 原版使用方式（touch(x, y, action=ACTION_DOWN)）重建。
scrcpy 协议版本: 1.20

触摸事件协议: type(1) | action(1) | pointer_id(8) | x(4) | y(4) | width(2) | height(2)
  - pointer_id: uint64 (使用 0xffffffffffffffff 表示无具体id)
  - x, y: int32 (屏幕坐标)
  - width, height: uint16 (屏幕分辨率)
"""

import struct
import time
from typing import Optional, Union

from .const import (
    ACTION_DOWN, ACTION_UP, ACTION_MOVE,
    TYPE_INJECT_KEYCODE, TYPE_INJECT_TEXT, TYPE_INJECT_TOUCH_EVENT,
    TYPE_INJECT_SCROLL_EVENT, TYPE_BACK_OR_SCREEN_ON,
    TYPE_EXPAND_NOTIFICATION_PANEL, TYPE_EXPAND_SETTINGS_PANEL,
    TYPE_COLLAPSE_PANELS, TYPE_GET_CLIPBOARD, TYPE_SET_CLIPBOARD,
    TYPE_SET_SCREEN_POWER_MODE, TYPE_ROTATE_DEVICE,
)

# scrcpy 1.x 协议常量
POINTER_ID_VIRTUAL_FINGER = 0xffffffffffffffff  # -1 的无符号表示


class ControlSender:
    """发送触摸/按键控制指令到 scrcpy server"""

    def __init__(self, client):
        self.client = client

    def __send(self, msg: bytes):
        """通过 control_socket 发送数据（线程安全）"""
        with self.client.control_socket_lock:
            self.client.control_socket.send(msg)

    def __inject_touch_event(self, action: int, x: int, y: int,
                             buttons: int = 0,
                             touch_id: int = POINTER_ID_VIRTUAL_FINGER):
        """注入触摸事件 - scrcpy 1.x 协议
        格式: type(1) | action(1) | pointer_id(8) | x(4) | y(4) | width(2) | height(2)
        """
        w, h = self.client.resolution if self.client.resolution else (0, 0)
        b = struct.pack(">BBQiiHH", TYPE_INJECT_TOUCH_EVENT, action,
                        touch_id, x, y, w, h)
        self.__send(b)

    def touch(self, x: int, y: int, action: int = ACTION_DOWN):
        """发送触摸事件（原版接口：touch(x, y, action=ACTION_DOWN)）

        注意：原版 click_util 调用 touch(x,y) 后再调用 touch(x,y,ACTION_UP)，
        所以此方法只发送单个触摸事件。
        """
        self.__inject_touch_event(action, x, y)

    def tap(self, x: int, y: int):
        """单击（DOWN + UP）"""
        self.touch(x, y, ACTION_DOWN)
        self.touch(x, y, ACTION_UP)

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              move_steps: int = 20, move_delay: float = 0.05):
        """滑动"""
        self.touch(start_x, start_y, ACTION_DOWN)
        for i in range(1, move_steps):
            self.touch(
                start_x + (end_x - start_x) * i // move_steps,
                start_y + (end_y - start_y) * i // move_steps,
                ACTION_MOVE,
            )
            time.sleep(move_delay)
        self.touch(end_x, end_y, ACTION_UP)

    def keyevent(self, keycode: int):
        """发送按键事件"""
        b = struct.pack(">BI", TYPE_INJECT_KEYCODE, keycode)
        self.__send(b)

    def keydown(self, keycode: int):
        """按下按键"""
        self.keyevent(keycode)

    def keyup(self, keycode: int):
        """释放按键（scrcpy 1.x 无单独 UP，用 keyevent 占位）"""
        pass

    def text(self, text: str):
        """输入文本"""
        b = struct.pack(">B", TYPE_INJECT_TEXT) + text.encode("utf-8")
        self.__send(b)

    def back_or_screen_on(self):
        """返回/点亮屏幕"""
        b = struct.pack(">B", TYPE_BACK_OR_SCREEN_ON)
        self.__send(b)

    def expand_notification_panel(self):
        b = struct.pack(">B", TYPE_EXPAND_NOTIFICATION_PANEL)
        self.__send(b)

    def collapse_panels(self):
        b = struct.pack(">B", TYPE_COLLAPSE_PANELS)
        self.__send(b)

    def set_screen_power_mode(self, mode: int):
        b = struct.pack(">BI", TYPE_SET_SCREEN_POWER_MODE, mode)
        self.__send(b)

    def rotate_device(self):
        b = struct.pack(">B", TYPE_ROTATE_DEVICE)
        self.__send(b)
