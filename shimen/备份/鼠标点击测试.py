import unittest
import pyautogui
import time
import cv2
import numpy as np
from PIL import ImageGrab
import win32gui
import win32con
import os
import math


class WindowManager:
    """窗口管理类，负责窗口查找、激活和截图"""

    def __init__(self, window_title):
        self.window_title = window_title
        self.window_handle = None
        self.window_rect = None
        self.client_rect = None
        self.border_offset = (0, 0)  # 窗口边框和标题栏的偏移量
        self.dpi_scale = 1  # 用于处理DPI缩放，初始设为1

    def find_and_activate_window(self):
        """查找并激活指定标题的窗口"""
        self.window_handle = win32gui.FindWindow(None, self.window_title)
        if self.window_handle == 0:
            print(f"未找到窗口: {self.window_title}")
            return False

        # 检查并恢复最小化窗口
        if win32gui.IsIconic(self.window_handle):
            win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)

        win32gui.ShowWindow(self.window_handle, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(self.window_handle)
        time.sleep(0.5)  # 等待窗口激活

        # 获取窗口位置和大小（包括边框和标题栏）
        self.window_rect = win32gui.GetWindowRect(self.window_handle)

        # 获取客户区位置和大小（不包括边框和标题栏）
        self.client_rect = win32gui.GetClientRect(self.window_handle)
        client_left, client_top = win32gui.ClientToScreen(self.window_handle, (0, 0))

        # 计算边框和标题栏的偏移量
        self.border_offset = (
            client_left - self.window_rect[0],
            client_top - self.window_rect[1]
        )

        # 尝试获取DPI缩放比例（简单示例，实际可能更复杂）
        try:
            dpi_scale_x, dpi_scale_y = pyautogui.size() / (96, 96)
            self.dpi_scale = max(dpi_scale_x, dpi_scale_y)
        except:
            print("获取DPI缩放比例失败，使用默认值1")

        print(f"激活后窗口位置和大小: {self.window_rect}")
        print(f"客户区位置和大小: ({client_left}, {client_top}, {self.client_rect[2]}, {self.client_rect[3]})")
        print(f"窗口边框偏移: {self.border_offset}")
        print(f"DPI缩放比例: {self.dpi_scale}")

        return True

    def capture_window_screenshot(self):
        """截取窗口客户区内容（不包括边框和标题栏）"""
        if not self.window_handle or not self.window_rect:
            print("窗口未初始化，请先调用 find_and_activate_window")
            return None

        # 使用客户区坐标进行截图
        client_left, client_top = win32gui.ClientToScreen(self.window_handle, (0, 0))
        client_right = client_left + self.client_rect[2]
        client_bottom = client_top + self.client_rect[3]

        screenshot = np.array(ImageGrab.grab(bbox=(client_left, client_top, client_right, client_bottom)))
        print(f"截图形状: {screenshot.shape}")

        # 确保截图是3通道(BGR)格式
        if len(screenshot.shape) == 3:
            if screenshot.shape[2] == 4:  # 如果是RGBA格式，转换为BGR
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGBA2BGR)
            elif screenshot.shape[2] != 3:
                print(f"截图通道数异常: {screenshot.shape[2]}")
                return None
        else:
            print(f"截图维度异常: {len(screenshot.shape)}")
            return None

        # 保存截图用于调试
        cv2.imwrite(f"screenshot_{int(time.time())}.png", screenshot)
        return screenshot


def locate_image_on_screen(window_manager, template_path, confidence=0.8, save_result=False):
    """
    在指定窗口的屏幕上查找模板图像的位置。
    返回值：屏幕坐标(x, y)，或None
    """
    # 截取窗口的屏幕截图（客户区）
    window_screenshot = window_manager.capture_window_screenshot()
    if window_screenshot is None:
        raise ValueError("无法截取窗口截图")

    # 转换为灰度图进行匹配
    screen_gray = cv2.cvtColor(window_screenshot, cv2.COLOR_BGR2GRAY)

    # 读取模板图像（以灰度模式）
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"无法找到模板图像: {template_path}")

    # 获取模板图像的宽度和高度
    template_height, template_width = template.shape

    # 使用模板匹配找到图像位置
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"模板匹配结果：最大相似度值 {max_val:.6f}，阈值 {confidence}")

    # 保存匹配结果图像用于调试
    if save_result:
        result_visual = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        cv2.imwrite(f"match_result_{int(time.time())}.png", result_visual)

    if max_val >= confidence:
        top_left = max_loc
        center_x = top_left[0] + template_width // 2
        center_y = top_left[1] + template_height // 2

        # 转换为屏幕坐标，考虑窗口边框和标题栏的偏移以及DPI缩放
        client_left, client_top = win32gui.ClientToScreen(window_manager.window_handle, (0, 0))
        screen_x = client_left + center_x * window_manager.dpi_scale
        screen_y = client_top + center_y * window_manager.dpi_scale
        print(f"识别到的目标位置 - 客户区坐标: ({center_x}, {center_y})")
        print(f"识别到的目标位置 - 屏幕坐标: ({screen_x}, {screen_y})")

        # 可视化匹配位置
        if save_result:
            screenshot_color = cv2.cvtColor(screen_gray, cv2.COLOR_GRAY2BGR)
            cv2.circle(screenshot_color, (center_x, center_y), 5, (0, 0, 255), -1)
            cv2.rectangle(screenshot_color, top_left,
                          (top_left[0] + template_width, top_left[1] + template_height),
                          (0, 255, 0), 2)
            cv2.imwrite(f"match_location_{int(time.time())}.png", screenshot_color)

        return (screen_x, screen_y)
    else:
        return None


# 模拟按键和鼠标点击
def press_key(key):
    """模拟按下并释放键盘按键"""
    pyautogui.press(key)
    time.sleep(0.1)  # 短暂等待按键生效


