import time
import cv2
import os
import numpy as np
import win32gui
import win32con
import pyautogui

from mouse_target_control import move_mouse_to_target
from 文字识别 import OCRExtractor
from 百度文字识别 import preprocess_image, client, extract_coordinates


class WindowManager:
    """窗口管理类，负责查找、激活窗口并截取窗口截图"""

    def __init__(self, window_title):
        self.window_title = window_title
        self.hwnd = None
        self.window_rect = (0, 0, 0, 0)  # 窗口坐标 (left, top, right, bottom)

    def find_and_activate_window(self):
        """查找并激活指定标题的窗口"""
        self.hwnd = win32gui.FindWindow(None, self.window_title)
        if not self.hwnd:
            print(f"错误：未找到窗口 - {self.window_title}")
            return False

        # 激活窗口并获取坐标
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.hwnd)
        self.window_rect = win32gui.GetWindowRect(self.hwnd)
        left, top, right, bottom = self.window_rect
        # print(f"成功绑定窗口，坐标：左{left}, 上{top}, 右{right}, 下{bottom}")
        return True

    def capture_window_screenshot(self):
        """使用pyautogui截取窗口截图（更简单稳定的方案）"""
        if not self.hwnd:
            print("错误：未找到窗口句柄，请先调用find_and_activate_window")
            return None

        try:
            left, top, right, bottom = self.window_rect
            # 使用pyautogui截取窗口区域
            screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
            # 转换为OpenCV格式
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            print(f"截图过程中出错: {str(e)}")
            return None


def locate_image_on_screen(window_manager, template_path, confidence=0.8):
    """
    在窗口截图中查找模板图像的位置

    :param window_manager: WindowManager实例
    :param template_path: 模板图像路径
    :param confidence: 匹配阈值，默认0.8
    :return: 元组(匹配位置(x, y), 匹配度)或(None, 0)
    """
    # 检查模板文件是否存在
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    # 截取窗口截图
    screenshot = window_manager.capture_window_screenshot()
    if screenshot is None:
        raise ValueError("无法获取窗口截图")

    # 转换为灰度图
    screen_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if template is None:
        raise ValueError(f"无法读取模板图像: {template_path}")

    # 获取模板尺寸
    h, w = template.shape[:2]

    # 执行模板匹配
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 如果匹配度足够，返回中心坐标和匹配度
    if max_val >= confidence:
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        # 转换为屏幕绝对坐标
        left, top, _, _ = window_manager.window_rect
        screen_x = left + center_x
        screen_y = top + center_y

        return (screen_x, screen_y), max_val

    return None, max_val


def find_image_with_retry(window_manager, template_path, max_attempts=30, confidence=0.8, retry_interval=0.5):
    """
    带重试机制的图像查找函数

    :param window_manager: WindowManager实例
    :param template_path: 模板图像路径
    :param max_attempts: 最大尝试次数，默认30
    :param confidence: 匹配阈值，默认0.8
    :param retry_interval: 重试间隔(秒)，默认0.5
    :return: 匹配位置(x, y)或None
    """
    for attempt in range(max_attempts):
        # print(f"[尝试 {attempt + 1}/{max_attempts}] 正在查找图像...")
        try:
            position, max_val = locate_image_on_screen(window_manager, template_path, confidence)
            if position:
                # print(f"成功找到图像，匹配度: {max_val:.2f}")
                return position
            else:
                print(f"未找到匹配图像，当前匹配度: {max_val:.2f} (阈值: {confidence})")
        except Exception as e:
            print(f"查找过程中出错: {str(e)}")

        time.sleep(retry_interval)

    print(f"达到最大尝试次数，未找到匹配图像")
    return None


