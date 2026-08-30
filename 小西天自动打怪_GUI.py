# -*- coding: utf-8 -*-
"""
梦幻西游 自动打怪 - 现代 UI 控制面板
===============================
参考用户提供的页面重新设计，使用 ttkbootstrap 主题，更接近参考图风格。
"""
import json
import os
import queue
import subprocess as sp
import sys
import threading
import time
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk

from mhxy_engine import (
    ADB_EXE,
    AutoFightEngine,
    MAP_CONFIG,
    GUI_CONFIG_FILE,
    list_adb_devices,
    stats_day,
    short_dev_label,
)


# 设备统计文件（按天记录，关闭程序后重启可恢复当日累计）
STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "device_stats.txt")

# 特殊场景（队伍抓特殊）队伍配置
TEAM_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "special_team_config.json")

# 特殊场景可选场景（引擎已支持的地图）
SPECIAL_SCENES = list(MAP_CONFIG.keys())

# 设备独立配置目录
DEVICE_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")

# 场景历史目录
SCENE_HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


def get_scene_history_file(serial, date=None):
    """获取设备场景历史文件路径（按统计日记录，每天5:00为界）"""
    if date is None:
        date = stats_day()
    return os.path.join(SCENE_HISTORY_DIR, f"scene_history_{serial}_{date}.json")


def load_scene_history_from_file(serial, days=7):
    """从文件加载场景历史记录（支持多天合并，按统计日回溯）"""
    from datetime import timedelta

    history_by_date = {}
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i, hours=5)
        date_str = date.strftime("%Y-%m-%d")
        history_file = get_scene_history_file(serial, date_str)

        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    day_history = json.load(f)
                    if day_history:
                        # 为每条记录添加日期信息
                        for record in day_history:
                            record["date"] = date_str
                        history_by_date[date_str] = day_history
            except Exception:
                pass

    # 按日期倒序合并历史记录
    result = []
    for date_str in sorted(history_by_date.keys(), reverse=True):
        result.extend(history_by_date[date_str])

    return result


