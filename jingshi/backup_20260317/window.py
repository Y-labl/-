import pygetwindow as gw
import pyautogui
import logging
from config.config import Config

class WindowManager:
    def __init__(self):
        self.window = None
        self.logger = logging.getLogger(__name__)
    
    def find_window(self):
        """查找游戏窗口"""
        windows = gw.getWindowsWithTitle(Config.WINDOW_TITLE)
        if not windows:
            self.logger.error(f"未找到标题为'{Config.WINDOW_TITLE}'的窗口")
            return False
        
        # 打印所有找到的窗口信息
        for i, window in enumerate(windows):
            self.logger.info(f"窗口 {i}: {window.title}, 位置: ({window.left}, {window.top}), 大小: ({window.width}, {window.height})")
        
        # 选择尺寸合理的窗口（宽度和高度都大于100）
        valid_windows = [w for w in windows if w.width > 100 and w.height > 100]
        if not valid_windows:
            self.logger.error("未找到尺寸合理的窗口")
            return False
        
        self.window = valid_windows[0]
        self.logger.info(f"选择窗口: {self.window.title}, 位置: ({self.window.left}, {self.window.top}), 大小: ({self.window.width}, {self.window.height})")
        return True
    
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
            self.logger.info(f"窗口位置: ({left}, {top}), 大小: ({width}, {height})")
            return (left, top, width, height)
        except Exception as e:
            self.logger.error(f"获取窗口矩形失败: {e}")
            return None
    
    def capture_window(self):
        """截图窗口内容"""
        rect = self.get_window_rect()
        if not rect:
            return None
        
        try:
            left, top, width, height = rect
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            self.logger.info("窗口截图成功")
            return screenshot
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None