def click_position(x, y, click_type='left', click_error=3, max_adjustments=10):
    """模拟鼠标点击指定位置，带微调功能"""
    print(f"尝试点击位置: ({x}, {y})")

    # 记录当前鼠标位置
    current_x, current_y = pyautogui.position()

    # 计算目标坐标和当前鼠标坐标的距离
    distance = math.sqrt((x - current_x) ** 2 + (y - current_y) ** 2)
    print(f"初始距离目标位置: {distance:.2f} 像素")

    # 自研鼠标偏移算法（根据距离调整步长）
    step_size = 1
    while distance > click_error and max_adjustments > 0:
        dx = x - current_x
        dy = y - current_y
        move_x = current_x + dx * step_size
        move_y = current_y + dy * step_size

        # 限制鼠标移动范围在窗口内（假设窗口坐标为window_rect）
        window_rect = win32gui.GetWindowRect(win32gui.GetForegroundWindow())
        move_x = max(window_rect[0], min(move_x, window_rect[2]))
        move_y = max(window_rect[1], min(move_y, window_rect[3]))

        print(f"微调: 从 ({current_x}, {current_y}) 移动到 ({move_x}, {move_y})")
        pyautogui.moveTo(move_x, move_y, duration=0.1)
        time.sleep(0.1)

        current_x, current_y = pyautogui.position()
        new_distance = math.sqrt((x - current_x) ** 2 + (y - current_y) ** 2)

        if new_distance < distance:
            distance = new_distance
            max_adjustments -= 1
            if distance < click_error * 0.8:  # 距离较近时缩小步长
                step_size = 0.5
        else:
            step_size = 0.5  # 如果距离没有缩小，缩小步长

    # 执行点击操作（添加轻微随机偏移模拟人类点击）
    click_offset_x = np.random.randint(-1, 2)  # -1到1之间的随机整数
    click_offset_y = np.random.randint(-1, 2)

    pyautogui.moveRel(click_offset_x, click_offset_y, duration=0.05)
    if click_type == 'left':
        pyautogui.click()
    elif click_type == 'right':
        pyautogui.rightClick()

    time.sleep(0.5)  # 点击后等待，给游戏响应时间
    print(f"点击后鼠标坐标: ({pyautogui.position()[0]}, {pyautogui.position()[1]})")

    # 返回实际点击的位置
    return (current_x + click_offset_x, current_y + click_offset_y)


# 持续查找图像直到找到或超时
def find_image_with_retry(window_manager, template_path, max_attempts=50, confidence=0.8,
                         initial_wait=0, retry_wait=0.2, save_every_n=5):
    """持续查找图像，直到找到或达到最大尝试次数"""
    # 初始等待
    if initial_wait > 0:
        print(f"初始等待 {initial_wait} 秒...")
        time.sleep(initial_wait)

    for attempt in range(max_attempts):
        print(f"尝试查找图像 {attempt + 1}/{max_attempts}...")
        try:
            # 每n次尝试保存一次结果图像用于调试
            save_result = (attempt % save_every_n == 0)
            position = locate_image_on_screen(window_manager, template_path, confidence=confidence,
                                              save_result=save_result)
            if position:
                return position
        except Exception as e:
            print(f"查找图像时出错: {e}")

        time.sleep(retry_wait)  # 等待一段时间再重试

    print(f"达到最大尝试次数，未找到匹配图像")
    return None


class TestMouseClick(unittest.TestCase):
    def setUp(self):
        self.window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"
        self.window_manager = WindowManager(self.window_title)
        self.assertTrue(self.window_manager.find_and_activate_window())

    def test_mouse_click(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cahc7_image_path = os.path.join(base_dir, "../images/cahc7.png")
        yz_image_path = os.path.join(base_dir, "../images/yz.png")

        # 按下alt+e打开道具栏
        print("按下 Alt+E 打开道具栏...")
        pyautogui.hotkey('alt', 'e')
        time.sleep(1.5)  # 增加等待时间，确保道具栏完全打开

        # 识别并右键点击cahc7.png
        print("开始查找 cahc7.png...")
        cahc7_position = find_image_with_retry(
            self.window_manager,
            cahc7_image_path,
            max_attempts=20,
            confidence=0.7,  # 可根据实际情况调整阈值
            save_every_n=5
        )

        self.assertIsNotNone(cahc7_position, "未找到 cahc7.png")
        print(f"准备点击 cahc7.png 位置: {cahc7_position}")

        # 点击前验证窗口位置是否变化
        current_window_rect = win32gui.GetWindowRect(self.window_manager.window_handle)
        if current_window_rect != self.window_manager.window_rect:
            print(f"警告：窗口位置发生变化，从 {self.window_manager.window_rect} 变为 {current_window_rect}")
            self.window_manager.window_rect = current_window_rect

        # 执行点击并获取实际点击位置
        actual_click_position = click_position(*cahc7_position, click_type='right')
        print(f"实际点击位置: {actual_click_position}")

        # 增加点击后的等待时间，让游戏界面有时间响应
        print("右键点击后等待 2 秒...")
        time.sleep(2)

        # 查找并点击yz.png
        print("开始查找 yz.png...")
        yz_position = find_image_with_retry(
            self.window_manager,
            yz_image_path,
            max_attempts=50,
            confidence=0.65,  # 降低匹配阈值，适应可能的图像变化
            initial_wait=1,
            retry_wait=0.3,
            save_every_n=5
        )

        self.assertIsNotNone(yz_position, "未找到 yz.png")
        print(f"准备点击 yz.png 位置: {yz_position}")

        # 执行点击
        click_position(*yz_position)


if __name__ == '__main__':
    unittest.main()