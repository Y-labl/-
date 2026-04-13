from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from PIL import Image

from .settings import BotSettings
from .window import GameWindow

# 与 dataset/data.yaml 一致（七类 NPC）
CLASS_NAMES = ("马副将", "驿站老板", "黑无常", "钟馗", "主鬼", "小怪", "鼠标指针")


class YoloNpcClient:
    def __init__(self, settings: BotSettings):
        self._log = logging.getLogger(__name__)
        self._cfg = settings
        self._model: Any = None
        w = (settings.paths.yolo_npc_weights or "").strip()
        if w:
            p = Path(w)
            if not p.is_absolute():
                p = Path(__file__).resolve().parent.parent / w
            if p.is_file():
                try:
                    from ultralytics import YOLO

                    self._model = YOLO(str(p))
                    self._log.info("已加载 YOLO: %s", p)
                except Exception as e:
                    self._log.warning("加载 YOLO 失败: %s", e)
            else:
                self._log.warning("权重文件不存在: %s", p)
        else:
            self._log.info("未配置 yolo_npc_weights，跳过检测")

    @property
    def available(self) -> bool:
        return self._model is not None

    def detect_in_window(
        self,
        win: GameWindow,
        conf: float = 0.35,
    ) -> list[tuple[str, tuple[int, int, int, int], float]]:
        """返回 [(类名, (wx, wy, ww, wh) 窗口内像素框, conf), ...]"""
        out: list[tuple[str, tuple[int, int, int, int], float]] = []
        if not self._model:
            return out
        img = win.capture()
        if not img:
            return out
        try:
            results = self._model.predict(source=img, conf=conf, verbose=False)
            r = results[0]
            if r.boxes is None:
                return out
            for b in r.boxes:
                cid = int(b.cls)
                name = CLASS_NAMES[cid] if 0 <= cid < len(CLASS_NAMES) else str(cid)
                xyxy = b.xyxy[0].tolist()
                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                cf = float(b.conf)
                out.append((name, (x1, y1, x2 - x1, y2 - y1), cf))
        except Exception as e:
            self._log.error("YOLO 推理失败: %s", e)
        return out

    def find_center_click(
        self,
        win: GameWindow,
        class_filter: Optional[set[str]] = None,
        conf: float = 0.35,
    ) -> Optional[tuple[int, int]]:
        """返回窗口内点击坐标 (wx, wy)"""
        dets = self.detect_in_window(win, conf=conf)
        best: Optional[tuple[float, int, int]] = None
        for name, (bx, by, bw, bh), cf in dets:
            if class_filter and name not in class_filter:
                continue
            cx, cy = bx + bw // 2, by + bh // 2
            if best is None or cf > best[0]:
                best = (cf, cx, cy)
        if best:
            return best[1], best[2]
        return None
