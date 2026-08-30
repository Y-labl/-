# -*- coding: utf-8 -*-
"""
场景切换工具：传入设备号 + 目标场景，自动执行

    关闭背包(如开着) → 打开道具 → 点击飞行符(选中) → 点击使用
    → 目的地面板弹出 → 点击目标场景模板 → 关闭背包

    支持跑图路线（小西天/小雷音寺/龙窟五层/凤巢五层/女娲神迹）：
    飞行到起点 → 使用摄妖香(防遇怪) → 按路线逐段跑图 → 到达后使用洞冥草。
    跑图方式（坐标制，参考小霸王项目反编译 map_action）：
      - 走位：打开小地图 → 按“地图坐标→屏幕坐标”换算点击 → 前往 → 关图 → 等到达
      - 传送：走到传送点后点击“传送”按钮
      - NPC：走到 NPC 坐标 → 点击 NPC → 点“是的我要去”

用法:
    python 场景切换.py <设备号> <场景/模板名> [选项]
    不传设备号默认 DEFAULT_SERIAL；不传场景默认 DEFAULT_TEMPLATE。
"""

import argparse
import math
import os
import random
import re
import subprocess as sp
import sys
import time
from datetime import datetime

import cv2
import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(SCRIPT_DIR, "image")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")

STREAM_W = 800   # 项目模板基准宽度
STREAM_H = 448   # 项目模板基准高度

# ADB 可执行路径：优先项目虚拟环境自带，其次 adbutils，最后系统 PATH
_ADB_EXE = os.path.join(SCRIPT_DIR, ".venv", "Lib", "site-packages", "adbutils", "binaries", "adb.exe")
if not os.path.exists(_ADB_EXE):
    try:
        import adbutils
        _ADB_EXE = adbutils.adb_path()
    except Exception:
        _ADB_EXE = "adb"

ADB_EXE = _ADB_EXE
CREATE_NO_WINDOW = getattr(sp, "CREATE_NO_WINDOW", 0)


# ======================== 默认参数 ========================
DEFAULT_SERIAL = "WEENU18A18102828"
DEFAULT_TEMPLATE = "傲来国"

# ======================== 场景快捷名 → 飞行符模板 ========================
SCENE_SHORTCUTS = {
    "傲来": "飞行符飞傲来国",
    "傲来国": "飞行符飞傲来国",
    "宝象国": "飞行符飞宝象国",
    "建邺城": "飞行符飞建邺城",
    "朱紫国": "飞行符飞朱紫国",
    "西梁女国": "飞行符飞西梁女国",
    "长安城": "飞行符飞长安城",
    "长寿村": "飞行符飞长寿村",
}

# ======================== 场景跑动路线 ========================
# 每个场景: [飞行目的地, 途经地图...]
SCENE_ROUTES = {
    "小西天": ["朱紫国", "大唐境外", "小西天"],
    "小雷音寺": ["朱紫国", "大唐境外", "小西天", "小雷音寺"],
    "龙窟五层": ["傲来国", "花果山", "北俱芦洲", "龙窟一层", "龙窟二层", "龙窟三层", "龙窟四层", "龙窟五层"],
    "凤巢五层": ["傲来国", "花果山", "北俱芦洲", "凤巢一层", "凤巢二层", "凤巢三层", "凤巢四层", "凤巢五层"],
    "女娲神迹": ["傲来国", "花果山", "北俱芦洲", "女娲神迹"],
    "子母河底": ["西梁女国", "子母河底"],
}

# 不需要摄妖香/洞冥草的场景：跑图途中不遇低级怪，飞行后直接走位到达即可
# （其他场景统一在飞行后吃摄妖香、到达后吃洞冥草）
NO_BUFF_SCENES = {"子母河底"}

# 小地图面板参数（来自小霸王项目反编译）: 地图名 -> (左下点, xy范围, xy宽高)
# 地图坐标→小地图点击: clickX = lb.x + x*wh.x/range.x; clickY = lb.y - y*wh.y/range.y
MAP_PARAMS = {
    "傲来国": ((123, 366), (223, 150), (440, 295)),
    "花果山": ((148, 366), (159, 119), (390, 293)),
    "北俱芦洲": ((145, 367), (227, 169), (394, 297)),
    "朱紫国": ((102, 370), (191, 119), (482, 302)),
    "大唐境外": ((78, 284), (639, 118), (641, 120)),
    "龙窟一层": ((70, 374), (164, 91), (541, 301)),
    "龙窟五层": ((71, 358), (139, 71), (543, 279)),
    "龙窟六层": ((73, 374), (137, 79), (539, 310)),
    "凤巢三层": ((126, 340), (127, 71), (434, 243)),
    "凤巢四层": ((126, 340), (127, 71), (434, 243)),
    "小西天": ((210, 417), (159, 239), (266, 397)),
    "小雷音寺": ((92, 406), (191, 143), (501, 375)),
    "女娲神迹": ((145, 366), (191, 143), (394, 295)),
    "长安城": ((53, 365), (549, 279), (578, 292)),
    "长寿村": ((226, 370), (159, 209), (233, 303)),
    "长寿郊外": ((175, 365), (191, 167), (335, 292)),
    "大唐国境": ((153, 399), (351, 335), (380, 360)),
    "江南野外": ((189, 332), (159, 119), (308, 227)),
    "西梁女国": ((149, 364), (163, 123), (387, 290)),
    "宝象国": ((158, 357), (159, 119), (370, 276)),
}

# 跨图腿: (起点, 终点) -> (走位地图, 目标坐标, 方式)
# 方式: "chuan_song"=走位后点传送; "npc"=走位后点NPC; "cave"=打开地图点标签坐标后等传送图标点传送
LEG_STEPS = {
    ("傲来国", "花果山"): ("傲来国", (566, 82), "cave"),
    ("花果山", "北俱芦洲"): ("花果山", (28, 98), "npc"),
    # 第4元素（可选）：传送光圈兜底坐标——点传送模板没反应且图标消失时点光圈进洞
    ("北俱芦洲", "龙窟一层"): ("北俱芦洲", (164, 215), "cave", (141, 227)),
    ("北俱芦洲", "凤巢一层"): ("北俱芦洲", (285, 102), "cave"),
    ("朱紫国", "大唐境外"): ("朱紫国", (4, 4), "chuan_song"),
    # 洞穴层间：小地图标签点击位置（流坐标）
    ("龙窟一层", "龙窟二层"): ("龙窟一层", (110, 129), "cave", (163, 204)),
    ("龙窟二层", "龙窟三层"): ("龙窟二层", (146, 336), "cave", (303, 374)),
    ("龙窟三层", "龙窟四层"): ("龙窟三层", (583, 282), "cave", (618, 249)),
    ("龙窟四层", "龙窟五层"): ("龙窟四层", (526, 224), "cave", (465, 184)),
    ("凤巢一层", "凤巢二层"): ("凤巢一层", (281, 321), "cave"),
    ("凤巢二层", "凤巢三层"): ("凤巢二层", (548, 185), "cave"),
    ("凤巢三层", "凤巢四层"): ("凤巢三层", (543, 322), "cave"),
    ("凤巢四层", "凤巢五层"): ("凤巢四层", (381, 109), "cave"),
    # 回程（下层）
    ("龙窟五层", "龙窟四层"): ("龙窟五层", (538, 119), "cave"),
    ("龙窟四层", "龙窟三层"): ("龙窟四层", (88, 327), "cave"),
    ("凤巢五层", "凤巢四层"): ("凤巢五层", (386, 318), "cave"),
    ("凤巢四层", "凤巢三层"): ("凤巢四层", (167, 132), "cave"),
    # 子母河底：西梁女国走位到 (152,12) 点传送
    ("西梁女国", "子母河底"): ("西梁女国", (152, 12), "chuan_song"),
    # 小雷音寺：小西天走位到 (26,218) 点传送
    ("小西天", "小雷音寺"): ("小西天", (26, 218), "chuan_song"),
}

