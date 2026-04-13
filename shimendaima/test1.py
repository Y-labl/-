import pygetwindow as gw
import pyautogui
import cv2
import numpy as np
import logging
import time
from pynput.keyboard import Controller, Key

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化键盘控制器
keyboard = Controller()

def find_window_and_activate(window_title):
    """
    查找并激活指定标题的窗口。

    :param window_title: 窗口标题
    :return: 如果找到并激活了窗口，则返回窗口对象；否则返回 None
    """
    try:
        # 查找窗口
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            logging.error(f"未找到标题为 '{window_title}' 的窗口")
            return None

        # 获取第一个匹配的窗口
        target_window = windows[0]

        # 激活窗口（使其成为前台窗口）
        target_window.activate()
        time.sleep(0.2)  # 等待窗口激活
        logging.info(f"已激活窗口: {window_title}")

        return target_window

    except Exception as e:
        logging.error(f"激活窗口时发生错误: {e}")
        return None


def locate_image_center(image_path, window, confidence=0.85):
    """
    在窗口内查找目标图片，并返回图片的中心位置。

    :param image_path: 目标图片的路径
    :param window: 目标窗口对象
    :param confidence: 图片匹配的置信度阈值，默认为 0.85
    :return: 如果找到图片，则返回图片的中心坐标 (x, y)；否则返回 None
    """
    try:
        # 读取目标图像
        target_image = cv2.imread(image_path)
        if target_image is None:
            logging.error(f"无法读取文件 '{image_path}'，请检查文件路径或文件是否存在。")
            return None

        # 截取窗口区域的截图
        screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 使用模板匹配找到目标图像的位置
        result = cv2.matchTemplate(screenshot, target_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            # 获取匹配区域的中心坐标
            h, w = target_image.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2

            # 将窗口的左上角坐标加到匹配到的坐标上，得到全局屏幕坐标
            global_center_x = window.left + center_x
            global_center_y = window.top + center_y

            logging.info(f"已找到图片 '{image_path}'，中心位置: ({global_center_x}, {global_center_y})")
            return (global_center_x, global_center_y)
        else:
            logging.warning(f"未能找到图片 '{image_path}'，最大匹配度: {max_val}")
            return None

    except Exception as e:
        logging.error(f"查找图片时发生错误: {e}")
        return None


def click_image_center(center_position):
    """
    将鼠标移动到指定位置并点击。

    :param center_position: 图片的中心坐标 (x, y)
    """
    try:
        if center_position:
            x, y = center_position
            pyautogui.moveTo(x-50, y, duration=0.8)
            pyautogui.click()
            logging.info(f"已点击图片的中心位置: ({x}, {y})")
        else:
            logging.warning("未提供有效的点击位置")
    except Exception as e:
        logging.error(f"点击图片时发生错误: {e}")


def press_f9_and_click_image(image_path, window, confidence=0.85):
    """
    按下 F9 键，然后识别图片并点击其中心位置。

    :param image_path: 目标图片的路径
    :param window: 目标窗口对象
    :param confidence: 图片匹配的置信度阈值，默认为 0.85
    :return: 如果成功点击图片，则返回点击位置的坐标 (x, y)；否则返回 None
    """
    try:
        # 按下 F9 键
        logging.info("按下 F9 键...")
        keyboard.press(Key.f9)
        keyboard.release(Key.f9)
        time.sleep(0.3)  # 等待 F9 键的效果

        # 识别图片并获取中心位置
        center_position = locate_image_center(image_path, window, confidence)
        if not center_position:
            logging.error(f"未能找到图片 '{image_path}'，程序终止。")
            return None

        # 点击图片的中心位置
        click_image_center(center_position)

        return center_position

    except Exception as e:
        logging.error(f"按下 F9 并点击图片时发生错误: {e}")
        return None


def main():
    # 定义窗口标题和图片路径
    window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"  # 替换为实际的窗口标题
    image_path = "../shimen/HS_SF.png"  # 替换为你要识别的图片路径

    # 找到并激活窗口
    target_window = find_window_and_activate(window_title)
    if not target_window:
        logging.error("未能找到并激活窗口，程序终止。")
        return

    # 按下 F9 并点击图片
    press_f9_and_click_image(image_path, target_window)


if __name__ == "__main__":
    main()