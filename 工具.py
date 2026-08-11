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
from rapidocr_onnxruntime import RapidOCR

# 打包为 windowed exe（console=False）后，调用控制台程序（adb.exe）会闪黑框，
# 所有 subprocess 调用必须带 CREATE_NO_WINDOW 抑制窗口弹出
CREATE_NO_WINDOW = getattr(sp, "CREATE_NO_WINDOW", 0)

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
           capture_output=True, timeout=3, creationflags=CREATE_NO_WINDOW)


# ======================== 场景恢复配置 ========================

# ======================== 通用基础步骤模板 ========================
_BASE_PART1 = [  # 步骤 1-6: 使用摄妖香 → 打开地图
    {"action": "click_template", "name": "道具", "threshold": 0.6, "wait": 0.3},
    {"action": "click_template", "name": "摄妖香", "threshold": 0.5, "wait": 0.3},
    {"action": "click_position", "x": 268, "y": 260, "wait": 0.5},
    {"action": "click_template", "name": "关闭弹窗", "wait": 0.3},
    {"action": "click_template", "name": "打开地图", "wait": 0.5},
]

_BASE_PART2 = [  # 步骤 8: 关闭地图弹窗
    {"action": "click_template", "name": "关闭弹窗", "wait": 0.5},
]

_BASE_PART3 = [  # 步骤 10-13: 使用洞冥草 → 关闭弹窗
    {"action": "click_template", "name": "道具", "threshold": 0.6, "wait": 0.3},
    {"action": "click_template", "name": "洞冥草", "threshold": 0.5, "wait": 0.3},
    {"action": "click_position", "x": 281, "y": 296, "wait": 0.5},
    {"action": "click_template", "name": "关闭弹窗", "wait": 0.3},
]

# ======================== 场景配置 ========================
# 方式一: 直接定义 steps（兼容旧配置）
# 方式二: 定义 coord_input + wait_target，自动拼接通用模板
SCENE_RECOVERY = {
    "小雷音寺": {
        "coord_input": [  # 步骤 6-7: 输入地图坐标
            {"action": "click_position", "x": 657, "y": 72, "wait": 0.3},
            {"action": "click_sequence", "positions": [[530,275],[595,278],[723,275],[530,157],[592,153],[595,222],[718,275]], "interval": 0.1, "wait": 0.3},
        ],
        "wait_target": {  # 步骤 9: 等待到达目标坐标 → 点击
            "action": "wait_coord",
            "target_map": "小雷音寺", "target_x": 78, "target_y": 125, "tolerance": 3, "timeout": 120,
            "clicks": [[504,186],[662,214],[565,401]], "wait": 0.5,
        },
    },
    "龙窟三层": {
        "coord_input": [  # 步骤 6-7: 输入地图坐标
            {"action": "click_position", "x": 683, "y": 101, "wait": 0.3},
            {"action": "click_sequence", "positions": [[451,258],[451,258],[578,325],[395,200],[451,262],[578,318]], "interval": 0.1, "wait": 0.3},
        ],
        "wait_target": {  # 步骤 9: 等待到达目标坐标 → 点击
            "action": "wait_coord",
            "target_map": "龙窟三层", "target_x": 55, "target_y": 15, "tolerance": 3, "timeout": 120,
            "clicks": [[290,197],[661,220],[565,401]], "wait": 0.5,
        },
    },
    "凤巢三层": {
        "coord_input": [  # 步骤 6-7: 输入地图坐标
            {"action": "click_position", "x": 618, "y": 137, "wait": 0.3},
            {"action": "click_sequence", "positions": [[573,233],[573,233],[640,354],[517,233],[573,354],[635,354]], "interval": 0.1, "wait": 0.3},
        ],
        "wait_target": {  # 步骤 9: 等待到达目标坐标 → 点击
            "action": "wait_coord",
            "target_map": "凤巢三层", "target_x": 33, "target_y": 29, "tolerance": 3, "timeout": 120,
            "clicks": [[290,167],[661,220],[565,401]], "wait": 0.5,
        },
    },
    "女娲神迹": {
        "coord_input": [  # 步骤 6-7: 输入地图坐标
            {"action": "click_position", "x": 595, "y": 108, "wait": 0.3},
            {"action": "click_sequence", "positions": [[535,334],[473,209],[661,328],[538,269],[478,325],[661,331]], "interval": 0.1, "wait": 0.3},
        ],
        "wait_target": {  # 步骤 9: 等待到达目标坐标 → 点击
            "action": "wait_coord",
            "target_map": "女娲神迹", "target_x": 81, "target_y": 57, "tolerance": 3, "timeout": 120,
            "clicks": [[513,190],[661,220],[565,401]], "wait": 0.5,
        },
    },
    "子母河底": {
        "coord_input": [  # 步骤 6-7: 输入地图坐标
            {"action": "click_position", "x": 599, "y": 111, "wait": 0.3},
            {"action": "click_sequence", "positions": [[468,267],[538,269],[661,325],[595,204],[661,267],[661,328]], "interval": 0.1, "wait": 0.3},
        ],
        "wait_target": {  # 步骤 9: 等待到达目标坐标 → 点击
            "action": "wait_coord",
            "target_map": "子母河底", "target_x": 45, "target_y": 30, "tolerance": 3, "timeout": 120,
            "clicks": [[324,167],[662,214],[565,401]], "wait": 0.5,
        },
    },
    "小西天": {
        "coord_input": [  # 步骤 7: 输入地图坐标
            {"action": "click_position", "x": 535, "y": 59, "wait": 0.3},
            {"action": "click_sequence", "positions": [[657,220],[530,155],[723,279],[535,158],[592,158],[653,220],[718,279]], "interval": 0.1, "wait": 0.3},
        ],
        "wait_target": {  # 步骤 9: 等待到达目标坐标 → 点击
            "action": "wait_coord",
            "target_map": "小西天", "target_x": 61, "target_y": 126, "tolerance": 3, "timeout": 120,
            "clicks": [[522,184],[662,214],[565,401]], "wait": 0.5,
        },
    },
}

