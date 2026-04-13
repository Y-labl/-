from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WindowSettings:
    title_substring: str = "梦幻西游"
    min_width: int = 400
    min_height: int = 300
    # 若 >0，则在多个候选中选尺寸最接近 expected 的窗口（适合多开区分 800x600 客户端）
    expected_width: int = 0
    expected_height: int = 0


@dataclass
class StrategySettings:
    assume_party_ready: bool = True
    # 主流程开头：长安导标→马副将(可选领双)→驿站→国境，再地府钟馗(可选黑无常)领抓鬼，最后才 OCR 任务栏
    auto_ghost_prep: bool = True
    enable_double_exp: bool = False
    enable_guowang: bool = False
    enable_tianyan: bool = False
    max_rounds: int = 1
    dry_run: bool = True


@dataclass
class PathSettings:
    yolo_npc_weights: str = ""
    # 端游 Alt+G 为「给予」非寻路；仅当你配置了 hotkeys.open_goto 为真实寻路热键时才可开 true
    enable_coordinate_hotkey_path: bool = False


@dataclass
class DelaySettings:
    action_min_ms: int = 80
    action_max_ms: int = 220
    after_map_load_s: float = 1.2


@dataclass
class ROISettings:
    task_tracker: tuple[float, float, float, float] = (0.68, 0.06, 0.99, 0.42)


@dataclass
class HotkeySettings:
    open_goto: list[str] = field(default_factory=lambda: ["alt", "g"])
    confirm_keys: list[str] = field(default_factory=lambda: ["enter"])


@dataclass
class CursorSettings:
    """用游戏内鼠标皮肤做模板匹配，迭代消除与系统鼠标的偏移。"""
    enabled: bool = True
    # True：每次点击前做模板对齐；道具栏内指针常变形，易误移导致关窗，默认关
    align_before_click: bool = False
    # 名义坐标 moveTo 的动画时长（秒），便于肉眼确认是否对准格子
    move_to_point_duration_s: float = 0.15
    template_path: str = "assets/ingame_cursor_template.png"
    # 非空则再试一张图，取置信度更高者（你提供的 sb0 备选）
    template_path_alt: str = "assets/ingame_cursor_template_alt.png"
    # 游戏点击生效点相对模板左上角的偏移（尖端在左上时多为小整数，可用 --probe-cursor 核对）
    hotspot_in_template: tuple[int, int] = (2, 2)
    match_threshold: float = 0.55
    max_align_steps: int = 12
    tolerance_px: int = 3
    settle_delay_s: float = 0.07
    # 截图/对齐前先把系统鼠标移到窗口内此比例处，否则游戏可能不画指针
    park_in_window_norm: tuple[float, float] = (0.5, 0.55)
    park_delay_s: float = 0.2
    # 目标点附近小区域匹配 + 分象限渐进 pyautogui.move（对齐游戏内指针）
    align_search_padding_px: int = 120
    align_nudge_min_px: int = 3
    align_nudge_half_threshold_px: int = 5
    align_nudge_duration_s: float = 0.05


@dataclass
class GuideFlagSettings:
    """长安导标旗：道具栏热键 + 第 1 格中心比例 + 地图模板路径。"""
    open_inventory: list[str] = field(default_factory=lambda: ["alt", "e"])
    # 打开道具栏前系统鼠标移到窗口内比例，默认中心（减轻与游戏内光标不同步）
    park_before_inventory_norm: tuple[float, float] = (0.5, 0.5)
    max_inventory_open_attempts: int = 3
    esc_before_reopen_inventory: int = 1
    # True：缓慢移到导标旗后再用模板对齐游戏内光标再右键（背包内指针样式变化时可能需备选用模板）
    align_after_move_to_flag: bool = False
    # True：点击 inventory_icon_click_norm 打开道具（部分客户端/焦点下 Alt+E 无效）
    open_inventory_use_icon_click: bool = False
    # True：先按 open_inventory 热键再点图标（提高打开成功率）
    open_inventory_also_hotkey: bool = False
    inventory_icon_click_norm: tuple[float, float] = (0.73, 0.90)
    changan_slot_index: int = 0
    first_slot_center_norm: tuple[float, float] = (0.38, 0.58)
    slot_spacing_x_norm: float = 0.034
    template_mafujiang: str = "assets/guide_flag/changan_map_mafujiang.png"
    template_yizhan: str = "assets/guide_flag/changan_map_yizhan.png"
    # 导标旗图标模板，用于在背包内精确定位后右键；空则用 first_slot_center_norm 比例
    template_icon: str = "assets/guide_flag/guide_flag_icon.png"
    icon_match_threshold: float = 0.7
    move_to_flag_duration_s: float = 0.35
    match_threshold: float = 0.72
    after_open_inventory_s: float = 0.45
    pre_fly_esc_presses: int = 2
    after_right_click_flag_s: float = 0.85
    after_teleport_extra_s: float = 0.4
    close_ui_esc_presses: int = 2


