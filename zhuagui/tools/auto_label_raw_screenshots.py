"""
对 dataset/raw_screenshots 下未标注 PNG：
- 使用 7 类 NPC 权重预测 0-5
- 使用 2 类「钟馗+鼠标」权重中的鼠标类(预测 id=1 -> 写出 id=6)

输出到 dataset/auto_labeled_raw/{images,labels}，请人工抽查后再合并进正式集。

用法（在 zhuagui 根目录）:
  python tools/auto_label_raw_screenshots.py --npc path/to/best.pt --mouse path/to/mouse_best.pt

若省略 --npc，将尝试 trained_separate 与 runs/detect 下常见 best.pt。
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

os.environ.setdefault("POLARS_SKIP_CPU_CHECK", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "dataset" / "raw_screenshots"
OUT = ROOT / "dataset" / "auto_labeled_raw"
OUT_IMG = OUT / "images"
OUT_LBL = OUT / "labels"

CONF_NPC = 0.25
CONF_MOUSE = 0.2


def find_default_npc() -> Path | None:
    cands = [
        ROOT / "dataset" / "runs" / "detect" / "pseudo_npc_7c" / "weights" / "best.pt",
        ROOT / "dataset" / "runs" / "detect" / "trained_model" / "zhuagui_final" / "weights" / "best.pt",
    ]
    for p in cands:
        if p.is_file():
            return p
    return None


def merge_predict(npc_path: Path | None, mouse_path: Path | None, src: Path, stem: str) -> str:
    lines: list[str] = []

    if npc_path and npc_path.is_file():
        m = YOLO(str(npc_path))
        r = m.predict(source=str(src), conf=CONF_NPC, verbose=False)[0]
        if r.boxes is not None:
            for b in r.boxes:
                if int(b.cls) > 5:
                    continue
                xywhn = b.xywhn[0].tolist()
                lines.append(
                    f"{int(b.cls)} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}"
                )

    if mouse_path and mouse_path.is_file():
        m2 = YOLO(str(mouse_path))
        r2 = m2.predict(source=str(src), conf=CONF_MOUSE, verbose=False)[0]
        best = None
        best_s = -1.0
        if r2.boxes is not None:
            for b in r2.boxes:
                if int(b.cls) != 1:
                    continue
                s = float(b.conf)
                if s > best_s:
                    best_s = s
                    xywhn = b.xywhn[0].tolist()
                    best = f"6 {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}"
        if best:
            lines.append(best)

    return "\n".join(lines) + ("\n" if lines else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npc", type=Path, default=None)
    ap.add_argument("--mouse", type=Path, default=ROOT / "trained_separate" / "mouse_zhongkui_2c" / "weights" / "best.pt")
    args = ap.parse_args()

    npc = args.npc or find_default_npc()
    mouse = args.mouse if args.mouse.is_file() else None

    if not npc and not mouse:
        raise SystemExit("请至少提供可用的 --npc 或 --mouse 权重")

    pngs = sorted(RAW.glob("*.png"))
    if not pngs:
        raise SystemExit(f"无 PNG：{RAW}")

    OUT_IMG.mkdir(parents=True, exist_ok=True)
    OUT_LBL.mkdir(parents=True, exist_ok=True)

    print("NPC:", npc)
    print("Mouse:", mouse)
    for png in pngs:
        text = merge_predict(npc, mouse, png, png.stem)
        dest = OUT_IMG / png.name
        shutil.copy2(png, dest)
        (OUT_LBL / f"{png.stem}.txt").write_text(text, encoding="utf-8")
    print(f"完成 {len(pngs)} 张 -> {OUT}")


if __name__ == "__main__":
    main()
