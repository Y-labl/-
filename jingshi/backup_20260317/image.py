import cv2
import numpy as np
import os
import logging
from config.config import Config

class ImageRecognizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_template(self, template_name):
        """加载模板图像"""
        template_path = Config.TEMPLATES.get(template_name)
        if not template_path:
            self.logger.error(f"未找到模板: {template_name}")
            return None
        
        # 打印当前工作目录和模板路径
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, template_path)
        self.logger.info(f"当前工作目录: {current_dir}")
        self.logger.info(f"模板完整路径: {full_path}")
        
        if not os.path.exists(full_path):
            self.logger.error(f"模板文件不存在: {full_path}")
            return None
        
        try:
            # 尝试使用Pillow加载图像
            from PIL import Image
            pil_image = Image.open(full_path)
            self.logger.info(f"Pillow加载成功: {full_path}")
            
            # 转换为OpenCV格式
            template = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            self.logger.info(f"模板加载成功: {full_path}")
            return template
        except Exception as e:
            self.logger.error(f"加载模板失败: {e}")
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
    
    def find_image_with_retry(self, screenshot, template_name, max_attempts=None):
        """带重试的图像查找"""
        if max_attempts is None:
            max_attempts = Config.MAX_ATTEMPTS
        
        for attempt in range(max_attempts):
            self.logger.info(f"尝试查找 {template_name} (第 {attempt + 1}/{max_attempts} 次)")
            result = self.find_image(screenshot, template_name)
            if result:
                return result
        
        self.logger.error(f"在 {max_attempts} 次尝试后未找到 {template_name}")
        return None
