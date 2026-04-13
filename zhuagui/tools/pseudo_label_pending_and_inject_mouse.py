"""
1) 用 annotation_100 当前已标注图训练一版轻量 NPC 模型（7 类，数据里尚无鼠标类框亦可）。
2) 对 pending_labels 中 PNG 伪标注，写入 labels/ 并移图回 images/。
3) 用 trained_separate/mouse_zhongkui_2c/weights/best.pt 在 annotation_100 全图预测鼠标，写入 class_id=6。

用法（在 zhuagui 根目录）:
  python tools/pseudo_label_pending_and_inject_mouse.py

依赖：已运行 backup_remap_yolo_2class.py + train_mouse_2c.py 得到鼠标模型；
若尚无鼠标模型，脚本会跳过注入鼠标并提示。
"""
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
DATA_7C = DATASET / "data.yaml"
MOUSE_PT = ROOT / "trained_separate" / "mouse_zhongkui_2c" / "weights" / "best.pt"

NPC_EPOCHS = 35
NPC_BATCH = 8
CONF_NPC = 0.25
CONF_MOUSE = 0.2


def yolo_lines_from_result(result, conf: float, class_map: dict[int, int] | None = None) -> list[str]:
    """class_map: pred_cls -> out_cls；None 表示不变。"""
    lines: list[str] = []
    if result.boxes is None or len(result.boxes) == 0:
        return lines
    h, w = result.orig_shape
    for b in result.boxes:
        score = float(b.conf)
        if score < conf:
            continue
        cls = int(b.cls)
        if class_map is not None:
            if cls not in class_map:
                continue
            cls = class_map[cls]
        xywhn = b.xywhn[0].tolist()
        lines.append(f"{cls} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}")
    return lines


def train_npc_quick() -> Path:
    print(">>> 训练 7 类 NPC 模型（用于补全 pending 伪标注）…")
    os.chdir(DATASET)
    model = YOLO("yolov8n.pt")
    model.train(
        data="data.yaml",
        epochs=NPC_EPOCHS,
        batch=NPC_BATCH,
        imgsz=640,
        workers=0,
        device="cpu",
        project=str(DATASET / "runs" / "detect"),
        name="pseudo_npc_7c",
        exist_ok=True,
        verbose=True,
        plots=False,
        patience=15,
        amp=False,
    )
    save_dir = Path(model.trainer.save_dir)
    best = save_dir / "weights" / "best.pt"
    assert best.is_file(), best
    print(">>> NPC best:", best.resolve())
    return best


def pseudo_label_pending(npc_weights: Path) -> None:
    pngs = sorted(PENDING.glob("*.png"))
    if not pngs:
        print(">>> pending_labels 无 PNG，跳过伪标注")
        return
    model = YOLO(str(npc_weights))
    for png in pngs:
        results = model.predict(source=str(png), conf=CONF_NPC, verbose=False)
        r = results[0]
        lines = yolo_lines_from_result(r, CONF_NPC)
        stem = png.stem
        out_txt = LBL / f"{stem}.txt"
        out_txt.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        dest = IMG / png.name
        shutil.move(str(png), str(dest))
        print(f"  pseudo {stem}: {len(lines)} boxes -> {out_txt.name}, moved to images/")
    # 清理 cache
    for cache in (ANN / "labels.cache", LBL.parent / "labels.cache"):
        cache.unlink(missing_ok=True)


def inject_mouse_class6() -> None:
    if not MOUSE_PT.is_file():
        print(f">>> 未找到鼠标模型 {MOUSE_PT}，跳过鼠标注入（请先 train_mouse_2c）")
        return
    print(">>> 注入鼠标 class=6 …")
    model = YOLO(str(MOUSE_PT))
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
                if not parts:
                    continue
                if int(parts[0]) == 6:
                    continue
                existing.append(line.strip())
        existing.append(best)
        txt.write_text("\n".join(existing) + "\n", encoding="utf-8")


def main() -> None:
    assert DATA_7C.is_file()
    assert LBL.is_dir() and IMG.is_dir()

    npc_pt = train_npc_quick()
    pseudo_label_pending(npc_pt)
    inject_mouse_class6()
    print(">>> 完成。请删除 annotation_100/labels.cache 后运行 train_local_full.py 训练 100 张（含鼠标）。")


if __name__ == "__main__":
    main()