# NPC 对话式传送（点 NPC -> 出现确认对话框 -> 点确认 -> 等地图变化）
# 与 LEG_NPCS 不同：确认按钮直接是"送我到XX"对话框本身（OCR 文本/模板均可点）
LEG_NPCS2 = {
    ("大唐境外", "小西天"): ((16, 106), "点NPC对话-快送我进去吧", "点NPC对话-快送我进去吧"),
    ("北俱芦洲", "女娲神迹"): ((14, 156), "点NPC对话-请送我进去", "点NPC对话-请送我进去"),
}

# NPC 传送: (起点, 终点) -> (NPC地图坐标, NPC模板, 确认按钮模板)
LEG_NPCS = {
    ("花果山", "北俱芦洲"): ((28, 98), "点NPC重叠-花果山土地", "点NPC对话-是的我要去"),
}

# NPC 对话确认按钮 OCR 区域（流坐标，对应设备 1419-1658,489-527）
NPC_CONFIRM_ROI = (580, 195, 710, 230)

# 点击某按钮时的备选模板
FALLBACK_NAMES = {
    "道具": ["道具-道具栏"],
    # 旧"关闭弹窗"模板在大地图界面会匹配错位（命中 X 按钮右侧的其他元素），
    # 新模板从大地图实测截图裁剪，精确命中右上角 X
    "关闭弹窗": ["关闭弹窗2"],
}

# 模板匹配中心到按钮可点击中心的偏移（流坐标，y 向下为正）
CLICK_OFFSETS = {
    "道具": (0, 17),
}

# 固定 UI 元素直接点击位置（800x448 流坐标）：底部栏“道具”按钮
FIXED_CLICKS = {
    "道具": (703, 420),
}

# OCR 区域（流坐标）
BAG_ROI = (333, 25, 425, 54)
BAG_CLOSE_ROI = (600, 15, 800, 70)
MAP_ROI = (62, 10, 133, 39)
MAP_GO_ROI = (580, 150, 700, 230)
MAP_LABEL_ROI = (42, 62, 646, 373)

MAP_GO_BTN = (625, 186)
MAP_TRANSFER_BTN = (596, 309)
BAG_CLOSE_FALLBACK = (668, 38)
CAVE_GUANGQUAN = (586, 260)   # 洞穴传送光圈（流坐标，实测 1406,626 设备）
CHUANSONG_NEAR_POINT = (120, 410)   # 点传送后未触发时，点屏幕左下角让角色靠近传送口
                                     #（朱紫国→大唐境外等传送口在地图左下方，角色走到附近差几步时补点一下）

# 传送按钮出现区域（流坐标，实测 西梁女国→子母河底 在 (596,310)、洞穴传送光圈在 (586,260)）：
# 只裁屏幕中下部，排除顶部小地图/坐标/任务文字——旧版全帧 800x448 OCR 每轮 2~4s 且
# "传送"小字常漏读，是"点小地图关图 → 点击传送"空耗 ~34s 的根因
TRANSFER_BTN_ROI = (250, 180, 800, 430)
TRANSFER_BTN_WAIT = 30.0   # 等传送按钮出现的最大时长（覆盖角色走路到传送口的时间）


def resolve_template(name):
    """把场景快捷名/模板名/图片路径解析为实际模板名。"""
    n = str(name).strip()
    if n in SCENE_SHORTCUTS:
        return SCENE_SHORTCUTS[n]
    return n


def resolve_route(target_name):
    """解析目标场景的完整路线；途经点返回前缀路线；其他返回 None。"""
    n = str(target_name).strip()
    if n in SCENE_ROUTES:
        return SCENE_ROUTES[n]
    for route in SCENE_ROUTES.values():
        if n in route:
            idx = route.index(n)
            if idx > 0:
                return route[:idx + 1]
    return None


# ======================== 图片与模板 ========================

def imread_unicode(path, flags=cv2.IMREAD_COLOR):
    arr = np.fromfile(path, dtype=np.uint8)
    if arr.size == 0:
        return None
    return cv2.imdecode(arr, flags)


def load_template(name):
    """按项目规则加载模板：image/ 与 images/ 目录，后缀 点卡服/畅玩服/空。"""
    if os.path.sep in name or "/" in name or name.lower().endswith((".png", ".bmp", ".jpg")):
        path = name if os.path.isabs(name) else os.path.join(SCRIPT_DIR, name)
        if os.path.exists(path):
            return imread_unicode(path)
        return None
    for d in [IMAGE_DIR, IMAGES_DIR]:
        for ext in [".png", ".bmp", ".jpg"]:
            for suffix in ["点卡服", "畅玩服", ""]:
                path = os.path.join(d, f"{name}{suffix}{ext}")
                if os.path.exists(path):
                    img = imread_unicode(path)
                    if img is not None:
                        return img
    return None


