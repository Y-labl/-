import time
import cv2
import os

import pyautogui
import win32con
import win32gui

from fanhuizuobiao import find_image_with_retry
from mouse_target_control import move_mouse_to_target
from 任务截图 import WindowManager, capture_task_tracking
from 文字识别 import OCRExtractor


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





def main():
    # 配置参数
    window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"  # 请替换为实际游戏窗口标题
    # 使用相对路径，确保图片在正确的目录下
    base_dir = os.path.dirname(os.path.abspath(__file__))
    door_image_path = "images/sm.png"
    portal_image_path = "images/smchuansongkou.png"
    portal_image_path = "images/kdcs.png"
    zuobiao_image_path = "baotuzuobiao/zuobiao.png"

    # 检查文件是否存在
    # if not os.path.exists(door_image_path):
    #     print(f"师门传送口图片不存在: {door_image_path}")
    #     return
    #
    # if not os.path.exists(portal_image_path):
    #     print(f"传送口图片不存在: {portal_image_path}")
    #     return

    # 创建窗口管理器
    window_manager = WindowManager(window_title)

    # 1. 识别并绑定窗口
    if not window_manager.find_and_activate_window():
        return

    # 查找并激活窗口
    hwnd = win32gui.FindWindow(None, window_title)
    door_position = find_image_with_retry(window_manager, zuobiao_image_path, confidence=0.7)
    if door_position:
        x = door_position[0]
        y = door_position[1]
        print(f"找到化生寺师门传送口位置: {({x}, {y})}")

        # 调用核心函数
        success, info = move_mouse_to_target(x, y)
        if success:
            print(f"任务完成，耗时：{info:.4f} 秒")
        else:
            print(f"任务失败：{info}")



    # 开始截图
    # capture_task_tracking(window_title,"renwu_images/task_images.png")
    #
    # # 开始识别截图中的文字
    # extractor = OCRExtractor()
    # img_path = "renwu_images/task_images.png"  # 替换为实际图片路径
    #
    # result = extractor.process_image(img_path)
    # if result["success"]:
    #     print("合并后的完整文本：", result["full_text"])
    #     print("\n提取的重点信息：")
    #     for k, v in result["key_info"].items():
    #         print(f"{k}：{v}")
    # else:
    #     print("错误：", result["message"])


    # if hwnd:
    #     win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    #     win32gui.SetForegroundWindow(hwnd)
    #     time.sleep(1)  # 等待窗口激活
    #
    #     # 获取窗口在屏幕上的坐标
    #     left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    #     print(f"窗口坐标：左{left}, 上{top}, 右{right}, 下{bottom}")
    #
    #     # 计算任务追踪区域坐标（窗口内右上角）
    #     task_left = right - 200
    #     task_top = top + 190
    #     task_width = 200
    #     task_height = 90
    #
    #     # 截图
    #     screenshot = pyautogui.screenshot(region=(task_left, task_top, task_width, task_height))
    #     screenshot.save("renwu_images/task_images.png")
    #     print("截图成功")
    # else:
    #     print("未找到窗口")



    # 2. 模拟按下F1键，等待500毫秒
    # print("按下 F1 键")
    # press_key('f1')
    # time.sleep(0.5)
    #
    # # 3. 按下Tab键，识别并点击门口位置，再按Tab键
    # print("按下 Tab 键")
    # press_key('tab')
    #
    # # 识别门口位置并点击，增加重试机制
    # print("正在识别化生寺师门传送口...")
    #
    # door_position = find_image_with_retry(window_manager, door_image_path, confidence=0.7)
    # if door_position:
    #     x = door_position[0]
    #     y = door_position[1]
    #     print(f"找到化生寺师门传送口位置: {({x}, {y})}")
    #
    #     # 调用核心函数
    #     success, info = move_mouse_to_target(x, y)
    #     if success:
    #         print(f"任务完成，耗时：{info:.4f} 秒")
    #     else:
    #         print(f"任务失败：{info}")
    #     # 再次按下Tab键
    #     print("按下 Tab 键")
    #     press_key('tab')
    # else:
    #     print("未找到化生寺师门传送口，退出脚本")
    #     return
    #
    # # 4. 等待5秒，识别传送口并点击
    # print("等待人物移动到化生寺师门传送口...")
    # time.sleep(5)

    # print("正在识别化生寺传送口...")
    # portal_position = find_image_with_retry(window_manager, portal_image_path, confidence=0.7)
    # if portal_position:
    #     x = portal_position[0]
    #     y = portal_position[1]
    #     print(f"找到化生寺师门传送口位置: {({x}, {y})}")
    #
    #     # 调用核心函数
    #     success, info = move_mouse_to_target(x, y)
    #     if success:
    #         print(f"任务完成，耗时：{info:.4f} 秒")
    #     else:
    #         print(f"为找到：{info}")
    #         press_key('F9')
    #
    #     print("已点击化生寺传送口，进入房间")
    #     print("正在识别化生寺传送口...")
    # portal_position = find_image_with_retry(window_manager, portal_image_path, confidence=0.7)
    # if portal_position:
    #     x = portal_position[0]
    #     y = portal_position[1]
    #     print(f"找到门派师傅位置: {({x}, {y})}")
    #
    #     # 调用核心函数
    #     success, info = move_mouse_to_target(x, y)
    #     if success:
    #         print(f"任务完成，耗时：{info:.4f} 秒")
    #     else:
    #         print(f"未找到：{info}")
    #         press_key('F9')
    # else:
    #     print("未找到门派师傅，退出脚本")

if __name__ == "__main__":
    main()