import time
import os
import sys
import logging
import pyautogui
import pygetwindow as gw

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 窗口标题
WINDOW_TITLE = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"

def find_and_activate_window():
    """查找并激活游戏窗口"""
    try:
        # 查找窗口
        windows = gw.getWindowsWithTitle(WINDOW_TITLE)
        if not windows:
            logger.error(f"未找到窗口: {WINDOW_TITLE}")
            return None
        
        window = windows[0]
        
        # 检查并恢复最小化窗口
        if window.isMinimized:
            window.restore()
        
        # 激活窗口
        window.activate()
        time.sleep(0.5)  # 等待窗口激活

        logger.info(f"窗口已激活，位置: ({window.left}, {window.top})，大小: {window.width}x{window.height}")
        return window
    except Exception as e:
        logger.error(f"查找和激活窗口时出错: {str(e)}")
        return None

def main():
    """主程序"""
    logger.info("开始执行简化版测试脚本")
    
    # 查找并激活窗口
    window = find_and_activate_window()
    if not window:
        logger.error("无法找到或激活游戏窗口，退出脚本")
        return
    
    # 模拟鼠标移动
    logger.info("模拟鼠标移动...")
    center_x = window.left + window.width // 2
    center_y = window.top + window.height // 2
    pyautogui.moveTo(center_x, center_y, duration=1.0)
    logger.info(f"鼠标已移动到窗口中心: ({center_x}, {center_y})")
    
    # 模拟点击
    logger.info("模拟鼠标点击...")
    pyautogui.click()
    logger.info("鼠标点击完成")
    
    logger.info("简化版测试脚本执行完毕")

if __name__ == "__main__":
    main()
