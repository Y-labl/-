"""仅：训练 7 类 NPC（当前 annotation_100 已配对图）+ 对 pending_labels 伪标注并移回 images。不注入鼠标。"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

os.environ.setdefault("POLARS_SKIP_CPU_CHECK", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
ANN = DATASET / "annotation_100"
IMG = ANN / "images"
LBL = ANN / "labels"
PENDING = ANN / "pending_labels"
CONF_NPC = 0.25
NPC_EPOCHS = 25


def yolo_lines_from_result(result, conf: float) -> list[str]:
    lines: list[str] = []
    if result.boxes is None or len(result.boxes) == 0:
        return lines
    for b in result.boxes:
        if float(b.conf) < conf:
            continue
        cls = int(b.cls)
        if cls > 5:
            continue
        xywhn = b.xywhn[0].tolist()
        lines.append(f"{cls} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}")
    return lines


def main() -> None:
    os.chdir(DATASET)
    print(">>> 训练 NPC 模型 epochs=", NPC_EPOCHS)
    model = YOLO("yolov8n.pt")
    model.train(
        data="data.yaml",
        epochs=NPC_EPOCHS,
        batch=8,
        imgsz=640,
        workers=0,
        device="cpu",
        project=str(DATASET / "runs" / "detect"),
        name="pseudo_npc_7c",
        exist_ok=True,
        verbose=True,
        plots=False,
        patience=12,
        amp=False,
    )
    best = Path(model.trainer.save_dir) / "weights" / "best.pt"
    model2 = YOLO(str(best))
    for png in sorted(PENDING.glob("*.png")):
        r = model2.predict(source=str(png), conf=CONF_NPC, verbose=False)[0]
        lines = yolo_lines_from_result(r, CONF_NPC)
        stem = png.stem
        (LBL / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        shutil.move(str(png), str(IMG / png.name))
        print(f"  {stem}: {len(lines)} boxes, moved")
    (ANN / "labels.cache").unlink(missing_ok=True)
    print(">>> best.pt:", best.resolve())
    print(">>> 下一步：train_mouse_2c 完成后运行 inject_mouse_only.py，再跑完整训练。")


if __name__ == "__main__":
    main()
