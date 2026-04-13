"""
单独训练：钟馗 + 鼠标（2 类），数据来自 yolo_dataset。
请先运行：python tools/backup_remap_yolo_2class.py
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("POLARS_SKIP_CPU_CHECK", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "dataset" / "data_mouse_2c.yaml"


if __name__ == "__main__":
    assert DATA.is_file(), f"missing {DATA}"
    epochs = int(os.environ.get("ZHUAGUI_MOUSE_EPOCHS", "60"))
    patience = int(os.environ.get("ZHUAGUI_MOUSE_PATIENCE", "25"))
    project_dir = (ROOT / "trained_separate").resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(DATA.parent)  # dataset/，保证 data.yaml 里 path: . 正确
    print("训练 2 类模型：钟馗 + 鼠标 | cwd=", Path.cwd(), "data=data_mouse_2c.yaml")
    print("project ->", project_dir, "| epochs=", epochs)
    model = YOLO("yolov8n.pt")
    model.train(
        data="data_mouse_2c.yaml",
        epochs=epochs,
        batch=8,
        imgsz=640,
        workers=0,
        device="cpu",
        project=str(project_dir),
        name="mouse_zhongkui_2c",
        verbose=True,
        plots=False,
        patience=patience,
        amp=False,
    )
    try:
        save_dir = Path(model.trainer.save_dir)
    except Exception:
        save_dir = ROOT / "trained_separate" / "mouse_zhongkui_2c"
    print("best.pt ->", (save_dir / "weights" / "best.pt").resolve())
