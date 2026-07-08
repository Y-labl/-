import os
import sys
import time
import re
import pyautogui
import cv2
from PIL import Image, ImageDraw
import win32gui
import win32con
import win32api
import win32ui
from rapidocr_onnxruntime import RapidOCR
from pyscreeze import ImageNotFoundException

# ================= 配置区 =================
TEMPLATE_NAME = "00.png"  # 模板文件名（与脚本同目录）
CONFIDENCE = 0.6  # 匹配置信度（根据实际调整）
REFRESH_INTERVAL = 0.1  # 刷新间隔（秒）
BOX_COLOR = (255, 255, 0)  # 黄色边框 (RGB)
BOX_WIDTH = 2
TEXT_COLOR = (0, 255, 255)  # 青色文字（易读，不与黄框冲突）
FONT_SIZE = 16


# =========================================

def get_template_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), TEMPLATE_NAME)


def validate_template(path):
    if not os.path.exists(path):
        print(f"[ERROR] 模板文件不存在: {path}")
        sys.exit(1)
    img = cv2.imread(path)
    if img is None:
        print(f"[ERROR] 模板无法读取: {path}")
        sys.exit(1)
    print(f"[INFO] 模板加载成功: {path} ({img.shape[1]}x{img.shape[0]})")
    return path


# ===== 屏幕覆盖绘制函数（带文字标注）=====
def draw_overlay_with_text(x, y, w, h, text="", color=(255, 255, 0), thickness=2, text_color=(0, 255, 255)):
    """
    在屏幕指定位置绘制矩形框 + 右上角显示识别文本
    x, y: 屏幕绝对坐标（左上角原点）
    text: 要显示的识别结果（如 "X:123, Y:456"）
    """
    hwnd = win32gui.GetDesktopWindow()
    srcdc = win32gui.GetWindowDC(hwnd)
    srcdc_obj = win32ui.CreateDCFromHandle(srcdc)
    dest_dc = srcdc_obj.CreateCompatibleDC()

    # 创建位图（稍大一点容纳文字）
    canvas_w = w + 2 * thickness + 120  # 预留右侧文字空间
    canvas_h = h + 2 * thickness + 20
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(srcdc_obj, canvas_w, canvas_h)
    dest_dc.SelectObject(bitmap)

    # 清空背景（黑色半透明）
    brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
    win32gui.SelectObject(dest_dc.GetSafeHdc(), brush)
    win32gui.PatBlt(dest_dc.GetSafeHdc(), 0, 0, canvas_w, canvas_h, win32con.PATCOPY)

    # 绘制黄色边框（主框）
    pen = win32gui.CreatePen(win32con.PS_SOLID, thickness, win32api.RGB(*color[::-1]))
    win32gui.SelectObject(dest_dc.GetSafeHdc(), pen)
    win32gui.Rectangle(dest_dc.GetSafeHdc(), thickness, thickness, w + thickness, h + thickness)

    # 绘制识别文本（右上角，青色）
    if text:
        # 设置字体（使用系统默认字体）
        font = win32gui.CreateFont(
            FONT_SIZE, 0, 0, 0, win32con.FW_NORMAL, 0, 0, 0,
            win32con.ANSI_CHARSET, win32con.OUT_DEFAULT_PRECIS,
            win32con.CLIP_DEFAULT_PRECIS, win32con.DEFAULT_QUALITY,
            win32con.DEFAULT_PITCH | win32con.FF_DONTCARE, "Consolas"
        )
        win32gui.SelectObject(dest_dc.GetSafeHdc(), font)

        # 文字颜色（RGB → BGR）
        text_bgr = win32api.RGB(*text_color[::-1])
        win32gui.SetTextColor(dest_dc.GetSafeHdc(), text_bgr)
        win32gui.SetBkMode(dest_dc.GetSafeHdc(), win32con.TRANSPARENT)

        # 文字位置：框右上角外侧
        text_x = x + w + 5
        text_y = y + 5
        win32gui.TextOut(dest_dc.GetSafeHdc(), text_x, text_y, text)

    # 复制到屏幕
    win32gui.BitBlt(
        srcdc,
        x - thickness, y - thickness,
        canvas_w, canvas_h,
        dest_dc.GetSafeHdc(),
        0, 0,
        win32con.SRCCOPY
    )

    # 清理
    win32gui.DeleteObject(pen)
    win32gui.DeleteObject(brush)
    win32gui.DeleteObject(font)
    dest_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, srcdc)


# ===== 清除覆盖层（仅清除上次绘制区域）=====
def clear_overlay(last_rect=None):
    if last_rect is None:
        return
    x, y, w, h = last_rect
    hwnd = win32gui.GetDesktopWindow()
    srcdc = win32gui.GetWindowDC(hwnd)
    # 用黑色覆盖原区域（精确清除）
    win32gui.FillRect(srcdc, (x - 2, y - 2, w + 4, h + 4), win32gui.GetStockObject(win32con.BLACK_BRUSH))
    win32gui.ReleaseDC(hwnd, srcdc)


# ===== 主程序 =====
def main():
    template_path = validate_template(get_template_path())
    engine = RapidOCR()
    print("[INFO] OCR模型加载完成，开始循环检测...")
    print("[提示] 按 Ctrl+C 退出，检测框+文本将实时显示在屏幕上")
    print("-" * 60)

    last_box_info = None  # (x, y, w, h, text)

    try:
        while True:
            box = None
            try:
                box = pyautogui.locateOnScreen(template_path, confidence=CONFIDENCE)
            except ImageNotFoundException:
                pass

            # 【关键】先清除上一帧的覆盖层
            if last_box_info:
                clear_overlay(last_box_info[:4])  # 仅清除矩形区域

            if box is not None:
                x, y, w, h = int(box.left), int(box.top), int(box.width), int(box.height)

                # 截图 + OCR
                roi_pil = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                result, elapse = engine(roi_pil)
                raw_text = "".join([item[1] for item in result]) if result else ""

                # 提取坐标
                numbers = re.findall(r'\d+', raw_text)
                if len(numbers) >= 2:
                    x_val, y_val = numbers[0], numbers[1]
                    display_text = f"X:{x_val}, Y:{y_val}"
                else:
                    display_text = f"Raw: {raw_text[:20]}"

                # 绘制带文字的覆盖层
                draw_overlay_with_text(
                    x, y, w, h,
                    text=display_text,
                    color=BOX_COLOR,
                    thickness=BOX_WIDTH,
                    text_color=TEXT_COLOR
                )

                # 控制台同步输出（与绘图一致）
                print(f"\r[✅] {display_text} | 框位置: ({x},{y})-{w}x{h} | OCR耗时:{elapse:.3f}s", end="", flush=True)
                last_box_info = (x, y, w, h, display_text)

            else:
                print("\r[⏳] 未检测到目标...", end="", flush=True)
                last_box_info = None

            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] 正在清除覆盖层...")
        if last_box_info:
            clear_overlay(last_box_info[:4])
        print("[INFO] 退出完成")


if __name__ == "__main__":
    main()