def capture_area_relative_to_point(
        x, y, width=100, height=50,
        upward_offset=10,  # 向上偏移量（保留之前的向上调整功能）
        right_offset=10,  # 新增：向右偏移量（默认10像素，值越大越靠右）
        save_path="baotuzuobiao/baotuzuobiao.png"
):
    """
    截取以指定点为基准的区域（支持向上+向右偏移）

    :param x: 基准点x坐标
    :param y: 基准点y坐标
    :param width: 截图宽度（默认100像素）
    :param height: 截图高度（默认50像素）
    :param upward_offset: 向上偏移量（像素），默认10
    :param right_offset: 向右偏移量（像素），默认10
    :param save_path: 截图保存路径
    :return: 是否成功，截图路径
    """
    try:
        # 创建保存目录
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 计算截图区域：向右偏移 → region_left = 基准x + 向右偏移量
        # 向上偏移 → region_top = 基准y - 向上偏移量（保留原功能）
        region_left = x + right_offset  # 核心：向右偏移的关键
        region_top = y - upward_offset  # 保留向上偏移（可根据需要设为0）
        region = (region_left, region_top, width, height)

        # 截取并保存
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(save_path)
        # print(f"已保存截图：基准点({x},{y}) → 向右偏移{right_offset}px + 向上偏移{upward_offset}px")
        # print(f"截图区域：左{region_left}, 上{region_top}, 宽{width}, 高{height}")
        return True, save_path
    except Exception as e:
        print(f"截图失败: {str(e)}")
        return False, ""


def main():
    """主函数：绑定窗口 -> 查找图像 -> 移动鼠标"""
    # 配置参数
    window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"
    template_image_path = "images/baotu.png"  # 模板图像路径
    confidence_threshold = 0.7  # 匹配阈值
    screenshot_save_path = "baotuzuobiao/baotuzuobiao.png"  # 截图保存路径
    zuobiao_image_path = "baotuzuobiao/zuobiao.png"

    # 检查模板文件
    if not os.path.exists(template_image_path):
        print(f"错误：模板图像不存在 - {template_image_path}")
        return

    # 创建窗口管理器并绑定窗口
    window_manager = WindowManager(window_title)
    if not window_manager.find_and_activate_window():
        return

    # 查找图像
    # print(f"开始查找图像，阈值: {confidence_threshold}")
    target_position = find_image_with_retry(
        window_manager,
        template_image_path,
        max_attempts=20,
        confidence=confidence_threshold
    )

    if target_position:
        x, y = target_position
        # print(f"找到目标位置: x={x}, y={y}")

        # 移动鼠标到目标位置
        success, info = move_mouse_to_target(x, y)
        if success:
            # print(f"鼠标移动成功，耗时: {info:.4f} 秒")
            door_position = find_image_with_retry(window_manager, zuobiao_image_path, confidence=0.7)
            # 在main函数中，找到这部分代码（找到坐标位置后调用截图）
            # 在main函数中，找到“找到坐标位置后调用截图”的代码段
            if door_position:
                x, y = door_position
                # print(f"找到坐标位置: {({x}, {y})}")

                # 调用截图函数：向右偏移20px + 向上偏移15px（可按需调整）
                capture_success, save_path = capture_area_relative_to_point(
                    x,
                    y,
                    width=140,  # 保持原宽度
                    height=14,  # 保持原高度
                    upward_offset=6,  # 向上偏移15px（不需要可设为0）
                    right_offset=22,  # 向右偏移20px（核心：调整这个值控制右移幅度）
                    save_path=screenshot_save_path
                )
                if capture_success:
                    # 开始识别截图中的文字
                    extractor = OCRExtractor()

                    # result = extractor.process_image(save_path)
                    # image_path = "D:/Program Files/mhxy/shimendaima/shimen/img_1.png"

                    try:
                        processed_img = preprocess_image(save_path)
                        result = client.basicAccurate(processed_img)

                        # print("\n百度API返回结果：", result)
                        if result.get('words_result_num', 0) > 0:
                            # print("\n✅ 识别成功！")
                            coordinates = extract_coordinates(result)
                            print(coordinates)
                        else:
                            print("\n❌ 未识别到文字")

                    except Exception as e:
                        print(f"\n程序出错：{str(e)}")
                else:
                    print("无法完成截图")
        else:
            print(f"鼠标移动失败: {info}")
    else:
        print("未找到目标图像，程序结束")


if __name__ == "__main__":
    main()