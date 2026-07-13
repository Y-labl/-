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
    "capture_enabled": False,
    "miaoshou_enabled": True,
    "skill_then_auto": False,
    "normal_then_auto": False,
    "defend_then_auto": False,
    "direct_auto": False,
    "escape_enabled": True,
    "auto_path_enabled": True,
    # 妙手空空场景配置（参考图）
    "scene_config": [
        {"enabled": False, "scene": "龙窟五层", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "凤巢四层", "rings": "得3个环", "cards": "无要求", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "子母河底", "rings": "得3个环", "cards": "无要求", "time": "满180分钟", "after": "后换场景"},
        {"enabled": True, "scene": "小西天", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": True, "scene": "小雷音寺", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": True, "scene": "女娲神迹", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
        {"enabled": False, "scene": "须弥东界", "rings": "得3个环", "cards": "得2张卡片", "time": "满180分钟", "after": "后换场景"},
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
        self.engine = None
        self.engine_thread = None
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

        self.capture_enabled = tk.BooleanVar(value=cfg.get("capture_enabled", False))
        self.miaoshou_enabled = tk.BooleanVar(value=cfg.get("miaoshou_enabled", True))
        self.skill_then_auto = tk.BooleanVar(value=cfg.get("skill_then_auto", False))
        self.normal_then_auto = tk.BooleanVar(value=cfg.get("normal_then_auto", False))
        self.defend_then_auto = tk.BooleanVar(value=cfg.get("defend_then_auto", False))
        self.direct_auto = tk.BooleanVar(value=cfg.get("direct_auto", False))
        self.escape_enabled = tk.BooleanVar(value=cfg.get("escape_enabled", True))
        self.auto_path_enabled = tk.BooleanVar(value=cfg.get("auto_path_enabled", True))

    # ---------- UI 构建 ----------
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)
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

        # ---- 设备绑定 ----
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

        ops = [
            ("一、捕捉", self.capture_enabled),
            ("二、妙手空空", self.miaoshou_enabled),
            ("三、1.点选技能后自动战斗", self.skill_then_auto),
            ("2.普通攻击后自动战斗", self.normal_then_auto),
            ("3.防御后自动战斗", self.defend_then_auto),
            ("4.直接自动战斗", self.direct_auto),
            ("5.逃跑", self.escape_enabled),
        ]
        for i, (txt, var) in enumerate(ops):
            ttk.Checkbutton(left, text=txt, variable=var,
                            bootstyle="success-round-toggle").grid(
                row=i, column=0, sticky="w", pady=4)

        right = ttk.Frame(battle_card)
        right.grid(row=0, column=1, sticky="ne")
        ttk.Checkbutton(right, text="自动寻路", variable=self.auto_path_enabled,
                        bootstyle="success-round-toggle").grid(row=0, column=0, sticky="w")

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
        self.bb_display.pack(side=tk.LEFT)

        self.log_text = ttk.ScrolledText(
            log_card, height=10, font=("Consolas", 9),
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

    # ---------- 设备 ----------
    def _refresh_devices(self):
        devices = list_adb_devices()
        self.device_combo["values"] = devices
        if devices:
            if self.cfg.get("serial") in devices:
                self.device_combo.set(self.cfg["serial"])
            else:
                self.device_combo.set(devices[0])
                self.cfg["serial"] = devices[0]
            self.dev_status.configure(text=f"已发现 {len(devices)} 个设备", foreground="green")
        else:
            self.device_combo.set("")
            self.dev_status.configure(text="未发现 ADB 设备", foreground="orange")

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
        self.dev_status.configure(text=f"已绑定: {serial}", foreground="#0d6efd")
        self._log(f"✅ 已绑定设备: {serial}")
        self.btn_start.configure(state=tk.NORMAL)

    # ---------- 引擎控制 ----------
    def start_engine(self):
        serial = self.cfg.get("serial")
        if not serial:
            messagebox.showwarning("提示", "请先绑定设备")
            return
        self._sync_ui_to_cfg()
        save_config(self.cfg)

        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self._draw_status("green")
        self.status_label.configure(text="运行中")

        self.engine = AutoFightEngine(self.cfg, self.log_queue)
        self.engine_thread = threading.Thread(target=self.engine.run_loop, daemon=True)
        self.engine_thread.start()

    def stop_engine(self):
        if self.engine:
            self.engine.running = False
        self._log("⏹ 正在停止...")

    def _on_engine_stopped(self):
        self.btn_start.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)
        self._draw_status("gray")
        self.status_label.configure(text="已停止")
        self.hp_display.configure(text="HP: --%")
        self.mp_display.configure(text="MP: --%")
        self.bb_display.configure(text="BB: --%")

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

        self.capture_enabled.set(cfg.get("capture_enabled", False))
        self.miaoshou_enabled.set(cfg.get("miaoshou_enabled", True))
        self.skill_then_auto.set(cfg.get("skill_then_auto", False))
        self.normal_then_auto.set(cfg.get("normal_then_auto", False))
        self.defend_then_auto.set(cfg.get("defend_then_auto", False))
        self.direct_auto.set(cfg.get("direct_auto", False))
        self.escape_enabled.set(cfg.get("escape_enabled", True))
        self.auto_path_enabled.set(cfg.get("auto_path_enabled", True))

        self.map_select.set(cfg.get("map", "小西天"))
        self.project_select.set("点卡场景(2币/天)")

        if cfg.get("serial"):
            if cfg["serial"] in (self.device_combo["values"] or []):
                self.device_combo.set(cfg["serial"])
            self.dev_status.configure(text=f"设备: {cfg['serial']}", foreground="green")
            self.btn_start.configure(state=tk.NORMAL)

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
        cfg["capture_enabled"] = self.capture_enabled.get()
        cfg["miaoshou_enabled"] = self.miaoshou_enabled.get()
        cfg["skill_then_auto"] = self.skill_then_auto.get()
        cfg["normal_then_auto"] = self.normal_then_auto.get()
        cfg["defend_then_auto"] = self.defend_then_auto.get()
        cfg["direct_auto"] = self.direct_auto.get()
        cfg["escape_enabled"] = self.escape_enabled.get()
        cfg["auto_path_enabled"] = self.auto_path_enabled.get()

    def _on_setting_change(self, event=None):
        pass

    def _save_cfg(self):
        self._sync_ui_to_cfg()
        save_config(self.cfg)
        self._log("✅ 配置已保存")

    def _take_screenshot(self):
        """截取当前设备屏幕并保存到 screenshots 目录"""
        serial = self.cfg.get("serial", "").strip()
        if not serial:
            messagebox.showwarning("提示", "请先绑定设备再截图")
            return
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(save_dir, filename)
        try:
            result = sp.run([ADB_EXE, "-s", serial, "exec-out", "screencap", "-p"],
                           capture_output=True, timeout=10)
            if result.returncode != 0:
                err = result.stderr.decode(errors="replace") if result.stderr else "未知错误"
                self._log(f"❌ 截图失败: {err}")
                messagebox.showerror("截图失败", f"ADB 命令执行失败:\n{err}")
                return
            with open(filepath, "wb") as f:
                f.write(result.stdout)
            self._log(f"📸 截图已保存: {filepath}")
        except Exception as e:
            self._log(f"❌ 截图失败: {e}")
            messagebox.showerror("截图失败", f"截图过程出错:\n{e}")

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
        self.win.geometry("820x560")
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
