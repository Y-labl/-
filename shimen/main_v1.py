import time
import os
import sys
import logging
import random
import pyautogui
import pygetwindow as gw
import cv2
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """配置管理类"""
    # 游戏窗口标题
    WINDOW_TITLE = "梦幻西游 ONLINE"
    
    # 图像识别配置
    MAX_ATTEMPTS = 50  # 最大尝试次数
    CONFIDENCE = 0.7  # 匹配阈值
    RETRY_WAIT = 0.2  # 重试间隔时间(秒)
    
    # 目录配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = "templates"
    
    # 模板图片路径
    TEMPLATES = {
        "HUASHENGSI": "huashengsi.png",  # 化生寺地图标识
        "MASTER": "master.png",  # 门派师傅
        "TASK": "task.png",  # 任务图标
        "SUBMIT": "submit.png"  # 提交任务
    }
    
    # 任务追踪区域配置
    TASK_TRACKING = {
        "LEFT": 650,  # 相对窗口左侧的偏移
        "TOP": 100,  # 相对窗口顶部的偏移
        "WIDTH": 150,  # 宽度
        "HEIGHT": 150  # 高度
    }
    
    @classmethod
    def get_template_path(cls, template_name):
        """获取模板图片路径"""
        if template_name in cls.TEMPLATES:
            return os.path.join(cls.BASE_DIR, cls.TEMPLATE_DIR, cls.TEMPLATES[template_name])
        return None

class WindowManager:
    """窗口管理类"""
    
    def __init__(self, window_title):
        self.window_title = window_title
        self.window = None
        self.window_rect = None
        self.client_rect = None
        self.border_offset = (0, 0)
        self.dpi_scale = 1
    
    def find_and_activate_window(self):
        """查找并激活窗口"""
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
            try:
                self.window.activate()
            except Exception as e:
                logger.warning(f"激活窗口时出错：{e}，继续执行")
            
            time.sleep(1)  # 等待窗口激活

            # 获取窗口位置和大小
            self.window_rect = (self.window.left, self.window.top, 
                               self.window.left + self.window.width, 
                               self.window.top + self.window.height)
            
            # 简化处理，使用窗口的整个区域作为客户区
            self.client_rect = (self.window.left, self.window.top, 
                               self.window.width, self.window.height)
            
            # 边框偏移设为(0, 0)
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
    
    def get_window_position(self):
        """获取窗口位置和尺寸"""
        if not self.window_rect:
            return None
        left, top, right, bottom = self.window_rect
        width = right - left
        height = bottom - top
        return (left, top, width, height)
    
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
    
    def capture_region(self, rel_left, rel_top, width, height):
        """在窗口内指定相对位置截图"""
        if not self.window:
            logger.error("未找到窗口，无法截图")
            return None

        # 获取基准坐标
        base_left, base_top, _, _ = self.client_rect
        logger.info(f"基于客户区坐标: ({base_left}, {base_top})")

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
            return screenshot
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return None
    
    def is_window_visible(self):
        """检查窗口是否可见"""
        if not self.window:
            return False
        return not self.window.isMinimized

class MouseController:
    """鼠标控制类"""
    
    def __init__(self, window_manager):
        self.window_manager = window_manager
        self.mouse_offset = (0, 0)  # 鼠标偏移量
    
    def calculate_mouse_offset(self):
        """计算鼠标偏移量"""
        # 梦幻西游窗口内鼠标会有随机偏移，这里模拟偏移量
        # 实际使用时需要根据具体情况调整
        self.mouse_offset = (random.randint(-5, 5), random.randint(-5, 5))
        logger.info(f"计算鼠标偏移量: {self.mouse_offset}")
    
    def move_to(self, x, y, relative=False):
        """移动鼠标到指定位置"""
        try:
            if relative:
                # 相对窗口的坐标
                left, top, _, _ = self.window_manager.client_rect
                abs_x = left + x
                abs_y = top + y
            else:
                abs_x = x
                abs_y = y
            
            # 应用鼠标偏移
            self.calculate_mouse_offset()
            abs_x += self.mouse_offset[0]
            abs_y += self.mouse_offset[1]
            
            # 移动鼠标
            pyautogui.moveTo(abs_x, abs_y, duration=0.5)
            logger.info(f"移动鼠标到: ({abs_x}, {abs_y})")
            return True
        except Exception as e:
            logger.error(f"移动鼠标时出错: {str(e)}")
            return False
    
    def click(self, x=None, y=None, relative=False):
        """点击指定位置"""
        try:
            if x is not None and y is not None:
                self.move_to(x, y, relative)
            
            # 模拟人工点击，添加随机延迟
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.click()
            logger.info("点击鼠标")
            return True
        except Exception as e:
            logger.error(f"点击鼠标时出错: {str(e)}")
            return False
    
    def press_key(self, key):
        """按下键盘按键"""
        try:
            pyautogui.press(key)
            logger.info(f"按下按键: {key}")
            return True
        except Exception as e:
            logger.error(f"按下按键时出错: {str(e)}")
            return False