def _build_floor_recovery(floor_name, legs_down, legs_up, third_scene):
    """构建五层忠诚恢复完整流程 steps（复用场景切换引擎的层间传送 + 三层输入坐标恢复）：
    层间传送下行到三层 → 打开地图输入三层恢复点坐标 → 洞冥草恢复 →
    层间传送上行回五层 → 吃摄妖香。"""
    third = SCENE_RECOVERY[third_scene]
    steps = []
    # 1) 层间传送下行：五层→四层→三层（场景切换引擎小地图点击+OCR验证）
    steps.append({"action": "layer_teleport", "legs": legs_down, "wait": 0.5})
    # 2) 打开地图 → 输入三层恢复点坐标
    steps.append({"action": "click_template", "name": "打开地图", "wait": 0.5})
    steps.extend(third.get("coord_input", []))
    steps.append({"action": "debug_shot", "tag": "after_coord_input", "wait": 0.3})
    steps.extend(_BASE_PART2)
    # 3) 等待到达三层恢复点 → 点击
    if third.get("wait_target"):
        wait_step = dict(third["wait_target"])
        retry_inputs = list(third.get("coord_input", []))
        if retry_inputs:
            wait_step["retry_inputs"] = [
                {"action": "click_template", "name": "打开地图", "threshold": 0.6, "wait": 0.5},
            ] + retry_inputs
            wait_step["retry_inputs"].append(
                {"action": "click_template", "name": "关闭弹窗", "threshold": 0.5, "wait": 0.5})
        steps.append(wait_step)
    # 4) 洞冥草恢复
    steps.extend(_BASE_PART3)
    # 5) 层间传送上行：三层→四层→五层
    steps.append({"action": "layer_teleport", "legs": legs_up, "wait": 0.5})
    # 6) 吃摄妖香（回五层打怪前）
    steps.append({"action": "click_template", "name": "道具", "threshold": 0.6, "wait": 0.3})
    steps.append({"action": "click_template", "name": "摄妖香", "threshold": 0.5, "wait": 0.3})
    steps.append({"action": "click_position", "x": 268, "y": 260, "wait": 0.5})
    steps.append({"action": "click_template", "name": "关闭弹窗", "wait": 0.3})
    return steps

