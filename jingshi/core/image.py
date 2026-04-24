import cv2
import numpy as np
import os
import sys
import logging
from config.config import Config


def get_resource_path(relative_path):
    """资源文件绝对路径：打包后优先 exe 同目录（便于热更新），其次 _MEIPASS，最后源码目录。"""
    rel = relative_path.replace("/", os.sep)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        side = os.path.join(exe_dir, rel)
        if os.path.isfile(side):
            return os.path.normpath(side)
        if hasattr(sys, "_MEIPASS"):
            bundled = os.path.join(sys._MEIPASS, rel)
            return os.path.normpath(bundled)
        return os.path.normpath(side)
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", rel)
    return os.path.normpath(base)

class ImageRecognizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._gray_template_cache = {}
        self._template_cache = {}
        self._gray_template_miss_logged = set()

    def template_file_exists(self, config_key):
        """Config.TEMPLATES 中键对应文件是否存在（任意解析路径）。"""
        rel = Config.TEMPLATES.get(config_key)
        if not rel:
            return False
        return os.path.isfile(get_resource_path(rel))

    def load_template_grayscale(self, config_key):
        """按 TEMPLATES 键加载灰度 numpy 图（Pillow，兼容中文路径）；成功则缓存。"""
        if config_key in self._gray_template_cache:
            return self._gray_template_cache[config_key]

        rel = Config.TEMPLATES.get(config_key)
        if not rel:
            self.logger.error(f"配置中无模板键：{config_key}")
            return None

        full_path = get_resource_path(rel)
        if not os.path.isfile(full_path):
            if config_key not in self._gray_template_miss_logged:
                self.logger.error(
                    f"缺少模板文件 {rel}（已查找：{full_path}）。"
                    f"请将游戏内「120级」小图存为 {rel}，放在 exe 同目录或 jingshi 根目录后重试/重打包。"
                )
                self._gray_template_miss_logged.add(config_key)
            return None

        try:
            from PIL import Image

            pil_image = Image.open(full_path).convert("L")
            arr = np.array(pil_image)
            self._gray_template_cache[config_key] = arr
            self.logger.info(f"灰度模板已加载：{config_key} <- {full_path}")
            return arr
        except Exception as e:
            self.logger.error(f"加载灰度模板失败 {full_path}：{e}")
            return None

    def load_template_gray(self, template_name):
        """加载模板灰度图（缓存），用于更快的 matchTemplate。"""
        if template_name in self._gray_template_cache:
            return self._gray_template_cache[template_name]

        template_bgr = self.load_template(template_name)
        if template_bgr is None:
            return None

        try:
            template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
            self._gray_template_cache[template_name] = template_gray
            return template_gray
        except Exception as e:
            self.logger.error(f"转换模板灰度失败 {template_name}: {e}")
            return None

    def clear_template_cache(self):
        self._gray_template_cache.clear()
        self._template_cache.clear()
        self._gray_template_miss_logged.clear()
    
    def load_template(self, template_name):
        """加载模板图像（缓存 BGR numpy，避免重复 I/O 与转换）"""
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        template_path = Config.TEMPLATES.get(template_name)
        if not template_path:
            self.logger.error(f"未找到模板：{template_name}")
            return None
        
        # 使用支持打包的资源路径
        full_path = get_resource_path(template_path)
        self.logger.info(f"模板完整路径：{full_path}")
        
        if not os.path.exists(full_path):
            self.logger.error(f"模板文件不存在：{full_path}")
            return None
        
        try:
            # 尝试使用 Pillow 加载图像
            from PIL import Image
            pil_image = Image.open(full_path)
            self.logger.info(f"Pillow 加载成功：{full_path}")
            
            # 转换为 OpenCV 格式
            template = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            self._template_cache[template_name] = template
            self.logger.info(f"模板加载成功：{full_path}")
            return template
        except Exception as e:
            self.logger.error(f"加载模板失败：{e}")
            return None
    
    def _resolve_search_roi(self, image_w, image_h, template_name):
        """将 Config.TEMPLATE_SEARCH_REGIONS[template_name] 解析为像素 ROI。"""
        roi = getattr(Config, "TEMPLATE_SEARCH_REGIONS", {}).get(template_name)
        if not roi:
            return None

        try:
            x, y, w, h = roi
        except Exception:
            self.logger.warning(f"TEMPLATE_SEARCH_REGIONS[{template_name}] 配置无效：{roi}")
            return None

        # 全 float 且在 0~1：按比例
        if all(isinstance(v, float) for v in (x, y, w, h)):
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0):
                return None
            px = int(x * image_w)
            py = int(y * image_h)
            pw = int(w * image_w)
            ph = int(h * image_h)
        else:
            # 含 int：按像素
            px, py, pw, ph = int(x), int(y), int(w), int(h)

        if pw <= 0 or ph <= 0:
            return None

        px = max(0, min(px, image_w - 1))
        py = max(0, min(py, image_h - 1))
        pw = max(1, min(pw, image_w - px))
        ph = max(1, min(ph, image_h - py))
        return (px, py, pw, ph)

    def find_image(self, screenshot, template_name):
        """在截图中查找模板图像（灰度匹配 + 可选 ROI 提速）。"""
        template_gray = self.load_template_gray(template_name)
        if template_gray is None:
            return None

        try:
            # PIL -> ndarray（RGB）-> 灰度。灰度匹配比 BGR 更快。
            screenshot_rgb = np.asarray(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2GRAY)

            h_img, w_img = screenshot_gray.shape[:2]
            roi = self._resolve_search_roi(w_img, h_img, template_name)

            if roi:
                x, y, w, h = roi
                search_gray = screenshot_gray[y : y + h, x : x + w]
                roi_offset_x, roi_offset_y = x, y
            else:
                search_gray = screenshot_gray
                roi_offset_x, roi_offset_y = 0, 0

            # 模板必须不大于搜索区域
            th, tw = template_gray.shape[:2]
            sh, sw = search_gray.shape[:2]
            if th > sh or tw > sw:
                return None

            result = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val < Config.CONFIDENCE_THRESHOLD:
                return None

            center_x = roi_offset_x + max_loc[0] + tw // 2
            center_y = roi_offset_y + max_loc[1] + th // 2
            self.logger.info(f"找到 {template_name} 在位置: ({center_x}, {center_y})，匹配度: {max_val}")
            return (center_x, center_y)
        except Exception as e:
            self.logger.error(f"查找图像失败: {e}")
            return None
    
    def find_image_with_retry(self, screenshot_provider, template_name, max_attempts=None):
        """带重试的图像查找

        :param screenshot_provider: PIL.Image 或 callable（每次重试时重新截图）
        """
        if max_attempts is None:
            max_attempts = Config.MAX_ATTEMPTS

        for attempt in range(max_attempts):
            self.logger.info(f"尝试查找 {template_name} (第 {attempt + 1}/{max_attempts} 次)")
            screenshot = screenshot_provider() if callable(screenshot_provider) else screenshot_provider
            if screenshot is None:
                self.logger.warning(f"第 {attempt + 1} 次截图为空，继续重试")
                continue
            result = self.find_image(screenshot, template_name)
            if result:
                return result

        self.logger.error(f"在 {max_attempts} 次尝试后未找到 {template_name}")
        return None
