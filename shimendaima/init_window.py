import pygetwindow as gw
import pyautogui
from pynput.keyboard import Controller, Key
import time
import cv2
import numpy as np
import random
import logging


# 定义窗口标题
window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"  # 替换为实际的窗口标题
# window_title1 = "Phone-4HDVB23218001313)"

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