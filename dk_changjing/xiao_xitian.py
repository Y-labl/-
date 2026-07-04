# -*- coding: utf-8 -*-

"""小西天场景自动化 - 基于 pyscrcpy 直连手机

流程:

  1. 识别"位置栏-小西天点卡服.png"确认位置

  2. 点击"打开地图点卡服.png"

  3. 等待0.3秒

  4. 识别"点卡小西天地图.png"并随机点击地图中某位置

  5. 识别"关闭弹窗点卡服.png"并点击关闭

  6. 循环

"""

import os, sys, time, random, threading

from datetime import datetime

import cv2

import numpy as np



# 确保路径

project_dir = os.path.dirname(os.path.abspath(__file__))

if project_dir not in sys.path:

    sys.path.insert(0, project_dir)

core_path = os.path.join(project_dir, "core")

if os.path.exists(core_path) and core_path not in sys.path:

    sys.path.insert(0, core_path)

original_path = os.path.join(core_path, "original")

if os.path.exists(original_path) and original_path not in sys.path:

    sys.path.insert(0, original_path)



from core.img_util import find_template



# ---- 常量 ----

IMAGES_DIR = os.path.join(project_dir, "images")





class XiaoXiTianThread(threading.Thread):

    """小西天场景自动化线程 - pyscrcpy 版"""



    def __init__(self, serial, screenshot=None):

        super().__init__(daemon=True)

        self.serial = serial

        self._client = None      # pyscrcpy Client

        self._running = False

        self._callbacks = []

        self._last_frame = None

        self._loop_count = 0

        self._state = "INIT"



    # ---- 兼容主界面属性 ----

    @property

    def state(self):

        return self._state



    @property

    def battle_count(self):

        return self._loop_count



    def add_callback(self, name, func):

        self._callbacks.append((name, func))



    def _emit(self, name, *args):

        for n, f in self._callbacks:

            if n == name:

                try:

                    f(*args)

                except Exception:

                    pass



    def _log(self, msg):

        ts = datetime.now().strftime("%H:%M:%S")

        full = f"[{ts}] {msg}"

        print(full)

        self._emit("log", full)



    @property

    def running(self):

        return self._running



    def stop(self):

        self._running = False

        self._state = "STOPPING"

        self._log("正在停止...")

        self._emit("state_update", "STOPPING")



    # ================================================================

    # pyscrcpy 连接

    # ================================================================



    def _init_client(self):

        """初始化 pyscrcpy Client"""

        try:

            from pyscrcpy.core import Client



            self._log(f"正在连接设备 {self.serial} ...")

            client = Client(

                device=self.serial,

                max_size=1080,

                bitrate=8000000,

                max_fps=15,

                block_frame=True,

            )

            # 通过 add_callback 方式在 frame 回调中更新 last_frame

            # 但我们需要在 start 前设置好

            client.start(threaded=True)

            # 等待首帧

            for _ in range(50):

                if client.last_frame is not None:

                    break

                time.sleep(0.1)

            if client.last_frame is None:

                self._log("连接超时，未能获取画面")

                client.stop()

                return False



            self._client = client

            # 同步 resolution 到实际帧尺寸（scrcpy header 可能与实际帧方向不同）
            frame = client.last_frame

            if frame is not None:

                client.resolution = (frame.shape[1], frame.shape[0])

            self._log(f"已连接: {client.resolution[0]}x{client.resolution[1]} (帧:{frame.shape[1] if frame is not None else chr(39)+chr(63)+chr(39)}x{frame.shape[0] if frame is not None else chr(39)+chr(63)+chr(39)})")
            return True

        except Exception as e:

            self._log(f"连接设备失败: {e}")

            return False



    def _disconnect(self):

        if self._client:

            try:

                self._client.stop()

            except Exception:

                pass

            self._client = None



    # ================================================================

    # 截图 & 点击

    # ================================================================



    def _get_frame(self):

        """返回 scrcpy 原始画面，同时同步 resolution 到实际帧尺寸
        

        模板匹配直接用原始帧，点击坐标也在原始帧空间，

        消除所有旋转变换带来的坐标错位问题。

        """

        if self._client is None:

            return None

        frame = self._client.last_frame

        if frame is None:

            return None

        # 确保 resolution 与实际帧尺寸一致（关键：touch 事件用 resolution 做坐标映射）
        self._client.resolution = (frame.shape[1], frame.shape[0])

        self._last_frame = frame

        return frame



    def _tap(self, x, y):

        """发送触摸点击，x, y 是原始帧坐标，scrcpy 协议按比例映射到设备"""
        if self._client is None:

            return

        # 坐标边界校验
        frame = self._client.last_frame

        if frame is not None:

            fh, fw = frame.shape[:2]

            if x < 0 or y < 0 or x >= fw or y >= fh:

                self._log(f"⚠ 坐标越界: ({x},{y}) 超出帧范围 {fw}x{fh}，已拒绝")
                return

        try:

            from pyscrcpy.const import ACTION_DOWN, ACTION_UP

            self._client.control.touch(x, y, ACTION_DOWN)

            time.sleep(0.05)

            self._client.control.touch(x, y, ACTION_UP)

        except Exception as e:

            self._log(f"点击失败: {e}")
    def _find(self, img_name, threshold=0.7):

        """查找模板，返回 (x, y, w, h, conf) 或 None"""
        frame = self._get_frame()

        if frame is None:

            return None

        img_path = os.path.join(IMAGES_DIR, img_name)

        template = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)

        if template is None:

            self._log(f"_find: 无法加载模板 {img_name}")
            return None

        th, tw = template.shape[:2]

        fh, fw = frame.shape[:2]

        # 小模板（任一边 < 30px）自动提高阈值，避免匹配到随机噪声
        effective_threshold = threshold

        if tw < 30 or th < 30:

            effective_threshold = max(threshold, 0.85)

        result = find_template(frame, img_path, effective_threshold)

        if result is None:

            return None

        x, y, conf = result

        # 防御性边界校验
        if x < 0 or y < 0 or x + tw > fw or y + th > fh:

            self._log(f"_find: 匹配区域越界 ({x},{y})+{tw}x{th} > 帧 {fw}x{fh}")
            return None

        return (x, y, tw, th, conf)

    def _click_template(self, img_name, threshold=0.7):

        """查找模板并点击中心"""
        r = self._find(img_name, threshold)

        if r is None:

            return False

        x, y, w, h, conf = r

        cx, cy = x + w // 2, y + h // 2

        # 验证点击坐标在帧内
        frame = self._client.last_frame if self._client else None

        if frame is not None:

            fh, fw = frame.shape[:2]

            if cx < 0 or cy < 0 or cx >= fw or cy >= fh:

                self._log(f"⚠ 点击坐标越界: ({cx},{cy}) > 帧 {fw}x{fh}，已跳过")
                return False

        self._log(f"点击: {img_name} ({cx},{cy}) conf={conf:.2f}")
        self._tap(cx, cy)

        return True

    def run(self):

        self._running = True

        self._loop_count = 0

        self._state = "CONNECTING"

        self._log("=== 小西天场景 v2 启动 ===")

        self._log(f"设备: {self.serial}")



        # Step 0: 连接 pyscrcpy

        if not self._init_client():

            self._log("设备连接失败，退出")

            self._state = "STOPPED"

            self._emit("state_update", "STOPPED")

            return



        self._state = "RUNNING"

        self._emit("state_update", "RUNNING")



        while self._running:

            self._loop_count += 1

            self._log(f"--- 第 {self._loop_count} 轮 ---")



            # Step 1: 识别位置栏，确认在小西天

            # pos = self._find("位置栏-小西天点卡服.png", threshold=0.7)

            # if pos is None:

            #     self._log("未检测到小西天位置栏，等待1秒...")

            #     # 调试: 保存当前帧用于分析

            #     debug_frame = self._get_frame()

            #     if debug_frame is not None:

            #         debug_path = os.path.join(project_dir, "_debug_frame.png")

            #         cv2.imwrite(debug_path, debug_frame)

            #         self._log(f"调试截图已保存: {debug_path} shape={debug_frame.shape}")

            #     time.sleep(1)

            #     continue

            # x, y, w, h, conf = pos

            # self._log(f"确认位置: 小西天 (conf={conf:.2f})")



            # Step 2: 点击打开地图

            ok = self._click_template("打开地图点卡服.png", threshold=0.85)

            if not ok:

                self._log("未找到打开地图按钮，重试...")

                time.sleep(0.5)

                continue



            # Step 3: 等待地图展开（给足够时间渲染）

            time.sleep(1.2)



            # Step 4: 识别小西天地图，随机点击

            # 调试: 保存当前帧分析

            frame = self._get_frame()

            if frame is not None:

                debug_path = os.path.join(project_dir, "_debug_map_frame.png")

                cv2.imwrite(debug_path, frame)

            map_r = self._find("点卡小西天地图.png", threshold=0.6)

            if map_r is None:

                self._log(f"未识别到小西天地图，调试截图已保存: _debug_map_frame.png shape={frame.shape if frame is not None else 'None'}")

                time.sleep(0.5)

                continue



            mx, my, mw, mh, mconf = map_r

            self._log(f"识别到小西天地图 {mw}x{mh} at ({mx},{my}) conf={mconf:.2f}")



            # 随机点击地图中某个位置（留边距避免点到边缘）

            margin_x = max(15, mw // 10)

            margin_y = max(15, mh // 10)

            rx = random.randint(mx + margin_x, mx + mw - margin_x)

            ry = random.randint(my + margin_y, my + mh - margin_y)

            self._log(f"随机点击地图位置 ({rx}, {ry})")

            self._tap(rx, ry)



            # Step 5: 等待弹窗出现，识别并点击关闭

            time.sleep(0.5)

            ok = self._click_template("关闭弹窗点卡服.png", threshold=0.7)

            if ok:

                self._log("弹窗已关闭")

            else:

                self._log("未检测到关闭弹窗按钮（可能已自动关闭）")



            self._log(f"第 {self._loop_count} 轮完成，等待5秒...")

            time.sleep(5)



        self._disconnect()

        self._state = "STOPPED"

        self._log("=== 已停止 ===")

        self._emit("state_update", "STOPPED")





# ================================================================

# 独立运行

# ================================================================



if __name__ == "__main__":

    import argparse

    from core.adb_util import AdbUtil



    parser = argparse.ArgumentParser(description="小西天场景自动化")

    parser.add_argument("--serial", "-s", default=None, help="ADB设备序列号")

    args = parser.parse_args()



    if not args.serial:

        devices = AdbUtil.list_devices()

        if not devices:

            print("未找到ADB设备，请连接设备后重试")

            sys.exit(1)

        if len(devices) == 1:

            args.serial = devices[0]["serial"]

        else:

            print("多个设备:")

            for i, d in enumerate(devices):

                print(f"  [{i}] {d['serial']} {d.get('resolution','')}")

            idx = input("选择设备序号: ").strip()

            args.serial = devices[int(idx)]["serial"]



    print(f"使用设备: {args.serial}")



    thread = XiaoXiTianThread(args.serial)

    thread.start()

    print("运行中，按 Ctrl+C 停止...")

    try:

        while thread.running:

            time.sleep(1)

    except KeyboardInterrupt:

        thread.stop()

        thread.join(timeout=5)

    print("已退出")

