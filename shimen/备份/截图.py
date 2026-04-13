import cv2
import win32gui
import win32ui
import win32con
import numpy as np
import time
import os
import pyautogui

# 创建保存目录
if not os.path.exists('dataset/images'):
    os.makedirs('dataset/images')
if not os.path.exists('dataset/labels'):
    os.makedirs('dataset/labels')


def find_game_window(title_keyword="梦幻西游"):
    """查找包含指定关键词的窗口并返回句柄"""
    windows = []

    def enum_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title_keyword.lower() in title.lower():
                windows.append((hwnd, title))
        return True

    win32gui.EnumWindows(enum_callback, windows)

    if not windows:
        print(f"未找到标题包含 '{title_keyword}' 的窗口")
        return None

    print(f"找到 {len(windows)} 个匹配的窗口:")
    for i, (hwnd, title) in enumerate(windows):
        print(f"{i + 1}. 窗口句柄: {hwnd}, 标题: {title}")

    # 默认选择第一个匹配的窗口
    return windows[0][0]


def capture_game_screenshots(num_samples=50, window_title="梦幻西游"):
    """收集游戏窗口截图作为训练数据"""
    hwnd = find_game_window(window_title)

    if hwnd is None:
        print("尝试使用全屏截图...")
        # 备选方案：截取整个屏幕
        for i in range(num_samples):
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            image_path = f"dataset/images/screenshot_{i}.jpg"
            cv2.imwrite(image_path, screenshot_cv)

            print(f"已保存全屏截图 {i + 1}/{num_samples}: {image_path}")
            time.sleep(1)
        return

    print(f"准备开始收集数据，共收集 {num_samples} 张截图")
    print("请确保游戏窗口已激活")
    time.sleep(3)  # 给用户时间切换到游戏窗口

    for i in range(num_samples):
        try:
            # 获取窗口位置
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # 确保窗口有效
            if width <= 0 or height <= 0:
                print(f"窗口尺寸无效: {width}x{height}，尝试下一次")
                time.sleep(1)
                continue

            # 截取游戏窗口
            try:
                # 方法1: 使用win32gui (更高效)
                hwnd_dc = win32gui.GetWindowDC(hwnd)
                mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
                save_dc = mfc_dc.CreateCompatibleDC()

                save_bitmap = win32ui.CreateBitmap()
                save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
                save_dc.SelectObject(save_bitmap)

                result = save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

                signed_ints_array = save_bitmap.GetBitmapBits(True)
                img = np.frombuffer(signed_ints_array, dtype='uint8')
                img.shape = (height, width, 4)

                win32gui.DeleteObject(save_bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwnd_dc)

                # 转换为OpenCV格式
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            except Exception as e:
                print(f"使用win32gui截图失败: {e}")
                # 方法2: 使用pyautogui (兼容性更好)
                screenshot = pyautogui.screenshot()
                screenshot_np = np.array(screenshot)
                img = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                img = img[top:bottom, left:right]

            # 保存截图
            image_path = f"dataset/images/screenshot_{i}.jpg"
            cv2.imwrite(image_path, img)

            print(f"已保存截图 {i + 1}/{num_samples}: {image_path}")
            time.sleep(1)  # 间隔1秒，给用户时间调整游戏画面

        except Exception as e:
            print(f"截图过程中出错: {e}")
            time.sleep(1)


# 收集50张截图，可根据需要调整数量
capture_game_screenshots(100)