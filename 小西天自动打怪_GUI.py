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
import threading
import time
from datetime import datetime

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk

from mhxy_engine import (
    ADB_EXE,
    AutoFightEngine,
    MAP_CONFIG,
    GUI_CONFIG_FILE,
    list_adb_devices,
)


# ============== 扩展默认配置 ==============
DEFAULT_CONFIG = {
    "serial": "",
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
        self.root.geometry("1240x1240")
        self.root.minsize(800, 700)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.cfg = load_config()
        self.log_queue = queue.Queue()
        self.engine = None            # 当前绑定设备（Tab1 显示用）
        self.engine_thread = None
        self.engines = {}             # serial -> AutoFightEngine
        self.engine_threads = {}      # serial -> Thread
        self._device_widgets = {}     # serial -> {status, hp, mp, bb, bc}
        self._threshold_labels = {}

        self._init_vars()
        self._build_ui()
        self._refresh_devices()
        self._load_cfg_to_ui()
        self._poll_log()

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

    # ---------- UI 构建 ----------
    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ===== Tab 1: 场景控制 =====
        main = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(main, text="场景控制")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

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
        self.project_select = ttk.Combobox(scene_card, values=["点卡场景(2币/天)"],
                                           state="readonly", width=22, bootstyle="primary")
        self.project_select.grid(row=0, column=1, sticky="w", padx=(0, 25))
        self.project_select.set("点卡场景(2币/天)")

        ttk.Label(scene_card, text="地图选择：").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.map_select = ttk.Combobox(scene_card, values=list(MAP_CONFIG),
                                       state="readonly", width=18, bootstyle="primary")
        self.map_select.grid(row=0, column=3, sticky="w", padx=(0, 25))
        self.map_select.bind("<<ComboboxSelected>>", lambda e: self._on_setting_change())

        ttk.Button(scene_card, text="妙手空空场景设置", command=self._open_scene_settings,
                   width=18, bootstyle="warning").grid(row=0, column=4, sticky="e")

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
        ttk.Checkbutton(left, text="一、捕捉", variable=self.capture_bb_enabled,
                        bootstyle="success-round-toggle").grid(row=0, column=0, sticky="w", pady=4)
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

        # ---- 日志 & 实时数据 ----
        log_card = ttk.Labelframe(main, text=" 运行日志 & 实时数据 ", padding=10)
        log_card.grid(row=5, column=0, sticky="nsew", pady=(0, 12))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        data_frame = ttk.Frame(log_card)
        data_frame.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.hp_display = ttk.Label(data_frame, text="HP: --%",
                                    font=("Microsoft YaHei", 11, "bold"), foreground="#e83e8c")
        self.hp_display.pack(side=tk.LEFT, padx=(0, 20))
        self.mp_display = ttk.Label(data_frame, text="MP: --%",
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
        self.log_text = ttk.ScrolledText(
            log_card, height=10, font=("Microsoft YaHei", 9),
            bg="#ffffff", fg="#333333", insertbackground="#333333")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        self.log_text.configure(state=tk.DISABLED)

        # ---- 底部 ----
        bottom = ttk.Frame(main)
        bottom.grid(row=7, column=0, sticky="ew")
        ttk.Button(bottom, text="清空日志", command=self._clear_log,
                   bootstyle="outline").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom, text="保存配置", command=self._save_cfg,
                   bootstyle="primary").pack(side=tk.LEFT)

        # ===== Tab 2: 设备管理 =====
        self._build_tab2()

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
        tab2 = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab2, text="设备管理")
        tab2.columnconfigure(0, weight=1)
        tab2.rowconfigure(1, weight=1)

        # 顶部操作栏
        top_frame = ttk.Frame(tab2)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(top_frame, text="刷新设备", command=self._refresh_device_tab,
                   width=10, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(top_frame, text="列出所有 ADB 设备，可独立控制每台设备的启停",
                  foreground="gray", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

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

    def _refresh_device_tab(self):
        """刷新设备管理 Tab"""
        for w in self.dev_list_frame.winfo_children():
            w.destroy()
        self._device_widgets.clear()

        devices = list_adb_devices()
        if not devices:
            ttk.Label(self.dev_list_frame, text="未发现 ADB 设备",
                      foreground="orange", font=("Microsoft YaHei", 10)).pack(pady=20)
            return

        # 表头
        hdr = ttk.Frame(self.dev_list_frame)
        hdr.pack(fill=tk.X, pady=(0, 8))
        for ci in range(8):
            hdr.columnconfigure(ci, weight=1)
        hdr.columnconfigure(8, weight=0)
        for ci, (txt, wd) in enumerate([
            ("设备序列号", 16), ("设备名称", 10),
            ("状态", 6), ("HP", 5), ("MP", 5),
            ("BB", 5), ("战斗", 4), ("时长", 6), ("操作", 0),
        ]):
            ttk.Label(hdr, text=txt, font=("Microsoft YaHei", 9, "bold"),
                      width=wd if wd else None, anchor="w").grid(row=0, column=ci, sticky="ew", padx=2)

        for serial in devices:
            self._add_device_row(serial)

    def _add_device_row(self, serial):
        """在设备管理 Tab 中添加一行"""
        engine = self.engines.get(serial)
        running = engine is not None and engine.running

        row_frame = ttk.Frame(self.dev_list_frame)
        row_frame.pack(fill=tk.X, pady=1)

        ttk.Label(row_frame, text=serial, width=16, anchor="w",
                  font=("Consolas", 9)).grid(row=0, column=0, sticky="ew", padx=2)

        # device_name
        dev_names = self.cfg.get("device_names", {})
        dev_name = dev_names.get(serial, "")
        for ci in range(8):
            row_frame.columnconfigure(ci, weight=1)
        row_frame.columnconfigure(8, weight=0)
        name_lbl = ttk.Label(row_frame, text=dev_name or "点击设置", width=10, anchor="w",
                             foreground="gray" if not dev_name else "",
                             cursor="hand2")
        name_lbl.grid(row=0, column=1, sticky="ew", padx=2)
        name_lbl.bind("<Button-1>", lambda e, s=serial, lbl=name_lbl: self._rename_device(s, lbl))

        status_text = "运行中" if running else "空闲"
        status_color = "green" if running else "gray"
        status_lbl = ttk.Label(row_frame, text=status_text, foreground=status_color,
                               width=6, anchor="w")
        status_lbl.grid(row=0, column=2, sticky="ew", padx=2)

        hp_v, mp_v, bb_v = "--", "--", "--"
        if running:
            hp_v = f"{engine.last_hp:.0f}%"
            mp_v = f"{engine.last_mp:.0f}%"
            bb_v = "--" if engine.has_no_bb else f"{engine.last_bb:.0f}%"

        hp_lbl = ttk.Label(row_frame, text=hp_v, width=5, anchor="w")
        hp_lbl.grid(row=0, column=3, sticky="ew", padx=2)
        mp_lbl = ttk.Label(row_frame, text=mp_v, width=5, anchor="w")
        mp_lbl.grid(row=0, column=4, sticky="ew", padx=2)
        bb_lbl = ttk.Label(row_frame, text=bb_v, width=5, anchor="w")
        bb_lbl.grid(row=0, column=5, sticky="ew", padx=2)

        bc_v = f"{engine.battle_count}" if running else "--"
        bc_lbl = ttk.Label(row_frame, text=bc_v, width=4, anchor="w")
        bc_lbl.grid(row=0, column=6, sticky="ew", padx=2)

        # 当前场景时长
        if running and getattr(engine, "start_time", 0):
            elapsed = int(time.time() - engine.start_time)
            duration = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        else:
            duration = "--"
        dur_lbl = ttk.Label(row_frame, text=duration, width=6, anchor="w")
        dur_lbl.grid(row=0, column=7, sticky="ew", padx=2)

        btn_frame = ttk.Frame(row_frame)
        btn_frame.grid(row=0, column=8, padx=2)
        start_btn2 = ttk.Button(btn_frame, text="▶", width=2, bootstyle="success",
                               command=lambda s=serial: self._start_device(s))
        start_btn2.pack(side=tk.LEFT, padx=1)
        stop_btn2 = ttk.Button(btn_frame, text="⏹", width=2, bootstyle="danger",
                               command=lambda s=serial: self._stop_device(s))
        stop_btn2.pack(side=tk.LEFT, padx=1)

        if running:
            start_btn2.configure(state=tk.DISABLED)
            stop_btn2.configure(state=tk.NORMAL)
        else:
            start_btn2.configure(state=tk.NORMAL)
            stop_btn2.configure(state=tk.DISABLED)

        ttk.Button(btn_frame, text="📸", width=2, bootstyle="outline",
                   command=lambda s=serial: self._device_screenshot(s)).pack(
            side=tk.LEFT, padx=1)

        self._device_widgets[serial] = {
            "status": status_lbl, "hp": hp_lbl, "mp": mp_lbl,
            "bb": bb_lbl, "bc": bc_lbl, "dur": dur_lbl,
        }

    def _start_device(self, serial):
        """启动指定设备的引擎"""
        if serial in self.engines and self.engines[serial].running:
            self._log(f"[{serial}] 已在运行中")
            return
        self._draw_status("green")
        self.status_label.configure(text="运行中")
        self._update_tab1_buttons()
        self._refresh_devices()
        self._refresh_device_tab()

        cfg = dict(self.cfg)
        cfg["serial"] = serial
        engine = AutoFightEngine(cfg, self.log_queue)
        engine.coord_enabled = self.coord_enabled.get()
        self.engines[serial] = engine
        if serial == self.cfg.get("serial"):
            self.engine = engine
        t = threading.Thread(target=engine.run_loop, daemon=True)
        self.engine_threads[serial] = t
        t.start()
        # 引擎启动后延迟更新按钮状态
        self.root.after(500, self._update_tab1_buttons)
        self._log(f"[{serial}] ▶ 引擎启动")

    def _stop_device(self, serial):
        """停止指定设备的引擎"""
        engine = self.engines.get(serial)
        if engine:
            engine.running = False
        self._log(f"[{serial}] ⏹ 正在停止...")

    def _device_screenshot(self, serial):
        """为指定设备截图（始终使用ADB实时截图）"""
        import cv2
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"device_{serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
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
                _small = _cv2.resize(_raw, (800, 480))
                _cv2.imwrite(filepath, _small)
                self._log(f"[{serial}] 📸 ADB截图已保存: {filepath} (800x480)")
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

    # ---------- 设备 ----------
    def _refresh_devices(self):
        """刷新设备下拉列表"""
        devices = list_adb_devices()
        self.device_combo["values"] = devices
        if devices:
            if self.cfg.get("serial") in devices:
                self.device_combo.set(self.cfg["serial"])
            else:
                self.device_combo.set(devices[0])
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
            self.cfg["serial"] = sel
            self.dev_status.configure(text=f"设备: {sel}", foreground="green")
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
        self.cfg["serial"] = serial
        save_config(self.cfg)
        self.dev_status.configure(text=f"设备: {serial}", foreground="#0d6efd")
        self._log(f"✅ 已绑定设备: {serial}")
        self._update_tab1_buttons()

    # ---------- 引擎控制 ----------
    def _on_engine_stopped(self):
        self._draw_status("gray")
        self.status_label.configure(text="已停止")
        self.root.after(100, self._update_tab1_buttons)
        self.root.after(150, self._refresh_devices)
        self.root.after(200, self._refresh_device_tab)
        self.hp_display.configure(text="HP: --%")
        self.mp_display.configure(text="MP: --%")
        self.bb_display.configure(text="BB: --%")
        self.coord_display.configure(text="--")
        self.battle_display.configure(text="⚔ -- 场")
        self.time_display.configure(text="⏱ 00:00")
        self.coord_display.configure(text="📍 --")

    # ---------- 日志 ----------
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
                    self.hp_display.configure(text=f"HP: {hp:.0f}%")
                    self.mp_display.configure(text=f"MP: {mp:.0f}%")
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
                        elapsed = int(time.time() - self.engine.start_time)
                        m, s = divmod(elapsed, 60)
                        self.time_display.configure(text=f"⏱ {m:02d}:{s:02d}")
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

        self.map_select.set(cfg.get("map", "小西天"))
        self.project_select.set("点卡场景(2币/天)")

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

    def _on_setting_change(self, event=None):
        pass

    def _save_cfg(self):
        self._sync_ui_to_cfg()
        save_config(self.cfg)
        self._log("✅ 配置已保存")


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

    def _apply_scene_settings(self, scene_config):
        self.cfg["scene_config"] = scene_config

    def on_close(self):
        running_count = sum(1 for e in self.engines.values() if e.running)
        if running_count > 0:
            if messagebox.askyesno("确认", f"有 {running_count} 个引擎正在运行，确定要退出吗？"):
                for e in self.engines.values():
                    e.running = False
                for t in self.engine_threads.values():
                    t.join(timeout=3)
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()



class SceneSettingsDialog:
    """场景之妙手空空 - 多场景配置弹窗"""

    SCENE_NAMES = ["龙窟五层", "凤巢四层", "子母河底", "小西天", "小雷音寺", "女娲神迹", "须弥东界"]
    RING_OPTIONS = ["无要求", "得1个环", "得2个环", "得3个环"]
    CARD_OPTIONS = ["无要求", "得1张卡片", "得2张卡片"]
    TIME_OPTIONS = ["无要求", "满60分钟", "满120分钟", "满180分钟"]
    AFTER_OPTIONS = ["后换场景", "停止"]

    def __init__(self, parent, cfg_list):
        self.cfg_list = cfg_list or []
        self.result = None
        self.row_widgets = []

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
        main = ttk.Frame(self.win, padding=15)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)

        ttk.Label(main, text="场景之妙手空空", font=("Microsoft YaHei", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(main, text="不支持自动换场景到：丝绸之路、无名鬼域", foreground="gray").grid(
            row=1, column=0, sticky="w", pady=(0, 10))

        # 表头
        header = ttk.Frame(main)
        header.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)
        header.columnconfigure(3, weight=1)
        header.columnconfigure(4, weight=1)
        header.columnconfigure(5, weight=1)

        ttk.Label(header, text="启用", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=0, padx=(0, 10))
        ttk.Label(header, text="场景", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=1)
        ttk.Label(header, text="环数要求", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=2)
        ttk.Label(header, text="卡片要求", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=3)
        ttk.Label(header, text="时间要求", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=4)
        ttk.Label(header, text="后续操作", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=5)

        # 场景行容器
        rows_frame = ttk.Frame(main)
        rows_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 12))
        rows_frame.columnconfigure(1, weight=1)
        rows_frame.columnconfigure(2, weight=1)
        rows_frame.columnconfigure(3, weight=1)
        rows_frame.columnconfigure(4, weight=1)
        rows_frame.columnconfigure(5, weight=1)

        for i in range(8):
            row = ttk.Frame(rows_frame)
            row.grid(row=i, column=0, sticky="ew", pady=3)
            row.columnconfigure(1, weight=1)
            row.columnconfigure(2, weight=1)
            row.columnconfigure(3, weight=1)
            row.columnconfigure(4, weight=1)
            row.columnconfigure(5, weight=1)

            enabled_var = tk.BooleanVar(value=False)
            scene_var = tk.StringVar(value="小西天")
            rings_var = tk.StringVar(value="无要求")
            cards_var = tk.StringVar(value="无要求")
            time_var = tk.StringVar(value="无要求")
            after_var = tk.StringVar(value="后换场景")

            cb = ttk.Checkbutton(row, text=f"场景{i+1}", variable=enabled_var, bootstyle="success-round-toggle")
            cb.grid(row=0, column=0, sticky="w", padx=(0, 10))

            scene_cb = ttk.Combobox(row, textvariable=scene_var, values=self.SCENE_NAMES,
                                    state="readonly", width=12, bootstyle="primary")
            scene_cb.grid(row=0, column=1, padx=(0, 10))

            rings_cb = ttk.Combobox(row, textvariable=rings_var, values=self.RING_OPTIONS,
                                    state="readonly", width=10, bootstyle="info")
            rings_cb.grid(row=0, column=2, padx=(0, 10))

            cards_cb = ttk.Combobox(row, textvariable=cards_var, values=self.CARD_OPTIONS,
                                    state="readonly", width=10, bootstyle="info")
            cards_cb.grid(row=0, column=3, padx=(0, 10))

            time_cb = ttk.Combobox(row, textvariable=time_var, values=self.TIME_OPTIONS,
                                   state="readonly", width=10, bootstyle="info")
            time_cb.grid(row=0, column=4, padx=(0, 10))

            after_cb = ttk.Combobox(row, textvariable=after_var, values=self.AFTER_OPTIONS,
                                    state="readonly", width=10, bootstyle="warning")
            after_cb.grid(row=0, column=5, padx=(0, 10))

            self.row_widgets.append({
                "enabled": enabled_var,
                "scene": scene_var,
                "rings": rings_var,
                "cards": cards_var,
                "time": time_var,
                "after": after_var,
            })

        # 底部提示 + 按钮
        ttk.Label(main, text="💡 当前仅小西天逻辑已完善，其他场景已预留配置，运行时会提示跳过", foreground="gray").grid(
            row=4, column=0, sticky="w", pady=(0, 10))

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, column=0, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        ttk.Button(btn_frame, text="确认", command=self._on_ok, width=20, bootstyle="primary").grid(
            row=0, column=0, sticky="e", padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self._on_cancel, width=20, bootstyle="outline").grid(
            row=0, column=1, sticky="w", padx=(10, 0))

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
                    ("子母河底", "得3个环", "无要求"),
                    ("小西天", "得3个环", "得2张卡片"),
                    ("小雷音寺", "得3个环", "得2张卡片"),
                    ("女娲神迹", "得3个环", "得2张卡片"),
                    ("须弥东界", "得3个环", "得2张卡片"),
                    ("小西天", "得3个环", "得2张卡片"),
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
        for widgets in self.row_widgets:
            self.result.append({
                "enabled": widgets["enabled"].get(),
                "scene": widgets["scene"].get(),
                "rings": widgets["rings"].get(),
                "cards": widgets["cards"].get(),
                "time": widgets["time"].get(),
                "after": widgets["after"].get(),
            })
        self.win.destroy()

    def _on_cancel(self):
        self.result = None
        self.win.destroy()


if __name__ == "__main__":
    app = AutoFightGUI()
    app.run()

