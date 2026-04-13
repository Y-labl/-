import logging
from PIL import Image
import pyautogui
import time
import os
import cv2
import numpy as np
import pygetwindow as gw

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WindowManager:
    """窗口管理类，负责窗口查找、激活和截图"""

    def __init__(self, window_title=None):
        self.window_title = window_title
        self.window = None  # 窗口对象
        self.window_rect = None  # 窗口在屏幕上的坐标 (left, top, right, bottom)
        self.client_rect = None  # 窗口客户区坐标
        self.border_offset = (0, 0)  # 窗口边框和标题栏的偏移量
        self.dpi_scale = 1  # DPI缩放比例

    def find_and_activate_window(self) -> bool:
        """查找并激活指定标题的窗口"""
        try:
            # 查找窗口
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                logger.error(f"未找到窗口: {self.window_title}")
                return False
            
            self.window = windows[0]
            
            # 检查并恢复最小化窗口
            if self.window.isMinimized:
                self.window.restore()
            
            # 激活窗口
            self.window.activate()
            time.sleep(0.5)  # 等待窗口激活

            # 获取窗口位置和大小
            self.window_rect = (self.window.left, self.window.top, self.window.left + self.window.width, self.window.top + self.window.height)
            
            # 简化处理，使用窗口的整个区域作为客户区
            self.client_rect = (self.window.left, self.window.top, self.window.width, self.window.height)
            
            # 边框偏移设为(0, 0)，因为pygetwindow不提供客户区信息
            self.border_offset = (0, 0)

            # 尝试获取DPI缩放比例
            try:
                screen_width, screen_height = pyautogui.size()
                self.dpi_scale = screen_width / 96  # 假设96 DPI为基准
            except Exception as e:
                logger.error(f"获取DPI缩放比例失败，使用默认值1，错误: {e}")
                self.dpi_scale = 1

            logger.info(f"激活后窗口位置和大小: {self.window_rect}")
            logger.info(f"客户区位置和大小: {self.client_rect}")
            logger.info(f"窗口边框偏移: {self.border_offset}")
            logger.info(f"DPI缩放比例: {self.dpi_scale}")

            return True
        except Exception as e:
            logger.error(f"查找和激活窗口时出错: {str(e)}")
            return False

    def capture_window_screenshot(self):
        """截取整个窗口的截图并返回OpenCV格式的图像"""
        if not self.window:
            logger.error("未找到窗口，无法截图")
            return None

        try:
            # 获取窗口在屏幕上的坐标
            left, top, right, bottom = self.window_rect
            width = right - left
            height = bottom - top

            # 截图
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            # 转换为OpenCV格式
            screenshot_np = np.array(screenshot)
            return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return None

    def get_window_position(self):
        """获取窗口位置和尺寸"""
        if not self.window_rect:
            return None
        left, top, right, bottom = self.window_rect
        width = right - left
        height = bottom - top
        return (left, top, width, height)

    def capture_region(self, rel_left, rel_top, width, height, use_client_area=False):
        """在窗口内指定相对位置截图"""
        if not self.window:
            logger.error("未找到窗口，无法截图")
            return None

        if not self.is_window_visible():
            logger.warning("窗口不可见，可能影响截图结果")

        # 获取基准坐标（整个窗口/客户区）
        if use_client_area and self.client_rect:
            base_left, base_top, _, _ = self.client_rect
            logger.info(f"基于客户区坐标: ({base_left}, {base_top})")
        else:
            base_left, base_top, _, _ = self.window_rect
            logger.info(f"基于整个窗口坐标: ({base_left}, {base_top})")

        # 应用DPI缩放
        rel_left = int(rel_left / self.dpi_scale)
        rel_top = int(rel_top / self.dpi_scale)
        width = int(width / self.dpi_scale)
        height = int(height / self.dpi_scale)

        # 计算绝对坐标
        abs_left = base_left + rel_left
        abs_top = base_top + rel_top
        logger.debug(f"绝对坐标: ({abs_left}, {abs_top}), 尺寸: {width}x{height}")

        try:
            # 截图
            screenshot = pyautogui.screenshot(region=(abs_left, abs_top, width, height))
            return Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return None

    def is_window_visible(self) -> bool:
        """检查窗口是否可见"""
        if not self.window:
            return False
        return not self.window.isMinimized

    def locate_image_on_screen(self, template_path, confidence=0.8, save_result=False):
        """在窗口中定位图像"""
        # 截取窗口的屏幕截图
        window_screenshot = self.capture_window_screenshot()
        if window_screenshot is None:
            raise ValueError("无法截取窗口截图")

        screen_gray = cv2.cvtColor(window_screenshot, cv2.COLOR_BGR2GRAY)

        # 读取模板图像
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise FileNotFoundError(f"无法找到模板图像: {template_path}")

        # 获取模板图像的宽度和高度
        template_height, template_width = template.shape

        # 使用模板匹配找到图像位置
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            top_left = max_loc
            center_x = top_left[0] + template_width // 2
            center_y = top_left[1] + template_height // 2

            # 转换为屏幕坐标，考虑窗口边框和标题栏的偏移
            window_left, window_top, _, _ = self.window_rect
            screen_x = window_left + center_x
            screen_y = window_top + center_y

            # 返回相对坐标和绝对坐标
            return (center_x, center_y, template_width, template_height, window_left, window_top)
        else:
            return None