@dataclass
class PrepChanganSettings:
    """导标落地后 ALT+G 找 NPC，再点击；无 YOLO 时用窗口比例兜底。"""
    after_fly_sleep_s: float = 2.5
    after_altg_walk_s: float = 5.0
    between_steps_sleep_s: float = 1.2
    yolo_npc_conf: float = 0.32
    # 键为 npc_coords 里的名字，如 马副将、驿站老板（游戏内驿站传送人）
    fallback_click_norm: dict[str, tuple[float, float]] = field(default_factory=dict)


@dataclass
class PrepGhostSettings:
    """国境之后：到地府领鬼王(可选)→钟馗领抓鬼。依赖 Alt+G 坐标与 npc_coords。"""
    post_guojing_delay_s: float = 2.0
    # 若需从国境手动跑进地府，可设为等待秒数（0 表示不等待）
    manual_travel_to_difu_s: float = 0.0
    after_altg_heiwuchang_walk_s: float = 6.0
    after_altg_zhongkui_walk_s: float = 6.0
    dialog_enter_presses: int = 8
    yolo_npc_conf: float = 0.32
    fallback_click_norm: dict[str, tuple[float, float]] = field(default_factory=dict)


@dataclass
class LoggingSettings:
    level: str = "INFO"


@dataclass
class LiveObserveSettings:
    """主程序跑状态时定时截图 + manifest，便于用图片对照每一步执行结果。"""
    enabled: bool = True
    # 相对 zhuagui 根目录；每次运行建子目录 YYYYMMDD_HHMMSS
    dir: str = "debug_run"
    save_full_window: bool = True
    save_task_tracker_roi: bool = True


