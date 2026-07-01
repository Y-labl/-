#!/usr/bin/env python3
"""
从梦幻西游背包/商店类截图切出格子图标（本图：左 6×8、右 2×8）。
用法:
  python slice_mhxy_item_sheet.py <输入.png> [输出目录]
默认输出: ../client/public/mhxy-items/

参数针对资源 image-98fa9da4...png 标定；换图若切偏，可改 CELL_W/CELL_H/OX/OY/GAP。
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

# 标定：474×495 截图
CELL_W, CELL_H = 58, 61
GAP = 2
OX, OY = 4, 5


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "client/public/mhxy-items"
    out.mkdir(parents=True, exist_ok=True)

    im = Image.open(src).convert("RGBA")
    rx = OX + 6 * CELL_W + GAP

    n = 0
    for r in range(8):
        for c in range(6):
            n += 1
            x, y = OX + c * CELL_W, OY + r * CELL_H
            im.crop((x, y, x + CELL_W, y + CELL_H)).save(out / f"sheet-fixed-{n:02d}.png")

    n = 0
    for r in range(8):
        for c in range(2):
            n += 1
            x, y = rx + c * CELL_W, OY + r * CELL_H
            im.crop((x, y, x + CELL_W, y + CELL_H)).save(out / f"sheet-var-{n:02d}.png")

    print(f"Wrote 48 sheet-fixed-*.png + 16 sheet-var-*.png -> {out}")


if __name__ == "__main__":
    main()
