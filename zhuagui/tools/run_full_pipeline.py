"""
顺序执行：1) 鼠标+钟馗二分类  2) inject 鼠标到 annotation_100  3) 七类全量训练

默认轮数由环境变量控制（便于 CPU 上一口气跑完）：
  ZHUAGUI_MOUSE_EPOCHS   默认 15
  ZHUAGUI_FULL_EPOCHS    默认 40
要长训可设：set ZHUAGUI_MOUSE_EPOCHS=60 & set ZHUAGUI_FULL_EPOCHS=100

用法（在 zhuagui 根目录）:
  python tools\\run_full_pipeline.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "pipeline_log.txt"


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    LOG.open("a", encoding="utf-8").write(line + "\n")


def main() -> None:
    os.environ.setdefault("POLARS_SKIP_CPU_CHECK", "1")
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("ZHUAGUI_MOUSE_EPOCHS", os.environ.get("ZHUAGUI_MOUSE_EPOCHS", "15"))
    os.environ.setdefault("ZHUAGUI_MOUSE_PATIENCE", os.environ.get("ZHUAGUI_MOUSE_PATIENCE", "12"))
    os.environ.setdefault("ZHUAGUI_FULL_EPOCHS", os.environ.get("ZHUAGUI_FULL_EPOCHS", "40"))
    os.environ.setdefault("ZHUAGUI_FULL_PATIENCE", os.environ.get("ZHUAGUI_FULL_PATIENCE", "20"))

    LOG.write_text(f"=== pipeline start {datetime.now().isoformat()} ===\n", encoding="utf-8")
    py = sys.executable

    steps = [
        ("mouse_2c", [py, str(ROOT / "tools" / "train_mouse_2c.py")]),
        ("inject_mouse", [py, str(ROOT / "tools" / "inject_mouse_only.py")]),
        ("full_7c", [py, str(ROOT / "tools" / "train_local_full.py")]),
    ]
    for name, cmd in steps:
        log(f"START {name}: " + " ".join(cmd))
        r = subprocess.run(cmd, cwd=str(ROOT), env={**os.environ})
        log(f"END {name} exit={r.returncode}")
        if r.returncode != 0:
            log(f"ABORT: step {name} failed")
            sys.exit(r.returncode)

    log("PIPELINE OK")


if __name__ == "__main__":
    main()