# ============== 扩展默认配置 ==============
DEFAULT_CONFIG = {
    "serial": "",
    "device_order": [],
    "map": "小西天",
    # 新版 UI 映射（战斗中补给）
    "hp_method": "酒肆",
    "mp_method": "酒肆",
    "hp_threshold": 30,
    "mp_threshold": 20,
    # 战斗后酒肆恢复
    "jiusi_enabled": True,
    "jiusi_hp_threshold": 50,
    "jiusi_mp_threshold": 30,
    "jiusi_bb_threshold": 50,
    # 兼容旧引擎的字段
    "hp_enabled": True,
    "hp_item": "红碗",
    "mp_enabled": True,
    "mp_item": "蓝碗",
    "mizhi_enabled": False,
    # 战斗操作
    "capture_bb_enabled": False,
    "miaoshou_enabled": True,
    "skill_then_auto": False,
    "normal_then_auto": False,
    "defend_then_auto": False,
    "direct_auto": False,
    "escape_enabled": True,
    "auto_path_enabled": True,
    "coord_enabled": True,
    # 妙手空空场景配置（参考图）
    "scene_config": [
        {"enabled": False, "scene": "龙窟五层", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "龙窟六层", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "凤巢三层", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "凤巢四层", "rings": "得3个环", "cards": "无要求", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "凤巢五层", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": True, "scene": "小西天", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "子母河底", "rings": "得3个环", "cards": "无要求", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "麒麟山", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": True, "scene": "女娲神迹", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
    ],
    # 检测参数
    "detect_params": {
        "hp_y": 6, "hp_xs": 756, "hp_xe": 799,
        "mp_y": 14, "mp_xs": 756, "mp_xe": 799,
        "bb_y": 6, "bb_xs": 654, "bb_xe": 697,
        "pp": 2.38,
    },
    # 四小人检测 ROI（流分辨率坐标）
    "four_person_roi": {"left": 540, "top": 170, "width": 880, "height": 380},
}


def get_device_config_file(serial):
    """获取设备独立配置文件路径"""
    os.makedirs(DEVICE_CONFIG_DIR, exist_ok=True)
    return os.path.join(DEVICE_CONFIG_DIR, f"{serial}.json")


def load_device_config(serial):
    """加载设备独立配置，如果不存在则返回None"""
    device_file = get_device_config_file(serial)
    if os.path.exists(device_file):
        try:
            with open(device_file, "r", encoding="utf-8") as f:
                # 只存真正要覆盖的键（局部覆盖）；不跑 migrate_config，
                # 避免默认键被迁移补齐后意外覆盖全局设置
                return json.load(f)
        except Exception:
            return None
    return None


def save_device_config(serial, cfg):
    """保存设备独立配置"""
    device_file = get_device_config_file(serial)
    try:
        os.makedirs(os.path.dirname(device_file), exist_ok=True)
        with open(device_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存设备配置失败: {e}")
        return False


def fmt_duration_hm(seconds):
    """把秒数格式化为"小时+分钟"显示：满1小时显示 X小时YY分，不足1小时显示 Y分钟"""
    total_minutes = int(seconds or 0) // 60
    h, m = divmod(total_minutes, 60)
    if h > 0:
        return f"{h}小时{m:02d}分"
    return f"{m}分钟"


def load_config():
    if os.path.exists(GUI_CONFIG_FILE):
        try:
            with open(GUI_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    else:
        cfg = {}
    return migrate_config(cfg)


def migrate_config(cfg):
    """把旧版/默认配置转成新版 UI 字段，兼容旧值"""
    valid_hp = {"酒肆", "红碗", "秘制"}
    valid_mp = {"酒肆", "蓝碗", "秘制"}

    if "hp_method" not in cfg or cfg.get("hp_method") not in valid_hp:
        if cfg.get("mizhi_enabled"):
            cfg["hp_method"] = "秘制"
        else:
            cfg["hp_method"] = cfg.get("hp_item", "酒肆") if cfg.get("hp_enabled") else "酒肆"
        if cfg["hp_method"] not in valid_hp:
            cfg["hp_method"] = "酒肆"

    if "mp_method" not in cfg or cfg.get("mp_method") not in valid_mp:
        if cfg.get("mizhi_enabled"):
            cfg["mp_method"] = "秘制"
        else:
            cfg["mp_method"] = cfg.get("mp_item", "酒肆") if cfg.get("mp_enabled") else "酒肆"
        if cfg["mp_method"] not in valid_mp:
            cfg["mp_method"] = "酒肆"

    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    # 确保 four_person_roi 存在
    cfg.setdefault("four_person_roi", {"left": 540, "top": 170, "width": 880, "height": 380})
    return cfg


def save_config(cfg):
    with open(GUI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ============== GUI 主界面 ==============
class AutoFightGUI:
    def __init__(self):
        self.root = ttk.Window(themename="litera")
        self.root.title("场景之妙手空空")
        self.root.geometry("930x860")
        self.root.minsize(800, 700)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # 立即显示"正在加载"覆盖层并渲染，贯穿整个构建期（UI 构建约需数秒）
        self._splash_overlay = self._create_splash_overlay()
        self.root.update()

        self.cfg = load_config()
        self.log_queue = queue.Queue()
        self.engine = None            # 当前绑定设备（Tab1 显示用）
        self.engine_thread = None
        self.engines = {}             # serial -> AutoFightEngine
        self.engine_threads = {}      # serial -> Thread
        self._device_widgets = {}     # serial -> {status, hp, mp, bb, bc}
        self._threshold_labels = {}
        self._selected_devices = set()  # 设备管理页勾选的设备
        self._device_configs = {}     # serial -> 设备独立配置缓存
        self._device_order = list(self.cfg.get("device_order", []) or [])
        self._device_stats_cache = self._load_device_stats()  # 今日设备统计缓存（环/卡按天累计）
        self._last_stats_save_t = time.time()   # 上次自动写盘时间（每60秒）
        self._drag_serial = None        # 拖拽排序：当前拖动的设备
        self._drag_y0 = 0               # 拖拽起始 y
        self._drag_widget = None        # 拖拽起始控件
        self._highlight_serial = None   # 设备表格：当前高亮行
        self._row_highlight_widgets = {}  # serial -> 行内可换背景的控件列表

        # 设备显示映射
        self._serial_to_display = {}  # 序列号 -> 显示文本
        self._display_to_serial = {}  # 显示文本 -> 序列号

        # GUI系统日志文件
        self.gui_log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self._gui_log_day_dir = None
        self.gui_log_file = self._gui_daily_log_file()

        self._init_vars()
        self._build_ui()
        self._refresh_devices()
        self._load_cfg_to_ui()

        # 构建完成：先渲染主界面一帧，再移除加载覆盖层（避免闪白）
        try:
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass
        self._remove_splash_overlay()
        self.root.update()

        # 启动日志轮询（延迟到UI完全加载后）
        self.root.after(100, self._start_log_polling)

    def _create_splash_overlay(self):
        """在窗口上方创建'正在加载'覆盖层（构建期间一直可见）"""
        try:
            frm = tk.Frame(self.root, bg="white")
            frm.place(relx=0, rely=0, relwidth=1, relheight=1)
            tk.Label(frm, text="⏳ 正在加载...", bg="white",
                     font=("Microsoft YaHei", 14, "bold")).place(relx=0.5, rely=0.45, anchor="center")
            tk.Label(frm, text="场景之妙手空空", bg="white",
                     font=("Microsoft YaHei", 10), foreground="gray").place(relx=0.5, rely=0.55, anchor="center")
            return frm
        except Exception:
            return None

    def _remove_splash_overlay(self):
        """移除加载覆盖层"""
        try:
            if self._splash_overlay is not None:
                self._splash_overlay.destroy()
                self._splash_overlay = None
        except Exception:
            pass

    def _start_log_polling(self):
        """启动日志轮询"""
        # 初始化日志筛选选项
        self._update_log_filter_options()
        self._poll_log()

        # 记录程序启动日志
        self._log("=" * 60)
        self._log(f"程序启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"日志目录: {self.gui_log_dir}")
        self._log("=" * 60)

    def _get_effective_config(self, serial):
        """获取设备的有效配置（全局为底，设备独立配置局部覆盖）"""
        # 优先从缓存获取
        if serial not in self._device_configs:
            device_cfg = load_device_config(serial)
            if device_cfg:
                self._device_configs[serial] = device_cfg
            else:
                self._device_configs[serial] = None

        # 全局配置为底，独立配置只覆盖其存储的键（缺的键自然跟随全局）
        result = dict(self.cfg)
        if self._device_configs[serial]:
            result.update(self._device_configs[serial])
        # 确保全局的设备顺序和名称配置也被合并
        result.setdefault("device_order", self.cfg.get("device_order", []))
        result.setdefault("device_names", self.cfg.get("device_names", {}))
        return result

    def _save_device_config(self, serial):
        """保存设备独立配置"""
        current_ui_config = {}
        self._sync_ui_to_config_obj(current_ui_config)

        # 保存到文件和缓存
        save_device_config(serial, current_ui_config)
        self._device_configs[serial] = current_ui_config
        self._log(f"[{serial}] 已保存设备独立配置")

    def _sync_ui_to_config_obj(self, config_obj):
        """将UI设置同步到配置对象"""
        config_obj["hp_method"] = self.hp_method.get()
        config_obj["mp_method"] = self.mp_method.get()
        config_obj["hp_threshold"] = self.hp_threshold.get()
        config_obj["mp_threshold"] = self.mp_threshold.get()

        hp = config_obj["hp_method"]
        mp = config_obj["mp_method"]

        if "秘制" in (hp, mp):
            config_obj["mizhi_enabled"] = True
            config_obj["hp_enabled"] = False
            config_obj["mp_enabled"] = False
        else:
            config_obj["mizhi_enabled"] = False
            config_obj["hp_enabled"] = (hp != "酒肆")
            config_obj["hp_item"] = hp if hp != "酒肆" else config_obj.get("hp_item", "红碗")
            config_obj["mp_enabled"] = (mp != "酒肆")
            config_obj["mp_item"] = mp if mp != "酒肆" else config_obj.get("mp_item", "蓝碗")

        config_obj["jiusi_enabled"] = (hp == "酒肆" or mp == "酒肆")
        config_obj["jiusi_hp_threshold"] = config_obj["hp_threshold"] if hp == "酒肆" else 0
        config_obj["jiusi_mp_threshold"] = config_obj["mp_threshold"] if mp == "酒肆" else 0
        config_obj["jiusi_bb_threshold"] = self.jiusi_bb_threshold.get()

        config_obj["map"] = self.map_select.get()
        config_obj["capture_bb_enabled"] = self.capture_bb_enabled.get()
        config_obj["miaoshou_enabled"] = self.miaoshou_enabled.get()
        _mode = self.combat_mode.get()
        config_obj["skill_then_auto"] = (_mode == "skill_then_auto")
        config_obj["normal_then_auto"] = (_mode == "normal_then_auto")
        config_obj["defend_then_auto"] = (_mode == "defend_then_auto")
        config_obj["direct_auto"] = (_mode == "direct_auto")
        config_obj["escape_enabled"] = (_mode == "escape")
        config_obj["auto_path_enabled"] = self.auto_path_enabled.get()
        config_obj["coord_enabled"] = self.coord_enabled.get()
        config_obj["use_local_four_person"] = self.local_four_person_enabled.get()
        config_obj["check_pkg_counts"] = self.check_pkg_counts_enabled.get()
        config_obj["use_real_scene_switch"] = self.real_scene_switch_enabled.get()
        config_obj["scene_config"] = self.cfg.get("scene_config", [])

    # ---------- 变量 ----------
    def _init_vars(self):
        cfg = self.cfg
        self.hp_method = tk.StringVar(value=cfg.get("hp_method", "酒肆"))
        self.hp_threshold = tk.IntVar(value=cfg.get("hp_threshold", 30))
        self.mp_method = tk.StringVar(value=cfg.get("mp_method", "酒肆"))
        self.mp_threshold = tk.IntVar(value=cfg.get("mp_threshold", 20))

        self.jiusi_enabled = tk.BooleanVar(value=cfg.get("jiusi_enabled", True))
        self.jiusi_hp_threshold = tk.IntVar(value=cfg.get("jiusi_hp_threshold", 50))
        self.jiusi_mp_threshold = tk.IntVar(value=cfg.get("jiusi_mp_threshold", 30))
        self.jiusi_bb_threshold = tk.IntVar(value=cfg.get("jiusi_bb_threshold", 50))

        self.capture_bb_enabled = tk.BooleanVar(value=cfg.get("capture_bb_enabled", False))
        self.miaoshou_enabled = tk.BooleanVar(value=cfg.get("miaoshou_enabled", True))
        # 战斗模式互斥：skill_then_auto / normal_then_auto / defend_then_auto / direct_auto / escape
        _mode = "escape"
        if cfg.get("skill_then_auto"): _mode = "skill_then_auto"
        elif cfg.get("normal_then_auto"): _mode = "normal_then_auto"
        elif cfg.get("defend_then_auto"): _mode = "defend_then_auto"
        elif cfg.get("direct_auto"): _mode = "direct_auto"
        elif cfg.get("escape_enabled", True): _mode = "escape"
        self.combat_mode = tk.StringVar(value=_mode)
        self.auto_path_enabled = tk.BooleanVar(value=cfg.get("auto_path_enabled", True))
        self.coord_enabled = tk.BooleanVar(value=cfg.get("coord_enabled", True))
        # 小霸王合并功能开关
        self.local_four_person_enabled = tk.BooleanVar(value=cfg.get("use_local_four_person", True))
        self.check_pkg_counts_enabled = tk.BooleanVar(value=cfg.get("check_pkg_counts", True))
        self.real_scene_switch_enabled = tk.BooleanVar(value=cfg.get("use_real_scene_switch", True))

        # 日志相关
        self.all_logs = []  # 存储所有日志

        # 功能测试页面设备映射
        self._test_display_to_serial = {}  # 显示文本 -> 序列号

    # ---------- UI 构建 ----------
    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ===== Tab 4(顺序1): 特殊场景 =====
        self._build_tab_special()

        # ===== Tab 1: 场景控制 =====
        main = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(main, text="场景控制")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        # ---- 标题 / 控制 ----
        header = ttk.Labelframe(main, text=" 场景之妙手空空 ", padding=12)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="场景之妙手空空",
                  font=("Microsoft YaHei", 16, "bold")).grid(row=0, column=0, sticky="w")

        hright = ttk.Frame(header)
        hright.grid(row=0, column=1, sticky="e")

        self.status_canvas = tk.Canvas(hright, width=18, height=18, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 6))
        self._draw_status("gray")

        self.status_label = ttk.Label(hright, text="就绪", font=("Microsoft YaHei", 10))
        self.status_label.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_start = ttk.Button(hright, text="▶ 启动", command=self.start_engine,
                                    width=10, bootstyle="success")
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_stop = ttk.Button(hright, text="⏹ 停止", command=self.stop_engine,
                                   width=10, bootstyle="danger", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(hright, text="📸 截图", command=self._take_screenshot,
                   width=10, bootstyle="outline").pack(side=tk.LEFT)

        # ---- 当前设备 ----
        dev_card = ttk.Labelframe(main, text=" 当前设备 ", padding=12)
        dev_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        dev_card.columnconfigure(1, weight=1)

        ttk.Label(dev_card, text="当前设备：").grid(row=0, column=0, sticky="w")
        self.dev_status = ttk.Label(dev_card, text="未绑定", foreground="gray",
                                    font=("Microsoft YaHei", 9))
        self.dev_status.grid(row=0, column=1, sticky="w", padx=(0, 10))

        self.device_combo = ttk.Combobox(dev_card, state="readonly", width=30, bootstyle="primary")
        self.device_combo.grid(row=0, column=2, padx=(0, 10))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)

        ttk.Button(dev_card, text="刷新", command=self._refresh_devices,
                   width=8, bootstyle="outline").grid(row=0, column=3, padx=(0, 6))
        ttk.Button(dev_card, text="绑定窗口", command=self._bind_window,
                   width=10, bootstyle="primary").grid(row=0, column=4)

        # ---- 场景 & 地图 ----
        scene_card = ttk.Labelframe(main, text=" 场景 & 地图 ", padding=12)
        scene_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        scene_card.columnconfigure(1, weight=1)
        scene_card.columnconfigure(3, weight=1)

        ttk.Label(scene_card, text="选择项目：").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.project_select = ttk.Combobox(scene_card, values=["点卡场景"],
                                           state="readonly", width=22, bootstyle="primary")
        self.project_select.grid(row=0, column=1, sticky="w", padx=(0, 25))
        self.project_select.set("点卡场景")

        ttk.Label(scene_card, text="地图选择：").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.map_select = ttk.Combobox(scene_card, values=list(MAP_CONFIG),
                                       state="readonly", width=18, bootstyle="primary")
        self.map_select.grid(row=0, column=3, sticky="w", padx=(0, 25))
        self.map_select.bind("<<ComboboxSelected>>", lambda e: self._on_setting_change())

        ttk.Button(scene_card, text="妙手空空场景设置", command=self._open_scene_settings,
                   width=18, bootstyle="warning").grid(row=0, column=4, sticky="e", padx=(0, 6))

        # ---- 人物补给设置 ----
        supply_card = ttk.Labelframe(main, text=" 人物补给设置 ", padding=12)
        supply_card.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        supply_card.columnconfigure(3, weight=1)

        self._add_supply_row(
            supply_card, 0,
            label="人物血量低于时补充：",
            method_var=self.hp_method,
            method_values=["酒肆", "红碗", "秘制"],
            threshold_var=self.hp_threshold,
            bootstyle="danger",
            key="hp",
        )
        self._add_supply_row(
            supply_card, 1,
            label="人物蓝量低于时补充：",
            method_var=self.mp_method,
            method_values=["酒肆", "蓝碗", "秘制"],
            threshold_var=self.mp_threshold,
            bootstyle="info",
            key="mp",
        )

        ttk.Label(supply_card,
                  text="💡 选择「酒肆」时，低于阈值会在战斗结束后自动触发酒肆→休息",
                  foreground="gray", font=("Microsoft YaHei", 9)).grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))

        # ---- 人物战斗操作 ----
        battle_card = ttk.Labelframe(main, text=" 人物战斗操作 ", padding=12)
        battle_card.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        battle_card.columnconfigure(0, weight=1)

        left = ttk.Frame(battle_card)
        left.grid(row=0, column=0, sticky="nsw")

        # 一、二 为独立勾选
        capture_frame = ttk.Frame(left)
        capture_frame.grid(row=0, column=0, sticky="w", pady=4)
        ttk.Checkbutton(capture_frame, text="一、捕捉", variable=self.capture_bb_enabled,
                        bootstyle="success-round-toggle").pack(side=tk.LEFT)
        ttk.Button(capture_frame, text="配置", command=self._show_capture_blacklist_config,
                  bootstyle="info-outline", width=6).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Checkbutton(left, text="二、妙手空空", variable=self.miaoshou_enabled,
                        bootstyle="success-round-toggle").grid(row=1, column=0, sticky="w", pady=4)
        # 三、战斗模式 5选1 互斥
        ttk.Label(left, text="三、人物战斗操作：").grid(row=2, column=0, sticky="w", pady=(8,2))
        modes = [
            ("1.点选技能后自动战斗", "skill_then_auto"),
            ("2.普通攻击后自动战斗", "normal_then_auto"),
            ("3.防御后自动战斗", "defend_then_auto"),
            ("4.直接自动战斗", "direct_auto"),
            ("5.逃跑", "escape"),
        ]
        for j, (txt, val) in enumerate(modes):
            ttk.Radiobutton(left, text=txt, variable=self.combat_mode, value=val).grid(
                row=3+j, column=0, sticky="w", pady=2, padx=(16,0))

        right = ttk.Frame(battle_card)
        right.grid(row=0, column=1, sticky="ne")
        ttk.Checkbutton(right, text="自动寻路", variable=self.auto_path_enabled,
                        bootstyle="success-round-toggle").grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(right, text="坐标检测", variable=self.coord_enabled,
                        bootstyle="success-round-toggle").grid(row=1, column=0, sticky="w", pady=(4,0))
        ttk.Checkbutton(right, text="本地四小人识别", variable=self.local_four_person_enabled,
                        bootstyle="success-round-toggle").grid(row=2, column=0, sticky="w", pady=(4,0))
        ttk.Checkbutton(right, text="背包环/卡计数", variable=self.check_pkg_counts_enabled,
                        bootstyle="success-round-toggle").grid(row=3, column=0, sticky="w", pady=(4,0))
        ttk.Checkbutton(right, text="真实切场导航", variable=self.real_scene_switch_enabled,
                        bootstyle="success-round-toggle").grid(row=4, column=0, sticky="w", pady=(4,0))

        # ---- 底部 ----
        bottom = ttk.Frame(main)
        bottom.grid(row=6, column=0, sticky="ew")
        ttk.Button(bottom, text="保存配置", command=self._save_cfg,
                   bootstyle="primary").pack(side=tk.LEFT)

        # ===== Tab 2: 设备管理 =====
        self._build_tab2()

        # ===== Tab 3: 功能测试 =====
        self._build_tab3()

        # 调整 Tab 顺序：设备管理放最前，场景控制次之，功能测试最后
        # （注意：add() 对已存在的组件不会移动，必须用 insert()）
        self.notebook.insert(0, self._tab2_frame)   # 设备管理
        self.notebook.insert(1, self._tab_special_frame)  # 特殊场景
        self.notebook.insert(2, main)               # 场景控制
        self.notebook.insert(3, self._tab3_frame)   # 功能测试
        # insert 只改顺序、不改当前选中页，需显式选中设备管理（启动默认展示）
        self.notebook.select(self._tab2_frame)

    # ---------- 辅助 UI ----------
    def _add_supply_row(self, parent, row, label, method_var, method_values,
                        threshold_var, bootstyle, key):
        ttk.Label(parent, text=label, font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10))

        cb = ttk.Combobox(parent, textvariable=method_var, values=method_values,
                          state="readonly", width=12, bootstyle=bootstyle)
        cb.grid(row=row, column=1, sticky="w", padx=(0, 20))
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_setting_change())

        ttk.Label(parent, text="低于").grid(row=row, column=2, sticky="w")

        slider_frame = ttk.Frame(parent)
        slider_frame.grid(row=row, column=3, sticky="ew", padx=(5, 0))
        slider_frame.columnconfigure(0, weight=1)

        scale = ttk.Scale(slider_frame, from_=0, to=100, variable=threshold_var,
                          orient=tk.HORIZONTAL, length=240, bootstyle=bootstyle,
                          command=lambda v: self._on_slider_change(key, v))
        scale.grid(row=0, column=0, sticky="ew")

        val_label = ttk.Label(slider_frame, text=f"{threshold_var.get()}%", width=4)
        val_label.grid(row=0, column=1, padx=(8, 0))
        self._threshold_labels[key] = val_label

    def _add_jiusi_row(self, parent, row, label, threshold_var, bootstyle, key):
        ttk.Label(parent, text=label, font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10))

        slider_frame = ttk.Frame(parent)
        slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 0))
        slider_frame.columnconfigure(0, weight=1)

        scale = ttk.Scale(slider_frame, from_=0, to=100, variable=threshold_var,
                          orient=tk.HORIZONTAL, length=280, bootstyle=bootstyle,
                          command=lambda v: self._on_slider_change(key, v))
        scale.grid(row=0, column=0, sticky="ew")

        val_label = ttk.Label(slider_frame, text=f"{threshold_var.get()}%", width=4)
        val_label.grid(row=0, column=1, padx=(8, 0))
        self._threshold_labels[key] = val_label

    def _on_slider_change(self, key, value):
        self._threshold_labels[key].configure(text=f"{int(float(value))}%")

    def _update_all_threshold_labels(self):
        for key, var in [
            ("hp", self.hp_threshold),
            ("mp", self.mp_threshold),
            ("jhp", self.jiusi_hp_threshold),
            ("jmp", self.jiusi_mp_threshold),
            ("jbb", self.jiusi_bb_threshold),
        ]:
            if key in self._threshold_labels:
                self._threshold_labels[key].configure(text=f"{var.get()}%")

    def _draw_status(self, color):
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 16, 16, fill=color, outline="")

    # ---------- Tab2: 设备管理 ----------
    def _build_tab2(self):
        """构建设备管理 Tab（ttkbootstrap 风格）"""
        # 设备行操作栏小按钮样式：复制场景控制按钮配色，缩小字体与内边距
        style = ttk.Style()
        for src, dst in [
            ("success.TButton", "SmallSuccess.TButton"),
            ("danger.TButton", "SmallDanger.TButton"),
            ("Outline.TButton", "SmallOutline.TButton"),
        ]:
            opts = dict(style.configure(src) or {})
            opts["font"] = ("Microsoft YaHei", 8)
            opts["padding"] = (6, 2)
            style.configure(dst, **opts)
            style.map(dst, **style.map(src))

        tab2 = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab2, text="设备管理")
        self._tab2_frame = tab2   # 用于调整 Tab 顺序（设备管理放最前）
        tab2.columnconfigure(0, weight=1)
        tab2.rowconfigure(1, weight=3)   # 设备列表
        tab2.rowconfigure(2, weight=2)   # 运行日志 & 实时数据

        # 顶部操作栏
        top_frame = ttk.Frame(tab2)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(top_frame, text="刷新设备", command=self._refresh_device_tab,
                   width=10, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(top_frame, text="配置模板", command=self._show_config_templates,
                   width=10, bootstyle="info").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(top_frame, text="列出所有 ADB 设备，可独立控制每台设备的启停",
                  foreground="gray", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        # 右侧批量操作按钮
        batch_frame = ttk.Frame(top_frame)
        batch_frame.pack(side=tk.RIGHT)
        ttk.Button(batch_frame, text="▶ 一键启动", width=10, bootstyle="success",
                   command=self._start_selected_devices).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(batch_frame, text="⏹ 一键停止", width=10, bootstyle="danger",
                   command=self._stop_selected_devices).pack(side=tk.LEFT)

        # 设备列表面板（Canvas + Scrollbar）
        canvas_frame = ttk.Frame(tab2)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.dev_canvas = tk.Canvas(canvas_frame, highlightthickness=0,
                                    bg=self.root.style.lookup("TFrame", "background"))
        self.dev_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                                           command=self.dev_canvas.yview)
        self.dev_list_frame = ttk.Frame(self.dev_canvas)
        self.dev_list_frame.bind("<Configure>", self._on_dev_list_configure)
        self._dev_canvas_win = self.dev_canvas.create_window((0, 0), window=self.dev_list_frame, anchor="nw")
        self.dev_canvas.bind("<Configure>", self._on_dev_canvas_resize)
        self.dev_canvas.configure(yscrollcommand=self.dev_scrollbar.set)
        self.dev_canvas.grid(row=0, column=0, sticky="nsew")
        self.dev_scrollbar.grid(row=0, column=1, sticky="ns")
        self.dev_canvas.bind("<Enter>",
            lambda e: self.dev_canvas.bind_all(
                "<MouseWheel>",
                lambda ev: self.dev_canvas.yview_scroll(-1 * (ev.delta // 120), "units")))
        self.dev_canvas.bind("<Leave>",
            lambda e: self.dev_canvas.unbind_all("<MouseWheel>"))

        self._refresh_device_tab()

        # ---- 运行日志 & 实时数据（设备列表下方） ----
        log_card = ttk.Labelframe(tab2, text=" 运行日志 & 实时数据 ", padding=10)
        log_card.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        # 实时数据显示行（含日志筛选，位于气血/魔法等数据最前面）
        data_frame = ttk.Frame(log_card)
        data_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # 日志筛选
        ttk.Label(data_frame, text="日志筛选：").pack(side=tk.LEFT, padx=(0, 6))

        self.log_filter_var = tk.StringVar(value="全部设备")
        self.log_filter_combo = ttk.Combobox(data_frame, textvariable=self.log_filter_var,
                                             state="readonly", width=15, bootstyle="info")
        self.log_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.log_filter_combo.bind("<<ComboboxSelected>>", self._on_log_filter_change)

        ttk.Label(data_frame, text="|", foreground="gray").pack(side=tk.LEFT, padx=5)

        self.log_count_label = ttk.Label(data_frame, text="共 0 条", foreground="gray", font=("Microsoft YaHei", 9))
        self.log_count_label.pack(side=tk.LEFT, padx=(5, 15))

        self.hp_display = ttk.Label(data_frame, text="气血: --%",
                                    font=("Microsoft YaHei", 11, "bold"), foreground="#e83e8c")
        self.hp_display.pack(side=tk.LEFT, padx=(0, 20))
        self.mp_display = ttk.Label(data_frame, text="魔法: --%",
                                    font=("Microsoft YaHei", 11, "bold"), foreground="#0d6efd")
        self.mp_display.pack(side=tk.LEFT, padx=(0, 20))
        self.bb_display = ttk.Label(data_frame, text="BB: --%",
                                    font=("Microsoft YaHei", 11, "bold"), foreground="#6c757d")
        self.bb_display.pack(side=tk.LEFT, padx=(0, 20))
        self.coord_display = ttk.Label(data_frame, text="📍 --",
                                       font=("Microsoft YaHei", 11, "bold"), foreground="#6f42c1")
        self.coord_display.pack(side=tk.LEFT)

        self.battle_display = ttk.Label(data_frame, text="⚔ -- 场",
                                    font=("Microsoft YaHei", 11, "bold"), foreground="#fd7e14")
        self.battle_display.pack(side=tk.LEFT, padx=(0, 20))

        self.time_display = ttk.Label(data_frame, text="⏱ 00:00",
                                    font=("Microsoft YaHei", 11, "bold"), foreground="#198754")
        self.time_display.pack(side=tk.LEFT)

        # 存储所有日志（用于筛选）
        self.all_logs = []  # 格式: [(device_id, timestamp, message), ...]

        # 日志文本框
        self.log_text = ttk.ScrolledText(
            log_card, height=8, font=("Microsoft YaHei", 9),
            bg="#ffffff", fg="#333333", insertbackground="#333333")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        self.log_text.configure(state=tk.DISABLED)
        # 滚轮翻看历史：向上滚暂停自动滚动，滚回底部自动恢复
        self.log_text.bind("<MouseWheel>", self._on_log_scroll)
        self.log_text.bind("<Button-4>", self._on_log_scroll)   # Linux 上滚
        self.log_text.bind("<Button-5>", self._on_log_scroll)   # Linux 下滚

        # 日志工具条（独立一行，避免被实时数据行挤压）
        tool_bar = ttk.Frame(log_card)
        tool_bar.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.log_follow = tk.BooleanVar(value=True)   # 自动滚动跟随最新日志
        ttk.Checkbutton(tool_bar, text="自动滚动", variable=self.log_follow,
                        bootstyle="success-round-toggle").pack(side=tk.LEFT)
        ttk.Button(tool_bar, text="清空日志", command=self._clear_log,
                   bootstyle="outline", width=8).pack(side=tk.RIGHT)

    def _on_dev_canvas_resize(self, event):
        """让内部框自适应画布宽度"""
        self.dev_canvas.itemconfig(self._dev_canvas_win, width=event.width)
        self._on_dev_list_configure()

    def _on_dev_list_configure(self, event=None):
        """内容变化时更新滚动区域，并自动隐藏/显示滚动条"""
        self.dev_canvas.configure(scrollregion=self.dev_canvas.bbox("all"))
        bbox = self.dev_canvas.bbox("all")
        if bbox and bbox[3] <= self.dev_canvas.winfo_height():
            self.dev_scrollbar.grid_remove()
        else:
            self.dev_scrollbar.grid()

    # ---------- Tab3: 功能测试 ----------
    def _build_tab3(self):
        """功能测试 Tab：本地四小人识别（上传图片）/ 背包环卡 / 切换地图"""
        tab3 = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab3, text="功能测试")
        self._tab3_frame = tab3   # 用于调整 Tab 顺序
        tab3.columnconfigure(0, weight=1)
        tab3.rowconfigure(2, weight=1)

        # 设备 + 地图选择
        sel = ttk.Labelframe(tab3, text=" 选择设备 / 地图 ", padding=10)
        sel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(sel, text="设备：").grid(row=0, column=0, sticky="w")
        self.test_device_combo = ttk.Combobox(sel, state="readonly", width=26, bootstyle="primary")
        self.test_device_combo.grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Button(sel, text="刷新", command=self._refresh_test_devices,
                   width=6, bootstyle="outline").grid(row=0, column=2, sticky="w", padx=(0, 16))
        ttk.Label(sel, text="忠诚恢复场景：").grid(row=0, column=3, sticky="w")
        self.test_map_combo = ttk.Combobox(sel, state="readonly", width=16)
        self.test_map_combo.grid(row=0, column=4, sticky="w")

        # 忠诚恢复支持的场景；其余地图仍可用于“测试切换地图”
        try:
            from 工具 import SCENE_RECOVERY
            recovery_scenes = list(SCENE_RECOVERY.keys())
        except Exception:
            recovery_scenes = ["小西天", "女娲神迹", "子母河底", "龙窟三层", "凤巢三层"]
        try:
            scene_cfg = self.cfg.get("scene_config", []) or []
            preferred = []
            for r in scene_cfg:
                s = r.get("scene")
                if s in recovery_scenes and s not in preferred:
                    preferred.append(s)
            recovery_scenes = preferred + [s for s in recovery_scenes if s not in preferred]
        except Exception:
            pass
        self.test_map_combo["values"] = recovery_scenes
        if recovery_scenes:
            self.test_map_combo.current(0)

        # 测试按钮
        btns = ttk.Frame(tab3)
        btns.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(btns, text="① 本地识别四小人（上传图片）", bootstyle="primary",
                   command=self._test_four_person_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btns, text="② 测试背包环/卡", bootstyle="success",
                   command=self._test_backpack).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btns, text="③ 测试切换地图", bootstyle="warning",
                   command=self._test_switch_map).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btns, text="④ 测试忠诚度恢复", bootstyle="info",
                   command=self._test_loyalty_recovery).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btns, text="⏹ 停止", bootstyle="danger",
                   command=self._test_stop).pack(side=tk.LEFT)

        self._test_stop_event = threading.Event()

        # 图片预览区
        preview = ttk.Labelframe(tab3, text=" 识别预览（四小人 / 背包环卡标注） ", padding=6)
        preview.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(0, weight=1)
        self._test_photo = None
        self.test_image_label = ttk.Label(preview, text="四小人识别/背包环卡标注会显示在这里",
                                          anchor="center", bootstyle="secondary")
        self.test_image_label.grid(row=0, column=0, sticky="nsew")

        # 测试日志区
        log_card = ttk.Labelframe(tab3, text=" 测试日志 ", padding=6)
        log_card.grid(row=3, column=0, sticky="ew")
        log_card.columnconfigure(0, weight=1)
        self.test_log_text = tk.Text(log_card, height=6, font=("Microsoft YaHei", 9),
                                     state=tk.DISABLED, wrap="word")
        self.test_log_text.grid(row=0, column=0, sticky="ew")
        tlog_sb = ttk.Scrollbar(log_card, orient=tk.VERTICAL, command=self.test_log_text.yview)
        tlog_sb.grid(row=0, column=1, sticky="ns")
        self.test_log_text.configure(yscrollcommand=tlog_sb.set)

        # 初始化设备列表
        self._refresh_test_devices()

    # ---------- Tab: 特殊场景（队伍抓特殊） ----------
    def _build_tab_special(self):
        """特殊场景 Tab：设备入队 + 场景/角色分配 + 队长一键启动队伍。

        每台设备按分配的场景执行不同抓捕逻辑（引擎按 MAP_CONFIG 场景分支），
        队长=猎术号（捕捉+妙手空空），队员=防御（等待队长抓完）。
        """
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="特殊场景")
        self._tab_special_frame = tab   # 用于调整 Tab 顺序（放在设备管理之后）
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=3)   # 队伍设备列表
        tab.rowconfigure(2, weight=2)   # 队伍日志

        # ---- 顶部操作栏 ----
        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(top, text="刷新设备", command=self._refresh_special_devices,
                   width=10, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(top, text="全选", command=lambda: self._special_set_all(True),
                   width=6, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="全不选", command=lambda: self._special_set_all(False),
                   width=7, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(top,
                  text="勾选设备入队，分配场景与角色；队长(猎术号)抓特殊/宝宝，队员防御。",
                  foreground="gray", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT)
        ttk.Button(right, text="保存队伍", command=self._save_team_cfg,
                   width=10, bootstyle="info").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(right, text="▶ 一键启动队伍", command=self._start_team,
                   width=14, bootstyle="success").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(right, text="⏹ 停止队伍", command=self._stop_team,
                   width=12, bootstyle="danger").pack(side=tk.LEFT)

        # ---- 队伍设备列表（Canvas + Scrollbar，与设备管理页一致） ----
        canvas_frame = ttk.Frame(tab)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self._special_canvas = tk.Canvas(
            canvas_frame, highlightthickness=0,
            bg=self.root.style.lookup("TFrame", "background"))
        self._special_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self._special_canvas.yview)
        self._special_list_frame = ttk.Frame(self._special_canvas)
        self._special_list_frame.bind(
            "<Configure>",
            lambda e: self._special_canvas.configure(
                scrollregion=self._special_canvas.bbox("all")))
        self._special_canvas_win = self._special_canvas.create_window(
            (0, 0), window=self._special_list_frame, anchor="nw")
        self._special_canvas.bind(
            "<Configure>",
            lambda e: self._special_canvas.itemconfig(
                self._special_canvas_win, width=e.width))
        self._special_canvas.configure(yscrollcommand=self._special_scrollbar.set)
        self._special_canvas.grid(row=0, column=0, sticky="nsew")
        self._special_scrollbar.grid(row=0, column=1, sticky="ns")

        self._special_sel_vars = {}     # serial -> BooleanVar(入队)
        self._special_row_widgets = {}  # serial -> {scene_cb, role_cb, status_lbl}
        self._special_scenes = {}       # serial -> 场景
        self._special_roles = {}        # serial -> "captain"/"member"
        self._special_ordered = []

        self._lbl_team_summary = ttk.Label(
            tab, text="队伍: 0 台设备 | 队长: 无",
            font=("Microsoft YaHei", 10, "bold"), foreground="#0d6efd")
        self._lbl_team_summary.grid(row=1, column=0, sticky="sw", pady=(4, 0))

        # ---- 队伍日志 ----
        log_card = ttk.Labelframe(tab, text=" 队伍日志 ", padding=8)
        log_card.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)
        self._special_log_text = ttk.ScrolledText(
            log_card, height=9, font=("Microsoft YaHei", 9),
            state=tk.DISABLED)
        self._special_log_text.grid(row=0, column=0, sticky="nsew")

        self._refresh_special_devices()
        self._load_team_cfg()
        self.root.after(1500, self._special_poll_status)

    # ------------------------------------------------------------------
    def _refresh_special_devices(self):
        """刷新特殊场景队伍设备列表"""
        for w in self._special_list_frame.winfo_children():
            w.destroy()
        self._special_sel_vars.clear()
        self._special_row_widgets.clear()

        devices = list_adb_devices()
        if not devices:
            ttk.Label(self._special_list_frame, text="未发现 ADB 设备",
                      foreground="orange", font=("Microsoft YaHei", 10)).pack(pady=20)
            self._special_ordered = []
            self._update_team_summary()
            return

        ordered = [s for s in self._special_ordered if s in devices]
        for s in devices:
            if s not in ordered:
                ordered.append(s)
        self._special_ordered = ordered

        # 表头
        head = ttk.Frame(self._special_list_frame)
        head.pack(fill=tk.X, pady=(0, 4))
        head.columnconfigure(1, weight=2)
        head.columnconfigure(2, weight=1)
        head.columnconfigure(3, weight=1)
        ttk.Label(head, text="入队", font=("Microsoft YaHei", 9, "bold")).grid(
            row=0, column=0, padx=6)
        ttk.Label(head, text="设备序列号", font=("Microsoft YaHei", 9, "bold")).grid(
            row=0, column=1, sticky="w")
        ttk.Label(head, text="场景", font=("Microsoft YaHei", 9, "bold")).grid(
            row=0, column=2, sticky="w")
        ttk.Label(head, text="角色", font=("Microsoft YaHei", 9, "bold")).grid(
            row=0, column=3, sticky="w")
        ttk.Label(head, text="状态", font=("Microsoft YaHei", 9, "bold")).grid(
            row=0, column=4, padx=8)

        for serial in ordered:
            self._special_add_row(serial)
        self._update_team_summary()

    def _special_add_row(self, serial):
        row = ttk.Frame(self._special_list_frame)
        row.pack(fill=tk.X, pady=2)
        row.columnconfigure(1, weight=2)
        row.columnconfigure(2, weight=1)
        row.columnconfigure(3, weight=1)

        var = tk.BooleanVar(value=True)
        self._special_sel_vars[serial] = var
        var.trace_add("write", lambda *a: self._update_team_summary())
        ttk.Checkbutton(row, variable=var, bootstyle="success-round-toggle").grid(
            row=0, column=0, padx=6)

        ttk.Label(row, text=short_dev_label(serial),
                  font=("Consolas", 9)).grid(row=0, column=1, sticky="w")

        scene = self._special_scenes.get(serial, SPECIAL_SCENES[0] if SPECIAL_SCENES else "小西天")
        scene_cb = ttk.Combobox(row, values=SPECIAL_SCENES,
                                state="readonly", width=12, bootstyle="info")
        scene_cb.set(scene)
        scene_cb.grid(row=0, column=2, sticky="w", padx=(0, 8))

        role = self._special_roles.get(serial, "member")
        role_cb = ttk.Combobox(row, values=["队长(猎术号-抓)", "队员(防御)"],
                               state="readonly", width=16, bootstyle="primary")
        role_cb.set("队长(猎术号-抓)" if role == "captain" else "队员(防御)")
        role_cb.grid(row=0, column=3, sticky="w", padx=(0, 8))
        role_cb.bind("<<ComboboxSelected>>", lambda e: self._update_team_summary())

        status_lbl = ttk.Label(row, text="停止", foreground="gray",
                               font=("Microsoft YaHei", 9))
        status_lbl.grid(row=0, column=4, padx=8)

        self._special_row_widgets[serial] = {
            "scene_cb": scene_cb,
            "role_cb": role_cb,
            "status_lbl": status_lbl,
        }

    def _special_set_all(self, checked):
        for var in self._special_sel_vars.values():
            var.set(checked)
        self._update_team_summary()

    def _collect_team_members(self):
        """读取队伍配置：[{serial, scene, is_captain}]"""
        members = []
        for serial in self._special_ordered:
            var = self._special_sel_vars.get(serial)
            if var is None or not var.get():
                continue
            w = self._special_row_widgets.get(serial)
            if w is None:
                continue
            scene = w["scene_cb"].get() or (self._special_scenes.get(serial) or SPECIAL_SCENES[0])
            is_captain = w["role_cb"].get().startswith("队长")
            members.append({
                "serial": serial,
                "scene": scene,
                "is_captain": is_captain,
            })
        return members

    def _update_team_summary(self):
        members = self._collect_team_members()
        captain = next((m["serial"] for m in members if m["is_captain"]), None)
        self._lbl_team_summary.configure(
            text="队伍: %d 台设备 | 队长: %s" % (
                len(members), short_dev_label(captain) if captain else "无"))

    # ------------------------------------------------------------------
    def _start_team(self):
        """一键启动队伍：队长先启动（抓），队员后启动（防御）。"""
        members = self._collect_team_members()
        if not members:
            messagebox.showwarning("提示", "请至少勾选一台设备加入队伍")
            return
        if not any(m["is_captain"] for m in members):
            messagebox.showwarning("提示", "请将一台设备设置为队长（猎术号）")
            return
        self._stop_team()

        ordered = sorted(members, key=lambda m: 0 if m["is_captain"] else 1)
        for m in ordered:
            override = {
                "map": m["scene"],
                "capture_bb_enabled": m["is_captain"],
                "miaoshou_enabled": m["is_captain"],
                # 队员：防御后自动战斗；队长：保留全局战斗模式（默认逃跑）
                "defend_then_auto": not m["is_captain"],
                "skill_then_auto": False,
                "normal_then_auto": False,
                "direct_auto": False,
                "escape_enabled": m["is_captain"],
                "auto_path_enabled": m["is_captain"],
                "coord_enabled": True,
                "check_pkg_counts": True,
                "use_real_scene_switch": m["is_captain"],
            }
            self._team_log("[%s] 入队 scene=%s role=%s" % (
                short_dev_label(m["serial"]), m["scene"],
                "队长(抓)" if m["is_captain"] else "队员(防御)"))
            self._start_device(m["serial"], override=override)
        self._save_team_cfg()
        self._team_log("▶ 队伍启动完成（%d 台）" % len(ordered))

    def _stop_team(self):
        members = self._collect_team_members()
        if not members:
            return
        for m in members:
            self._stop_device(m["serial"])
        self._team_log("⏹ 队伍已停止（%d 台）" % len(members))

    def _special_poll_status(self):
        """定时刷新队伍设备状态"""
        try:
            for serial, w in self._special_row_widgets.items():
                eng = self.engines.get(serial)
                if eng and getattr(eng, "running", False):
                    w["status_lbl"].configure(
                        text="运行中", foreground="green")
                else:
                    w["status_lbl"].configure(
                        text="停止", foreground="gray")
        except Exception:
            pass
        try:
            self.root.after(1500, self._special_poll_status)
        except Exception:
            pass

    def _team_log(self, msg):
        try:
            self._special_log_text.configure(state=tk.NORMAL)
            self._special_log_text.insert(tk.END, time.strftime("[%H:%M:%S] ") + msg + "\n")
            self._special_log_text.see(tk.END)
            self._special_log_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _save_team_cfg(self):
        data = {"devices": self._collect_team_members()}
        try:
            with open(TEAM_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._team_log("队伍配置已保存: %s" % TEAM_CONFIG_FILE)
        except Exception as e:
            self._team_log("保存队伍配置失败: %s" % e)

    def _load_team_cfg(self):
        if not os.path.exists(TEAM_CONFIG_FILE):
            return
        try:
            with open(TEAM_CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for dev in data.get("devices", []):
                self._special_scenes[dev["serial"]] = dev.get("scene", SPECIAL_SCENES[0])
                self._special_roles[dev["serial"]] = (
                    "captain" if dev.get("is_captain") else "member")
            self._apply_team_cfg_to_rows()
            self._team_log("已加载队伍配置（%d 台）" % len(data.get("devices", [])))
        except Exception as e:
            self._team_log("加载队伍配置失败: %s" % e)

    def _apply_team_cfg_to_rows(self):
        """把已加载的队伍配置应用到现有行控件"""
        for serial, w in self._special_row_widgets.items():
            if serial in self._special_scenes:
                try:
                    w["scene_cb"].set(self._special_scenes[serial])
                except Exception:
                    pass
            if serial in self._special_roles:
                try:
                    w["role_cb"].set(
                        "队长(猎术号-抓)" if self._special_roles[serial] == "captain"
                        else "队员(防御)")
                except Exception:
                    pass
    def _refresh_test_devices(self):
        """刷新功能测试页的设备下拉列表（显示设备名称）"""
        try:
            devs = list_adb_devices()
            dev_names = self.cfg.get("device_names", {})

            # 构建显示列表
            display_list = []
            self._test_display_to_serial = {}

            for serial in devs:
                name = dev_names.get(serial, "")
                if name:
                    display_text = f"{name} ({serial})"
                else:
                    display_text = serial
                display_list.append(display_text)
                self._test_display_to_serial[display_text] = serial

            self.test_device_combo["values"] = display_list
            cur = self.test_device_combo.get()
            self.test_device_combo.set(cur if cur in display_list else (display_list[0] if display_list else ""))
            self._log(f"功能测试：检测到 {len(devs)} 台设备")
        except Exception as e:
            self._log(f"功能测试：刷新设备失败 {e}")

    def _test_log(self, msg):
        """测试页日志：写入页内日志区并同步到主日志。"""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        try:
            self.test_log_text.configure(state=tk.NORMAL)
            self.test_log_text.insert(tk.END, line + "\n")
            self.test_log_text.see(tk.END)
            self.test_log_text.configure(state=tk.DISABLED)
        except Exception:
            pass
        self._log(f"[测试] {msg}")

    def _test_stop(self):
        """停止按钮：置位停止信号，长任务在下一次取帧/点击时中断。"""
        self._test_stop_event.set()
        self._test_log("⏹ 停止信号已发送，正在等待当前步骤结束...")

    # ---------- 测试动作 ----------
    def _test_four_person_image(self):
        """上传图片 -> 本地识别四小人 -> 标注显示"""
        path = filedialog.askopenfilename(
            title="选择游戏截图（四小人界面）",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")])
        if not path:
            return
        threading.Thread(target=self._run_four_person_image_test, args=(path,), daemon=True).start()

    def _run_four_person_image_test(self, path):
        def log(msg):
            self.root.after(0, lambda m=msg: self._test_log(m))
        log(f"开始本地识别：{path}")
        try:
            import cv2
            import numpy as np
            frame = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                log("❌ 图片读取失败")
                return
            from xbw_features.four_person.tester import analyze_four_person_image
            result = analyze_four_person_image(frame)
            if result is None or result.get("frame") is None:
                log("❌ 识别失败：" + str(result.get("error", "未知")))
                return
            rgb = cv2.cvtColor(result["frame"], cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            scale = min(1.0, 760.0 / w)
            if scale < 1.0:
                rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)))
            from PIL import Image, ImageTk
            img = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(img)
            self.root.after(0, lambda p=photo, r=result: self._show_test_image(p, r))
            log(f"识别结果：ROI={result['roi']} 最佳槽位={result['best_index']} "
                f"置信度={result['best_prob']:.4f} 点击点={result['click_point']}")
            log("各槽位：" + "  ".join(f"slot{i}={p:.2f}" for i, p in result["slots"]))
            log("✅ 本地识别成功" if result["success"] else "⚠️ 最高置信度不足 0.8（可能不是四小人界面）")
        except Exception as e:
            log(f"❌ 识别异常：{e}")

    def _show_test_image(self, photo, result):
        self._test_photo = photo
        self.test_image_label.configure(image=photo, text="")

    def _show_bag_annotation(self, bag_frame, result):
        """在背包截图上标注检测到的环（红圈）/卡（绿圈）并显示。"""
        try:
            import cv2
            import numpy as np
            from PIL import Image, ImageDraw, ImageFont
            ann = bag_frame.copy()
            for x, y in result.get("ring_points", []):
                cv2.circle(ann, (int(x), int(y)), 14, (0, 0, 255), 3)
            for x, y in result.get("card_points", []):
                cv2.circle(ann, (int(x), int(y)), 14, (0, 200, 0), 3)
            # 中文标注用 PIL + 系统字体（OpenCV putText 不支持中文）
            font = self._test_cn_font(28)
            pil = Image.fromarray(cv2.cvtColor(ann, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil)
            for x, y in result.get("ring_points", []):
                draw.text((int(x) - 14, int(y) - 30), "环", font=font, fill=(255, 0, 0))
            for x, y in result.get("card_points", []):
                draw.text((int(x) - 14, int(y) - 30), "卡", font=font, fill=(0, 200, 0))
            ann = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            rgb = cv2.cvtColor(ann, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            scale = min(1.0, 760.0 / w)
            if scale < 1.0:
                rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)))
            from PIL import ImageTk
            self._test_photo = ImageTk.PhotoImage(Image.fromarray(rgb))
            self.test_image_label.configure(image=self._test_photo, text="")
        except Exception as e:
            self._test_log(f"⚠️ 背包标注显示失败：{e}")

    def _test_cn_font(self, size):
        """取一个可用的中文字体（微软雅黑/黑体/宋体）。"""
        from PIL import ImageFont
        for path in (r"C:/Windows/Fonts/msyh.ttc",
                     r"C:/Windows/Fonts/simhei.ttf",
                     r"C:/Windows/Fonts/simsun.ttc"):
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _test_backpack(self):
        serial = self.test_device_combo.get().strip()
        if not serial:
            self._log("请先在功能测试页签选择设备")
            return
        # 从显示文本中提取序列号
        serial = self._test_display_to_serial.get(serial, serial)
        self._prepare_test_device(serial, "背包测试")
        threading.Thread(target=self._run_backpack_test, args=(serial,), daemon=True).start()

    def _run_backpack_test(self, serial):
        def log(msg):
            self.root.after(0, lambda m=msg: self._test_log(m))
        log(f"开始背包测试（全量扫描）：{serial}")
        self._wait_test_engine_idle(serial, log)
        from xbw_features import backend as xbw_backend
        xbw_backend.set_stop_event(self._test_stop_event)
        self._xbw_backend_standalone(serial, log)
        try:
            from xbw_features.threads.dk_changjing import check_backpack
            prev = getattr(self, "_test_pkg_snapshot", None)
            result = check_backpack(serial, prev, stop_event=self._test_stop_event,
                                    scan_mode="all")
            self._test_pkg_snapshot = result["snapshot"]
            if result["bag_frame"] is None:
                log("背包未打开（未找到物品锁），本次背包测试已中止")
                return
            log(f"背包占用槽位：{len(result['snapshot'])}/20")
            log(f"全量扫描结果：环 {result['add_huan']} 个 / 卡 {result['add_card']} 张"
                + ("（已逐个点击全部占用槽位匹配“装备条件/怪物卡片”）"))
            if result["ring_points"]:
                log("检测到【环】：" + "  ".join(f"({x},{y})" for x, y in result["ring_points"]))
            if result["card_points"]:
                log("检测到【卡】：" + "  ".join(f"({x},{y})" for x, y in result["card_points"]))
            # 在背包截图上标注环/卡并显示
            bag = result.get("bag_frame")
            if bag is not None:
                self.root.after(0, lambda f=bag, r=result: self._show_bag_annotation(f, r))
            log("✅ 背包检查完成")
        except xbw_backend.StopTest:
            log("⏹ 背包测试已停止")
        except Exception as e:
            log(f"❌ 背包测试异常：{e}")
        finally:
            self._xbw_backend_restore(serial)
            xbw_backend.clear_stop_event()
            self._test_stop_event.clear()
            self._resume_test_devices()

    def _test_switch_map(self):
        serial = self.test_device_combo.get().strip()
        if not serial:
            self._log("请先在功能测试页签选择设备")
            return
        # 从显示文本中提取序列号
        serial = self._test_display_to_serial.get(serial, serial)
        target = self.test_map_combo.get().strip()
        if not target:
            self._log("请选择目标地图")
            return
        self._prepare_test_device(serial, "切换地图测试")
        threading.Thread(target=self._run_switch_map_test, args=(serial, target), daemon=True).start()

    def _run_switch_map_test(self, serial, target):
        def log(msg):
            self.root.after(0, lambda m=msg: self._test_log(m))
        log(f"开始切换地图测试：{serial} -> {target}")
        self._wait_test_engine_idle(serial, log)
        from xbw_features import backend as xbw_backend
        xbw_backend.set_stop_event(self._test_stop_event)
        self._xbw_backend_standalone(serial, log)
        try:
            # 优先用场景切换引擎 SceneSwitcher（每步 OCR 验证，失败明确返回）
            arrived = False
            try:
                from 场景切换 import SceneSwitcher
                log(f"🛫 场景切换引擎 -> {target} ...")
                # 复用该设备引擎的 scrcpy 流帧（若引擎在跑），免 ADB 截图提速
                _eng = self.engines.get(serial)
                sw = SceneSwitcher(serial, log_fn=lambda m: log(m),
                                   client=getattr(_eng, "client", None),
                                   frame_lock=getattr(_eng, "_frame_lock", None))
                if sw.connect():
                    arrived = sw.switch_scene(target)
                    if arrived:
                        log(f"✅ 已到达 {target}（场景切换引擎确认）")
                else:
                    log("⚠️ 场景切换引擎连接失败")
            except Exception as e:
                log(f"⚠️ 场景切换引擎异常：{e}")
            if not arrived:
                # 回退：小霸王 goToMapAction + detectPosition 到达验证
                from xbw_features import go_to_chang_jing
                from mhxy_engine import _match_scene_name
                from xbw_features.common.util.detect_position_util import detectPosition
                for _try in range(2):
                    log(f"🛫 小霸王切图 {target}（第{_try+1}次）...")
                    go_to_chang_jing(serial, target)
                    time.sleep(1.5)
                    detected = None
                    try:
                        _dp = detectPosition(serial)
                        if _dp and _dp[0]:
                            detected = _dp[0]
                    except Exception:
                        detected = None
                    if detected and _match_scene_name(detected, target):
                        log(f"✅ 已到达 {target}（检测到场景 {detected}）")
                        arrived = True
                        break
                    log(f"⚠️ 切图后仍在 {detected or '未知场景'}，未到达 {target}"
                        + ("，重试一次" if _try == 0 else ""))
                if not arrived:
                    log("❌ 两次切图后仍未到达目标场景，请检查游戏画面")
        except xbw_backend.StopTest:
            log("⏹ 切换地图测试已停止")
        except Exception as e:
            log(f"❌ 切换地图异常：{e}")
        finally:
            self._xbw_backend_restore(serial)
            xbw_backend.clear_stop_event()
            self._test_stop_event.clear()
            self._resume_test_devices()

    def _prepare_test_device(self, serial, label):
        """测试前准备：选中设备若在挂机则临时暂停其引擎（其他挂机设备不受影响）。
        仅设置暂停标志并记录，不阻塞 GUI；等引擎脱离战斗放到测试线程里做。"""
        eng = self.engines.get(serial)
        if eng is not None and getattr(eng, "running", False):
            if not getattr(eng, "_paused", False):
                eng._paused = True
            self._test_paused_engines = getattr(self, "_test_paused_engines", set())
            self._test_paused_engines.add(serial)
            self._log(f"⏸️ {label}: 已暂停设备 {serial} 的引擎（测试结束自动恢复）")
        return True

    def _wait_test_engine_idle(self, serial, log):
        """测试线程开头：等所选设备引擎脱离当前战斗、进入暂停，避免测试与战斗同时操作屏幕"""
        eng = self.engines.get(serial)
        if eng is None or not getattr(eng, "running", False):
            return
        if getattr(eng, "was_in_pk", False):
            log(f"⏳ 设备 {serial} 正在战斗，等待战斗结束...")
            for _ in range(120):
                if not getattr(eng, "running", False):
                    return
                if not getattr(eng, "was_in_pk", False):
                    break
                time.sleep(0.5)
            if getattr(eng, "was_in_pk", False):
                log(f"⚠️ 设备 {serial} 战斗超时，测试可能与战斗重叠")
        else:
            time.sleep(0.5)   # 确保引擎主循环已进入暂停分支

    def _resume_test_devices(self):
        """测试结束：恢复临时暂停的引擎"""
        for serial in getattr(self, "_test_paused_engines", set()):
            eng = self.engines.get(serial)
            if eng is not None and getattr(eng, "running", False):
                eng._paused = False
                self._log(f"▶️ 已恢复设备 {serial} 的引擎")
        self._test_paused_engines = set()

    def _xbw_backend_standalone(self, serial, log):
        """按所选设备注册独立后端槽位（仅 log_fn 回灌 GUI；screencap/tap 走 ADB 默认）。
        per-device 槽位互不影响，其他挂机引擎继续用自己的取帧/点击函数。"""
        from xbw_features import backend as xbw_backend
        xbw_backend.backend.set(
            deviceId=serial,
            log_fn=lambda d, m: log(f"[{d}] {m}"),
            cache_seconds=0.2)   # 与引擎一致：0.2s 帧缓存，减少 ADB 截图次数

    def _xbw_backend_restore(self, serial):
        """清除所选设备的测试槽位（不影响其他设备的注册）"""
        from xbw_features import backend as xbw_backend
        xbw_backend.backend.clear_cache(serial)

    def _refresh_device_tab(self):
        """刷新设备管理 Tab"""
        for w in self.dev_list_frame.winfo_children():
            w.destroy()
        self._device_widgets.clear()
        self._device_sel_vars = {}      # serial -> 行勾选框变量（全选联动）
        self._device_sel_all_var = tk.BooleanVar(value=False)  # 表头全选框
        self._row_highlight_widgets = {}   # serial -> 行内可换背景的控件列表
        self._highlight_serial = None      # 当前高亮行

        devices = list_adb_devices()
        if not devices:
            ttk.Label(self.dev_list_frame, text="未发现 ADB 设备",
                      foreground="orange", font=("Microsoft YaHei", 10)).pack(pady=20)
            return

        # 按手动排序顺序显示：以已保存的顺序为准，新设备追加到末尾
        ordered = [s for s in self.cfg.get("device_order", []) if s in devices]
        for s in devices:
            if s not in ordered:
                ordered.append(s)
        self._device_order = ordered

        # 表头与数据行共用同一个 grid，保证各列边界完全一致
        self.dev_table = ttk.Frame(self.dev_list_frame)
        self.dev_table.pack(fill=tk.X)
        self.dev_table.columnconfigure(0, weight=0)
        for ci in range(1, 9):
            self.dev_table.columnconfigure(ci, weight=1)
        self.dev_table.columnconfigure(9, weight=0)
        for ci, (txt, wd) in enumerate([
            ("选择", 0), ("设备名称", 10), ("设备序列号", 16),
            ("状态", 6), ("当前场景", 6), ("当日卡", 5),
            ("当日环", 5), ("战斗", 4), ("时长", 6), ("操作", 0),
        ]):
            if ci == 0:
                # 第一列：全选/全不选复选框（表头即选择框）
                head_frame = tk.Frame(self.dev_table, bg="white", bd=0, pady=4)
                head_frame.grid(row=0, column=ci, sticky="ew")
                ttk.Checkbutton(head_frame, variable=self._device_sel_all_var,
                                command=self._toggle_all_devices,
                                bootstyle="primary").pack(expand=True)
            else:
                tk.Label(self.dev_table, text=txt, font=("Microsoft YaHei", 9, "bold"),
                         width=wd if wd else None, anchor="center", bg="white",
                         bd=0, padx=4, pady=6).grid(row=0, column=ci, sticky="ew")

        self._device_row = 1
        for serial in ordered:
            self._add_device_row(serial)
        self._update_sel_all()
        self._total_widgets = None
        self._add_total_row()

    def _update_sel_all(self):
        """行勾选变化时同步全选框状态：全部勾选才显示勾选"""
        sel_all = bool(self._device_sel_vars) and all(v.get() for v in self._device_sel_vars.values())
        self._device_sel_all_var.set(sel_all)

    def _toggle_all_devices(self):
        """表头全选框点击：全选/全不选所有设备行"""
        select_all = self._device_sel_all_var.get()
        if select_all:
            self._selected_devices.update(self._device_sel_vars.keys())
        else:
            self._selected_devices.clear()
        for v in self._device_sel_vars.values():
            v.set(select_all)

    def _table_cell(self, parent, row, col, serial=None, **kw):
        """在设备表格中创建一个单元格（与操作栏同风格：白底无边框）"""
        kw.setdefault("bg", "white")
        kw.setdefault("bd", 0)
        kw.setdefault("padx", 4)
        kw.setdefault("pady", 6)
        lbl = tk.Label(parent, **kw)
        lbl.grid(row=row, column=col, sticky="ew")
        if serial is not None:
            self._bind_row_drag(lbl, serial)
            self._row_highlight_widgets.setdefault(serial, []).append(lbl)
        return lbl

    def _on_row_click(self, serial):
        """点击设备行：整行高亮背景，便于区分当前选中的行"""
        if self._highlight_serial == serial:
            return
        if self._highlight_serial is not None:
            self._set_row_highlight(self._highlight_serial, False)
        self._highlight_serial = serial
        self._set_row_highlight(serial, True)

    def _set_row_highlight(self, serial, highlight):
        """设置整行背景色：高亮用浅黄色，否则还原白色"""
        bg = "#fff3cd" if highlight else "white"
        for w in self._row_highlight_widgets.get(serial, []):
            try:
                if hasattr(w, "configure"):
                    w.configure(bg=bg)
            except Exception:
                pass

    def _row_btn_cmd(self, serial, action):
        """设备行按钮统一入口：点击先高亮整行，再执行按钮动作"""
        self._on_row_click(serial)
        return action(serial)

    def _add_device_row(self, serial):
        """在设备管理 Tab 中添加一行"""
        engine = self.engines.get(serial)
        running = engine is not None and engine.running

        row = self._device_row
        self._device_row += 1
        parent = self.dev_table

        # 多选复选框列
        sel_frame = tk.Frame(parent, bg="white", bd=0, pady=6)
        sel_frame.grid(row=row, column=0, sticky="ew")
        sel_var = tk.BooleanVar(value=serial in self._selected_devices)

        def on_check(s=serial, v=sel_var):
            if v.get():
                self._selected_devices.add(s)
            else:
                self._selected_devices.discard(s)
            self._on_row_click(s)
            self._update_sel_all()

        self._device_sel_vars[serial] = sel_var
        ttk.Checkbutton(sel_frame, variable=sel_var, command=on_check,
                        bootstyle="primary").pack(expand=True)
        self._bind_row_drag(sel_frame, serial)
        self._row_highlight_widgets.setdefault(serial, []).append(sel_frame)

        # device_name（列1）
        dev_names = self.cfg.get("device_names", {})
        dev_name = dev_names.get(serial, "")
        name_kw = {"text": dev_name or "点击设置", "width": 10, "anchor": "center",
                   "cursor": "hand2"}
        if not dev_name:
            name_kw["foreground"] = "gray"
        name_lbl = self._table_cell(parent, row, 1, serial=serial, **name_kw)
        name_lbl._is_name_cell = True

        # 设备序列号（列2）
        serial_lbl = self._table_cell(parent, row, 2, serial=serial, text=serial, width=16,
                                      anchor="center", font=("Consolas", 9), cursor="hand2")
        serial_lbl._is_serial_cell = True

        status_text = "运行中" if running else "空闲"
        status_color = "green" if running else "gray"
        status_lbl = self._table_cell(parent, row, 3, serial=serial, text=status_text,
                                      foreground=status_color, width=6, anchor="center")

        scene_v = "--"
        card_v, huan_v = self._device_daily_counts(serial)
        card_v, huan_v = str(card_v), str(huan_v)
        if running:
            scene_v = getattr(engine, "last_map_name", None) or engine.cfg.get("map", "") or "--"

        scene_lbl = self._table_cell(parent, row, 4, serial=serial, text=scene_v,
                                     width=6, anchor="center")
        card_lbl = self._table_cell(parent, row, 5, serial=serial, text=card_v,
                                    width=5, anchor="center")
        huan_lbl = self._table_cell(parent, row, 6, serial=serial, text=huan_v,
                                    width=5, anchor="center")

        stats = self._today_stats().get(serial, {})
        if running:
            bc_v = f"{engine.battle_count}"
        else:
            bc_v = str(stats.get("battle_count", 0) or 0)
        bc_lbl = self._table_cell(parent, row, 7, serial=serial, text=bc_v,
                                  width=4, anchor="center")

        # 当前场景时长（空闲时显示当日累计运行时长）
        total_runtime = getattr(engine, "total_runtime", 0) or 0
        if running and getattr(engine, "start_time", 0):
            elapsed = int(total_runtime + (time.time() - engine.start_time))
            duration = fmt_duration_hm(elapsed)
        elif total_runtime > 0:
            duration = fmt_duration_hm(total_runtime)
        elif not running and stats.get("total_runtime"):
            duration = fmt_duration_hm(stats.get("total_runtime", 0))
        else:
            duration = "--"
        dur_lbl = self._table_cell(parent, row, 8, serial=serial, text=duration,
                                   width=6, anchor="center")

        btn_frame = tk.Frame(parent, bg="white", bd=0, padx=4, pady=6)
        btn_frame.grid(row=row, column=9, sticky="ew")
        self._bind_row_drag(btn_frame, serial)
        self._row_highlight_widgets.setdefault(serial, []).append(btn_frame)
        start_btn2 = ttk.Button(btn_frame, text="▶ 启动", width=7,
                                style="SmallSuccess.TButton",
                                command=lambda s=serial: self._row_btn_cmd(s, self._start_device))
        start_btn2.pack(side=tk.LEFT, padx=(0, 3))
        stop_btn2 = ttk.Button(btn_frame, text="⏹ 停止", width=7,
                               style="SmallDanger.TButton",
                               command=lambda s=serial: self._row_btn_cmd(s, self._stop_device))
        stop_btn2.pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(btn_frame, text="📸 截图", width=7,
                   style="SmallOutline.TButton",
                   command=lambda s=serial: self._row_btn_cmd(s, self._device_screenshot)).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(btn_frame, text="详情", width=6,
                   style="SmallOutline.TButton",
                   command=lambda s=serial: self._row_btn_cmd(s, self._show_device_detail)).pack(side=tk.LEFT, padx=(0, 3))

        # 显示是否有独立配置的标识
        has_custom = self._device_configs.get(serial) is not None
        if has_custom:
            config_lbl = tk.Label(btn_frame, text="🔧", fg="#ff6b00",
                                 font=("Microsoft YaHei", 8), bg="white")
            config_lbl.pack(side=tk.LEFT, padx=(0, 3))
            self._row_highlight_widgets.setdefault(serial, []).append(config_lbl)

        self._device_widgets[serial] = {
            "status": status_lbl, "scene": scene_lbl, "card": card_lbl,
            "huan": huan_lbl, "bc": bc_lbl, "dur": dur_lbl,
            "start": start_btn2, "stop": stop_btn2,
        }
        self._update_device_row_buttons(serial)

    def _add_total_row(self):
        """在设备表格最下面加一行"总计"：统计所有设备的当日累计卡片/环总数与运行时长"""
        parent = self.dev_table
        row = self._device_row

        total_card, total_huan = self._compute_total_counts()

        total_label = tk.Label(parent, text="总计", font=("Microsoft YaHei", 9, "bold"),
                               bg="white", bd=0, padx=4, pady=2, anchor="center")
        total_label.grid(row=row, column=1, sticky="ew")

        card_lbl = tk.Label(parent, text=str(total_card), font=("Microsoft YaHei", 9, "bold"),
                            bg="white", bd=0, padx=4, pady=2, anchor="center",
                            foreground="#198754")
        card_lbl.grid(row=row, column=5, sticky="ew")

        huan_lbl = tk.Label(parent, text=str(total_huan), font=("Microsoft YaHei", 9, "bold"),
                            bg="white", bd=0, padx=4, pady=2, anchor="center",
                            foreground="#dc3545")
        huan_lbl.grid(row=row, column=6, sticky="ew")

        dur_lbl = tk.Label(parent, text=fmt_duration_hm(self._compute_total_runtime()),
                           font=("Microsoft YaHei", 9, "bold"),
                           bg="white", bd=0, padx=4, pady=2, anchor="center",
                           foreground="#0d6efd")
        dur_lbl.grid(row=row, column=8, sticky="ew")

        self._total_widgets = {"card": card_lbl, "huan": huan_lbl, "dur": dur_lbl}

    def _compute_total_counts(self):
        """计算所有设备的当日累计卡片/环总数（含空闲设备，跨重启保留）"""
        total_card = 0
        total_huan = 0
        serials = set(self.engines.keys()) | set(self._today_stats().keys())
        for serial in serials:
            card_v, huan_v = self._device_daily_counts(serial)
            total_card += int(card_v or 0)
            total_huan += int(huan_v or 0)
        return total_card, total_huan

    def _device_daily_counts(self, serial):
        """返回设备当日累计 (卡, 环)：运行中取引擎实时值，空闲/重启后取统计文件值"""
        eng = self.engines.get(serial)
        if eng is not None:
            return (getattr(eng, "_daily_card_count", 0) or 0,
                    getattr(eng, "_daily_huan_count", 0) or 0)
        stats = self._today_stats().get(serial, {})
        return (stats.get("cards", 0) or 0, stats.get("rings", 0) or 0)

    def _device_daily_runtime(self, serial):
        """返回设备当日累计运行时长（秒）：运行中含本次已运行时间，空闲/重启后取统计文件值"""
        eng = self.engines.get(serial)
        if eng is not None:
            runtime = getattr(eng, "total_runtime", 0) or 0
            if getattr(eng, "running", False) and getattr(eng, "start_time", 0):
                runtime += max(0.0, time.time() - eng.start_time)
            return runtime
        stats = self._today_stats().get(serial, {})
        return stats.get("total_runtime", 0) or 0

    def _compute_total_runtime(self):
        """计算所有设备的当日累计运行时长总数（秒，含空闲设备，跨重启保留）"""
        total = 0.0
        serials = set(self.engines.keys()) | set(self._today_stats().keys())
        for serial in serials:
            total += float(self._device_daily_runtime(serial) or 0)
        return total

    def _today_stats(self):
        """返回今日统计文件中的设备数据（每天5:00自动切换新统计日）"""
        cache = self._device_stats_cache or {}
        if cache.get("date") != stats_day():
            return {}
        return cache.get("devices", {})

    def _update_device_row_buttons(self, serial):
        """根据设备运行状态更新设备行的按钮与状态（与场景控制页按钮逻辑一致）"""
        w = self._device_widgets.get(serial)
        if not w:
            return
        engine = self.engines.get(serial)
        running = engine is not None and engine.running
        if running:
            w["start"].configure(state=tk.DISABLED)
            w["stop"].configure(state=tk.NORMAL)
            w["status"].configure(text="运行中", foreground="green")
        else:
            w["start"].configure(state=tk.NORMAL)
            w["stop"].configure(state=tk.DISABLED)
            w["status"].configure(text="空闲", foreground="gray")
            w["scene"].configure(text="--")
            card_v, huan_v = self._device_daily_counts(serial)
            w["card"].configure(text=str(card_v))
            w["huan"].configure(text=str(huan_v))
            stats = self._today_stats().get(serial, {})
            w["bc"].configure(text=str(stats.get("battle_count", 0) or 0))
            runtime = stats.get("total_runtime", 0) or 0
            if runtime:
                w["dur"].configure(text=fmt_duration_hm(runtime))
            else:
                w["dur"].configure(text="--")

    def _load_device_stats(self):
        """读取今日设备统计（跨重启保留，每天5:00切换新统计日）"""
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("date") == stats_day():
                    return data
        except Exception:
            pass
        return {"date": "", "devices": {}}

    def _save_device_stats(self):
        """把当前各引擎统计写入今日文件（合并保留环/卡当日累计）"""
        devices = dict(self._today_stats())
        today = stats_day()
        for serial, eng in self.engines.items():
            if eng is None:
                continue
            # 引擎统计日与当前不一致（跨 5:00 尚未在引擎主循环里重置）：
            # 不把昨天的计数写入新统计日文件，避免"新日期存旧数据"
            if getattr(eng, "_stats_day_key", today) != today:
                devices.pop(serial, None)
                continue
            runtime = getattr(eng, "total_runtime", 0) or 0
            if getattr(eng, "start_time", 0) > 0:
                runtime += max(0.0, time.time() - eng.start_time)
            devices[serial] = {
                "battle_count": getattr(eng, "battle_count", 0),
                "cards": getattr(eng, "_daily_card_count", 0) or 0,
                "rings": getattr(eng, "_daily_huan_count", 0) or 0,
                "total_runtime": runtime,
                "last_loyalty": getattr(eng, "_last_loyalty_recovery", 0),
            }
        try:
            os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                data = {"date": stats_day(), "devices": devices}
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._device_stats_cache = data
        except Exception as e:
            self._log(f"⚠️ 统计保存失败: {e}")

    def _start_device(self, serial, override=None):
        """启动指定设备的引擎（使用设备独立配置或全局配置）
        override: dict，额外覆盖配置键（特殊场景队伍模式使用）"""
        if serial in self.engines and self.engines[serial].running:
            self._log(f"[{serial}] 已在运行中")
            return

        # 获取设备的有效配置
        device_cfg = self._get_effective_config(serial)
        if override:
            device_cfg.update(override)
        device_cfg["serial"] = serial

        self.device_combo.set(serial)
        self.dev_status.configure(text=f"设备: {serial}", foreground="green")

        self._draw_status("green")
        self.status_label.configure(text="运行中")

        # 检查是否有独立配置
        has_custom_config = self._device_configs.get(serial) is not None
        if has_custom_config:
            self._log(f"[{serial}] 使用设备独立配置")
        else:
            self._log(f"[{serial}] 使用全局配置")

        # 传递全局的设备名称配置给引擎
        device_cfg["device_names"] = self.cfg.get("device_names", {})

        engine = AutoFightEngine(device_cfg, self.log_queue)
        # 统计恢复：优先用本次运行期间的旧引擎，否则读今日统计文件（按天重置）
        old_engine = self.engines.get(serial)
        if old_engine is not None:
            engine.battle_count = old_engine.battle_count
            engine._daily_card_count = getattr(old_engine, "_daily_card_count", 0) or 0
            engine._daily_huan_count = getattr(old_engine, "_daily_huan_count", 0) or 0
            engine._last_loyalty_recovery = getattr(old_engine, "_last_loyalty_recovery", 0)
            runtime = getattr(old_engine, "total_runtime", 0) or 0
            if getattr(old_engine, "start_time", 0) > 0:
                runtime += max(0.0, time.time() - old_engine.start_time)
            engine.total_runtime = runtime
        else:
            stats = self._today_stats().get(serial, {})
            engine.battle_count = stats.get("battle_count", 0)
            engine._daily_card_count = stats.get("cards", 0) or 0
            engine._daily_huan_count = stats.get("rings", 0) or 0
            engine._last_loyalty_recovery = stats.get("last_loyalty", 0)
            engine.total_runtime = stats.get("total_runtime", 0) or 0
        engine.coord_enabled = device_cfg.get("coord_enabled", True)
        self.engines[serial] = engine
        self.engine = engine
        t = threading.Thread(target=engine.run_loop, daemon=True)
        self.engine_threads[serial] = t
        t.start()
        self._update_device_row_buttons(serial)
        # 引擎启动后延迟更新按钮状态
        self.root.after(500, self._update_tab1_buttons)
        self.root.after(500, lambda: self._update_device_row_buttons(serial))
        self._log(f"[{serial}] ▶ 引擎启动")

    def _stop_device(self, serial):
        """停止指定设备的引擎（与场景控制页「停止」一致）"""
        engine = self.engines.get(serial)
        if engine:
            engine.running = False
            if hasattr(engine, '_loyalty_stop_event'):
                engine._loyalty_stop_event.set()
        self._update_device_row_buttons(serial)
        self.root.after(500, self._update_tab1_buttons)
        self.root.after(500, lambda: self._update_device_row_buttons(serial))
        self._log(f"[{serial}] ⏹ 正在停止...")
        self._save_device_stats()

    def _selected_serials(self):
        """按当前显示顺序返回已勾选的设备"""
        return [s for s in self._device_order if s in self._selected_devices]

    def _start_selected_devices(self):
        """一键启动所有勾选的设备"""
        serials = self._selected_serials()
        if not serials:
            messagebox.showwarning("提示", "请先勾选要启动的设备")
            return
        for s in serials:
            self._start_device(s)
        self._log(f"▶ 一键启动 {len(serials)} 台设备")

    def _stop_selected_devices(self):
        """一键停止所有勾选的设备"""
        serials = self._selected_serials()
        if not serials:
            messagebox.showwarning("提示", "请先勾选要停止的设备")
            return
        for s in serials:
            self._stop_device(s)
        self._log(f"⏹ 一键停止 {len(serials)} 台设备")

    def _bind_row_drag(self, widget, serial):
        """给行的单元格绑定拖拽排序事件"""
        widget.bind("<Button-1>", lambda e, s=serial: self._on_row_drag_start(s, e))
        widget.bind("<ButtonRelease-1>", lambda e, s=serial: self._on_row_drag_end(s, e))

    def _on_row_drag_start(self, serial, event):
        self._drag_serial = serial
        self._drag_y0 = event.y_root
        self._drag_widget = event.widget

    def _on_row_drag_end(self, serial, event):
        """拖拽松手：按鼠标位置重新插入行并保存顺序"""
        if self._drag_serial != serial:
            return
        widget = self._drag_widget
        self._drag_serial = None
        self._drag_widget = None
        # 移动距离很小视为单击：整行高亮；名称列触发重命名，序列号列复制到剪贴板
        if abs(event.y_root - self._drag_y0) < 4:
            self._on_row_click(serial)
            if widget is not None and getattr(widget, "_is_name_cell", False):
                self._rename_device(serial, widget)
            elif widget is not None and getattr(widget, "_is_serial_cell", False):
                self._copy_serial(serial, widget)
            return
        target = self._row_pos_at_y(event.y_root)
        try:
            idx = self._device_order.index(serial)
        except ValueError:
            return
        if target is None or idx == target:
            return
        self._device_order.pop(idx)
        self._device_order.insert(target, serial)
        self.cfg["device_order"] = self._merged_device_order()
        save_config(self.cfg)
        self._refresh_device_tab()

    def _copy_serial(self, serial, lbl):
        """点击设备序列号复制到剪贴板，并短暂显示"已复制"提示（2秒后自动恢复）"""
        self.root.clipboard_clear()
        self.root.clipboard_append(serial)
        if getattr(lbl, "_copied", False):
            # 已在提示状态（重复点击）：不重新捕获文本/颜色，只重新计时
            self.root.after(2000, lambda: self._restore_serial(lbl, serial))
            return
        lbl._copied = True
        lbl._orig_fg = lbl.cget("foreground")
        lbl.configure(text="已复制 ✓", foreground="green")
        self.root.after(2000, lambda: self._restore_serial(lbl, serial))

    def _restore_serial(self, lbl, serial):
        """恢复序列号显示；控件已重建（表格刷新）则跳过"""
        try:
            if lbl.winfo_exists():
                lbl.configure(text=serial, foreground=getattr(lbl, "_orig_fg", "black"))
                lbl._copied = False
        except Exception:
            pass

    def _merged_device_order(self):
        """合并显示顺序与已保存顺序：暂未连接的设备保留原槽位"""
        saved = list(self.cfg.get("device_order", []))
        current = list(self._device_order)
        current_set = set(current)
        merged = []
        placed = set()
        idx = 0
        for s in saved:
            if s in current_set:
                while idx < len(current) and current[idx] in placed:
                    idx += 1
                if idx < len(current):
                    t = current[idx]
                    merged.append(t)
                    placed.add(t)
                    idx += 1
            else:
                merged.append(s)
                placed.add(s)
        for t in current:
            if t not in placed:
                merged.append(t)
                placed.add(t)
        return merged

    def _row_pos_at_y(self, y):
        """把屏幕 y 坐标换算成目标行位置（0 为第一行）"""
        best = None
        best_dist = None
        for w in self.dev_table.winfo_children():
            gi = w.grid_info()
            r = int(gi.get("row", -1))
            if r < 1:
                continue
            center = (w.winfo_rooty() + w.winfo_height() / 2)
            dist = abs(y - center)
            if best is None or dist < best_dist:
                best = r - 1
                best_dist = dist
        return best

    def _device_screenshot(self, serial):
        """为指定设备截图（始终使用ADB实时截图）"""
        import cv2
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        os.makedirs(save_dir, exist_ok=True)
        # 按日期自增编号: 2026_07_29_001.png
        today = datetime.now().strftime("%Y_%m_%d")
        if not hasattr(self, "_screenshot_counter_date"):
            self._screenshot_counter_date = today
            self._screenshot_counter = 0
        if self._screenshot_counter_date != today:
            self._screenshot_counter_date = today
            self._screenshot_counter = 0
        self._screenshot_counter += 1
        filename = f"{today}_{self._screenshot_counter:03d}.png"
        filepath = os.path.join(save_dir, filename)
        try:
            # ADB截全分辨率图，resize到800x448保存（与流坐标一致）
            result = sp.run([ADB_EXE, "-s", serial, "exec-out", "screencap", "-p"],
                           capture_output=True, timeout=10, creationflags=sp.CREATE_NO_WINDOW)
            if result.returncode != 0 or len(result.stdout) < 100:
                self._log(f"[{serial}] ❌ ADB截图失败")
                return
            import cv2 as _cv2
            import numpy as _np
            _raw = _cv2.imdecode(_np.frombuffer(result.stdout, dtype=_np.uint8), _cv2.IMREAD_COLOR)
            if _raw is not None:
                _small = _cv2.resize(_raw, (800, 448))
                _cv2.imwrite(filepath, _small)
                self._log(f"[{serial}] 📸 ADB截图已保存: {filepath} (800x448)")
            else:
                with open(filepath, "wb") as f:
                    f.write(result.stdout)
                self._log(f"[{serial}] 📸 截图已保存: {filepath} (原始分辨率)")
        except Exception as e:
            self._log(f"[{serial}] ❌ 截图异常: {e}")

    def _rename_device(self, serial, label_widget=None):
        dev_names = self.cfg.get("device_names", {})
        current = dev_names.get(serial, "")

        dlg = tk.Toplevel(self.root)
        dlg.title("设备重命名 - " + serial)
        dlg.geometry("350x140")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="设备: " + serial, font=("Microsoft YaHei", 9)).pack(pady=(12, 6))
        ttk.Label(dlg, text="设备名称：").pack()
        entry = ttk.Entry(dlg, width=30, font=("Microsoft YaHei", 11))
        entry.insert(0, current)
        entry.pack(pady=(4, 10))
        entry.selection_range(0, tk.END)
        entry.focus_set()

        def on_ok():
            name = entry.get().strip()
            dev_names = self.cfg.get("device_names", {})
            if name:
                dev_names[serial] = name
            else:
                dev_names.pop(serial, None)
            self.cfg["device_names"] = dev_names
            save_config(self.cfg)
            dlg.destroy()
            self._refresh_device_tab()

        entry.bind("<Return>", lambda e: on_ok())
        btn_f = ttk.Frame(dlg)
        btn_f.pack()
        ttk.Button(btn_f, text="确定", command=on_ok, bootstyle="primary", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="取消", command=dlg.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # 居中显示
        dlg.update_idletasks()
        self.root.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

    def _show_capture_blacklist_config(self):
        """显示捕捉宝宝黑名单配置弹窗"""
        # 获取当前黑名单配置
        blacklist = self.cfg.get("capture_bb_blacklist", {})

        # 创建弹窗
        dlg = tk.Toplevel(self.root)
        dlg.title("捕捉宝宝黑名单配置")
        dlg.geometry("600x500")
        dlg.resizable(True, True)
        dlg.transient(self.root)
        dlg.grab_set()

        # 主容器
        main = ttk.Frame(dlg, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # 标题
        title_frame = ttk.Frame(main)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        ttk.Label(title_frame, text="捕捉宝宝黑名单配置",
                 font=("Microsoft YaHei", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="(指定哪些场景的哪些宝宝不捕捉)",
                 foreground="gray", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(10, 0))

        # 内容区域：左侧场景列表，右侧宝宝列表
        content_frame = ttk.Frame(main)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)

        # 左侧场景列表
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(left_frame, text="场景列表",
                 font=("Microsoft YaHei", 10, "bold")).pack(pady=(0, 5))

        scene_listbox = tk.Listbox(left_frame, font=("Microsoft YaHei", 10), height=15)
        scene_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=scene_listbox.yview)
        scene_listbox.configure(yscrollcommand=scene_scrollbar.set)
        scene_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scene_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧宝宝列表
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right_frame, text="黑名单宝宝 (双击删除)",
                 font=("Microsoft YaHei", 10, "bold")).pack(pady=(0, 5))

        bb_frame = ttk.Frame(right_frame)
        bb_frame.pack(fill=tk.BOTH, expand=True)

        bb_listbox = tk.Listbox(bb_frame, font=("Microsoft YaHei", 10), height=12)
        bb_scrollbar = ttk.Scrollbar(bb_frame, orient=tk.VERTICAL, command=bb_listbox.yview)
        bb_listbox.configure(yscrollcommand=bb_scrollbar.set)
        bb_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 预定义场景列表
        scenes = ["小西天", "小雷音寺", "龙窟五层", "凤巢四层", "凤巢五层", "子母河底", "女娲神迹", "须弥东界"]
        for scene in scenes:
            scene_listbox.insert(tk.END, scene)

        # 存储当前选中的场景
        current_scene = [None]

        def on_scene_select(event):
            """场景选中事件"""
            selection = scene_listbox.curselection()
            if not selection:
                return
            scene = scenes[selection[0]]
            current_scene[0] = scene

            # 显示该场景的黑名单宝宝
            bb_listbox.delete(0, tk.END)
            bb_list = blacklist.get(scene, [])
            for bb in bb_list:
                bb_listbox.insert(tk.END, bb)

        def add_bb():
            """添加宝宝到黑名单"""
            scene = current_scene[0]
            if not scene:
                messagebox.showwarning("提示", "请先选择场景")
                return
            bb_name = bb_entry.get().strip()
            if not bb_name:
                messagebox.showwarning("提示", "请输入宝宝名称")
                return

            if scene not in blacklist:
                blacklist[scene] = []
            if bb_name not in blacklist[scene]:
                blacklist[scene].append(bb_name)
                bb_listbox.insert(tk.END, bb_name)
                bb_entry.delete(0, tk.END)
            else:
                messagebox.showinfo("提示", "该宝宝已在黑名单中")

        def remove_bb(event):
            """双击删除宝宝"""
            selection = bb_listbox.curselection()
            if not selection:
                return
            scene = current_scene[0]
            if not scene:
                return

            bb_name = bb_listbox.get(selection[0])
            if scene in blacklist and bb_name in blacklist[scene]:
                blacklist[scene].remove(bb_name)
                bb_listbox.delete(selection[0])

        def on_save():
            """保存配置"""
            self.cfg["capture_bb_blacklist"] = blacklist
            save_config(self.cfg)
            self._log("✅ 捕捉宝宝黑名单配置已保存")
            dlg.destroy()

        # 绑定事件
        scene_listbox.bind("<<ListboxSelect>>", on_scene_select)
        bb_listbox.bind("<Double-Button-1>", remove_bb)

        # 添加宝宝按钮（在函数定义之后）
        add_btn_frame = ttk.Frame(right_frame)
        add_btn_frame.pack(fill=tk.X, pady=(10, 0))

        bb_entry = ttk.Entry(add_btn_frame, width=20, font=("Microsoft YaHei", 9))
        bb_entry.pack(side=tk.LEFT, padx=(0, 5))
        add_bb_btn = ttk.Button(add_btn_frame, text="添加", width=8, bootstyle="success", command=add_bb)
        add_bb_btn.pack(side=tk.LEFT)

        # 底部按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, pady=(15, 0))

        ttk.Button(btn_frame, text="保存", command=on_save,
                   bootstyle="success", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dlg.destroy,
                   bootstyle="outline", width=12).pack(side=tk.LEFT)

        # 居中显示
        dlg.update_idletasks()
        self.root.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

    def _show_device_detail(self, serial):
        """显示设备配置详情弹窗（包含场景历史和配置信息）"""
        engine = self.engines.get(serial)

        # 创建弹窗
        dlg = tk.Toplevel(self.root)
        dlg.title(f"设备详情 - {serial}")
        dlg.geometry("940x720")
        dlg.resizable(True, True)
        dlg.transient(self.root)
        dlg.grab_set()

        # 获取设备名称
        dev_names = self.cfg.get("device_names", {})
        dev_name = dev_names.get(serial, serial[:4])

        # 使用 Notebook 分页显示场景历史和配置
        notebook = ttk.Notebook(dlg)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== Tab 1: 场景历史 =====
        history_frame = ttk.Frame(notebook, padding=15)
        notebook.add(history_frame, text="场景历史")

        # 标题
        title_frame = ttk.Frame(history_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text=f"设备：{dev_name} ({serial})",
                  font=("Microsoft YaHei", 12, "bold")).pack(side=tk.LEFT)

        # 表格容器
        table_frame = ttk.Frame(history_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # 创建表格
        columns = ("场景名称", "卡片(张)", "环(个)", "时长")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # 设置列标题和宽度
        tree.heading("场景名称", text="场景名称")
        tree.heading("卡片(张)", text="卡片(张)")
        tree.heading("环(个)", text="环(个)")
        tree.heading("时长", text="时长")

        tree.column("场景名称", width=200, anchor="center")
        tree.column("卡片(张)", width=100, anchor="center")
        tree.column("环(个)", width=100, anchor="center")
        tree.column("时长", width=150, anchor="center")

        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充数据
        try:
            # 如果引擎正在运行，从引擎获取实时数据
            if engine:
                history = engine.get_scene_history()
            else:
                # 设备未启动，从文件加载历史数据（支持多天）
                history = load_scene_history_from_file(serial)

            # 连续同名场景合并为一条（旧数据里的重复行 / 重启产生的分段记录）：
            # 时长累计、环/卡累加；中间隔了其他场景的再次进入仍各自一行
            merged_history = []
            for record in history:
                if merged_history and merged_history[-1].get("name") == record.get("name"):
                    merged_history[-1]["duration"] = (merged_history[-1].get("duration") or 0) + (record.get("duration") or 0)
                    merged_history[-1]["cards"] = (merged_history[-1].get("cards") or 0) + (record.get("cards") or 0)
                    merged_history[-1]["rings"] = (merged_history[-1].get("rings") or 0) + (record.get("rings") or 0)
                else:
                    merged_history.append(dict(record))
            history = merged_history

            if not history:
                tree.insert("", tk.END, values=("暂无场景记录", "--", "--", "--", "--"))
            else:
                # 按日期分组显示
                current_date = None
                for record in history:
                    # 检查是否有日期字段（从文件加载的历史有日期）
                    record_date = record.get("date", "")
                    if record_date and record_date != current_date:
                        current_date = record_date
                        # 插入日期分隔行
                        tree.insert("", tk.END, values=(f"📅 {record_date}", "---", "---", "---"),
                                  tags=("date_row"))

                    duration_str = fmt_duration_hm(record["duration"])

                    tree.insert("", tk.END, values=(
                        record["name"],
                        record["cards"],
                        record["rings"],
                        duration_str
                    ))

                # 设置日期行的样式
                tree.tag_configure("date_row", background="#f0f0f0", foreground="#666")
        except Exception as e:
            tree.insert("", tk.END, values=(f"获取历史失败: {e}", "--", "--", "--", "--"))

        # ===== Tab 2: 配置信息 =====
        config_frame = ttk.Frame(notebook, padding=15)
        notebook.add(config_frame, text="配置信息")

        # 获取设备有效配置
        device_cfg = self._get_effective_config(serial)
        has_custom = self._device_configs.get(serial) is not None

        # 配置来源提示
        source_frame = ttk.Frame(config_frame)
        source_frame.pack(fill=tk.X, pady=(0, 15))
        if has_custom:
            ttk.Label(source_frame, text="🔧 使用独立配置",
                      foreground="#ff6b00", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT)
        else:
            ttk.Label(source_frame, text="📋 使用全局配置",
                      foreground="gray", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)

        # 配置详情表格
        config_table = ttk.Frame(config_frame)
        config_table.pack(fill=tk.BOTH, expand=True)

        # 关键配置项
        key_configs = [
            ("地图", device_cfg.get("map", "--")),
            ("HP恢复方式", device_cfg.get("hp_method", "--")),
            ("HP阈值", f"{device_cfg.get('hp_threshold', 0)}%"),
            ("MP恢复方式", device_cfg.get("mp_method", "--")),
            ("MP阈值", f"{device_cfg.get('mp_threshold', 0)}%"),
            ("捕捉召唤兽", "是" if device_cfg.get("capture_bb_enabled") else "否"),
            ("妙手空空", "是" if device_cfg.get("miaoshou_enabled") else "否"),
            ("战斗模式", self._get_combat_mode_text(device_cfg)),
            ("自动寻路", "是" if device_cfg.get("auto_path_enabled") else "否"),
            ("坐标检测", "是" if device_cfg.get("coord_enabled") else "否"),
            ("本地四小人", "是" if device_cfg.get("use_local_four_person") else "否"),
            ("背包计数", "是" if device_cfg.get("check_pkg_counts") else "否"),
            ("真实切场", "是" if device_cfg.get("use_real_scene_switch") else "否"),
        ]

        for i, (key, value) in enumerate(key_configs):
            row = i // 2
            col = (i % 2) * 2

            ttk.Label(config_table, text=f"{key}：",
                     font=("Microsoft YaHei", 9)).grid(row=row, column=col, sticky="e", padx=(0, 5), pady=3)
            ttk.Label(config_table, text=value,
                     font=("Microsoft YaHei", 9, "bold")).grid(row=row, column=col+1, sticky="w", padx=(0, 20), pady=3)

        # ===== 妙手空空场景配置摘要（可滚动，限高避免挤压底部按钮） =====
        scene_cfg = device_cfg.get("scene_config", []) or []
        scene_box = ttk.Labelframe(config_frame, text=" 妙手空空场景配置 ", padding=(10, 6))
        scene_box.pack(fill=tk.X, pady=(12, 0))

        scene_canvas = tk.Canvas(scene_box, height=150, highlightthickness=0)
        scene_scroll = ttk.Scrollbar(scene_box, orient=tk.VERTICAL, command=scene_canvas.yview)
        rows_frame = ttk.Frame(scene_canvas)
        rows_frame.bind(
            "<Configure>",
            lambda e: scene_canvas.configure(scrollregion=scene_canvas.bbox("all"))
        )
        scene_canvas.create_window((0, 0), window=rows_frame, anchor="nw")
        scene_canvas.configure(yscrollcommand=scene_scroll.set)

        enabled_rows = [r for r in scene_cfg if r.get("enabled")]
        disabled_rows = [r for r in scene_cfg if not r.get("enabled")]
        if not enabled_rows:
            ttk.Label(rows_frame, text="未配置启用的场景",
                      foreground="gray", font=("Microsoft YaHei", 9)).pack(anchor="w", pady=2)
        else:
            for r in enabled_rows:
                ttk.Label(rows_frame,
                          text=(f"✅ {r.get('scene', '--')}　环:{r.get('rings', '无要求')}　"
                                f"卡:{r.get('cards', '无要求')}　时间:{r.get('time', '无要求')}　"
                                f"后续:{r.get('after', '后换场景')}"),
                          font=("Microsoft YaHei", 9), foreground="#198754").pack(anchor="w", pady=1)
            if disabled_rows:
                ttk.Separator(rows_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
                for r in disabled_rows:
                    ttk.Label(rows_frame, text=f"☐ {r.get('scene', '--')}（未启用）",
                              font=("Microsoft YaHei", 9), foreground="#999").pack(anchor="w", pady=1)
        scene_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scene_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(scene_box, text="💡 点击「编辑场景配置」可单独修改此设备的场景配置，其他设置仍跟随全局配置",
                  foreground="#666", font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(4, 0))

        # 底部操作按钮
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(btn_frame, text="编辑场景配置",
                   command=lambda: self._edit_device_scene_config(serial, dlg),
                   bootstyle="success", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="对比配置", command=lambda: self._compare_config(serial),
                   bootstyle="info", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="复制配置", command=lambda: self._copy_config_to_devices(serial),
                   bootstyle="warning", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="保存为模板", command=lambda: self._save_config_template(serial),
                   bootstyle="success", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="清除历史", command=lambda: self._clear_scene_history(serial, dlg),
                   bootstyle="danger", width=12).pack(side=tk.LEFT)

        # 居中显示
        dlg.update_idletasks()
        self.root.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

    def _clear_scene_history(self, serial, parent_dlg):
        """清除设备场景历史"""
        from datetime import timedelta

        # 创建选择弹窗
        clear_dlg = tk.Toplevel(parent_dlg)
        clear_dlg.title("清除场景历史")
        clear_dlg.geometry("400x300")
        clear_dlg.resizable(False, False)
        clear_dlg.transient(parent_dlg)
        clear_dlg.grab_set()

        ttk.Label(clear_dlg, text="选择要清除的历史",
                  font=("Microsoft YaHei", 12, "bold")).pack(pady=(15, 10))

        ttk.Label(clear_dlg, text=f"设备: {serial}",
                  foreground="gray").pack(pady=(0, 15))

        # 选项
        options_frame = ttk.Frame(clear_dlg)
        options_frame.pack(fill=tk.X, padx=40)

        clear_var = tk.StringVar(value="today")

        ttk.Radiobutton(options_frame, text="仅清除今日历史",
                       variable=clear_var, value="today").pack(anchor="w", pady=5)
        ttk.Radiobutton(options_frame, text="清除最近7天历史",
                       variable=clear_var, value="week").pack(anchor="w", pady=5)
        ttk.Radiobutton(options_frame, text="清除所有历史",
                       variable=clear_var, value="all").pack(anchor="w", pady=5)

        def on_confirm():
            choice = clear_var.get()
            if choice == "today":
                # 只删除当前统计日（每天5:00为界）的历史文件
                files = [get_scene_history_file(serial, stats_day())]
                msg = f"确定要清除设备 [{serial}] 今日的场景历史吗？"
            elif choice == "week":
                # 删除最近7个统计日的历史文件
                from datetime import timedelta
                files = []
                today = datetime.now()
                for i in range(7):
                    date = today - timedelta(days=i, hours=5)
                    date_str = date.strftime("%Y-%m-%d")
                    files.append(get_scene_history_file(serial, date_str))
                msg = f"确定要清除设备 [{serial}] 最近7天的场景历史吗？"
            else:
                # 删除所有历史文件
                import glob
                pattern = os.path.join(SCENE_HISTORY_DIR, f"scene_history_{serial}_*.json")
                files = glob.glob(pattern)
                msg = f"确定要清除设备 [{serial}] 所有的场景历史吗？"

            clear_dlg.destroy()

            if messagebox.askyesno("确认清除", f"{msg}\n\n此操作不可撤销。"):
                cleared_count = 0
                for history_file in files:
                    try:
                        if os.path.exists(history_file):
                            os.remove(history_file)
                            cleared_count += 1
                    except Exception as e:
                        self._log(f"⚠️ 清除历史文件失败 {history_file}: {e}")

                # 如果设备正在运行，也清除内存中的历史
                engine = self.engines.get(serial)
                if engine and clear_var.get() == "today":
                    engine._scene_history = []
                    engine._save_scene_history()

                self._log(f"[{serial}] 已清除 {cleared_count} 个历史文件")
                messagebox.showinfo("完成", f"已清除 {cleeled_count} 个历史文件")

                # 刷新详情弹窗
                parent_dlg.destroy()
                self._show_device_detail(serial)

        btn_frame = ttk.Frame(clear_dlg)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="确定清除", command=on_confirm,
                   bootstyle="danger", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=clear_dlg.destroy,
                   bootstyle="outline", width=12).pack(side=tk.LEFT)

        # 居中显示
        clear_dlg.update_idletasks()
        parent_dlg.update_idletasks()
        pw = parent_dlg.winfo_width()
        ph = parent_dlg.winfo_height()
        px = parent_dlg.winfo_x()
        py = parent_dlg.winfo_y()
        ww = clear_dlg.winfo_width()
        wh = clear_dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        clear_dlg.geometry(f"+{x}+{y}")

    def _get_combat_mode_text(self, cfg):
        """获取战斗模式文本"""
        if cfg.get("skill_then_auto"):
            return "技能后自动"
        elif cfg.get("normal_then_auto"):
            return "普攻后自动"
        elif cfg.get("defend_then_auto"):
            return "防御后自动"
        elif cfg.get("direct_auto"):
            return "直接自动"
        elif cfg.get("escape_enabled"):
            return "逃跑"
        else:
            return "未设置"

    def _compare_config(self, serial):
        """对比设备配置与全局配置的差异"""
        device_cfg = self._get_effective_config(serial)
        has_custom = self._device_configs.get(serial) is not None

        if not has_custom:
            messagebox.showinfo("配置对比", f"设备 [{serial}] 使用的是全局配置，无差异。")
            return

        # 创建对比弹窗
        dlg = tk.Toplevel(self.root)
        dlg.title(f"配置对比 - {serial}")
        dlg.geometry("900x600")
        dlg.resizable(True, True)
        dlg.transient(self.root)
        dlg.grab_set()

        # 标题
        title_frame = ttk.Frame(dlg, padding=10)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="配置差异对比",
                  font=("Microsoft YaHei", 14, "bold")).pack(side=tk.LEFT)

        # 表头
        header_frame = ttk.Frame(dlg, padding=(10, 0))
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="配置项", width=20, font=("Microsoft YaHei", 9, "bold"),
                 anchor="center").grid(row=0, column=0, padx=1)
        ttk.Label(header_frame, text="全局配置", width=25, font=("Microsoft YaHei", 9, "bold"),
                 foreground="#666", anchor="center").grid(row=0, column=1, padx=1)
        ttk.Label(header_frame, text="设备配置", width=25, font=("Microsoft YaHei", 9, "bold"),
                 foreground="#ff6b00", anchor="center").grid(row=0, column=2, padx=1)

        # 对比容器
        canvas = tk.Canvas(dlg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dlg, orient=tk.VERTICAL, command=canvas.yview)
        compare_frame = ttk.Frame(canvas)

        compare_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=compare_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # 配置项对比
        config_keys = [
            ("地图", "map"),
            ("HP恢复", "hp_method"),
            ("HP阈值", "hp_threshold"),
            ("MP恢复", "mp_method"),
            ("MP阈值", "mp_threshold"),
            ("捕捉", "capture_bb_enabled"),
            ("妙手", "miaoshou_enabled"),
            ("战斗模式", "combat_mode"),
            ("自动寻路", "auto_path_enabled"),
            ("坐标检测", "coord_enabled"),
            ("本地四小人", "use_local_four_person"),
            ("背包计数", "check_pkg_counts"),
            ("真实切场", "use_real_scene_switch"),
        ]

        for i, (label, key) in enumerate(config_keys):
            # 获取全局配置值
            global_val = self._format_config_value(key, self.cfg)

            # 获取设备配置值
            device_val = self._format_config_value(key, device_cfg)

            # 判断是否相同
            is_different = global_val != device_val
            bg_color = "#fff3cd" if is_different else "white"
            fg_color = "#ff6b00" if is_different else "#333"

            # 配置项名
            ttk.Label(compare_frame, text=label, width=18, anchor="e",
                     font=("Microsoft YaHei", 9)).grid(row=i, column=0, padx=5, pady=3, sticky="e")

            # 全局配置值
            ttk.Label(compare_frame, text=global_val, width=23, anchor="center",
                     foreground="#666", font=("Microsoft YaHei", 9)).grid(
                row=i, column=1, padx=5, pady=3)

            # 设备配置值
            ttk.Label(compare_frame, text=device_val, width=23, anchor="center",
                     foreground=fg_color, font=("Microsoft YaHei", 9, "bold" if is_different else "")).grid(
                row=i, column=2, padx=5, pady=3)

        # 底部按钮
        btn_frame = ttk.Frame(dlg, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="关闭", command=dlg.destroy,
                   bootstyle="primary", width=10).pack(side=tk.RIGHT, padx=(0, 10))
        ttk.Button(btn_frame, text="应用全局配置",
                   command=lambda: self._apply_global_config(serial, dlg),
                   bootstyle="warning", width=15).pack(side=tk.RIGHT)

    def _format_config_value(self, key, cfg):
        """格式化配置值用于显示"""
        value = cfg.get(key, "")
        if key == "combat_mode":
            return self._get_combat_mode_text(cfg)
        elif key in ["capture_bb_enabled", "miaoshou_enabled", "auto_path_enabled",
                     "coord_enabled", "use_local_four_person", "check_pkg_counts",
                     "use_real_scene_switch"]:
            return "是" if value else "否"
        elif key in ["hp_threshold", "mp_threshold"]:
            return f"{value}%"
        else:
            return str(value) if value != "" else "--"

    def _apply_global_config(self, serial, dialog):
        """将全局配置应用到设备（清除设备独立配置）"""
        if messagebox.askyesno("确认",
            f"确定要将全局配置应用到设备 [{serial}] 吗？\n\n"
            "这将清除该设备的独立配置，之后将使用全局配置。"):
            device_file = get_device_config_file(serial)
            try:
                if os.path.exists(device_file):
                    os.remove(device_file)
                self._device_configs[serial] = None
                self._log(f"[{serial}] 已清除独立配置，将使用全局配置")
                dialog.destroy()
                self._refresh_device_tab()
            except Exception as e:
                messagebox.showerror("错误", f"应用配置失败：{e}")

    def _copy_config_to_devices(self, source_serial):
        """复制配置到其他设备"""
        # 获取源设备配置
        source_cfg = self._get_effective_config(source_serial)
        dev_names = self.cfg.get("device_names", {})
        source_name = dev_names.get(source_serial, source_serial[:4])

        # 创建选择弹窗
        dlg = tk.Toplevel(self.root)
        dlg.title("复制配置")
        dlg.geometry("450x500")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        # 标题
        title_frame = ttk.Frame(dlg, padding=15)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame,
                 text=f"从 [{source_name}] 复制配置到：",
                 font=("Microsoft YaHei", 11)).pack(side=tk.LEFT)

        # 设备列表
        list_frame = ttk.Frame(dlg)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15)

        # 获取所有设备（排除源设备）
        all_devices = list_adb_devices()
        target_devices = [d for d in all_devices if d != source_serial]

        if not target_devices:
            ttk.Label(list_frame, text="没有其他设备可供复制",
                     foreground="gray").pack(pady=20)
        else:
            # 创建滚动区域
            canvas = tk.Canvas(list_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
            check_frame = ttk.Frame(canvas)

            check_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # 设备复选框
            check_vars = {}
            for i, serial in enumerate(target_devices):
                var = tk.BooleanVar(value=False)
                check_vars[serial] = var
                name = dev_names.get(serial, serial[:4])
                cb = ttk.Checkbutton(check_frame, text=f"{name} ({serial})",
                                    variable=var, bootstyle="primary")
                cb.pack(anchor="w", pady=2, padx=5)

        # 按钮区域
        btn_frame = ttk.Frame(dlg, padding=15)
        btn_frame.pack(fill=tk.X)

        def on_copy():
            selected = [s for s, v in check_vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("提示", "请选择要复制到的设备")
                return

            if messagebox.askyesno("确认",
                f"确定要将配置复制到 {len(selected)} 台设备吗？\n\n"
                "这将会覆盖这些设备的现有独立配置。"):
                for serial in selected:
                    save_device_config(serial, source_cfg)
                    self._device_configs[serial] = source_cfg
                    self._log(f"[{serial}] 已复制配置")
                self._log(f"✅ 配置已复制到 {len(selected)} 台设备")
                dlg.destroy()
                self._refresh_device_tab()

        ttk.Button(btn_frame, text="复制", command=on_copy,
                   bootstyle="success", width=12).pack(side=tk.RIGHT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dlg.destroy,
                   bootstyle="outline", width=12).pack(side=tk.RIGHT)

        # 居中显示
        dlg.update_idletasks()
        self.root.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

    def _save_config_template(self, serial):
        """将设备配置保存为模板"""
        device_cfg = self._get_effective_config(serial)
        dev_names = self.cfg.get("device_names", {})
        dev_name = dev_names.get(serial, serial[:4])

        # 创建保存模板弹窗
        dlg = tk.Toplevel(self.root)
        dlg.title("保存配置模板")
        dlg.geometry("400x250")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        # 标题
        ttk.Label(dlg, text="保存配置模板",
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=(15, 10))

        ttk.Label(dlg, text=f"从设备 [{dev_name}] 保存模板",
                 foreground="gray").pack(pady=(0, 15))

        # 模板名称输入
        input_frame = ttk.Frame(dlg)
        input_frame.pack(fill=tk.X, padx=40, pady=(0, 20))

        ttk.Label(input_frame, text="模板名称：").pack(anchor="w")
        entry = ttk.Entry(input_frame, width=30, font=("Microsoft YaHei", 11))
        entry.pack(fill=tk.X, pady=(5, 0))
        entry.insert(0, f"{dev_name}配置")
        entry.selection_range(0, tk.END)
        entry.focus_set()

        # 备注
        ttk.Label(input_frame, text="备注（可选）：").pack(anchor="w", pady=(10, 0))
        note_entry = ttk.Entry(input_frame, width=30, font=("Microsoft YaHei", 10))
        note_entry.pack(fill=tk.X, pady=(5, 0))

        # 按钮
        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=10)

        def on_save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入模板名称")
                return

            # 保存模板
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_templates")
            os.makedirs(template_dir, exist_ok=True)

            template_file = os.path.join(template_dir, f"{name}.json")
            template_data = {
                "name": name,
                "note": note_entry.get().strip(),
                "config": device_cfg,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            try:
                with open(template_file, "w", encoding="utf-8") as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=2)
                self._log(f"✅ 配置模板已保存: {name}")
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存模板失败：{e}")

        ttk.Button(btn_frame, text="保存", command=on_save,
                   bootstyle="success", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dlg.destroy,
                   bootstyle="outline", width=12).pack(side=tk.LEFT)

        # 居中显示
        dlg.update_idletasks()
        self.root.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

    # ---------- 设备 ----------
    def _refresh_devices(self):
        """刷新设备下拉列表（显示设备名称）"""
        devices = list_adb_devices()
        dev_names = self.cfg.get("device_names", {})

        # 构建显示列表：设备名称 (序列号)
        display_list = []
        self._serial_to_display = {}  # 序列号 -> 显示文本
        self._display_to_serial = {}  # 显示文本 -> 序列号

        for serial in devices:
            name = dev_names.get(serial, "")
            if name:
                display_text = f"{name} ({serial})"
            else:
                display_text = serial
            display_list.append(display_text)
            self._serial_to_display[serial] = display_text
            self._display_to_serial[display_text] = serial

        self.device_combo["values"] = display_list
        if devices:
            current_serial = self.cfg.get("serial", "")
            if current_serial in self._serial_to_display:
                self.device_combo.set(self._serial_to_display[current_serial])
            else:
                self.device_combo.set(display_list[0])
                self.cfg["serial"] = devices[0]
            self.dev_status.configure(text=f"设备: {self.cfg['serial']}", foreground="green")
            self._update_tab1_buttons()
        else:
            self.device_combo.set("")
            self.dev_status.configure(text="未绑定", foreground="gray")
            self.btn_start.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.DISABLED)

    def _on_device_selected(self, event=None):
        """下拉选择设备时更新按钮状态"""
        sel = self.device_combo.get()
        if sel:
            # 从显示文本中提取序列号
            serial = self._display_to_serial.get(sel, sel)
            self.cfg["serial"] = serial
            self.dev_status.configure(text=f"设备: {serial}", foreground="green")
            self._update_tab1_buttons()

    def _update_tab1_buttons(self):
        """根据当前选中设备的运行状态更新按钮"""
        serial = self.cfg.get("serial", "")
        engine = self.engines.get(serial)
        running = engine is not None and engine.running
        if running:
            self.btn_start.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.NORMAL)
        else:
            self.btn_start.configure(state=tk.NORMAL)
            self.btn_stop.configure(state=tk.DISABLED)

    def start_engine(self):
        serial = self.cfg.get("serial")
        if not serial:
            messagebox.showwarning("提示", "请先绑定设备")
            return
        self._sync_ui_to_cfg()
        save_config(self.cfg)

        # 检查是否要为当前设备创建独立配置
        if self._device_configs.get(serial) is None:
            # 设备没有独立配置，询问用户是否要创建
            result = messagebox.askyesno(
                "设备配置",
                f"当前设备 [{serial}] 没有独立配置，将使用全局配置启动。\n\n"
                "是否要为此设备创建独立配置？\n"
                "（选择「是」将保存当前设置为该设备的独立配置，"
                "之后修改此设备的配置不会影响其他设备）"
            )
            if result:
                self._save_device_config(serial)

        self._start_device(serial)

    def stop_engine(self):
        serial = self.cfg.get("serial")
        if serial:
            self._stop_device(serial)

    def _take_screenshot(self):
        """截取当前绑定设备屏幕并保存到 screenshots 目录"""
        serial = self.cfg.get("serial", "").strip()
        if not serial:
            messagebox.showwarning("提示", "请先绑定设备再截图")
            return
        self._device_screenshot(serial)

    def _bind_window(self):
        serial = self.device_combo.get()
        if not serial:
            messagebox.showwarning("提示", "请先选择一个设备")
            return
        # 从显示文本中提取序列号
        serial = self._display_to_serial.get(serial, serial)
        self.cfg["serial"] = serial
        save_config(self.cfg)
        self.dev_status.configure(text=f"设备: {serial}", foreground="#0d6efd")
        self._log(f"✅ 已绑定设备: {serial}")
        self._update_tab1_buttons()

    # ---------- 引擎控制 ----------
    def _on_engine_stopped(self):
        self._save_device_stats()
        self._draw_status("gray")
        self.status_label.configure(text="已停止")
        self.root.after(100, self._update_tab1_buttons)
        self.root.after(150, self._refresh_devices)
        self.root.after(200, self._refresh_device_tab)
        self.hp_display.configure(text="气血: --%")
        self.mp_display.configure(text="魔法: --%")
        self.bb_display.configure(text="BB: --%")
        self.coord_display.configure(text="--")
        self.battle_display.configure(text="⚔ -- 场")
        self.time_display.configure(text="⏱ 00:00")
        self.coord_display.configure(text="📍 --")

    # ---------- 日志 ----------
    def _poll_log(self):
        try:
            # 每隔一定时间更新日志筛选选项
            if hasattr(self, '_last_filter_update'):
                if time.time() - self._last_filter_update > 5:  # 每5秒更新一次
                    self._update_log_filter_options()
                    self._last_filter_update = time.time()
            else:
                self._last_filter_update = time.time()

            while True:
                msg = self.log_queue.get_nowait()
                if msg == "__STOPPED__":
                    self.root.after(0, self._on_engine_stopped)
                    continue
                if isinstance(msg, str) and msg.startswith("__ALERT__:"):
                    parts = msg.split(":", 2)
                    dev = parts[1] if len(parts) > 1 else ""
                    text = parts[2] if len(parts) > 2 else msg
                    self.root.after(0, lambda d=dev, t=text: messagebox.showwarning("提醒", f"设备 [{d}]\n{t}"))
                    continue
                self._log_to_ui(msg)
                if self.engine:
                    hp = self.engine.last_hp
                    mp = self.engine.last_mp
                    bb = self.engine.last_bb
                    no_bb = self.engine.has_no_bb
                    self.hp_display.configure(text=f"气血: {hp:.0f}%")
                    self.mp_display.configure(text=f"魔法: {mp:.0f}%")
                    self.bb_display.configure(text=f"BB: {'--' if no_bb else f'{bb:.0f}%'}")
                    # 坐标显示
                    coord = self.engine.last_coord
                    map_name = self.engine.last_map_name
                    if coord:
                        self.coord_display.configure(text=f"📍 {map_name or ''}({coord[0]},{coord[1]})")
                    else:
                        self.coord_display.configure(text="📍 --")
                    # 战斗场次 运行时间
                    bc = self.engine.battle_count
                    self.battle_display.configure(text=f"⚔ {bc} 场")
                    if self.engine.start_time > 0:
                        elapsed = int((getattr(self.engine, "total_runtime", 0) or 0)
                                      + (time.time() - self.engine.start_time))
                        m, s = divmod(elapsed, 60)
                        self.time_display.configure(text=f"⏱ {m:02d}:{s:02d}")
                # 同步更新设备管理页的每台设备数据
                if self._device_widgets:
                    for ser, eng in self.engines.items():
                        w = self._device_widgets.get(ser)
                        if w and eng and eng.running:
                            scene = getattr(eng, "last_map_name", None) or eng.cfg.get("map", "") or "--"
                            w["scene"].configure(text=scene)
                            w["card"].configure(text=str(eng._daily_card_count))
                            w["huan"].configure(text=str(eng._daily_huan_count))
                            w["bc"].configure(text=str(eng.battle_count))
                            if getattr(eng, "start_time", 0):
                                elapsed = int((getattr(eng, "total_runtime", 0) or 0)
                                              + (time.time() - eng.start_time))
                                w["dur"].configure(text=fmt_duration_hm(elapsed))
                            w["status"].configure(text="运行中", foreground="green")
                    # 同步更新总计行（所有运行中设备的卡片/环总数）
                    if getattr(self, "_total_widgets", None):
                        tc, th = self._compute_total_counts()
                        self._total_widgets["card"].configure(text=str(tc))
                        self._total_widgets["huan"].configure(text=str(th))
                        if "dur" in self._total_widgets:
                            self._total_widgets["dur"].configure(
                                text=fmt_duration_hm(self._compute_total_runtime()))
        except queue.Empty:
            pass
        # 定期把当日累计写盘（异常退出最多丢失60秒增量）
        if any(eng is not None and getattr(eng, "running", False)
               for eng in self.engines.values()):
            now = time.time()
            if now - getattr(self, "_last_stats_save_t", 0) >= 60:
                self._last_stats_save_t = now
                self._save_device_stats()
        self.root.after(300, self._poll_log)

    def _log(self, msg):
        """GUI系统日志：输出到UI和文件"""
        ts = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{ts}] {msg}"
        self._log_to_ui(log_msg)
        # 写入GUI日志文件
        self._write_gui_log(ts, msg)

    def _write_gui_log(self, timestamp, msg):
        """写入GUI系统日志到文件"""
        try:
            # 按日期文件夹存储：logs/YYYY-MM-DD/GUI.log（跨天自动切换）
            self.gui_log_file = self._gui_daily_log_file()
            # 检查日志文件大小，超过10MB自动轮转
            max_size = 10 * 1024 * 1024  # 10MB
            if os.path.exists(self.gui_log_file):
                file_size = os.path.getsize(self.gui_log_file)
                if file_size > max_size:
                    # 重命名旧文件
                    base, ext = os.path.splitext(self.gui_log_file)
                    old_file = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
                    os.rename(self.gui_log_file, old_file)
            # 写入新日志
            with open(self.gui_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
                f.flush()  # 立即刷新到磁盘
        except Exception as e:
            try:
                print(f"GUI日志写入失败: {e}")
            except:
                pass

    def _gui_daily_log_file(self):
        """返回当天日期目录下的 GUI 日志路径：logs/YYYY-MM-DD/GUI.log。"""
        day = datetime.now().strftime("%Y-%m-%d")
        day_dir = os.path.join(self.gui_log_dir, day)
        if self._gui_log_day_dir != day_dir:
            self._gui_log_day_dir = day_dir
            os.makedirs(day_dir, exist_ok=True)
        return os.path.join(day_dir, "GUI.log")

    def _log_to_ui(self, msg):
        """将日志添加到列表并根据筛选条件显示"""

        # 解析日志中的设备ID

        device_id = None

        # 格式: [时间] [设备ID] 消息 或 [时间] 消息

        import re

        match = re.search(r'\[([^\]]+)\]\s*\[([^\]]+)\]', msg)

        if match:

            # 第一个是时间，第二个是设备ID

            device_id = match.group(2)

        else:

            # 尝试匹配 [设备ID] 格式

            match = re.search(r'\[([^\]]+)\]', msg)

            if match and ":" not in match.group(1):  # 不是时间格式

                device_id = match.group(1)

        # 如果没有设备ID，默认为系统消息

        if not device_id:

            device_id = "系统"

        # 存储日志

        timestamp = datetime.now()

        self.all_logs.append((device_id, timestamp, msg))

        # 根据筛选条件决定是否显示

        filter_val = self.log_filter_var.get()

        should_show = (filter_val == "全部设备") or (filter_val == device_id)

        if should_show:

            self.log_text.configure(state=tk.NORMAL)

            self.log_text.insert(tk.END, msg + "\n")

            # 自动滚动勾选时才跟随最新日志；取消勾选后可自由翻看历史
            if self.log_follow.get():

                self.log_text.see(tk.END)

            self.log_text.configure(state=tk.DISABLED)

        # 更新日志计数

        self._update_log_count()

    def _on_log_scroll(self, event):
        """日志框滚轮：向上翻看历史时自动暂停跟随，滚回底部自动恢复"""
        try:
            if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
                # 向上滚动 → 暂停自动滚动，便于翻看历史
                self.log_follow.set(False)
            else:
                # 向下滚动：已在底部则恢复自动滚动
                if self.log_text.yview()[1] >= 0.999:
                    self.log_follow.set(True)
        except Exception:
            pass

    def _update_log_count(self):

        """更新日志计数显示"""

        filter_val = self.log_filter_var.get()

        if filter_val == "全部设备":

            count = len(self.all_logs)

        else:

            count = sum(1 for d, _, _ in self.all_logs if d == filter_val)

        self.log_count_label.configure(text=f"共 {count} 条")

    def _refresh_log_display(self):

        """根据当前筛选条件刷新日志显示"""

        self.log_text.configure(state=tk.NORMAL)

        self.log_text.delete("1.0", tk.END)

        filter_val = self.log_filter_var.get()

        for device_id, timestamp, msg in self.all_logs:

            if filter_val == "全部设备" or filter_val == device_id:

                self.log_text.insert(tk.END, msg + "\n")

        # 自动滚动勾选时才滚到底部（筛选切换后仍跟随最新）
        if self.log_follow.get():

            self.log_text.see(tk.END)

        self.log_text.configure(state=tk.DISABLED)

        self._update_log_count()

    def _on_log_filter_change(self, event=None):

        """筛选条件变化时刷新显示"""

        self._refresh_log_display()

    def _update_log_filter_options(self):

        """更新日志筛选下拉框选项：全部设备 + 所有已连接设备 + 有日志的标识"""

        devices_with_logs = set()

        # 收集所有有日志的设备

        for device_id, _, _ in self.all_logs:

            if device_id:

                devices_with_logs.add(device_id)

        # 所有已连接的 ADB 设备（无论是否运行/有无日志，都能在筛选里选）
        # 标识与引擎日志一致：自定义名优先，否则 前5位(尾3位)
        try:
            dev_names = self.cfg.get("device_names", {}) or {}
            from mhxy_engine import list_adb_devices as _lad
            for serial in _lad():
                dev_id = dev_names.get(serial, "") or short_dev_label(serial)
                if dev_id:
                    devices_with_logs.add(dev_id)
        except Exception:
            pass

        # 添加当前运行的引擎（标识与日志保持一致）

        for serial, engine in self.engines.items():

            if engine.running:

                dev_id = getattr(engine, "device_id", "") or ""

                if not dev_id:

                    dev_id = short_dev_label(serial)

                if dev_id:

                    devices_with_logs.add(dev_id)

        # 构建选项列表：按设备列表顺序排列（与设备管理页一致）
        ordered_ids = []
        try:
            dev_names = self.cfg.get("device_names", {}) or {}
            from mhxy_engine import list_adb_devices as _lad
            order = list(getattr(self, "_device_order", None) or [])
            if not order:
                order = list(_lad())
            # 运行中的引擎追加到末尾，确保出现在下拉里
            for serial, engine in self.engines.items():
                if engine.running and serial not in order:
                    order.append(serial)
            for serial in order:
                label = dev_names.get(serial, "") or short_dev_label(serial)
                if label and label not in ordered_ids:
                    ordered_ids.append(label)
        except Exception:
            pass
        # 有日志但不在设备列表里的标识（历史/已拔出设备）排后面，系统消息排最后
        extra = sorted(l for l in devices_with_logs if l not in ordered_ids and l != "系统")
        options = ["全部设备"] + ordered_ids + extra
        if "系统" in devices_with_logs:
            options.append("系统")

        current_val = self.log_filter_var.get()

        self.log_filter_combo["values"] = options

        # 如果当前值不在新选项中，重置为"全部设备"

        if current_val not in options:

            self.log_filter_var.set("全部设备")

        else:

            self.log_filter_combo.set(current_val)

    def _clear_log(self):

        """清空日志"""

        self.all_logs.clear()

        self.log_text.configure(state=tk.NORMAL)

        self.log_text.delete("1.0", tk.END)

        self.log_text.configure(state=tk.DISABLED)

        self._update_log_count()

    # ---------- 配置 ----------
    def _load_cfg_to_ui(self):
        cfg = self.cfg
        self.hp_method.set(cfg.get("hp_method", "酒肆"))
        self.hp_threshold.set(cfg.get("hp_threshold", 30))
        self.mp_method.set(cfg.get("mp_method", "酒肆"))
        self.mp_threshold.set(cfg.get("mp_threshold", 20))

        self.jiusi_enabled.set(cfg.get("jiusi_enabled", True))
        self.jiusi_hp_threshold.set(cfg.get("jiusi_hp_threshold", 50))
        self.jiusi_mp_threshold.set(cfg.get("jiusi_mp_threshold", 30))
        self.jiusi_bb_threshold.set(cfg.get("jiusi_bb_threshold", 50))

        self.capture_bb_enabled.set(cfg.get("capture_bb_enabled", False))
        self.miaoshou_enabled.set(cfg.get("miaoshou_enabled", True))
        _mode = "escape"
        if cfg.get("skill_then_auto"): _mode = "skill_then_auto"
        elif cfg.get("normal_then_auto"): _mode = "normal_then_auto"
        elif cfg.get("defend_then_auto"): _mode = "defend_then_auto"
        elif cfg.get("direct_auto"): _mode = "direct_auto"
        elif cfg.get("escape_enabled", True): _mode = "escape"
        self.combat_mode.set(_mode)
        self.auto_path_enabled.set(cfg.get("auto_path_enabled", True))
        self.coord_enabled.set(cfg.get("coord_enabled", True))
        self.local_four_person_enabled.set(cfg.get("use_local_four_person", True))
        self.check_pkg_counts_enabled.set(cfg.get("check_pkg_counts", True))
        self.real_scene_switch_enabled.set(cfg.get("use_real_scene_switch", True))

        self.map_select.set(cfg.get("map", "小西天"))
        self.project_select.set("点卡场景")

        if cfg.get("serial"):
            if cfg["serial"] in (self.device_combo["values"] or []):
                self.device_combo.set(cfg["serial"])
            self.dev_status.configure(text=f"设备: {cfg['serial']}", foreground="green")
            self._update_tab1_buttons()
        else:
            self.dev_status.configure(text="未绑定", foreground="gray")
            self.btn_start.configure(state=tk.DISABLED)

        self._update_all_threshold_labels()

    def _sync_ui_to_cfg(self):
        cfg = self.cfg
        cfg["hp_method"] = self.hp_method.get()
        cfg["mp_method"] = self.mp_method.get()
        cfg["hp_threshold"] = self.hp_threshold.get()
        cfg["mp_threshold"] = self.mp_threshold.get()

        hp = cfg["hp_method"]
        mp = cfg["mp_method"]

        if "秘制" in (hp, mp):
            cfg["mizhi_enabled"] = True
            cfg["hp_enabled"] = False
            cfg["mp_enabled"] = False
        else:
            cfg["mizhi_enabled"] = False
            cfg["hp_enabled"] = (hp != "酒肆")
            cfg["hp_item"] = hp if hp != "酒肆" else cfg.get("hp_item", "红碗")
            cfg["mp_enabled"] = (mp != "酒肆")
            cfg["mp_item"] = mp if mp != "酒肆" else cfg.get("mp_item", "蓝碗")

        cfg["jiusi_enabled"] = (hp == "酒肆" or mp == "酒肆")
        cfg["jiusi_hp_threshold"] = cfg["hp_threshold"] if hp == "酒肆" else 0
        cfg["jiusi_mp_threshold"] = cfg["mp_threshold"] if mp == "酒肆" else 0
        cfg["jiusi_bb_threshold"] = self.jiusi_bb_threshold.get()

        cfg["map"] = self.map_select.get()
        cfg["capture_bb_enabled"] = self.capture_bb_enabled.get()
        cfg["miaoshou_enabled"] = self.miaoshou_enabled.get()
        _mode = self.combat_mode.get()
        cfg["skill_then_auto"] = (_mode == "skill_then_auto")
        cfg["normal_then_auto"] = (_mode == "normal_then_auto")
        cfg["defend_then_auto"] = (_mode == "defend_then_auto")
        cfg["direct_auto"] = (_mode == "direct_auto")
        cfg["escape_enabled"] = (_mode == "escape")
        cfg["auto_path_enabled"] = self.auto_path_enabled.get()
        cfg["coord_enabled"] = self.coord_enabled.get()
        cfg["use_local_four_person"] = self.local_four_person_enabled.get()
        cfg["check_pkg_counts"] = self.check_pkg_counts_enabled.get()
        cfg["use_real_scene_switch"] = self.real_scene_switch_enabled.get()

    def _on_setting_change(self, event=None):
        pass

    def _save_cfg(self):
        serial = self.cfg.get("serial", "")
        self._sync_ui_to_cfg()

        # 如果有选中的设备，询问保存为全局配置还是设备独立配置
        if serial:
            result = messagebox.askyesnocancel(
                "保存配置",
                f"当前选中设备：[{serial}]\n\n"
                "「是」：保存为该设备的独立配置\n"
                "「否」：保存为全局配置（影响所有使用全局配置的设备）\n"
                "「取消」：不保存"
            )
            if result is True:  # 是 - 保存为设备独立配置
                self._save_device_config(serial)
                return
            elif result is False:  # 否 - 保存为全局配置
                save_config(self.cfg)
                self._log("✅ 全局配置已保存")
                return
            else:  # 取消
                return

        # 没有选中设备，直接保存为全局配置
        save_config(self.cfg)
        self._log("✅ 全局配置已保存")


    def _test_loyalty_recovery(self):
        """在功能测试页选择设备与场景后，独立测试忠诚度恢复。"""
        display = self.test_device_combo.get().strip()
        serial = self._test_display_to_serial.get(display, "").strip()
        scene = self.test_map_combo.get().strip()
        if not serial:
            messagebox.showwarning("提示", "请先在功能测试页选择设备")
            return
        if not scene:
            messagebox.showwarning("提示", "请先选择忠诚恢复场景")
            return

        engine = self.engines.get(serial)
        if engine and getattr(engine, "running", False):
            messagebox.showwarning(
                "提示",
                f"设备 [{display}] 主流程正在运行。\n请先停止该设备，避免两个流程同时操作手机。")
            return

        confirm = messagebox.askyesno(
            "确认测试",
            f"设备：{display}\n忠诚恢复场景：{scene}\n\n"
            "将独立执行忠诚恢复测试，途中遇到战斗会自动逃跑。是否继续？")
        if not confirm:
            return

        self._test_log(f"开始忠诚恢复测试 - 设备: {serial}, 场景: {scene}")
        self._test_stop_event.clear()

        def _run():
            tool = None
            try:
                from 工具 import ToolEngine
                tool = ToolEngine(serial)
                raw_log = tool._log

                def tool_log(msg):
                    raw_log(msg)
                    self.root.after(0, lambda m=msg: self._test_log(m))

                tool._log = tool_log
                tool._stop_event = self._test_stop_event
                if not tool.connect():
                    raise RuntimeError("ADB/scrcpy 连接失败")
                tool.cfg["map"] = scene
                tool.loyalty_recovery()
                self.root.after(0, lambda: self._test_log("✅ 忠诚恢复测试完成"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "测试完成", "忠诚恢复流程已执行完成！\n请查看测试日志确认执行结果。"))
            except Exception as e:
                self.root.after(0, lambda err=e: self._test_log(f"❌ 忠诚恢复测试失败: {err}"))
                self.root.after(0, lambda err=e: messagebox.showerror(
                    "测试失败", f"忠诚恢复流程执行失败：\n{err}"))
            finally:
                if tool:
                    tool.disconnect()

        threading.Thread(target=_run, daemon=True).start()



    def _open_scene_settings(self):
        dialog = SceneSettingsDialog(self.root, self.cfg.get("scene_config", []))
        self.root.wait_window(dialog.win)
        if dialog.result is not None:
            self.cfg["scene_config"] = dialog.result
            # 把第一个启用的场景同步到地图选择（方便引擎兼容旧逻辑）
            enabled = [r for r in dialog.result if r.get("enabled")]
            if enabled:
                first_scene = enabled[0]["scene"]
                if first_scene in list(MAP_CONFIG):
                    self.map_select.set(first_scene)
                else:
                    self.map_select.set("小西天")
            save_config(self.cfg)
            self._log("✅ 妙手空空场景配置已保存")

    def _edit_device_scene_config(self, serial, parent_dlg):
        """在设备详情中单独编辑该设备的妙手空空场景配置（局部覆盖，其他设置仍跟随全局）"""
        device_cfg = self._get_effective_config(serial)
        dialog = SceneSettingsDialog(parent_dlg, device_cfg.get("scene_config", []) or [])
        parent_dlg.wait_window(dialog.win)
        if dialog.result is None:
            return

        # 已有独立配置则在其基础上只更新 scene_config；
        # 没有则新建仅含 scene_config 的局部覆盖配置（其余键自然跟随全局）
        base = dict(self._device_configs.get(serial) or {})
        base["scene_config"] = dialog.result
        if not save_device_config(serial, base):
            messagebox.showerror("错误", "保存设备场景配置失败")
            return

        self._device_configs[serial] = base
        engine = self.engines.get(serial)
        if engine is not None and engine.running:
            self._log(f"[{serial}] ✅ 设备场景配置已保存（当前引擎正在运行，将在下次启动时生效）")
        else:
            self._log(f"[{serial}] ✅ 设备场景配置已保存，启动时将使用独立配置")
        # 重建详情弹窗刷新来源提示与场景摘要，并刷新设备管理页（🔧 标识）
        parent_dlg.destroy()
        self._refresh_device_tab()
        self._show_device_detail(serial)

    def _apply_scene_settings(self, scene_config):
        self.cfg["scene_config"] = scene_config

    def on_close(self):
        self._save_device_stats()
        running_count = sum(1 for e in self.engines.values() if e.running)
        if running_count > 0:
            if messagebox.askyesno("确认", f"有 {running_count} 个引擎正在运行，确定要退出吗？"):
                for e in self.engines.values():
                    e.running = False
                    if hasattr(e, '_loyalty_stop_event'):
                        e._loyalty_stop_event.set()
                for t in self.engine_threads.values():
                    t.join(timeout=3)
                self.root.destroy()
        else:
            self.root.destroy()

    def _show_config_templates(self):
        """显示配置模板管理弹窗"""
        # 创建模板管理弹窗
        dlg = tk.Toplevel(self.root)
        dlg.title("配置模板管理")
        dlg.geometry("700x550")
        dlg.resizable(True, True)
        dlg.transient(self.root)
        dlg.grab_set()

        # 主容器
        main = ttk.Frame(dlg, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # 标题区域
        title_frame = ttk.Frame(main)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ttk.Label(title_frame, text="配置模板",
                 font=("Microsoft YaHei", 14, "bold")).pack(side=tk.LEFT)

        ttk.Button(title_frame, text="从当前配置创建",
                  command=lambda: self._create_template_from_current(dlg),
                  bootstyle="success", width=15).pack(side=tk.RIGHT)

        # 居中显示
        dlg.update_idletasks()
        self.root.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

        # 模板列表区域
        list_frame = ttk.Frame(main)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建表格
        columns = ("模板名称", "备注", "创建时间", "操作")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        # 设置列标题和宽度
        tree.heading("模板名称", text="模板名称")
        tree.heading("备注", text="备注")
        tree.heading("创建时间", text="创建时间")
        tree.heading("操作", text="操作")

        tree.column("模板名称", width=180, anchor="w")
        tree.column("备注", width=200, anchor="w")
        tree.column("创建时间", width=150, anchor="center")
        tree.column("操作", width=120, anchor="center")

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 存储树控件
        self._template_tree = tree

        # 加载模板列表
        def load_templates():
            tree.delete(*tree.get_children())
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_templates")
            if not os.path.exists(template_dir):
                return

            for filename in os.listdir(template_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(template_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            template = json.load(f)

                        name = template.get("name", filename[:-5])
                        note = template.get("note", "")
                        created = template.get("created_at", "")

                        tree.insert("", tk.END, values=(
                            name,
                            note,
                            created,
                            "应用 | 删除"
                        ), tags=(filepath,))

                    except Exception as e:
                        self._log(f"⚠️ 加载模板失败 {filename}: {e}")

        # 绑定双击事件
        def on_double_click(event):
            item = tree.selection()
            if item:
                values = tree.item(item, "values")
                filepath = tree.item(item, "tags")[0] if tree.item(item, "tags") else ""
                # 获取点击位置判断操作
                region = tree.identify_region(event.x, event.y)
                if region == "cell":
                    column = tree.identify_column(event.x)
                    if column == "#4":  # 操作列
                        # 显示操作菜单
                        self._show_template_menu(event, filepath, item, dlg)

        tree.bind("<Double-1>", on_double_click)

        load_templates()

        # 底部按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        ttk.Button(btn_frame, text="刷新列表",
                  command=load_templates, bootstyle="outline", width=12).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="关闭", command=dlg.destroy,
                  bootstyle="primary", width=12).pack(side=tk.RIGHT)

    def _show_template_menu(self, event, filepath, item, parent_dlg):
        """显示模板操作菜单"""
        menu = tk.Menu(parent_dlg, tearoff=0)
        menu.add_command(label="应用到当前设备",
                        command=lambda: self._apply_template(filepath, parent_dlg))
        menu.add_command(label="应用到选中设备",
                        command=lambda: self._apply_template_to_selected(filepath, parent_dlg))
        menu.add_separator()
        menu.add_command(label="删除模板",
                        command=lambda: self._delete_template(filepath, item, parent_dlg))

        menu.post(event.x_root, event.y_root)

    def _apply_template(self, filepath, parent_dlg):
        """应用模板到当前设备"""
        serial = self.cfg.get("serial", "")
        if not serial:
            messagebox.showwarning("提示", "请先在场景控制页选择设备")
            return

        if not self._apply_template_to_device(filepath, serial):
            return

        messagebox.showinfo("成功", f"模板已应用到设备 [{serial}]")
        parent_dlg.destroy()
        self._refresh_device_tab()

    def _apply_template_to_selected(self, filepath, parent_dlg):
        """应用模板到选中的设备"""
        selected = self._selected_serials()
        if not selected:
            messagebox.showwarning("提示", "请先在设备管理页勾选设备")
            return

        if messagebox.askyesno("确认",
            f"确定要将模板应用到 {len(selected)} 台设备吗？\n\n"
            "这将会覆盖这些设备的现有独立配置。"):
            for serial in selected:
                self._apply_template_to_device(filepath, serial)
            messagebox.showinfo("成功", f"模板已应用到 {len(selected)} 台设备")
            parent_dlg.destroy()
            self._refresh_device_tab()

    def _apply_template_to_device(self, filepath, serial):
        """应用模板到指定设备"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                template = json.load(f)

            config = template.get("config", {})
            save_device_config(serial, config)
            self._device_configs[serial] = config
            self._log(f"[{serial}] 已应用模板: {template.get('name', '未知')}")
            return True

        except Exception as e:
            messagebox.showerror("错误", f"应用模板失败：{e}")
            return False

    def _delete_template(self, filepath, item, parent_dlg):
        """删除模板"""
        if messagebox.askyesno("确认删除", "确定要删除此模板吗？"):
            try:
                os.remove(filepath)
                if hasattr(self, "_template_tree"):
                    self._template_tree.delete(item)
                self._log("✅ 模板已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除模板失败：{e}")

    def _create_template_from_current(self, parent_dlg):
        """从当前UI配置创建模板"""
        serial = self.cfg.get("serial", "")

        # 创建保存模板弹窗
        dlg = tk.Toplevel(parent_dlg)
        dlg.title("保存配置模板")
        dlg.geometry("400x250")
        dlg.resizable(False, False)
        dlg.transient(parent_dlg)
        dlg.grab_set()

        # 标题
        ttk.Label(dlg, text="保存配置模板",
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=(15, 10))

        source_text = f"从当前配置保存" if not serial else f"从设备 [{serial}] 配置保存"
        ttk.Label(dlg, text=source_text,
                 foreground="gray").pack(pady=(0, 15))

        # 模板名称输入
        input_frame = ttk.Frame(dlg)
        input_frame.pack(fill=tk.X, padx=40, pady=(0, 20))

        ttk.Label(input_frame, text="模板名称：").pack(anchor="w")
        entry = ttk.Entry(input_frame, width=30, font=("Microsoft YaHei", 11))
        entry.pack(fill=tk.X, pady=(5, 0))
        default_name = f"配置模板_{datetime.now().strftime('%m%d_%H%M')}"
        entry.insert(0, default_name)
        entry.selection_range(0, tk.END)
        entry.focus_set()

        # 备注
        ttk.Label(input_frame, text="备注（可选）：").pack(anchor="w", pady=(10, 0))
        note_entry = ttk.Entry(input_frame, width=30, font=("Microsoft YaHei", 10))
        note_entry.pack(fill=tk.X, pady=(5, 0))

        # 按钮
        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=10)

        def on_save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入模板名称")
                return

            # 同步UI到配置
            self._sync_ui_to_cfg()

            # 保存模板
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_templates")
            os.makedirs(template_dir, exist_ok=True)

            template_file = os.path.join(template_dir, f"{name}.json")
            template_data = {
                "name": name,
                "note": note_entry.get().strip(),
                "config": self.cfg,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            try:
                with open(template_file, "w", encoding="utf-8") as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=2)
                self._log(f"✅ 配置模板已保存: {name}")
                dlg.destroy()
                parent_dlg.destroy()
                # 重新打开模板管理窗口
                self._show_config_templates()
            except Exception as e:
                messagebox.showerror("错误", f"保存模板失败：{e}")

        ttk.Button(btn_frame, text="保存", command=on_save,
                   bootstyle="success", width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dlg.destroy,
                   bootstyle="outline", width=12).pack(side=tk.LEFT)

        # 居中显示（相对于父窗口）
        dlg.update_idletasks()
        parent_dlg.update_idletasks()
        px = parent_dlg.winfo_x()
        py = parent_dlg.winfo_y()
        pw = parent_dlg.winfo_width()
        ph = parent_dlg.winfo_height()
        ww = dlg.winfo_width()
        wh = dlg.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        dlg.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()



class SceneSettingsDialog:
    """场景之妙手空空 - 多场景配置弹窗"""

    SCENE_NAMES = ["龙窟五层", "凤巢四层", "凤巢五层", "子母河底", "小西天", "小雷音寺", "女娲神迹", "须弥东界"]
    RING_OPTIONS = ["无要求", "得1个环", "得2个环", "得3个环", "得4个环"]
    CARD_OPTIONS = ["无要求", "得1张卡片", "得2张卡片"]
    TIME_OPTIONS = ["无要求", "满60分钟", "满120分钟", "满180分钟"]
    AFTER_OPTIONS = ["后换场景", "停止"]

    def __init__(self, parent, cfg_list):
        self.cfg_list = cfg_list or []
        self.result = None
        self.row_widgets = []
        self.row_frames = []  # 存储行框架用于拖动排序
        self.drag_row = None  # 当前拖动的行
        self.drag_start_y = 0  # 拖动起始Y坐标

        self.win = tk.Toplevel(parent)
        self.win.title("场景之妙手空空")
        self.win.geometry("1240x610")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()
        self._load_cfg()
        self._center_over_parent(parent)

    def _center_over_parent(self, parent):
        """将弹窗居中显示在主窗口上方，避免跑到屏幕角落"""
        self.win.update_idletasks()
        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        ww = self.win.winfo_width()
        wh = self.win.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2 - 30
        if y < 0:
            y = py + ph + 10
        self.win.geometry(f"+{x}+{y}")

    def _build_ui(self):
        main = ttk.Frame(self.win, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)

        # 标题区域
        ttk.Label(main, text="场景之妙手空空", font=("Microsoft YaHei", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(main, text="不支持自动换场景到：丝绸之路、无名鬼域；凤巢三层/凤巢五层仅支持打怪、暂不支持自动切入",
                 foreground="gray", font=("Microsoft YaHei", 9)).grid(
            row=1, column=0, sticky="w", pady=(0, 15))

        # 统一的表格容器 - 表头和所有行在同一个grid中
        table_container = ttk.Frame(main)
        table_container.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        table_container.columnconfigure(0, weight=0, minsize=40)   # 拖动把手
        table_container.columnconfigure(1, weight=0, minsize=70)   # 启用
        table_container.columnconfigure(2, weight=1, minsize=160)   # 场景
        table_container.columnconfigure(3, weight=1, minsize=140)   # 环数要求
        table_container.columnconfigure(4, weight=1, minsize=140)   # 卡片要求
        table_container.columnconfigure(5, weight=1, minsize=140)   # 时间要求
        table_container.columnconfigure(6, weight=1, minsize=120)   # 后续操作

        # 表头行 (row=0)
        tk.Label(table_container, text="⋮⋮", font=("Microsoft YaHei", 9, "bold"),
                width=4, bg="#f0f0f0", fg="#999").grid(row=0, column=0, padx=2, pady=8)
        tk.Label(table_container, text="启用", font=("Microsoft YaHei", 9, "bold"),
                width=8, anchor="w", bg="#f0f0f0").grid(row=0, column=1, padx=2, pady=8)
        tk.Label(table_container, text="场景", font=("Microsoft YaHei", 9, "bold"),
                width=18, anchor="center", bg="#f0f0f0").grid(row=0, column=2, padx=2, pady=8)
        tk.Label(table_container, text="环数要求", font=("Microsoft YaHei", 9, "bold"),
                width=16, anchor="center", bg="#f0f0f0").grid(row=0, column=3, padx=2, pady=8)
        tk.Label(table_container, text="卡片要求", font=("Microsoft YaHei", 9, "bold"),
                width=16, anchor="center", bg="#f0f0f0").grid(row=0, column=4, padx=2, pady=8)
        tk.Label(table_container, text="时间要求", font=("Microsoft YaHei", 9, "bold"),
                width=16, anchor="center", bg="#f0f0f0").grid(row=0, column=5, padx=2, pady=8)
        tk.Label(table_container, text="后续操作", font=("Microsoft YaHei", 9, "bold"),
                width=14, anchor="center", bg="#f0f0f0").grid(row=0, column=6, padx=2, pady=8)

        # 数据行 (row=1 到 8)
        for i in range(8):
            row_idx = i + 1  # 数据行从1开始

            enabled_var = tk.BooleanVar(value=False)
            scene_var = tk.StringVar(value="小西天")
            rings_var = tk.StringVar(value="无要求")
            cards_var = tk.StringVar(value="无要求")
            time_var = tk.StringVar(value="无要求")
            after_var = tk.StringVar(value="后换场景")

            # 拖动把手
            drag_handle = tk.Label(table_container, text="⋮⋮", bg="white", fg="#666",
                                   cursor="sb_v_double_arrow", width=4)
            drag_handle.grid(row=row_idx, column=0, padx=2, pady=8)

            # 添加拖动事件
            drag_handle.bind("<Button-1>", lambda e, idx=i: self._on_drag_start(e, idx))
            drag_handle.bind("<B1-Motion>", lambda e, idx=i: self._on_drag_motion(e, idx))
            drag_handle.bind("<ButtonRelease-1>", lambda e: self._on_drag_end(e))

            # 启用复选框
            cb = ttk.Checkbutton(table_container, text="", variable=enabled_var,
                               bootstyle="success-round-toggle")
            cb.grid(row=row_idx, column=1, padx=2, pady=8, sticky="w")

            # 场景下拉框
            scene_cb = ttk.Combobox(table_container, textvariable=scene_var,
                                   values=self.SCENE_NAMES, state="readonly",
                                   width=18, bootstyle="primary")
            scene_cb.grid(row=row_idx, column=2, padx=2, pady=8)

            # 环数要求
            rings_cb = ttk.Combobox(table_container, textvariable=rings_var,
                                    values=self.RING_OPTIONS, state="readonly",
                                    width=16, bootstyle="info")
            rings_cb.grid(row=row_idx, column=3, padx=2, pady=8)

            # 卡片要求
            cards_cb = ttk.Combobox(table_container, textvariable=cards_var,
                                    values=self.CARD_OPTIONS, state="readonly",
                                    width=16, bootstyle="info")
            cards_cb.grid(row=row_idx, column=4, padx=2, pady=8)

            # 时间要求
            time_cb = ttk.Combobox(table_container, textvariable=time_var,
                                   values=self.TIME_OPTIONS, state="readonly",
                                   width=16, bootstyle="info")
            time_cb.grid(row=row_idx, column=5, padx=2, pady=8)

            # 后续操作
            after_cb = ttk.Combobox(table_container, textvariable=after_var,
                                    values=self.AFTER_OPTIONS, state="readonly",
                                    width=14, bootstyle="warning")
            after_cb.grid(row=row_idx, column=6, padx=2, pady=8)

            self.row_widgets.append({
                "enabled": enabled_var,
                "scene": scene_var,
                "rings": rings_var,
                "cards": cards_var,
                "time": time_var,
                "after": after_var,
                "handle": drag_handle,  # 保存拖动把手引用
            })

        # 保存统一的表格容器用于拖动检测
        self.table_container = table_container

        # 底部提示区域
        tip_frame = ttk.Frame(main)
        tip_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        tip_frame.columnconfigure(0, weight=1)
        ttk.Label(tip_frame, text="💡 当前仅小西天逻辑已完善，其他场景已预留配置，运行时会提示跳过",
                 foreground="gray", font=("Microsoft YaHei", 9)).grid(row=0, column=0, sticky="w")

        # 按钮区域 - 居中对齐
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=4, column=0, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)

        btn_inner = ttk.Frame(btn_frame)
        btn_inner.grid(row=0, column=0)

        ttk.Button(btn_inner, text="确认", command=self._on_ok, width=15,
                  bootstyle="primary").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(btn_inner, text="取消", command=self._on_cancel, width=15,
                  bootstyle="outline").pack(side=tk.LEFT)

    def _load_cfg(self):
        for i, widgets in enumerate(self.row_widgets):
            if i < len(self.cfg_list):
                cfg = self.cfg_list[i]
                widgets["enabled"].set(cfg.get("enabled", False))
                widgets["scene"].set(cfg.get("scene", "小西天"))
                widgets["rings"].set(cfg.get("rings", "无要求"))
                widgets["cards"].set(cfg.get("cards", "无要求"))
                widgets["time"].set(cfg.get("time", "无要求"))
                widgets["after"].set(cfg.get("after", "后换场景"))
            else:
                # 默认按参考图填充
                defaults = [
                    ("龙窟五层", "得3个环", "得2张卡片"),
                    ("凤巢四层", "得3个环", "无要求"),
                    ("凤巢五层", "得3个环", "得2张卡片"),
                    ("子母河底", "得3个环", "无要求"),
                    ("小西天", "得3个环", "得2张卡片"),
                    ("小雷音寺", "得3个环", "得2张卡片"),
                    ("女娲神迹", "得3个环", "得2张卡片"),
                    ("须弥东界", "得3个环", "得2张卡片"),
                ]
                scene, rings, cards = defaults[i] if i < len(defaults) else ("小西天", "无要求", "无要求")
                widgets["scene"].set(scene)
                widgets["rings"].set(rings)
                widgets["cards"].set(cards)
                widgets["time"].set("满180分钟")
                widgets["after"].set("后换场景")
                widgets["enabled"].set(i in (3, 4, 5))  # 默认选中 4/5/6

    def _on_ok(self):
        self.result = []
        for i, widgets in enumerate(self.row_widgets):
            self.result.append({
                "enabled": widgets["enabled"].get(),
                "scene": widgets["scene"].get(),
                "rings": widgets["rings"].get(),
                "cards": widgets["cards"].get(),
                "time": widgets["time"].get(),
                "after": widgets["after"].get(),
            })
        self.win.destroy()

    def _on_drag_start(self, event, row_idx):
        """开始拖动行"""
        self.drag_row = row_idx
        self.drag_start_y = event.y_root
        # 保存原始数据
        self._original_widgets = {k: v.get() for k, v in self.row_widgets[row_idx].items()
                                 if hasattr(v, 'get')}

    def _on_drag_motion(self, event, row_idx):
        """拖动中 - 检测是否需要交换行"""
        if self.drag_row is None:
            return

        # 计算移动距离
        dy = event.y_root - self.drag_start_y

        # 判断移动方向
        if abs(dy) > 25:  # 移动超过25像素才触发交换
            direction = 1 if dy > 0 else -1
            new_row = self.drag_row + direction

            if 0 <= new_row < len(self.row_widgets):
                self._swap_rows(self.drag_row, new_row)
                self.drag_row = new_row
                self.drag_start_y = event.y_root

    def _on_drag_end(self, event):
        """结束拖动"""
        self.drag_row = None
        self.drag_start_y = 0

    def _swap_rows(self, row1_idx, row2_idx):
        """交换两行的数据"""
        widgets1 = self.row_widgets[row1_idx]
        widgets2 = self.row_widgets[row2_idx]

        # 保存数据
        data1 = {k: v.get() for k, v in widgets1.items() if hasattr(v, 'get') and k != "handle"}
        data2 = {k: v.get() for k, v in widgets2.items() if hasattr(v, 'get') and k != "handle"}

        # 交换数据
        for key in data1:
            if key in data2:
                widgets1[key].set(data2[key])
                widgets2[key].set(data1[key])

    def _on_cancel(self):
        self.result = None
        self.win.destroy()


if __name__ == "__main__":
    # 用 pythonw.exe 启动时没有控制台，sys.stdout/stderr 为 None，
    # 程序内异常分支的 print 会因此崩溃，这里替换为可忽略的哑对象
    if sys.stdout is None:
        import io as _io
        sys.stdout = _io.StringIO()
    if sys.stderr is None:
        import io as _io
        sys.stderr = _io.StringIO()
    app = AutoFightGUI()
    app.run()

