# -*- coding: utf-8 -*-
"""忠诚度恢复工具类 - 独立运行，传入设备号自动连接并执行恢复流程"""

import os
import sys
import time
import random
import subprocess as sp
import cv2
import numpy as np
from datetime import datetime
import re

# ── 路径 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(SCRIPT_DIR, "image")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")

# ── ADB ──
_ADB_EXE = os.path.join(SCRIPT_DIR, ".venv", "Lib", "site-packages", "adbutils", "binaries", "adb.exe")
if not os.path.exists(_ADB_EXE):
    try:
        import adbutils
        _ADB_EXE = adbutils.adb_path()
    except Exception:
        _ADB_EXE = "adb"


# ======================== 工具函数 ========================

def imread_unicode(path, flags=cv2.IMREAD_COLOR):
    arr = np.fromfile(path, dtype=np.uint8)
    if arr.size == 0:
        return None
    return cv2.imdecode(arr, flags)


def load_template(name):
    for d in [IMAGE_DIR, IMAGES_DIR]:
        for ext in [".png", ".bmp"]:
            for suffix in ["点卡服", "畅玩服", ""]:
                path = os.path.join(d, f"{name}{suffix}{ext}")
                if os.path.exists(path):
                    img = imread_unicode(path)
                    if img is not None:
                        return img
    return None


