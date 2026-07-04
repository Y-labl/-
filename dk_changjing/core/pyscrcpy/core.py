# -*- coding: utf-8 -*-
"""pyscrcpy core.py - 从 .pyc 反编译重建（反编译结构错乱，基于标准 pyscrcpy 1.x 重写）

scrcpy 协议版本: 1.20
保留原版接口: Client(device, bitrate, max_fps, max_size), start(threaded),
              last_frame, resolution, control.touch(x, y, action)
"""

import os
import socket
import struct
import threading
import time
from pathlib import Path
from time import sleep
from typing import Any, Callable, Optional, Union

import cv2 as cv
import numpy as np
from adbutils import AdbDevice, AdbError, Network, adb
from av.codec import CodecContext
from av.error import InvalidDataError
from loguru import logger

from common.util.log_util import logUtil
from const import SCRCPY_SERVER_PATH
from .const import (
    EVENT_DISCONNECT, EVENT_FRAME, EVENT_INIT,
    LOCK_SCREEN_ORIENTATION_UNLOCKED, EVENT_ONCHANGE,
)
from .control import ControlSender

VERSION = "1.20"
HERE = Path(__file__).resolve().parent
JAR = HERE / "scrcpy-server.jar"


class Client:

    def __init__(self, device: Optional[Union[AdbDevice, str]] = None,
                 max_size: int = 0, bitrate: int = 8000000,
                 max_fps: int = 0, block_frame: bool = True,
                 stay_awake: bool = True,
                 lock_screen_orientation: int = LOCK_SCREEN_ORIENTATION_UNLOCKED,
                 skip_same_frame: bool = False):
        self.max_size = max_size
        self.bitrate = bitrate
        self.max_fps = max_fps
        self.block_frame = block_frame
        self.stay_awake = stay_awake
        self.lock_screen_orientation = lock_screen_orientation
        self.skip_same_frame = skip_same_frame
        self.min_frame_interval = 1 / max_fps if max_fps else 0

        if device is None:
            try:
                device = adb.device_list()[0]
            except IndexError:
                raise Exception("Cannot connect to phone")
        elif isinstance(device, str):
            device = adb.device(serial=device)

        self.device = device
        self.listeners = dict(frame=[], init=[], disconnect=[], onchange=[])
        self.last_frame = None
        self.resolution = None
        self.device_name = None
        self.control = ControlSender(self)
        self.alive = False
        self.__server_stream = None
        self.__video_socket = None
        self.control_socket = None
        self.control_socket_lock = threading.Lock()

    def __init_server_connection(self) -> None:
        """Connect to android server (video + control socket), set resolution."""
        for _ in range(30):
            try:
                self.__video_socket = self.device.create_connection(
                    Network.LOCAL_ABSTRACT, "scrcpy")
                break
            except AdbError:
                sleep(0.1)
        else:
            raise ConnectionError("Failed to connect scrcpy-server after 3 seconds")

        dummy_byte = self.__video_socket.recv(1)
        if not len(dummy_byte):
            raise ConnectionError("Did not receive Dummy Byte!")
        self.control_socket = self.device.create_connection(
            Network.LOCAL_ABSTRACT, "scrcpy")
        self.device_name = self.__video_socket.recv(64).decode("utf-8").rstrip("\x00")
        if not len(self.device_name):
            raise ConnectionError("Did not receive Device Name!")
        res = self.__video_socket.recv(4)
        self.resolution = struct.unpack(">HH", res)
        self.__video_socket.setblocking(False)

    def __deploy_server(self) -> None:
        """Push scrcpy-server.jar to device and start it."""
        cmd = [
            "CLASSPATH=/data/local/tmp/scrcpy-server.jar",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            VERSION,
            "info",
            f"{self.max_size}",
            f"{self.bitrate}",
            f"{self.max_fps}",
            f"{self.lock_screen_orientation}",
            "true",
            "-",
            "false",
            "true",
            "0",
            "false",
            "true" if self.stay_awake else "false",
            "-",
            "-",
            "false",
        ]
        self.device.push(
            SCRCPY_SERVER_PATH.format(logUtil.getParentPath()),
            "/data/local/tmp/scrcpy-server.jar",
        )
        self.__server_stream = self.device.shell(cmd, stream=True)

    def start(self, threaded: bool = False) -> None:
        """Start the client-server connection."""
        if self.alive:
            raise AssertionError("Client already started")

        self.__deploy_server()
        self.__init_server_connection()
        self.alive = True

        for func in self.listeners[EVENT_INIT]:
            func(self)

        if threaded:
            threading.Thread(target=self.__stream_loop, daemon=True).start()
        else:
            self.__stream_loop()

    def stop(self) -> None:
        """Close socket connections and stop listening."""
        self.alive = False
        for sock in (self.__server_stream, self.control_socket, self.__video_socket):
            if sock is None:
                continue
            try:
                sock.close()
            except Exception:
                pass

    def __del__(self):
        self.stop()

    def __calculate_diff(self, img1, img2):
        if img1 is None:
            return 1
        gray1 = cv.cvtColor(img1, cv.COLOR_BGR2GRAY)
        gray2 = cv.cvtColor(img2, cv.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        threshold = 30
        _, thresholded_diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        total_diff_pixels = np.sum(thresholded_diff / 255)
        total_pixels = gray1.size
        return total_diff_pixels / total_pixels

    def __stream_loop(self) -> None:
        """Core loop: receive h264 stream, decode to frames, update last_frame."""
        codec = CodecContext.create("h264", "r")
        while self.alive:
            try:
                raw = self.__video_socket.recv(65536)
                if raw == b'':
                    raise ConnectionError("Video stream is disconnected")
                for packet in codec.parse(raw):
                    for frame in codec.decode(packet):
                        frame = frame.to_ndarray(format="bgr24")
                        self.last_frame = frame
                        self.resolution = (frame.shape[1], frame.shape[0])

                        if self.skip_same_frame and \
                                self.__calculate_diff(self.last_frame, frame) <= 0.1:
                            logger.debug("different frame detected")

                        for func in self.listeners[EVENT_ONCHANGE]:
                            func(self, frame)

                        for func in self.listeners[EVENT_FRAME]:
                            func(self, frame)

            except (BlockingIOError, InvalidDataError):
                time.sleep(0.01)
                if not self.block_frame:
                    for func in self.listeners[EVENT_FRAME]:
                        func(self, None)

            except (ConnectionError, OSError) as e:
                if self.alive:
                    self.stop()
                    raise e

    def on_init(self, func: Callable) -> None:
        """Add function to on_init listeners."""
        self.listeners[EVENT_INIT].append(func)

    def on_frame(self, func: Callable):
        """Add function to on-frame listeners."""
        self.listeners[EVENT_FRAME].append(func)

    def on_change(self, func: Callable):
        self.listeners[EVENT_ONCHANGE].append(func)
