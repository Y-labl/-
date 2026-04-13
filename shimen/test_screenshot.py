import time
import os
import sys
import logging
import pyautogui
import pygetwindow as gw

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config

def test_screenshot_position():
    """测试截图位置"""
    try:
        logger.info("开始测试截图位置")
        
        # 查找窗口
        window_title = Config.WINDOW_TITLE
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            logger.error(f"未找到标题为 '{window_title}' 的窗口")
            return
        
        window = windows[0]
        
        # 检查并恢复最小化窗口
        if window.isMinimized:
            window.restore()
        
        # 激活窗口
        window.activate()
        time.sleep(1)  # 等待窗口完全激活

        # 获取窗口在屏幕上的坐标
        left = window.left
        top = window.top
        right = left + window.width
        bottom = top + window.height
        logger.info(f"窗口坐标：左{left}, 上{top}, 右{right}, 下{bottom}")
        logger.info(f"窗口宽度：{window.width}, 高度：{window.height}")

        # 测试1：截取整个窗口
        logger.info("测试1：截取整个窗口")
        whole_window_path = "test_screenshots/whole_window.png"
        os.makedirs(os.path.dirname(whole_window_path), exist_ok=True)
        screenshot = pyautogui.screenshot(region=(left, top, window.width, window.height))
        screenshot.save(whole_window_path)
        logger.info(f"整个窗口截图已保存至 {whole_window_path}")

        # 测试2：截取任务追踪区域（当前配置）
        logger.info("测试2：截取任务追踪区域（当前配置）")
        task_left = left + Config.TASK_TRACKING["LEFT"]
        task_top = top + Config.TASK_TRACKING["TOP"]
        task_width = Config.TASK_TRACKING["WIDTH"]
        task_height = Config.TASK_TRACKING["HEIGHT"]
        logger.info(f"任务追踪区域坐标：左{task_left}, 上{task_top}, 宽度{task_width}, 高度{task_height}")
        
        task_path = "test_screenshots/task_tracking.png"
        screenshot = pyautogui.screenshot(region=(task_left, task_top, task_width, task_height))
        screenshot.save(task_path)
        logger.info(f"任务追踪区域截图已保存至 {task_path}")

        # 测试3：截取窗口右上角区域（可能的任务追踪区域）
        logger.info("测试3：截取窗口右上角区域（可能的任务追踪区域）")
        test_left = right - 200  # 从窗口右侧向左200像素
        test_top = top + 50  # 从窗口顶部向下50像素
        test_width = 180
        test_height = 150
        logger.info(f"测试区域坐标：左{test_left}, 上{test_top}, 宽度{test_width}, 高度{test_height}")
        
        test_path = "test_screenshots/test_area.png"
        screenshot = pyautogui.screenshot(region=(test_left, test_top, test_width, test_height))
        screenshot.save(test_path)
        logger.info(f"测试区域截图已保存至 {test_path}")

        # 测试4：调整配置参数后的任务追踪区域
        logger.info("测试4：调整配置参数后的任务追踪区域")
        adjusted_left = right - 250  # 从窗口右侧向左250像素
        adjusted_top = top + 100  # 从窗口顶部向下100像素
        adjusted_width = 200
        adjusted_height = 120
        logger.info(f"调整后区域坐标：左{adjusted_left}, 上{adjusted_top}, 宽度{adjusted_width}, 高度{adjusted_height}")
        
        adjusted_path = "test_screenshots/adjusted_area.png"
        screenshot = pyautogui.screenshot(region=(adjusted_left, adjusted_top, adjusted_width, adjusted_height))
        screenshot.save(adjusted_path)
        logger.info(f"调整后区域截图已保存至 {adjusted_path}")

        logger.info("截图位置测试完成，请查看test_screenshots目录下的截图文件")
        logger.info("根据截图结果，您可能需要调整config.py中的TASK_TRACKING配置")
        
    except Exception as e:
        logger.error(f"测试过程中出错：{e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_screenshot_position()