# 五层恢复配置：层间传送下行到三层恢复 → 传送回五层 → 摄妖香
SCENE_RECOVERY["龙窟五层"] = {
    "steps": _build_floor_recovery(
        "龙窟五层",
        [["龙窟五层", "龙窟四层"], ["龙窟四层", "龙窟三层"]],
        [["龙窟三层", "龙窟四层"], ["龙窟四层", "龙窟五层"]],
        "龙窟三层",
    ),
}
SCENE_RECOVERY["凤巢五层"] = {
    "steps": _build_floor_recovery(
        "凤巢五层",
        [["凤巢五层", "凤巢四层"], ["凤巢四层", "凤巢三层"]],
        [["凤巢三层", "凤巢四层"], ["凤巢四层", "凤巢五层"]],
        "凤巢三层",
    ),
}

def build_steps(config):
    """根据场景配置构建完整步骤列表"""
    if "steps" in config:
        return config["steps"]
    steps = list(_BASE_PART1)  # 步骤 1-6
    steps.extend(config.get("coord_input", []))  # 步骤 7
    steps.append({"action": "debug_shot", "tag": "after_coord_input", "wait": 0.3})
    steps.extend(_BASE_PART2)  # 步骤 8
    if config.get("wait_target"):
        wait_step = dict(config["wait_target"])  # 步骤 9
        retry_inputs = list(config.get("coord_input", []))
        if retry_inputs:
            # 重试时地图已关闭，先重新打开地图 -> 输入坐标 -> 关闭地图，
            # 否则等待循环里 OCR 的是地图面板而非角色坐标
            wait_step["retry_inputs"] = [
                {"action": "click_template", "name": "打开地图", "threshold": 0.6, "wait": 0.5},
            ] + retry_inputs
            wait_step["retry_inputs"].append(
                {"action": "click_template", "name": "关闭弹窗", "threshold": 0.5, "wait": 0.5})
        steps.append(wait_step)
    steps.extend(_BASE_PART3)  # 步骤 10-13
    # 恢复后的尾部步骤（如：层间传送回原打怪场景 + 摄妖香）
    steps.extend(config.get("after_steps", []))
    return steps


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
        self.ocr = None  # 延迟初始化
        self.last_map_name = ""
        self.log_lines = []
        self._stop_event = None  # 外部停止信号

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
            "道具", "道具-道具栏", "洞冥草", "关闭弹窗", "关闭聊天", "关闭活动弹窗", "左下角返回",
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

    def _init_ocr(self):
        if self.ocr is None:
            self._log("初始化 OCR...")
            self.ocr = RapidOCR()
            self.ocr(np.zeros((64, 64, 3), dtype=np.uint8))
            self.ocr_engine = self.ocr

    # OCR 裁剪区域（设备分辨率下的坐标，对齐 mhxy_engine.py 的 OCR_CROP）
    OCR_CROP = {"x": 131, "y": 40, "w": 200, "h": 100}

    def _ocr_coord(self, frame, log=True):
        """OCR 检测当前地图名和坐标（仅识别顶部地图名+坐标区域），返回 (map_name, (x, y)) 或 (None, None)"""
        fh, fw = frame.shape[:2]
        # 根据流分辨率缩放 OCR 区域
        cx = max(0, int(self.OCR_CROP["x"] / self.scale_x))
        cy = max(0, int(self.OCR_CROP["y"] / self.scale_y))
        cw = min(int(self.OCR_CROP["w"] / self.scale_x), fw - cx)
        ch = min(int(self.OCR_CROP["h"] / self.scale_y), fh - cy)
        if cw <= 0 or ch <= 0:
            return None, None
        roi = frame[cy:cy+ch, cx:cx+cw]
        if roi.size == 0:
            return None, None
        result, _ = self.ocr(roi)
        texts = []
        for r in (result or []):
            text = str(r[1]).strip()
            if text:
                texts.append(text)
        if texts and log:
            self._log("OCR 识别(顶部区域): {}".format(texts))
        map_name = None
        coord = None
        for text in texts:
            m = re.search(r"[(（]\s*(\d{1,4})\s*[,，]\s*(\d{1,4})\s*[)）]", text)
            if m:
                coord = (int(m.group(1)), int(m.group(2)))
            elif re.search(r"[一-鿿]{2,}", text) and not text.startswith("("):
                map_name = text
        return map_name, coord

    def _save_debug_frame(self, tag, frame=None):
        """保存诊断截图到 logs/loyalty_debug/，便于核对坐标输入/地图面板位置。"""
        try:
            if frame is None:
                frame = self.get_frame()
            if frame is None:
                return
            d = os.path.join(SCRIPT_DIR, "logs", "loyalty_debug")
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, "{}_{}_{}.png".format(
                self.serial, datetime.now().strftime("%H%M%S"), tag))
            cv2.imencode(".png", frame)[1].tofile(path)
            self._log("  诊断截图已保存: {}".format(path))
        except Exception as e:
            self._log("  诊断截图保存失败: {}".format(e))

    def _retry_coord_input(self, steps):
        """重新执行坐标输入步骤（打开地图 → 点输入框 → 点数字键盘）。"""
        for s in steps:
            if self._stop_event and self._stop_event.is_set():
                return False
            action = s["action"]
            wait = s.get("wait", 0.3)
            if action == "click_template":
                frame = self.get_frame()
                btn = self.find(frame, s["name"], threshold=s.get("threshold", 0.75)) if frame is not None else None
                if btn is None:
                    self._log("  [重试] 未找到 {}，跳过该步".format(s["name"]))
                else:
                    self._log("  [重试] click {} ({},{})".format(s["name"], btn[0], btn[1]))
                    self.tap(btn[0], btn[1])
            elif action == "click_position":
                self._log("  [重试] click position ({},{})".format(s["x"], s["y"]))
                self.tap(s["x"], s["y"])
            elif action == "click_sequence":
                self._log("  [重试] click_sequence {} points".format(len(s["positions"])))
                for px, py in s["positions"]:
                    self.tap(px, py)
                    time.sleep(s.get("interval", 0.1))
            time.sleep(wait)
        return True

    def connect(self):

        # 验证 ADB
        try:
            r = sp.run([_ADB_EXE, "-s", self.serial, "shell", "echo", "ok"],
                       capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW)
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
                       capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW)
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
                # 坐标: (x, y) 或 (x.y)
                m = re.search(r'[(（]\s*(\d{1,4})\s*[,，.]\s*(\d{1,4})\s*[)）]', text)
                if m:
                    coord = (int(m.group(1)), int(m.group(2)))
                # 地图名: 包含中文且不是纯数字坐标
                elif re.search(r'[一-鿿]{2,}', text) and not text.startswith('('):
                    map_name = text
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

        # 自动 OCR 识别当前地图
        map_name = None
        self._init_ocr()
        for _ in range(5):
            detected_map, _ = self.detect_map(frame)
            if detected_map:
                map_name = detected_map
                self.last_map_name = map_name
                self._log(f"OCR 识别到地图: {map_name}")
                break
            time.sleep(0.5)
            frame = self.get_frame()

        if not map_name:
            self._log("未识别到地图，跳过")
            return

        config = SCENE_RECOVERY.get(map_name)

        if config is None:
            self._log(f"当前场景 [{map_name}] 未配置忠诚度恢复流程，跳过")
            return

        self._log(f"执行 [{map_name}] 完整流程...")

        steps = build_steps(config)
        for i, step in enumerate(steps, 1):
            if self._stop_event and self._stop_event.is_set():
                self._log("[{}] 收到停止信号，退出".format(i))
                return
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
                       capture_output=True, timeout=3, creationflags=CREATE_NO_WINDOW)
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

            elif action == "debug_shot":
                tag = step.get("tag", "shot")
                self._save_debug_frame(tag)
                time.sleep(wait)

            elif action == "wait_coord":
                self._init_ocr()
                target_map = step["target_map"]
                target_x = step["target_x"]
                target_y = step["target_y"]
                tolerance = step.get("tolerance", 3)
                timeout = step.get("timeout", 120)
                stable_time = step.get("stable_time", 1.5)
                clicks = step.get("clicks", [])
                retry_inputs = step.get("retry_inputs", [])
                max_retries = step.get("max_retries", 2)
                stall_timeout = step.get("stall_timeout", 5)   # 坐标超过 N 秒没变 = 卡住
                stall_grace = step.get("stall_grace", 8)       # 每轮输入后先给 N 秒起步时间
                self._log("[{}] 等待坐标: {} ({},{})".format(i, target_map, target_x, target_y))
                self._save_debug_frame("wait_coord_start_{}_{}".format(target_x, target_y))
                reached = False
                last_coord = None
                last_stable_t = 0
                last_log_t = 0
                for retry_round in range(max_retries + 1):
                    if self._stop_event and self._stop_event.is_set():
                        self._log(f"[{i}] 收到停止信号，退出等待坐标")
                        return
                    round_start = time.time()
                    last_read_coord = None
                    last_move_t = None
                    while time.time() - round_start < timeout:
                        if self._stop_event and self._stop_event.is_set():
                            self._log(f"[{i}] 收到停止信号，退出等待坐标")
                            return
                        frame = self.get_frame()
                        if frame is None:
                            time.sleep(0.3)
                            continue
                        map_name, coord = self._ocr_coord(frame, log=False)
                        now = time.time()
                        on_target = False
                        if map_name and target_map in map_name and coord:
                            dx = abs(coord[0] - target_x)
                            dy = abs(coord[1] - target_y)
                            on_target = dx <= tolerance and dy <= tolerance
                            if on_target:
                                if last_coord is None:
                                    last_coord = coord
                                    last_stable_t = now
                                    self._log("[{}] 首次进入目标区域: {} ({},{})".format(i, map_name, coord[0], coord[1]))
                                elif coord == last_coord:
                                    if now - last_stable_t >= stable_time:
                                        self._log("[{}] 坐标已稳定: {} ({},{})".format(i, map_name, coord[0], coord[1]))
                                        reached = True
                                        break
                                else:
                                    last_coord = coord
                                    last_stable_t = now
                            else:
                                last_coord = None
                        # 移动检测：坐标变化即刷新最近移动时间
                        if coord:
                            if coord != last_read_coord:
                                last_read_coord = coord
                                last_move_t = now
                            elif last_move_t is None:
                                last_move_t = now
                        # 卡住检测：非目标位置、已过起步宽限、坐标超过 stall_timeout 没变
                        stalled = (not on_target and last_read_coord is not None
                                   and (now - round_start) > stall_grace
                                   and last_move_t is not None
                                   and (now - last_move_t) >= stall_timeout)
                        if stalled:
                            self._log("[{}] 角色超过 {}s 未移动（当前 {}），提前重试坐标输入".format(
                                i, stall_timeout, last_read_coord))
                            break
                        # 进度日志：每 15 秒一次，避免 OCR 刷屏
                        if now - last_log_t >= 15:
                            last_log_t = now
                            dist = ""
                            if coord:
                                dist = "距离 ({},{})".format(
                                    abs(coord[0] - target_x), abs(coord[1] - target_y))
                            self._log("[{}] 等待中... 当前 {} {} {}".format(
                                i, map_name or "?", coord or "?", dist))
                        time.sleep(0.3)
                    if reached:
                        break
                    if retry_round < max_retries and retry_inputs:
                        self._log(f"[{i}] 坐标未到达，重试输入坐标（第 {retry_round + 1}/{max_retries} 次）")
                        self._save_debug_frame("retry_input_{}".format(retry_round + 1))
                        ok = self._retry_coord_input(retry_inputs)
                        self._save_debug_frame("retry_input_{}_done".format(retry_round + 1))
                        if not ok:
                            break
                        last_coord = None
                        last_stable_t = 0
                    else:
                        break
                if reached:
                    self._log("[{}] 已到达目标坐标: {} ({},{})".format(i, target_map, target_x, target_y))
                    self._log("[{}] 依次点击 {} 个位置: {}".format(i, len(clicks), clicks))
                    for idx_c, (px, py) in enumerate(clicks):
                        if self._stop_event and self._stop_event.is_set():
                            self._log(f"[{i}] 收到停止信号，中断点击")
                            return
                        self._log("[{}]   点击 [{}/{}] ({},{})".format(i, idx_c+1, len(clicks), px, py))
                        self.tap(px, py)
                        time.sleep(0.2)
                else:
                    self._log("[{}] 等待坐标超时，跳过".format(i))
                time.sleep(wait)

            elif action == "layer_teleport":
                # 层间传送回上层场景（如龙窟三层→四层→五层），复用场景切换引擎的洞穴传送
                legs = step.get("legs", [])
                self._log("[{}] 层间传送: {}".format(i, " -> ".join("{}→{}".format(a, b) for a, b in legs)))
                from 场景切换 import SceneSwitcher
                switcher = SceneSwitcher(self.serial)
                switcher.connect()
                ok = True
                for src, dst in legs:
                    if self._stop_event and self._stop_event.is_set():
                        self._log(f"[{i}] 收到停止信号，退出层间传送")
                        return
                    if not switcher._walk_leg(src, dst):
                        self._log("[{}] 层间传送失败: {} -> {}".format(i, src, dst))
                        ok = False
                        break
                if ok:
                    self._log("[{}] 层间传送完成，回到 {}".format(i, legs[-1][1]))
                time.sleep(wait)
                frame = self.get_frame()
                if frame is not None:
                    m, _ = self._ocr_coord(frame, log=False)
                    if m:
                        self.last_map_name = m

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



