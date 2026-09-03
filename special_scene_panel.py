# -*- coding: utf-8 -*-
"""特殊场景（队伍抓特殊）独立面板。

与偷偷场景（设备管理）项目相互独立：战斗/时长/环卡等数据不共享。
顶部选择一个全局场景；设备按 5 台一组分成「队伍一/队伍二…」Tab。
角色可选 队长(抓) / 队员(攻击) / 队员(防御)。
"""
import json
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from mhxy_engine import USER_DATA_DIR, list_adb_devices, short_dev_label
from target_mapping import SCENE_ALIASES

TEAM_CONFIG_FILE = os.path.join(USER_DATA_DIR, "special_team_config.json")
SPECIAL_SCENES = ["须弥东界", "银华镜", "弥勒山", "丝绸之路", "伊阙龙门", "无名鬼域", "青丘"]
TEAM_SIZE = 5
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def _norm_scene(scene):
    """把面板写法的场景名（如 银华镜）正常化为引擎/OCR 使用的规范名（银华境）。"""
    return SCENE_ALIASES.get(scene, scene)


def fmt_duration_hm(seconds):
    """把秒数格式化为"小时+分钟"显示：满1小时显示 X小时YY分，不足1小时显示 Y分钟"""
    total_minutes = int(seconds or 0) // 60
    h, m = divmod(total_minutes, 60)
    if h > 0:
        return "{}小时{:02d}分".format(h, m)
    return "{}分钟".format(m)


def _role_text_to_role(txt):
    txt = txt or ""
    if txt.startswith("队长"):
        return "captain"
    if "攻击" in txt and "捕捉" in txt:
        return "attack_capture"
    if "攻击" in txt:
        return "attack"
    return "defend"


def _role_to_text(role):
    return {"captain": "队长(猎术号-抓)", "attack": "队员(攻击)",
            "attack_capture": "队员(攻击+捕捉)",
            "defend": "队员(防御)"}.get(role, "队员(防御)")


