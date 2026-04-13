import pyautogui
from PIL import Image, ImageOps, ImageFilter
import cv2
import numpy as np
import logging
import os
import init_window  # 引入 init_window.py 文件
import ddddocr  # 引入 ddddocr 库
import pytesseract  # 引入 Tesseract OCR 库

# 设置 TESSDATA_PREFIX 环境变量
os.environ['TESSDATA_PREFIX'] = r'D:\Program Files\Tesseract-OCR\tessdata'

# 指定 tesseract.exe 的路径
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'



# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def rgb_to_hsv(r, g, b):
    """将 RGB 值转换为 HSV 值"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df / mx) * 100
    v = mx * 100
    return h, s, v

def filter_yellow(image):
    """
    提取图像中的黄色部分，并返回经过增强和二值化处理后的图像。

    :param image: PIL.Image 对象
    :return: 二值化后的图像
    """
    # 将图像转换为 NumPy 数组
    np_image = np.array(image)

    # 将图像从 RGB 转换为 HSV 颜色空间
    hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)

    # 定义黄色的 HSV 范围（稍微放宽）
    lower_yellow = np.array([20, 40, 40])  # 扩展下限
    upper_yellow = np.array([50, 255, 255])  # 扩展上限

    # 创建掩码，只保留黄色部分
    mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

    # 将掩码应用到原始图像上，只保留黄色部分
    yellow_only_image = cv2.bitwise_and(np_image, np_image, mask=mask)

    # 将处理后的图像转换回 PIL 图像对象
    yellow_only_image = Image.fromarray(cv2.cvtColor(yellow_only_image, cv2.COLOR_BGR2RGB))

    # 增强图像对比度
    yellow_only_image = ImageOps.autocontrast(yellow_only_image)

    # 锐化图像
    yellow_only_image = yellow_only_image.filter(ImageFilter.SHARPEN)

    # 将图像转换为灰度图像
    gray_image = yellow_only_image.convert('L')

    # 使用 OpenCV 的自适应二值化
    np_gray_image = np.array(gray_image)
    adaptive_threshold = cv2.adaptiveThreshold(np_gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY, 11, 2)

    # 将二值化后的图像转换回 PIL 图像对象
    final_image = Image.fromarray(adaptive_threshold)

    return final_image

def capture_and_ocr(left, top, width, height, save_path=None):
    """
    截取指定区域的屏幕截图，提取黄色部分的文字，并进行 OCR 识别。如果提供了 save_path，则将截图保存到该路径。

    :param left: 截图区域的左边界
    :param top: 截图区域的上边界
    :param width: 截图区域的宽度
    :param height: 截图区域的高度
    :param save_path: 保存截图的路径（可选）
    :return: 识别到的文字内容
    """
    try:
        # 截取指定区域的屏幕截图
        screenshot = pyautogui.screenshot(region=(left, top + 190, width, height))
        logging.info(f"已截取区域: 左={left}, 上={top}, 宽={width}, 高={height}")

        # 将截图转换为 PIL 图像对象
        image = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())

        # 如果提供了 save_path，则保存原始截图
        if save_path:
            # 确保保存目录存在，如果不存在则创建
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            image.save(save_path)
            logging.info(f"原始截图已保存到: {save_path}")

        # 提取黄色部分的文本
        yellow_only_image = filter_yellow(image)

        # 如果提供了 save_path，则保存处理后的黄色部分截图
        if save_path:
            yellow_save_path = os.path.join(os.path.dirname(save_path), "yellow_" + os.path.basename(save_path))
            yellow_only_image.save(yellow_save_path)
            logging.info(f"黄色部分截图已保存到: {yellow_save_path}")

        # 使用 ddddocr 识别图像中的文字
        ocr = ddddocr.DdddOcr()
        text_ddddocr = ocr.classification(yellow_only_image)

        # 使用 Tesseract 识别图像中的文字
        text_tesseract = pytesseract.image_to_string(yellow_only_image, lang='chi_sim')

        # 去除多余的空白字符
        text_ddddocr = text_ddddocr.strip()
        text_tesseract = text_tesseract.strip()

        logging.info(f"ddddocr 识别到的文字: {text_ddddocr}")
        logging.info(f"Tesseract 识别到的文字: {text_tesseract}")

        # 返回识别结果
        if text_ddddocr:
            return text_ddddocr
        else:
            return text_tesseract

    except Exception as e:
        logging.error(f"截图或 OCR 识别时发生错误: {e}")
        return None

def main():
    # 调用 init_window.py 中的函数查找并激活窗口
    target_window = init_window.find_window_and_activate(init_window.window_title)
    if not target_window:
        print("未能找到并激活窗口，程序终止。")
        return

    # 计算窗口右上角的截图区域
    # 假设我们要截取一个 170x200 像素的区域
    screenshot_width = 170
    screenshot_height = 200

    # 右上角的左边界是窗口的右边界减去截图宽度
    left = target_window.left + target_window.width - screenshot_width
    top = target_window.top
    width = screenshot_width
    height = screenshot_height

    # 定义保存截图的路径
    save_directory = "shimen/"
    save_filename = "screenshot.png"
    save_path = os.path.join(save_directory, save_filename)

    # 调用 capture_and_ocr 函数进行截图、保存和 OCR 识别
    # -i https://pypi.tuna.tsinghua.edu.cn/simple
    recognized_text = capture_and_ocr(left, top, width, height, save_path=save_path)

    if recognized_text:
        print(f"识别到的文字: {recognized_text}")
    else:
        print("未能识别到任何文字。")

if __name__ == "__main__":
    main()