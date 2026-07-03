"""取色模块"""
import json
from PIL import Image
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass


@dataclass
class ColorPoint:
    index: int = 0
    x: int = 0
    y: int = 0
    color_rgb: tuple = (0, 0, 0)
    found: bool = None
    found_x: int = 0
    found_y: int = 0

    @property
    def hex_color(self):
        return "#{:02X}{:02X}{:02X}".format(*self.color_rgb)

    @property
    def rgb_str(self):
        return f"({self.color_rgb[0]}, {self.color_rgb[1]}, {self.color_rgb[2]})"

    def to_dict(self):
        return {"index": self.index, "x": self.x, "y": self.y,
                "rgb": list(self.color_rgb), "hex": self.hex_color}


class ColorPicker(QObject):
    point_added = Signal(ColorPoint)
    point_removed = Signal(int)
    list_cleared = Signal()
    list_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points = []
        self._next_index = 1

    def pick_color(self, x, y, image):
        try:
            if x < 0 or y < 0 or x >= image.width or y >= image.height:
                return None
            pixel = image.getpixel((x, y))
            if isinstance(pixel, tuple) and len(pixel) >= 3:
                rgb = tuple(pixel[:3])
            else:
                rgb = (pixel, pixel, pixel)
            point = ColorPoint(index=self._next_index, x=x, y=y, color_rgb=rgb)
            self._points.append(point)
            self._next_index += 1
            self.point_added.emit(point)
            self.list_changed.emit()
            return point
        except Exception as e:
            print(f"取色失败: {e}")
            return None

    def remove_selected(self, indices):
        self._points = [p for p in self._points if p.index not in indices]
        self.list_changed.emit()

    def clear_all(self):
        self._points.clear()
        self._next_index = 1
        self.list_cleared.emit()
        self.list_changed.emit()

    def get_points(self):
        return list(self._points)

    def count(self):
        return len(self._points)

    def to_json(self):
        return json.dumps([p.to_dict() for p in self._points], ensure_ascii=False, indent=2)

    def to_csv(self):
        lines = ["序号,x,y,R,G,B,HEX"]
        for p in self._points:
            lines.append(f"{p.index},{p.x},{p.y},{p.color_rgb[0]},{p.color_rgb[1]},{p.color_rgb[2]},{p.hex_color}")
        return "\n".join(lines)

    def parse_from_clipboard(self, text):
        text = text.strip()
        points = []
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        rgb = tuple(item.get("rgb", [0, 0, 0])[:3])
                        point = ColorPoint(index=self._next_index, x=item.get("x", 0),
                                            y=item.get("y", 0), color_rgb=rgb)
                        points.append(point)
                        self._next_index += 1
                if points:
                    self._points.extend(points)
                    self.list_changed.emit()
                    return points
        except json.JSONDecodeError:
            pass

        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("序号"):
                continue
            parts = line.replace(" ", "").split(",")
            if len(parts) >= 6:
                try:
                    x, y = int(parts[1]), int(parts[2])
                    r, g, b = int(parts[3]), int(parts[4]), int(parts[5])
                    point = ColorPoint(index=self._next_index, x=x, y=y, color_rgb=(r, g, b))
                    points.append(point)
                    self._next_index += 1
                except (ValueError, IndexError):
                    continue
        if points:
            self._points.extend(points)
            self.list_changed.emit()
        return points

    def update_verification_results(self, results):
        for result in results:
            idx = result.get("index")
            for p in self._points:
                if p.index == idx:
                    p.found = result.get("found", False)
                    p.found_x = result.get("found_x", 0)
                    p.found_y = result.get("found_y", 0)
                    break
        self.list_changed.emit()

    def reset_verification(self):
        for p in self._points:
            p.found = None
            p.found_x = 0
            p.found_y = 0
        self.list_changed.emit()
