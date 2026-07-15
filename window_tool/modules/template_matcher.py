"""模板匹配模块 — 在截图/窗口中查找小图标/区域的位置
无 OpenCV 依赖，纯 numpy 实现 NCC (归一化互相关)
"""

import numpy as np
from PIL import Image
import time


class TemplateMatch:
    """单次匹配结果"""
    __slots__ = ('x', 'y', 'confidence', 'template_w', 'template_h')

    def __init__(self, x: int, y: int, confidence: float, tw: int, th: int):
        self.x = x
        self.y = y
        self.confidence = confidence
        self.template_w = tw
        self.template_h = th

    @property
    def center(self):
        return (self.x + self.template_w // 2, self.y + self.template_h // 2)

    def __repr__(self):
        return f"Match({self.x},{self.y} conf={self.confidence:.3f})"


class TemplateMatcher:
    """模板匹配引擎"""

    def __init__(self, threshold: float = 0.75, max_results: int = 30):
        self.threshold = threshold
        self.max_results = max_results
        self._last_image = None
        self._last_template = None
        self._max_score = 0.0  # 最后一次匹配的最高分（用于诊断）

    def match(self, image: Image.Image, template: Image.Image):
        """在 image 中查找 template，返回置信度降序的匹配列表"""
        t0 = time.time()

        src = np.array(image.convert('L'), dtype=np.float32)
        tpl = np.array(template.convert('L'), dtype=np.float32)

        ih, iw = src.shape
        th, tw = tpl.shape

        if th > ih or tw > iw or th < 4 or tw < 4:
            return [], 0.0

        results = self._ncc_match(src, tpl)
        elapsed = time.time() - t0

        self._last_image = image
        self._last_template = template
        return results, elapsed

    def _ncc_match(self, src: np.ndarray, tpl: np.ndarray):
        """归一化互相关模板匹配 (步进式, 非 FFT)"""
        ih, iw = src.shape
        th, tw = tpl.shape

        # 模板归一化
        tpl_flat = tpl.ravel().astype(np.float64)
        tpl_mean = tpl_flat.mean()
        tpl_std = tpl_flat.std()
        if tpl_std < 1e-6:
            tpl_norm = tpl_flat - tpl_mean
        else:
            tpl_norm = (tpl_flat - tpl_mean) / tpl_std
        tpl_norm_len = float(np.sqrt(np.sum(tpl_norm ** 2)))
        if tpl_norm_len < 1e-9:
            return []

        # 步长自适应 (小模板细步长, 大模板粗步长)
        step = max(1, min(tw, th) // 4)
        candidates = []
        self._max_score = 0.0

        for y in range(0, ih - th + 1, step):
            for x in range(0, iw - tw + 1, step):
                patch = src[y:y + th, x:x + tw].ravel().astype(np.float64)
                patch_mean = patch.mean()
                patch_std = patch.std()
                if patch_std < 1e-6:
                    # 纯色区域 → 直接比较均值
                    score = 1.0 if abs(patch_mean - tpl_mean) < 10 else 0.0
                else:
                    patch_norm = (patch - patch_mean) / patch_std
                    dot = float(np.dot(tpl_norm, patch_norm))
                    patch_norm_len = float(np.sqrt(np.sum(patch_norm ** 2)))
                    if patch_norm_len < 1e-9:
                        score = 0.0
                    else:
                        score = dot / (tpl_norm_len * patch_norm_len)

                if score > self._max_score:
                    self._max_score = score

                if score >= self.threshold:
                    candidates.append((x, y, score))

        if not candidates:
            return []

        # 按置信度降序
        candidates.sort(key=lambda c: c[2], reverse=True)

        # 非极大值抑制 (NMS)
        filtered = []
        min_dist_x = tw // 3
        min_dist_y = th // 3
        for cx, cy, score in candidates:
            too_close = False
            for fx, fy, _ in filtered:
                if abs(cx - fx) < min_dist_x and abs(cy - fy) < min_dist_y:
                    too_close = True
                    break
            if not too_close:
                filtered.append((cx, cy, score))
                if len(filtered) >= self.max_results:
                    break

        # 构建结果
        results = []
        for fx, fy, score in filtered:
            results.append(TemplateMatch(fx, fy, score, tw, th))
        return results

    def draw_matches(self, image: Image.Image, matches: list,
                     color: tuple = (0, 255, 0), thickness: int = 2):
        """在原图上标注匹配位置"""
        from PIL import ImageDraw
        img = image.copy().convert('RGB')
        draw = ImageDraw.Draw(img)
        for m in matches:
            x1, y1 = m.x, m.y
            x2, y2 = m.x + m.template_w, m.y + m.template_h
            # 外框
            for t in range(thickness):
                draw.rectangle(
                    [x1 - t, y1 - t, x2 + t, y2 + t],
                    outline=color)
            # 中心十字
            cx, cy = m.center
            draw.line([cx - 6, cy, cx + 6, cy], fill=color, width=1)
            draw.line([cx, cy - 6, cx, cy + 6], fill=color, width=1)
            # 置信度标签
            draw.text((x1 + 2, y1 - 14), f"{m.confidence:.3f}",
                      fill=(255, 255, 0))
        return img
