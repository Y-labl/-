import pygetwindow as gw
import pyautogui
from pynput.keyboard import Controller, Key
import time
import cv2
import numpy as np
import random
import logging


# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# 初始化键盘控制器
keyboard = Controller()

# 定义窗口标题
window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"  # 替换为实际的窗口标题

# 定义要识别的图片路径
target_image_path = "../shimen/menkou.png"  # 替换为你要识别的图片路径

def find_window_and_activate(window_title):
    try:
        # 查找窗口
        window = gw.getWindowsWithTitle(window_title)

        if not window:
            print(f"未找到标题为 '{window_title}' 的窗口")
            return None

        # 获取第一个匹配的窗口
        target_window = window[0]

        # 激活窗口（使其成为前台窗口）
        target_window.activate()
        time.sleep(0.2)  # 等待窗口激活

        return target_window

    except Exception as e:
        print(f"发生错误: {e}")
        return None


def press_keys():
    # 按下 F1 键
    keyboard.press(Key.f1)
    keyboard.release(Key.f1)
    time.sleep(0.3)  # 等待 F1 键的效果

    # 按下 Tab 键
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    time.sleep(0.2)  # 等待 Tab 键的效果


# 去往师门
def locate_and_click_image(image_path, confidence=0.85, retries=3, delay_between_retries=1):
    try:
        for attempt in range(retries):
            # 读取目标图像
            target_image = cv2.imread(image_path)
            if target_image is None:
                print(f"无法读取文件 '{image_path}'，请检查文件路径或文件是否存在。")
                return None

            # 截取屏幕
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 使用模板匹配找到目标图像的位置
            result = cv2.matchTemplate(screenshot, target_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                # 获取匹配区域的中心坐标
                h, w = target_image.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2

                # 生成随机偏移量，确保偏移量在图片范围内
                offset_x = random.randint(-w // 4, w // 4)  # 水平方向的随机偏移量，最大为图片宽度的 1/4
                offset_y = random.randint(-h // 4, h // 4)  # 垂直方向的随机偏移量，最大为图片高度的 1/4

                # 确保点击位置在图片范围内
                click_x = max(center_x + offset_x, max_loc[0])
                click_x = min(click_x, max_loc[0] + w)

                click_y = max(center_y + offset_y, max_loc[1])
                click_y = min(click_y, max_loc[1] + h)

                # 将鼠标移动到目标位置并点击
                pyautogui.moveTo(click_x-30, click_y+20, duration=0.8)
                pyautogui.click()

                print(f"已找到并点击图片 '{image_path}'，点击位置: ({click_x}, {click_y})")
                return (click_x, click_y)

            else:
                print(f"第 {attempt + 1} 次尝试：未能找到图片 '{image_path}'，最大匹配度: {max_val}")

            # 如果未找到图片，等待一段时间后重试
            if attempt < retries - 1:
                time.sleep(delay_between_retries)

        print(f"经过 {retries} 次尝试后仍未找到图片 '{image_path}'")
        return None

    except Exception as e:
        print(f"发生错误: {e}")
        return None

# 点击传送口
def wait_and_click_image_center( wait_time=15, confidence=0.85):
    """
    等待指定时间后，识别图片并点击图片的中心位置。

    :param image_path: 目标图片的路径
    :param wait_time: 等待时间（秒）
    :param confidence: 图片匹配的置信度阈值，默认为 0.85
    :return: 如果成功点击图片，则返回点击位置的坐标 (x, y)；否则返回 None
    """
    try:
        image_path = "../shimen/chuansongquan.png"
        # 等待指定时间
        print(f"开始等待 {wait_time} 秒...")
        time.sleep(wait_time)
        print("等待结束，开始查找图片...")

        # 读取目标图像
        target_image = cv2.imread(image_path)
        if target_image is None:
            print(f"无法读取文件 '{image_path}'，请检查文件路径或文件是否存在。")
            return None

        # 截取屏幕
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 使用模板匹配找到目标图像的位置
        result = cv2.matchTemplate(screenshot, target_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            # 获取匹配区域的中心坐标
            h, w = target_image.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2

            # 将鼠标移动到目标位置并点击
            pyautogui.moveTo(center_x-30, center_y, duration=0.5)
            pyautogui.click()

            print(f"已找到并点击图片 '{image_path}' 的中心位置: ({center_x}, {center_y})")
            return (center_x, center_y)
        else:
            print(f"未能找到图片 '{image_path}'，最大匹配度: {max_val}")
            return None

    except Exception as e:
        print(f"发生错误: {e}")
        return None


def locate_image_center(image_path, confidence=0.85):
    """
    在屏幕上查找目标图片，并返回图片的中心位置。

    :param image_path: 目标图片的路径
    :param confidence: 图片匹配的置信度阈值，默认为 0.85
    :return: 如果找到图片，则返回图片的中心坐标 (x, y)；否则返回 None
    """
    try:
        # 读取目标图像
        target_image = cv2.imread(image_path)
        if target_image is None:
            logging.error(f"无法读取文件 '{image_path}'，请检查文件路径或文件是否存在。")
            return None

        # 截取屏幕
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 使用模板匹配找到目标图像的位置
        result = cv2.matchTemplate(screenshot, target_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            # 获取匹配区域的中心坐标
            h, w = target_image.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            logging.info(f"已找到图片 '{image_path}'，中心位置: ({center_x}, {center_y})")
            return (center_x, center_y)
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
            pyautogui.moveTo(x, y, duration=0.5)
            pyautogui.click()
            logging.info(f"已点击图片的中心位置: ({x}, {y})")
        else:
            logging.warning("未提供有效的点击位置")
    except Exception as e:
        logging.error(f"点击图片时发生错误: {e}")


# 点击师傅
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

# 进入藏金阁，按下F9
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



image_path = "../shimen/chuansongquan.png"  # 替换为你要识别的图片路径
def main():
    # 找到并激活窗口
    target_window = find_window_and_activate(window_title)
    if not target_window:
        return

    # 按下 F1 和 Tab 键
    press_keys()

    # 识别图片并点击
    locate_and_click_image(target_image_path)

    # 按下 Tab 键
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    time.sleep(0.5)  # 等待 Tab 键的效果

    # 进入师门
    wait_and_click_image_center()

    time.sleep(4)  # 等待 Tab 键的效果
    sf_image_path = "../shimen/HS_SF.png"  # 替换为你要识别的图片路径
    # 按下 F9 并点击图片
    press_f9_and_click_image(sf_image_path, target_window)
    time.sleep(1)  # 等待

    er_image_path = "../shimen/renwu.png"
    # 识别图片并点击
    locate_and_click_image(er_image_path)



if __name__ == "__main__":
    main()