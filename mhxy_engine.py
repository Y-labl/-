# -*- coding: utf-8 -*-
"""
小西天 / 女娲神迹 自动打怪 GUI 控制面板 v2.0
===============================================
功能：
  1. 手动选择/绑定 ADB 设备（支持模拟器窗口绑定）
  2. 可视化设置：HP/MP/BB 阈值、补药选择、酒肆恢复
  3. 像素扫描 HP/MP/BB 检测（集成血量检测测试.py）
  4. 战斗结束后自动酒肆恢复
  5. 地图选择：小西天 / 女娲神迹
  6. 一键启动/停止自动化流程
  7. 实时日志 + 血量显示
"""
import os, sys, json, re, random, time, threading, queue, subprocess as sp
import base64
from datetime import datetime
import requests
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR

# ======================== GUI ========================
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ======================== 常量 ========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(SCRIPT_DIR, "image")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
GUI_CONFIG_FILE = os.path.join(SCRIPT_DIR, "gui_config.json")

# ======================== 实时地图坐标 OCR 检测配置 ========================
# OCR区域（设备坐标，直接使用全分辨率ADB截图）
OCR_CROP = {"x": 131, "y": 40, "w": 200, "h": 100}
OCR_INTERVAL = 0.15
OCR_CONF_THRESHOLD = 0.5
COORD_STOP_TIMEOUT = 1.0  # 坐标停止超过1秒触发跑图
VALID_MAP_PREFIXES = [
    "小西天", "长安城", "大唐国境", "五庄观", "花果山",
    "傲来国", "朱紫国", "宝象国", "乌鸡国", "车迟国",
    "东海湾", "长寿村", "化生寺", "方寸山", "女儿村",
    "大雷音寺", "龙窟一层", "龙窟二层", "龙窟三层",
    "龙窟四层", "凤巢一层", "凤巢二层", "凤巢三层",
    "凤巢四层", "狮驼岭", "盘丝洞", "魔王寨", "天宫",
    "地府", "江南野外", "建邺城", "普陀山",
]

# 地图配置
MAP_CONFIG = {
    "小西天": {
        "map_click": {"x1": 212, "y1": 21, "x2": 475, "y2": 415},
        "monsters": ["金饶僧", "炎魔神", "噬天虎"],
        "steal_target": "炎魔神",
    },
    "女娲神迹": {
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "monsters": ["律法女娲", "灵符女娲", "净瓶女娲"],
        "steal_target": "律法女娲",
    },
}

# ======================== ADB 工具 ========================
try:
    import adbutils
    _ADB_EXE = adbutils.adb_path()
except Exception:
    _ADB_EXE = "adb"

# GUI 可直接引用的 ADB 可执行路径
ADB_EXE = _ADB_EXE


def adb_tap(serial, x, y):
    sp.run([_ADB_EXE, "-s", serial, "shell", "input", "tap", str(x), str(y)],
           capture_output=True, timeout=3, creationflags=sp.CREATE_NO_WINDOW)


def adb_key(serial, keycode):
    sp.run([_ADB_EXE, "-s", serial, "shell", "input", "keyevent", str(keycode)],
           capture_output=True, timeout=3, creationflags=sp.CREATE_NO_WINDOW)


def adb_screencap(serial):
    r = sp.run([_ADB_EXE, "-s", serial, "exec-out", "screencap", "-p"],
               capture_output=True, timeout=10, creationflags=sp.CREATE_NO_WINDOW)
    if r.returncode != 0:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)


def list_adb_devices():
    try:
        r = sp.run([_ADB_EXE, "devices"], capture_output=True, text=True, timeout=5, creationflags=sp.CREATE_NO_WINDOW)
        lines = r.stdout.strip().split("\n")[1:]
        return [l.split("\t")[0] for l in lines if "\tdevice" in l]
    except Exception:
        return []


# ======================== 模板匹配 ========================
def load_template(name):
    for d in [IMAGE_DIR, IMAGES_DIR]:
        for ext in [".png", ".bmp"]:
            for suffix in ["点卡服", "畅玩服", ""]:
                path = os.path.join(d, f"{name}{suffix}{ext}")
                if os.path.exists(path):
                    raw = np.fromfile(path, dtype=np.uint8)
                    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
                    if img is not None:
                        return img
    return None