def match_template(screenshot, template, threshold=0.75, debug_name=""):
    """多尺度模板匹配，返回 (中心x, 中心y, 置信度) 或 None。
    性能优化：同分辨率设备（模板与截图都是 800x448 流坐标）绝大多数情况
    1.0 尺度单方法即可命中（约 0.04s），先试 1.0；未命中才扩展多尺度，
    避免每次点击都付出 13 尺度 ≈ 1.2s 的全量匹配成本。"""
    if screenshot is None or template is None:
        return None
    h, w = screenshot.shape[:2]
    tw, th = template.shape[1], template.shape[0]
    if h < th or w < tw:
        return None
    # 快路径：1.0 尺度 TM_CCOEFF_NORMED
    r1 = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, v1, _, loc1 = cv2.minMaxLoc(r1)
    if v1 >= threshold:
        return (loc1[0] + tw // 2, loc1[1] + th // 2, v1)
    # 慢路径：只保留 TM_CCOEFF_NORMED。TM_CCORR_NORMED 在主界面高亮区域
    # 会产生 0.90+ 的大面积假命中，导致“地图-筛选/关闭弹窗”位置乱跳。
    best_result = None
    best_val = v1
    scales = [round(x, 2) for x in np.arange(0.7, 1.35, 0.05)]
    for s in scales:
        stw = max(2, int(tw * s))
        sth = max(2, int(th * s))
        if stw > w or sth > h:
            continue
        if abs(s - 1.0) < 0.01:
            result = r1
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
        else:
            small_tmpl = cv2.resize(template, (stw, sth), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(screenshot, small_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best_val:
            best_val = max_val
            best_result = (max_loc[0] + stw // 2, max_loc[1] + sth // 2, max_val)
    if best_result is not None and best_val >= threshold:
        return best_result
    if debug_name:
        print(f"[DEBUG] {debug_name}: best={best_val:.3f} (threshold={threshold})")
    return None


# ======================== ADB ========================

def list_adb_devices():
    try:
        r = sp.run([ADB_EXE, "devices"], capture_output=True, text=True, timeout=5,
                   creationflags=CREATE_NO_WINDOW)
        lines = r.stdout.strip().split("\n")[1:]
        return [l.split("\t")[0] for l in lines if "\tdevice" in l]
    except Exception:
        return []


def adb_tap(serial, x, y):
    sp.run([ADB_EXE, "-s", serial, "shell", "input", "tap", str(int(x)), str(int(y))],
           capture_output=True, timeout=3, creationflags=CREATE_NO_WINDOW)


def adb_screencap(serial):
    r = sp.run([ADB_EXE, "-s", serial, "exec-out", "screencap", "-p"],
               capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
    if r.returncode != 0 or not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)


# ======================== 场景切换引擎 ========================

class SceneSwitchCombatAbort(Exception):
    """切场过程中检测到进入战斗：中止切换，交由上层战斗流程处理。"""


class SceneSwitcher:
    def __init__(self, serial, threshold=0.75, retries=3, wait=0.8, debug=False, log_fn=None,
                 combat_check=None, client=None, frame_lock=None):
        self.serial = serial
        self.threshold = threshold
        self.retries = retries
        self.wait = wait
        self.debug = debug
        self.log_fn = log_fn   # 可选：外部日志回调（引擎/测试页回灌用）
        self.combat_check = combat_check  # 可选：外部战斗检测回调，返回 True=战斗中
        self.client = client             # 可选：复用引擎 scrcpy 流帧（免 ADB 截图，性能优化）
        self.frame_lock = frame_lock     # 可选：引擎的帧锁（访问 client.last_frame 时加锁）
        self._last_combat_check_t = 0.0
        self.device_w = 0
        self.device_h = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.templates = {}
        self.ocr = None
        self._ocr_warned = False
        self._orient_fixed = False
        self._load_templates()

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        if self.log_fn is not None:
            try:
                self.log_fn(f"[{ts}] {msg}")
                return
            except Exception:
                pass
        print(f"[{ts}] {msg}")

    def _in_combat(self, force=False):
        """调用外部战斗检测回调（带 1 秒节流，避免高频截图/模板匹配）。"""
        if not self.combat_check:
            return False
        now = time.time()
        if not force and now - self._last_combat_check_t < 1.0:
            return False
        self._last_combat_check_t = now
        try:
            return bool(self.combat_check())
        except Exception:
            return False

    def _abort_if_combat(self, force=False):
        """检测到战斗立即抛出 SceneSwitchCombatAbort，中止当前切场流程。"""
        if self._in_combat(force=force):
            self._log("  ⚔️ 检测到进入战斗，中止场景切换")
            raise SceneSwitchCombatAbort()

    def _load_templates(self, target_name=None):
        names = ["道具", "道具-道具栏", "飞行符", "使用", "关闭弹窗", "打开地图",
                 "摄妖香", "洞冥草",
                 "点NPC重叠-花果山土地", "点NPC对话-是的我要去", "点NPC对话-确认"]
        if target_name:
            names.append(target_name)
        for name in names:
            if name in self.templates:
                continue
            tmpl = load_template(name)
            if tmpl is not None:
                self.templates[name] = tmpl
                h, w = tmpl.shape[:2]
                self._log(f"  模板 [OK] {name} ({w}x{h})")
            else:
                self._log(f"  模板 [WARN] 未找到: {name}")

    def _init_ocr(self):
        if self.ocr is not None:
            return
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr = RapidOCR()
            self.ocr(np.zeros((64, 64, 3), dtype=np.uint8))
            self._log("RapidOCR 初始化完成")
        except Exception as e:
            if not self._ocr_warned:
                self._log(f"[WARN] RapidOCR 不可用({e})，状态校验降级为跳过")
                self._ocr_warned = True

    def _ocr_has(self, roi, keywords, min_count=1, timeout=3.0):
        """OCR 指定区域，判断是否命中足够多的关键字。OCR 不可用时直接放行。"""
        if self.ocr is None:
            self._init_ocr()
            if self.ocr is None:
                return True
        x1, y1, x2, y2 = roi
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = self.get_frame()
            if frame is not None and frame.shape[0] >= y2 and frame.shape[1] >= x2:
                crop = frame[y1:y2, x1:x2]
                if crop.size:
                    for _ in range(2):
                        try:
                            res, _ = self.ocr(crop)
                            texts = " ".join(str(r[1]) for r in (res or []))
                            hits = sum(1 for k in keywords if k in texts)
                            if hits >= min_count:
                                return True
                        except Exception:
                            pass
            time.sleep(0.6)  # OCR 轮询节流：减少每轮截图次数（截图约1.5s/次）
        return False

    def connect(self):
        try:
            r = sp.run([ADB_EXE, "-s", self.serial, "shell", "echo", "ok"],
                       capture_output=True, text=True, timeout=5,
                       creationflags=CREATE_NO_WINDOW)
            if r.returncode != 0 or r.stdout.strip() != "ok":
                self._log(f"ADB 连接失败: {r.stderr.strip() or r.stdout.strip()}")
                return False
        except Exception as e:
            self._log(f"ADB 异常: {e}")
            return False
        self._log(f"ADB 连接正常: {self.serial}")
        try:
            r = sp.run([ADB_EXE, "-s", self.serial, "shell", "wm", "size"],
                       capture_output=True, text=True, timeout=5,
                       creationflags=CREATE_NO_WINDOW)
            m = re.search(r"(\d+)x(\d+)", r.stdout)
            if m:
                self.device_w, self.device_h = int(m.group(1)), int(m.group(2))
                self._log(f"设备分辨率: {self.device_w}x{self.device_h}")
        except Exception:
            self._log("无法获取设备分辨率，按 1:1 处理")
        return True

    def get_frame(self):
        # 优先复用引擎 scrcpy 流帧（几乎零成本，免 ADB 截图 1.5s/次）；
        # 未传 client 或流无帧时回退 ADB 截图
        if self.client is not None:
            try:
                if self.frame_lock is not None:
                    with self.frame_lock:
                        frame = self.client.last_frame
                        frame = frame.copy() if frame is not None else None
                else:
                    frame = self.client.last_frame
                    frame = frame.copy() if frame is not None else None
            except Exception:
                frame = None
            if frame is None:
                frame = adb_screencap(self.serial)
        else:
            frame = adb_screencap(self.serial)
        if frame is None:
            return None
        fh, fw = frame.shape[:2]
        if fh > fw:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            fh, fw = frame.shape[:2]
            if self.device_h > self.device_w:
                self.device_w, self.device_h = self.device_h, self.device_w
        if (fw, fh) != (STREAM_W, STREAM_H):
            frame = cv2.resize(frame, (STREAM_W, STREAM_H), interpolation=cv2.INTER_LINEAR)
        if self.device_w and self.device_h:
            if fw > fh and self.device_h > self.device_w:
                self.device_w, self.device_h = self.device_h, self.device_w
                if not self._orient_fixed:
                    self._log(f"屏幕方向修正: {self.device_w}x{self.device_h}")
                    self._orient_fixed = True
            self.scale_x = self.device_w / STREAM_W
            self.scale_y = self.device_h / STREAM_H
        return frame

    def tap(self, x, y, offset=True):
        tx, ty = x, y
        if offset:
            tx += random.randint(-3, 3)
            ty += random.randint(-3, 3)
        adb_tap(self.serial, tx * self.scale_x, ty * self.scale_y)

    def find(self, frame, name, threshold=None, roi=None):
        thr = threshold if threshold is not None else self.threshold
        candidates = [name] + FALLBACK_NAMES.get(name, [])
        for cand in candidates:
            tmpl = self.templates.get(cand)
            if tmpl is None:
                tmpl = load_template(cand)
            if tmpl is None:
                continue
            if roi is not None:
                x1, y1, x2, y2 = roi
                sub = frame[y1:y2, x1:x2]
                r = match_template(sub, tmpl, threshold=thr, debug_name=cand if self.debug else "")
                if r is not None:
                    return cand, (r[0] + x1, r[1] + y1, r[2])
            else:
                r = match_template(frame, tmpl, threshold=thr, debug_name=cand if self.debug else "")
                if r is not None:
                    return cand, r
        return None, None

    def _save_debug(self, frame, tag):
        if not self.debug:
            return
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR,
                            f"scene_switch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{tag}.png")
        cv2.imencode(".png", frame)[1].tofile(path)
        self._log(f"  已保存调试截图: {path}")

    def click_template(self, name, threshold=None, roi=None):
        """查找模板并点击；未找到时重试。点击后等待 0.4s。"""
        thr = threshold if threshold is not None else self.threshold
        for attempt in range(1, self.retries + 1):
            frame = self.get_frame()
            if frame is None:
                self._log(f"[{name}] 第 {attempt}/{self.retries} 次：截图失败")
                time.sleep(0.4)
                continue
            found, r = self.find(frame, name, threshold=thr, roi=roi)
            if not found:
                self._log(f"[{name}] 第 {attempt}/{self.retries} 次：未找到")
                self._save_debug(frame, f"no_{name.replace('-', '_')}")
                time.sleep(0.5)
                continue
            ox, oy = CLICK_OFFSETS.get(name, (0, 0))
            tx, ty = r[0] + ox, r[1] + oy
            self._log(f"[{name}] 点击 ({tx}, {ty}) 置信度 {r[2]:.2f}")
            self.tap(tx, ty)
            time.sleep(0.4)
            return True
        return False

    def click_fixed(self, name):
        pos = FIXED_CLICKS.get(name)
        if pos is None:
            self._log(f"[{name}] 未配置固定坐标")
            return False
        self._log(f"[{name}] 固定坐标点击 ({pos[0]}, {pos[1]})")
        self.tap(pos[0], pos[1])
        time.sleep(0.4)
        return True

    def _open_bag(self):
        if self._ocr_has(BAG_ROI, ["行囊"], timeout=1.5):
            self._log("背包已打开，跳过")
            return True
        if self.click_fixed("道具"):
            return True
        self._log("固定坐标未生效，尝试模板匹配")
        return self.click_template("道具")

    def _close_bag_if_open(self):
        if not self._ocr_has(BAG_ROI, ["行囊"], timeout=1.5):
            self._log("背包未打开，跳过关闭")
            return True
        self._log("背包已打开，使用关闭按钮关闭")
        for attempt in range(1, self.retries + 1):
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.4)
                continue
            found, r = self.find(frame, "关闭弹窗", threshold=0.75, roi=BAG_CLOSE_ROI)
            if found:
                self._log(f"  关闭按钮 ({r[0]}, {r[1]}) 置信度 {r[2]:.2f}")
                self.tap(r[0], r[1])
            else:
                fx, fy = BAG_CLOSE_FALLBACK
                self._log(f"  头部未匹配到关闭按钮，回退点击 ({fx}, {fy})")
                self.tap(fx, fy)
            time.sleep(0.5)
            if not self._ocr_has(BAG_ROI, ["行囊"], timeout=1.5):
                self._log("背包已关闭")
                return True
        self._log("[WARN] 背包关闭失败")
        return False

    def _close_bag_fast(self):
        """快速关闭背包：直接点关闭按钮，不做 OCR 校验（节省时间）。"""
        frame = self.get_frame()
        if frame is not None:
            found, r = self.find(frame, "关闭弹窗", threshold=0.8, roi=BAG_CLOSE_ROI)
            if found:
                self._log(f"  关闭背包 ({r[0]}, {r[1]})")
                self.tap(r[0], r[1])
                time.sleep(0.3)
                return
        self._log("  背包关闭按钮兜底 (668,38)")
        self.tap(BAG_CLOSE_FALLBACK[0], BAG_CLOSE_FALLBACK[1])
        time.sleep(0.3)

    # ---------- OCR 查找 ----------

    def _ocr_find(self, roi, keyword, timeout=5.0, check_combat=False):
        """在指定流坐标区域 OCR 查找关键字，返回 (x, y, 文本) 或 None。
        keyword 可为 str 或 list/tuple（按优先级顺序逐个匹配，命中即返回）。"""
        if self.ocr is None:
            self._init_ocr()
            if self.ocr is None:
                return None
        kws = keyword if isinstance(keyword, (list, tuple)) else [keyword]
        x1, y1, x2, y2 = roi
        deadline = time.time() + timeout
        while time.time() < deadline:
            if check_combat:
                self._abort_if_combat()
            frame = self.get_frame()
            if frame is not None and frame.shape[0] >= y2 and frame.shape[1] >= x2:
                crop = frame[y1:y2, x1:x2]
                if crop.size:
                    try:
                        res, _ = self.ocr(crop)
                        for box, text, conf in (res or []):
                            t = str(text)
                            for k in kws:
                                if k in t:
                                    bx = [p[0] for p in box]
                                    by = [p[1] for p in box]
                                    cx = (min(bx) + max(bx)) // 2 + x1
                                    cy = (min(by) + max(by)) // 2 + y1
                                    return (cx, cy, t)
                    except Exception:
                        pass
            time.sleep(0.2)  # OCR 轮询节流（截图约1.5s/次时开销在截图，节流取小值）
        return None

    def _open_minimap(self):
        """必须先点击“打开地图”，再验证地图是否真的打开。
        即使上次可能已开着，也不先用“地图-筛选”跳过点击。"""
        self._log("先点击打开地图（打开地图点卡服.png）")
        clicked = self.click_template("打开地图")
        if not clicked:
            self._log("  未点击到打开地图按钮；再确认地图是否已打开")
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if self._is_minimap_open():
                return True
            time.sleep(0.2)
        self._log("  ⚠️ 已点击打开地图，但未确认到地图-筛选；不盲点地图坐标")
        return False

    def _is_minimap_open(self):
        """小地图开着时，画面上必须有"地图-筛选"按钮。
        不再使用“前往”OCR兜底：主界面/其他弹窗误报“前往”会导致地图未开就点坐标。"""
        frame = self.get_frame()
        if frame is None:
            return False
        # 限定在小地图区域（屏幕右侧）找"地图-筛选"，避免主界面其他图标误匹配
        found, r = self.find(frame, "地图-筛选", threshold=0.8, roi=(380, 40, 800, 448))
        if found:
            self._log(f"已确认地图打开：识别到地图-筛选 ({r[0]}, {r[1]}) 置信度 {r[2]:.2f}")
            return True
        return False

    def _dialog_open(self, confirm_tmpl=None):
        """判断当前画面是否有对话/确认框（OCR"送我"或确认模板在对话框区域命中）"""
        if self._ocr_find((0, 0, 800, 448), "送我", timeout=1.0):
            return True
        if confirm_tmpl:
            frame = self.get_frame()
            if frame is not None:
                found, _ = self.find(frame, confirm_tmpl, threshold=0.8, roi=(200, 150, 700, 430))
                if found:
                    return True
        return False

    def _close_minimap(self):
        """关闭小地图：调用时地图必然刚被打开（_go_to_position 刚 _open_minimap）。
        每轮重新识别"关闭弹窗"按钮（自动尝试新旧两套模板）并点击，点击后必须验证
        真的关掉；未关掉则逐轮放宽阈值重识别，识别不到时点大地图已知 X 坐标兜底。
        最多 4 轮，不做其他固定坐标盲点。"""
        known_x = (677, 72)   # 大地图对话框右上角 X 实测位置
        for round_, thr in enumerate([0.75, 0.72, 0.70, 0.68]):
            if not self._is_minimap_open():
                return True
            btn = self._find_close_btn(thr)
            if btn:
                self._log(f"  点小地图关闭按钮 ({btn[0]}, {btn[1]}) 置信度 {btn[2]:.2f}")
                self.tap(btn[0], btn[1])
                # 点击关闭后立即截图会拿到关闭前的旧帧/未完成动画，
                # 之前因此误判“未关闭成功”并马上多点了一次。
                time.sleep(0.8)
            else:
                self._log(f"  未识别到关闭按钮（阈值 {thr}），点已知关闭位 {known_x}")
                self.tap(known_x[0], known_x[1])
                time.sleep(1.0)
            if self._minimap_closed():
                return True
            self._log(f"  小地图未关闭成功，重试（第 {round_ + 1}/4 轮）")
        self._log("  ⚠️ 小地图关闭失败，继续后续流程")
        return False

    def _find_close_btn(self, thr):
        """识别小地图/大地图弹窗的关闭按钮（自动尝试新旧两套模板）。"""
        frame = self.get_frame()
        if frame is None:
            return None
        found, r = self.find(frame, "关闭弹窗", threshold=thr, roi=(500, 20, 800, 120))
        if found:
            return r
        return None

    def _minimap_closed(self):
        """小地图是否已关闭：关闭按钮消失，且筛选/前往都不在画面上。"""
        if self._find_close_btn(0.65) is not None:
            return False
        return not self._is_minimap_open()

    def _get_current_map(self, attempts=3):
        """读取左上角当前地图名（一次性检测）；失败返回 None。"""
        if self.ocr is None:
            self._init_ocr()
            if self.ocr is None:
                return None
        x1, y1, x2, y2 = MAP_ROI
        for _ in range(attempts):
            frame = self.get_frame()
            if frame is not None and frame.shape[0] >= y2 and frame.shape[1] >= x2:
                crop = frame[y1:y2, x1:x2]
                if crop.size:
                    try:
                        res, _ = self.ocr(crop)
                        for box, text, conf in (res or []):
                            t = str(text).strip()
                            if len(t) >= 2:
                                return t
                    except Exception:
                        pass
            time.sleep(0.3)
        return None

    def _scene_in_route(self, ocr_text, route):
        """OCR 地图名与路线场景名容错匹配，返回 route 下标；不匹配返回 -1。"""
        if not ocr_text:
            return -1
        t = str(ocr_text).strip()
        for i, scene in enumerate(route):
            if t == scene or t.startswith(scene) or scene.startswith(t):
                return i
        return -1

    def _wait_map_name(self, keyword, timeout=90.0):
        """等待左上角地图名出现关键字。"""
        if self.ocr is None:
            self._init_ocr()
            if self.ocr is None:
                return None
        x1, y1, x2, y2 = MAP_ROI
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._abort_if_combat()
            frame = self.get_frame()
            if frame is not None:
                crop = frame[y1:y2, x1:x2]
                if crop.size:
                    try:
                        res, _ = self.ocr(crop)
                        for box, text, conf in (res or []):
                            if keyword in str(text):
                                return str(text)
                    except Exception:
                        pass
            time.sleep(0.6)  # 等地图名轮询节流：减少每轮截图次数
        return None

    # ---------- 小地图走位（坐标制，参考小霸王 map_action） ----------

    def _map_click_xy(self, map_name, x, y):
        params = MAP_PARAMS.get(map_name)
        if params is None:
            self._log(f"[未配置地图参数] {map_name}")
            return None
        lb, rng, wh = params
        cx = lb[0] + int(x * wh[0] / rng[0])
        cy = lb[1] - int(y * wh[1] / rng[1])
        return (cx, cy)

    def _map_game_xy_from_click(self, map_name, px, py):
        """小地图点击像素 -> 游戏坐标（MAP_PARAMS 逆变换）。
        用于核对角色是否真的走到传送口附近，再点传送图标。"""
        params = MAP_PARAMS.get(map_name)
        if params is None:
            return None
        lb, rng, wh = params
        gx = (px - lb[0]) * rng[0] / wh[0]
        gy = (lb[1] - py) * rng[1] / wh[1]
        return (int(round(gx)), int(round(gy)))

    def _click_map_times(self, point):
        """在小地图目标点批量随机点 1~3 下，必须整批点完后才允许关图。
        每下在 ±8 像素内随机偏移（避免同坐标被检测）。"""
        cnt = random.randint(1, 3)
        for i in range(cnt):
            ox = point[0] + random.randint(-8, 8)
            oy = point[1] + random.randint(-8, 8)
            self._log(f"  点小地图 {i + 1}/{cnt} ({ox}, {oy})")
            self.tap(ox, oy, offset=False)
            time.sleep(random.uniform(0.08, 0.15))

    def _wait_coord_near(self, x, y, tolerance=8, timeout=90.0, stable_secs=2.0):
        """等待角色走到目标坐标附近（跑图/走位用）。
        到达判定：
        1. 左上角坐标进入目标 ±tolerance → 立即算到达；
        2. 坐标连续 stable_secs 秒无变化 = 角色已停下：停下位置在容差内算到达，
           否则说明跑动结束但没到目标（被挡/点歪），快速返回 False 让上层重试，
           不再干等到 timeout。"""
        if self.ocr is None:
            self._init_ocr()
        if self.ocr is None:
            time.sleep(6.0)
            return True
        deadline = time.time() + timeout
        last_coord = None
        last_move_t = time.time()
        while time.time() < deadline:
            self._abort_if_combat()
            frame = self.get_frame()
            if frame is not None:
                # 左上角坐标显示区域（流坐标 y 30-62, x 55-135）
                res, _ = self.ocr(frame[30:62, 55:135])
                cur = None
                for box, text, conf in (res or []):
                    m = re.search(r"\((\d{1,3}),(\d{1,3})\)", str(text))
                    if m:
                        cur = (int(m.group(1)), int(m.group(2)))
                        break
                if cur is not None:
                    if abs(cur[0] - x) <= tolerance and abs(cur[1] - y) <= tolerance:
                        self._log(f"  已走到目标坐标 ({cur[0]},{cur[1]})")
                        return True
                    if cur == last_coord:
                        if time.time() - last_move_t >= stable_secs:
                            self._log(f"  坐标连续{stable_secs:.0f}秒无变化，角色停在 ({cur[0]},{cur[1]})，"
                                      f"未到目标 ({x},{y})")
                            return False
                    else:
                        last_coord = cur
                        last_move_t = time.time()
            time.sleep(0.5)  # 等坐标轮询节流：角色移动是秒级的，0.5s 足够且省截图
        return False

    def _go_to_position(self, map_name, x, y, timeout=90.0, wait_coord=True):
        """打开小地图，走到指定地图坐标。wait_coord=False 时关图即返回（由调用方等传送）。"""
        pt = self._map_click_xy(map_name, x, y)
        if pt is None:
            return False
        self._log(f"走位: {map_name} ({x},{y}) -> 小地图点击 {pt}")
        if not self._open_minimap():
            return False
        time.sleep(0.4)
        # 点目标点即触发自动寻路。这里批量随机点 1~3 下；
        # 必须等这一批点完再关图，关图后不再补点地图坐标。
        self._click_map_times(pt)
        time.sleep(0.3)
        # 点完目标点立即关闭小地图
        self._close_minimap()
        if wait_coord:
            return self._wait_coord_near(x, y, timeout=timeout)
        return True

    def _wait_transfer_button(self, target_map=None, timeout=TRANSFER_BTN_WAIT):
        """轮询传送按钮出现：每轮先模板匹配（~0.04s，远快于 OCR），未命中再按钮区域 OCR
        （单轮合并多关键字、按优先级返回）。返回 ("tmpl"/"ocr", 坐标+信息) 或 None。
        旧版 _click_chuan_song 全帧 OCR 串行扫"传送子母/子母/传送"3 轮（3+3+5s 超时），
        按钮出现前空转十几秒、每轮 2~4s 且"传送"小字常漏读 → 关图到点击实测空耗 ~34s。"""
        kws = None
        if target_map:
            # 优先目标传送口文字（朱紫国等多口地图避免点到其他传送口），最后泛匹配
            kws = [f"传送{target_map[:2]}", target_map[:2], "传送"]
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._abort_if_combat()
            frame = self.get_frame()
            if frame is not None:
                found, r = self.find(frame, "传送", threshold=0.75, roi=TRANSFER_BTN_ROI)
                if found:
                    return ("tmpl", r)
                tr = self._ocr_find(TRANSFER_BTN_ROI, kws or ["传送"], timeout=0.8,
                                    check_combat=False)
                if tr:
                    return ("ocr", tr)
            time.sleep(0.2)
        return None

    def _click_chuan_song(self, target_map=None):
        """点传送按钮：等按钮出现即点（模板优先、区域 OCR 兜底）；超时未出现用固定位兜底。"""
        hit = self._wait_transfer_button(target_map, timeout=3.0)
        if hit is not None:
            kind, pos = hit
            if kind == "tmpl":
                self._log(f"  点击传送(模板) ({pos[0]}, {pos[1]}) 置信度 {pos[2]:.2f}")
            else:
                self._log(f"  点击传送(OCR) {pos}")
            self.tap(pos[0], pos[1])
            return True
        self._abort_if_combat(force=True)
        self._log("  未找到传送按钮，用兜底位置")
        self.tap(MAP_TRANSFER_BTN[0], MAP_TRANSFER_BTN[1])
        return True

    def _find_npc_click(self, npc_tmpl, fallback=None):
        # 1) 优先 OCR 名字牌文字
        pos = self._ocr_find((0, 0, 800, 448), "花果山土地", timeout=2.0)
        if pos:
            self._log(f"  NPC 名字牌(OCR): {pos}")
            self.tap(pos[0], pos[1])
            return True
        # 2) 固定位置（角色走位到 NPC 后，名字牌在固定屏幕位置）
        if fallback:
            self._log(f"  NPC 固定位置点击 {fallback}")
            self.tap(fallback[0], fallback[1])
            return True
        # 3) 聚簇模板匹配（仅无固定位置时）
        frame = self.get_frame()
        if frame is None:
            return False
        tmpl = load_template(npc_tmpl)
        if tmpl is None:
            self._log(f"NPC 模板不存在: {npc_tmpl}")
            return False
        small = cv2.resize(frame, (STREAM_W, STREAM_H))
        hits = []
        for method in [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]:
            for s in [1.0, 0.9, 0.8, 1.1, 1.2]:
                stw, sth = max(2, int(tmpl.shape[1] * s)), max(2, int(tmpl.shape[0] * s))
                tt = tmpl if abs(s - 1) < 0.01 else cv2.resize(tmpl, (stw, sth))
                res = cv2.matchTemplate(small, tt, method)
                _, mv, _, ml = cv2.minMaxLoc(res)
                if mv > 0.6:
                    hits.append((mv, ml[0] + stw // 2, ml[1] + sth // 2))
        if not hits:
            if fallback:
                self._log(f"  NPC 未匹配，用固定位置 {fallback}")
                self.tap(fallback[0], fallback[1])
                return True
            self._log(f"未找到 NPC: {npc_tmpl}")
            return False
        hits.sort(reverse=True)
        best = None
        for mv, cx, cy in hits:
            cluster = [h for h in hits if abs(h[1] - cx) < 80 and abs(h[2] - cy) < 80]
            score = sum(h[0] for h in cluster)
            if best is None or score > best[0]:
                best = (score, int(sum(h[1] for h in cluster) / len(cluster)),
                        int(sum(h[2] for h in cluster) / len(cluster)))
        self._log(f"  NPC 聚簇定位: ({best[1]}, {best[2]}) 得分 {best[0]:.2f}")
        self.tap(best[1], best[2])
        return True

    def _get_npc_screen_pos(self, npc_xy):
        """按角色当前位置计算 NPC 屏幕坐标（小霸王公式，流坐标 400,224 为中心）。"""
        frame = self.get_frame()
        if frame is None:
            return None
        res, _ = self.ocr(frame[30:62, 55:135])
        char = None
        for box, text, conf in (res or []):
            m = re.search(r"\((\d{1,3}),(\d{1,3})\)", str(text))
            if m:
                char = (int(m.group(1)), int(m.group(2)))
                break
        if char is None:
            return None
        cx = int(400 - (char[0] - npc_xy[0]) * 16.6)
        cy = int(224 + (char[1] - npc_xy[1]) * 16.6)
        self._log(f"  NPC 坐标计算: 角色{char} NPC{npc_xy} -> 屏幕({cx},{cy})")
        return (cx, cy)

    def _walk_leg(self, source_map, target_map):
        """跨图腿：走位到传送点 → 点传送 / 点 NPC → 等地图变化。"""
        self._log(f"跑图: {source_map} -> {target_map}")
        if (source_map, target_map) in LEG_STEPS:
            step = LEG_STEPS[(source_map, target_map)]
            walk_map, xy, mode = step[0], step[1], step[2]
            circle_fallback = step[3] if len(step) > 3 else None
        elif (source_map, target_map) in LEG_NPCS:
            npc_xy = LEG_NPCS[(source_map, target_map)][0]
            walk_map, xy, mode = source_map, npc_xy, "npc"
        elif (source_map, target_map) in LEG_NPCS2:
            npc_xy, npc_tmpl, confirm_tmpl = LEG_NPCS2[(source_map, target_map)]
            walk_map, xy, mode = source_map, npc_xy, "npc2"
        else:
            self._log(f"[未配置] {source_map} -> {target_map}，请补充 LEG_STEPS / LEG_NPCS / LEG_NPCS2")
            return False

        if mode == "cave":
            return self._cave_leg(walk_map, target_map, xy, circle_fallback)

        if mode == "npc2":
            # NPC 对话式传送：走位到点 -> 点 NPC -> 等确认对话框（"送我到XX"）点击 -> 等地图变化
            # 注意：_go_to_position 内部已关闭小地图，这里不能再调 _close_minimap
            # （图已关时识别不到关闭按钮，会点固定位 (705,63) 落在主界面上乱点）
            for retry in range(2):
                if not self._go_to_position(walk_map, xy[0], xy[1]):
                    self._log("  走位失败")
                    break
                # 点 NPC：公式位置不可靠，用候选位置逐个点击并验证对话框是否弹出
                npc_pos = self._get_npc_screen_pos(npc_xy)
                candidates = []
                if npc_pos:
                    candidates.append(npc_pos)
                candidates.append((405, 190))   # 固定位置（角色走位到NPC旁，名字牌在屏幕中上）
                candidates.append((400, 230))   # 屏幕中央偏下
                clicked_npc = False
                for cand in candidates:
                    self._log(f"  点NPC候选 {cand}")
                    self.tap(cand[0], cand[1])
                    time.sleep(1.2)
                    if self._ocr_find((0, 0, 800, 448), "送我", timeout=2.0):
                        clicked_npc = True
                        break
                    if self._dialog_open(confirm_tmpl):
                        clicked_npc = True
                        break
                if not clicked_npc:
                    self._log("  NPC 候选位置均未弹出对话框，用模板聚簇补点")
                    self._find_npc_click(npc_tmpl, fallback=None)
                confirmed = False
                for attempt in range(3):
                    time.sleep(1.2)
                    pos = self._ocr_find((0, 0, 800, 448), "送我", timeout=3.0)
                    if pos:
                        self._log(f"  点确认(OCR): {pos}")
                        self.tap(pos[0], pos[1])
                        confirmed = True
                        break
                    frame = self.get_frame()
                    if frame is not None:
                        # 确认框限制在对话框区域，避免全屏误匹配
                        found, r = self.find(frame, confirm_tmpl, threshold=0.8, roi=(200, 150, 700, 430))
                        if found:
                            self._log(f"  点确认(模板): {r[:2]}")
                            self.tap(r[0], r[1])
                            confirmed = True
                            break
                if not confirmed:
                    self._log("  未找到确认对话框，点兜底位置 (405,190)")
                    self.tap(405, 190)
                kw = target_map[-2:] if target_map.endswith("层") else target_map[:2]
                got = self._wait_map_name(kw, timeout=3.0)
                if got:
                    self._log(f"  已到达 {target_map}（OCR: {got}）")
                    return True
                self._log("  NPC 传送未生效，重新走位重试")
            return False

        if mode == "npc":
            npc_xy, npc_tmpl, confirm_tmpl = LEG_NPCS[(source_map, target_map)]
            # _go_to_position 内部已关闭小地图，这里不再调 _close_minimap
            for retry in range(2):
                if not self._go_to_position(walk_map, xy[0], xy[1]):
                    self._log("  走位失败")
                    break
                npc_pos = self._get_npc_screen_pos(npc_xy)
                if npc_pos:
                    self.tap(npc_pos[0], npc_pos[1])
                else:
                    self._find_npc_click(npc_tmpl, fallback=(405, 190))
                confirmed = False
                for attempt in range(3):
                    time.sleep(1.2)
                    pos = self._ocr_find(NPC_CONFIRM_ROI, "是的", timeout=3.0)
                    if pos:
                        self._log(f"  点击确认(OCR): {pos}")
                        self.tap(pos[0], pos[1])
                        confirmed = True
                        break
                    frame = self.get_frame()
                    if frame is not None:
                        found, r = self.find(frame, confirm_tmpl, threshold=0.8, roi=NPC_CONFIRM_ROI)
                        if found:
                            self._log(f"  点击确认(模板): {r[:2]}")
                            self.tap(r[0], r[1])
                            confirmed = True
                            break
                if not confirmed:
                    self._log("  确认按钮兜底固定位置 (607,210)")
                    self.tap(607, 210)
                kw = target_map[-2:] if target_map.endswith("层") else target_map[:2]
                got = self._wait_map_name(kw, timeout=3.0)
                if got:
                    self._log(f"  已到达 {target_map}（OCR: {got}）")
                    return True
                self._log("  NPC 传送未生效，重新走位重试")
            return False
        else:
            if not self._go_to_position(walk_map, xy[0], xy[1], wait_coord=False):
                self._log("  走位失败")
                return False
            self._click_chuan_song(target_map=target_map)

        kw = target_map[-2:] if target_map.endswith("层") else target_map[:2]
        got = self._wait_map_name(kw, timeout=3.0)
        if got:
            self._log(f"  已到达 {target_map}（OCR: {got}）")
            return True
        # 点传送后地图未变：可能离传送口差几步（或点到其他传送口方向）。
        # 点屏幕左下角让角色靠近传送口，再点一次传送重试
        self._log(f"  传送未触发，点屏幕左下角靠近传送口再点一次")
        for _ in range(2):
            self.tap(CHUANSONG_NEAR_POINT[0], CHUANSONG_NEAR_POINT[1])
            time.sleep(1.5)
            got = self._wait_map_name(kw, timeout=3.0)
            if got:
                self._log(f"  已到达 {target_map}（OCR: {got}）")
                return True
            self._click_chuan_song(target_map=target_map)
            got = self._wait_map_name(kw, timeout=3.0)
            if got:
                self._log(f"  已到达 {target_map}（OCR: {got}）")
                return True
        self._log(f"  等待地图变化超时: {target_map}")
        return False

    def _cave_leg(self, source_map, target_map, label_click, circle_fallback=None):
        """洞穴层间：打开地图 → 点标签坐标 → 关图 → 等角色走到传送口 → 等传送图标 → 点传送 → 验证。
        点传送后地图没变且传送图标消失时，若配置了光圈兜底坐标则点光圈进洞；
        否则重新打开地图重新点标签重试。"""
        self._log(f"洞穴传送: {source_map} -> {target_map}（标签点击 {label_click}）")
        kw = target_map[-2:] if target_map.endswith("层") else target_map[:2]
        # 传送口游戏坐标（小地图点击像素逆推）：角色没走到之前，场景里其他"传送"
        # 文字（市场招牌/NPC名等）可能以高置信度误匹配传送模板，导致提前空点。
        # 先用左上角坐标确认到位，再等传送图标。
        gate_xy = self._map_game_xy_from_click(source_map, *label_click)
        for retry in range(3):
            # 上一轮点击可能延迟生效：先确认是否已经到达目标（≤3秒）
            got = self._wait_map_name(kw, timeout=1.0)
            if got:
                self._log(f"  已到达 {target_map}（OCR: {got}）")
                return True
            if not self._open_minimap():
                return False
            time.sleep(0.4)
            self._click_map_times(label_click)
            time.sleep(0.4)
            self._close_minimap()
            if gate_xy is not None:
                if not self._wait_coord_near(gate_xy[0], gate_xy[1], tolerance=25, timeout=90.0):
                    self._log(f"  等待走到传送口超时，重新打开地图重试（第 {retry + 1}/3 次）")
                    continue
            # 已走到传送口，等传送图标出现（模板优先、区域 OCR 兜底）
            hit = self._wait_transfer_button(timeout=3.0)
            if hit is None:
                self._log(f"  传送图标未出现，重新打开地图重试（第 {retry + 1}/3 次）")
                continue
            kind, pos = hit
            if kind == "tmpl":
                self._log(f"  点击传送(模板) ({pos[0]}, {pos[1]}) 置信度 {pos[2]:.2f}")
            else:
                self._log(f"  点击传送 {pos}")
            self.tap(pos[0], pos[1])
            # 传送正常 2~5 秒内完成，步骤等待不超过 3 秒，失败走兜底/重试
            got = self._wait_map_name(kw, timeout=3.0)
            if got:
                self._log(f"  已到达 {target_map}（OCR: {got}）")
                return True
            # 点传送没反应、且传送图标已消失 → 点传送光圈兜底（如北俱芦洲进洞口）
            if circle_fallback and self._wait_transfer_button(timeout=3.0) is None:
                self._log(f"  传送图标已消失，点击传送光圈 {circle_fallback} 兜底")
                self.tap(circle_fallback[0], circle_fallback[1])
                time.sleep(1.5)
                got = self._wait_map_name(kw, timeout=2.0)
                if got:
                    self._log(f"  已到达 {target_map}（OCR: {got}）")
                    return True
            self._log(f"  点传送后地图未变，重新打开地图重试（第 {retry + 1}/3 次）")
        self._log(f"  洞穴传送失败: {source_map} -> {target_map}")
        return False

    # ---------- 道具使用 ----------

    def _use_bag_item(self, item_name):
        self._log(f"使用道具: {item_name}")
        if not self._open_bag():
            self._log("打开背包失败")
            return False
        time.sleep(0.4)
        # 找到物品并点击选中
        used = False
        for attempt in range(self.retries):
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.3)
                continue
            found, r = self.find(frame, item_name, threshold=0.6)
            if not found:
                self._log(f"[{item_name}] 第 {attempt+1} 次：未找到")
                time.sleep(0.4)
                continue
            ix, iy = r[0], r[1]
            self._log(f"[{item_name}] 点击物品 ({ix},{iy}) 置信度 {r[2]:.2f}")
            self.tap(ix, iy)
            time.sleep(0.4)
            # 1) 优先模板匹配“使用”按钮（与飞行符路径一致，全屏匹配更可靠）
            frame = self.get_frame()
            used = False
            if frame is not None:
                f_use, r_use = self.find(frame, "使用", threshold=0.75)
                if f_use:
                    self._log(f"  点击使用(模板) ({r_use[0]}, {r_use[1]}) 置信度 {r_use[2]:.2f}")
                    self.tap(r_use[0], r_use[1])
                    used = True
            # 2) 模板没匹配到：在物品附近找“使用”按钮（避免全屏误匹配）
            if not used:
                roi = (max(0, ix - 150), max(0, iy - 100), min(800, ix + 220), min(448, iy + 160))
                pos = self._ocr_find(roi, "使用", timeout=3.0)
                if pos:
                    self._log(f"  点击使用(物品旁) {pos}")
                    self.tap(pos[0], pos[1])
                    used = True
            if used:
                break
            # 3) 兜底：双击物品直接使用
            self._log("  未找到使用按钮，双击物品")
            self.tap(ix, iy)
            time.sleep(0.15)
            self.tap(ix, iy)
            used = True
            break
        if not used:
            self._log(f"使用道具失败: {item_name}")
            return False
        time.sleep(0.4)
        self._close_bag_fast()
        self._log(f"道具使用完成: {item_name}")
        return True

    # ---------- 场景切换流程 ----------

    def _fly_to(self, map_name):
        target = resolve_template(map_name)
        self._log(f"飞行: {map_name} -> {target}")
        self._load_templates(target)
        if target not in self.templates and load_template(target) is None:
            self._log(f"飞行目的地模板不存在: {target}")
            return False
        self._close_bag_if_open()
        self._log("打开道具")
        if not self._open_bag():
            self._log("打开道具失败")
            return False
        self._log("点击飞行符")
        if not self.click_template("飞行符"):
            self._log("点击飞行符失败")
            return False
        self._log("点击使用")
        if not self.click_template("使用"):
            self._log("点击使用失败")
            return False
        self._log(f"点击 {target}")
        if not self.click_template(target):
            self._log(f"点击飞行目的地失败: {target}")
            return False
        time.sleep(1.5)
        self._close_bag_if_open()

        # 到达验证：之前点完目的地就直接返回成功，目的地按钮没点中/飞行没触发时，
        # 后续跑图会在原地图里瞎点。这里 OCR 左上角地图名确认真的到达才算成功，
        # 未到达判定飞行失败，由主循环保留切场请求稍后重试。
        arrived = self._wait_map_name(map_name, timeout=3.0)
        if not arrived:
            self._log(f"飞行后未到达 {map_name}（可能飞行未触发），判定飞行失败")
            return False
        self._log(f"已确认到达 {map_name}")
        return True

    def switch_scene(self, target_name):
        route = resolve_route(target_name)
        if route is not None and len(route) >= 2:
            self._log(f"路线: {target_name} = {' -> '.join(route)}")
            self._abort_if_combat(force=True)

            # 检测当前场景：已在路线中就从当前位置继续（不重复飞行/跑图）
            cur_map = self._get_current_map()
            start_idx = self._scene_in_route(cur_map, route)
            if start_idx > 0:
                self._log(f"  当前位于 {cur_map}（{route[start_idx]}），从该处继续")
            elif start_idx == 0:
                self._log(f"  已在 {route[0]}，跳过飞行")
            else:
                self._log(f"  当前 {cur_map or '未知场景'}，飞行到起点 {route[0]}")
                if not self._fly_to(route[0]):
                    self._log(f"飞行到起点失败: {route[0]}")
                    return False
                start_idx = 0

            self._abort_if_combat(force=True)
            # 子母河底等场景不遇低级怪，无需摄妖香防怪 / 洞冥草恢复，跳过这两步
            need_buff = target_name not in NO_BUFF_SCENES
            if need_buff and start_idx == 0:
                self._use_bag_item("摄妖香")
            self._abort_if_combat(force=True)
            cur = route[start_idx]
            for i, leg in enumerate(route[start_idx + 1:], start_idx + 1):
                self._log(f"跑图段 {i}/{len(route)-1}")
                self._abort_if_combat(force=True)
                if not self._walk_leg(cur, leg):
                    self._log(f"跑图失败: {cur} -> {leg}")
                    return False
                cur = leg
                self._abort_if_combat(force=True)
            if need_buff:
                self._use_bag_item("洞冥草")
            self._abort_if_combat(force=True)
            self._log(f"场景切换完成: {target_name}")
            return True

        self._log(f"目标模板: {target_name} -> {resolve_template(target_name)}")
        self._abort_if_combat(force=True)
        return self._fly_to(target_name)


# ======================== 命令行入口 ========================

def build_parser():
    p = argparse.ArgumentParser(
        description="场景切换：飞行 → 摄妖香 → 跑图 → 洞冥草",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("serial", nargs="?", help="ADB 设备号")
    p.add_argument("template", nargs="?", help="目标场景/地图名")
    p.add_argument("--devices", action="store_true", help="列出当前 ADB 设备")
    p.add_argument("--list", action="store_true", help="列出内置场景/路线")
    p.add_argument("--threshold", type=float, default=0.75, help="模板匹配阈值")
    p.add_argument("--retry", type=int, default=3, help="每个步骤最大重试次数")
    p.add_argument("--wait", type=float, default=0.8, help="步骤间等待秒数")
    p.add_argument("--debug", action="store_true", help="失败时保存调试截图")
    return p


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = build_parser().parse_args()

    if args.devices:
        devices = list_adb_devices()
        if not devices:
            print("未发现 ADB 设备")
            return 1
        for d in devices:
            print(d)
        return 0

    if args.list:
        print("内置场景快捷名：")
        for k, v in SCENE_SHORTCUTS.items():
            print(f"  {k} -> {v}")
        print("\n内置跑图路线：")
        for k, route in SCENE_ROUTES.items():
            print(f"  {k}: {' -> '.join(route)}")
        print("\n途经点也可作为目标（自动按路线前缀走到该点）。")
        return 0

    if not args.template:
        args.template = DEFAULT_TEMPLATE
        print(f"未指定场景/模板，默认使用: {args.template}")

    if not args.serial:
        devices = list_adb_devices()
        if DEFAULT_SERIAL in devices:
            args.serial = DEFAULT_SERIAL
            print(f"未指定设备号，使用默认设备: {args.serial}")
        elif len(devices) == 1:
            args.serial = devices[0]
            print(f"未指定设备号，自动选择: {args.serial}")
        elif not devices:
            print("未发现 ADB 设备")
            return 1
        else:
            print(f"未指定设备号，默认设备 {DEFAULT_SERIAL} 不在线，检测到多台设备：")
            for d in devices:
                print(f"  {d}")
            return 2

    switcher = SceneSwitcher(
        serial=args.serial,
        threshold=args.threshold,
        retries=args.retry,
        wait=args.wait,
        debug=args.debug,
    )
    if not switcher.connect():
        print("设备连接失败，请检查设备号")
        return 1

    ok = switcher.switch_scene(args.template)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
