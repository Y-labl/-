"""
将 yolo_dataset/labels 中 3->0(钟馗)、6->1(鼠标)，并备份原始标签到 labels_backup_3_6。
训练「钟馗+鼠标」专用模型前执行一次即可；恢复请用 restore_yolo_labels.py。
"""
from __future__ import annotations

import shutil
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent / "dataset" / "yolo_dataset"
BACKUP = DATASET / "labels_backup_3_6"
LABELS = DATASET / "labels"
MAP = {3: 0, 6: 1}


def main() -> None:
    if not LABELS.is_dir():
        raise SystemExit(f"missing {LABELS}")

    if BACKUP.exists():
        print(f"backup exists, skip copy: {BACKUP}")
    else:
        shutil.copytree(LABELS, BACKUP)
        print(f"backed up -> {BACKUP}")

    for txt in sorted(LABELS.glob("*.txt")):
        lines_out: list[str] = []
        for line in txt.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cls = int(parts[0])
            if cls not in MAP:
                continue
            parts[0] = str(MAP[cls])
            lines_out.append(" ".join(parts))
        txt.write_text("\n".join(lines_out) + ("\n" if lines_out else ""), encoding="utf-8")

    print(f"remapped labels in {LABELS} (classes 0=钟馗, 1=鼠标)")


if __name__ == "__main__":
    main()
