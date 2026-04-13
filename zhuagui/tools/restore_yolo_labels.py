"""从 labels_backup_3_6 还原 yolo_dataset/labels（恢复 3、6 类编号）。"""
from __future__ import annotations

import shutil
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent / "dataset" / "yolo_dataset"
BACKUP = DATASET / "labels_backup_3_6"
LABELS = DATASET / "labels"


def main() -> None:
    if not BACKUP.is_dir():
        raise SystemExit(f"no backup at {BACKUP}")
    if LABELS.is_dir():
        shutil.rmtree(LABELS)
    shutil.copytree(BACKUP, LABELS)
    print(f"restored {LABELS} from backup")


if __name__ == "__main__":
    main()
