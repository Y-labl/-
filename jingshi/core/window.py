import pygetwindow as gw
import pyautogui
import logging
from config.config import Config

# 配置 pyautogui 使用更快的截图方法
pyautogui.PAUSE = 0

class WindowManager:
    def __init__(self):
        self.window = None
        self.logger = logging.getLogger(__name__)
    
    def find_window_by_title(self, window_title):
        """根据指定的窗口标题查找游戏窗口"""
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            self.logger.error(f"未找到标题为'{window_title}'的窗口")
            return False
        
        # 选择尺寸合理的窗口（宽度和高度都大于 100）
        valid_windows = [w for w in windows if w.width > 100 and w.height > 100]
        if not valid_windows:
            self.logger.error("未找到尺寸合理的窗口")
            return False
        
        self.window = valid_windows[0]
        return True
    
    def find_window(self):
        """查找游戏窗口（使用配置文件中的标题）"""
        return self.find_window_by_title(Config.WINDOW_TITLE)
    
    def activate_window(self):
        """激活窗口"""
        if not self.window:
            self.logger.error("窗口未找到，无法激活")
            return False
        
        try:
            self.window.activate()
            self.logger.info("窗口已激活")
            return True
        except Exception as e:
            self.logger.error(f"激活窗口失败: {e}")
            return False
    
    def get_window_rect(self):
        """获取窗口矩形区域"""
        if not self.window:
            self.logger.error("窗口未找到，无法获取矩形区域")
            return None
        
        try:
            left, top, width, height = self.window.left, self.window.top, self.window.width, self.window.height
            return (left, top, width, height)
        except Exception as e:
            self.logger.error(f"获取窗口矩形失败：{e}")
            return None
    
    def capture_window(self, region=None):
        """截图窗口内容

        :param region: 可选的截图区域 (x, y, width, height)，不传则截取整个窗口
        :return: PIL Image 对象或 None
        """
        rect = self.get_window_rect()
        if not rect:
            return None

        try:
            left, top, width, height = rect

            if region:
                region_abs = (
                    left + region[0],
                    top + region[1],
                    region[2],
                    region[3],
                )
                return pyautogui.screenshot(region=region_abs)

            return pyautogui.screenshot(region=(left, top, width, height))
        except Exception as e:
            self.logger.error(f"截图失败：{e}")
            return None
