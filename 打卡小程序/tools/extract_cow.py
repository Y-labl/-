import os

import cv2
import numpy as np
from PIL import Image


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def grabcut_cutout(img_bgr: np.ndarray, rect, iter_count: int = 6) -> np.ndarray:
    mask = np.zeros(img_bgr.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, iter_count, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")
    return mask2


def crop_to_alpha_bounds(rgba: np.ndarray, pad: int = 8) -> np.ndarray:
    alpha = rgba[:, :, 3]
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0 or len(ys) == 0:
        return rgba
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(rgba.shape[1] - 1, x1 + pad)
    y1 = min(rgba.shape[0] - 1, y1 + pad)
    return rgba[y0 : y1 + 1, x0 : x1 + 1]


def save_resized_png(rgba: np.ndarray, out_path: str, size: int) -> None:
    im = Image.fromarray(rgba, mode="RGBA")
    im = im.resize((size, size), resample=Image.LANCZOS)
    im.save(out_path, format="PNG")


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = os.environ.get("COW_SRC")
    if not src:
        raise SystemExit("Missing env var COW_SRC")

    out_dir = os.path.join(root, "assets")
    ensure_dir(out_dir)

    img_bgr = cv2.imread(src, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise SystemExit(f"Failed to read image: {src}")

    # Screenshot size is 460x1024. The left cow is roughly here.
    # Keep the crop tight to avoid picking up the banner below.
    x0, y0, x1, y1 = 35, 170, 265, 455
    crop = img_bgr[y0:y1, x0:x1].copy()

    # Foreground rectangle inside the crop (leave some margin).
    rect = (18, 28, crop.shape[1] - 36, crop.shape[0] - 45)
    alpha = grabcut_cutout(crop, rect, iter_count=7)

    # Hard trim: the banner below often gets classified as foreground.
    # Keep only the upper part where the mascot sits.
    h = alpha.shape[0]
    alpha[int(h * 0.78) :, :] = 0

    rgba = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    rgba = crop_to_alpha_bounds(rgba, pad=12)

    cow_path = os.path.join(out_dir, "cow.png")
    tab_path = os.path.join(out_dir, "tab-cow.png")
    tab_sel_path = os.path.join(out_dir, "tab-cow-selected.png")

    # Larger for hero, smaller for tab bar (WeChat tab icons typically 81x81px, but PNG can be larger).
    Image.fromarray(rgba, mode="RGBA").save(cow_path, format="PNG")
    save_resized_png(rgba, tab_path, size=96)
    save_resized_png(rgba, tab_sel_path, size=96)

    print("wrote:", cow_path)
    print("wrote:", tab_path)
    print("wrote:", tab_sel_path)


if __name__ == "__main__":
    main()