def match_template(screenshot, template, threshold=0.75):
    if screenshot is None or template is None:
        return None
    h, w = screenshot.shape[:2]
    tw, th = template.shape[1], template.shape[0]
    if h < th or w < tw:
        return None
    best_val, best_pos = 0.0, None
    for s in [1.0, 0.75, 0.5]:
        sw, sh = int(w * s), int(h * s)
        stw, sth = int(tw * s), int(th * s)
        if sh < sth or sw < stw:
            continue
        small = cv2.resize(screenshot, (sw, sh))
        small_tmpl = cv2.resize(template, (stw, sth))
        result = cv2.matchTemplate(small, small_tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best_val:
            best_val = max_val
            best_pos = (int((max_loc[0] + stw // 2) / s),
                        int((max_loc[1] + sth // 2) / s))
    return (best_pos[0], best_pos[1], best_val) if best_val >= threshold else None


# ======================== HP/MP/BB 像素扫描检测 ========================
# 检测参数（流 800x448 下的坐标，来自血量检测测试.py）
DETECT_PARAMS = {
    "hp_y": 6,    "hp_xs": 756, "hp_xe": 799,   # 人物血量条 Y行, X起止
    "mp_y": 14,   "mp_xs": 756, "mp_xe": 799,   # 人物蓝量条
    "bb_y": 6,    "bb_xs": 654, "bb_xe": 697,   # 宝宝血量条
    "pp": 2.38,   # 每像素对应百分比
}

# ======================== 图灵云 API 配置（四小人检测） ========================
TULING_API_URL = "http://www.tulingcloud.com/tuling/predict"
TULING_AUTH = {
    "username": "yqning5",
    "password": "sai+123",
    "ID": 48117555,
    "version": "3.1.1",
}

# 四小人检测 ROI（设备分辨率 1920x1080 下的坐标）
FOUR_PERSON_ROI = {
    "left": 540, "top": 170, "width": 880, "height": 380,
}



def is_hp_pixel(b, g, r):
    """判断是否为血量像素（红色）"""
    return r > 200 and 34 < g < 98 and b < 65


def is_mp_pixel(b, g, r):
    """判断是否为蓝量像素（蓝色）"""
    return 10 < r < 87 and 120 < g < 175 and b > 205


def detect_hp_mp_bb(frame, params=None):
    """
    像素扫描检测 HP / MP / BB 百分比
    返回: (hp_pct, mp_pct, bb_pct, has_no_bb)
      - hp_pct/mp_pct/bb_pct: 0~100 的百分比
      - has_no_bb: True=没带宝宝
    """
    if frame is None:
        return 100.0, 100.0, 100.0, False

    p = params or DETECT_PARAMS
    h, w = frame.shape[:2]
    pp = p["pp"]

    def _get_pixel(x, y):
        if x < 0 or y < 0 or x >= w or y >= h:
            return (0, 0, 0)
        px = frame[y, x]
        return (int(px[0]), int(px[1]), int(px[2]))

    hp_count, mp_count, bb_count = 0.0, 0.0, 0.0

    # 扫描 HP 条
    hp_xs = min(p["hp_xs"], w - 1)
    hp_xe = min(p["hp_xe"], w)
    hp_y = min(p["hp_y"], h - 1)
    for x in range(hp_xs, hp_xe):
        b, g, r = _get_pixel(x, hp_y)
        if is_hp_pixel(b, g, r):
            hp_count += pp

    # 扫描 MP 条
    mp_xs = min(p["mp_xs"], w - 1)
    mp_xe = min(p["mp_xe"], w)
    mp_y = min(p["mp_y"], h - 1)
    for x in range(mp_xs, mp_xe):
        b, g, r = _get_pixel(x, mp_y)
        if is_mp_pixel(b, g, r):
            mp_count += pp

    # 扫描 BB 条
    bb_xs = min(p["bb_xs"], w - 1)
    bb_xe = min(p["bb_xe"], w)
    bb_y = min(p["bb_y"], h - 1)
    for x in range(bb_xs, bb_xe):
        b, g, r = _get_pixel(x, bb_y)
        if is_hp_pixel(b, g, r):
            bb_count += pp

    return min(hp_count, 100), min(mp_count, 100), min(bb_count, 100), bb_count == 0


# ======================== 配置管理 ========================
DEFAULT_CONFIG = {
    "serial": "",
    "map": "小西天",
    # 战斗中补血补蓝（快捷键物品）
    "hp_enabled": True,
    "hp_threshold": 30,
    "hp_item": "红碗",
    "mp_enabled": True,
    "mp_threshold": 20,
    "mp_item": "蓝碗",
    "mizhi_enabled": False,
    # 战斗后酒肆恢复
    "jiusi_enabled": True,
    "jiusi_hp_threshold": 50,
    "jiusi_mp_threshold": 30,
    "jiusi_bb_threshold": 50,
    # 妙手空空场景配置（与 UI 共用）
    "scene_config": [
        {"enabled": True, "scene": "小西天", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
    ],
    # 检测参数（可调）
    "detect_params": dict(DETECT_PARAMS),
    # 四小人检测 ROI（流分辨率 800x448 下的坐标）
    "four_person_roi": dict(FOUR_PERSON_ROI),
}

_item_hotkey_map = {
    "红碗": ("F1", 131),
    "九转": ("F1", 131),
    "蓝碗": ("F2", 132),
    "94蓝碗": ("F2", 132),
    "秘制": ("F5", 135),
}


def load_config():
    if os.path.exists(GUI_CONFIG_FILE):
        try:
            with open(GUI_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            # 确保 four_person_roi 每个键都存在
            cfg.setdefault("four_person_roi", dict(FOUR_PERSON_ROI))
            for rk, rv in FOUR_PERSON_ROI.items():
                cfg["four_person_roi"].setdefault(rk, rv)
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(GUI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def extract_coordinates(text):
    """从 OCR 文本提取坐标，支持 (393,66) / (393, 66) 格式"""
    text = str(text).strip()
    m = re.search(r"[(（]\s*(\d{1,4})\s*[,，]\s*(\d{1,4})\s*[)）]", text)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
        if 0 <= x <= 2500 and 0 <= y <= 2500:
            return (x, y)
    return None


def is_valid_map_name(text):
    """判断 OCR 文本是否为有效地名"""
    text = str(text).strip()
    for prefix in VALID_MAP_PREFIXES:
        if text.startswith(prefix):
            return True
    return False


def filter_ocr_result(result):
    """过滤 OCR 结果，仅保留地图名和坐标"""
    if result is None:
        return [], []
    maps, coords = [], []
    for box, text, conf in result:
        text = str(text).strip()
        if conf < OCR_CONF_THRESHOLD or len(text) < 2:
            continue
        if any(k in text for k in ["正在", "发现", "意外", "系统", "设置"]):
            continue
        coord = extract_coordinates(text)
        if coord:
            coords.append((coord, conf))
        if is_valid_map_name(text):
            maps.append((text, conf))
    return maps, coords


# ======================== 自动化引擎 ========================
class AutoFightEngine:
    """后台自动化引擎"""

    def __init__(self, config, log_queue):
        self.cfg = config
        self.log = log_queue
        self.running = False
        self.serial = config.get("serial", "")
        self.client = None
        self.templates = {}
        self.stream_w = 800
        self.stream_h = 448
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.was_in_pk = False
        # 血量状态
        self.last_hp = 100.0
        self.last_mp = 100.0
        self.last_bb = 100.0
        self.has_no_bb = False
        # 冷却计时
        self.hp_item_used_time = 0
        self.mp_item_used_time = 0
        self.jiusi_used_time = 0
        self._frame_lock = threading.Lock()
        self.last_skill = None
        # 实时坐标 OCR 检测
        self.ocr_engine = None
        self.last_coord = None
        self.last_map_name = None
        self.last_coord_time = 0
        self.coord_enabled = True
        self.battle_count = 0
        self.start_time = 0

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.put(f"[{ts}] {msg}")

    # ========== 截图 ==========
    def get_frame(self):
        if self.client is None:
            return adb_screencap(self.serial)
        with self._frame_lock:
            f = self.client.last_frame
            return f.copy() if f is not None else None

    def tap(self, x, y, offset=True):
        if offset:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)
        adb_tap(self.serial, int(x * self.scale_x), int(y * self.scale_y))

    def press_key(self, key_name):
        if key_name in _item_hotkey_map:
            _, code = _item_hotkey_map[key_name]
            adb_key(self.serial, code)
            self._log(f"  🔑 按键 {key_name}")

    # ========== 模板加载 ==========
    def load_templates(self, map_name):
        self._log("正在加载模板...")
        self.templates.clear()

        ui_templates = [
            "打开地图", "地图-筛选", "关闭地图", "好友入口",
            "主界面-右侧任务", "关闭弹窗", "关闭聊天", "关闭活动弹窗",
            "左下角返回", "菜单-指引",
        ]
        combat_templates = [
            "PK-妙手空空技能", "PK-自动按钮", "PK-取消自动战斗",
            "重置回合数", "PK-逃跑",
        ]
        monsters = MAP_CONFIG.get(map_name, MAP_CONFIG["小西天"])["monsters"]
        for m in monsters:
            combat_templates.append(f"PK-召唤兽-{m}")

        for name in ui_templates + combat_templates:
            tmpl = load_template(name)
            if tmpl is not None:
                tag = name.split("-")[-1]
                self.templates[tag if name.startswith("PK-召唤兽-") else name] = tmpl

        # 加载酒肆相关模板（独立加载，不需要后缀）
        for label, fname in [("酒肆技能", "酒肆技能"),
                              ("酒肆休息", "酒肆-休息"),
                              ("没带宝宝", "没带宝宝")]:
            for d in [IMAGE_DIR, IMAGES_DIR]:
                for ext in [".png", ".bmp"]:
                    path = os.path.join(d, f"{fname}{ext}")
                    if os.path.exists(path):
                        raw = np.fromfile(path, dtype=np.uint8)
                        img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
                        if img is not None:
                            self.templates[label] = img
                        break

        self._log(f"模板加载完成，共 {len(self.templates)} 个")

    # ========== 模板匹配 ==========
    def find(self, frame, name, threshold=0.75):
        tmpl = self.templates.get(name)
        return match_template(frame, tmpl, threshold) if tmpl is not None else None

    def is_map_open(self, frame):
        return (self.find(frame, "好友入口") is None and
                self.find(frame, "主界面-右侧任务") is None)

    def is_in_pk(self, frame):
        if self.is_map_open(frame):
            return False
        friend = self.find(frame, "好友入口")
        return friend is None or friend[0] < 100

    # ========== HP/MP/BB 检测与补药 ==========
    def detect_hp_mp_bb(self, frame):
        """像素扫描检测血量，返回 (hp, mp, bb, no_bb)"""
        params = self.cfg.get("detect_params", DETECT_PARAMS)
        hp, mp, bb, bb_pixel_zero = detect_hp_mp_bb(frame, params)

        # 检测是否没带宝宝：像素扫描 BB 区域无红色 + 模板匹配
        no_bb = bb_pixel_zero
        if not no_bb:
            bb_tmpl = self.templates.get("没带宝宝")
            if bb_tmpl is not None and match_template(frame, bb_tmpl, 0.75):
                no_bb = True

        self.last_hp = hp
        self.last_mp = mp
        self.last_bb = 101 if no_bb else bb  # 101 标记为无宝宝
        self.has_no_bb = no_bb
        return hp, mp, bb, no_bb

    def check_hp_mp_battle(self, frame):
        """战斗中 HP/MP 检测 → 快捷键补药"""
        if frame is None:
            return

        hp, mp, bb, no_bb = self.detect_hp_mp_bb(frame)
        now = time.time()

        if self.cfg.get("mizhi_enabled"):
            th = min(self.cfg.get("hp_threshold", 30), self.cfg.get("mp_threshold", 20))
            if (hp < th or mp < th) and now - self.hp_item_used_time > 8:
                self._log(f"  💊 秘制 (HP={hp:.0f}% MP={mp:.0f}%)")
                self.press_key("秘制")
                self.hp_item_used_time = now
                time.sleep(0.5)
            return

        if self.cfg.get("hp_enabled"):
            th = self.cfg.get("hp_threshold", 30)
            if hp < th and now - self.hp_item_used_time > 8:
                item = self.cfg.get("hp_item", "红碗")
                self._log(f"  ❤️ HP={hp:.0f}% < {th}%，使用 {item}")
                self.press_key(item)
                self.hp_item_used_time = now
                time.sleep(0.5)

        if self.cfg.get("mp_enabled"):
            th = self.cfg.get("mp_threshold", 20)
            if mp < th and now - self.mp_item_used_time > 8:
                item = self.cfg.get("mp_item", "蓝碗")
                self._log(f"  💙 MP={mp:.0f}% < {th}%，使用 {item}")
                self.press_key(item)
                self.mp_item_used_time = now
                time.sleep(0.5)

    # ========== 酒肆恢复（战斗结束后） ==========
    def do_jiu_si_heal(self):
        """
        酒肆恢复流程（来自血量检测测试.py）：
        1. 找「酒肆技能」→ 点击
        2. 等待 0.3s
        3. 找「酒肆-休息」→ 点击
        4. 等待恢复
        """
        now = time.time()
        if now - self.jiusi_used_time < 15:
            return  # 冷却中

        self._log("  🍶 酒肆恢复流程...")

        # 等待非战斗状态
        for _ in range(10):
            f = self.get_frame()
            if f is not None and not self.is_in_pk(f):
                break
            time.sleep(0.5)

        # 关闭弹窗确保干净
        self.close_pop(is_one_time=True)
        time.sleep(0.3)

        # 第1步：找酒肆技能
        found_skill = False
        for attempt in range(5):
            f = self.get_frame()
            if f is None:
                time.sleep(0.3)
                continue
            r = self.find(f, "酒肆技能", threshold=0.70)
            if r:
                self._log(f"  ✅ 找到酒肆技能 ({r[0]},{r[1]})")
                self.tap(r[0], r[1])
                found_skill = True
                break
            time.sleep(0.3)

        if not found_skill:
            self._log("  ❌ 未找到酒肆技能，跳过恢复")
            return

        time.sleep(0.5)

        # 第2步：找酒肆休息
        found_rest = False
        for attempt in range(8):
            f = self.get_frame()
            if f is None:
                time.sleep(0.3)
                continue
            r = self.find(f, "酒肆休息", threshold=0.65)
            if r:
                self._log(f"  ✅ 找到酒肆-休息 ({r[0]},{r[1]})")
                self.tap(r[0], r[1])
                found_rest = True
                break
            time.sleep(0.3)

        if not found_rest:
            self._log("  ⚠️ 未找到酒肆-休息，可能已恢复")
        else:
            # 等待恢复动画
            self._log("  ⏳ 等待酒肆恢复...")
            time.sleep(3.0)

        self.jiusi_used_time = time.time()
        self._log("  🍶 酒肆恢复完成")

    def check_and_heal_after_combat(self):
        """
        战斗结束后：检测血量，按阈值判断是否酒肆恢复
        优先使用新版 UI 字段 hp_method / mp_method / hp_threshold / mp_threshold
        """
        hp_method = self.cfg.get("hp_method", "")
        mp_method = self.cfg.get("mp_method", "")

        # 新版 UI 配置：酒肆作为补给方式
        if hp_method or mp_method:
            jiusi_enabled = (hp_method == "酒肆" or mp_method == "酒肆")
            jiusi_hp = self.cfg.get("hp_threshold", 30) if hp_method == "酒肆" else 0
            jiusi_mp = self.cfg.get("mp_threshold", 20) if mp_method == "酒肆" else 0
        else:
            # 旧版/默认配置兼容
            jiusi_enabled = self.cfg.get("jiusi_enabled", True)
            jiusi_hp = self.cfg.get("jiusi_hp_threshold", 50)
            jiusi_mp = self.cfg.get("jiusi_mp_threshold", 30)

        if not jiusi_enabled:
            return

        jiusi_bb = self.cfg.get("jiusi_bb_threshold", 50)

        # ????????????????
        time.sleep(0.05)
        f = self.get_frame()
        if f is None:
            return

        hp, mp, bb, no_bb = self.detect_hp_mp_bb(f)

        need_heal = hp < jiusi_hp or mp < jiusi_mp
        need_bb_heal = (not no_bb) and bb < jiusi_bb

        msg_parts = []
        if hp < jiusi_hp:
            msg_parts.append(f"HP:{hp:.0f}% < {jiusi_hp}%")
        if mp < jiusi_mp:
            msg_parts.append(f"MP:{mp:.0f}% < {jiusi_mp}%")
        if need_bb_heal:
            msg_parts.append(f"BB:{bb:.0f}% < {jiusi_bb}%")

        if not msg_parts:
            self._log(f"  ✅ 血量正常 (HP:{hp:.0f}% MP:{mp:.0f}% BB:{'--' if no_bb else f'{bb:.0f}%'})")
            return

        self._log(f"  🔔 触发酒肆恢复: {', '.join(msg_parts)}")
        self.do_jiu_si_heal()


    # ========== 设备初始化 ==========
    def init_device_scale(self):
        try:
            r = sp.run([_ADB_EXE, "-s", self.serial, "shell", "dumpsys", "window", "displays"],
                       capture_output=True, text=True, timeout=5, creationflags=sp.CREATE_NO_WINDOW)
            m = re.search(r"cur=(\d+)x(\d+)", r.stdout)
            if not m:
                m = re.search(r"app=(\d+)x(\d+)", r.stdout)
            if m:
                dw, dh = int(m.group(1)), int(m.group(2))
                self.scale_x = dw / self.stream_w
                self.scale_y = dh / self.stream_h
                self._log(f"设备: {dw}x{dh}  缩放: {self.scale_x:.2f}x{self.scale_y:.2f}")
                return
        except Exception as e:
            self._log(f"分辨率获取失败: {e}")
        self.scale_x = 1920 / self.stream_w
        self.scale_y = 1080 / self.stream_h

    def init_device(self):
        self._log(f"连接设备: {self.serial}")
        try:
            from pyscrcpy import Client
            self.client = Client(self.serial, bitrate=8000000, max_fps=10, max_size=800)
            self.client.start(threaded=True)
            time.sleep(1.5)
            if self.client.last_frame is None:
                self._log("❌ 无首帧，回退 ADB 截图")
                self.client = None
                f = adb_screencap(self.serial)
                if f is not None:
                    self.stream_h, self.stream_w = f.shape[:2]
                    self._log(f"✅ ADB 截图 ({self.stream_w}x{self.stream_h})")
                else:
                    return False
            else:
                self.stream_h, self.stream_w = self.client.last_frame.shape[:2]
                self._log(f"✅ 视频流 ({self.stream_w}x{self.stream_h})")
            self.init_device_scale()
            return True
        except Exception as e:
            self._log(f"pyscrcpy 失败: {e}")
            self.client = None
            f = adb_screencap(self.serial)
            if f is not None:
                self.stream_h, self.stream_w = f.shape[:2]
                self._log(f"✅ ADB 截图 ({self.stream_w}x{self.stream_h})")
                self.init_device_scale()
                return True
            return False

    # ========== 弹窗 ==========
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
            self.close_pop(is_one_time=is_one_time, try_count=try_count)

    def close_map_if_open(self):
        for _ in range(3):
            f = self.get_frame()
            if f is None:
                time.sleep(0.15)
                continue
            close = self.find(f, "关闭地图", threshold=0.5)
            if close:
                self.tap(close[0], close[1])
                time.sleep(random.uniform(0.2, 0.3))
                return True
        time.sleep(0.15)
        self.tap(60, 25)
        time.sleep(random.uniform(0.1, 0.2))
        return False

    # ========== 战斗 ==========
    def _wait_for_skill(self, timeout=10.0):
        start = time.time()
        while time.time() - start < timeout:
            if not self.running:
                return None
            frame = self.get_frame()
            if frame is None or not self.is_in_pk(frame):
                return None
            self.check_hp_mp_battle(frame)
            ms = self.find(frame, "PK-妙手空空技能", threshold=0.60)
            if ms:
                self.last_skill = ms
                return ms
            time.sleep(0.3)
        return None

    def _check_in_combat(self):
        if not self.running:
            return False
        frame = self.get_frame()
        return frame is not None and self.is_in_pk(frame)

    def _save_detection_debug(self, frame, name, targets):
        """保存怪物检测标注截图用于调试"""
        try:
            debug_dir = os.path.join(SCRIPT_DIR, "screenshots")
            os.makedirs(debug_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(debug_dir, f"detect_{name}_{ts}.png")
            annotated = frame.copy()
            for i, (x, y, conf) in enumerate(targets):
                cv2.circle(annotated, (x, y), 20, (0, 0, 255), 3)
                cv2.putText(annotated, f"{i+1} {conf:.2f}", (x+25, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.imwrite(path, annotated)
            self._log("  📸 检测截图: " + path)
        except Exception as e:
            self._log("  ⚠️ 截图保存失败: " + str(e))

    def do_combat(self):
        self._log("⚔️ 开始战斗流程")
        map_name = self.cfg.get("map", "小西天")
        steal_target = MAP_CONFIG.get(map_name, MAP_CONFIG["小西天"])["steal_target"]

        tmpl = self.templates.get(steal_target)
        if tmpl is None:
            self._log(f"⚠️ 未加载目标模板: {steal_target}")
            self._try_escape()
            return

        frame = self.get_frame()
        if frame is None:
            return
        if not self.is_in_pk(frame):
            return
        # 战斗截图已关闭
        targets = self._find_all(frame, steal_target, threshold=0.81)
        # 距离去重：相距<15px的只保留置信度最高的
        deduped = []
        for t in sorted(targets, key=lambda x: x[2], reverse=True):
            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 225 for d in deduped):
                deduped.append(t)
        targets = deduped
        self._log(f"  🔍 检测到 {len(targets)} 个 {steal_target}")
        for i, t in enumerate(targets):
            self._log(f"    [{i+1}] ({t[0]},{t[1]}) conf={t[2]:.2f}")
        # self._save_detection_debug(frame, steal_target, targets)  # 调试截图已关闭

        plan = self._build_plan(targets)
        if not plan:
            self._log(f"  ⚠️ 未检测到 {steal_target}，跳过妙手空空")

        if self.cfg.get("miaoshou_enabled", True):
            clicked = []  # 已点击过的坐标，避免重复
            max_attempts = min(len(plan), 3) if plan else 3
            self._log(f"  🎯 妙手空空 ×{max_attempts}")
            for i in range(max_attempts):
                if not self._check_in_combat():
                    return
                # 每次先重新检测目标
                f2 = self.get_frame()
                if f2 is None:
                    break
                cur = self._find_all(f2, steal_target, threshold=0.78)
                if not cur:
                    self._log(f"  ⚠️ {steal_target}已全部消失")
                    break
                self._log(f"  \U0001f50d \u91cd\u65b0\u68c0\u6d4b\u5230 {len(cur)} \u4e2a {steal_target}")
                # 过滤已点击过的位置（相距<30px视为同一个）
                available = [c for c in cur if not any(abs(c[0]-px)**2+abs(c[1]-py)**2 < 900 for px, py in clicked)]
                if not available:
                    self._log(f"  ⚠️ 所有{steal_target}均已偷过")
                    break
                best = max(available, key=lambda c: c[2])
                tx, ty, conf = best[0], best[1], best[2]
                ms = self._wait_for_skill(timeout=10.0)
                if ms is None:
                    self._log(f"  第{i+1}次: 超时，跳过")
                    continue
                cx_ms, cy_ms, _ = ms
                self.tap(cx_ms, cy_ms)
                time.sleep(random.uniform(0.3, 0.5))
                self.tap(tx, ty)
                self._log(f"  🎯 第{i+1}次 妙手空空 -> ({tx},{ty}) conf={conf:.2f}")
                clicked.append((tx, ty))
                time.sleep(random.uniform(2.0, 3.0))
        else:
            if self.cfg.get("miaoshou_enabled", True):
                self._log("  ⏭️ 妙手空空已关闭")
            else:
                self._log("  ⏭️ 妙手空空未触发")

        self._try_escape()
        self._wait_combat_end()

    def _find_all(self, frame, name, threshold=0.81):
        tmpl = self.templates.get(name)
        if tmpl is None or frame is None:
            return []
        h, w = frame.shape[:2]
        tw, th = tmpl.shape[1], tmpl.shape[0]
        if h < th or w < tw:
            return []
        best = {}
        for s in [1.0, 0.75, 0.5]:
            sw, sh = int(w * s), int(h * s)
            sth, stw = int(th * s), int(tw * s)
            if sh < sth or sw < stw:
                continue
            small = cv2.resize(frame, (sw, sh))
            small_tmpl = cv2.resize(tmpl, (stw, sth))
            result = cv2.matchTemplate(small, small_tmpl, cv2.TM_CCOEFF_NORMED)
            mask = np.zeros(result.shape, dtype=np.uint8)
            while True:
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val < threshold:
                    break
                cx = int((max_loc[0] + stw // 2) / s)
                cy = int((max_loc[1] + sth // 2) / s)
                key = (cx // max(tw // 3, 1), cy // max(th // 3, 1))
                if key not in best or max_val > best[key][2]:
                    best[key] = (cx, cy, max_val)
                x1 = max(0, max_loc[0] - stw // 2)
                y1 = max(0, max_loc[1] - sth // 2)
                cv2.rectangle(mask, (x1, y1), (x1 + stw, y1 + sth), 1, -1)
                result[mask > 0] = 0
        return list(best.values())

    def _build_plan(self, targets):
        if not targets:
            return []
        sorted_targets = sorted(targets, key=lambda x: x[2], reverse=True)
        n = len(sorted_targets)
        if n >= 3:
            # 3个以上：各偷1次，共计3次
            return [(sorted_targets[j][0], sorted_targets[j][1]) for j in range(3)]
        elif n == 2:
            # 2个：交替 A、B、A，每个最多2次
            return [
                (sorted_targets[0][0], sorted_targets[0][1]),
                (sorted_targets[1][0], sorted_targets[1][1]),
                (sorted_targets[0][0], sorted_targets[0][1]),
            ]
        else:
            # 1个：最多2次
            return [(sorted_targets[0][0], sorted_targets[0][1])] * 2

    def _try_escape(self):
        if not self.cfg.get('escape_enabled', True):
            self._log("  ⏭️ 逃跑已关闭，等待战斗结束")
            self._wait_combat_end()
            return

        self._log("  🏃 尝试逃跑...")
        escape_count = 0
        skill_visible = False
        for _ in range(200):
            if not self._check_in_combat():
                break
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.3)
                continue
            # 检测妙手空空技能：可见=玩家回合，不可见=敌人回合
            ms = self.find(frame, "PK-妙手空空技能", threshold=0.60)
            if ms and not skill_visible:
                # 玩家回合到了，尝试逃跑
                skill_visible = True
                esc = self.find(frame, "PK-逃跑", threshold=0.70)
                if esc is None:
                    esc = self.find(frame, "PK-逃跑", threshold=0.50)
                if esc:
                    escape_count += 1
                    self._log(f"  🏃 第{escape_count}次逃跑")
                    self.tap(esc[0], esc[1])
                    time.sleep(1.2)
                    if not self._check_in_combat():
                        self._log("  🏁 已逃跑")
                        break
                    self._log("  ❌ 逃跑失败")
            elif not ms:
                # 敌人回合，等待下一轮
                skill_visible = False
            time.sleep(0.3)

    def _wait_combat_end(self):
        for _ in range(30):
            frame = self.get_frame()
            if frame is not None and not self.is_in_pk(frame):
                self._log("  🏁 战斗结束")
                return
            time.sleep(0.3)

    def _is_avatar_visible(self):
        """Pixel-color scan of character avatar bar (from isShowRoleAvatar)."""
        frame = self.get_frame()
        if frame is None:
            return True
        h, w = frame.shape[:2]
        scale_x = w / 800.0
        scale_y = h / 448.0
        y = max(0, min(int(1 * scale_y), h - 1))
        x_start = max(0, int(700 * scale_x))
        x_end = min(int(740 * scale_x), w)
        if x_end - x_start < 15:
            return True
        total = 0
        matched = 0
        for x in range(x_start, x_end):
            bgr = frame[y, x]
            b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
            total += 1
            cwf1 = (55 < r < 85)  and (70 < g < 115) and (70 < b < 115)
            cwf2 = (115 < r < 150) and (145 < g < 185) and (145 < b < 185)
            dkf  = (45 < r < 115) and (75 < g < 140) and (85 < b < 180)
            if cwf1 or cwf2 or dkf:
                matched += 1
        return matched > total * 0.85


    def _is_show_four_person(self):
        """四小人检测：HP/MP + 角色头像"""
        frame = self.get_frame()
        if frame is None:
            return False
        hp, mp, bb, no_bb = self.detect_hp_mp_bb(frame)
        if not (hp < 1 and mp < 1):
            return False
        if self._is_avatar_visible():
            return False
        return True

    def _handle_four_person(self):
        """四小人检测：截取区域 -> 图灵云API识别 -> 点击坐标"""
        if not self._is_show_four_person():
            self._log("  👥 非四小人界面，跳过检测")
            return

        self._log("  👅 检测到四小人界面，开始识别...")
        result = self._detect_four_person()
        if result["success"]:
            x, y = result["x"], result["y"]
            self._log(f"  ✅ 四小人识别成功: ({x}, {y})")
            self.tap(x, y)
            time.sleep(random.uniform(1, 2))
        else:
            self._log("  ⚠️ 四小人识别失败: " + str(result.get("error", "未知")))


    # ========== 四小人检测（图灵云API） ==========
    def _detect_four_person(self):
        """
        全分辨率 ADB 截图 -> 裁剪 ROI -> 上传图灵云 API -> 返回识别坐标（流坐标）
        返回: {"success": bool, "x": int, "y": int, "error": str, ...}
        坐标转换: 设备坐标 / scale -> 流坐标, tap() 再 * scale -> 设备坐标
        """
        result = {
            "success": False,
            "x": None, "y": None,
            "error": None,
        }

        try:
            # 使用全分辨率 ADB 截图（质量更好，ROI 值直接对应设备分辨率）
            frame = adb_screencap(self.serial)
            if frame is None:
                result["error"] = "全分辨率截图失败"
                return result

            h, w = frame.shape[:2]
            roi_cfg = self.cfg.get("four_person_roi", FOUR_PERSON_ROI)
            left = roi_cfg.get("left", FOUR_PERSON_ROI["left"])
            top = roi_cfg.get("top", FOUR_PERSON_ROI["top"])
            width = roi_cfg.get("width", FOUR_PERSON_ROI["width"])
            height = roi_cfg.get("height", FOUR_PERSON_ROI["height"])

            # 根据实际设备分辨率缩放 ROI
            # FOUR_PERSON_ROI 基于 1920x1080，按比例映射到实际设备
            ref_w, ref_h = 1920, 1080
            scale_roi_x = w / ref_w
            scale_roi_y = h / ref_h
            left = int(left * scale_roi_x)
            top = int(top * scale_roi_y)
            width = int(width * scale_roi_x)
            height = int(height * scale_roi_y)

            # 边界安全
            left = max(0, min(left, w - 1))
            top = max(0, min(top, h - 1))
            width = min(width, w - left)
            height = min(height, h - top)

            if width <= 0 or height <= 0:
                result["error"] = f"ROI 无效: ({left},{top},{width},{height}) 图片 {w}x{h}"
                return result

            roi = frame[top:top + height, left:left + width]
            retval, buffer = cv2.imencode(".png", roi)
            if not retval:
                result["error"] = "ROI 编码失败"
                return result

            roi_base64 = base64.b64encode(buffer).decode("utf-8")
            data = {}
            data.update(TULING_AUTH)
            data["b64"] = roi_base64
            data_json = json.dumps(data, ensure_ascii=False)

            resp = requests.post(TULING_API_URL, data=data_json, timeout=5)
            api_result = json.loads(resp.text)

            if api_result.get("data") and api_result["data"]:
                x_val = api_result["data"].get("X坐标值")
                y_val = api_result["data"].get("Y坐标值")
                if x_val is not None and y_val is not None:
                    # API 返回 ROI 内的坐标 -> 加上 ROI 偏移 -> 设备坐标
                    dev_x = left + int(x_val)
                    dev_y = top + int(y_val)
                    # 转换为流坐标，tap() 会自动乘以 scale_x/scale_y 转回设备坐标
                    result["success"] = True
                    result["x"] = int(dev_x / self.scale_x)
                    result["y"] = int(dev_y / self.scale_y)
                    return result

            result["error"] = f"API 未返回坐标: {api_result}"
            return result

        except Exception as e:
            result["error"] = str(e)
            return result


    # ========== 实时坐标 OCR 检测 ==========
    def init_ocr(self):
        """初始化 OCR"""
        if self.ocr_engine is not None:
            return
        self._log("初始化 RapidOCR ...")
        try:
            self.ocr_engine = RapidOCR()
            self.ocr_engine(np.zeros((64, 64, 3), dtype=np.uint8))
            self._log("RapidOCR 初始化完成")
            # self._save_ocr_debug()  # OCR调试截图已关闭
        except Exception as e:
            self._log(f"OCR初始化失败: {e}")
            self.ocr_engine = None

    def _save_ocr_debug(self):
        """保存 OCR 区域调试截图"""
        try:
            f = self.get_frame()
            if f is None:
                return
            h, w = f.shape[:2]
            cx = max(0, int(OCR_CROP["x"] / self.scale_x))
            cy = max(0, int(OCR_CROP["y"] / self.scale_y))
            cw = min(int(OCR_CROP["w"] / self.scale_x), w - cx)
            ch = min(int(OCR_CROP["h"] / self.scale_y), h - cy)
            ann = f.copy()
            cv2.rectangle(ann, (cx, cy), (cx + cw, cy + ch), (0, 0, 255), 2)
            cv2.putText(ann, f"OCR ({cx},{cy}) {cw}x{ch}", (cx, cy - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            dd = os.path.join(SCRIPT_DIR, "screenshots")
            os.makedirs(dd, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = os.path.join(dd, f"ocr_region_{ts}.png")
            cv2.imwrite(fp, ann)
            self._log(f"OCR region screenshot: screenshots/ocr_region_{ts}.png")
            self._log(f"  stream crop: ({cx},{cy}) {cw}x{ch}  stream: {w}x{h}  scale: {self.scale_x:.2f}x{self.scale_y:.2f}")
        except Exception as e:
            self._log(f"OCR debug failed: {e}")

    def detect_map_coord(self, frame=None):
        """OCR检测地图名和坐标（使用pyscrcpy流帧）"""
        if self.ocr_engine is None:
            return None, None, False
        f = frame if frame is not None else self.get_frame()
        if f is None:
            return None, None, False
        h, w = f.shape[:2]
        cx = max(0, int(OCR_CROP["x"] / self.scale_x))
        cy = max(0, int(OCR_CROP["y"] / self.scale_y))
        cw = min(int(OCR_CROP["w"] / self.scale_x), w - cx)
        ch = min(int(OCR_CROP["h"] / self.scale_y), h - cy)
        if cw <= 0 or ch <= 0:
            return None, None, False
        crop = f[cy:cy+ch, cx:cx+cw]
        try:
            result, _ = self.ocr_engine(crop)
            maps, coords = filter_ocr_result(result)
            map_name = maps[0][0] if maps else None
            coord = coords[0][0] if coords else None
            # 调试：打印OCR识别到的原始文本
            if result and len(result) > 0:
                texts = [str(r[1]).strip() for r in result[:8] if len(str(r[1]).strip()) > 1]
                if texts:
                    self._log(f"OCR raw texts: {texts}")
            return map_name, coord, True
        except Exception as e:
            self._log(f"OCR exception: {e}")
            return None, None, False

    def check_coord_stopped(self, frame=None):
        """检测坐标是否停止超过1秒"""
        if not self.coord_enabled:
            return False, None, None
        map_name, coord, ok = self.detect_map_coord(frame)
        if not ok or coord is None:
            return False, map_name, coord
        now = time.time()
        if self.last_coord is None:
            self.last_coord = coord
            self.last_map_name = map_name
            self.last_coord_time = now
            self._log(f"首次检测坐标: {map_name or '?'} ({coord[0]},{coord[1]})")
            return False, map_name, coord
        if coord != self.last_coord:
            self.last_coord = coord
            self.last_map_name = map_name
            self.last_coord_time = now
            return False, map_name, coord
        if now - self.last_coord_time > COORD_STOP_TIMEOUT:
            return True, map_name, coord
        return False, map_name, coord

    def reset_coord_tracking(self):
        self.last_coord = None
        self.last_coord_time = 0

    def post_combat(self, frame):
        """战斗结束后清理 + 血量检测 + 酒肆恢复"""
        self.was_in_pk = False
        cancel = self.find(frame, "PK-取消自动战斗")
        if cancel:
            self._log("  🔄 取消自动战斗")
            self.tap(cancel[0], cancel[1])
            time.sleep(0.5)
        reset = self.find(frame, "重置回合数")
        if reset:
            self._log("  🔄 重置回合数")
            self.tap(reset[0], reset[1])
            time.sleep(0.5)

        # ===== 战斗后血量检测 + 酒肆恢复 =====
        time.sleep(0.2)
        self.check_and_heal_after_combat()

    # ========== 主循环 ==========
    def run_loop(self):
        scene_config = self.cfg.get("scene_config", DEFAULT_CONFIG["scene_config"])
        enabled_scenes = [s for s in scene_config if s.get("enabled")]
        if not enabled_scenes:
            self._log("❌ 没有启用的场景，请在 UI 中至少勾选一个场景")
            self.log.put("__STOPPED__")
            return

        # 当前只实现 MAP_CONFIG 中已有的场景逻辑，其余场景预留
        supported = []
        reserved = []
        for s in enabled_scenes:
            if s.get("scene") in MAP_CONFIG:
                supported.append(s)
            else:
                reserved.append(s.get("scene"))

        if reserved:
            self._log(f"⚠️ 以下场景已配置但逻辑暂未完善：{', '.join(reserved)}")
        if not supported:
            self._log("❌ 没有已完善的场景可运行。当前支持：小西天、女娲神迹")
            self.log.put("__STOPPED__")
            return

        # 取第一个已支持的场景运行（后续可扩展为自动切换）
        current_scene = supported[0]
        map_name = current_scene["scene"]
        self.cfg["map"] = map_name
        map_cfg = MAP_CONFIG.get(map_name, MAP_CONFIG["小西天"])
        mc = map_cfg["map_click"]

        self.load_templates(map_name)
        if not self.init_device():
            self._log("❌ 设备初始化失败")
            self.log.put("__STOPPED__")
            return

        self.running = True
        self.start_time = time.time()
        self.battle_count = 0
        hp_method = self.cfg.get("hp_method", "")
        mp_method = self.cfg.get("mp_method", "")
        if hp_method or mp_method:
            jiusi_en = (hp_method == "酒肆" or mp_method == "酒肆")
            jiusi_hp = self.cfg.get("hp_threshold", 30) if hp_method == "酒肆" else 0
            jiusi_mp = self.cfg.get("mp_threshold", 20) if mp_method == "酒肆" else 0
        else:
            jiusi_en = self.cfg.get("jiusi_enabled", True)
            jiusi_hp = self.cfg.get("jiusi_hp_threshold", 50)
            jiusi_mp = self.cfg.get("jiusi_mp_threshold", 30)
        self._log("=" * 40)
        self._log(f"🚀 {map_name} 自动打怪 启动")
        self._log(f"   场景: {current_scene.get('scene')}  环数:{current_scene.get('rings')}  卡片:{current_scene.get('cards')}  时间:{current_scene.get('time')}")
        self._log(f"   战斗中: HP<{self.cfg.get('hp_threshold',30)}%→{self.cfg.get('hp_item','红碗')}  "
                  f"MP<{self.cfg.get('mp_threshold',20)}%→{self.cfg.get('mp_item','蓝碗')}")
        self._log(f"   战后酒肆: {'✅' if jiusi_en else '❌'}  "
                  f"HP<{jiusi_hp}%  "
                  f"MP<{jiusi_mp}%  "
                  f"BB<{self.cfg.get('jiusi_bb_threshold',50)}%")
        self._log("=" * 40)

        loop = 0
        try:
            while self.running:
                loop += 1
                frame = self.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue

                # 四小人快速检测（没带宝宝模板不可见即四小人界面）
                if self._is_show_four_person():
                    self._log(f"[{loop}] 👥 检测到四小人界面")
                    self._handle_four_person()
                    time.sleep(random.uniform(0.5, 1))
                    continue

                in_pk = self.is_in_pk(frame)

                # === 刚进入战斗 ===
                if in_pk and not self.was_in_pk:
                    self.was_in_pk = True
                    self._log(f"[{loop}] ⚔️ 进入战斗！")
                    self.check_hp_mp_battle(frame)
                    self.do_combat()
                    time.sleep(0.15)
                    continue

                # === 刚结束战斗 → post_combat 里会触发酒肆恢复 ===
                if not in_pk and self.was_in_pk:
                    self.post_combat(frame)
                    time.sleep(0.15)
                    continue

                # === 非战斗：跑图（坐标检测驱动） ===
                if not in_pk:
                    if self.cfg.get("auto_path_enabled", True):
                        def _pk_check():
                            return self.running and self.is_in_pk(self.get_frame())

                        # 确保 OCR 已初始化
                        if self.coord_enabled and self.ocr_engine is None:
                            self.init_ocr()

                        # 检测坐标是否停止
                        coord_stopped, cur_map, cur_coord = self.check_coord_stopped(frame)

                        # 坐标还在变化中，无需跑图
                        if not coord_stopped:
                            if self.last_coord is not None and cur_coord is not None:
                                self._log(f"[{loop}] \U0001f3c3 跑动中 ({cur_coord[0]},{cur_coord[1]})")
                            self.close_pop(is_one_time=True)
                            time.sleep(0.3)
                            continue

                        # 坐标停止超过1秒，触发跑图
                        self._log(f"[{loop}] \u23f8 坐标停止 ({self.last_coord})，重新跑图")

                        pk_detected = False

                        # 1. 打开地图
                        map_btn = self.find(frame, "打开地图")
                        if map_btn:
                            self.tap(map_btn[0], map_btn[1])
                            for _ in range(4):
                                time.sleep(0.15)
                                if _pk_check():
                                    pk_detected = True
                                    break

                        # 2. 随机点击地图
                        if not pk_detected:
                            cx = random.randint(mc["x1"], min(mc["x2"], self.stream_w - 1))
                            cy = random.randint(mc["y1"], min(mc["y2"], self.stream_h - 1))
                            self.tap(cx, cy, offset=False)
                            for _ in range(5):
                                time.sleep(0.15)
                                if _pk_check():
                                    pk_detected = True
                                    break

                        # 3. 关闭地图
                        if not pk_detected:
                            self.close_map_if_open()
                            for _ in range(4):
                                time.sleep(0.15)
                                if _pk_check():
                                    pk_detected = True
                                    break

                        if pk_detected:
                            continue

                        # 重置坐标跟踪（刚移动完，等坐标变化）
                        self.reset_coord_tracking()
                        self.close_pop(is_one_time=True)
                    else:
                        self._log(f"[{loop}] \u23f8\ufe0f 自动寻路已关闭，等待遇怪")
                        pk = False
                        for _ in range(3):
                            time.sleep(0.4)
                            if self.is_in_pk(self.get_frame()):
                                pk = True
                                break
                        if pk:
                            continue


                time.sleep(0.3)

        except Exception as e:
            self._log(f"❌ 异常: {e}")
            import traceback
            self._log(traceback.format_exc())
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.client:
            try:
                self.client.stop()
            except Exception:
                pass
        self._log("🏁 已停止")
        self.log.put("__STOPPED__")


# ======================== GUI 主界面 ========================
class AutoFightGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("小西天 / 女娲神迹 自动打怪 v2.0")
        self.root.geometry("640x880")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.cfg = load_config()
        self.log_queue = queue.Queue()
        self.engine_thread = None
        self.engine = None

        self._build_ui()
        self._refresh_devices()
        self._load_cfg_to_ui()
        self._poll_log()

    # ==================== UI 构建 ====================
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 滚动容器
        canvas = tk.Canvas(self.root, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas, padding=10)
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 鼠标滚轮
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(-1 * (ev.delta // 120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        main_frame = self.scroll_frame
        row = 0

        # ---- 标题 ----
        ttk.Label(main_frame, text="🎮 梦幻西游 自动打怪控制面板 v2.0",
                  font=("Microsoft YaHei", 14, "bold")).grid(
            row=row, column=0, columnspan=3, pady=(0, 10), sticky="w")
        row += 1

        # ======== 设备绑定 ========
        self._add_section(main_frame, "📱 设备绑定", row); row += 1
        dev_frame = ttk.LabelFrame(main_frame, padding=8)
        dev_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1

        ttk.Label(dev_frame, text="选择设备:").grid(row=0, column=0, padx=(0, 5))
        self.device_combo = ttk.Combobox(dev_frame, state="readonly", width=35)
        self.device_combo.grid(row=0, column=1, padx=(0, 5))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)
        self.btn_refresh = ttk.Button(dev_frame, text="刷新", command=self._refresh_devices, width=6)
        self.btn_refresh.grid(row=0, column=2, padx=(0, 5))
        self.btn_bind = ttk.Button(dev_frame, text="绑定窗口", command=self._bind_window, width=10)
        self.btn_bind.grid(row=0, column=3)
        self.dev_status = ttk.Label(dev_frame, text="未绑定", foreground="red")
        self.dev_status.grid(row=1, column=0, columnspan=4, pady=(5, 0), sticky="w")

        # ======== 战斗中补给设置 ========
        self._add_section(main_frame, "⚙️ 战斗中补给（快捷键物品）", row); row += 1
        set_frame = ttk.LabelFrame(main_frame, padding=8)
        set_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1

        # HP
        self.hp_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(set_frame, text="战斗中补血", variable=self.hp_enabled,
                        command=self._on_setting_change).grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(set_frame, text="HP<").grid(row=0, column=1)
        self.hp_threshold = tk.StringVar(value="30")
        ttk.Entry(set_frame, textvariable=self.hp_threshold, width=5).grid(row=0, column=2)
        ttk.Label(set_frame, text="% →").grid(row=0, column=3, padx=(2, 5))
        self.hp_item = ttk.Combobox(set_frame, values=["九转", "秘制"], state="readonly", width=10)
        self.hp_item.grid(row=0, column=4)
        self.hp_item.set("九转")
        self.hp_item.bind("<<ComboboxSelected>>", lambda e: self._on_setting_change())

        # MP
        self.mp_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(set_frame, text="战斗中补蓝", variable=self.mp_enabled,
                        command=self._on_setting_change).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(6, 0))
        ttk.Label(set_frame, text="MP<").grid(row=1, column=1, pady=(6, 0))
        self.mp_threshold = tk.StringVar(value="20")
        ttk.Entry(set_frame, textvariable=self.mp_threshold, width=5).grid(row=1, column=2, pady=(6, 0))
        ttk.Label(set_frame, text="% →").grid(row=1, column=3, padx=(2, 5), pady=(6, 0))
        self.mp_item = ttk.Combobox(set_frame, values=["94蓝碗", "秘制"], state="readonly", width=10)
        self.mp_item.grid(row=1, column=4, pady=(6, 0))
        self.mp_item.set("94蓝碗")
        self.mp_item.bind("<<ComboboxSelected>>", lambda e: self._on_setting_change())

        # 秘制
        self.mizhi_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(set_frame, text="使用秘制（补血补蓝，忽略上方单设）",
                        variable=self.mizhi_enabled, command=self._on_setting_change
                        ).grid(row=2, column=0, columnspan=5, sticky="w", pady=(6, 0))

        ttk.Label(set_frame, text="💡 游戏内提前把 F1=九转 / F2=蓝碗 / F5=秘制 放快捷栏",
                  foreground="gray").grid(row=3, column=0, columnspan=5, sticky="w", pady=(6, 0))

        # ======== 战后酒肆恢复 ========
        self._add_section(main_frame, "🍶 战后酒肆恢复（战斗结束自动检测）", row); row += 1
        jiusi_frame = ttk.LabelFrame(main_frame, padding=8)
        jiusi_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1

        self.jiusi_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(jiusi_frame, text="启用战后自动酒肆恢复",
                        variable=self.jiusi_enabled).grid(row=0, column=0, columnspan=5, sticky="w")

        ttk.Label(jiusi_frame, text="HP<").grid(row=1, column=0, pady=(6, 0))
        self.jiusi_hp_threshold = tk.StringVar(value="50")
        ttk.Entry(jiusi_frame, textvariable=self.jiusi_hp_threshold, width=5).grid(row=1, column=1, pady=(6, 0))
        ttk.Label(jiusi_frame, text="%").grid(row=1, column=2, padx=(2, 15))

        ttk.Label(jiusi_frame, text="MP<").grid(row=1, column=3, pady=(6, 0))
        self.jiusi_mp_threshold = tk.StringVar(value="30")
        ttk.Entry(jiusi_frame, textvariable=self.jiusi_mp_threshold, width=5).grid(row=1, column=4, pady=(6, 0))
        ttk.Label(jiusi_frame, text="%").grid(row=1, column=5, padx=(2, 15))

        ttk.Label(jiusi_frame, text="BB<").grid(row=1, column=6, pady=(6, 0))
        self.jiusi_bb_threshold = tk.StringVar(value="50")
        ttk.Entry(jiusi_frame, textvariable=self.jiusi_bb_threshold, width=5).grid(row=1, column=7, pady=(6, 0))
        ttk.Label(jiusi_frame, text="%").grid(row=1, column=8, padx=(2, 5))

        ttk.Label(jiusi_frame, text="💡 任一项低于阈值，战斗结束后自动触发酒肆→休息恢复",
                  foreground="gray").grid(row=2, column=0, columnspan=9, sticky="w", pady=(6, 0))

        # ======== 地图设置 ========
        self._add_section(main_frame, "🗺️ 地图设置", row); row += 1
        map_frame = ttk.LabelFrame(main_frame, padding=8)
        map_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1
        ttk.Label(map_frame, text="地图选择:").grid(row=0, column=0, padx=(0, 10))
        self.map_select = ttk.Combobox(map_frame, values=list(MAP_CONFIG.keys()), state="readonly", width=15)
        self.map_select.grid(row=0, column=1)
        self.map_select.set("小西天")
        self.map_select.bind("<<ComboboxSelected>>", lambda e: self._on_setting_change())

        # ======== 控制 ========
        self._add_section(main_frame, "🎮 控制", row); row += 1
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1
        self.btn_start = ttk.Button(ctrl_frame, text="▶ 启动", command=self.start_engine, width=12)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_stop = ttk.Button(ctrl_frame, text="⏹ 停止", command=self.stop_engine, width=12, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 10))
        self.status_canvas = tk.Canvas(ctrl_frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(5, 5))
        self._draw_status("gray")
        self.status_label = ttk.Label(ctrl_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)

        # ======== 实时数据 ========
        self._add_section(main_frame, "📊 实时数据", row); row += 1
        data_frame = ttk.Frame(main_frame)
        data_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1
        self.hp_display = ttk.Label(data_frame, text="HP: --%", font=("Consolas", 11))
        self.hp_display.pack(side=tk.LEFT, padx=(0, 20))
        self.mp_display = ttk.Label(data_frame, text="MP: --%", font=("Consolas", 11))
        self.mp_display.pack(side=tk.LEFT, padx=(0, 20))
        self.bb_display = ttk.Label(data_frame, text="BB: --%", font=("Consolas", 11))
        self.bb_display.pack(side=tk.LEFT)

        # ======== 日志 ========
        self._add_section(main_frame, "📋 运行日志", row); row += 1
        self.log_text = scrolledtext.ScrolledText(
            main_frame, height=14, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        self.log_text.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=(0, 5))
        self.log_text.configure(state=tk.DISABLED)
        row += 1

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=row, column=0, columnspan=3, sticky="ew")
        ttk.Button(bottom_frame, text="清空日志", command=self._clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="保存配置", command=self._save_cfg).pack(side=tk.LEFT)

        main_frame.rowconfigure(row - 2, weight=1)
        main_frame.columnconfigure(0, weight=1)
        self.root.geometry("640x850")

    def _add_section(self, parent, text, row):
        ttk.Label(parent, text=text, font=("Microsoft YaHei", 11, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(8, 2))

    def _draw_status(self, color):
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 18, 18, fill=color, outline="")

    # ==================== 设备 ====================
    def _refresh_devices(self):
        devices = list_adb_devices()
        self.device_combo["values"] = devices
        if devices:
            if self.cfg.get("serial") in devices:
                self.device_combo.set(self.cfg["serial"])
            else:
                self.device_combo.set(devices[0])
                self.cfg["serial"] = devices[0]
            self.dev_status.config(text=f"已发现 {len(devices)} 个设备", foreground="green")
        else:
            self.device_combo.set("")
            self.dev_status.config(text="未发现 ADB 设备", foreground="orange")

    def _on_device_selected(self, event=None):
        sel = self.device_combo.get()
        if sel:
            self.cfg["serial"] = sel

    def _bind_window(self):
        serial = self.device_combo.get()
        if not serial:
            messagebox.showwarning("提示", "请先选择一个设备")
            return
        self.cfg["serial"] = serial
        save_config(self.cfg)
        self.dev_status.config(text=f"已绑定: {serial}", foreground="green")
        self._log(f"✅ 已绑定设备: {serial}")
        self.btn_start.config(state=tk.NORMAL)

    # ==================== 引擎控制 ====================
    def start_engine(self):
        serial = self.cfg.get("serial")
        if not serial:
            messagebox.showwarning("提示", "请先绑定设备")
            return
        self._sync_ui_to_cfg()
        save_config(self.cfg)
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_bind.config(state=tk.DISABLED)
        self._draw_status("green")
        self.status_label.config(text="运行中")
        self.engine = AutoFightEngine(self.cfg, self.log_queue)
        self.engine_thread = threading.Thread(target=self.engine.run_loop, daemon=True)
        self.engine_thread.start()

    def stop_engine(self):
        if self.engine:
            self.engine.running = False
        self._log("⏹ 正在停止...")
        self._on_engine_stopped()

    def _on_engine_stopped(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_bind.config(state=tk.NORMAL)
        self._draw_status("gray")
        self.status_label.config(text="已停止")
        self.hp_display.config(text="HP: --%")
        self.mp_display.config(text="MP: --%")
        self.bb_display.config(text="BB: --%")

    # ==================== 日志 ====================
    def _poll_log(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg == "__STOPPED__":
                    self.root.after(0, self._on_engine_stopped)
                    continue
                self._log_to_ui(msg)
                if self.engine:
                    hp = self.engine.last_hp
                    mp = self.engine.last_mp
                    bb = self.engine.last_bb
                    no_bb = self.engine.has_no_bb
                    self.hp_display.config(
                        text=f"HP: {hp:.0f}%",
                        foreground="red" if hp < 30 else "green")
                    self.mp_display.config(
                        text=f"MP: {mp:.0f}%",
                        foreground="blue" if mp < 30 else "green")
                    bb_text = "--" if no_bb else f"{bb:.0f}%"
                    bb_color = "gray" if no_bb else ("red" if bb < 30 else "green")
                    self.bb_display.config(text=f"BB: {bb_text}", foreground=bb_color)
        except queue.Empty:
            pass
        self.root.after(300, self._poll_log)

    def _log(self, msg):
        self._log_to_ui(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _log_to_ui(self, msg):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ==================== 配置 ====================
    def _load_cfg_to_ui(self):
        cfg = self.cfg
        self.hp_enabled.set(cfg.get("hp_enabled", True))
        self.hp_threshold.set(str(cfg.get("hp_threshold", 30)))
        self.hp_item.set(cfg.get("hp_item", "九转"))
        self.mp_enabled.set(cfg.get("mp_enabled", True))
        self.mp_threshold.set(str(cfg.get("mp_threshold", 20)))
        self.mp_item.set(cfg.get("mp_item", "94蓝碗"))
        self.mizhi_enabled.set(cfg.get("mizhi_enabled", False))
        self.jiusi_enabled.set(cfg.get("jiusi_enabled", True))
        self.jiusi_hp_threshold.set(str(cfg.get("jiusi_hp_threshold", 50)))
        self.jiusi_mp_threshold.set(str(cfg.get("jiusi_mp_threshold", 30)))
        self.jiusi_bb_threshold.set(str(cfg.get("jiusi_bb_threshold", 50)))
        self.map_select.set(cfg.get("map", "小西天"))
        if cfg.get("serial"):
            if cfg["serial"] in (self.device_combo["values"] or []):
                self.device_combo.set(cfg["serial"])
            self.dev_status.config(text=f"设备: {cfg['serial']}", foreground="green")
            self.btn_start.config(state=tk.NORMAL)
        self._on_setting_change()

    def _sync_ui_to_cfg(self):
        try:
            self.cfg["hp_enabled"] = self.hp_enabled.get()
            self.cfg["hp_threshold"] = int(self.hp_threshold.get())
            self.cfg["hp_item"] = self.hp_item.get()
            self.cfg["mp_enabled"] = self.mp_enabled.get()
            self.cfg["mp_threshold"] = int(self.mp_threshold.get())
            self.cfg["mp_item"] = self.mp_item.get()
            self.cfg["mizhi_enabled"] = self.mizhi_enabled.get()
            self.cfg["jiusi_enabled"] = self.jiusi_enabled.get()
            self.cfg["jiusi_hp_threshold"] = int(self.jiusi_hp_threshold.get())
            self.cfg["jiusi_mp_threshold"] = int(self.jiusi_mp_threshold.get())
            self.cfg["jiusi_bb_threshold"] = int(self.jiusi_bb_threshold.get())
            self.cfg["map"] = self.map_select.get()
        except ValueError:
            pass

    def _on_setting_change(self, event=None):
        if self.mizhi_enabled.get():
            self.hp_item.config(state=tk.DISABLED)
            self.mp_item.config(state=tk.DISABLED)
        else:
            self.hp_item.config(state="readonly")
            self.mp_item.config(state="readonly")

    def _save_cfg(self):
        self._sync_ui_to_cfg()
        save_config(self.cfg)
        self._log("✅ 配置已保存")

    def on_close(self):
        if self.engine and self.engine.running:
            if messagebox.askyesno("确认", "引擎正在运行，确定要退出吗？"):
                self.engine.running = False
                if self.engine_thread:
                    self.engine_thread.join(timeout=3)
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()


# ======================== 入口 ========================
if __name__ == "__main__":
    app = AutoFightGUI()
    app.run()
