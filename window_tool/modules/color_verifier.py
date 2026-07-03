"""颜色验证与标注模块"""
import os, subprocess, platform
from datetime import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import QObject, Signal, QThread


class VerifyWorker(QThread):
    finished = Signal(object, object)
    error = Signal(str)

    def __init__(self, screenshot, color_points, tolerance=5, scope=15, parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        self.color_points = color_points
        self.tolerance = tolerance
        self.scope = scope

    def run(self):
        try:
            results, annotated = ColorVerifier.verify_colors(
                self.screenshot, self.color_points, self.tolerance, self.scope)
            self.finished.emit(results, annotated)
        except Exception as e:
            self.error.emit(f"验证异常: {str(e)}")


class ColorVerifier(QObject):
    verification_done = Signal(list, object)
    verification_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._last_results = []
        self._last_annotated = None
        self.tolerance = 5
        self.search_scope = 15

    @staticmethod
    def color_distance(c1, c2):
        return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5

    @staticmethod
    def find_color_in_scope(img, target_color, cx, cy, tolerance=5, scope=15):
        w, h = img.width, img.height
        search_coords = [(cx, cy)]
        for d in range(1, scope + 1):
            for dx in range(-d, d + 1):
                search_coords.append((cx + dx, cy - d))
                search_coords.append((cx + dx, cy + d))
            for dy in range(-d + 1, d):
                search_coords.append((cx - d, cy + dy))
                search_coords.append((cx + d, cy + dy))

        for sx, sy in search_coords:
            if 0 <= sx < w and 0 <= sy < h:
                pixel = img.getpixel((sx, sy))
                rgb = tuple(pixel[:3]) if isinstance(pixel, tuple) and len(pixel) >= 3 else (pixel, pixel, pixel)
                if rgb == target_color:
                    return (sx, sy)

        best_pos = (-1, -1)
        best_dist = float('inf')
        for sx, sy in search_coords:
            if 0 <= sx < w and 0 <= sy < h:
                pixel = img.getpixel((sx, sy))
                rgb = tuple(pixel[:3]) if isinstance(pixel, tuple) and len(pixel) >= 3 else (pixel, pixel, pixel)
                dist = ColorVerifier.color_distance(rgb, target_color)
                if dist <= tolerance and dist < best_dist:
                    best_dist = dist
                    best_pos = (sx, sy)
        return best_pos

    @staticmethod
    def verify_colors(screenshot, color_points, tolerance=5, scope=15):
        annotated = screenshot.copy().convert("RGBA")
        draw = ImageDraw.Draw(annotated)

        font = None
        font_paths = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc",
                       "C:/Windows/Fonts/arial.ttf"]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, 14)
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()

        results = []
        circle_radius = 10
        cross_size = 8

        for point in color_points:
            found_x, found_y = ColorVerifier.find_color_in_scope(
                screenshot, point.color_rgb, point.x, point.y, tolerance, scope)
            found = found_x >= 0 and found_y >= 0
            result = {
                "index": point.index, "found": found,
                "found_x": found_x if found else point.x,
                "found_y": found_y if found else point.y,
                "original_x": point.x, "original_y": point.y,
                "color": point.color_rgb
            }
            results.append(result)

            if found:
                color = (0, 255, 0, 255)
                draw.ellipse([found_x - circle_radius, found_y - circle_radius,
                               found_x + circle_radius, found_y + circle_radius],
                              outline=color, width=2)
                draw.line([found_x - cross_size, found_y, found_x + cross_size, found_y],
                           fill=color, width=1)
                draw.line([found_x, found_y - cross_size, found_x, found_y + cross_size],
                           fill=color, width=1)
                draw.text((found_x + circle_radius + 3, found_y - 7),
                           str(point.index), fill=(0, 255, 0, 255), font=font)
            else:
                color = (255, 0, 0, 255)
                draw.line([point.x - cross_size, point.y - cross_size,
                            point.x + cross_size, point.y + cross_size], fill=color, width=2)
                draw.line([point.x + cross_size, point.y - cross_size,
                            point.x - cross_size, point.y + cross_size], fill=color, width=2)
                draw.ellipse([point.x - circle_radius, point.y - circle_radius,
                               point.x + circle_radius, point.y + circle_radius],
                              outline=color, width=1)
                draw.text((point.x + circle_radius + 3, point.y - 7),
                           f"{point.index}✗", fill=(255, 50, 50, 255), font=font)

        return results, annotated

    def verify_async(self, screenshot, color_points):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)
        self._worker = VerifyWorker(screenshot, color_points, self.tolerance, self.search_scope)
        self._worker.finished.connect(self._on_verify_done)
        self._worker.error.connect(self._on_verify_error)
        self._worker.start()

    def _on_verify_done(self, results, annotated):
        self._last_results = results
        self._last_annotated = annotated
        self.verification_done.emit(results, annotated)

    def _on_verify_error(self, msg):
        self.verification_error.emit(msg)

    def save_and_open(self, annotated, directory=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if directory is None:
            directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        os.makedirs(directory, exist_ok=True)
        filename = f"verify_{timestamp}.png"
        filepath = os.path.join(directory, filename)
        annotated.save(filepath, "PNG")
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.run(["open", filepath])
            else:
                subprocess.run(["xdg-open", filepath])
        except Exception:
            pass
        return filepath
