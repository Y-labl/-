# -*- coding: utf-8 -*-

"""

小西天 / 女娲神迹 自动打怪 GUI 控制面板 v2.0

===============================================

功能：

  1. 手动选择/绑定 ADB 设备（支持模拟器窗口绑定）

  2. 可视化设置：气血/魔法/BB 阈值、补药选择、酒肆恢复

  3. 像素扫描 气血/魔法/BB 检测（集成血量检测测试.py）

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

# RapidOCR 改为惰性导入（仅 init_ocr 时加载），避免 GUI 启动时加载 onnxruntime 拖慢启动

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

# OCR区域（800x448 流坐标；get_frame 已统一归一化到 800x448，直接按流坐标裁剪）。
# 覆盖左上角 y0-100：16:9 设备地图名/坐标在 x54-137，20:9 设备偏右在 x100-240，
# 两区域合并后 (40,0,220,100) 可同时覆盖两种设备布局。
# OCR_CROP = {"x": 131, "y": 40, "w": 200, "h": 100}  # 旧：1920x1080 设备坐标，20:9 设备会裁偏
OCR_CROP = {"x": 40, "y": 0, "w": 220, "h": 100}

OCR_INTERVAL = 0.15

OCR_CONF_THRESHOLD = 0.5

COORD_STOP_TIMEOUT = 3.0  # 坐标停止超过1秒触发跑图

COMBAT_ROI = {"x": 90, "y": 60, "w": 375, "h": 278}  # 战斗怪物检测区域

# 后排5个怪物位置坐标（划过可露出被前排遮挡的名字）

SWIPE_POSITIONS = [(349,568),(486,481),(590,403),(716,355),(853,285)]  # 1920x1080 device coords



# 后排5个怪物位置坐标（划过可露出被前排遮挡的名字）

# 场景配置（从 target_mapping 动态加载）

from target_mapping import (

    SCENE_MAPPING,

    get_tou_targets,

    get_jineng_targets,

    get_all_monsters,

    get_map_click_area,

    is_supported_scene,

    list_supported_scenes,

    list_all_known_scenes,

)



VALID_MAP_PREFIXES = list_all_known_scenes() + [

    "乌鸡国", "车迟国", "大雷音寺",

    "龙窟二层", "龙窟三层", "龙窟四层",

    "凤巢一层", "凤巢二层",

    "狮驼岭", "盘丝洞", "天宫",

]



# 兼容旧版 MAP_CONFIG 接口（GUI 使用）

from target_mapping import (

    SCENE_MAPPING,

    get_tou_targets,

    get_jineng_targets,

    get_all_monsters,

    get_map_click_area,

    is_supported_scene,

    list_supported_scenes,

    list_all_known_scenes,

    list_all_known_scenes,

)



# 兼容旧版 MAP_CONFIG 接口（GUI 使用）

MAP_CONFIG = {}

for scene_name in list_supported_scenes():

    monsters = []

    for mt in get_all_monsters(scene_name):

        tag = mt.split("-")[-1]

        monsters.append(tag)

    tou_targets = get_tou_targets(scene_name)

    steal_tag = tou_targets[0].split("-")[-1] if tou_targets else ""

    MAP_CONFIG[scene_name] = {

        "map_click": get_map_click_area(scene_name),

        "monsters": monsters,

        "steal_target": steal_tag,

    }



# 在 xbw_features goToMapAction 中无导航分支的场景（真实切场会静默失败），
# 仍可打怪但不出现在自动切场轮转列表中
NO_SWITCH_NAV_SCENES = {"凤巢三层", "凤巢五层"}


def _match_scene_name(ocr_text, scene_name):
    """OCR 场景名与配置场景名容错匹配：完全相等或前缀匹配。
    OCR 常识别出带多余字符的文本（如"小西天："），用 startswith 兼容。"""
    if not ocr_text or not scene_name:
        return False
    ocr_text = str(ocr_text).strip()
    if not ocr_text:
        return False
    return ocr_text == scene_name or ocr_text.startswith(scene_name)


def short_dev_label(serial):
    """设备显示标识：前5位(尾3位)，如 WEENU18720159489 -> WEENU(489)。
    引擎日志前缀与 GUI 筛选下拉共用此规则，保证两边可互相匹配。"""
    if not serial:
        return "未知"
    serial = str(serial)
    if len(serial) >= 8:
        return f"{serial[:5]}({serial[-3:]})"
    return serial


def stats_day(now=None):
    """统计日：以每天 05:00 为界（05:00~次日 04:59 属同一天），返回 YYYY-MM-DD。
    挂机常跨 0 点，按自然日 0 点切天会把记录串到第二天；
    统一按游戏凌晨 5 点刷新，下班挂机跨夜后计数仍算"当天"。"""
    if now is None:
        now = datetime.now()
    from datetime import timedelta
    return (now - timedelta(hours=5)).strftime("%Y-%m-%d")



# ======================== ADB 工具 ========================

try:

    import adbutils

    _ADB_EXE = adbutils.adb_path()

except Exception:

    _ADB_EXE = "adb"



# GUI 可直接引用的 ADB 可执行路径

ADB_EXE = _ADB_EXE





def adb_tap(serial, x, y):
    # ADB 偶发卡顿/超时会导致 TimeoutExpired 异常冒泡到主循环把引擎整个停掉。
    # 这里重试2次 + 吞掉异常：仍失败则静默跳过这次点击，不终止战斗流程。
    for _attempt in range(3):
        try:
            sp.run([_ADB_EXE, "-s", serial, "shell", "input", "tap", str(x), str(y)],
                   capture_output=True, timeout=3, creationflags=sp.CREATE_NO_WINDOW)
            return
        except Exception:
            if _attempt == 2:
                return  # 3次都失败，丢弃本次点击，避免引擎被异常终止
            time.sleep(0.3)





def adb_key(serial, keycode):
    try:
        sp.run([_ADB_EXE, "-s", serial, "shell", "input", "keyevent", str(keycode)],
               capture_output=True, timeout=3, creationflags=sp.CREATE_NO_WINDOW)
    except Exception:
        pass  # ADB 偶发卡顿：吞掉异常，避免顶掉引擎







def adb_screencap(serial):
    try:
        r = sp.run([_ADB_EXE, "-s", serial, "exec-out", "screencap", "-p"],
                   capture_output=True, timeout=10, creationflags=sp.CREATE_NO_WINDOW)
        if r.returncode != 0:
            return None
        return cv2.imdecode(np.frombuffer(r.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception:
        return None  # ADB 偶发卡顿：返回 None，调用方自行处理，不顶掉引擎





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

    # 战斗中捕捉召唤兽

    "capture_bb_enabled": False,

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
        self._loyalty_stop_event = threading.Event()  # 诚度恢复停止信号
        self._paused = False  # 暂停标志（忠诚度恢复等工具运行时暂停主循环）

        self.serial = config.get("serial", "")

        # 设备名称（从配置获取，用于日志标识）
        device_names = config.get("device_names", {})
        self.device_name = device_names.get(self.serial, "") if device_names else ""

        # 设备短标识（用于日志前缀，优先用设备名，否则用序列号前4位）
        self.device_id = self.device_name if self.device_name else short_dev_label(self.serial)

        # 日志文件路径
        import os
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self._log_day_dir = None
        self.log_file = self._daily_log_file()

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

        self._last_map_click = None  # 上次地图点击坐标，用于距离检查

        # ===== 小霸王三功能合并（xbw_features） =====
        self._xbw_wired = False
        self._pkg_snapshot = None        # 上次背包 20 格占用快照
        self._pkg_check_t = 0.0          # 上次检查背包时间
        self._pkg_interval = 0.0         # 下次检查间隔（550~700 随机）
        self._huan_count = 0             # 当前场景累计环数
        self._card_count = 0             # 当前场景累计卡数
        self._daily_huan_count = 0       # 当日累计环数（跨重启保留，按天重置）
        self._daily_card_count = 0       # 当日累计卡数（跨重启保留，按天重置）
        self._scene_switch_requested = False
        self._switch_retry_after = 0.0    # 真实切场失败后的重试冷却截止时间戳
        self._last_4p_check_t = 0.0      # 战斗中四小人判定节流
        self._tuling_fail_streak = 0     # 图灵云连续失败次数（用于冷却节流）
        self._tuling_cooldown_until = 0  # 图灵云冷却截止时间戳（余额不足等持续失败时暂停调用）
        self._scene_history = []         # 场景历史记录：[{name, cards, rings, duration, start_time}]
        self._current_scene_start_time = time.time()  # 当前场景开始时间

        # 场景历史文件（按天记录，每天 5:00 为界）
        self._scene_history_date = stats_day()
        self._scene_history_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "logs",
            f"scene_history_{self.serial}_{self._scene_history_date}.json"
        )

        # 当前统计日（每天 5:00 切换）：跨统计日重置当日累计
        self._stats_day_key = stats_day()

        # 加载场景历史
        self._load_scene_history()

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

        self._loyalty_recovery_requested = False   # 战斗中识别不到防御（可能忠诚度问题），战后执行恢复

        self._loyalty_recovery_done = False        # 战后已执行过忠诚度恢复，等待下一场验证

        self._defend_miss_streak = 0               # 本场连续识别不到防御按钮次数（防回合收尾误报）

        self._battle_defend_attempted = False      # 本场是否尝试过点防御（有偷卡且非无宝宝）

        self._battle_defend_ok = False             # 本场是否至少一次成功识别到防御

        self._auto_battle_on = False               # 本场已点自动：挂自动后不再补点防御（自动会接管指令）

        self._loyalty_recovery_pending = False     # 3次防御都没识别到逃跑后，待执行忠诚度恢复

        self._loyalty_recovery_done_since_miss = False  # 是否已为“未参战”执行过一次恢复

        self._pet_no_lifespan = False              # 恢复后仍3次都没识别到 -> 判定没寿命，每场偷3次逃跑

        self._lifespan_alerted = False             # 本场战斗是否已弹框提醒宝宝无寿命

        # ===== 实时战斗循环持久状态（_battle_loop 使用，进战斗时 _reset_battle_state 重置） =====
        self._combat_phase = None                # 实时战斗循环阶段：entry/steal/post/wait_end
        self._plan = []                          # 本场偷卡计划
        self._plan_idx = 0                       # 已偷次数
        self._clicked = []                       # 已偷过的怪物坐标
        self._steal_targets = []                 # 偷卡目标
        self._matched_targets = []               # 匹配到的怪物
        self._matched_names = []                 # 命中的模板名
        self._all_monsters = []                  # 全部怪物模板
        self._tou_targets = []                   # 偷窃目标模板

        self._force_run_map = False       # 酒肆休息完成后立即跑图

        self.total_runtime = 0.0          # 累计运行时长（秒），跨重启保留

        self.start_time = 0



        # 初始化日志文件并写入启动记录

        try:

            init_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.log_file, "a", encoding="utf-8") as f:

                f.write(f"\n{'='*60}\n")

                f.write(f"[{init_ts}] 引擎初始化 - 设备: {self.device_id} ({self.serial})\n")

                f.write(f"[{init_ts}] 日志文件: {self.log_file}\n")

                f.write(f"{'='*60}\n")

                f.flush()

        except Exception:

            pass



    def _log(self, msg, also_console=True):

        """输出日志到队列和文件，格式: [设备名] 时间 消息"""

        ts = datetime.now().strftime("%H:%M:%S")

        log_msg = f"[{self.device_id}] {msg}"

        # 发送到UI队列

        if also_console:

            self.log.put(f"[{ts}] {log_msg}")

        # 保存到设备专属日志文件

        self._write_to_log_file(ts, msg)

    def _write_to_log_file(self, timestamp, msg):

        """写入日志到文件，支持文件大小自动轮转"""

        try:

            # 按日期文件夹存储：logs/YYYY-MM-DD/{device_id}.log（跨天自动切换）
            self.log_file = self._daily_log_file()

            # 检查日志文件大小，超过10MB自动轮转

            max_size = 10 * 1024 * 1024  # 10MB

            if os.path.exists(self.log_file):

                file_size = os.path.getsize(self.log_file)

                if file_size > max_size:

                    # 重命名旧文件

                    base, ext = os.path.splitext(self.log_file)

                    old_file = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"

                    os.rename(self.log_file, old_file)

            # 写入新日志

            with open(self.log_file, "a", encoding="utf-8") as f:

                f.write(f"[{timestamp}] {msg}\n")

                f.flush()  # 立即刷新到磁盘

        except Exception as e:

            # 日志写入失败不影响主流程，但打印到控制台

            try:

                print(f"日志写入失败: {e}")

            except:

                pass

    def _daily_log_file(self):
        """返回当天日期目录下的日志路径：logs/YYYY-MM-DD/{device_id}.log。"""
        day = datetime.now().strftime("%Y-%m-%d")
        day_dir = os.path.join(self.log_dir, day)
        if self._log_day_dir != day_dir:
            self._log_day_dir = day_dir
            os.makedirs(day_dir, exist_ok=True)
        return os.path.join(day_dir, f"{self.device_id}.log")



    # ========== 截图 ==========

    def get_frame(self):

        if self.client is None:

            f = adb_screencap(self.serial)

        else:

            with self._frame_lock:

                f = self.client.last_frame

                f = f.copy() if f is not None else None

        # 统一归一化到 800x448 流坐标：20:9 设备（如 2400x1080）视频流是 800x360，
        # 而引擎所有像素检测/模板匹配/坐标都按 800x448 语义（血量条、头像、四小人 ROI 等）。
        # 不归一化的话 HP/MP 固定行扫不到 → 四小人预筛恒误判为 True。
        if f is not None:

            fh, fw = f.shape[:2]

            if fh > fw:

                f = cv2.rotate(f, cv2.ROTATE_90_CLOCKWISE)

                fh, fw = f.shape[:2]

            if (fw, fh) != (800, 448):

                f = cv2.resize(f, (800, 448), interpolation=cv2.INTER_LINEAR)

        return f



    def tap(self, x, y, offset=True):

        if offset:

            x += random.randint(-3, 3)

            y += random.randint(-3, 3)

        adb_tap(self.serial, int(x * self.scale_x), int(y * self.scale_y))

    # ========== 小霸王三功能（xbw_features）接入 ==========

    def _wire_xbw_backend(self):
        """把 xbw_features 的取帧/点击/日志桥接到本引擎。"""
        if self._xbw_wired:
            return
        try:
            from xbw_features import backend as _xbw
            _xbw.setup(
                deviceId=self.serial,
                screencap_fn=lambda deviceId: self.get_frame(),
                tap_fn=lambda deviceId, x, y, is_double=False: self._xbw_tap(x, y, is_double),
                log_fn=lambda deviceId, msg: self._log(f"[小霸王] {msg}"),
                cache_seconds=0.2,
            )
            self._xbw_wired = True
            self._log("✅ 已接入小霸王三功能（本地四小人 / 真实切场 / 背包环卡计数）")
        except Exception as e:
            self._log(f"⚠️ 小霸王功能包接入失败: {e}")

    def _xbw_tap(self, x, y, is_double=False):
        """800x448 流坐标 -> 设备坐标（独立于引擎当前 stream 分辨率换算）。"""
        dw = int(self.stream_w * self.scale_x)
        dh = int(self.stream_h * self.scale_y)
        tx = int(x * dw / 800)
        ty = int(y * dh / 448)
        if is_double:
            adb_tap(self.serial, tx, ty)
            time.sleep(random.uniform(0.05, 0.1))
        adb_tap(self.serial, tx, ty)

    def _detect_current_map(self):
        """OCR 检测当前实际场景名（导航后到达验证用）；失败返回 None"""
        try:
            if self.ocr_engine is None:
                self.init_ocr()
            if self.ocr_engine is None:
                return None
            f = self.get_frame()
            if f is None:
                return None
            ocr_name, _, _ = self.detect_map_coord(f)
            if not ocr_name:
                return None
            from scene_detector import detect_position as _detect
            detected, _ = _detect(self.serial, f, self.scale_x, self.scale_y, ocr_name)
            return detected
        except Exception as e:
            self._log(f"  ⚠️ 当前场景检测失败: {e}")
            return None

    def _do_real_scene_switch(self, target_map):
        """
        真实导航到目标场景：
        优先用 场景切换.py 的 SceneSwitcher（每段跑图有 OCR 到达验证、失败明确返回）；
        失败/未覆盖时回退小霸王 goToMapAction（导航后 OCR 验证，未到达重试一次）。
        """
        if not self.cfg.get("use_real_scene_switch", True):
            return False

        # ===== 方案1：场景切换引擎 SceneSwitcher（推荐，带到达验证 + 每步反馈） =====
        try:
            from 场景切换 import SceneSwitcher, SceneSwitchCombatAbort
            self._log(f"  🗺️ 场景切换引擎导航到 {target_map} ...")
            sw = SceneSwitcher(self.serial,
                               log_fn=lambda m: self._log(f"  [切场] {m}"),
                               combat_check=self._check_in_combat,
                               client=self.client,          # 复用引擎 scrcpy 流帧（免 ADB 截图）
                               frame_lock=self._frame_lock)
            if not sw.connect():
                self._log("  ⚠️ 场景切换引擎连接失败，回退小霸王导航")
            else:
                try:
                    if sw.switch_scene(target_map):
                        self._log(f"  ✅ 已到达 {target_map}（场景切换引擎确认）")
                        time.sleep(1)
                        return True
                except SceneSwitchCombatAbort:
                    self._log("  ⚔️ 切场途中检测到战斗，中止切场（保留切场请求，稍后重试）")
                    return False
                self._log("  ⚠️ 场景切换引擎导航失败，回退小霸王导航")
        except Exception as e:
            self._log(f"  ⚠️ 场景切换引擎异常({e})，回退小霸王导航")

        # ===== 方案2：小霸王 goToMapAction（兜底，导航后 OCR 验证到达） =====
        if not self.coord_enabled:
            # 坐标检测关闭：无法 OCR 验证，仅执行导航流程
            try:
                from xbw_features import go_to_chang_jing
                if self._check_in_combat():
                    self._log("  ⚔️ 导航前检测到战斗，中止切场")
                    return False
                self._log(f"  🗺️ 小霸王导航到 {target_map} ...")
                go_to_chang_jing(self.serial, target_map)
                self._log(f"  ✅ 已执行导航到 {target_map}（坐标检测关闭，无法验证到达）")
                time.sleep(1)
                return True
            except Exception as e:
                self._log(f"  ⚠️ 真实切场失败({e})，回退本地切场")
                return False
        try:
            from xbw_features import go_to_chang_jing
            for _try in range(2):
                if self._check_in_combat():
                    self._log("  ⚔️ 导航前检测到战斗，中止切场")
                    return False
                self._log(f"  🗺️ 小霸王导航到 {target_map}（第{_try+1}次）...")
                go_to_chang_jing(self.serial, target_map)
                time.sleep(1.5)
                if self._check_in_combat():
                    self._log("  ⚔️ 导航后检测到战斗，中止切场")
                    return False
                detected = self._detect_current_map()
                if detected and _match_scene_name(detected, target_map):
                    self._log(f"  ✅ 已到达 {target_map}（OCR 确认）")
                    return True
                self._log(f"  ⚠️ 导航后仍在 {detected or '未知场景'}，未到达 {target_map}"
                          + ("，重试一次" if _try == 0 else ""))
            self._log(f"  ⚠️ 两次导航后仍未到达 {target_map}，回退本地切场（仅切换模板）")
            return False
        except Exception as e:
            self._log(f"  ⚠️ 真实切场失败({e})，回退本地切场")
            return False

    def _check_backpack_counts(self, scene):
        """
        小霸王“偷偷检查背包”：20 格快照 diff 新增槽位 ->
        模板匹配“装备条件/怪物卡片”累计环/卡计数；达标时切场请求在下次循环即触发。
        """
        ok = False
        try:
            from xbw_features import check_backpack_and_maybe_switch
            rings_req = scene.get("rings", "无要求")
            cards_req = scene.get("cards", "无要求")
            self._log(f"  🎒 背包检查：当前环 {self._huan_count} / 卡 {self._card_count}"
                      f"（要求 {rings_req} / {cards_req}）")
            old_huan = self._huan_count
            old_card = self._card_count
            self._pkg_snapshot, self._huan_count, self._card_count, reason, ok = \
                check_backpack_and_maybe_switch(
                    self.serial, rings_req, cards_req,
                    self._huan_count, self._card_count, self._pkg_snapshot)
            # 同步累加到当日计数：切场景/重启不清零，跨统计日由引擎/统计文件重置
            self._daily_huan_count += max(0, self._huan_count - old_huan)
            self._daily_card_count += max(0, self._card_count - old_card)
            self._log(f"  🎒 检查后：环 {self._huan_count} / 卡 {self._card_count}")
            if reason:
                self._log(f"  🎉 {reason}，准备切换场景")
                # 立即置位（不依赖下一次背包检查），主循环下一次迭代即执行切场；
                # 关闭"真实场景导航"时不置位（不切场，且不挡住后续背包检查）
                if self.cfg.get("use_real_scene_switch", True):
                    self._scene_switch_requested = True
            if not ok:
                self._log("  ⚠️ 背包未成功打开（可能被弹窗/窗口挡住），8秒后重试")
        except Exception as e:
            self._log(f"  ⚠️ 背包检查异常: {e}")
        finally:
            self._pkg_check_t = time.time()
            if ok:
                try:
                    from xbw_features import next_check_interval as _nci
                    self._pkg_interval = _nci()
                except Exception:
                    self._pkg_interval = 600
            else:
                self._pkg_interval = 8.0   # 打开失败/异常：8秒后重试，避免长时间不检查


    def get_scene_history(self):
        """
        获取场景历史记录（包括当前场景）
        返回格式：[{name: 场景名, cards: 卡片数, rings: 环数, duration: 时长(秒)}]
        """
        result = []
        # 历史场景
        for record in self._scene_history:
            result.append({
                "name": record["name"],
                "cards": record["cards"],
                "rings": record["rings"],
                "duration": record["duration"],
            })
        # 当前场景
        if self.running and hasattr(self, '_current_scene_start_time'):
            current_duration = time.time() - self._current_scene_start_time
            current_map = self.cfg.get("map", "")
            if current_map:
                result.append({
                    "name": current_map,
                    "cards": self._card_count,
                    "rings": self._huan_count,
                    "duration": current_duration,
                })
        return result

    def _save_scene_history(self):
        """保存场景历史到文件（按天记录）"""
        try:
            # 检查是否跨统计日（每天 5:00 为界），跨天则切换到新文件
            current_date = stats_day()
            if current_date != self._scene_history_date:
                self._scene_history_date = current_date
                self._scene_history_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "logs",
                    f"scene_history_{self.serial}_{current_date}.json"
                )
                # 清空旧历史（因为已经在旧文件中保存过了）
                self._scene_history = []

            os.makedirs(os.path.dirname(self._scene_history_file), exist_ok=True)
            with open(self._scene_history_file, "w", encoding="utf-8") as f:
                json.dump(self._scene_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"⚠️ 保存场景历史失败: {e}")

    def _save_current_scene_history(self):
        """流程结束时记录当前场景到历史（手动停止/达标停止/异常退出都会走这里），
        避免"在小西天跑了3个环，手动换场景后小西天记录丢失"的问题。"""
        try:
            map_name = self.cfg.get("map", "")
            if not map_name:
                return
            start_time = getattr(self, "_current_scene_start_time", 0) or 0
            # 刚启动（<60秒）且无任何环/卡产出则视为"没跑起来"，不记录，避免空记录刷屏
            if start_time > 0 and time.time() - start_time < 60 and not self._huan_count and not self._card_count:
                return
            # 避免重复记录同一条当前场景（切场块已记录过时）
            if self._scene_history and self._scene_history[-1].get("name") == map_name \
                    and abs((self._scene_history[-1].get("start_time") or 0) - start_time) < 1:
                return
            duration = max(0.0, time.time() - start_time) if start_time > 0 else 0.0
            self._scene_history.append({
                "name": map_name,
                "cards": self._card_count,
                "rings": self._huan_count,
                "duration": duration,
                "start_time": start_time,
            })
            self._save_scene_history()
            self._log(f"📝 流程结束，已记录当前场景 {map_name} 到历史（环 {self._huan_count} / 卡 {self._card_count}）")
        except Exception as e:
            self._log(f"⚠️ 记录当前场景历史失败: {e}")

    def _load_scene_history(self):
        """从文件加载场景历史（只加载当天的）"""
        try:
            if os.path.exists(self._scene_history_file):
                with open(self._scene_history_file, "r", encoding="utf-8") as f:
                    self._scene_history = json.load(f)
                self._log(f"📂 已加载 {len(self._scene_history)} 条今日场景历史记录")
        except Exception as e:
            self._log(f"⚠️ 加载场景历史失败: {e}")
            self._scene_history = []


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

            "左下角返回", "菜单-指引", "底部菜单-法术",

        ]

        combat_templates = [

            "PK-妙手空空技能", "PK-自动按钮", "PK-取消自动战斗",

            "重置回合数", "PK-逃跑", "PK-防御", "PK-撤销战斗操作", "PK-捕捉", "PK-四小人弹窗",

            "PK-对面宝宝文字蓝色", "PK-对面宝宝文字红色",

            "PK-护佑文字", "PK-暴击文字",

        ]

        # 加载所有场景的怪物模板（支持跨场景切换）

        from target_mapping import SCENE_MAPPING as _SM

        _seen = set()

        for _area, _cfg in _SM.items():

            for _name in _cfg.get("tou_targets", []) + _cfg.get("jineng_targets", []):

                if _name not in _seen:

                    _seen.add(_name)

                    combat_templates.append(_name)



        for name in ui_templates + combat_templates:

            tmpl = load_template(name)

            if tmpl is not None:

                self.templates[name] = tmpl



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

                self._log(f"  💊 秘制 (气血={hp:.0f}% 魔法={mp:.0f}%)")

                self.press_key("秘制")

                self.hp_item_used_time = now

                time.sleep(0.5)

            return



        if self.cfg.get("hp_enabled"):

            th = self.cfg.get("hp_threshold", 30)

            if hp < th and now - self.hp_item_used_time > 8:

                item = self.cfg.get("hp_item", "红碗")

                self._log(f"  ❤️ 气血={hp:.0f}% < {th}%，使用 {item}")

                self.press_key(item)

                self.hp_item_used_time = now

                time.sleep(0.5)



        if self.cfg.get("mp_enabled"):

            th = self.cfg.get("mp_threshold", 20)

            if mp < th and now - self.mp_item_used_time > 8:

                item = self.cfg.get("mp_item", "蓝碗")

                self._log(f"  💙 魔法={mp:.0f}% < {th}%，使用 {item}")

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

            if not self.running:

                return

            f = self.get_frame()

            if f is not None and not self.is_in_pk(f):

                break

            time.sleep(0.5)



        # 关闭弹窗确保干净

        self.close_pop(is_one_time=True)

        time.sleep(0.3)



        # 第1步：找酒肆技能（直接可见；找不到先点底部“法术”展开技能面板再找）
        found_skill = False
        fa_shu_clicked = False
        for _round in range(2):
            for attempt in range(5):
                if not self.running:
                    return
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
            if found_skill:
                break
            if _round == 0:
                # 主界面找不到酒肆：先点底部“法术”按钮展开技能面板，再重试
                self._log("  🔍 未直接找到酒肆技能，点击底部法术按钮后重试")
                fs = None
                for attempt in range(3):
                    f = self.get_frame()
                    if f is None:
                        time.sleep(0.3)
                        continue
                    fs = self.find(f, "底部菜单-法术", threshold=0.70)
                    if fs:
                        break
                    time.sleep(0.3)
                if fs is None:
                    self._log("  ❌ 未找到底部法术按钮，跳过恢复")
                    return
                self._log(f"  ✅ 点击底部法术按钮 ({fs[0]},{fs[1]})")
                self.tap(fs[0], fs[1])
                fa_shu_clicked = True
                time.sleep(0.5)

        if not found_skill:
            self._log("  ❌ 未找到酒肆技能，跳过恢复")
            return



        time.sleep(0.5)



        # 第2步：找酒肆休息

        found_rest = False

        for attempt in range(8):

            if not self.running:

                return

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

        self.jiusi_used_time = time.time()
        self._log("  🍶 酒肆恢复完成")
        # 点过底部法术展开技能面板的：顺手关闭，避免遮挡后续跑图/操作
        if fa_shu_clicked:
            self.close_pop(is_one_time=True)
            time.sleep(0.3)
        # 休息完成后，0.3秒后直接打开地图跑图（跳过坐标停止检测）
        self._force_run_map = True



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



        # 调试：在检测到的技能位置截图标注

        time.sleep(0.05)

        f = self.get_frame()

        if f is None:

            return



        hp, mp, bb, no_bb = self.detect_hp_mp_bb(f)



        need_heal = hp < jiusi_hp or mp < jiusi_mp

        need_bb_heal = (not no_bb) and bb < jiusi_bb



        msg_parts = []

        if hp < jiusi_hp:

            msg_parts.append(f"气血:{hp:.0f}% < {jiusi_hp}%")

        if mp < jiusi_mp:

            msg_parts.append(f"魔法:{mp:.0f}% < {jiusi_mp}%")

        if need_bb_heal:

            msg_parts.append(f"BB:{bb:.0f}% < {jiusi_bb}%")



        if not msg_parts:

            self._log(f"  ✅ 血量正常 (气血:{hp:.0f}% 魔法:{mp:.0f}% BB:{'--' if no_bb else f'{bb:.0f}%'})")

            return



        self._log(f"  🔔 触发酒肆恢复: {', '.join(msg_parts)}")

        self.do_jiu_si_heal()



    def _do_loyalty_recovery(self):
        """诚度恢复流程：暂停主循环，独立连接执行，支持停止信号"""
        try:
            from 工具 import run_loyalty_recovery
            self._loyalty_stop_event.clear()
            self._paused = True
            self._log("  🛠️ 启动诚度恢复工具(暂停主循环)...")
            try:
                # 传入引擎已知场景：避免恢复流程 OCR 识别失败时因"未识别到地图"跳过
                #（龙窟五层等场景 OCR 偶尔识别不出/识别成变体时，引擎仍知道当前在哪）
                known_map = self.cfg.get("map", "") or self.last_map_name or ""
                run_loyalty_recovery(self.serial, map_name=known_map,
                                     stop_event=self._loyalty_stop_event)
            finally:
                self._paused = False
            self._log("  ✅ 诚度恢复流程完成")
        except ImportError as e:
            self._log(f"  ❌ 导入工具模块失败: {e}")
        except Exception as e:
            self._log(f"  ❌ 诚度恢复执行异常: {e}")

    def init_device_scale(self):

        try:

            r = sp.run([_ADB_EXE, "-s", self.serial, "shell", "dumpsys", "window", "displays"],

                       capture_output=True, text=True, timeout=5, creationflags=sp.CREATE_NO_WINDOW)

            m = re.search(r"cur=(\d+)x(\d+)", r.stdout)

            if not m:

                m = re.search(r"app=(\d+)x(\d+)", r.stdout)

            if m:

                dw, dh = int(m.group(1)), int(m.group(2))

                # get_frame 固定输出 800x448，流坐标换算基准即 800x448
                self.scale_x = dw / 800

                self.scale_y = dh / 448

                self._log(f"设备: {dw}x{dh}  缩放: {self.scale_x:.2f}x{self.scale_y:.2f}")

                return

        except Exception as e:

            self._log(f"分辨率获取失败: {e}")

        self.scale_x = 1920 / 800

        self.scale_y = 1080 / 448



    def _get_foreground_package(self):
        """ADB 查询当前前台应用包名；失败返回 None。"""
        try:
            r = sp.run([_ADB_EXE, "-s", self.serial, "shell", "dumpsys", "window"],
                       capture_output=True, text=True, timeout=5, creationflags=sp.CREATE_NO_WINDOW)
            for line in r.stdout.splitlines():
                if "mCurrentFocus" in line or "mFocusedApp" in line:
                    # 形如 mCurrentFocus=Window{... u0 com.xxx.yyy/com.xxx.yyy.Activity}
                    m = re.search(r'([a-zA-Z][\w.]*)/', line)
                    if m:
                        return m.group(1)
        except Exception:
            pass
        return None

    def _is_game_foreground(self):
        """游戏是否在前台（四小人检测门禁：手机主页/其它app在前台时不判四小人，避免图灵云扣分）。"""
        pkg = getattr(self, "_game_package", None)
        if pkg is None:
            return True  # 未记录包名时不拦截，保持原行为
        return self._get_foreground_package() == pkg

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

                    self._log(f"✅ ADB 截图 ({f.shape[1]}x{f.shape[0]})")

                else:

                    return False

            else:

                raw_h, raw_w = self.client.last_frame.shape[:2]

                self._log(f"✅ 视频流 ({raw_w}x{raw_h})")

            # 统一流坐标语义为 800x448（get_frame 归一化输出；20:9 设备原始流是 800x360）
            self.stream_w, self.stream_h = 800, 448

            self.init_device_scale()

            # 记录游戏包名（四小人检测门禁用：只在游戏前台时判四小人）
            self._game_package = self._get_foreground_package()
            self._log(f"📱 游戏包名: {self._game_package}")

            return True

        except Exception as e:

            self._log(f"pyscrcpy 失败: {e}")

            self.client = None

            f = adb_screencap(self.serial)

            if f is not None:

                self._log(f"✅ ADB 截图 ({f.shape[1]}x{f.shape[0]})")

                self.stream_w, self.stream_h = 800, 448

                self.init_device_scale()

                self._game_package = self._get_foreground_package()

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
        # 连续非战斗/截图失败容忍窗口：点空后取消技能选择等瞬间画面可能短暂识别不到
        # 战斗，若第一帧就返回 None，调用方会跳过击杀直接点自动（表现为"点空后没有击杀"）。
        _non_pk_since = None
        _non_pk_grace = 1.5

        # use cached skill position from detection phase
        if self.last_skill is not None:
            frame = self.get_frame()
            if frame is not None:
                ms = self.find(frame, "PK-妙手空空技能", threshold=0.60)
                if ms:
                    self.last_skill = ms
                    return ms
            # cache miss, fall through to polling

        while time.time() - start < timeout:

            if not self.running:

                return None

            frame = self.get_frame()

            if frame is None or not self.is_in_pk(frame):

                # 短暂容忍：连续 1.5 秒非战斗才判定战斗结束/截图失败
                if _non_pk_since is None:
                    _non_pk_since = time.time()
                elif time.time() - _non_pk_since >= _non_pk_grace:
                    return None
                time.sleep(0.3)
                continue

            _non_pk_since = None  # 恢复战斗帧：清零连续非战斗计时
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

        # 多帧容错：战斗中被特效/动画短暂遮挡 HUD 时，单帧 is_in_pk 会误判 False，
        # 这里连续取几帧，只要有一帧仍是战斗态就判“仍在战斗”，避免提前 return 丢操作。
        for _ in range(3):

            frame = self.get_frame()

            if frame is not None and self.is_in_pk(frame):

                return True

            time.sleep(0.15)

        return False



    def _tap_defend(self, log_label="", timeout=3.0, check_wait=0.5, max_attempts=3, require_skill_hidden=False):

        """点完怪物后调用：在 timeout 秒内持续从实时流找防御按钮，找到马上点；
        点完按钮消失即成功；超时仍未找到则跳过（如宝宝未参战/没寿命）。
        require_skill_hidden=True 时只点宝宝面板的防御：防御按钮与妙手空空技能
        图标同屏说明这是人物操作栏（宝宝面板只在人物指令提交、技能图标消失后
        才出现），此时点防御会把人物改成防御，跳过不点。
        返回 True=成功点防御，False=按钮始终点不中，'missing'=超时未找到。"""

        start = time.time()

        taps = 0

        _char_bar_warned = False

        while True:

            if not self.running:

                return False

            frame = self.get_frame()

            defend = self.find(frame, "PK-防御") if frame is not None else None

            if defend is not None and require_skill_hidden:

                if self.find(frame, "PK-妙手空空技能", threshold=0.60) is not None:

                    if not _char_bar_warned:

                        _char_bar_warned = True

                        self._log("  🚫 防御按钮与技能图标同屏（人物操作栏），不点人物防御")

                    defend = None

            if defend is not None:

                self.tap(defend[0], defend[1])

                taps += 1

                self._log(f"  🎯 {log_label}点防御 ({defend[0]},{defend[1]}) 第{taps}次")

                time.sleep(check_wait)

                # 点完验证：按钮已消失即认为点中成功

                frame2 = self.get_frame()

                if frame2 is not None and self.find(frame2, "PK-防御") is None:

                    self._log(f"  ✅ {log_label}防御点击成功，按钮已消失")

                    return True

                if taps >= max_attempts:

                    self._log(f"  ⚠️ {log_label}防御按钮点击{max_attempts}次后仍存在，未确认成功")

                    return False

                continue

            if taps > 0:

                # 上一轮点过，此刻按钮已消失（last_frame 可能延迟一帧）→ 成功

                self._log(f"  ✅ {log_label}防御点击成功，按钮已消失")

                return True

            if time.time() - start > timeout:

                self._log(f"  ⚠️ {timeout:.0f}秒内未识别到{log_label}防御按钮，跳过")

                return "missing"

            time.sleep(0.05)  # 实时流高频轮询，直到面板出现





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



    def _scan_name_center(self, frame, mx, my):
        """扫描宝宝名字文字的实际水平范围，返回名字中心 x。
        模板匹配点可能是名字的一部分（名字长时匹配点偏右），
        名字中心直直上去才是怪物中心，点击才准确。"""
        try:
            h, w = frame.shape[:2]
            # 在标记点所在行附近（上下各 8px）扫描亮色/蓝色/红色文字像素
            y0 = max(0, my - 8)
            y1 = min(h, my + 8)
            x0 = max(0, mx - 90)
            x1 = min(w, mx + 90)
            # 逐列统计文字像素（蓝色文字 B高 或 亮白 或 红色 R高）
            cols = []
            for x in range(x0, x1):
                cnt = 0
                for y in range(y0, y1):
                    b, g, r = frame[y, x]
                    b, g, r = int(b), int(g), int(r)
                    if (b > 100 and b > r + 40) or (r > 150 and g > 150 and b > 150) or (r > 130 and r > b + 50):
                        cnt += 1
                if cnt >= 2:  # 该列有文字
                    cols.append(x)
            if len(cols) >= 5:
                return (cols[0] + cols[-1]) // 2
        except Exception:
            pass
        return mx  # 扫描失败回退到模板匹配点

    def _try_capture_bb(self, frame, matched_targets, max_rounds=None, scan_retries=0):
        """对面宝宝/变异召唤兽检测 + 捕捉。优先捕捉变异蛟龙/变异地狱战神；
        do_combat 开头和第四回合攻击前各调用一次；不滑动。
        返回 (是否捕捉过宝宝, 捕捉回合数)"""

        if frame is None:
            return False, 0

        # 1) 优先：识别变异召唤兽（变异蛟龙/变异地狱战神），识别到直接作为捕捉目标。
        #    变异模板很小（~17x15），0.70 阈值会把普通怪身体区域误判为变异
        #    （实测普通怪画面最高匹配 0.65~0.78，且位置与普通怪重叠），
        #    因此阈值提到 0.80 过滤模糊匹配，并要求变异位置不与已检测到的
        #    普通怪物重叠（变异怪与普通怪不同位置，重叠即普通怪的误匹配）。
        normal_pts = [(p[0], p[1]) for p in matched_targets]
        mutant_pts = []
        for tmpl in ("PK-召唤兽-变异蛟龙", "PK-召唤兽-变异地狱战神"):
            hits = self._find_all(frame, tmpl, threshold=0.80, roi=COMBAT_ROI)
            for hx, hy, hc in hits:
                # 变异位置与任意普通怪重叠（距离<25px）→ 判为普通怪的误匹配
                if any(abs(hx-nx)**2 + abs(hy-ny)**2 < 625 for nx, ny in normal_pts):
                    self._log(f"  ⚠️ 变异模板与普通怪重叠 ({hx},{hy}) conf={hc:.2f}，忽略")
                    continue
                mutant_pts.append((hx, hy, hc))
        dedup_m = []
        for t in sorted(mutant_pts, key=lambda x: x[2], reverse=True):
            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup_m):
                dedup_m.append(t)
        if self.cfg.get("capture_bb_enabled", False) and dedup_m:
            self._log(f"  🎣 识别到变异召唤兽 {len(dedup_m)} 个，优先捕捉")
            for t in dedup_m:
                self._log(f"      变异位置 ({t[0]},{t[1]}) conf={t[2]:.2f}")
            # 变异目标：点击位置与验证位置都是变异坐标
            return self._run_capture_loop([(p[0], p[1], p[0], p[1]) for p in dedup_m], max_rounds)

        # 2) 对面宝宝文字流程（原有）
        bb_markers = []

        # 先检测蓝色文字（直接可见的）
        cur_blue = self._find_all(frame, "PK-对面宝宝文字蓝色", threshold=0.80, roi=COMBAT_ROI)
        if cur_blue:
            bb_markers.extend(cur_blue)

        # 前排怪物可能遮挡后排名字（不做滑动，多刷新几帧再查，等名字渲染/遮挡变化）
        if len(matched_targets) >= 5:
            self._log("  👆 检测到前排怪物，后排名字可能被遮挡，多帧重扫")
            for _scan in range(scan_retries + 1):
                if not self._check_in_combat():
                    break
                if _scan == 0:
                    frame2 = self.get_frame()
                else:
                    time.sleep(0.5)
                    frame2 = self.get_frame()
                if frame2 is None:
                    continue
                cur_red = self._find_all(frame2, "PK-对面宝宝文字红色", threshold=0.80, roi=COMBAT_ROI)
                if cur_red:
                    bb_markers.extend(cur_red)
                cur_blue2 = self._find_all(frame2, "PK-对面宝宝文字蓝色", threshold=0.80, roi=COMBAT_ROI)
                if cur_blue2:
                    bb_markers.extend(cur_blue2)
                if bb_markers:
                    break
        else:
            cur_red = self._find_all(frame, "PK-对面宝宝文字红色", threshold=0.80, roi=COMBAT_ROI)
            if cur_red:
                bb_markers.extend(cur_red)

        # 去重
        dedup_bb = []
        if bb_markers:
            for t in sorted(bb_markers, key=lambda x: x[2], reverse=True):
                if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup_bb):
                    dedup_bb.append(t)
            self._log(f"  🐶🔴 检测到 {len(dedup_bb)} 个对面宝宝标记")
            for t in dedup_bb:
                self._log(f"      宝宝标记 ({t[0]},{t[1]}) conf={t[2]:.2f}")

        # 获取当前场景的黑名单配置
        map_name = self.last_map_name or self.cfg.get("map", "")
        blacklist = self.cfg.get("capture_bb_blacklist", {}).get(map_name, [])

        # 检测黑名单中的宝宝名字，过滤掉不能捕捉的宝宝
        filtered_bb_markers = []
        if blacklist and dedup_bb:
            self._log(f"  🔍 检查黑名单宝宝: {blacklist}")
            for bb_marker in dedup_bb:
                mx, my = bb_marker[0], bb_marker[1]
                is_blacklisted = False

                # 检查是否匹配黑名单中的任一宝宝
                for bb_name in blacklist:
                    tmpl_name = f"PK-召唤兽-{bb_name}"
                    hits = self._find_all(frame, tmpl_name, threshold=0.75, roi=COMBAT_ROI)
                    if hits:
                        # 检查黑名单宝宝位置是否与当前宝宝标记位置相近
                        for hx, hy, hc in hits:
                            # 宝宝名字应该在宝宝文字标记附近（横向偏移不超过80px）
                            if abs(hx - mx) < 80 and abs(hy - my) < 50:
                                self._log(f"  🚫 识别到黑名单宝宝: {bb_name} 位置({hx},{hy})，跳过捕捉")
                                is_blacklisted = True
                                break
                        if is_blacklisted:
                            break

                if not is_blacklisted:
                    filtered_bb_markers.append(bb_marker)

            # 替换为过滤后的列表
            dedup_bb = filtered_bb_markers
            if not dedup_bb:
                self._log("  ℹ️ 所有宝宝都在黑名单中，跳过捕捉")
                return False, 0
            else:
                self._log(f"  ✅ 过滤后剩余 {len(dedup_bb)} 个可捕捉宝宝")

        if not (self.cfg.get("capture_bb_enabled", False) and dedup_bb):
            return False, 0

        # 将宝宝文字标记位置转换为对应怪物的点击坐标
        capture_targets = []
        for marker in dedup_bb:
            mx, my = marker[0], marker[1]
            # 模板匹配点可能是名字的一部分（名字长时匹配点偏右），
            # 扫描名字实际水平范围取中心：名字中心直直上去才是怪物中心
            name_cx = self._scan_name_center(frame, mx, my)
            best_monster = None
            best_score = 999999
            for mt in matched_targets:
                dx = abs(mt[0] - name_cx)
                dy = my - mt[1]
                if 10 < dy < 100 and dx < 60:
                    score = dx * 2 + abs(dy - 45)
                    if score < best_score:
                        best_score = score
                        best_monster = (mt[0], mt[1])
            if best_monster:
                # (点击x, 点击y, 验证标记x, 验证标记y)：点击怪物位置，验证用宝宝文字标记
                capture_targets.append((best_monster[0], best_monster[1], name_cx, my))
                self._log(f"  🐶 宝宝文字中心({name_cx},{my}) -> 匹配怪物({best_monster[0]},{best_monster[1]})")
            else:
                # 未匹配到怪物：怪物中心 = 名字中心直直上去 55px（用户实测校准），
                # 验证仍用名字中心标记
                fallback = (name_cx, my - 55)
                capture_targets.append((fallback[0], fallback[1], name_cx, my))
                self._log(f"  🐶 宝宝文字中心({name_cx},{my}) -> 未匹配到怪物，估算({fallback[0]},{fallback[1]})")

        if not capture_targets:
            return False, 0

        self._log(f"  🎣 捕捉模式已开启，目标 {len(capture_targets)} 个")
        return self._run_capture_loop(capture_targets, max_rounds)



    def _run_capture_loop(self, capture_targets, max_rounds=None):
        """捕捉循环：每回合点捕捉按钮(539,403) + 点目标 + 点防御，最多 max_rounds 回合（默认8）。
        每回合重新检测变异/对面宝宝标记是否还在。
        捕捉后等待妙手空空技能出现，并点击防御按钮。
        capture_targets 元素：4 元组 (点击x, 点击y, 验证标记x, 验证标记y)。
        点击用怪物/变异坐标，验证用宝宝文字/变异标记坐标（两者可能不同）。
        返回：(是否捕捉过宝宝, 回合数)"""
        MAX_CAPTURE_ROUNDS = max_rounds if max_rounds is not None else 8
        captured_count = 0
        for cap_round in range(MAX_CAPTURE_ROUNDS):
            if not self._check_in_combat():
                break
            skill_pos = self._wait_for_skill(timeout=10.0)
            if skill_pos is None:
                self._log("  ⏳ 等待回合超时，停止捕捉")
                break
            # 每回合重新检测变异/对面宝宝标记
            frame_check = self.get_frame()
            current_bb = []
            if frame_check is not None:
                for tmpl in ("PK-召唤兽-变异蛟龙", "PK-召唤兽-变异地狱战神",
                             "PK-对面宝宝文字蓝色", "PK-对面宝宝文字红色"):
                    # 变异模板阈值 0.80（同 _try_capture_bb，0.70 会误匹配普通怪）
                    hits = self._find_all(frame_check, tmpl, threshold=0.80, roi=COMBAT_ROI)
                    current_bb.extend(hits)
            still_there = []
            for ct in capture_targets:
                if len(ct) == 4:
                    click_pos = (ct[0], ct[1])
                    verify_pos = (ct[2], ct[3])
                else:
                    click_pos = (ct[0], ct[1])
                    verify_pos = click_pos
                for h in current_bb:
                    # 用验证位置与当前检测到的标记比对（同语义坐标）
                    if abs(h[0]-verify_pos[0])**2 + abs(h[1]-verify_pos[1])**2 < 2500:
                        still_there.append(click_pos)
                        break
            if not still_there:
                self._log(f"  🎣 第{cap_round+1}回合：目标已不在场，停止捕捉")
                break
            for st in still_there:
                self.tap(539, 403)  # 点击捕捉按钮
                time.sleep(0.3)
                self.tap(st[0], st[1])  # 点击目标
                self._log(f"  🎣 第{cap_round+1}回合 捕捉 ({st[0]},{st[1]})")
                captured_count += 1
                # 捕捉后点击防御按钮
                defend_status = self._tap_defend(log_label="捕捉后防御", timeout=2.5, require_skill_hidden=True)
                if defend_status == "missing":
                    if self.has_no_bb:
                        self._log("  ⚠️ 未识别到宝宝防御按钮（画面判定未带宝宝），跳过")
                    else:
                        self._defend_miss_streak += 1
                        self._log(f"  ⚠️ 未识别到宝宝防御按钮（第{self._defend_miss_streak}次），跳过")
                    self._battle_defend_attempted = True
                else:
                    self._defend_miss_streak = 0
                    self._battle_defend_attempted = True
                    self._battle_defend_ok = True
                time.sleep(0.2)
        if captured_count > 0:
            self._log(f"  🎣 捕捉完成，共捕捉 {captured_count} 次")
        else:
            self._log("  🎣 未执行捕捉操作")
        return captured_count > 0, min(captured_count, MAX_CAPTURE_ROUNDS)



    def _match_templates_map(self, frame, template_names, threshold=0.80, roi=None):
        """一次性匹配多个模板，返回 {模板名: [(x, y, conf), ...]}。
        进入战斗后只取一帧、只匹配一遍，各环节从结果里按模板名筛选，
        避免 matched/steal 等各自重复 _find_all 同一批模板。"""
        detected = {}
        for name in template_names:
            detected[name] = self._find_all(frame, name, threshold=threshold, roi=roi)
        return detected

    def _merge_matches(self, detected, names):
        """把多个模板的匹配结果合并（按置信度排序 + 去重），返回 (合并点列表, 命中的模板名列表)"""
        merged = []
        hit_names = []
        for name in names:
            cur = detected.get(name, [])
            if cur:
                hit_names.append(name)
                merged.extend(cur)
        deduped = []
        for t in sorted(merged, key=lambda x: x[2], reverse=True):
            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in deduped):
                deduped.append(t)
        return deduped, hit_names

    def _reset_battle_state(self):
        """每场战斗开始时重置实时战斗循环的持久状态（在主循环进入战斗时调用一次）。"""
        self.last_skill = None
        self._lifespan_alerted = False
        self._defend_miss_streak = 0
        self._battle_defend_attempted = False
        self._battle_defend_ok = False
        self._steal_targets_gone = False
        self._auto_battle_on = False
        self._combat_phase = "entry"
        self._plan = []
        self._plan_idx = 0
        self._clicked = []
        self._steal_targets = []
        self._matched_targets = []
        self._matched_names = []
        self._all_monsters = []
        self._tou_targets = []

    def _undo_misoperation(self):
        """进战斗后若出现“撤销战斗操作”（跑图时误点到怪物占用回合），先撤销。"""
        try:
            _f_undo = self.get_frame()
            if _f_undo is not None:
                _undo_btn = self.find(_f_undo, "PK-撤销战斗操作", threshold=0.7)
                if _undo_btn and _undo_btn[1] >= 250:
                    self.tap(_undo_btn[0], _undo_btn[1])
                    self._log(f"  ↩️ 检测到误操作指令，撤销战斗操作 ({_undo_btn[0]},{_undo_btn[1]})")
                    time.sleep(0.3)
        except Exception as e:
            self._log(f"  ⚠️ 撤销战斗操作处理异常: {e}")

    def _combat_enter(self):
        """第一回合：只识别偷卡目标和宝宝（不识别所有怪物）。
        有宝宝先捕捉，没有则看偷卡目标：有就偷，没有就逃跑。
        返回 True 可继续（有偷卡计划），False 表示战斗结束/已逃跑/无需偷窃。"""
        from target_mapping import get_tou_targets as _get_tou, get_all_monsters as _get_all
        map_name = self.last_map_name or self.cfg.get("map", "小西天")
        self._tou_targets = _get_tou(map_name)
        self._all_monsters = _get_all(map_name) or []
        if not self._all_monsters:
            self._log(f"  ⚠️ 场景 {map_name} 无怪物配置")
            self._try_escape()
            self._wait_combat_end()
            return False

        frame = self.get_frame()
        if frame is None or not self.is_in_pk(frame):
            return False

        # 第一回合只识别偷卡目标（不识别所有怪物）
        steal_targets = self._detect_steal_targets(frame)
        # 名字偶发比技能栏晚渲染：无目标时多扫几帧，避免蛟龙等晚渲染被误判成"无偷卡目标"而逃跑
        if not steal_targets:
            for _retry in range(3):
                time.sleep(0.3)
                f_r = self.get_frame()
                if f_r is None or not self.is_in_pk(f_r):
                    break
                steal_targets = self._detect_steal_targets(f_r)
                if steal_targets:
                    frame = f_r
                    break
        self._steal_targets = steal_targets
        self._matched_targets = steal_targets   # 作为宝宝捕捉的怪物位置参考
        self._matched_names = []

        # 有宝宝先捕捉（宝宝非偷卡目标时，点击位置回退名字上方估算）
        captured_bb, capture_rounds = self._try_capture_bb(frame, steal_targets, max_rounds=3, scan_retries=1)
        if captured_bb:
            self._log(f"  🎣 第一回合已执行捕捉 {capture_rounds} 次，继续执行妙手空空逻辑")
            if not self._check_in_combat():
                self._log("  🏁 捕捉后战斗已结束")
                return False
            # 捕捉占用回合，重新识别偷卡目标（位置/目标可能变化）
            f_after_capture = self.get_frame()
            if f_after_capture is not None:
                steal_targets = self._detect_steal_targets(f_after_capture)
                self._steal_targets = steal_targets
                self._matched_targets = steal_targets
                if self.cfg.get("miaoshou_enabled", True):
                    ms_skill = self.find(f_after_capture, "PK-妙手空空技能", threshold=0.60)
                    if ms_skill:
                        self.last_skill = ms_skill
                        self._log(f"  ⚡ 捕捉后识别到妙手空空技能 at ({ms_skill[0]},{ms_skill[1]})")

        # 妙手空空关闭（队员防御等）：不偷卡，直接进入战斗模式分支
        if not self.cfg.get("miaoshou_enabled", True):
            self._plan = []
            return True

        # 没有宝宝/宝宝捕捉完：看有没有偷卡目标，没有就逃跑，有就偷
        if not steal_targets:
            self._log("  🏃 无偷卡目标，强制逃跑")
            self._try_escape(force=True)
            self._wait_combat_end()
            return False

        self._plan = self._build_plan(steal_targets)
        self._log(f"  🎯 识别到 {len(steal_targets)} 个偷卡目标，准备偷窃")
        return True

    def _detect_steal_targets(self, frame):
        """只识别偷卡目标（tou_targets 子集），返回去重后的 (x, y, conf) 列表。"""
        if frame is None:
            return []
        targets = []
        for candidate in self._tou_targets:
            targets.extend(self._find_all(frame, candidate, threshold=0.80, roi=COMBAT_ROI))
        dedup = []
        for t in sorted(targets, key=lambda x: x[2], reverse=True):
            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup):
                dedup.append(t)
        return dedup

    def _do_one_steal(self, frame, ms, i):
        """执行一次妙手空空：点技能 -> 点怪物 -> 点宝宝防御。
        返回 'ok'（已偷）/ 'ended'（战斗结束）/ 'targets_gone'（目标逃跑/点空）/
        'reround'（偷窃回合捕捉到宝宝占用了本回合，下回合再偷）。"""
        from target_mapping import get_all_monsters as _get_all
        steal_targets = self._steal_targets
        all_monsters = self._all_monsters
        tou_targets = self._tou_targets
        clicked = self._clicked

        if i == 0:
            cur_all = steal_targets
        else:
            f2 = self.get_frame()
            if f2 is None:
                return "reround"
            cur_all = []
            for candidate in tou_targets:
                cur = self._find_all(f2, candidate, threshold=0.80, roi=COMBAT_ROI)
                if cur:
                    cur_all.extend(cur)
            deduped2 = []
            for t in sorted(cur_all, key=lambda x: x[2], reverse=True):
                if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in deduped2):
                    deduped2.append(t)
            cur_all = deduped2
            self._log(f"  🔍 重新检测 {len(cur_all)} 个目标")

        if not cur_all:
            if clicked:
                _escaped = False
                f_verify = self.get_frame()
                if f_verify is not None:
                    _still = False
                    for cand in all_monsters:
                        for _vp in self._find_all(f_verify, cand, threshold=0.70, roi=COMBAT_ROI):
                            if any(abs(_vp[0]-px)**2 + abs(_vp[1]-py)**2 < 625 for px, py, _pc in steal_targets):
                                _still = True
                                break
                        if _still:
                            break
                    if not _still:
                        _escaped = True
                if _escaped:
                    self._log("  🏃 偷窃目标已逃跑（重检测无目标且旧位置无怪物），停止妙手空空")
                    self._steal_targets_gone = True
                    return "targets_gone"
                cur_all = steal_targets
                self._log(f"  re-detect failed, fallback to initial ({len(cur_all)} targets)")
            else:
                self._log(f"  ⚠️ 无可偷目标，跳过")
                return "targets_gone"

        available = [c for c in cur_all if not any(abs(c[0]-px)**2+abs(c[1]-py)**2 < 2500 for px, py in clicked)]
        if not available:
            available = cur_all
            self._log(f"  ⚠️ 所有目标均已偷过，选最优重复偷")

        best = max(available, key=lambda c: c[2])
        tx, ty, conf = best[0], best[1], best[2]
        cx_ms, cy_ms, _ = ms

        # 偷窃回合重新检测宝宝标记（第1轮跳过：入场时刚扫过）
        if self.cfg.get("capture_bb_enabled", False) and i > 0:
            f_cap_chk = self.get_frame()
            if f_cap_chk is not None:
                _cur_chk = []
                for _cand_chk in (_get_all(self.last_map_name or self.cfg.get("map", "")) or []):
                    _cur_chk.extend(self._find_all(f_cap_chk, _cand_chk, threshold=0.80, roi=COMBAT_ROI))
                _captured_chk, _ = self._try_capture_bb(f_cap_chk, _cur_chk or self._matched_targets, max_rounds=1)
                if _captured_chk:
                    self._log("  🎣 偷窃回合捕捉到宝宝，继续偷窃")
                    if not self._check_in_combat():
                        return "ended"
                    return "reround"   # 捕捉占用本回合，下回合再偷

        # 点技能前用当前帧刷新目标坐标（怪物可能移动/被挡，避免点空）
        _fresh = None
        f_pre = self.get_frame()
        if f_pre is not None:
            _cand = []
            for _ct in tou_targets:
                for _c in self._find_all(f_pre, _ct, threshold=0.80, roi=COMBAT_ROI):
                    _cand.append(_c)
            if _cand:
                _cand.sort(key=lambda c: (c[0]-tx)**2 + (c[1]-ty)**2)
                _fresh = _cand[0]
        if _fresh is not None:
            self._log(f"  🔄 点技能前刷新目标: 缓存({tx},{ty}) -> 最新({_fresh[0]},{_fresh[1]}) conf={_fresh[2]:.2f}")
            tx, ty = int(_fresh[0]), int(_fresh[1])

        # 每轮偷窃前检查血量：低于阈值立即逃跑
        if self._escape_if_low_hp():
            return "ended"

        self._log(f"  🎯 第{i+1}次 妙手空空 -> 点技能({cx_ms},{cy_ms}) -> 点怪物({tx},{ty}) conf={conf:.2f}")
        self.tap(cx_ms, cy_ms)
        self._last_steal_skill_time = time.time()
        time.sleep(0.5)

        # 点技能后重新检测目标（画面进入选目标状态，坐标可能变化），多试几次
        _fresh2 = None
        for _att2 in range(3):
            f_after = self.get_frame()
            if f_after is None:
                time.sleep(0.3)
                continue
            _cand2 = []
            for _ct in tou_targets:
                for _c in self._find_all(f_after, _ct, threshold=0.80, roi=COMBAT_ROI):
                    _cand2.append(_c)
            if _cand2:
                _cand2.sort(key=lambda c: (c[0]-tx)**2 + (c[1]-ty)**2)
                _fresh2 = _cand2[0]
                break
            time.sleep(0.3)
        if _fresh2 is not None:
            self._log(f"  🔄 点技能后刷新目标: ({tx},{ty}) -> 最新({_fresh2[0]},{_fresh2[1]}) conf={_fresh2[2]:.2f}")
            tx, ty = int(_fresh2[0]), int(_fresh2[1])
        else:
            self._log(f"  ⚠️ 点技能后未检测到目标，用点技能前坐标 ({tx},{ty})")
        time.sleep(random.uniform(0.3, 0.6))
        self.tap(tx, ty)

        # 妙手空空操作是否已提交：技能图标消失 = 已提交，宝宝面板才会出现。
        # 若技能图标还在（点怪点空/未提交），此时是"人物操作页"，防御按钮是人物防御，
        # 绝不能算宝宝参战（否则把人物点成防御、还误判宝宝在参战 → 该恢复忠诚却不恢复）。
        if not self._wait_skill_gone(timeout=3.0, min_wait=0.3):
            self._log("  ⚠️ 点怪后技能图标未消失（点空/未提交），不计宝宝防御，直接转击杀")
            self._steal_targets_gone = True
            return "targets_gone"

        _defend_wait = 1.5 if self.has_no_bb else 2.5
        defend_status = self._tap_defend(log_label="宝宝", timeout=_defend_wait, require_skill_hidden=True)
        if defend_status is True:
            _c_end = time.time() + 3.0
            _defend_back = False
            while time.time() < _c_end:
                f_c = self.get_frame()
                if f_c is not None and self.find(f_c, "PK-防御") is not None:
                    _defend_back = True
                    break
                time.sleep(0.2)
            if _defend_back:
                self._log("  ⚠️ 防御点击后按钮再次出现，重新点击")
                defend_status = self._tap_defend(log_label="宝宝", timeout=3.0, require_skill_hidden=True)
            else:
                self._log("  ✅ 防御点击完成，3秒内未再出现（本回合操作完成）")
        if defend_status == "missing":
            self._wait_for_skill(timeout=15.0)
            _point_empty = False
            _still_near = False
            for _chk_i in range(3):
                f_chk = self.get_frame()
                if f_chk is not None:
                    for _ct in all_monsters:
                        for _c in self._find_all(f_chk, _ct, threshold=0.70, roi=COMBAT_ROI):
                            if abs(_c[0] - tx) ** 2 + abs(_c[1] - ty) ** 2 < 2500:
                                _still_near = True
                                break
                        if _still_near:
                            break
                if _still_near:
                    break
                time.sleep(0.4)
            if not _still_near:
                _point_empty = True
            if _point_empty:
                self._log("  🎯 点怪后目标已不在（点空/目标逃跑），直接转击杀分支")
                self._steal_targets_gone = True
                return "targets_gone"
            if self.has_no_bb:
                self._log("  ⚠️ 未识别到宝宝防御按钮（画面判定未带宝宝），跳过")
            else:
                self._defend_miss_streak += 1
                self._log(f"  ⚠️ 未识别到宝宝防御按钮（第{self._defend_miss_streak}次，二次点击后仍无），跳过")
            self._battle_defend_attempted = True
        else:
            self._defend_miss_streak = 0
            self._battle_defend_attempted = True
            self._battle_defend_ok = True
        time.sleep(0.2)
        clicked.append((tx, ty))
        return "ok"

    def _battle_loop(self):
        """从进入战斗到战斗结束的常驻实时循环：
        每帧实时识别妙手空空技能图标，识别到（=轮到玩家操作）就立即执行，直到战斗结束才返回。"""
        self._log("⚔️ 开始战斗流程（实时识别）")
        if self._combat_phase is None:
            self._reset_battle_state()

        # 首次进入：低血量先跑、撤销误操作
        if self._combat_phase == "entry":
            if self._escape_if_low_hp():
                return
            self._undo_misoperation()

        non_pk_since = None          # 战斗结束多帧容错
        last_hp_check = 0.0

        while self.running:
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            # === 战斗结束判定：连续约2.5s非战斗才判结束（抗特效/动画遮挡误判） ===
            if not self.is_in_pk(frame):
                if non_pk_since is None:
                    non_pk_since = time.time()
                elif time.time() - non_pk_since >= 2.5:
                    self._log("  🏁 战斗结束")
                    return
                time.sleep(0.1)
                continue
            non_pk_since = None

            # 战斗中 HP/MP 补给（节流）
            now = time.time()
            if now - last_hp_check >= 2.0:
                last_hp_check = now
                self.check_hp_mp_battle(frame)

            # === 核心：实时识别妙手空空技能图标（= 轮到玩家操作） ===
            ms = self.find(frame, "PK-妙手空空技能", threshold=0.60)

            if ms is None:
                # 妙手空空图标漏识别时，用"捕捉"按钮兜底判断是否轮到操作。
                # 捕捉按钮每回合轮到人物操作时都显示，且只有人物有、召唤兽没有 → 无歧义。
                if self.find(frame, "PK-捕捉", threshold=0.70) is None:
                    time.sleep(0.1)
                    continue
                # 轮到操作了，但技能图标没识别到：用缓存/固定坐标兜底
                if self.last_skill is not None:
                    ms = self.last_skill
                else:
                    ms = (708, 97, 0.0)
                    self._log("  ⚠️ 妙手空空图标漏识别，无缓存坐标，用固定坐标(708,97)")

            # 已轮到玩家操作
            self.last_skill = ms

            phase = self._combat_phase
            if phase == "entry":
                if not self._combat_enter():
                    return
                self._combat_phase = "steal" if (self._plan and self.cfg.get("miaoshou_enabled", True)) else "post"
                time.sleep(0.1)
                continue

            phase = self._combat_phase
            if phase == "steal":
                if self._plan_idx < len(self._plan):
                    st = self._do_one_steal(frame, ms, self._plan_idx)
                    if st == "ended":
                        return
                    if st == "targets_gone":
                        self._steal_targets_gone = True
                        self._combat_phase = "post"
                    elif st == "reround":
                        pass  # 捕捉占用了本回合，下回合再偷
                    else:
                        self._plan_idx += 1
                    time.sleep(0.2)
                    continue
                else:
                    self._combat_phase = "post"

            phase = self._combat_phase
            if phase == "post":
                if self._auto_battle_on:
                    self._combat_phase = "wait_end"
                else:
                    # 未挂自动（怪物未检测到/逃跑失败）：本回合再次尝试击杀/逃跑
                    self._post_steal_action(skip_wait=not bool(self._plan), matched_targets=self._matched_targets)
                time.sleep(0.2)
                continue

            if phase == "wait_end":
                # 已挂自动/已逃跑：继续实时识别直到战斗结束
                time.sleep(0.1)
                continue

            time.sleep(0.05)

        return

    def do_combat(self):

        self._log("⚔️ 开始战斗流程")
        # 进战斗先查血量：低于阈值立即逃跑，避免低血量硬扛阵亡
        if self._escape_if_low_hp():
            return
        self.last_skill = None  # clear old cache
        self._lifespan_alerted = False             # 每场战斗重置：是否已弹框提醒宝宝无寿命
        self._defend_miss_streak = 0               # 每场战斗重置：连续识别不到防御按钮次数
        self._battle_defend_attempted = False
        self._battle_defend_ok = False
        self._steal_targets_gone = False           # 每场重置：偷窃目标是否已逃跑（喽啰会跑）
        self._auto_battle_on = False               # 每场重置：是否已挂自动战斗

        # 进战斗后如果出现“撤销战斗操作”（例如跑图点地图时误点到怪物，回合已被占用），
        # 先撤销误操作，避免本回合被普通攻击占用导致召唤兽无法防御。
        try:
            _f_undo = self.get_frame()
            if _f_undo is not None:
                _undo_btn = self.find(_f_undo, "PK-撤销战斗操作", threshold=0.7)
                # 撤销按钮应在下方操作区（误匹配到顶部 HUD 时忽略，避免白点一下）
                if _undo_btn and _undo_btn[1] >= 250:
                    self.tap(_undo_btn[0], _undo_btn[1])
                    self._log(f"  ↩️ 检测到误操作指令，撤销战斗操作 ({_undo_btn[0]},{_undo_btn[1]})")
                    time.sleep(0.3)
        except Exception as e:
            self._log(f"  ⚠️ 撤销战斗操作处理异常: {e}")

        map_name = self.last_map_name or self.cfg.get("map", "小西天")



        # 从 target_mapping 获取偷窃目标和全部怪物

        from target_mapping import get_tou_targets as _get_tou, get_all_monsters as _get_all

        tou_targets = _get_tou(map_name)

        all_monsters = _get_all(map_name) or []

        if not all_monsters:

            self._log(f"  ⚠️ 场景 {map_name} 无怪物配置")

            self._try_escape()

            return



        # 进场提速：进场动画期间怪物名字/技能栏都还没渲染，原流程是
        # "扫怪重试(0.3s×3) -> 捕捉标记扫描 -> 偷卡筛选 -> 再等技能栏"，
        # 识别耗时全部串在游戏动画后面。改为先轮询等妙手空空技能图标出现
        # （= 轮到玩家操作，此时怪物名字也已渲染），在那一帧一次性匹配全部模板，
        # 识别等待与进场动画重叠，捕捉/妙手空空在技能栏出现后零点几秒内执行。
        matched_targets = []

        matched_names = []

        frame = None

        detected = {}

        if self.cfg.get("miaoshou_enabled", True):

            _bar_deadline = time.time() + 12.0

            while time.time() < _bar_deadline:

                _f = self.get_frame()

                if _f is None:

                    time.sleep(0.15)

                    continue

                if not self.is_in_pk(_f):

                    return

                ms_skill = self.find(_f, "PK-妙手空空技能", threshold=0.60)

                if ms_skill is not None:

                    self.last_skill = ms_skill

                    frame = _f

                    break

                time.sleep(0.15)

        if frame is None:
            # 妙手关闭 / 12秒内未等到技能栏（极端卡顿）：取当前帧按旧逻辑扫描，
            # 后续 _wait_for_skill 与偷卡重试各自兜底
            frame = self.get_frame()

            if frame is None:

                return

            if not self.is_in_pk(frame):

                return

        # 一次性匹配全部怪物模板，按模板名分组（steal 复用同一份结果，不再重复匹配）
        detected = self._match_templates_map(frame, all_monsters, threshold=0.80, roi=COMBAT_ROI)

        matched_targets, matched_names = self._merge_matches(detected, all_monsters)

        # 名字偶发比技能栏晚渲染：无目标时隔0.3s再扫一帧
        if not matched_targets:

            time.sleep(0.3)

            _f = self.get_frame()

            if _f is None:

                return

            if not self.is_in_pk(_f):

                return

            detected = self._match_templates_map(_f, all_monsters, threshold=0.80, roi=COMBAT_ROI)

            matched_targets, matched_names = self._merge_matches(detected, all_monsters)

            if matched_targets:

                frame = _f

        # ===== 战斗中四小人弹窗（妙手空空）：先图灵云识别点击，再走正常流程 =====
        if self._handle_combat_four_person(frame):

            time.sleep(0.5)

            frame = self.get_frame()

            if frame is None:

                return

            detected = self._match_templates_map(frame, all_monsters, threshold=0.80, roi=COMBAT_ROI)

            matched_targets, matched_names = self._merge_matches(detected, all_monsters)

        # 去重

        deduped = []

        for t in sorted(matched_targets, key=lambda x: x[2], reverse=True):

            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in deduped):

                deduped.append(t)

        matched_targets = deduped

        # detect skill icon on same frame
        if self.cfg.get("miaoshou_enabled", True):
            ms_skill = self.find(frame, "PK-妙手空空技能", threshold=0.60)
            if ms_skill:
                self.last_skill = ms_skill
                self._log(f"  \u26a1 skill at ({ms_skill[0]},{ms_skill[1]})")



        display_name = ", ".join(matched_names) if matched_names else (tou_targets[0] if tou_targets else "?")

        self._log(f"  🔍 检测到 {len(matched_targets)} 个目标 ({display_name})")

        for i, t in enumerate(matched_targets):

            self._log(f"    [{i+1}] ({t[0]},{t[1]}) conf={t[2]:.2f}")



        # ========== 对面宝宝文字检测 + 捕捉（第一回合优先：有宝宝/变异先捕捉） ==========
        # 捕捉和妙手空空不互斥：捕捉后继续执行妙手空空逻辑
        # 第一回合最多捕捉3次（节省时间），之后继续妙手空空
        captured_bb, capture_rounds = self._try_capture_bb(frame, matched_targets, max_rounds=3, scan_retries=1)
        if captured_bb:
            self._log(f"  🎣 第一回合已执行捕捉 {capture_rounds} 次，继续执行妙手空空逻辑")

            # 捕捉占用过回合，才需要重查战斗状态/技能栏；没捕捉时这两步是
            # 纯开销（两次全帧匹配），跳过以缩短首偷延迟
            if not self._check_in_combat():
                self._log("  🏁 捕捉后战斗已结束")
                return

            if self.cfg.get("miaoshou_enabled", True):
                f_after_capture = self.get_frame()
                if f_after_capture is not None:
                    ms_skill = self.find(f_after_capture, "PK-妙手空空技能", threshold=0.60)
                    if ms_skill:
                        self.last_skill = ms_skill
                        self._log(f"  ⚡ 捕捉后识别到妙手空空技能 at ({ms_skill[0]},{ms_skill[1]})")

        # 单独检测偷卡目标，如果场上没有偷卡目标则跳过偷窃直接击杀
        steal_targets = []
        if tou_targets:
            # tou_targets 是 all_monsters 的子集，直接从同一份匹配结果 detected 里筛选，
            # 不再单独 _find_all 一遍（省重复匹配）；结果与 matched 同帧同源，杜绝不一致。
            steal_targets, _ = self._merge_matches(detected, tou_targets)

        # 第一回合没识别到偷卡目标时，不立即放弃：稍等重新截图识别（滑动已移除，不做镜头滑动）
        retry_failed = False
        if (not steal_targets and tou_targets and matched_targets
                and self.cfg.get("miaoshou_enabled", True)):
            self._log("  🔍 第一次未识别到偷卡目标，进行第二次识别")
            if not self._check_in_combat():
                return
            time.sleep(1.0)
            f_retry = self.get_frame()
            if f_retry is not None:
                steal_targets = []
                for candidate in tou_targets:
                    cur = self._find_all(f_retry, candidate, threshold=0.80, roi=COMBAT_ROI)
                    if cur:
                        steal_targets.extend(cur)
                dedup_s = []
                for t in sorted(steal_targets, key=lambda x: x[2], reverse=True):
                    if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup_s):
                        dedup_s.append(t)
                steal_targets = dedup_s
                if steal_targets:
                    self._log(f"  🎯 第二次识别到 {len(steal_targets)} 个偷卡目标")
                else:
                    retry_failed = True
                    self._log("  🔍 第二次仍未识别到偷卡目标")

        if not steal_targets:
            if retry_failed:
                # 可能四小人弹窗遮挡了偷卡目标：先图灵识别点击四小人，再重试一次
                if self._handle_combat_four_person():
                    f3 = self.get_frame()
                    if f3 is not None:
                        steal_targets = []
                        for candidate in tou_targets:
                            cur = self._find_all(f3, candidate, threshold=0.80, roi=COMBAT_ROI)
                            if cur:
                                steal_targets.extend(cur)
                        dedup_s = []
                        for t in sorted(steal_targets, key=lambda x: x[2], reverse=True):
                            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup_s):
                                dedup_s.append(t)
                        steal_targets = dedup_s
                        if steal_targets:
                            self._log(f"  🎯 点击四小人后识别到 {len(steal_targets)} 个偷卡目标")

        if not steal_targets:
            if retry_failed:
                # 两次重试都无偷卡目标：保存调试截图，便于排查是怪没刷出来还是模板漏匹配
                try:
                    _df = self.get_frame()
                    if _df is not None:
                        self._save_detection_debug(_df, "no_steal_target", matched_targets)
                except Exception:
                    pass

            # 无偷卡目标：尝试捕捉对面宝宝/变异（捕捉不依赖偷卡目标，有变异先抓）
            # 捕捉成功但场上仍无偷卡目标 -> 直接战斗分支；捕捉失败 -> 再试一次偷卡目标识别
            for _extra in range(2):
                if not self._check_in_combat():
                    return
                time.sleep(0.8)
                f_extra = self.get_frame()
                if f_extra is None:
                    continue
                from target_mapping import get_all_monsters as _gt_extra
                _cur_extra = []
                for _cand_extra in (_gt_extra(self.last_map_name or self.cfg.get("map", "")) or []):
                    _cur_extra.extend(self._find_all(f_extra, _cand_extra, threshold=0.80, roi=COMBAT_ROI))
                # 捕捉到宝宝/变异
                _captured_extra, _ = self._try_capture_bb(f_extra, _cur_extra or matched_targets, max_rounds=3, scan_retries=0)
                if _captured_extra:
                    self._log(f"  🎣 第{_extra+1}次捕捉到宝宝/变异，继续执行妙手空空逻辑")
                    if not self._check_in_combat():
                        return
                    # 捕捉后重新检测偷卡目标（捕捉占用回合，目标可能变化）
                    f_after_cap = self.get_frame()
                    steal_targets = []
                    if f_after_cap is not None:
                        for candidate in tou_targets:
                            cur = self._find_all(f_after_cap, candidate, threshold=0.80, roi=COMBAT_ROI)
                            if cur:
                                steal_targets.extend(cur)
                        dedup_st2 = []
                        for t in sorted(steal_targets, key=lambda x: x[2], reverse=True):
                            if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup_st2):
                                dedup_st2.append(t)
                        steal_targets = dedup_st2
                    if steal_targets:
                        self._log(f"  🎯 捕捉后识别到偷卡目标 {len(steal_targets)} 个")
                        break
                    self._log("  ℹ️ 捕捉后场上仍无偷卡目标，直接战斗（跳过妙手空空）")
                    self._post_steal_action(skip_wait=True, matched_targets=matched_targets)
                    return
                # 捕捉未触发：再直接识别一次偷卡目标
                cur_st = []
                for candidate in tou_targets:
                    cur = self._find_all(f_extra, candidate, threshold=0.80, roi=COMBAT_ROI)
                    if cur:
                        cur_st.extend(cur)
                dedup_st = []
                for t in sorted(cur_st, key=lambda x: x[2], reverse=True):
                    if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in dedup_st):
                        dedup_st.append(t)
                if dedup_st:
                    steal_targets = dedup_st
                    self._log(f"  🎯 捕捉失败后识别到偷卡目标 {len(steal_targets)} 个")
                    break

            if not steal_targets:
                self._log("  🏃 无偷窃目标且无宝宝可捕捉，强制逃跑")
                self._try_escape(force=True)
                self._wait_combat_end()
                return

        # 构建偷窃目标攻击计划（按置信度排序，最多3个目标）
        plan = self._build_plan(steal_targets)

        if not plan:
            self._log(f"  ⚠️ 未检测到目标 ({display_name})，跳过妙手空空")

        if self.cfg.get("miaoshou_enabled", True):
            clicked = []
            # plan 为空（场上无偷卡目标）时 max_attempts=0：不进入妙手空空循环，
            # 避免日志显示"妙手空空 ×3"误导，也杜绝无目标时误点技能卡在选目标状态
            max_attempts = min(len(plan), 3) if plan else 0
            self._log(f"  🎯 妙手空空 ×{max_attempts}")
            for i in range(max_attempts):
                if not self._check_in_combat():
                    return

                if i == 0:
                    cur_all = steal_targets
                else:
                    f2 = self.get_frame()
                    if f2 is None:
                        break
                    cur_all = []
                    for candidate in tou_targets:
                        cur = self._find_all(f2, candidate, threshold=0.80, roi=COMBAT_ROI)
                        if cur:
                            cur_all.extend(cur)
                    deduped2 = []
                    for t in sorted(cur_all, key=lambda x: x[2], reverse=True):
                        if not any(abs(t[0]-d[0])**2+abs(t[1]-d[1])**2 < 625 for d in deduped2):
                            deduped2.append(t)
                    cur_all = deduped2
                    self._log(f"  🔍 重新检测 {len(cur_all)} 个目标")

                if not cur_all:
                    if clicked:
                        # 重检测失败：验证旧目标位置是否还有怪物，区分
                        # "名字暂时模糊（怪还在，可继续偷）" vs "目标已逃跑（喽啰会跑，
                        # 继续点旧位置只会点空 → 防御按钮不出现 → 误判宝宝未参战）"。
                        _escaped = False
                        f_verify = self.get_frame()
                        if f_verify is not None:
                            _still = False
                            for cand in all_monsters:
                                for _vp in self._find_all(f_verify, cand, threshold=0.70, roi=COMBAT_ROI):
                                    # steal_targets 元素是 3 元组 (x, y, conf)
                                    if any(abs(_vp[0]-px)**2 + abs(_vp[1]-py)**2 < 625 for px, py, _pc in steal_targets):
                                        _still = True
                                        break
                                if _still:
                                    break
                            if not _still:
                                _escaped = True
                        if _escaped:
                            self._log("  🏃 偷窃目标已逃跑（重检测无目标且旧位置无怪物），停止妙手空空")
                            self._steal_targets_gone = True
                            break
                        cur_all = steal_targets
                        self._log(f"  re-detect failed, fallback to initial ({len(cur_all)} targets)")
                    else:
                        self._log(f"  ⚠️ 无可偷目标，跳过")
                        break

                available = [c for c in cur_all if not any(abs(c[0]-px)**2+abs(c[1]-py)**2 < 2500 for px, py in clicked)]

                if not available:
                    available = cur_all
                    self._log(f"  ⚠️ 所有目标均已偷过，选最优重复偷")

                best = max(available, key=lambda c: c[2])
                tx, ty, conf = best[0], best[1], best[2]
                if i == 0 and self.last_skill is not None:
                    # 第一轮：进入战斗检测时已确认技能位置（⚡ skill at），
                    # 直接用缓存坐标，省去 _wait_for_skill 重新取帧验证的开销
                    ms = self.last_skill
                else:
                    ms = self._wait_for_skill(timeout=20.0)
                if ms is None:
                    self._log(f"  第{i+1}次: 超时，跳过")
                    continue
                cx_ms, cy_ms, _ = ms
                # 每轮偷窃前重新检测宝宝标记（名字被前排挡住时可能晚几回合才显示），
                # 检测到就立即捕捉一次，再继续偷窃。第1轮跳过：入场时 _try_capture_bb
                # 刚在技能栏就绪帧上扫过一遍，重复全量匹配只会拖慢首次偷卡
                if self.cfg.get("capture_bb_enabled", False) and i > 0:
                    f_cap_chk = self.get_frame()
                    if f_cap_chk is not None:
                        from target_mapping import get_all_monsters as _gt_chk
                        _cur_chk = []
                        for _cand_chk in (_gt_chk(self.last_map_name or self.cfg.get("map", "")) or []):
                            _cur_chk.extend(self._find_all(f_cap_chk, _cand_chk, threshold=0.80, roi=COMBAT_ROI))
                        _captured_chk, _ = self._try_capture_bb(f_cap_chk, _cur_chk or matched_targets, max_rounds=1)
                        if _captured_chk:
                            self._log("  🎣 偷窃回合捕捉到宝宝，继续偷窃")
                            if not self._check_in_combat():
                                return
                            # 捕捉占用本回合，重新等下一次玩家回合再执行偷窃
                            ms = self._wait_for_skill(timeout=20.0)
                            if ms is None:
                                continue
                            cx_ms, cy_ms, _ = ms
                # 点技能前用当前帧刷新目标坐标：怪物位置是进入战斗时的缓存，
                # 期间可能移动/被挡，直接用缓存坐标点容易点空（→ 技能挂在"选目标"
                # 状态 → 被误判成四小人界面死循环）。当前帧能识别到目标就取最新的。
                _fresh = None
                f_pre = self.get_frame()
                if f_pre is not None:
                    _cand = []
                    for _ct in tou_targets:
                        for _c in self._find_all(f_pre, _ct, threshold=0.80, roi=COMBAT_ROI):
                            _cand.append(_c)
                    if _cand:
                        # 优先选离原缓存目标最近的新位置（怪可能小幅移动，避免乱点别的怪）
                        _cand.sort(key=lambda c: (c[0]-tx)**2 + (c[1]-ty)**2)
                        _fresh = _cand[0]
                if _fresh is not None:
                    self._log(f"  🔄 点技能前刷新目标: 缓存({tx},{ty}) -> 最新({_fresh[0]},{_fresh[1]}) conf={_fresh[2]:.2f}")
                    tx, ty = int(_fresh[0]), int(_fresh[1])
                # 每轮偷窃前检查血量：低于阈值立即逃跑（低血量还继续偷卡容易阵亡）
                if self._escape_if_low_hp():
                    return
                self._log(f"  🎯 第{i+1}次 妙手空空 -> 点技能({cx_ms},{cy_ms}) -> 点怪物({tx},{ty}) conf={conf:.2f}")
                self.tap(cx_ms, cy_ms)
                self._last_steal_skill_time = time.time()   # 记录点技能时间（四小人误判保护用）
                # 点完技能后稍等，进入"选择目标"状态
                time.sleep(0.5)
                # 点技能后重新检测目标：点技能后画面进入选目标状态，怪物名字/位置可能变化，
                # 用点技能后最新的画面坐标点怪物，避免按点技能前的坐标点空。
                # 多试几次（画面刷新慢时第一帧可能检测不到）
                _fresh2 = None
                for _att2 in range(3):
                    f_after = self.get_frame()
                    if f_after is None:
                        time.sleep(0.3)
                        continue
                    _cand2 = []
                    for _ct in tou_targets:
                        for _c in self._find_all(f_after, _ct, threshold=0.80, roi=COMBAT_ROI):
                            _cand2.append(_c)
                    if _cand2:
                        _cand2.sort(key=lambda c: (c[0]-tx)**2 + (c[1]-ty)**2)
                        _fresh2 = _cand2[0]
                        break
                    time.sleep(0.3)
                if _fresh2 is not None:
                    self._log(f"  🔄 点技能后刷新目标: ({tx},{ty}) -> 最新({_fresh2[0]},{_fresh2[1]}) conf={_fresh2[2]:.2f}")
                    tx, ty = int(_fresh2[0]), int(_fresh2[1])
                else:
                    self._log(f"  ⚠️ 点技能后未检测到目标，用点技能前坐标 ({tx},{ty})")
                time.sleep(random.uniform(0.3, 0.6))
                self.tap(tx, ty)   # 点怪物（用点技能后最新坐标）
                # 游戏顺序：点妙手空空 -> 点怪物 -> 然后防御，操作完才开始偷窃。
                # 点中怪物且宝宝参战时，防御按钮应立即出现：
                # 实时识别防御按钮，识别到就点。带宝宝的号受视频流延迟影响，面板可能
                # 晚几秒才出现，窗口放宽到8秒；没带宝宝的号面板不会出现，维持4秒短窗口，
                # 避免拖到下一回合把人物点成防御
                _defend_wait = 4.0 if self.has_no_bb else 8.0
                defend_status = self._tap_defend(log_label="宝宝", timeout=_defend_wait, require_skill_hidden=True)
                if defend_status is True:
                    # 点击成功：再识别3秒确认防御按钮不再出现（本回合操作完成）；
                    # 若又出现说明刚才没点掉，重新点
                    _c_end = time.time() + 3.0
                    _defend_back = False
                    while time.time() < _c_end:
                        f_c = self.get_frame()
                        if f_c is not None and self.find(f_c, "PK-防御") is not None:
                            _defend_back = True
                            break
                        time.sleep(0.2)
                    if _defend_back:
                        self._log("  ⚠️ 防御点击后按钮再次出现，重新点击")
                        defend_status = self._tap_defend(log_label="宝宝", timeout=3.0, require_skill_hidden=True)
                    else:
                        self._log("  ✅ 防御点击完成，3秒内未再出现（本回合操作完成）")
                # 一直没识别到防御按钮（或点不掉）→ 停止本次，等待下一回合（不重试点怪）
                if defend_status == "missing":
                    # ---- 点空悬停检测 ----
                    # 防御按钮没出现，可能是技能点怪点空（目标已逃跑/名字模糊），
                    # 技能悬在"选择目标"状态；也可能是已点中、回合结算动画遮挡了名字。
                    # 结算期间立刻单帧检测会把"正在偷窃"误判成"目标已逃跑"，导致3次
                    # 妙手空空没偷完就转击杀。先等画面回到指令阶段（妙手空空技能图标
                    # 重新可见；悬停选目标时图标同样在、名字也清晰，两种情况检测都可靠），
                    # 再多帧确认目标是否还在点怪位置附近（±50px，宽松阈值0.70，
                    # 全量怪物模板）：目标已不在 -> 判定点空，停止妙手空空，避免下一轮
                    # 继续"点技能->点空"空转到回合倒计时自动普攻。
                    self._wait_for_skill(timeout=15.0)
                    _point_empty = False
                    _still_near = False
                    for _chk_i in range(3):
                        f_chk = self.get_frame()
                        if f_chk is not None:
                            for _ct in all_monsters:
                                for _c in self._find_all(f_chk, _ct, threshold=0.70, roi=COMBAT_ROI):
                                    if abs(_c[0] - tx) ** 2 + abs(_c[1] - ty) ** 2 < 2500:
                                        _still_near = True
                                        break
                                if _still_near:
                                    break
                        if _still_near:
                            break
                        time.sleep(0.4)
                    if not _still_near:
                        _point_empty = True
                    if _point_empty:
                        self._log("  🎯 点怪后目标已不在（点空/目标逃跑），直接转击杀分支")
                        # 不再点技能图标取消选择：点空后技能可能仍悬在选目标状态，
                        # 此时再点技能图标可能重新选中妙手空空反而坏事；直接转击杀分支，
                        # 击杀分支的点技能（法术）会替换当前技能选择。
                        self._steal_targets_gone = True
                        break
                    if self.has_no_bb:
                        # 画面判定未带宝宝，防御按钮不出现属正常，跳过
                        self._log("  ⚠️ 未识别到宝宝防御按钮（画面判定未带宝宝），跳过")
                    else:
                        self._defend_miss_streak += 1
                        self._log(f"  ⚠️ 未识别到宝宝防御按钮（第{self._defend_miss_streak}次，二次点击后仍无），跳过")
                    # 有偷卡但宝宝未参战（无宝宝/没寿命）都计入：连续2场后偷3次直接逃跑
                    self._battle_defend_attempted = True
                else:
                    # 防御按钮正常识别到（点击成功）：本场至少一次有效防御
                    self._defend_miss_streak = 0
                    self._battle_defend_attempted = True
                    self._battle_defend_ok = True
                time.sleep(0.2)
                clicked.append((tx, ty))
        else:
            if self.cfg.get("miaoshou_enabled", True):
                self._log("  ⏭️ 妙手空空已关闭")
            else:
                self._log("  ⏭️ 妙手空空未触发")

        self._post_steal_action(skip_wait=not bool(plan), matched_targets=matched_targets)



    def _post_steal_action(self, skip_wait=False, matched_targets=[]):

        """妙手空空3次后的战斗模式分支"""

        mode_skill = self.cfg.get("skill_then_auto", False)

        mode_normal = self.cfg.get("normal_then_auto", False)

        mode_defend = self.cfg.get("defend_then_auto", False)

        mode_direct = self.cfg.get("direct_auto", False)

        mode_escape = self.cfg.get("escape_enabled", True)



        # 本场偷卡后防御一次都没识别到（宝宝未参战/没寿命）：优先逃跑——没宝宝不能挂机打怪，
        # 即使偷窃目标已逃跑/点空也一样要逃，否则会白挂自动送死
        if self._battle_defend_attempted and not self._battle_defend_ok:
            self._log("  🏃 本场偷卡后防御都没识别到（宝宝未参战），等待下回合点击逃跑")
            # force=True：无视 escape_enabled 配置；_try_escape 内部会等待
            # 妙手空空技能出现（轮到玩家操作）后再点逃跑
            self._try_escape(force=True)
            self._wait_combat_end()
            if self._pet_no_lifespan:
                # 已确认没寿命：之后每场都偷3次逃跑，不再恢复
                pass
            elif self._loyalty_recovery_done_since_miss:
                # 已恢复过忠诚，仍然多次都没识别到 -> 判定没有寿命
                self._pet_no_lifespan = True
                self._log("  ❌ 恢复忠诚后宝宝仍未参战，可能没有寿命，之后每场偷3次后直接逃跑")
            else:
                # 逃跑后立即恢复忠诚（去掉50场判断）
                self._loyalty_recovery_pending = True
            return
        elif getattr(self, "_steal_targets_gone", False):
            # 偷窃目标已逃跑（喽啰逃跑/点空）：宝宝正常参战，直接进入正常战斗分支
            self._steal_targets_gone = False
            self._log("  ℹ️ 偷窃目标已逃跑，直接战斗")
        elif self._battle_defend_attempted and self._battle_defend_ok:
            # 宝宝正常参战：清除“已恢复”标记，若之后再出现多次全没识别到会重新走恢复流程
            self._loyalty_recovery_done_since_miss = False



        if mode_escape:

            self._try_escape()

            self._wait_combat_end()

            return



        # 检测怪物位置，优先攻击顺序：护佑 > 爆炸 > 暴击
        monster_pos = None

        for _ in range(5):
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.2)
                continue

            from target_mapping import get_all_monsters as _gt
            map_name = self.last_map_name or self.cfg.get("map", "")
            tou = _gt(map_name) or []

            # 检测所有怪物
            all_mon_pts = []
            for cand in tou:
                pts = self._find_all(frame, cand, threshold=0.80, roi=COMBAT_ROI)
                all_mon_pts.extend(pts)
                if pts and monster_pos is None:
                    monster_pos = (pts[0][0], pts[0][1])

            # 护佑/爆炸/暴击文字，优先攻击对应怪物（文字在怪物下方）
            huyou_pts = self._find_all(frame, "PK-护佑文字", threshold=0.70, roi=COMBAT_ROI)
            baozha_pts = self._find_all(frame, "PK-爆炸文字", threshold=0.70, roi=COMBAT_ROI)
            baoji_pts = self._find_all(frame, "PK-暴击文字", threshold=0.70, roi=COMBAT_ROI)
            special_text = huyou_pts if huyou_pts else (baozha_pts if baozha_pts else (baoji_pts if baoji_pts else []))
            tag = "护佑" if huyou_pts else ("爆炸" if baozha_pts else ("暴击" if baoji_pts else ""))
            if special_text and all_mon_pts:
                mx, my = special_text[0][0], special_text[0][1]
                best_m, best_d = None, 999999
                for m in all_mon_pts:
                    dx = abs(m[0] - mx)
                    dy = my - m[1]  # text below monster
                    if 10 < dy < 150 and dx < 80:
                        d = dx + abs(dy - 60)
                        if d < best_d:
                            best_d = d
                            best_m = (m[0], m[1])
                if best_m:
                    monster_pos = best_m
                    self._log(f"  🎯 检测到{tag}文字 -> 优先攻击 ({best_m[0]},{best_m[1]})")
                else:
                    self._log(f"  ⚠️ {tag}文字未匹配到怪物")

            if monster_pos:
                break

            time.sleep(0.3)

        # 等待第4回合（除了skip_wait=True即无偷窃目标的情况）
        if not skip_wait:
            self._log("  🎯 等待下回合（第4回合）后执行战斗操作")
            nxt = self._wait_for_skill(timeout=20.0)
            if nxt is None:
                self._log("  ⚡ 等待下回合超时，点自动让游戏接管（防卡死）")
                self._auto_with_attack_fix(monster_pos)
                return

        # 第四回合优先检测宝宝（非 mode_skill 模式；mode_skill 分支会在重检测怪物后用新位置重新检测）
        if not mode_skill and self.cfg.get("capture_bb_enabled", False):
            f_cap = self.get_frame()
            if f_cap is not None:
                captured_bb_4th, capture_rounds_4th = self._try_capture_bb(f_cap, matched_targets, max_rounds=3)
                if captured_bb_4th:
                    self._log(f"  🎣 第4回合已执行捕捉 {capture_rounds_4th} 次")
                # 捕捉后检查战斗是否还在，不在则直接返回
                if not self._check_in_combat():
                    self._log("  🏁 捕捉后战斗已结束")
                    return

        if mode_skill:

            # 点选技能后自动战斗: 点法术技能(713,145) -> 点怪物 -> 点自动

            sx, sy = 713, 145  # 法术技能坐标

            if skip_wait:

                self._log("  \u26a1 \u65e0\u5077\u7a83\u76ee\u6807\uff0c\u76f4\u63a5\u6cd5\u672f\u653b\u51fb")

                # skip_wait=无偷卡目标直接击杀：第一回合就能攻击，怪物位置已在上面检测到，
                # 不需要再等第四回合重检测（第四回合重检测会重置位置重新扫，浪费数秒）
                pass

            else:

                self._log("  \U0001f3af \u7b49\u5f85\u4e0b\u56de\u5408\uff08\u7b2c4\u6b21\u5999\u624b\u7a7a\u7a7a\u51fa\u73b0\uff09\u540e\u70b9\u6cd5\u672f\u6280\u80fd")

                nxt = self._wait_for_skill(timeout=20.0)

                if nxt is None:

                    self._log("  ⚡ 等待下回合超时，点自动让游戏接管（防卡死）")

                    self._auto_with_attack_fix(monster_pos)

                    return

            # 第4回合重新检测怪物（仅非 skip_wait：偷卡后等第四回合，喽啰可能逃跑/位置变化）
            # skip_wait 路径（无偷卡直接击杀）第一回合即可攻击，用已检测到的位置即可。
            if not skip_wait:

                # 第四回合喽啰会逃跑/残血名字模糊，需要多轮检测；但每轮检测约 0.3s，
                # 用 0.15s 间隔高频轮询（不再 0.5s），尽快命中，避免重检测拖慢操作。
                monster_pos = None

                self._log("  🔍 第4回合重新检测怪物")

                for _ in range(8):

                    if not self._check_in_combat():

                        # 重检测期间战斗已结束（喽啰逃跑/全灭），无需操作

                        self._log("  🏁 重检测期间战斗已结束")

                        return

                    f_mon = self.get_frame()

                    if f_mon is None:

                        time.sleep(0.15)

                        continue


                    # 正常检测怪物
                    from target_mapping import get_all_monsters as _gt_mon
                    _all_mon = _gt_mon(self.last_map_name or self.cfg.get("map", "")) or []
                    all_mon_pts = []
                    for cand in _all_mon:
                        pts = self._find_all(f_mon, cand, threshold=0.80, roi=COMBAT_ROI)
                        all_mon_pts.extend(pts)
                        if pts and monster_pos is None:
                            monster_pos = (pts[0][0], pts[0][1])

                    # 检测护佑/暴击文字，用已有怪物坐标匹配（文字在怪物下方）
                    # 优先顺序：护佑 > 爆炸 > 暴击
                    huyou_pts = self._find_all(f_mon, "PK-护佑文字", threshold=0.70, roi=COMBAT_ROI)
                    baozha_pts = self._find_all(f_mon, "PK-爆炸文字", threshold=0.70, roi=COMBAT_ROI)
                    baoji_pts = self._find_all(f_mon, "PK-暴击文字", threshold=0.70, roi=COMBAT_ROI)
                    special_text = huyou_pts if huyou_pts else (baozha_pts if baozha_pts else (baoji_pts if baoji_pts else []))
                    tag = "护佑" if huyou_pts else ("爆炸" if baozha_pts else ("暴击" if baoji_pts else ""))
                    if special_text and all_mon_pts:
                        mx, my = special_text[0][0], special_text[0][1]
                        best_m, best_d = None, 999999
                        for m in all_mon_pts:
                            dx = abs(m[0] - mx)
                            dy = my - m[1]  # text below monster
                            if 10 < dy < 150 and dx < 80:
                                d = dx + abs(dy - 60)
                                if d < best_d:
                                    best_d = d
                                    best_m = (m[0], m[1])
                        if best_m:
                            monster_pos = best_m
                            self._log(f"  检测到{tag}文字 -> 优先攻击 ({best_m[0]},{best_m[1]})")
                        else:
                            self._log(f"  {tag}文字未匹配到怪物")
                    elif special_text and monster_pos is None:
                        # 文字检测到了但怪物名字（模板）没匹配到：第四回合怪物残血/名字模糊，
                        # 直接用文字上方估算怪物位置（文字在怪物下方约 45px），
                        # 避免空转等怪物名字出现导致重检测拖慢。
                        mx, my = special_text[0][0], special_text[0][1]
                        monster_pos = (mx, my - 45)
                        self._log(f"  检测到{tag}文字 -> 估算怪物位置 ({monster_pos[0]},{monster_pos[1]})")

                    if monster_pos:
                        self._log(f"  🦎 怪物位置: ({monster_pos[0]},{monster_pos[1]})")
                        break

                    time.sleep(0.15)

            # 重检测不到：第四回合位置已变化（喽啰逃跑），不能用旧位置兜底点空。
            # 没有执行击杀操作不能点自动（否则自动会重复妙手空空/防御），等战斗自然结束。
            if monster_pos is None:
                self._log("  ⚠️ 重检测不到怪物（喽啰可能已逃跑），未执行击杀操作，不点自动")
                self._wait_combat_end()
                return

            # 第四回合优先检测宝宝：有宝宝/变异先捕捉（用重检测后的新怪物位置），
            # 捕捉循环内部处理多回合；战斗还在则点自动接管，否则直接攻击。
            if self.cfg.get("capture_bb_enabled", False):
                f_cap4 = self.get_frame()
                if f_cap4 is not None:
                    # 用当前帧重新检测的怪物位置匹配宝宝文字
                    _cur_mon = []
                    from target_mapping import get_all_monsters as _gt_mon4
                    for _cand4 in (_gt_mon4(self.last_map_name or self.cfg.get("map", "")) or []):
                        _cur_mon.extend(self._find_all(f_cap4, _cand4, threshold=0.80, roi=COMBAT_ROI))
                    # 捕捉循环：每回合重复 捕捉(539,403)->点目标->防御，直到宝宝消失
                    captured_bb_4, _ = self._try_capture_bb(f_cap4, _cur_mon or matched_targets)
                    if captured_bb_4:
                        self._log("  🎣 捕捉完成，宝宝已消失，执行击杀操作")
                    if not self._check_in_combat():
                        self._log("  🏁 捕捉后战斗已结束")
                        return
                    # 宝宝消失后用最新位置执行击杀操作（点技能->点怪物->点怪物）再挂自动
                    monster_pos = self._redetect_monster() or monster_pos

#             # 调试：点击前截图标注法术技能位置

#             debug_frame = self.get_frame()

#             if debug_frame is not None:

#                 try:

#                     h_f, w_f = debug_frame.shape[:2]

#                     if abs(w_f - self.stream_w) < 10 and abs(h_f - self.stream_h) < 10:

#                         dx, dy = sx, sy

#                     else:

#                         dx = int(sx * self.scale_x)

#                         dy = int(sy * self.scale_y)

#                     ann = debug_frame.copy()

#                     cv2.line(ann, (dx-50, dy), (dx+50, dy), (0, 0, 255), 3)

#                     cv2.line(ann, (dx, dy-50), (dx, dy+50), (0, 0, 255), 3)

#                     cv2.circle(ann, (dx, dy), 20, (0, 255, 255), 2)

#                     cv2.circle(ann, (dx, dy), 5, (0, 0, 255), -1)

#                     cv2.putText(ann, f"法术技能 ({dx},{dy})", (dx+30, dy-15),

#                                 cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

#                     # 如果有怪物位置，也标注上

#                     if monster_pos:

#                         _mx = monster_pos[0] if abs(w_f - self.stream_w) < 10 else int(monster_pos[0] * self.scale_x)

#                         _my = monster_pos[1] if abs(h_f - self.stream_h) < 10 else int(monster_pos[1] * self.scale_y)

#                         cv2.circle(ann, (_mx, _my), 12, (0, 255, 0), 2)

#                         cv2.putText(ann, f"怪物 ({_mx},{_my})", (_mx+15, _my-10),

#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

#                     # 保存截图

#                     import os as _os

#                     from datetime import datetime as _dt

#                     _dd = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "screenshots")

#                     _os.makedirs(_dd, exist_ok=True)

#                     _ts = _dt.now().strftime("%Y%m%d_%H%M%S")

#                     _fp = _os.path.join(_dd, f"skill_click_{_ts}.png")

#                     cv2.imwrite(_fp, ann)

#                     self._log(f"  📸 法术技能位置截图: screenshots/skill_click_{_ts}.png")

#                 except Exception as e:

#                     self._log(f"  ⚠️ 截图失败: {e}")

            # 点技能前检查血量：低于阈值立即逃跑（低血量别硬拼）
            if self._escape_if_low_hp():
                return
            self.tap(sx, sy)

            time.sleep(0.8)

            if monster_pos:

                self.tap(monster_pos[0], monster_pos[1])

                self._log(f"  🎯 人物点怪物 ({monster_pos[0]},{monster_pos[1]})")

                time.sleep(0.3)

                if not self.has_no_bb:

                    self.tap(monster_pos[0], monster_pos[1])

                    self._log(f"  🎯 宝宝点怪物 ({monster_pos[0]},{monster_pos[1]})")

                time.sleep(0.5)

            else:

                self._log("  ⚠️ 无怪物位置，跳过点怪物")

            self._tap_auto_and_wait()

        elif mode_normal:

            # 普通攻击后自动战斗: 点怪物 → 点自动

            self._log("  ⚔ 普通攻击后自动战斗")

            if monster_pos:

                self.tap(monster_pos[0], monster_pos[1])

                time.sleep(0.5)

            self._tap_auto_and_wait()



        elif mode_defend:

            # 防御后自动战斗: 人物点防御 → 宝宝点怪物 → 点自动

            self._log("  🛡 防御后自动战斗")

            self._tap_defend(log_label="人物")

            if monster_pos:

                self.tap(monster_pos[0], monster_pos[1])

                time.sleep(0.5)

            self._tap_auto_and_wait()



        elif mode_direct:

            # 直接自动战斗: 人物点怪物 → 宝宝点怪物 → 点自动

            self._log("  ⚡ 直接自动战斗")

            if monster_pos:

                self.tap(monster_pos[0], monster_pos[1])

                time.sleep(0.3)

                self.tap(monster_pos[0], monster_pos[1])

            self._tap_auto_and_wait()



        else:

            self._try_escape()

            self._wait_combat_end()





    def _tap_auto_and_wait(self):

        """点自动(765,409)后等待战斗结束。

        调用前必须已执行击杀操作（点技能→点怪物→点怪物），否则自动会重复妙手空空/防御。"""

        time.sleep(0.5)

        self._log("  🤖 点自动(765,409)")

        self.tap(765, 409)

        self._auto_battle_on = True

        self._wait_combat_end()

        # 取消自动战斗已统一在 post_combat 处理（对每场战斗生效），此处不再重复点击



    def _auto_with_attack_fix(self, monster_pos=None):

        """点自动并校验：若自动重复的是妙手空空/防御（挂错技能），

        取消自动后重新执行击杀操作再挂自动。"""

        time.sleep(0.5)

        self._log("  🤖 点自动(765,409)")

        self.tap(765, 409)

        self._auto_battle_on = True

        if not self._auto_hung_wrong(timeout=4.0):

            self._log("  ✅ 自动技能正常（未挂成妙手空空/防御）")

            self._wait_combat_end()

            return

        self._fix_auto_hang(monster_pos)



    def _auto_hung_wrong(self, timeout=4.0):

        """点自动后校验：轮询是否仍检测到妙手空空技能（=自动挂成了妙手空空/防御）。

        战斗结束或超时未检测到视为正常。"""

        start = time.time()

        while time.time() - start < timeout:

            if not self.running or not self._check_in_combat():

                return False

            frame = self.get_frame()

            if frame is not None and self.find(frame, "PK-妙手空空技能", threshold=0.60):

                return True

            time.sleep(0.5)

        return False



    def _cancel_auto(self):

        """取消自动战斗：优先模板识别，识别不到用固定坐标(767,408)，

        点击后确认取消按钮消失，仍在则继续点。"""

        self._auto_battle_on = False  # 取消后恢复手动指令

        for _ in range(3):

            frame = self.get_frame()

            cancel = self.find(frame, "PK-取消自动战斗") if frame is not None else None

            if cancel:

                self.tap(cancel[0], cancel[1])

                self._log(f"  🔄 取消自动战斗 ({cancel[0]},{cancel[1]})")

            else:

                self.tap(767, 408)

                self._log("  🔄 取消自动战斗 (767,408)")

            time.sleep(0.5)

            frame2 = self.get_frame()

            if frame2 is not None and self.find(frame2, "PK-取消自动战斗") is None:

                break



    def _wait_skill_gone(self, timeout=10.0, min_wait=1.5):

        """等待妙手空空技能按钮消失（=本回合操作已提交/轮到敌人），战斗结束也算完成。

        返回 True=操作已提交或战斗结束，False=超时仍未消失。"""

        start = time.time()

        while time.time() - start < min_wait:

            if not self.running:

                return False

            frame = self.get_frame()

            if frame is None:

                time.sleep(0.2)

                continue

            if not self.is_in_pk(frame):

                return True

            time.sleep(0.2)

        while time.time() - start < timeout:

            if not self.running:

                return False

            frame = self.get_frame()

            if frame is None:

                time.sleep(0.2)

                continue

            if not self.is_in_pk(frame):

                return True

            if self.find(frame, "PK-妙手空空技能", threshold=0.60) is None:

                return True

            time.sleep(0.2)

        return False



    def _redetect_monster(self):

        """重新检测怪物位置（复用现有模板检测）。"""

        from target_mapping import get_all_monsters as _gt_mon

        _all_mon = _gt_mon(self.last_map_name or self.cfg.get("map", "")) or []

        for _ in range(5):

            if not self._check_in_combat():

                return None

            f_mon = self.get_frame()

            if f_mon is None:

                time.sleep(0.2)

                continue

            for cand in _all_mon:

                pts = self._find_all(f_mon, cand, threshold=0.80, roi=COMBAT_ROI)

                if pts:

                    return (pts[0][0], pts[0][1])

            time.sleep(0.3)

        return None



    def _fix_auto_hang(self, monster_pos=None):

        """自动挂错（妙手空空/防御）后的修正流程：

        取消自动(767,408) → 重新检测妙手空空技能（等待轮到玩家操作）→

        执行击杀操作（点技能→点怪物→点怪物）→ 确认击杀操作完成后才挂自动。

        没有执行击杀操作时绝不点自动。"""

        self._log("  ⚠️ 自动挂成了妙手空空/防御，取消自动并重新执行击杀后再挂自动")

        self._cancel_auto()

        # 重新检测妙手空空技能 = 等待轮到玩家操作

        self._log("  🔍 重新检测妙手空空技能（等待轮到玩家操作）")

        ms = self._wait_for_skill(timeout=20.0)

        if ms is None:

            self._log("  ⚠️ 等待玩家回合超时，未执行击杀操作，不点自动")

            self._wait_combat_end()

            return

        # 重新检测怪物位置

        if monster_pos is None:

            monster_pos = self._redetect_monster()

        if monster_pos is None:

            self._log("  ⚠️ 未检测到怪物，未执行击杀操作，不点自动")

            self._wait_combat_end()

            return

        # 执行击杀操作：点技能(713,145) → 点怪物(人物) → 点怪物(宝宝)

        self.tap(713, 145)

        time.sleep(0.8)

        self.tap(monster_pos[0], monster_pos[1])

        self._log(f"  🎯 人物点怪物 ({monster_pos[0]},{monster_pos[1]})")

        time.sleep(0.3)

        if not self.has_no_bb:

            self.tap(monster_pos[0], monster_pos[1])

            self._log(f"  🎯 宝宝点怪物 ({monster_pos[0]},{monster_pos[1]})")

        time.sleep(0.5)

        # 确认击杀操作已执行（技能按钮消失=本回合操作已提交），执行完才能挂自动

        if not self._wait_skill_gone(timeout=10.0):

            self._log("  ⚠️ 未确认击杀操作已执行，不点自动")

            self._wait_combat_end()

            return

        if not self._check_in_combat():

            self._log("  🏁 击杀后战斗已结束，无需挂自动")

            return

        self._log("  🤖 击杀操作已完成，重新点自动(765,409)")

        self.tap(765, 409)

        self._auto_battle_on = True

        self._wait_combat_end()

    def _save_debug_combat(self, frame, targets, display_name):

        try:

            import os, time

            from PIL import Image, ImageDraw, ImageFont

            debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_combat")

            os.makedirs(debug_dir, exist_ok=True)



            # OpenCV BGR -> PIL RGB

            vis = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            pil_img = Image.fromarray(vis)

            draw = ImageDraw.Draw(pil_img)



            # 尝试加载中文字体

            try:

                font = ImageFont.truetype("simhei.ttf", 16)

                font_small = ImageFont.truetype("simhei.ttf", 12)

            except Exception:

                try:

                    font = ImageFont.truetype("msyh.ttc", 16)

                    font_small = ImageFont.truetype("msyh.ttc", 12)

                except Exception:

                    font = ImageFont.load_default()

                    font_small = ImageFont.load_default()



            rx, ry, rw, rh = COMBAT_ROI["x"], COMBAT_ROI["y"], COMBAT_ROI["w"], COMBAT_ROI["h"]



            # 画 ROI 区域（绿色框）

            draw.rectangle([rx, ry, rx + rw, ry + rh], outline=(0, 255, 0), width=2)

            draw.text((rx + 5, ry - 20), "ROI", fill=(0, 255, 0), font=font)



            # 画检测到的怪物

            colors = [(255, 0, 0), (0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0)]

            for i, (cx, cy, conf) in enumerate(targets):

                color = colors[i % len(colors)]

                # 画圆

                draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], outline=color, width=2)

                # 标签

                label = display_name.split("-")[-1] if "-" in display_name else display_name

                draw.text((cx + 30, cy - 18), f"{label} {conf:.2f}", fill=color, font=font_small)



            # PIL RGB -> OpenCV BGR 保存

            vis_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            ts = time.strftime("%Y%m%d_%H%M%S")

            path = os.path.join(debug_dir, f"combat_{ts}.png")

            cv2.imwrite(path, vis_bgr)

            self._log(f"  📸 调试截图已保存: debug_combat/combat_{ts}.png")

        except Exception as e:

            self._log(f"  ⚠️ 调试截图失败: {e}")



    def _find_all(self, frame, name, threshold=0.81, roi=None):

        tmpl = self.templates.get(name)

        if tmpl is None or frame is None:

            return []

        if roi:

            rx, ry, rw, rh = roi["x"], roi["y"], roi["w"], roi["h"]

            frame = frame[ry:ry+rh, rx:rx+rw]

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

        results = list(best.values())

        if roi:

            results = [(cx + roi["x"], cy + roi["y"], conf) for cx, cy, conf in results]

        return results



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

            # 1个：偷3次

            return [(sorted_targets[0][0], sorted_targets[0][1])] * 3

    def _escape_if_low_hp(self, threshold=20):
        """操作前检查人物血量：低于 threshold% 立即逃跑保命（今天已多次阵亡）。
        返回 True=已逃跑结束战斗（调用方应停止本次操作），False=血量正常可继续。"""
        try:
            frame = self.get_frame()
            if frame is None:
                return False
            hp, mp, bb, no_bb = self.detect_hp_mp_bb(frame)
            self.last_hp = hp
            if hp <= threshold:
                self._log(f"  🚨 人物血量 {hp:.0f}% < {threshold}%，立即逃跑保命")
                self._try_escape(force=True)
                self._wait_combat_end()
                return True
        except Exception as e:
            self._log(f"  ⚠️ 低血量检查异常: {e}")
        return False

    def _try_escape(self, force=False):

        if not force and not self.cfg.get('escape_enabled', True):

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

                    time.sleep(random.uniform(0.3, 0.5))

                    # 点完逃跑再点一下防御：逃跑失败时本回合仍执行防御动作，
                    # 避免角色空过回合（与原版小霸王逻辑一致）

                    if self._check_in_combat():

                        d_frame = self.get_frame()

                        if d_frame is not None:

                            # 防御按钮固定在右下操作区 (708,402) 附近；
                            # 0.50 低阈值会误匹配到怪物/场景元素（如日志中的
                            # (114,146)、(154,280) 等坐标），点到错误位置，
                            # 因此识别后用位置过滤掉远离右下操作区的误匹配。
                            defend = self.find(d_frame, "PK-防御", threshold=0.70)

                            if defend is None:

                                defend = self.find(d_frame, "PK-防御", threshold=0.60)

                            if defend and not (defend[0] > 480 and defend[1] > 280):

                                self._log(f"  ⚠️ 防御模板误匹配 ({defend[0]},{defend[1]})，忽略")

                                defend = None

                            if defend:

                                self._log(f"  🛡 点完逃跑再点防御 ({defend[0]},{defend[1]})")

                                self.tap(defend[0], defend[1])

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

        # 多帧容错 + 拉长等待：原来只等 9 秒且单帧非战斗即判“结束”，
        # 战斗一长或特效遮挡 HUD 就会提前返回、把战场丢回给主循环。
        # 这里连续 0.6s 非战斗才判结束，最长等 120s（超时由 _battle_loop 接管继续监督）。
        deadline = time.time() + 120.0

        non_pk_since = None

        while self.running and time.time() < deadline:

            frame = self.get_frame()

            if frame is not None:

                if not self.is_in_pk(frame):

                    if non_pk_since is None:

                        non_pk_since = time.time()

                    elif time.time() - non_pk_since >= 0.6:

                        self._log("  🏁 战斗结束")

                        return

                else:

                    non_pk_since = None

            time.sleep(0.3)



    def _is_avatar_visible(self, frame=None):

        """Pixel-color scan of character avatar bar (from isShowRoleAvatar)."""

        if frame is None:

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





    def _is_show_four_person(self, frame=None):

        """四小人界面预筛：HP/MP+头像。
        真伪由本地 CNN 打分判定（实测：走路画面各槽位概率≈0，
        真·四小人界面单槽位>0.9），网络兜底仅在不低于 0.4 时触发。"""

        if frame is None:

            frame = self.get_frame()

        if frame is None:

            return False

        hp, mp, bb, no_bb = self.detect_hp_mp_bb(frame)

        if not (hp < 1 and mp < 1):

            return False

        if self._is_avatar_visible(frame):

            return False

        # 保护：战斗中刚点过妙手空空技能（点技能后 2 秒内）——此时画面停在
        # "选中技能、待选目标"状态，血蓝条空 + 头像被技能面板遮住，会被误判成
        # 四小人界面。原来用 6 秒，太宽：每回合点技能都会重新计时，导致战斗中
        # 大部分时间四小人被屏蔽（看起来像"只在战斗开始检测"）。选目标状态实际
        # 只有 1~2 秒，故缩短到 2 秒。
        if self.was_in_pk and (time.time() - getattr(self, "_last_steal_skill_time", 0)) < 2.0:
            return False

        return True



    def _handle_combat_four_person(self, frame=None):

        """战斗中四小人弹窗（妙手空空）：按 8.5 前逻辑，仅以 _is_show_four_person 判定。

        识别到四小人界面后，固定 ROI 本地 CNN 识别点击（不找“在/请”文字）；
        本地识别不到（置信度不足/两次点击后仍在/异常）再按 8.5 前方式调用图灵云。
        返回 True=已检测到并处理，False=当前画面未被判定为四小人界面。
        """

        try:
            if not self._is_show_four_person(frame):
                return False

            self._log("  👥 战斗中检测到四小人界面")

            # 1) 本地识别优先
            try:
                from xbw_features import findFourPersonDetectArea, cnnUtil
                left, top, w, h = findFourPersonDetectArea(self.serial)
                if left != 0:
                    self._log(f"  🧠 本地四小人识别区域 ({left},{top},{w},{h})")
                    handled = cnnUtil.findFourPersonLocal(self.serial, left, top, w, h)
                else:
                    self._log("  ⚠️ 本地未找到“在/请”识别区域，回退默认区域识别")
                    handled = cnnUtil.findFourPersonLocal(self.serial)
            except Exception as e:
                self._log(f"  ⚠️ 本地四小人识别异常({e})，按 8.5 前方式调用图灵云")
                self._four_person_tuling_click()
                return True

            # 2) 本地两次没点掉/识别不到 -> 按 8.5 前方式调用图灵云
            if not handled:
                self._log("  ⚠️ 本地四小人识别未生效，按 8.5 前方式调用图灵云")
                self._four_person_tuling_click()
            return True
        except Exception as e:
            self._log(f"  ⚠️ 战斗中四小人处理异常: {e}")
            return False



    def _four_person_tuling_click(self):

        """8.5 前图灵处理方式：全分辨率截图 -> 固定 ROI(540,170,880,380) 上传
        图灵云 -> API 坐标换算（设备坐标/scale -> 流坐标）-> tap 点击。"""

        result = self._detect_four_person()

        if result["success"]:

            self._tuling_fail_streak = 0

            x, y = result["x"], result["y"]

            self._log(f"  ✅ 图灵四小人识别成功: ({x}, {y})")

            self.tap(x, y)

            return True

        self._log("  ⚠️ 图灵四小人识别失败: " + str(result.get("error", "未知")))

        # 连续失败（如账户余额不足）→ 进入冷却，暂停调用图灵，避免反复请求与死循环
        self._tuling_fail_streak = getattr(self, "_tuling_fail_streak", 0) + 1

        if self._tuling_fail_streak >= 2:

            self._tuling_cooldown_until = time.time() + 120

            self._log("  ⏸️ 图灵连续失败，2分钟内不再调用（本地降阈值重试）")

        return False

    def _tuling_unavailable(self):

        """图灵云是否处于冷却不可用状态（余额不足等持续失败时）"""

        return time.time() < getattr(self, "_tuling_cooldown_until", 0)



    def _handle_four_person(self):

        """四小人处理：优先本地 ONNX（小霸王合并功能），失败降级图灵云API。
        调用方（主循环）已确认四小人界面。"""

        if not self._xbw_wired and not self._is_show_four_person():

            self._log("  👥 非四小人界面，跳过检测")

            return

        if self.cfg.get("use_local_four_person", True):
            try:
                from xbw_features import findFourPersonDetectArea, cnnUtil
                left, top, w, h = findFourPersonDetectArea(self.serial)
                if left != 0:
                    self._log(f"  🧠 本地四小人识别区域 ({left},{top},{w},{h})")
                    handled = cnnUtil.findFourPersonLocal(self.serial, left, top, w, h)
                else:
                    self._log("  ⚠️ 本地未找到“在/请”识别区域，回退默认区域识别")
                    handled = cnnUtil.findFourPersonLocal(self.serial)
                if handled:
                    return
                # 本地 0.8 阈值没点掉：若图灵处于冷却（余额不足等），降阈值再试一次，
                # 仍不行则跳过本次（不点图灵），避免反复请求 + 死循环
                if self._tuling_unavailable():
                    self._log("  ⚠️ 图灵冷却中，本地降阈值(0.5)重试")
                    try:
                        if left != 0:
                            handled = cnnUtil.findFourPersonLocal(self.serial, left, top, w, h, conf_threshold=0.5)
                        else:
                            handled = cnnUtil.findFourPersonLocal(self.serial, conf_threshold=0.5)
                    except Exception:
                        handled = False
                    if handled:
                        return
                    self._log("  ⏭️ 图灵冷却中，跳过本次四小人处理")
                    return
                self._log("  ⚠️ 本地四小人识别未生效，按 8.5 前方式调用图灵云")
            except Exception as e:
                self._log(f"  ⚠️ 本地四小人识别异常({e})，按 8.5 前方式调用图灵云")

        # 8.5 前图灵处理方式：全分辨率截图 + 固定 ROI + 坐标换算 + tap
        self._log("  👅 检测到四小人界面，按 8.5 前方式调用图灵云识别...")

        self._four_person_tuling_click()





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



            session = getattr(self, "_tuling_session", None)

            if session is None:

                session = requests.Session()

                session.trust_env = False

                self._tuling_session = session

            resp = session.post(TULING_API_URL, data=data_json, timeout=10)

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

            from rapidocr_onnxruntime import RapidOCR

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

            # OCR_CROP 为 800x448 流坐标（get_frame 已归一化），无需再除以 scale
            cx = max(0, int(OCR_CROP["x"]))

            cy = max(0, int(OCR_CROP["y"]))

            cw = min(int(OCR_CROP["w"]), w - cx)

            ch = min(int(OCR_CROP["h"]), h - cy)

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

        # OCR_CROP 为 800x448 流坐标（get_frame 已归一化），无需再除以 scale
        cx = max(0, int(OCR_CROP["x"]))

        cy = max(0, int(OCR_CROP["y"]))

        cw = min(int(OCR_CROP["w"]), w - cx)

        ch = min(int(OCR_CROP["h"]), h - cy)

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

        """战斗结束后清理 + 血量检测 + 酒肆恢复 + 诚度恢复（55-60场）"""

        self.was_in_pk = False

        # 战斗结束后取消自动战斗：点击后重新确认，仍在则继续点击，直到消失（对所有战斗生效）
        for _ in range(5):

            frame = self.get_frame()

            if frame is None:

                time.sleep(0.2)

                continue

            cancel = self.find(frame, "PK-取消自动战斗")

            if cancel:

                self.tap(cancel[0], cancel[1])

                self._log("  🔄 取消自动战斗")

                time.sleep(0.3)  # 等待点击生效

                continue  # 重新识别，确认取消按钮已消失

            break

        # 取消完成后立即跑图：下一次主循环直接打开地图，不再等坐标停止检测
        self._force_run_map = True

        # 【已注释】重置回合数点击（避免多余点击）
        # reset = self.find(frame, "重置回合数")
        #
        # if reset:
        #
        #     self._log("  🔄 重置回合数")
        #
        #     self.tap(reset[0], reset[1])
        #
        #     time.sleep(0.5)


        # ===== 战斗计数 =====
        self.battle_count += 1
        self._log(f"  📊 战斗场次: {self.battle_count}")

        # 3次防御都没识别到逃跑后：立即执行忠诚度恢复（不再按场次）
        if self._loyalty_recovery_pending:
            self._loyalty_recovery_pending = False
            self._loyalty_recovery_done_since_miss = True
            self._log("  🔔 宝宝未参战，逃跑后执行忠诚度恢复")
            self._do_loyalty_recovery()


        # ===== 战斗后血量检测 + 酒肆恢复 =====

        time.sleep(0.2)

        self.check_and_heal_after_combat()



    # ========== 主循环 ==========

    def run_loop(self):

        scene_config = self.cfg.get("scene_config", DEFAULT_CONFIG["scene_config"])

        enabled_scenes = [s for s in scene_config if s.get("enabled")]

        if not enabled_scenes:

            self._log("❌ 没有启用的场景，请在 UI 中至少勾选一个场景")

            self.running = True

            self.running = False

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

        # 排除无导航分支的场景：仅支持打怪，不支持自动切场（否则真实切场会静默失败）
        nav_blocked = []

        supported2 = []

        for s in supported:

            if s.get("scene") in NO_SWITCH_NAV_SCENES:

                nav_blocked.append(s.get("scene"))

            else:

                supported2.append(s)

        supported = supported2

        if reserved:

            self._log(f"⚠️ 以下场景已配置但逻辑暂未完善：{', '.join(reserved)}")

        if nav_blocked:

            self._log(f"⚠️ 以下场景仅支持打怪、暂不支持自动切场，已从轮转列表移除：{', '.join(nav_blocked)}")

        if not supported:

            from target_mapping import list_supported_scenes as _lss

            self._log(f'没有已完善的场景可运行。当前支持：{", ".join(_lss())}')

            self.log.put("__STOPPED__")

            return



        from target_mapping import get_map_click_area as _get_mc

        self.running = True

        try:

            self._run_loop_impl(supported, reserved)

        finally:

            self.running = False

            self.log.put("__STOPPED__")



    def _run_loop_impl(self, supported, reserved):

        from target_mapping import get_map_click_area as _get_mc

        # 读取 GUI 配置的地图选择（若与实际场景匹配则从该场景开始轮转）

        gui_map = self.cfg.get("map", "")

        current_idx = 0

        if gui_map in MAP_CONFIG:

            for i, s in enumerate(supported):

                if _match_scene_name(gui_map, s["scene"]):

                    current_idx = i

                    break

        # 设备初始化（启动场景对齐需要在真实帧上 OCR，必须先连上设备）
        if not self.init_device():

            self._log("❌ 设备初始化失败")

            return

        self._wire_xbw_backend()

        # 启动场景对齐：先 OCR 检测角色当前实际所在的场景
        # 在配置轮转列表内 → 直接从这里开始；不在/检测失败 → 自动导航到配置的第一个场景
        actual_scene = None
        if self.coord_enabled:
            try:
                if self.ocr_engine is None:
                    self.init_ocr()
                ocr_name, _, _ = self.detect_map_coord()
                if ocr_name:
                    from scene_detector import detect_position as _detect
                    detected, _ = _detect(self.serial, None, self.scale_x, self.scale_y, ocr_name)
                    actual_scene = detected
            except Exception as e:
                self._log(f"  ⚠️ 启动场景检测失败: {e}")

        start_scene = None
        if actual_scene:
            for i, s in enumerate(supported):
                if _match_scene_name(actual_scene, s["scene"]):
                    current_idx = i
                    start_scene = s["scene"]
                    self._log(f"📍 检测到当前位于 {actual_scene}，从该场景开始轮转")
                    break
            if start_scene is None:
                # 角色实际所在场景不在配置里：自动导航到配置顺序的第一个场景
                start_scene = supported[0]["scene"]
                current_idx = 0
                self._log(f"🧭 当前位于 {actual_scene}，不在切场配置中，自动导航到配置第一个场景: {start_scene}")
                if not self._do_real_scene_switch(start_scene):
                    self._log(f"  ⚠️ 导航失败，回退本地切场（将按 {start_scene} 模板运行）")
        else:
            # OCR 检测失败/未启用：不知道角色在哪，退而尊重 GUI 地图选择；GUI 也不匹配则导航到第一个
            if gui_map in MAP_CONFIG and any(_match_scene_name(gui_map, s["scene"]) for s in supported):
                for i, s in enumerate(supported):
                    if _match_scene_name(gui_map, s["scene"]):
                        current_idx = i
                        start_scene = s["scene"]
                        break
                self._log(f"📌 未能检测到当前场景，按 GUI 地图选择从 {start_scene} 开始")
            else:
                start_scene = supported[0]["scene"]
                current_idx = 0
                self._log(f"🧭 未能检测到当前场景，自动导航到配置第一个场景: {start_scene}")
                if not self._do_real_scene_switch(start_scene):
                    self._log(f"  ⚠️ 导航失败，回退本地切场（将按 {start_scene} 模板运行）")

        current_scene = supported[current_idx]

        map_name = current_scene["scene"]

        self.cfg["map"] = map_name

        mc = _get_mc(map_name)



        self.load_templates(map_name)

        self._pkg_snapshot = None
        self._pkg_check_t = time.time()
        self._pkg_interval = 0.0   # 启动后立即检查背包
        self._huan_count = 0
        self._card_count = 0
        self._scene_switch_requested = False

        self.start_time = time.time()
        self._current_scene_start_time = time.time()  # 记录当前场景开始时间

        scene_start_time = time.time()

        # 切换场间隔：读场景配置的“满XX分钟”；“无要求”= 永不按时间切（仅靠环/卡达标切）
        try:
            from xbw_features import parse_require as _parse_require
            _switch_minutes = _parse_require(current_scene.get("time"))
        except Exception:
            _switch_minutes = None
        if _switch_minutes is None:
            scene_switch_interval = None
            self._log(f"  ⏱️ 场景 {map_name} 时间要求为无要求：将只在环/卡达标时切换")
        else:
            scene_switch_interval = _switch_minutes * 60

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

        self._log(f"   战斗中: 气血<{self.cfg.get('hp_threshold',30)}%→{self.cfg.get('hp_item','红碗')}  "

                  f"魔法<{self.cfg.get('mp_threshold',20)}%→{self.cfg.get('mp_item','蓝碗')}")

        self._log(f"   战后酒肆: {'✅' if jiusi_en else '❌'}  "

                  f"气血<{jiusi_hp}%  "

                  f"魔法<{jiusi_mp}%  "

                  f"BB<{self.cfg.get('jiusi_bb_threshold',50)}%")

        self._log("=" * 40)



        from scene_detector import detect_position



        loop = 0

        try:

            while self.running:

                loop += 1
                # 统计日切换（每天 5:00）：重置当日累计，避免跨 0 点挂机把记录串到第二天
                _day_key = stats_day()
                if self._stats_day_key != _day_key:
                    self._stats_day_key = _day_key
                    self._daily_huan_count = 0
                    self._daily_card_count = 0
                    self.battle_count = 0
                    self.total_runtime = 0
                    self._log(f"📅 进入新统计日 {_day_key}（每天5:00为界），当日环/卡计数已重置")
                if self._paused:
                    time.sleep(0.2)
                    continue

                frame = self.get_frame()

                # 每轮先尝试关闭弹窗（活动/公告等），避免遮挡后续检测

                self.close_pop(is_one_time=True)

                if loop % 5 == 0:

                    self._log(f"[{loop}] 循环中...")

                if frame is None:

                    time.sleep(0.05)

                    continue



                # === 战斗中：检测回合是否恢复 / 战斗是否结束 ===

                if self.was_in_pk:

                    in_pk = self.is_in_pk(frame)

                    if in_pk:

                        # 卡死恢复：妙手空空技能出现 = 轮到玩家操作，继续偷卡流程

                        if self.cfg.get("miaoshou_enabled", True):

                            ms = self.find(frame, "PK-妙手空空技能", threshold=0.60)

                            if ms is not None:

                                self._log(f"[{loop}] 🔄 检测到妙手空空技能，继续偷卡流程")

                                self._battle_loop()

                                time.sleep(0.3)

                                continue

                        time.sleep(0.1)

                        continue

                    # 战斗结束

                    self.post_combat(frame)

                    time.sleep(0.15)

                    continue



                # === 场景切换检测：时间到期 / 环卡达标 / 后续操作判定 ===
                # 关闭"真实场景导航" → 不自动切换场景（固定当前场景打怪）

                _switch_due = (scene_switch_interval is not None
                               and (time.time() - scene_start_time) > scene_switch_interval)
                _switch_retry_ok = time.time() >= self._switch_retry_after
                if (self.cfg.get("use_real_scene_switch", True)
                        and not self.was_in_pk and _switch_retry_ok
                        and not self.is_in_pk(frame)
                        and (self._scene_switch_requested or _switch_due)):

                    # 记录当前场景到历史
                    prev_map_name = self.cfg.get("map", "")
                    if prev_map_name:
                        duration = time.time() - scene_start_time
                        self._scene_history.append({
                            "name": prev_map_name,
                            "cards": self._card_count,
                            "rings": self._huan_count,
                            "duration": duration,
                            "start_time": scene_start_time,
                        })
                        # 保存场景历史到文件
                        self._save_scene_history()

                    # 当前场景“后续操作=停止”：达标后整个自动流程结束
                    if current_scene.get("after", "后换场景") == "停止":
                        self._log(f"🛑 场景 {map_name} 条件已满足且配置为“停止”，结束自动流程")
                        self.running = False
                        break

                    # 单场景且配置为“后换场景”：没有下一个可去的场景，重置计数继续挂机
                    if len(supported) == 1:
                        self._log(f"🔁 仅配置了一个场景({map_name})，条件满足后重置环/卡计数继续挂机")
                        self._scene_switch_requested = False
                        self._pkg_snapshot = None
                        self._pkg_check_t = time.time()
                        self._pkg_interval = 0.0   # 立即重建背包基线
                        self._huan_count = 0
                        self._card_count = 0
                        scene_start_time = time.time()
                        self._current_scene_start_time = time.time()  # 更新当前场景开始时间
                        continue

                    current_idx = (current_idx + 1) % len(supported)

                    current_scene = supported[current_idx]

                    map_name = current_scene["scene"]

                    mc = _get_mc(map_name)

                    self._log(f"场景切换: {map_name}")

                    self._scene_switch_requested = False
                    if not self._do_real_scene_switch(map_name):
                        # 真实导航失败：不静默降级为"只切模板"（否则角色实际还在旧图，
                        # 日志却显示在新图打怪）。保留切场请求并冷却 30 秒后重试，
                        # 期间维持原场景的计数/模板/时间间隔状态不变。
                        self._log(f"  ⚠️ 真实切场失败，角色可能仍在 {prev_map_name or '原场景'}；"
                                  f"保留切场请求，30 秒后重试（不切模板）")
                        # 回退轮转索引（上方已 +1），重试时仍指向同一目标场景
                        current_idx = (current_idx - 1) % len(supported)
                        self._scene_switch_requested = True
                        self._switch_retry_after = time.time() + 30
                        continue

                    self.cfg["map"] = map_name

                    self.load_templates(map_name)

                    self.reset_coord_tracking()

                    # 新场景重新计数环/卡
                    self._pkg_snapshot = None
                    self._pkg_check_t = time.time()
                    self._pkg_interval = 0.0   # 新场景立即检查背包
                    self._huan_count = 0
                    self._card_count = 0

                    # 按新场景的时间要求重算切换间隔；“无要求”= 永不按时间切
                    try:
                        from xbw_features import parse_require as _parse_require
                        _switch_minutes = _parse_require(current_scene.get("time"))
                    except Exception:
                        _switch_minutes = None
                    if _switch_minutes is None:
                        scene_switch_interval = None
                        self._log(f"  ⏱️ 场景 {map_name} 时间要求为无要求：将只在环/卡达标时切换")
                    else:
                        scene_switch_interval = _switch_minutes * 60

                    scene_start_time = time.time()
                    self._current_scene_start_time = time.time()  # 更新当前场景开始时间

                    continue

                # === 非战斗：背包环/卡计数（小霸王合并功能） ===

                if (self.cfg.get("check_pkg_counts", True) and not self.was_in_pk
                        and not self._scene_switch_requested):
                    if (time.time() - self._pkg_check_t) >= self._pkg_interval:
                        self._check_backpack_counts(current_scene)



                # === 非战斗：四小人检测 ===

                if (self._is_show_four_person(frame)
                        and (time.time() - self._last_4p_check_t) > 2.0
                        and self._is_game_foreground()):
                    self._last_4p_check_t = time.time()

                    self._log(f"[{loop}] 👥 检测到四小人界面")

                    self._handle_four_person()

                    time.sleep(random.uniform(0.2, 0.5))

                    continue



                # === 非战斗：检测是否进入战斗 ===

                in_pk = self.is_in_pk(frame)

                if in_pk:

                    self.was_in_pk = True

                    self._log(f"[{loop}] ⚔️ 进入战斗！")

                    self._reset_battle_state()

                    self._battle_loop()

                    time.sleep(0.15)

                    continue



                # === 非战斗：场景验证（间隔检测） ===

                if loop % 200 == 0 and self.coord_enabled:

                    ocr_name, _, _ = self.detect_map_coord(frame)

                    if ocr_name:

                        from scene_detector import detect_position as _detect

                        detected, method = _detect(self.serial, frame, self.scale_x, self.scale_y, ocr_name)

                        # 关闭"真实场景导航"：不随场景变化跳转（固定当前场景打怪）
                        if (self.cfg.get("use_real_scene_switch", True)
                                and detected and not _match_scene_name(detected, map_name)):

                            target_idx = next((i for i, s in enumerate(supported) if _match_scene_name(detected, s["scene"])), None)

                            if target_idx is not None:

                                self._log(f"检测到场景变化: {detected}")

                                current_idx = target_idx

                                current_scene = supported[current_idx]

                                map_name = current_scene["scene"]

                                mc = _get_mc(map_name)

                                self.cfg["map"] = map_name

                                self.load_templates(map_name)

                                self.reset_coord_tracking()

                                # 场景已变：重置环/卡计数与背包基线（与正常切场一致）
                                self._scene_switch_requested = False
                                self._pkg_snapshot = None
                                self._pkg_check_t = time.time()
                                self._pkg_interval = 0.0   # 新场景立即检查背包
                                self._huan_count = 0
                                self._card_count = 0

                                # 按新场景时间要求重算切换间隔；“无要求”= 永不按时间切
                                try:
                                    from xbw_features import parse_require as _parse_require
                                    _switch_minutes = _parse_require(current_scene.get("time"))
                                except Exception:
                                    _switch_minutes = None
                                if _switch_minutes is None:
                                    scene_switch_interval = None
                                else:
                                    scene_switch_interval = _switch_minutes * 60

                                scene_start_time = time.time()
                                self._current_scene_start_time = time.time()  # 更新当前场景开始时间

                                continue



                # === 非战斗：跑图 ===

                if self.cfg.get("auto_path_enabled", True):

                    def _pk_check():

                        return self.running and self.is_in_pk(self.get_frame())



                    # 确保 OCR 已初始化

                    if self.coord_enabled and self.ocr_engine is None:

                        self.init_ocr()

                    t0 = time.time()

                    # 休息完：等待0.3秒后直接跑图，跳过坐标停止检测
                    if self._force_run_map:
                        self._force_run_map = False
                        time.sleep(0.3)
                        coord_stopped, cur_map, cur_coord = True, self.last_map_name, self.last_coord
                    else:
                        coord_stopped, cur_map, cur_coord = self.check_coord_stopped(frame)

                    if loop % 5 == 0:

                        self._log(f"[{loop}] OCR done, stopped={coord_stopped}, map={cur_map}, coord={cur_coord}")

                    if loop % 5 == 0:

                        self._log(f"[{loop}] coord_check: {time.time()-t0:.2f}s")



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



                    # 2. 随机点击地图（距上次至少50px），连续点2~3次，每次+-8px

                    if not pk_detected:

                        for _ in range(20):  # 最多重试20次

                            cx = random.randint(mc["x1"], min(mc["x2"], self.stream_w - 1))

                            cy = random.randint(mc["y1"], min(mc["y2"], self.stream_h - 1))

                            if self._last_map_click is None:

                                break

                            lx, ly = self._last_map_click

                            if abs(cx - lx) >= 50 or abs(cy - ly) >= 50:

                                break

                        self._last_map_click = (cx, cy)

                        # 随机每隔几回合多点几下（1/3概率），其余点1次

                        if random.randint(1, 8) == 1:

                            tap_count = random.randint(2, 3)

                            for _ in range(tap_count):

                                # 每次点击前再查一次战斗，防止切入战斗的瞬间点到怪物

                                if _pk_check():

                                    pk_detected = True

                                    break

                                ox = cx + random.randint(-8, 8)

                                oy = cy + random.randint(-8, 8)

                                self.tap(max(0, ox), max(0, oy), offset=False)

                                time.sleep(random.uniform(0.05, 0.15))

                        else:

                            if _pk_check():

                                pk_detected = True

                            else:

                                self.tap(cx, cy, offset=False)

                        for _ in range(2):

                            time.sleep(0.15)

                            if _pk_check():

                                pk_detected = True

                                break



                    # 3. 关闭地图

                    if not pk_detected:

                        f_pop = self.get_frame()

                        if f_pop is not None:

                            close_btn = self.find(f_pop, "关闭地图", threshold=0.5)

                            if close_btn:

                                self.tap(close_btn[0], close_btn[1])

                                time.sleep(0.1)

                            else:

                                self.tap(60, 25)

                        self.close_pop(is_one_time=True)



                    if pk_detected:

                        continue



                    # 重置坐标跟踪（刚移动完，等坐标变化）

                    self.reset_coord_tracking()

                    self.close_pop(is_one_time=True)

























                else:

                    self._log(f"[{loop}] 自动寻路已关闭，等待遇怪")

                    pk = False

                    for _ in range(3):

                        time.sleep(0.4)

                        if self._check_in_combat():

                            pk = True

                            break

                    if pk:

                        continue



                    # 检测坐标是否停止

                time.sleep(0.3)



        except Exception as e:

            self._log(f"❌ 异常: {e}")

            import traceback

            self._log(traceback.format_exc())

        finally:

            self._save_current_scene_history()

            self.stop()



    def stop(self):

        self.running = False

        # 累计本次运行时长（跨重启保留），start_time 置 0 防止重复累计
        if self.start_time > 0:

            self.total_runtime += max(0.0, time.time() - self.start_time)

            self.start_time = 0

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

        ttk.Label(set_frame, text="气血<").grid(row=0, column=1)

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

        ttk.Label(set_frame, text="魔法<").grid(row=1, column=1, pady=(6, 0))

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



        ttk.Label(jiusi_frame, text="气血<").grid(row=1, column=0, pady=(6, 0))

        self.jiusi_hp_threshold = tk.StringVar(value="50")

        ttk.Entry(jiusi_frame, textvariable=self.jiusi_hp_threshold, width=5).grid(row=1, column=1, pady=(6, 0))

        ttk.Label(jiusi_frame, text="%").grid(row=1, column=2, padx=(2, 15))



        ttk.Label(jiusi_frame, text="魔法<").grid(row=1, column=3, pady=(6, 0))

        self.jiusi_mp_threshold = tk.StringVar(value="30")

        ttk.Entry(jiusi_frame, textvariable=self.jiusi_mp_threshold, width=5).grid(row=1, column=4, pady=(6, 0))

        ttk.Label(jiusi_frame, text="%").grid(row=1, column=5, padx=(2, 15))



        ttk.Label(jiusi_frame, text="BB<").grid(row=1, column=6, pady=(6, 0))

        self.jiusi_bb_threshold = tk.StringVar(value="50")

        ttk.Entry(jiusi_frame, textvariable=self.jiusi_bb_threshold, width=5).grid(row=1, column=7, pady=(6, 0))

        ttk.Label(jiusi_frame, text="%").grid(row=1, column=8, padx=(2, 5))



        ttk.Label(jiusi_frame, text="💡 任一项低于阈值，战斗结束后自动触发酒肆→休息恢复",

                  foreground="gray").grid(row=2, column=0, columnspan=9, sticky="w", pady=(6, 0))



        # ======== 战斗设置 ========

        self._add_section(main_frame, "⚔️ 战斗设置", row); row += 1

        combat_frame = ttk.LabelFrame(main_frame, padding=8)

        combat_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)); row += 1



        self.capture_bb_enabled = tk.BooleanVar(value=self.cfg.get("capture_bb_enabled", False))

        ttk.Checkbutton(combat_frame, text="捕捉召唤兽（检测到对面宝宝时优先点击捕捉按钮）",

                        variable=self.capture_bb_enabled).grid(row=0, column=0, columnspan=5, sticky="w")



        ttk.Label(combat_frame, text="💡 战斗中将先点击捕捉按钮(539,403)，再点击对面宝宝位置",

                  foreground="gray").grid(row=1, column=0, columnspan=5, sticky="w", pady=(6, 0))



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

        self.hp_display = ttk.Label(data_frame, text="气血: --%", font=("Consolas", 11))

        self.hp_display.pack(side=tk.LEFT, padx=(0, 20))

        self.mp_display = ttk.Label(data_frame, text="魔法: --%", font=("Consolas", 11))

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

        self.hp_display.config(text="气血: --%")

        self.mp_display.config(text="魔法: --%")

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

                        text=f"气血: {hp:.0f}%",

                        foreground="red" if hp < 30 else "green")

                    self.mp_display.config(

                        text=f"魔法: {mp:.0f}%",

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

        self.capture_bb_enabled.set(cfg.get("capture_bb_enabled", False))

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

            self.cfg["capture_bb_enabled"] = self.capture_bb_enabled.get()

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
