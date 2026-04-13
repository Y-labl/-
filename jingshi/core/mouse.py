import pyautogui
import time
import logging
from config.config import Config

class MouseController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 设置 pyautogui 为即时模式
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
    
    def move_to(self, x, y):
        """移动鼠标到指定位置（极速模式）"""
        try:
            pyautogui.moveTo(x, y, duration=0)
            self.logger.info(f"鼠标移动到：({x}, {y})")
            return True
        except Exception as e:
            self.logger.error(f"移动鼠标失败：{e}")
            return False
    
    def click(self):
        """点击鼠标（极速模式）"""
        try:
            pyautogui.click()
            self.logger.info("鼠标点击成功")
            return True
        except Exception as e:
            self.logger.error(f"点击鼠标失败：{e}")
            return False
    
    def move_to_target(self, window_left, window_top, target_x, target_y):
        """移动鼠标到窗口内的目标位置，考虑窗口偏移"""
        # 计算绝对坐标
        absolute_x = window_left + target_x
        absolute_y = window_top + target_y
        
        self.logger.info(f"移动鼠标到窗口内位置：({target_x}, {target_y})，绝对位置：({absolute_x}, {absolute_y})")
        return self.move_to(absolute_x, absolute_y)
    
    def click_target(self, window_left, window_top, target_x, target_y):
        """移动到目标位置并点击"""
        if self.move_to_target(window_left, window_top, target_x, target_y):
            return self.click()
        return False
