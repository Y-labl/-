# -*- coding: utf-8 -*-
"""小西天场景自动化 - 横屏直连版（适配 debug_map_frame.png 实际画面）"""
import os, sys, time, random, threading
from datetime import datetime
import cv2
import math
import numpy as np

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
from battle import BattleHandler, get_monster_names
from core.adb_util import AdbUtil

# ---- 常量：模板基准分辨率（原始截图使用的横屏宽度）----
_REF_W = 1080  # 模板截图时的帧宽度，用于自动缩放适配
IMAGES_DIR = os.path.join(project_dir, "images")


class XiaoXiTianChangJingThread(threading.Thread):
    def __init__(self, serial, debug_win=False):
        super().__init__(daemon=True)
        self.serial = serial
        self._client = None
        self._running = False
        self._callbacks = []
        self._last_frame = None
        self._loop_count = 0
        self._state = "INIT"
        self._debug_win = debug_win
        self._debug_annotations = []
        self._battle = None  # 延迟初始化，等 client 就绪  # [(type, data), ...] type: "match"/"click"/"miss"

    @property
    def state(self): return self._state
    @property
    def battle_count(self): return getattr(self, "_battle_count", self._loop_count)

    def add_callback(self, name, func): self._callbacks.append((name, func))
    def _emit(self, name, *args):
        for n, f in self._callbacks:
            if n == name:
                try: f(*args)
                except: pass

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        full = f"[{ts}] {msg}"
        print(full)
        self._emit("log", full)

    @property
    def running(self): return self._running
    def stop(self):
        self._running = False
        self._state = "STOPPING"
        self._log("正在停止...")
        self._emit("state_update", "STOPPING")

    # ================================================================
    # 设备检查
    # ================================================================
    def _check_device(self):
        devices = AdbUtil.list_devices()
        if self.serial not in [d["serial"] for d in devices]:
            self._log(f"设备 {self.serial} 不在线")
            return False
        return True

    # ================================================================
    # pyscrcpy 连接（保持默认横屏输出）
    # ================================================================
    def _init_client(self):
        try:
            from pyscrcpy.core import Client
            self._log(f"连接设备 {self.serial} ...")
            client = Client(
                device=self.serial,
                max_size=1920,  # 全分辨率推流（和原版一致，避免模板缩放失真）
                bitrate=8000000,
                max_fps=15,
                block_frame=True,
                # 不锁定方向，让 scrcpy 输出原始竖屏（和设备一致）
            )
            client.start(threaded=True)

            for _ in range(50):
                if client.last_frame is not None:
                    break
                time.sleep(0.1)
            if client.last_frame is None:
                self._log("连接超时")
                client.stop()
                return False

            self._client = client
            frame = client.last_frame
            h, w = frame.shape[:2]
            self._log(f"已连接: {w}x{h} (帧:{frame.shape[1] if frame is not None else chr(39)+chr(63)+chr(39)}x{frame.shape[0] if frame is not None else chr(39)+chr(63)+chr(39)})")
            return True
        except Exception as e:
            self._log(f"连接失败: {e}")
            return False

    def _disconnect(self):
        if self._debug_win:
            try:
                cv2.destroyWindow("XiaoXiTian Debug")
                cv2.waitKey(1)
            except: pass
        if self._client:
            try: self._client.stop()
            except: pass
            self._client = None

    # ================================================================
    # 截图 & 点击（纯横屏，无旋转）
    # ================================================================
    def _get_frame(self):
        """返回原始帧，同步 resolution 到实际帧尺寸（关键：touch 用 resolution 做坐标映射）"""
        if self._client is None: return None
        frame = self._client.last_frame
        if frame is None: return None
        # 确保 resolution 与实际帧尺寸一致
        self._client.resolution = (frame.shape[1], frame.shape[0])
        self._last_frame = frame
        return frame

    def _tap(self, x, y):
        """点击：ADB input tap（稳定可靠，后台注入）"""
        if self._client is None: return
        frame = self._client.last_frame
        if frame is not None:
            fh, fw = frame.shape[:2]
            if x < 0 or y < 0 or x >= fw or y >= fh:
                self._log(f"  -> _tap: 越界 ({x},{y})/{fw}x{fh}")
                return
        src_x = int(x)
        src_y = int(y)
        try:
            self._client.device.shell(f"input tap {src_x} {src_y}")
        except Exception as e:
            self._log(f"  -> _tap: 失败 {e}")
    # ================================================================
    # 模板工具（要求模板为 1080x608 横屏）
    # ================================================================
    def _find(self, img_name, threshold=0.7):
        """查找模板，返回 (x, y, w, h, conf) 或 None（智能缩放）"""
        frame = self._get_frame()
        if frame is None: return None
        img_path = os.path.join(IMAGES_DIR, img_name)
        template_orig = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if template_orig is None:
            self._log(f"  -> 模板加载失败: {img_name}")
            return None
        fh, fw = frame.shape[:2]
        th_orig, tw_orig = template_orig.shape[:2]
        # 尝试多个缩放比例匹配（原尺寸 + 按宽度缩放）
        candidates = [(template_orig, 1.0)]
        REF_W = 1080
        if fw != REF_W and fw > 0:
            scale = fw / REF_W
            new_w = int(tw_orig * scale)
            new_h = int(th_orig * scale)
            # 仅当缩放后仍小于帧尺寸时才加入候选
            if new_w <= fw and new_h <= fh:
                scaled = cv2.resize(template_orig, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                candidates.append((scaled, scale))
        best_val = -1
        best_result = None
        for template, s in candidates:
            th, tw = template.shape[:2]
            if th > fh or tw > fw:
                continue
            effective_threshold = threshold
            if tw < 30 or th < 30:
                effective_threshold = max(threshold, 0.85)
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val > best_val and max_val >= effective_threshold:
                best_val = max_val
                best_result = (max_loc[0], max_loc[1], tw, th, float(max_val), template)
        if best_result is None:
            if self._debug_win:
                self._debug_annotations.append(("miss", img_name, threshold, threshold))
            return None
        x, y, tw, th, conf, template = best_result
        if self._debug_win:
            self._debug_annotations.append(("match", img_name, x, y, tw, th, conf, template))
        return (x, y, tw, th, conf)
    def _click_template(self, img_name, threshold=0.7):
        """查找模板并点击中心"""
        r = self._find(img_name, threshold)
        if r is None: return False
        x, y, w, h, conf = r
        cx, cy = x + w // 2, y + h // 2
        # 验证点击坐标在帧内
        frame = self._client.last_frame if self._client else None
        if frame is not None:
            fh, fw = frame.shape[:2]
            if cx < 0 or cy < 0 or cx >= fw or cy >= fh:
                self._log(f"⚠ 点击坐标越界: ({cx},{cy}) > 帧 {fw}x{fh}，已跳过")
                return False
        self._log(f"点击: {img_name} 中心=({cx},{cy}) conf={conf:.2f} 帧={fw}x{fh}")
        self._tap(cx, cy)
        if self._debug_win:
            self._debug_annotations.append(("click", img_name, cx, cy))
        return True

    # ================================================================
    # 调试窗口
    # ================================================================
    def _render_debug(self):
        """渲染调试窗口：在当前帧上标注匹配框、点击位置、置信度"""
        if not self._debug_win:
            return
        frame = self._last_frame
        if frame is None:
            return
        import copy
        display = copy.deepcopy(frame)

        for ann in self._debug_annotations:
            kind = ann[0]
            if kind == "match":
                _, name, x, y, tw, th, conf, tpl = ann
                # 画绿色匹配框
                cv2.rectangle(display, (x, y), (x + tw, y + th), (0, 255, 0), 2)
                # 标签：名称 + 置信度
                label = f"{name} {conf:.2f}"
                (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.rectangle(display, (x, y - lh - 6), (x + lw + 4, y), (0, 255, 0), -1)
                cv2.putText(display, label, (x + 2, y - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            elif kind == "click":
                _, name, cx, cy = ann
                # 画红色十字准星
                cv2.drawMarker(display, (cx, cy), (0, 0, 255),
                               cv2.MARKER_CROSS, 15, 2)
                cv2.putText(display, name, (cx + 10, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            elif kind == "miss":
                _, name, threshold, effective = ann
                # 在左上角显示未匹配信息
                pass  # miss 信息通过 _log 输出，窗口用状态栏

        # 帧信息状态栏（左上角）
        fh, fw = display.shape[:2]
        info = f"Frame: {fw}x{fh} | Loop: {self._loop_count}"
        cv2.putText(display, info, (5, fh - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        # 未匹配提示
        misses = [a for a in self._debug_annotations if a[0] == "miss"]
        if misses:
            miss_names = ", ".join(set(a[1] for a in misses))
            cv2.putText(display, f"MISS: {miss_names}", (5, 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        cv2.imshow("XiaoXiTian Debug", display)
        cv2.waitKey(1)
        self._debug_annotations.clear()

    # ================================================================
    # 核心流程
    # ================================================================
    def run(self):
        self._running = True
        self._loop_count = 0
        self._state = "CONNECTING"
        self._log("=== 小西天场景 v4 (横屏适配版) 启动 ===")
        self._log(f"设备: {self.serial}")

        if not self._check_device():
            self._state = "STOPPED"
            self._emit("state_update", "STOPPED")
            return

        if not self._init_client():
            self._state = "STOPPED"
            self._emit("state_update", "STOPPED")
            return

        self._state = "RUNNING"
        self._emit("state_update", "RUNNING")

        self._battle = BattleHandler(self._client, log_func=self._log)
        self._battle.set_mode("auto")
        self._battle.set_hp_threshold(30)
        self._battle.set_mp_threshold(20)
        self._battle.set_target_names(get_monster_names("小西天"))

        while self._running:
            self._loop_count += 1
            self._log(f"--- 第 {self._loop_count} 轮 ---")
            self._render_debug()

            # === A: 战斗检测（参照原版 startDuiZhang） ===
            if self._battle and self._battle.is_in_battle():
                self._log(">>> 进入战斗 <<<")
                self._battle._battle_count = 0
                self._battle._cached_targets = []
                self._battle._auto_toggled = False
                battle_rounds = 0
                while self._running and self._battle.is_in_battle():
                    battle_rounds += 1
                    flags = self._battle.check_battle_flags()
                    if flags:
                        self._battle.handle_battle_flags(flags)
                    if not self._battle.do_battle_round():
                        break
                    time.sleep(random.uniform(0.3, 0.6))
                self._log(f">>> 战斗结束 ({battle_rounds}回合) <<<")
                time.sleep(0.5)
                self._battle._check_hp_mp(in_battle=False)
                self._click_template("关闭弹窗点卡服.png", threshold=0.7)
                time.sleep(1)
                continue

            # === B: 打开地图 ===
            ok = self._click_template("打开地图点卡服.png", threshold=0.85)
            if not ok:
                self._log("未找到按钮，重试...")
                time.sleep(0.5)
                continue

            # === D: 找小西天地图 ===
            map_r = None
            elapsed = 0.0
            while elapsed < 5.0 and self._running:
                time.sleep(0.2)
                elapsed += 0.2
                if self._battle and self._battle.is_in_battle():
                    self._log("地图加载中遇怪，进入战斗")
                    self._battle._battle_count = 0
                    self._battle._cached_targets = []
                    self._battle._auto_toggled = False
                    br = 0
                    while self._running and self._battle.is_in_battle():
                        br += 1
                        flags = self._battle.check_battle_flags()
                        if flags: self._battle.handle_battle_flags(flags)
                        if not self._battle.do_battle_round(): break
                        time.sleep(random.uniform(0.3, 0.6))
                    self._log(f">>> 战斗结束 ({br}回合) <<<")
                    time.sleep(0.5)
                    self._click_template("关闭弹窗点卡服.png", threshold=0.7)
                    time.sleep(1)
                    break
                map_r = self._find("点卡小西天地图.png", threshold=0.6)
                if map_r:
                    self._log(f"地图已识别 (耗时{elapsed:.1f}s)")
                    break

            if map_r is None:
                self._render_debug()
                self._log("超时未识别地图，跳过")
                time.sleep(2)
                continue

            mx, my, mw, mh, mconf = map_r
            self._render_debug()
            self._log(f"地图位置: ({mx},{my}), {mw}x{mh}, conf={mconf:.2f}")

            # === E: 点击地图 ===
            margin_x = max(10, mw // 12)
            margin_y = max(10, mh // 12)
            rx = random.randint(mx + margin_x, mx + mw - margin_x)
            ry = random.randint(my + margin_y, my + mh - margin_y)
            self._log(f"地图点击: ({rx}, {ry})")
            self._tap(rx, ry)
            if random.random() < 0.3:
                ox, oy = random.randint(-5, 5), random.randint(-5, 5)
                time.sleep(random.uniform(0.05, 0.1))
                self._tap(rx + ox, ry + oy)

            # === F: 关闭弹窗 ===
            time.sleep(0.5)
            self._click_template("关闭弹窗点卡服.png", threshold=0.7)

            time.sleep(random.uniform(0.3, 0.6))

        self._disconnect()
        self._state = "STOPPED"
        self._log("=== 已停止 ===")
        self._emit("state_update", "STOPPED")

# ================================================================
# 入口函数（同前，仅微调提示）
# ================================================================
def bind_device(serial=None):
    devices = AdbUtil.list_devices()
    if not devices:
        print("⚠️ 未找到ADB设备，请确认：")
        print("  1. 手机USB连接 + 开启USB调试")
        print("  2. adb devices 可看到设备")
        return None
    if serial:
        if serial in [d["serial"] for d in devices]:
            d = next(d for d in devices if d["serial"] == serial)
            print(f"✅ 绑定设备: {serial} | 分辨率: {d.get('resolution', '未知')}")
            return serial
        print(f"❌ 设备 {serial} 不在线")
        return None
    if len(devices) == 1:
        d = devices[0]
        print(f"✅ 自动绑定: {d['serial']} | 分辨率: {d.get('resolution', '未知')}")
        return d["serial"]
    print("发现多个设备，请选择：")
    for i, d in enumerate(devices):
        print(f"  [{i}] {d['serial']} {d.get('resolution', '')}")
    while True:
        try:
            idx = int(input("序号: "))
            return devices[idx]["serial"]
        except (ValueError, IndexError):
            print("无效输入")

def list_devices():
    devs = AdbUtil.list_devices()
    print(f"在线设备 ({len(devs)}):")
    for d in devs: print(f"  {d['serial']} {d.get('resolution','')}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial", help="设备序列号")
    parser.add_argument("-l", "--list", action="store_true", help="列出设备")
    parser.add_argument("--no-debug", action="store_true", help="关闭实时调试窗口")
    args = parser.parse_args()

    if args.list:
        list_devices()
        sys.exit(0)

    serial = bind_device(args.serial)
    if not serial:
        sys.exit(1)

    debug = not getattr(args, "no_debug", False)  # 默认开启调试窗口
    thread = XiaoXiTianChangJingThread(serial, debug_win=debug)
    thread.start()
    if debug:
        print("调试窗口: 绿色框=匹配成功, 红色十字=点击位置, 按Q关闭窗口")
    else:
        print("调试窗口已关闭 (--no-debug)")
    print("运行中，Ctrl+C 停止...")
    try:
        while thread.running:
            time.sleep(1)
    except KeyboardInterrupt:
        thread.stop()
        thread.join(5)
    print("退出")