def match_template(screenshot, template, threshold=0.75, debug_name=""):
    if screenshot is None or template is None:
        return None
    h, w = screenshot.shape[:2]
    tw, th = template.shape[1], template.shape[0]
    if h < th or w < tw:
        return None
    # 多尺度 + 多方法匹配
    best_result = None
    best_val = -1
    scales = [round(x, 2) for x in np.arange(0.7, 1.35, 0.05)]
    methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
    for method in methods:
        for s in scales:
            if abs(s - 1.0) < 0.01:
                result = cv2.matchTemplate(screenshot, template, method)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val > best_val:
                    best_val = max_val
                    best_result = (max_loc[0] + tw // 2, max_loc[1] + th // 2, max_val)
            else:
                stw = max(2, int(tw * s))
                sth = max(2, int(th * s))
                if stw > w or sth > h:
                    continue
                small_tmpl = cv2.resize(template, (stw, sth), interpolation=cv2.INTER_AREA)
                result = cv2.matchTemplate(screenshot, small_tmpl, method)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val > best_val:
                    best_val = max_val
                    best_result = (max_loc[0] + stw // 2, max_loc[1] + sth // 2, max_val)
    if best_result is not None and best_val >= threshold:
        return best_result
    if debug_name:
        print("[DEBUG] {}: best={:.3f} (threshold={})".format(debug_name, best_val, threshold))
    return None


def adb_tap(serial, x, y):
    sp.run([_ADB_EXE, "-s", serial, "shell", "input", "tap", str(x), str(y)],
           capture_output=True, timeout=3)


# ======================== 场景恢复配置 ========================

SCENE_RECOVERY = {
    "小雷音寺": {
        "steps": [
            {"action": "click_template", "name": "道具", "threshold": 0.6, "wait": 0.3},
            {"action": "click_template", "name": "摄妖香", "threshold": 0.5, "wait": 0.3},
            {"action": "click_position", "x": 268, "y": 260, "wait": 0.5},
            {"action": "click_template", "name": "关闭弹窗", "wait": 0.3},
            {"action": "click_template", "name": "打开地图", "wait": 0.5},
            {"action": "click_map", "x": 293, "y": 94, "wait": 0.3},
            {"action": "close_map", "wait": 0.3},
            {"action": "detect_wuyi", "timeout": 120, "wait": 0.5},
        ],
    },
    "小西天": {
        "steps": [
            {"action": "click_template", "name": "道具", "threshold": 0.6, "wait": 0.3},
            {"action": "click_template", "name": "摄妖香", "threshold": 0.5, "wait": 0.3},
            {"action": "click_position", "x": 268, "y": 260, "wait": 0.5},
            {"action": "click_template", "name": "关闭弹窗", "wait": 0.3},
            {"action": "click_template", "name": "打开地图", "wait": 0.5},
            {"action": "click_position", "x": 535, "y": 59, "wait": 0.3},
            {"action": "click_sequence", "positions": [[657,220],[530,155],[723,279],[535,158],[592,158],[653,220],[718,279],[539,138]], "interval": 0.1, "wait": 0.3},
            {"action": "close_map", "wait": 0.3},
            {"action": "detect_wuyi", "timeout": 120, "wait": 0.5},
        ],
    },
}


# ======================== 工具类 ========================

class ToolEngine:
    def __init__(self, serial):
        self.serial = serial
        self.client = None
        self.stream_w = 800
        self.stream_h = 448
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.templates = {}
        self.cfg = {"map": ""}
        self.last_map_name = ""
        self.log_lines = []

        self._load_all_templates()

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.log_lines.append(line)
        print(line)

    # ---------- 模板加载 ----------

    def _load_all_templates(self):
        self._log("正在加载模板...")
        self.templates.clear()

        names = [
            "打开地图", "地图-筛选", "关闭地图", "好友入口",
            "PK-妙手空空技能", "PK-自动按钮", "PK-取消自动战斗",
            "道具", "道具-道具栏", "关闭弹窗", "关闭聊天", "关闭活动弹窗", "左下角返回",
            "菜单-指引", "摄妖香", "使用摄妖香", "wuyi", "wuyi1", "wuyi2", "wuyi3",
        ]
        for name in names:
            tmpl = load_template(name)
            if tmpl is not None:
                self.templates[name] = tmpl
                h, w = tmpl.shape[:2]
                self._log(f"  [OK] {name} ({w}x{h})")
            else:
                self._log(f"  [WARN] 未找到: {name}")

        # 加载怪物模板
        monster_names = [
            ("炎魔神", "炎魔神"), ("噬天虎", "噬天虎"),
            ("金饶僧", "金饶僧"), ("雾中仙", "雾中仙"),
            ("灵符女娲", "灵符女娲"), ("律法女娲", "律法女娲"),
            ("净瓶女娲", "净瓶女娲"), ("吸血鬼", "吸血鬼"),
            ("地狱战神", "地狱战神"), ("幽灵", "幽灵"),
            ("古代瑞兽", "古代瑞兽"), ("天兵", "天兵"),
            ("芙蓉仙子", "芙蓉仙子"), ("蛟龙", "蛟龙"),
            ("凤凰", "凤凰"), ("雨师", "雨师"),
            ("如意仙子", "如意仙子"), ("星灵仙子", "星灵仙子"),
            ("瓶子", "瓶子"), ("雾中仙", "雾中仙"),
            ("摄妖香", "摄妖香"), ("wuyi", "wuyi"),
        ]
        for label, fname in monster_names:
            for d in [IMAGE_DIR, IMAGES_DIR]:
                for ext in [".png", ".bmp"]:
                    for suffix in ["点卡服", "畅玩服", ""]:
                        path = os.path.join(d, f"{fname}{suffix}{ext}")
                        if os.path.exists(path):
                            img = imread_unicode(path)
                            if img is not None:
                                self.templates[label] = img
                                break
                    if self.templates.get(label) is not None:
                        break
                if self.templates.get(label) is not None:
                    break

        self._log(f"模板加载完成，共 {len(self.templates)} 个")

    # ---------- 设备连接 ----------

    def connect(self):

        # 验证 ADB
        try:
            r = sp.run([_ADB_EXE, "-s", self.serial, "shell", "echo", "ok"],
                       capture_output=True, text=True, timeout=5)
            if r.returncode != 0 or r.stdout.strip() != "ok":
                self._log(f"ADB 连接失败: {r.stderr.strip()}")
                return False
        except Exception as e:
            self._log(f"ADB 异常: {e}")
            return False
        self._log("ADB 连接正常")

        # 获取设备分辨率
        device_w, device_h = 0, 0
        try:
            r = sp.run([_ADB_EXE, "-s", self.serial, "shell", "wm", "size"],
                       capture_output=True, text=True, timeout=5)
            import re
            m = re.search(r"(\d+)x(\d+)", r.stdout)
            if m:
                device_w, device_h = int(m.group(1)), int(m.group(2))
                self._log(f"设备分辨率: {device_w}x{device_h}")
        except Exception:
            self._log("无法获取设备分辨率")

        # 启动 pyscrcpy
        try:
            from pyscrcpy import Client
            self.client = Client(self.serial, bitrate=8000000, max_fps=10, max_size=800)
            self.client.start(threaded=True)
            time.sleep(1.5)
            if self.client.last_frame is None:
                self._log("pyscrcpy 无法获取首帧")
                return False
            h, w = self.client.last_frame.shape[:2]
            self._log(f"pyscrcpy 原始帧: {w}x{h}")

            # 统一为横屏: 如果竖屏则交换宽高标记
            if h > w:  # 竖屏帧
                self.stream_w = h
                self.stream_h = w
                self._log(f"竖屏→横屏: {self.stream_w}x{self.stream_h}")
# fix: vertical frame - swap device dims too
                if device_h > device_w:
                    device_w,device_h=device_h,device_w
                    self._log(f"corrected: {device_w}x{device_h}")
            else:  # 已经是横屏帧
                self._log(f"横屏帧: {w}x{h}")
                # 如果设备是竖屏但游戏是横屏，交换设备尺寸
                if device_h > device_w:
                    device_w, device_h = device_h, device_w
                    self._log(f"设备(横屏修正): {device_w}x{device_h}")
                self.stream_w = w
                self.stream_h = h

            if device_w and device_h:
                self.scale_x = device_w / self.stream_w
                self.scale_y = device_h / self.stream_h
            else:
                self.scale_x = self.scale_y = 1.0
            self._log(f"缩放: {self.scale_x:.3f}x{self.scale_y:.3f}")

            self.init_ocr()
            return True

        except ImportError:
            self._log("请安装 pyscrcpy: pip install pyscrcpy")
            return False
        except Exception as e:
            self._log(f"pyscrcpy 启动失败: {e}")
            return False
    def disconnect(self):
        if self.client:
            try:
                self.client.stop()
            except Exception:
                pass
            self.client = None
        self._log("设备已断开")

    # ---------- 核心操作 ----------

    def get_frame(self):
        if self.client is None:
            return None
        f = self.client.last_frame
        if f is not None:
            f = cv2.resize(f, (self.stream_w, self.stream_h), interpolation=cv2.INTER_LINEAR)
        return f.copy() if f is not None else None

    def tap(self, x, y, offset=True):
        if offset:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)
        adb_tap(self.serial, int(x * self.scale_x), int(y * self.scale_y))

    def find(self, frame, name, threshold=0.75):
        tmpl = self.templates.get(name)
        if tmpl is not None:
            result = match_template(frame, tmpl, threshold, debug_name=name)
            if result is not None:
                return result
        # fallback: try alternative template names
        fallbacks = {
            "道具": ["道具-道具栏"],
        }
        for fb_name in fallbacks.get(name, []):
            fb_tmpl = self.templates.get(fb_name)
            if fb_tmpl is not None:
                result = match_template(frame, fb_tmpl, threshold, debug_name=fb_name)
                if result is not None:
                    return result
        return None

    def match_template_multi(self, frame, names, threshold=0.7):
        """多模板匹配 + NMS（参考模板匹配.py do_match）"""
        templates = []
        for n in names:
            t = self.templates.get(n)
            if t is not None:
                templates.append(t)
        if not templates:
            return None
        h, w = frame.shape[:2]
        all_rects = []
        scales = [round(x, 2) for x in np.arange(0.7, 1.35, 0.05)]
        for ti, templ in enumerate(templates):
            tw, th = templ.shape[1], templ.shape[0]
            for method in [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]:
                for s in scales:
                    stw = max(2, int(tw * s))
                    sth = max(2, int(th * s))
                    if stw > w or sth > h:
                        continue
                    if abs(s - 1.0) < 0.01:
                        scaled = templ
                    else:
                        scaled = cv2.resize(templ, (stw, sth), interpolation=cv2.INTER_AREA)
                    result = cv2.matchTemplate(frame, scaled, method)
                    locs = np.where(result >= threshold)
                    pts = list(zip(*locs[::-1]))
                    for px, py in pts:
                        all_rects.append((px, py, px + stw, py + sth, result[py, px]))
        if not all_rects:
            return None
        boxes = [[x1, y1, x2 - x1, y2 - y1] for (x1, y1, x2, y2, score) in all_rects]
        scores = [score for (_, _, _, _, score) in all_rects]
        try:
            pick = cv2.dnn.NMSBoxes(boxes, scores, 0.0, 0.3)
            if pick is not None and len(pick) > 0:
                pick = pick.flatten()
                best_idx = max(pick, key=lambda i: scores[i])
                x1, y1, x2, y2, score = all_rects[best_idx]
                return ((x1 + x2) // 2, (y1 + y2) // 2, score)
        except:
            pass
        best = max(all_rects, key=lambda r: r[4])
        return ((best[0] + best[2]) // 2, (best[1] + best[3]) // 2, best[4])

    def close_pop(self, is_one_time=False, try_count=0):
        if try_count > 3:
            return
        try_count += 1
        frame = self.get_frame()
        if frame is None:
            return
        close_found = 0
        for name in ["关闭弹窗", "关闭聊天", "关闭活动弹窗", "左下角返回"]:
            r = self.find(frame, name)
            if r:
                self.tap(r[0] + random.randint(0, 20), r[1] + random.randint(0, 15))
                close_found += 1
                time.sleep(random.uniform(0.5, 0.7))
        frame = self.get_frame()
        if frame is None:
            return
        if self.find(frame, "菜单-指引"):
            self.tap(15, 78)
            time.sleep(random.uniform(0.3, 0.5))
        if not is_one_time and close_found > 0:
            time.sleep(random.uniform(0.3, 0.5))

    # ---------- OCR 地图检测 ----------

    def init_ocr(self):
        self.ocr_engine = None
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr_engine = RapidOCR()
            self.ocr_engine(np.zeros((64, 64, 3), dtype=np.uint8))
            self._log("RapidOCR 初始化完成")
        except Exception as e:
            self._log(f"RapidOCR 不可用: {e}")

    def detect_map(self, frame=None):
        if self.ocr_engine is None:
            return None, None
        f = frame if frame is not None else self.get_frame()
        if f is None:
            return None, None
        h, w = f.shape[:2]
        sx = self.scale_x or 1.0
        sy = self.scale_y or 1.0
        cx = int(131 / sx)
        cy = int(40 / sy)
        cw = min(int(200 / sx), w - cx)
        ch = min(int(100 / sy), h - cy)
        if cw <= 0 or ch <= 0:
            return None, None
        crop = f[cy:cy+ch, cx:cx+cw]
        try:
            result, _ = self.ocr_engine(crop)
            if result is None:
                return None, None
            map_name, coord = None, None
            import re
            for box, text, conf in result:
                text = str(text).strip()
                if conf < 0.5 or len(text) < 2:
                    continue
                if any(k in text for k in ['西天', '寺', '塔', '洞', '殿', '谷', '山', '林', '湖']):
                    map_name = text
                import re
                m = re.search(r'(\d+)[.,](\d+)', text)
                if m:
                    coord = (int(m.group(1)), int(m.group(2)))
            return map_name, coord
        except:
            return None, None

    # ---------- 场景获取 ----------

    def _get_current_map(self):
        return self.cfg.get("map", "") or self.last_map_name or ""

    # ---------- 忠诚度恢复 ----------

    def loyalty_recovery(self):
        frame = self.get_frame()
        if frame is None:
            self._log("无法获取画面帧")
            return

        map_name = self._get_current_map()
        if not map_name:
            detected_map, _ = self.detect_map(frame)
            if detected_map:
                map_name = detected_map
                self.last_map_name = map_name
                self._log(f"OCR 检测到地图: {map_name}")
        config = SCENE_RECOVERY.get(map_name)

        if config is None:
            self._log(f"当前场景 [{map_name}] 未配置忠诚度恢复流程，跳过")
            return

        self._log(f"执行 [{map_name}] 忠诚度恢复流程...")

        for i, step in enumerate(config["steps"], 1):
            action = step["action"]
            wait = step.get("wait", 0.3)

            if action == "click_template":
                name = step["name"]
                thr = step.get("threshold", 0.75)
                btn = self.find(frame, name, threshold=thr)
                if btn is None:
                    self._log("[{}] 未找到 {}, abort".format(i, name))
                    return
                self._log("[{}] click {} ({},{})".format(i, name, btn[0], btn[1]))
                self.tap(btn[0], btn[1])
                time.sleep(wait)
                frame = self.get_frame()

            elif action == "double_click_template":
                name = step["name"]
                btn = self.find(frame, name)
                if btn is None:
                    self._log(f"[{i}] 未找到 {name}, abort")
                    return
                cx, cy = btn[0], btn[1]
                self._log(f"[{i}] double-click {name} ({cx},{cy})")
                self.tap(cx, cy)  # first tap (random offset)
                time.sleep(0.1)  # 100ms
                self.tap(cx, cy)  # second tap (random offset)
                time.sleep(wait)
                frame = self.get_frame()

            elif action == "click_map":
                x, y = step["x"], step["y"]
                self._log(f"[{i}] 点击地图坐标 ({x}, {y})")
                self.tap(x, y, offset=False)
                time.sleep(wait)

            elif action == "close_map":
                self._log(f"[{i}] 关闭地图")
                self.close_pop(is_one_time=True)
                time.sleep(wait)

            elif action == "click_position":
                cx = step["x"]
                cy = step["y"]
                self._log(f"[{i}] click position ({cx},{cy})")
                self.tap(cx, cy)
                time.sleep(wait)
                frame = self.get_frame()

            elif action == "input_coord":
                name = step["name"]
                offset_x = step.get("offset_x", 0)
                offset_y = step.get("offset_y", 0)
                text = step["text"]
                thr = step.get("threshold", 0.75)
                btn = self.find(frame, name, threshold=thr)
                if btn is None:
                    self._log("[{}] 未找到 {}, abort".format(i, name))
                    return
                tx = btn[0] + offset_x
                ty = btn[1] + offset_y
                self._log("[{}] input_coord {} at ({},{}) text={}".format(i, name, tx, ty, text))
                self.tap(tx, ty)
                time.sleep(0.3)
                sp.run([_ADB_EXE, "-s", self.serial, "shell", "input", "text", str(text)],
                       capture_output=True, timeout=3)
                time.sleep(wait)
                frame = self.get_frame()

            elif action == "click_sequence":
                positions = step["positions"]
                interval = step.get("interval", 0.1)
                self._log("[{}] click_sequence {} points".format(i, len(positions)))
                for px, py in positions:
                    self.tap(px, py)
                    time.sleep(interval)
                time.sleep(wait)

            elif action == "detect_wuyi":
                timeout = step.get("timeout", 120)
                threshold = step.get("threshold", 0.65)
                wuyi_names = step.get("templates", ["wuyi1", "wuyi2", "wuyi3"])
                self._log("into wuyi detect mode, timeout {}s, templates={}".format(timeout, wuyi_names))
                start_t = time.time()
                found = False
                while time.time() - start_t < timeout:
                    frame = self.get_frame()
                    if frame is None:
                        time.sleep(0.2)
                        continue
                    result = self.match_template_multi(frame, wuyi_names, threshold=threshold)
                    if result:
                        cx, cy, conf = result
                        self._log("wuyi found ({},{}) conf={:.0%}".format(cx, cy, conf))
                        self.tap(cx, cy)
                        time.sleep(0.3)
                        # click popup
                        f2 = self.get_frame()
                        if f2 is not None:
                            fh, fw = f2.shape[:2]
                            sx = fw / 800.0
                            sy = fh / 448.0
                        else:
                            sx = sy = 1.0
                        yb_x = int(665 * sx)
                        yb_y = int(225 * sy)
                        self._log("click popup ({},{})".format(yb_x, yb_y))
                        self.tap(yb_x, yb_y, offset=False)
                        time.sleep(0.2)
                        yb2_x = int(780 * sx)
                        yb2_y = int(353 * sy)
                        self._log("click confirm ({},{})".format(yb2_x, yb2_y))
                        self.tap(yb2_x, yb2_y, offset=False)
                        found = True
                        break
                    time.sleep(0.5)
                if not found:
                    self._log("timeout, no wuyi detected")
                time.sleep(wait)

        self._log("loyalty recovery done")

if __name__ == "__main__":
    import sys
    serial = sys.argv[1] if len(sys.argv) > 1 else "WEENU18810135788"
    map_name = sys.argv[2] if len(sys.argv) > 2 else ""
    print(f"device: {serial}")
    if map_name:
        print(f"map: {map_name}")
    print("=" * 50)
    engine = ToolEngine(serial)
    if engine.connect():
        if map_name:
            engine.cfg["map"] = map_name
        engine._log("connected, start loyalty recovery...")
        engine.loyalty_recovery()
        engine.disconnect()
    else:
        print("connect failed")
