import pyautogui
import time
import cv2
import numpy as np
from PIL import ImageGrab
import win32gui
import win32con
import os


class WindowManager:
    """窗口管理类，负责窗口查找、激活和截图"""

    def __init__(self, window_title):
        self.window_title = window_title
        self.window_handle = None
        self.window_rect = None

    def find_and_activate_window(self):
        """查找并激活指定标题的窗口"""
        self.window_handle = win32gui.FindWindow(None, self.window_title)
        if self.window_handle == 0:
            print(f"未找到窗口: {self.window_title}")
            return False

        # 确保窗口是可见的
        win32gui.ShowWindow(self.window_handle, win32con.SW_SHOW)
        # 激活窗口
        win32gui.SetForegroundWindow(self.window_handle)
        time.sleep(0.5)  # 等待窗口激活

        # 获取窗口位置和大小
        self.window_rect = win32gui.GetWindowRect(self.window_handle)
        return True

    def capture_window_screenshot(self):
        """截取窗口内容"""
        if not self.window_handle or not self.window_rect:
            print("窗口未初始化，请先调用 find_and_activate_window")
            return None

        left, top, right, bottom = self.window_rect
        width = right - left
        height = bottom - top

        # 截取窗口区域
        screenshot = np.array(ImageGrab.grab(bbox=(left, top, right, bottom)))
        return cv2.cvtColor(screenshot, cv2.COLOR_RGBA2RGB)


def locate_image_on_screen(window_manager, template_path, confidence=0.8):
    """
    在指定窗口的屏幕上查找模板图像的位置。

    :param window_manager: WindowManager 实例
    :param template_path: 模板图像的路径
    :param confidence: 匹配相似度阈值，默认为 0.8
    :return: 匹配到的区域 (x, y) 或 None 如果未找到
    """
    # 截取窗口的屏幕截图
    window_screenshot = window_manager.capture_window_screenshot()
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
        window_left, window_top, _, _ = window_manager.window_rect
        screen_x = window_left + center_x
        screen_y = window_top + center_y

        return (screen_x, screen_y)
    else:
        return None


# 模拟按键和鼠标点击
def press_key(key):
    """模拟按下并释放键盘按键"""
    pyautogui.press(key)
    time.sleep(0.1)  # 短暂等待按键生效


def click_position(x, y):
    """模拟鼠标点击指定位置"""
    pyautogui.moveTo(x, y, duration=0.2)  # 平滑移动
    pyautogui.click()
    time.sleep(0.2)  # 点击后等待


# 持续查找图像直到找到或超时
def find_image_with_retry(window_manager, template_path, max_attempts=50, confidence=0.8):
    """持续查找图像，直到找到或达到最大尝试次数"""
    for attempt in range(max_attempts):
        print(f"尝试查找图像 {attempt + 1}/{max_attempts}...")
        try:
            position = locate_image_on_screen(window_manager, template_path, confidence)
            if position:
                return position
        except Exception as e:
            print(f"查找图像时出错: {e}")

        time.sleep(0.2)  # 等待一段时间再重试

    print(f"达到最大尝试次数，未找到匹配图像")
    return None


# 主函数
def main():
    # 配置参数
    window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"  # 请替换为实际游戏窗口标题
    # 使用相对路径，确保图片在正确的目录下
    base_dir = os.path.dirname(os.path.abspath(__file__))
    door_image_path = "../images/sm.png"
    portal_image_path = "../images/ca.png"

    # 检查文件是否存在
    if not os.path.exists(door_image_path):
        print(f"师门传送口图片不存在: {door_image_path}")
        return

    if not os.path.exists(portal_image_path):
        print(f"传送口图片不存在: {portal_image_path}")
        return

    # 创建窗口管理器
    window_manager = WindowManager(window_title)

    # 1. 识别并绑定窗口
    if not window_manager.find_and_activate_window():
        return

    # 2. 模拟按下F1键，等待500毫秒
    print("按下 F1 键")
    press_key('f1')
    time.sleep(0.5)

    # 3. 按下Tab键，识别并点击门口位置，再按Tab键
    print("按下 Tab 键")
    press_key('tab')

    # 识别门口位置并点击，增加重试机制
    print("正在识别化生寺师门传送口...")
    door_position = find_image_with_retry(window_manager, door_image_path, confidence=0.7)
    if door_position:
        print(f"找到化生寺师门传送口位置: {door_position}")
        click_position(*door_position)

        # 再次按下Tab键
        print("按下 Tab 键")
        press_key('tab')
    else:
        print("未找到化生寺师门传送口，退出脚本")
        return

    # 4. 等待5秒，识别传送口并点击
    print("等待人物移动到化生寺师门传送口...")
    time.sleep(5)

    print("正在识别化生寺传送口...")
    portal_position = find_image_with_retry(window_manager, portal_image_path, confidence=0.7)
    if portal_position:
        print(f"找到化生寺传送口位置: {portal_position}")
        click_position(*portal_position)
        print("已点击化生寺传送口，进入房间")
    else:
        print("未找到化生寺传送口，退出脚本")


if __name__ == "__main__":
    main()