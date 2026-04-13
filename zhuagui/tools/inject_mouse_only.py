"""仅将 mouse_zhongkui_2c 模型预测的鼠标写入 annotation_100 labels（class 6）。"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("POLARS_SKIP_CPU_CHECK", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
ANN = ROOT / "dataset" / "annotation_100"
IMG = ANN / "images"
LBL = ANN / "labels"
CONF_MOUSE = 0.2


def find_mouse_weights() -> Path | None:
    cands = [
        ROOT / "trained_separate" / "mouse_zhongkui_2c" / "weights" / "best.pt",
        ROOT / "dataset" / "runs" / "trained_separate" / "mouse_smoke" / "weights" / "best.pt",
        ROOT / "dataset" / "runs" / "trained_separate" / "mouse_zhongkui_2c" / "weights" / "best.pt",
    ]
    for p in cands:
        if p.is_file():
            return p
    return None


def main() -> None:
    mouse_pt = find_mouse_weights()
    if not mouse_pt:
        raise SystemExit("未找到鼠标 2 类模型 best.pt，请先运行 tools/train_mouse_2c.py")
    print("使用权重:", mouse_pt.resolve())
    model = YOLO(str(mouse_pt))
    for png in sorted(IMG.glob("*.png")):
        results = model.predict(source=str(png), conf=CONF_MOUSE, verbose=False)
        r = results[0]
        best = None
        best_s = -1.0
        if r.boxes is not None:
            for b in r.boxes:
                if int(b.cls) != 1:
                    continue
                s = float(b.conf)
                if s > best_s:
                    best_s = s
                    xywhn = b.xywhn[0].tolist()
                    best = f"6 {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}"
        if not best:
            continue
        txt = LBL / f"{png.stem}.txt"
        existing: list[str] = []
        if txt.is_file():
            for line in txt.read_text(encoding="utf-8", errors="ignore").splitlines():
                parts = line.split()
                if not parts or int(parts[0]) == 6:
                    continue
                existing.append(line.strip())
        existing.append(best)
        txt.write_text("\n".join(existing) + "\n", encoding="utf-8")
        print(png.name, "mouse ok")
    (ANN / "labels.cache").unlink(missing_ok=True)
    print("done")


if __name__ == "__main__":
    main()
