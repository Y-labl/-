import os

import numpy as np
from PIL import Image


def clamp01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)


def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    diff = mx - mn

    h = np.zeros_like(mx)
    s = np.zeros_like(mx)
    v = mx

    nonzero = diff > 1e-6
    s[nonzero] = diff[nonzero] / mx[nonzero]

    # Hue
    mask = nonzero & (mx == r)
    h[mask] = ((g[mask] - b[mask]) / diff[mask]) % 6.0
    mask = nonzero & (mx == g)
    h[mask] = ((b[mask] - r[mask]) / diff[mask]) + 2.0
    mask = nonzero & (mx == b)
    h[mask] = ((r[mask] - g[mask]) / diff[mask]) + 4.0
    h = (h / 6.0) % 1.0
    return np.stack([h, s, v], axis=-1)


def hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    h6 = (h % 1.0) * 6.0
    i = np.floor(h6).astype(np.int32)
    f = h6 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    r = np.zeros_like(v)
    g = np.zeros_like(v)
    b = np.zeros_like(v)

    i_mod = i % 6
    mask = i_mod == 0
    r[mask], g[mask], b[mask] = v[mask], t[mask], p[mask]
    mask = i_mod == 1
    r[mask], g[mask], b[mask] = q[mask], v[mask], p[mask]
    mask = i_mod == 2
    r[mask], g[mask], b[mask] = p[mask], v[mask], t[mask]
    mask = i_mod == 3
    r[mask], g[mask], b[mask] = p[mask], q[mask], v[mask]
    mask = i_mod == 4
    r[mask], g[mask], b[mask] = t[mask], p[mask], v[mask]
    mask = i_mod == 5
    r[mask], g[mask], b[mask] = v[mask], p[mask], q[mask]

    return np.stack([r, g, b], axis=-1)


def recolor_to_magenta(src_path: str, dst_path: str, hue: float, sat_mul: float, val_mul: float) -> None:
    im = Image.open(src_path).convert("RGBA")
    arr = np.asarray(im).astype(np.float32) / 255.0
    rgb = arr[..., :3]
    a = arr[..., 3:4]

    mask = (a[..., 0] > 0.01).astype(np.float32)[..., None]

    hsv = rgb_to_hsv(rgb)
    # Keep very low-saturation pixels (highlights) closer to original.
    s = hsv[..., 1:2]
    keep = (s < 0.12).astype(np.float32)

    hsv_target = hsv.copy()
    hsv_target[..., 0] = hue  # 0-1
    hsv_target[..., 1] = clamp01(hsv_target[..., 1] * sat_mul)
    hsv_target[..., 2] = clamp01(hsv_target[..., 2] * val_mul)

    rgb_target = hsv_to_rgb(hsv_target)
    # keep: (H,W,1). Broadcast directly against (H,W,3)
    rgb_out = rgb * keep + rgb_target * (1.0 - keep)
    rgb_out = rgb * (1.0 - mask) + rgb_out * mask

    out = np.concatenate([rgb_out, a], axis=-1)
    out_u8 = (clamp01(out) * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(out_u8, mode="RGBA").save(dst_path, format="PNG")


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assets = os.path.join(root, "assets")

    cow = os.path.join(assets, "cow.png")
    tab = os.path.join(assets, "tab-cow.png")
    tab_sel = os.path.join(assets, "tab-cow-selected.png")

    # Rose/magenta hue close to #E91E63 (≈ 338°)
    magenta_hue = 338.0 / 360.0

    # Selected: more saturated/brighter. Unselected: slightly muted.
    recolor_to_magenta(cow, cow, hue=magenta_hue, sat_mul=1.35, val_mul=1.08)
    recolor_to_magenta(tab, tab, hue=magenta_hue, sat_mul=1.05, val_mul=0.98)
    recolor_to_magenta(tab_sel, tab_sel, hue=magenta_hue, sat_mul=1.40, val_mul=1.10)

    print("recolored:", cow)
    print("recolored:", tab)
    print("recolored:", tab_sel)


if __name__ == "__main__":
    main()

