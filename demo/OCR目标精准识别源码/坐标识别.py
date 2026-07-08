import re
import time
import cv2
import numpy as np
import pyautogui
from paddleocr import PaddleOCR

# ================= 配置区 =================
TEMPLATE_PATH = r"D:\pythonDemo\OCR\00.bmp"           # 定位模板（如“X:”图标）
SCREENSHOT_PATH = r"D:\pythonDemo\OCR\1.png"         # 用于调试的静态截图（可替换为实时截图）
OUTPUT_DIR = r"D:\pythonDemo\OCR"

BOX_COLOR = (0, 255, 0)        # OCR检测框：绿色 (BGR)
TEXT_BOX_COLOR = (0, 0, 255)   # 坐标文本框：红色 (BGR)
LOCATE_BOX_COLOR = (255, 0, 0) # 模板定位框：蓝色 (BGR)
FONT_SCALE = 0.6
FONT_THICKNESS = 2
# ==========================================

def init_ocr():
    return PaddleOCR(
        use_angle_cls=True,
        lang="ch",
        det_db_thresh=0.2,
        det_db_box_thresh=0.3,
        det_db_unclip_ratio=1.6,
        use_gpu=False,
        show_log=False
    )

def extract_coordinates(text):
    match = re.search(r'[Xx]\s*:\s*(\d+)\s*[Yy]\s*:\s*(\d+)', text)
    if match:
        return {"x": int(match.group(1)), "y": int(match.group(2)), "raw": text}
    # 宽松匹配：X393 Y66（无冒号）
    match = re.search(r'[Xx](\d+)\D*[Yy](\d+)', text)
    if match:
        return {"x": int(match.group(1)), "y": int(match.group(2)), "raw": text}
    return None

def draw_box_on_image(img, box, color, thickness=2):
    pts = np.array(box, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(img, [pts], isClosed=True, color=color, thickness=thickness)

def draw_text_label(img, text, top_left, bottom_right, bg_color, text_color=(255, 255, 255)):
    cv2.rectangle(img, top_left, bottom_right, bg_color, -1)
    cv2.putText(img, text, (top_left[0] + 5, top_left[1] + 22),
                cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, text_color, FONT_THICKNESS, cv2.LINE_AA)

# ===== 实时调试主循环 =====
def main_realtime():
    print("🔄 启动实时坐标识别与绘图（按 Ctrl+C 停止）...")
    ocr = init_ocr()

    # 创建一个透明叠加层（用于绘制，避免污染原图）
    overlay = None
    canvas = None

    try:
        while True:
            # 🔹 方式1：用静态图调试（推荐开发阶段）
            img = cv2.imread(SCREENSHOT_PATH)
            if img is None:
                print(f"⚠️ 截图未找到: {SCREENSHOT_PATH}，等待3秒...")
                time.sleep(3)
                continue

            # 🔹 方式2：实时截图（取消注释即可启用）
            # screenshot = pyautogui.screenshot()
            # img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            h, w = img.shape[:2]
            if overlay is None or overlay.shape != img.shape:
                overlay = np.zeros_like(img, dtype=np.uint8)
                canvas = img.copy()

            # 清空上一帧绘制
            overlay.fill(0)

            # 1. 模板定位（高置信度）
            box = None
            try:
                loc = pyautogui.locateOnScreen(
                    TEMPLATE_PATH,
                    confidence=0.99,
                    grayscale=True,
                    region=(0, 0, w, min(h, 400))  # 限制在屏幕顶部区域
                )
                if loc:
                    box = (loc.left, loc.top, loc.width, loc.height)
                    # 绘制蓝色模板框
                    cv2.rectangle(overlay, (box[0], box[1]), (box[0]+box[2], box[1]+box[3]),
                                  LOCATE_BOX_COLOR, 2)
            except Exception as e:
                pass  # 忽略异常，继续OCR

            # 2. OCR识别（全图 or ROI）
            detection_boxes = []
            if box:
                left, top, width, height = box
                padding = 40
                x1 = max(0, left - padding)
                y1 = max(0, top - padding)
                x2 = min(w, left + width + padding)
                y2 = min(h, top + height + padding)
                roi = img[y1:y2, x1:x2]
                result = ocr.ocr(roi, cls=True)
                if result and result[0]:
                    for line in result:
                        for b, (text, conf) in line:
                            global_box = [[p[0] + x1, p[1] + y1] for p in b]
                            detection_boxes.append((global_box, text, conf))
            else:
                result = ocr.ocr(img, cls=True)
                if result and result[0]:
                    for line in result:
                        for b, (text, conf) in line:
                            detection_boxes.append((b, text, conf))

            # 3. 提取坐标 & 绘图到 overlay
            coords_found = []
            for global_box, text, conf in detection_boxes:
                coord = extract_coordinates(text)
                if coord:
                    coords_found.append({**coord, "conf": conf, "box": global_box})
                    # 绘制绿色OCR框
                    draw_box_on_image(overlay, global_box, BOX_COLOR, 2)
                    # 绘制红色坐标标签
                    x_min = int(min(p[0] for p in global_box))
                    y_max = int(max(p[1] for p in global_box))
                    label_tl = (x_min, y_max + 5)
                    label_br = (x_min + 190, y_max + 38)
                    draw_text_label(overlay, f"X:{coord['x']} Y:{coord['y']}", label_tl, label_br, TEXT_BOX_COLOR)

            # 4. 合成最终图像：原图 + overlay（透明叠加）
            alpha = 0.7
            canvas = cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)

            # 5. 显示窗口（关键！实时可见）
            cv2.namedWindow("OCR Realtime Debug", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("OCR Realtime Debug", min(w, 1200), min(h, 800))
            cv2.imshow("OCR Realtime Debug", canvas)

            # 6. 按 'q' 退出，按 's' 保存当前帧
            key = cv2.waitKey(100) & 0xFF  # 100ms 刷新率
            if key == ord('q'):
                break
            elif key == ord('s'):
                save_path = f"{OUTPUT_DIR}\\debug_{int(time.time())}.jpg"
                cv2.imwrite(save_path, canvas)
                print(f"💾 已保存截图: {save_path}")

            time.sleep(0.1)  # 控制频率，避免CPU满载

    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
    finally:
        cv2.destroyAllWindows()
        print("✅ 实时调试已关闭")

if __name__ == "__main__":
    main_realtime()