from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="梦幻西游抓鬼自动化 v0.1")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="YAML 配置路径，默认 zhuagui/config/bot_default.yaml",
    )
    parser.add_argument("--probe", action="store_true", help="仅查找窗口并截图保存，不跑状态机")
    parser.add_argument(
        "--probe-bag",
        action="store_true",
        help="打开道具栏并保存全窗口截图，用于校准 guide_flag.first_slot_center_norm",
    )
    parser.add_argument(
        "--fly-changan",
        choices=("mafujiang", "yizhan", "both"),
        default=None,
        help="实测长安导标旗：右键第 1 格旗子后模板匹配并点击目标点（会真实操作鼠标键盘）",
    )
    parser.add_argument(
        "--probe-cursor",
        action="store_true",
        help="截图并匹配游戏内鼠标位置，保存 bot_probe_cursor.png（用于校准 cursor.hotspot_in_template）",
    )
    parser.add_argument(
        "--prep-changan",
        action="store_true",
        help="抓鬼前置：长安导标→马副将→点击，再导标→驿站→点击驿站传送人（真实键鼠）",
    )
    parser.add_argument(
        "--prep-changan-continue",
        action="store_true",
        help="抓鬼前置继续：假设已飞到马副将附近，点击马副将领取双倍；再导标→驿站传送人→大唐国境（真实键鼠）",
    )
    parser.add_argument(
        "--ghost-step1",
        action="store_true",
        help="抓鬼第一步：开道具栏→长安导标→飞到马副将（无端游坐标热键，需地图模板与格子配置正确）",
    )
    parser.add_argument(
        "--probe-flag-slot",
        action="store_true",
        help="开道具栏后只把鼠标名义移到导标格中心并保存 bot_probe_flag_slot.png（不右键，用于校准格子坐标）",
    )
    parser.add_argument(
        "--probe-flag-icon",
        action="store_true",
        help="开道具栏后用 template_icon 匹配导标旗，保存 bot_probe_flag_icon.png 供校准",
    )
    parser.add_argument(
        "--probe-state",
        action="store_true",
        help="识别窗口并截图+OCR 任务栏，写入 bot_probe_state.json（UTF-8），用于核对是否在抓鬼/是否被师门占用",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    cfg_path = args.config or (root / "config" / "bot_default.yaml")
    if not cfg_path.is_file():
        print("配置文件不存在:", cfg_path, file=sys.stderr)
        return 2

    from .settings import BotSettings
    from .runner import GhostRunner
    from .window import GameWindow

    settings = BotSettings.load(cfg_path)
    _setup_logging(settings.logging.level)

    if args.probe_state:
        import json
        import time

        from .cursor_align import park_mouse_in_window
        from .ocr_task import is_empty_task_tracker, parse_task_from_image

        win = GameWindow(settings)
        if not win.find():
            return 1
        win.activate()
        time.sleep(0.25)
        park_mouse_in_window(win, settings.cursor)
        img = win.capture()
        if img:
            p = root / "bot_probe_screenshot.png"
            img.save(p)
            logging.getLogger(__name__).info("已保存全窗口截图: %s", p)
        rx = settings.roi.task_tracker
        task_img = win.capture_roi_norm(*rx)
        if task_img:
            p2 = root / "bot_probe_task_roi.png"
            task_img.save(p2)
            logging.getLogger(__name__).info("已保存任务栏 ROI: %s", p2)
        info = parse_task_from_image(task_img, task_number=0)
        raw = info.raw_text or ""
        w = win.hwnd_window
        title = w.title if w else ""
        rect = win.rect()
        ghost_tokens = ("抓鬼", "鬼王", "钟馗", "索命")
        state = {
            "window_title": title,
            "window_rect_xywh": list(rect) if rect else None,
            "task_tracker_ocr_excerpt": raw[:900],
            "parsed_location": info.location,
            "parsed_xy": [info.coordinates[0], info.coordinates[1]],
            "has_target_coords": info.has_target,
            "task_tracker_empty": is_empty_task_tracker(raw),
            "likely_shimen_blocking": (
                "师门" in raw and not any(t in raw for t in ghost_tokens)
            ),
            "strategy_dry_run": settings.strategy.dry_run,
            "strategy_auto_ghost_prep": settings.strategy.auto_ghost_prep,
        }
        if state["task_tracker_empty"]:
            state["hint"] = (
                "追踪列表无任务（与截图/OCR 一致）。按《抓鬼任务需求文档》§2.1 须先完成步骤1～7；"
                "请设 dry_run=false 执行 auto_ghost_prep，或手动领抓鬼后再跑。"
            )
        elif state["likely_shimen_blocking"]:
            state["hint"] = (
                "任务栏为师门等（已 OCR），与抓鬼冲突：请先做完或取消师门，再设 dry_run=false 跑 auto_ghost_prep 领抓鬼。"
            )
        elif not info.has_target and raw.strip():
            state["hint"] = "有 OCR 文本但无地图坐标：可能尚未领抓鬼，或 ROI/解析规则需调整。"
        elif not raw.strip():
            state["hint"] = "任务栏 OCR 为空：检查 ROI、PaddleOCR 或是否未打开任务追踪。"
        else:
            state["hint"] = "已解析到坐标类信息，可进入寻路/战斗逻辑（仍请人工确认游戏内状态）。"
        out_path = root / "bot_probe_state.json"
        out_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logging.getLogger(__name__).info("已写入窗口观察结果: %s", out_path)
        return 0

    if args.probe_flag_slot:
        from .guide_flag import run_probe_flag_slot

        ok = run_probe_flag_slot(settings, root)
        return 0 if ok else 1

    if args.probe_flag_icon:
        from .guide_flag import run_probe_flag_icon

        ok = run_probe_flag_icon(settings, root)
        return 0 if ok else 1

    if args.ghost_step1:
        from .guide_flag import run_guide_flag_fly_to

        settings.strategy.dry_run = False
        logging.getLogger(__name__).info(
            "抓鬼第一步：开道具栏 → 长安导标 → 马副将传送点（无端游坐标热键）"
        )
        ok = run_guide_flag_fly_to(settings, "mafujiang", root / "debug_fly")
        return 0 if ok else 1

    if args.prep_changan:
        import time

        from .input_ctrl import InputController
        from .pathfind import PathfindService
        from .prep_changan import ChanganPrepFlow
        from .yolo_client import YoloNpcClient

        settings.strategy.dry_run = False
        win = GameWindow(settings)
        if not win.find():
            return 1
        win.activate()
        time.sleep(0.35)
        from .cursor_align import park_mouse_in_window

        park_mouse_in_window(win, settings.cursor)
        inp = InputController(settings)
        path = PathfindService(settings, win, inp)
        yolo = YoloNpcClient(settings)
        flow = ChanganPrepFlow(settings, win, inp, path, yolo, debug_dir=root / "debug_fly")
        return 0 if flow.run() else 1

    if args.prep_changan_continue:
        import time

        from .input_ctrl import InputController
        from .pathfind import PathfindService
        from .prep_changan import ChanganPrepFlow
        from .yolo_client import YoloNpcClient

        settings.strategy.dry_run = False
        win = GameWindow(settings)
        if not win.find():
            return 1
        win.activate()
        time.sleep(0.3)
        from .cursor_align import park_mouse_in_window

        park_mouse_in_window(win, settings.cursor)
        inp = InputController(settings)
        path = PathfindService(settings, win, inp)
        yolo = YoloNpcClient(settings)
        flow = ChanganPrepFlow(settings, win, inp, path, yolo, debug_dir=root / "debug_fly")
        return 0 if flow.run_continue_after_mafujiang() else 1

    if args.probe_cursor:
        import time

        import cv2

        from .cursor_align import _pil_to_bgr, find_cursor_hotspot_best, park_mouse_in_window

        win = GameWindow(settings)
        if not win.find():
            return 1
        win.activate()
        time.sleep(0.25)
        park_mouse_in_window(win, settings.cursor)
        img = win.capture()
        if not img:
            logging.getLogger(__name__).error("截图失败")
            return 1
        screen = _pil_to_bgr(img)
        htx, hty = settings.cursor.hotspot_in_template
        det = find_cursor_hotspot_best(screen, settings.cursor)
        vis = screen.copy()
        log = logging.getLogger(__name__)
        if det:
            hx, hy, conf, tw, th, which = det
            tl_x, tl_y = hx - htx, hy - hty
            cv2.rectangle(vis, (tl_x, tl_y), (tl_x + tw, tl_y + th), (0, 255, 0), 1)
            cv2.circle(vis, (hx, hy), 5, (255, 0, 0), 1)
            log.info(
                "匹配到游戏鼠标 tpl=%s 热点=(%s,%s) conf=%.3f（蓝圈为配置的热点）",
                which,
                hx,
                hy,
                conf,
            )
        else:
            log.warning(
                "未匹配到游戏鼠标（阈值 %.2f）。已先把鼠标移到窗口中心区域；若仍失败请换模板或略降 match_threshold",
                settings.cursor.match_threshold,
            )
        out = root / "bot_probe_cursor.png"
        cv2.imwrite(str(out), vis)
        log.info("已保存: %s", out)
        return 0

    if args.fly_changan:
        import time

        from .guide_flag import run_guide_flag_fly_to

        settings.strategy.dry_run = False
        dbg = root / "debug_fly"
        ok = True
        if args.fly_changan in ("mafujiang", "both"):
            ok = run_guide_flag_fly_to(settings, "mafujiang", dbg) and ok
            if args.fly_changan == "both":
                time.sleep(1.2)
        if args.fly_changan in ("yizhan", "both"):
            ok = run_guide_flag_fly_to(settings, "yizhan", dbg) and ok
        return 0 if ok else 1

    if args.probe_bag:
        import time

        from .guide_flag import open_inventory_from_settings
        from .input_ctrl import InputController

        settings.strategy.dry_run = False
        win = GameWindow(settings)
        if not win.find():
            return 1
        win.activate()
        time.sleep(0.35)
        inp = InputController(settings)
        open_inventory_from_settings(settings.guide_flag, win, inp, settings.cursor)
        time.sleep(settings.guide_flag.after_open_inventory_s)
        img = win.capture()
        if img:
            out = root / "bot_probe_bag.png"
            img.save(out)
            logging.getLogger(__name__).info("已保存道具栏截图: %s（用于调整 guide_flag 格子中心）", out)
        return 0

    if args.probe:
        import time

        from .cursor_align import park_mouse_in_window

        win = GameWindow(settings)
        if not win.find():
            return 1
        win.activate()
        time.sleep(0.2)
        park_mouse_in_window(win, settings.cursor)
        img = win.capture()
        if img:
            out = root / "bot_probe_screenshot.png"
            img.save(out)
            logging.getLogger(__name__).info("已保存全窗口截图: %s", out)
        rx = settings.roi.task_tracker
        task_img = win.capture_roi_norm(*rx)
        if task_img:
            out2 = root / "bot_probe_task_roi.png"
            task_img.save(out2)
            logging.getLogger(__name__).info("已保存任务栏 ROI: %s", out2)
        return 0

    runner = GhostRunner(settings)
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