class MapRecognizer:
    """地图识别类"""
    
    def __init__(self, window_manager):
        self.window_manager = window_manager
    
    def recognize_map(self):
        """识别当前地图"""
        try:
            # 截取窗口截图
            screenshot = self.window_manager.capture_window_screenshot()
            if screenshot is None:
                return "未知"
            
            # 尝试识别化生寺地图
            huashengsi_template = Config.get_template_path("HUASHENGSI")
            if huashengsi_template and os.path.exists(huashengsi_template):
                template = cv2.imread(huashengsi_template, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    # 转换截图为灰度
                    gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                    
                    # 模板匹配
                    result = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val >= Config.CONFIDENCE:
                        logger.info("识别到化生寺地图")
                        return "化生寺"
            
            logger.info("未识别到已知地图")
            return "未知"
        except Exception as e:
            logger.error(f"识别地图时出错: {str(e)}")
            return "未知"

class TaskAutomation:
    """任务自动化类"""
    
    def __init__(self):
        self.window_manager = WindowManager(Config.WINDOW_TITLE)
        self.mouse_controller = MouseController(self.window_manager)
        self.map_recognizer = MapRecognizer(self.window_manager)
    
    def run(self):
        """运行自动化脚本"""
        try:
            logger.info("开始执行梦幻西游师门任务自动化脚本")
            
            # 1. 查找并激活窗口
            logger.info("正在查找并激活游戏窗口...")
            if not self.window_manager.find_and_activate_window():
                logger.error("无法找到或激活游戏窗口，退出脚本")
                return
            
            # 2. 识别当前地图
            logger.info("正在识别当前地图...")
            current_map = self.map_recognizer.recognize_map()
            logger.info(f"当前地图: {current_map}")
            
            # 3. 如果不在化生寺，使用F8回师门
            if current_map != "化生寺":
                logger.info("不在化生寺，使用F8回师门...")
                self.mouse_controller.press_key('f8')
                time.sleep(3)  # 等待传送完成
            
            # 4. 识别师傅位置并点击
            logger.info("正在寻找门派师傅...")
            # 这里需要实现师傅位置识别，暂时使用固定坐标
            # 实际使用时需要根据截图和模板匹配来识别
            master_x, master_y = 400, 300  # 假设师傅在窗口内的坐标
            self.mouse_controller.move_to(master_x, master_y, relative=True)
            self.mouse_controller.click()
            time.sleep(1)
            
            # 5. 领取任务
            logger.info("正在领取师门任务...")
            # 这里需要实现领取任务的点击，暂时使用固定坐标
            task_x, task_y = 500, 350
            self.mouse_controller.move_to(task_x, task_y, relative=True)
            self.mouse_controller.click()
            time.sleep(1)
            
            # 6. 识别任务
            logger.info("正在识别任务...")
            # 截图任务追踪区域
            task_image = self.window_manager.capture_region(
                Config.TASK_TRACKING["LEFT"],
                Config.TASK_TRACKING["TOP"],
                Config.TASK_TRACKING["WIDTH"],
                Config.TASK_TRACKING["HEIGHT"]
            )
            if task_image:
                task_image.save("task_tracking.png")
                logger.info("任务追踪区域截图已保存")
            
            # 7. 执行任务（这里只是示例，实际需要根据任务类型执行不同操作）
            logger.info("正在执行任务...")
            # 模拟任务执行
            time.sleep(5)
            
            # 8. 回师门提交任务
            logger.info("任务完成，使用F8回师门...")
            self.mouse_controller.press_key('f8')
            time.sleep(3)
            
            # 9. 提交任务
            logger.info("正在提交任务...")
            # 点击师傅
            self.mouse_controller.move_to(master_x, master_y, relative=True)
            self.mouse_controller.click()
            time.sleep(1)
            
            # 点击提交任务
            submit_x, submit_y = 500, 400
            self.mouse_controller.move_to(submit_x, submit_y, relative=True)
            self.mouse_controller.click()
            time.sleep(1)
            
            logger.info("师门任务自动化脚本执行完毕")
            
        except Exception as e:
            logger.error(f"脚本执行过程中出错：{str(e)}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    automation = TaskAutomation()
    automation.run()