@dataclass
class BotSettings:
    window: WindowSettings = field(default_factory=WindowSettings)
    strategy: StrategySettings = field(default_factory=StrategySettings)
    paths: PathSettings = field(default_factory=PathSettings)
    delays: DelaySettings = field(default_factory=DelaySettings)
    roi: ROISettings = field(default_factory=ROISettings)
    hotkeys: HotkeySettings = field(default_factory=HotkeySettings)
    cursor: CursorSettings = field(default_factory=CursorSettings)
    guide_flag: GuideFlagSettings = field(default_factory=GuideFlagSettings)
    prep_changan: PrepChanganSettings = field(default_factory=PrepChanganSettings)
    prep_ghost: PrepGhostSettings = field(default_factory=PrepGhostSettings)
    npc_coords: dict[str, dict[str, int]] = field(default_factory=dict)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    live_observe: LiveObserveSettings = field(default_factory=LiveObserveSettings)

    @staticmethod
    def load(path: Path) -> BotSettings:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return BotSettings._from_dict(raw)

    @staticmethod
    def _from_dict(d: dict[str, Any]) -> BotSettings:
        w = d.get("window") or {}
        s = d.get("strategy") or {}
        p = d.get("paths") or {}
        del_ = d.get("delays") or {}
        roi = d.get("roi") or {}
        hk = d.get("hotkeys") or {}
        cur = d.get("cursor") or {}
        gf = d.get("guide_flag") or {}
        pc = d.get("prep_changan") or {}
        pg = d.get("prep_ghost") or {}
        lg = d.get("logging") or {}
        lo = d.get("live_observe") or {}
        tr = tuple(roi.get("task_tracker") or (0.68, 0.06, 0.99, 0.42))
        if len(tr) != 4:
            tr = (0.68, 0.06, 0.99, 0.42)
        fsn = tuple(gf.get("first_slot_center_norm") or (0.38, 0.58))
        if len(fsn) != 2:
            fsn = (0.38, 0.58)
        pbin = gf.get("park_before_inventory_norm")
        if isinstance(pbin, (list, tuple)) and len(pbin) == 2:
            park_inv_norm = (float(pbin[0]), float(pbin[1]))
        else:
            park_inv_norm = (0.5, 0.5)
        icn = gf.get("inventory_icon_click_norm")
        if isinstance(icn, (list, tuple)) and len(icn) == 2:
            inv_icon_norm = (float(icn[0]), float(icn[1]))
        else:
            inv_icon_norm = (0.73, 0.90)
        hs = cur.get("hotspot_in_template") or [2, 2]
        if isinstance(hs, (list, tuple)) and len(hs) == 2:
            hotspot_tpl = (int(hs[0]), int(hs[1]))
        else:
            hotspot_tpl = (2, 2)
        pk = cur.get("park_in_window_norm") or [0.5, 0.55]
        if isinstance(pk, (list, tuple)) and len(pk) == 2:
            park_norm = (float(pk[0]), float(pk[1]))
        else:
            park_norm = (0.5, 0.55)
        fb_raw = pc.get("fallback_click_norm") or {}
        fb_norm: dict[str, tuple[float, float]] = {}
        if isinstance(fb_raw, dict):
            for k, v in fb_raw.items():
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    fb_norm[str(k)] = (float(v[0]), float(v[1]))
        pg_fb_raw = pg.get("fallback_click_norm") or {}
        pg_fb: dict[str, tuple[float, float]] = {}
        if isinstance(pg_fb_raw, dict):
            for k, v in pg_fb_raw.items():
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    pg_fb[str(k)] = (float(v[0]), float(v[1]))
        return BotSettings(
            window=WindowSettings(
                title_substring=w.get("title_substring", "梦幻西游"),
                min_width=int(w.get("min_width", 400)),
                min_height=int(w.get("min_height", 300)),
                expected_width=int(w.get("expected_width", 0)),
                expected_height=int(w.get("expected_height", 0)),
            ),
            strategy=StrategySettings(
                assume_party_ready=bool(s.get("assume_party_ready", True)),
                auto_ghost_prep=bool(s.get("auto_ghost_prep", True)),
                enable_double_exp=bool(s.get("enable_double_exp", False)),
                enable_guowang=bool(s.get("enable_guowang", False)),
                enable_tianyan=bool(s.get("enable_tianyan", False)),
                max_rounds=int(s.get("max_rounds", 1)),
                dry_run=bool(s.get("dry_run", True)),
            ),
            paths=PathSettings(
                yolo_npc_weights=str(p.get("yolo_npc_weights") or ""),
                enable_coordinate_hotkey_path=bool(
                    p.get("enable_coordinate_hotkey_path", False)
                ),
            ),
            delays=DelaySettings(
                action_min_ms=int(del_.get("action_min_ms", 80)),
                action_max_ms=int(del_.get("action_max_ms", 220)),
                after_map_load_s=float(del_.get("after_map_load_s", 1.2)),
            ),
            roi=ROISettings(task_tracker=tr),  # type: ignore[arg-type]
            hotkeys=HotkeySettings(
                open_goto=list(hk.get("open_goto") or ["alt", "g"]),
                confirm_keys=list(hk.get("confirm_keys") or ["enter"]),
            ),
            cursor=CursorSettings(
                enabled=bool(cur.get("enabled", True)),
                align_before_click=bool(cur.get("align_before_click", False)),
                move_to_point_duration_s=float(
                    cur.get("move_to_point_duration_s", 0.15)
                ),
                template_path=str(
                    cur.get("template_path") or "assets/ingame_cursor_template.png"
                ),
                template_path_alt=(
                    ""
                    if cur.get("template_path_alt") == ""
                    else str(
                        cur.get("template_path_alt")
                        or "assets/ingame_cursor_template_alt.png"
                    )
                ),
                hotspot_in_template=hotspot_tpl,
                match_threshold=float(cur.get("match_threshold", 0.55)),
                max_align_steps=int(cur.get("max_align_steps", 12)),
                tolerance_px=int(cur.get("tolerance_px", 3)),
                settle_delay_s=float(cur.get("settle_delay_s", 0.07)),
                park_in_window_norm=park_norm,
                park_delay_s=float(cur.get("park_delay_s", 0.2)),
                align_search_padding_px=int(cur.get("align_search_padding_px", 120)),
                align_nudge_min_px=int(cur.get("align_nudge_min_px", 3)),
                align_nudge_half_threshold_px=int(
                    cur.get("align_nudge_half_threshold_px", 5)
                ),
                align_nudge_duration_s=float(
                    cur.get("align_nudge_duration_s", 0.05)
                ),
            ),
            guide_flag=GuideFlagSettings(
                open_inventory=list(gf.get("open_inventory") or ["alt", "e"]),
                park_before_inventory_norm=park_inv_norm,
                max_inventory_open_attempts=int(gf.get("max_inventory_open_attempts", 3)),
                esc_before_reopen_inventory=int(gf.get("esc_before_reopen_inventory", 1)),
                align_after_move_to_flag=bool(gf.get("align_after_move_to_flag", False)),
                open_inventory_use_icon_click=bool(gf.get("open_inventory_use_icon_click", False)),
                open_inventory_also_hotkey=bool(gf.get("open_inventory_also_hotkey", False)),
                inventory_icon_click_norm=inv_icon_norm,
                changan_slot_index=int(gf.get("changan_slot_index", 0)),
                first_slot_center_norm=fsn,  # type: ignore[arg-type]
                slot_spacing_x_norm=float(gf.get("slot_spacing_x_norm", 0.034)),
                template_mafujiang=str(
                    gf.get("template_mafujiang") or "assets/guide_flag/changan_map_mafujiang.png"
                ),
                template_yizhan=str(
                    gf.get("template_yizhan") or "assets/guide_flag/changan_map_yizhan.png"
                ),
                template_icon=str(
                    gf.get("template_icon") or "assets/guide_flag/guide_flag_icon.png"
                ),
                icon_match_threshold=float(gf.get("icon_match_threshold", 0.7)),
                move_to_flag_duration_s=float(gf.get("move_to_flag_duration_s", 0.35)),
                match_threshold=float(gf.get("match_threshold", 0.72)),
                after_open_inventory_s=float(gf.get("after_open_inventory_s", 0.45)),
                pre_fly_esc_presses=int(gf.get("pre_fly_esc_presses", 2)),
                after_right_click_flag_s=float(gf.get("after_right_click_flag_s", 0.85)),
                after_teleport_extra_s=float(gf.get("after_teleport_extra_s", 0.4)),
                close_ui_esc_presses=int(gf.get("close_ui_esc_presses", 2)),
            ),
            prep_changan=PrepChanganSettings(
                after_fly_sleep_s=float(pc.get("after_fly_sleep_s", 2.5)),
                after_altg_walk_s=float(pc.get("after_altg_walk_s", 5.0)),
                between_steps_sleep_s=float(pc.get("between_steps_sleep_s", 1.2)),
                yolo_npc_conf=float(pc.get("yolo_npc_conf", 0.32)),
                fallback_click_norm=fb_norm,
            ),
            prep_ghost=PrepGhostSettings(
                post_guojing_delay_s=float(pg.get("post_guojing_delay_s", 2.0)),
                manual_travel_to_difu_s=float(pg.get("manual_travel_to_difu_s", 0.0)),
                after_altg_heiwuchang_walk_s=float(
                    pg.get("after_altg_heiwuchang_walk_s", 6.0)
                ),
                after_altg_zhongkui_walk_s=float(
                    pg.get("after_altg_zhongkui_walk_s", 6.0)
                ),
                dialog_enter_presses=int(pg.get("dialog_enter_presses", 8)),
                yolo_npc_conf=float(pg.get("yolo_npc_conf", 0.32)),
                fallback_click_norm=pg_fb,
            ),
            npc_coords=dict(d.get("npc_coords") or {}),
            logging=LoggingSettings(level=str(lg.get("level", "INFO"))),
            live_observe=LiveObserveSettings(
                enabled=bool(lo.get("enabled", True)),
                dir=str(lo.get("dir") or "debug_run"),
                save_full_window=bool(lo.get("save_full_window", True)),
                save_task_tracker_roi=bool(lo.get("save_task_tracker_roi", True)),
            ),
        )
