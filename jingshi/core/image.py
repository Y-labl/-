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
    
    def find_image(self, screenshot, template_name):
        """在截图中查找模板图像"""
        template = self.load_template(template_name)
        if template is None:
            return None
        
        try:
            # 将PIL图像转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 检查匹配度
            if max_val < Config.CONFIDENCE_THRESHOLD:
                self.logger.warning(f"{template_name} 匹配度不足: {max_val}")
                return None
            
            # 计算中心点
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
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