class SpecialScenePanel:
    """特殊场景 Tab：设备按 5 台分队伍 + 全局场景 + 一键启动/停止队伍。"""

    def __init__(self, gui):
        self.gui = gui
        self._scene_var = tk.StringVar(value=SPECIAL_SCENES[0] if SPECIAL_SCENES else "")
        self._roles = {}          # serial -> "captain"/"attack"/"defend"
        self._device_order = []
        self._team_of = {}        # serial -> team_idx（手动移动后保留）
        self._teams = []          # list of {frame, table, sel_vars, row_widgets, summary}
        self._cur_team = 0
        self._team_log_queue = queue.Queue()   # 特殊场景队伍引擎日志队列（与偷偷场景主队列隔离）
        self.build_tab()

    # ------------------------------------------------------------------
    def build_tab(self):
        gui = self.gui
        tab = ttk.Frame(gui.notebook, padding=15)
        gui.notebook.add(tab, text="特殊场景")
        self.frame = tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)     # 队伍表格区吃掉所有多余高度
        tab.rowconfigure(2, weight=0)     # 日志区固定高度，不再挤占表格

        # ---- 顶部操作栏：刷新/全选/全不选 + 场景下拉 + 保存/启动/停止 ----
        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(top, text="刷新设备", command=self.refresh_devices,
                   width=10, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(top, text="全选", command=lambda: self.set_all(True),
                   width=6, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="全不选", command=lambda: self.set_all(False),
                   width=7, bootstyle="outline").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(top, text="场景:", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        ttk.Combobox(top, textvariable=self._scene_var, values=SPECIAL_SCENES,
                     state="readonly", width=10, bootstyle="info").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(top, text="每队≤{}台".format(TEAM_SIZE), foreground="gray",
                  font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT)
        ttk.Button(right, text="保存队伍", command=self.save_cfg,
                   width=10, bootstyle="info").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(right, text="▶ 一键启动队伍", command=self.start_team,
                   width=14, bootstyle="success").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(right, text="⏹ 停止队伍", command=self.stop_team,
                   width=12, bootstyle="danger").pack(side=tk.LEFT)

        # ---- 队伍 Tab（队伍一/队伍二…） ----
        self._team_notebook = ttk.Notebook(tab)
        self._team_notebook.grid(row=1, column=0, sticky="nsew")
        self._team_notebook.bind("<<NotebookTabChanged>>",
                                 lambda e: self._on_tab_changed())

        # ---- 队伍日志 ----
        log_card = ttk.Labelframe(tab, text=" 队伍日志 ", padding=8)
        log_card.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        # 总计固定在日志上方（不随日志滚动；跟随当前选中队伍，切 Tab 时刷新）
        self._log_total_lbl = ttk.Label(log_card, text="本队已抓特殊: 0 只",
                                        font=("Microsoft YaHei", 9, "bold"),
                                        foreground="#198754")
        self._log_total_lbl.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._team_log_text = ttk.ScrolledText(log_card, height=9,
                                               font=("Microsoft YaHei", 9), state=tk.DISABLED)
        self._team_log_text.grid(row=1, column=0, sticky="nsew")

        # 先恢复已保存的队伍配置（device_order / team_of / roles），再刷新设备，
        # 这样 refresh_devices 会保留已保存的队伍归属，只补充当前在线新设备。
        self.load_cfg()
        self.refresh_devices()
        gui.root.after(1500, self.poll_status)

    def _on_tab_changed(self):
        try:
            self._cur_team = self._team_notebook.index("current")
        except Exception:
            self._cur_team = 0
        # 切队伍 Tab 时同步日志上方固定的总计
        try:
            self.refresh_stats()
        except Exception:
            pass

    def _sync_cur_team(self):
        """同步 _cur_team 为当前实际选中的 Tab。
        Tk 的 <<NotebookTabChanged>> 虚拟事件触发时机不可靠，切 Tab 后 _cur_team
        可能滞后（导致启动/保存/停止操作到错误的队伍），这里强制读取当前索引。"""
        try:
            self._cur_team = self._team_notebook.index("current")
        except Exception:
            pass

    # ------------------------------------------------------------------
    def refresh_devices(self):
        devices = list_adb_devices()
        if not devices:
            ttk.Label(self._team_notebook, text="未发现 ADB 设备",
                      foreground="orange", font=("Microsoft YaHei", 10)).pack(pady=20)
            return
        ordered = [s for s in self._device_order if s in devices]
        for s in devices:
            if s not in ordered:
                ordered.append(s)
        self._device_order = ordered
        self._assign_teams()
        self._rebuild_teams()

    def _assign_teams(self):
        """分配/保留设备所属队伍：保留手动移动结果，其余按 5 台填进 4 个队伍。"""
        device_set = set(self._device_order)
        assigns = {s: tid for s, tid in self._team_of.items() if s in device_set}
        unmapped = [s for s in self._device_order if s not in assigns]
        counts = {}
        for tid in assigns.values():
            counts[tid] = counts.get(tid, 0) + 1
        cur = 0
        for s in unmapped:
            while cur < 4 and counts.get(cur, 0) >= TEAM_SIZE:
                cur += 1
            if cur >= 4:
                cur = 3   # 超员时归最后一队
            assigns[s] = cur
            counts[cur] = counts.get(cur, 0) + 1
        self._team_of = assigns

    def _rebuild_teams(self):
        for c in self._team_notebook.winfo_children():
            c.destroy()
        self._teams = []
        # 固定显示 队伍一~队伍四
        for tid in range(4):
            serials = [s for s in self._device_order if self._team_of.get(s) == tid]
            self._make_team_tab(tid, serials)
        if self._team_notebook.tabs():
            self._cur_team = min(self._cur_team, 3)
            self._team_notebook.select(self._cur_team)

    def move_device(self, serial):
        """弹出选择目标队伍，把设备移动到所选队伍。"""
        target = self._ask_team()
        if target is None:
            return
        self._team_of[serial] = target
        self.team_log("[{}] 移动到 队伍{}".format(short_dev_label(serial),
                       CN_NUM[target] if target < len(CN_NUM) else target + 1))
        self._rebuild_teams()

    def _ask_team(self):
        """模态弹窗：选择目标队伍（队伍一~四），返回队伍号或 None。"""
        labels = ["队伍{}".format(CN_NUM[i] if i < len(CN_NUM) else i + 1) for i in range(4)]
        result = {"team": None}
        dlg = tk.Toplevel(self.gui.root)
        dlg.title("移动到队伍")
        dlg.transient(self.gui.root)
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        var = tk.StringVar(value=labels[0])
        tk.Label(dlg, text="选择目标队伍:", font=("Microsoft YaHei", 10)).pack(
            padx=20, pady=(14, 4))
        ttk.Combobox(dlg, textvariable=var, values=labels, state="readonly",
                     width=10, bootstyle="info").pack(padx=20, pady=4)

        def on_ok():
            result["team"] = labels.index(var.get())
            dlg.destroy()

        btns = ttk.Frame(dlg)
        btns.pack(pady=12)
        ttk.Button(btns, text="确定", command=on_ok, bootstyle="success").pack(
            side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="取消", command=dlg.destroy, bootstyle="outline").pack(
            side=tk.LEFT)
        dlg.update_idletasks()
        px = (self.gui.root.winfo_screenwidth() - dlg.winfo_reqwidth()) // 2
        py = (self.gui.root.winfo_screenheight() - dlg.winfo_reqheight()) // 2
        dlg.geometry("+{}+{}".format(px, py))
        dlg.grab_set()
        dlg.wait_window()
        return result["team"]

    def _drag_start(self, serial, y_root):
        self._drag_serial = serial
        self._drag_y0 = y_root

    def _drag_end(self, team, serial, y_root):
        if getattr(self, "_drag_serial", None) != serial:
            return
        self._drag_serial = None
        # 移动距离很小视为点击，不重排
        if abs(y_root - getattr(self, "_drag_y0", y_root)) < 4:
            return
        rows = []
        for s, w in team["row_widgets"].items():
            try:
                rows.append((w["status_lbl"].winfo_rooty(), s))
            except Exception:
                pass
        rows.sort(key=lambda x: x[0])
        target = sum(1 for y, _ in rows if y < y_root)
        self._reorder_in_team(team, serial, target)

    def _reorder_in_team(self, team, serial, target):
        """在队伍内拖拽重排：只调整该队伍设备的显示/设备顺序。"""
        tid = self._team_of.get(serial)
        team_serials = [s for s in self._device_order if self._team_of.get(s) == tid]
        if serial not in team_serials:
            return
        cur = team_serials.index(serial)
        target = max(0, min(target, len(team_serials) - 1))
        if target == cur:
            return
        team_serials.pop(cur)
        team_serials.insert(target, serial)
        it = iter(team_serials)
        new_order = []
        for s in self._device_order:
            if self._team_of.get(s) == tid:
                new_order.append(next(it))
            else:
                new_order.append(s)
        self._device_order = new_order
        self._rebuild_teams()

    def _make_team_tab(self, idx, serials):
        frame = ttk.Frame(self._team_notebook)
        self._team_notebook.add(
            frame, text="队伍{}".format(CN_NUM[idx] if idx < len(CN_NUM) else idx + 1))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cell_bg = self.gui.root.style.lookup("TFrame", "background")

        # 表格放进 Canvas：窗口拉宽时列跟随拉伸，设备多时纵向滚动
        canvas = tk.Canvas(frame, highlightthickness=0, bg=cell_bg)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table = tk.Frame(canvas, bg=cell_bg)
        _tbl_id = canvas.create_window((0, 0), window=table, anchor="nw")
        table.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # 窗口变宽时让内部表格同宽（列才有拉伸空间）
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(_tbl_id, width=e.width))
        # 鼠标滚轮滚动表格（Windows：MouseWheel）。不用 bind_all，避免干扰其他面板
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self._wheel_canvas = canvas
        self._wheel_handler = _on_wheel
        self._bind_wheel(canvas)
        self._bind_wheel(table)

        # 列权重：文本列跟随窗口拉伸，开关/按钮列固定
        _col_weights = [0, 2, 2, 2, 1, 1, 1, 0, 0]
        for _ci, _w in enumerate(_col_weights):
            if _w:
                table.columnconfigure(_ci, weight=_w, uniform="teamcol")
            else:
                table.columnconfigure(_ci, weight=0)

        heads = [("入队", 0), ("设备名称", 10), ("设备序列号", 18),
                 ("角色", 16), ("状态", 6), ("战斗", 4), ("时长", 6), ("操作", 8)]
        for ci, (txt, wd) in enumerate(heads):
            tk.Label(table, text=txt, font=("Microsoft YaHei", 9, "bold"),
                     width=wd if wd else None, anchor="center", bg=cell_bg,
                     bd=0, padx=4, pady=6).grid(row=0, column=ci, sticky="ew")

        summary = ttk.Label(frame, text="本队 0 台 | 队长: 无",
                            font=("Microsoft YaHei", 9, "bold"), foreground="#0d6efd")
        summary.grid(row=1, column=0, sticky="w", pady=(2, 4))
        total_lbl = ttk.Label(frame, text="本队已抓特殊: 0 只",
                              font=("Microsoft YaHei", 9, "bold"), foreground="#198754")
        total_lbl.grid(row=2, column=0, sticky="w", pady=(2, 4))
        team = {"idx": idx, "frame": frame, "table": table, "canvas": canvas,
                "sel_vars": {}, "row_widgets": {}, "summary": summary, "total": total_lbl}
        for ri, serial in enumerate(serials, 1):
            self._add_row(table, ri, serial, team)
        self._teams.append(team)

    def _bind_wheel(self, widget):
        """给控件绑定表格滚轮事件（多行设备时滚动查看）"""
        widget.bind("<MouseWheel>", lambda e: self._wheel_handler(e))

    def _add_row(self, table, row_idx, serial, team):
        cell_bg = self.gui.root.style.lookup("TFrame", "background")
        var = tk.BooleanVar(value=True)
        team["sel_vars"][serial] = var
        var.trace_add("write", lambda *a: self.refresh_team_summaries())
        ttk.Checkbutton(table, variable=var, bootstyle="success-round-toggle").grid(
            row=row_idx, column=0, pady=4)

        dev_names = self.gui.cfg.get("device_names", {})
        # 未设置自定义名称的新设备显示完整序列号，避免只看到缩写（如 JUBNU(912)）
        dev_name = dev_names.get(serial) or serial
        name_lbl = tk.Label(table, text=dev_name, font=("Microsoft YaHei", 9), bg=cell_bg,
                            bd=0, padx=4, pady=6, width=10, anchor="w")
        name_lbl.grid(row=row_idx, column=1, sticky="ew")
        ser_lbl = tk.Label(table, text=serial, font=("Consolas", 9),
                           bg=cell_bg, bd=0, padx=4, pady=6, width=18, anchor="w")
        ser_lbl.grid(row=row_idx, column=2, sticky="ew")
        for w in (name_lbl, ser_lbl):
            w.bind("<Button-1>", lambda e, s=serial: self._drag_start(s, e.y_root))
            w.bind("<ButtonRelease-1>",
                   lambda e, s=serial: self._drag_end(team, s, e.y_root))

        role = self._roles.get(serial, "defend")
        role_cb = ttk.Combobox(table, values=["队长(猎术号-抓)", "队员(攻击+捕捉)", "队员(攻击)", "队员(防御)"],
                               state="readonly", width=16, bootstyle="primary")
        role_cb.set(_role_to_text(role))
        role_cb.grid(row=row_idx, column=3, sticky="w", padx=8, pady=4)
        role_cb.bind("<<ComboboxSelected>>",
                     lambda e, s=serial, cb=role_cb: self._set_role(s, team, cb))

        status_lbl = ttk.Label(table, text="停止", foreground="gray",
                               font=("Microsoft YaHei", 9), anchor="center")
        status_lbl.grid(row=row_idx, column=4, pady=6)
        bc, dur = self.bc_dur(serial)
        bc_lbl = ttk.Label(table, text=bc, font=("Consolas", 9), anchor="center")
        bc_lbl.grid(row=row_idx, column=5, pady=6)
        dur_lbl = ttk.Label(table, text=dur, font=("Consolas", 9), anchor="center")
        dur_lbl.grid(row=row_idx, column=6, pady=6)
        ttk.Button(table, text="移动", width=5, bootstyle="outline",
                   command=lambda s=serial: self.move_device(s)).grid(
            row=row_idx, column=7, padx=6, pady=4)
        ttk.Button(table, text="📸", width=4, bootstyle="secondary",
                   command=lambda s=serial: self.capture_device(s)).grid(
            row=row_idx, column=8, padx=4, pady=4)

        # 行内所有控件都响应滚轮（鼠标在行上也能滚动表格）
        for _w in table.grid_slaves(row=row_idx):
            self._bind_wheel(_w)

        team["row_widgets"][serial] = {"role_cb": role_cb, "status_lbl": status_lbl,
                                       "bc_lbl": bc_lbl, "dur_lbl": dur_lbl}

    def _set_role(self, serial, team, role_cb):
        """设置设备角色。同一队伍里队长只能有一个：
        若把某设备设为队长，而本队伍已有其它队长，则拒绝并回退，避免多队长。"""
        new_role = _role_text_to_role(role_cb.get())
        # 该队伍所有在列设备
        team_serials = set(team["sel_vars"].keys())
        # 若设为队长，检查同队伍已有其它队长
        if new_role == "captain":
            others_captain = [
                s for s in team_serials
                if s != serial and self._roles.get(s) == "captain"
            ]
            if others_captain:
                messagebox.showwarning(
                    "提示",
                    "本队伍已有队长：{}\n一个队伍只能有一个队长。".format(
                        short_dev_label(others_captain[0])))
                # 回退为原角色（保持当前 _roles 不变），并刷新下拉显示
                cur_role = self._roles.get(serial, "defend")
                role_cb.set(_role_to_text(cur_role))
                return
        # 正常更新角色
        self._roles[serial] = new_role
        self.refresh_team_summaries()

    def bc_dur(self, serial):
        """返回 (战斗场次, 时长文本)：只读特殊场景队伍引擎数据，与偷偷场景不共享。"""
        eng = self.gui.engines.get(serial)
        if eng is None or not getattr(eng, "_team_mode", False):
            return "0", "--"
        bc = getattr(eng, "battle_count", 0) or 0
        total_runtime = getattr(eng, "total_runtime", 0) or 0
        if getattr(eng, "running", False) and getattr(eng, "start_time", 0):
            elapsed = int(total_runtime + (time.time() - eng.start_time))
            dur = fmt_duration_hm(elapsed)
        elif total_runtime > 0:
            dur = fmt_duration_hm(total_runtime)
        else:
            dur = "--"
        return str(bc), dur

    def refresh_stats(self):
        for team in self._teams:
            total = 0
            for serial, w in team["row_widgets"].items():
                bc, dur = self.bc_dur(serial)
                w["bc_lbl"].configure(text=bc)
                w["dur_lbl"].configure(text=dur)
                eng = self.gui.engines.get(serial)
                if eng and getattr(eng, "_team_mode", False):
                    total += getattr(eng, "capture_count", 0) or 0
            team["total"].configure(text="本队已抓特殊: {} 只".format(total))
        # 日志上方固定总计：跟随当前选中队伍
        if self._teams:
            _cur = min(self._cur_team, len(self._teams) - 1)
            _t = 0
            for serial in self._teams[_cur]["row_widgets"]:
                eng = self.gui.engines.get(serial)
                if eng and getattr(eng, "_team_mode", False):
                    _t += getattr(eng, "capture_count", 0) or 0
            self._log_total_lbl.configure(text="本队已抓特殊: {} 只".format(_t))

    # ------------------------------------------------------------------
    def set_all(self, checked):
        team = self._teams[self._cur_team] if self._teams else None
        if team:
            for var in team["sel_vars"].values():
                var.set(checked)
        self.refresh_team_summaries()

    def collect_members(self, team_idx=None):
        """读取指定队伍（默认当前队伍）成员：[{serial, scene, role}]"""
        if team_idx is None:
            team_idx = self._cur_team
        if team_idx >= len(self._teams):
            return []
        team = self._teams[team_idx]
        members = []
        for serial in self._device_order:
            var = team["sel_vars"].get(serial)
            if var is None or not var.get():
                continue
            w = team["row_widgets"].get(serial)
            if w is None:
                continue
            members.append({
                "serial": serial,
                "scene": self._scene_var.get(),
                "role": _role_text_to_role(w["role_cb"].get()),
            })
        return members

    def refresh_team_summaries(self):
        for team in self._teams:
            members = []
            for serial in self._device_order:
                var = team["sel_vars"].get(serial)
                if var is not None and var.get():
                    w = team["row_widgets"].get(serial)
                    if w is not None:
                        members.append(serial)
            captain = next((s for s in members
                            if self._roles.get(s) == "captain"
                            and team["row_widgets"].get(s, {}).get("role_cb") is not None
                            and team["row_widgets"][s]["role_cb"].get().startswith("队长")), None)
            team["summary"].configure(
                text="本队 {} 台 | 队长: {}".format(
                    len(members), short_dev_label(captain) if captain else "无"))

    def start_team(self):
        # 同步当前选中的 Tab，保证启动的就是当前页队伍
        self._sync_cur_team()
        members = self.collect_members()
        if not members:
            messagebox.showwarning("提示", "请至少勾选一台设备加入队伍")
            return
        if not any(m["role"] == "captain" for m in members):
            messagebox.showwarning("提示", "请将一台设备设置为队长（猎术号）")
            return
        self.stop_team()
        scene = self._scene_var.get()
        # 队长先启动，其它队员按攻击/防御
        ordered = sorted(members, key=lambda m: 0 if m["role"] == "captain" else 1)
        for m in ordered:
            override = self._role_override(m["role"], scene)
            self.team_log("[{}] {} scene={} role={}".format(
                short_dev_label(m["serial"]), _role_to_text(m["role"]),
                m["scene"], m["role"]))
            self.gui._start_device(m["serial"], override=override, team_mode=True,
                                   log_queue=self._team_log_queue)
        # 启动队伍引擎日志消费线程（把引擎运行日志打印到队伍日志框）
        if not getattr(self, "_team_log_polling", False):
            self._team_log_polling = True
            threading.Thread(target=self._poll_team_log, daemon=True).start()
        self.save_cfg()
        self.team_log("▶ 队伍{} 启动完成（{} 台）".format(
            CN_NUM[self._cur_team] if self._cur_team < len(CN_NUM) else self._cur_team + 1,
            len(ordered)))

    @staticmethod
    def _role_override(role, scene):
        # 特殊场景按单场景跑：覆盖 scene_config 只保留当前场景，避免设备去轮转偷偷场景。
        scene = _norm_scene(scene)
        o = {
            "map": scene,
            "coord_enabled": True,
            # 特殊场景不检查背包（环/卡计数只属于偷偷场景逻辑）
            "check_pkg_counts": False,
            "auto_path_enabled": False,
            "scene_config": [
                {"enabled": True, "scene": scene, "rings": "无要求", "cards": "无要求",
                 "time": "无要求", "after": "后换场景"},
            ],
        }
        if role == "captain":
            # 特殊场景是「抓特殊怪」，不走妙手空空偷卡。
            # 逻辑：有 特殊/变异/宝宝 → 先捕捉；没有 → 普通攻击后挂自动击杀。
            # 关闭 escape_enabled，否则 _post_steal_action 第一层就逃跑，不会击杀。
            # 只有队长跑图（巡逻遇怪）；队员不跑图。
            o.update({"auto_path_enabled": True})
            # 没有特殊/宝宝时：第1回合点法术(710,100) → 点怪物 → 同回合点自动
            # （2026-08-27 用户要求参考偷偷场景击杀流程；原"第2回合再挂自动"已改同回合）
            # 战斗结束取消自动+酒肆恢复血蓝（取消自动与血蓝恢复在 post_combat 通用逻辑，对所有战斗生效）。
            o.update({"capture_bb_enabled": True, "miaoshou_enabled": False,
                      "skill_x": 710, "skill_y": 100,
                      "auto_next_round": True,
                      "skill_then_auto": True, "normal_then_auto": False,
                      "defend_then_auto": False,
                      "escape_enabled": False, "use_real_scene_switch": True})
        elif role == "attack":
            o.update({"capture_bb_enabled": False, "miaoshou_enabled": False,
                      "defend_then_auto": False, "normal_then_auto": True,
                      "auto_next_round": True,
                      "escape_enabled": False, "use_real_scene_switch": False})
        elif role == "attack_capture":
            # 队员也参与捕捉：有 特殊/变异/宝宝 → 捕捉；没有 → 第1回合点法术，第2回合挂自动。
            o.update({"capture_bb_enabled": True, "miaoshou_enabled": False,
                      "defend_then_auto": False, "normal_then_auto": True,
                      "auto_next_round": True,
                      "escape_enabled": False, "use_real_scene_switch": False})
        else:  # defend
            o.update({"capture_bb_enabled": False, "miaoshou_enabled": False,
                      "defend_then_auto": True, "normal_then_auto": False,
                      "auto_next_round": True,
                      "escape_enabled": False, "use_real_scene_switch": False})
        return o

    def stop_team(self):
        self._sync_cur_team()
        members = self.collect_members()
        for m in members:
            self.gui._stop_device(m["serial"])
        if members:
            self.team_log("⏹ 队伍已停止（{} 台）".format(len(members)))

    def capture_device(self, serial):
        """对指定单台设备截图（复用主界面 _device_screenshot）。"""
        try:
            if hasattr(self.gui, "_device_screenshot"):
                self.gui._device_screenshot(serial)
                self.team_log("📸 已对 {} 截图".format(short_dev_label(serial)))
            else:
                self.team_log("⚠️ 主界面无截图接口，跳过 {}".format(short_dev_label(serial)))
        except Exception as e:
            self.team_log("⚠️ 截图 {} 失败: {}".format(short_dev_label(serial), e))

    def poll_status(self):
        try:
            for team in self._teams:
                for serial, w in team["row_widgets"].items():
                    eng = self.gui.engines.get(serial)
                    if eng and getattr(eng, "running", False):
                        w["status_lbl"].configure(text="运行中", foreground="green")
                    else:
                        w["status_lbl"].configure(text="停止", foreground="gray")
            self.refresh_stats()
        except Exception:
            pass
        try:
            self.gui.root.after(1500, self.poll_status)
        except Exception:
            pass

    def team_log(self, msg):
        try:
            self._team_log_text.configure(state=tk.NORMAL)
            self._team_log_text.insert(tk.END, time.strftime("[%H:%M:%S] ") + msg + "\n")
            self._team_log_text.see(tk.END)
            self._team_log_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    def _poll_team_log(self):
        """消费队伍引擎日志队列，把引擎运行日志打印到队伍日志框。"""
        while True:
            try:
                msg = self._team_log_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.1)
                continue
            if msg == "__STOPPED__":
                self.team_log("⏹ 引擎已停止")
                continue
            self.team_log(str(msg))

    def save_cfg(self):
        """保存当前队伍配置。保持在当前队伍 Tab 不跳转。"""
        self._sync_cur_team()
        team_idx = self._cur_team
        # 全量保存所有队伍，避免旧文件里残留已移走的设备（导致同一设备多个队伍、角色被覆盖）
        all_teams = {}
        for tid in range(4):
            members = self.collect_members(tid)
            all_teams[str(tid)] = members
        data = {
            "scene": self._scene_var.get(),
            "teams": all_teams,
            # 完整快照：设备顺序 + 队伍归属（含未勾选设备），重新打开原样恢复
            "device_order": list(self._device_order),
            "team_of": dict(self._team_of),
        }
        try:
            with open(TEAM_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.team_log("队伍{} 配置已保存".format(
                CN_NUM[team_idx] if team_idx < len(CN_NUM) else team_idx + 1))
        except Exception as e:
            self.team_log("保存队伍配置失败: {}".format(e))
        self.refresh_team_summaries()

    def load_cfg(self):
        if not os.path.exists(TEAM_CONFIG_FILE):
            return
        try:
            with open(TEAM_CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            scene = data.get("scene", "")
            if scene and scene in SPECIAL_SCENES:
                self._scene_var.set(scene)
            # 恢复队伍归属与设备顺序：优先用保存的 device_order/team_of（完整快照），
            # 兼容旧格式（只有 teams）时从 teams 重建。
            team_of = data.get("team_of", {})
            device_order = data.get("device_order", [])
            # 当前已在线设备（load_cfg 在 refresh_devices 之前调用，此时 _device_order 还空，
            # 需自己查一次 ADB，避免把已保存设备全当离线过滤掉）
            devices = set(list_adb_devices())
            if device_order:
                self._device_order = [s for s in device_order if s in devices]
            else:
                rebuilt_order = []
                for tid in sorted(data.get("teams", {}).keys(), key=int):
                    for dev in data["teams"][tid]:
                        sid = dev["serial"]
                        if sid in devices and sid not in rebuilt_order:
                            rebuilt_order.append(sid)
                self._device_order = rebuilt_order
            # 填充 team_of：优先快照，缺的从 teams 推断（所有已保存设备都算进对应队伍）
            for tid in sorted(data.get("teams", {}).keys(), key=int):
                tid_int = int(tid)
                for dev in data["teams"][tid]:
                    sid = dev["serial"]
                    if sid not in team_of:
                        team_of[sid] = tid_int
            # 只保留当前在线设备的队伍归属（离线的先清掉，避免旧设备占用队伍）
            self._team_of = {s: t for s, t in team_of.items() if s in devices}

            # 恢复角色：以 team_of 为准，每台设备只从它所属队伍的 teams[tid] 读角色，
            # 避免旧文件 teams 跨队重复导致角色被覆盖（如一台设备同时出现在两个队伍）。
            saved_roles = {}
            for tid in sorted(data.get("teams", {}).keys(), key=int):
                tid_int = int(tid)
                for dev in data["teams"][tid]:
                    saved_roles[dev["serial"]] = dev.get("role", "defend")
            for sid in self._team_of:
                if sid in saved_roles:
                    self._roles[sid] = saved_roles[sid]

            # 队长唯一性校验：每个队伍只允许一个队长，超出的降级为 队员(攻击)。
            for tid in range(4):
                team_serials = [s for s in self._device_order if self._team_of.get(s) == tid]
                captains = [s for s in team_serials if self._roles.get(s) == "captain"]
                for extra in captains[1:]:
                    self._roles[extra] = "attack"
                    self.team_log("ℹ️ 队伍{} 有多个队长，已把 {} 降为 队员(攻击)".format(
                        CN_NUM[tid] if tid < len(CN_NUM) else tid + 1,
                        short_dev_label(extra)))
        except Exception as e:
            self.team_log("加载队伍配置失败: {}".format(e))