def run_loyalty_recovery(serial, map_name="", stop_event=None, client=None):
    """独立运行忠诚度恢复流程。client可选复用已有scrcpy连接。stop_event可选用于外部停止。"""
    print(f"device: {serial}")
    if map_name:
        print(f"map: {map_name}")
    print("=" * 50)
    engine = ToolEngine(serial)
    if stop_event:
        engine._stop_event = stop_event
    if client is not None:
        engine.client = client
        f = client.last_frame
        if f is not None:
            h, w = f.shape[:2]
            device_w, device_h = 0, 0
            try:
                import re
                r = sp.run([_ADB_EXE, "-s", serial, "shell", "wm", "size"],
                           capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW)
                m = re.search(r"(\d+)x(\d+)", r.stdout)
                if m:
                    device_w, device_h = int(m.group(1)), int(m.group(2))
            except Exception:
                pass
            if h > w:
                engine.stream_w = h
                engine.stream_h = w
                if device_h > device_w:
                    device_w, device_h = device_h, device_w
            else:
                engine.stream_w = w
                engine.stream_h = h
                if device_h > device_w:
                    device_w, device_h = device_h, device_w
            if device_w and device_h:
                engine.scale_x = device_w / engine.stream_w
                engine.scale_y = device_h / engine.stream_h
            else:
                engine.scale_x = engine.scale_y = 1.0
            engine._log("复用连接: stream={}x{} scale={:.3f}x{:.3f}".format(
                engine.stream_w, engine.stream_h,
                engine.scale_x, engine.scale_y))
            engine.init_ocr()
        else:
            engine._log("共享client无帧，fallback独立连接")
            if not engine.connect():
                print("connect failed")
                return
    else:
        if not engine.connect():
            print("connect failed")
            return
    if map_name:
        engine.cfg["map"] = map_name
    engine._log("connected, start loyalty recovery...")
    engine.loyalty_recovery()
    if client is None:
        engine.disconnect()

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
