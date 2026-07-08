import os
import re
import cv2
import numpy as np
from paddleocr import PaddleOCR

# ================= 配置区 =================
IMAGE_FOLDER = r"D:\pythonDemo\OCR"  # 👈 存放待检测图片的文件夹
TEMPLATE_PATH = r"D:\pythonDemo\OCR\00.bmp"       # 定位模板（可选）
BOX_COLOR = (0, 255, 0)        # OCR框：绿色
TEXT_BOX_COLOR = (0, 0, 255)   # 坐标标签：红色
LOCATE_BOX_COLOR = (255, 0, 0) # 模板框：蓝色
FONT_SCALE = 0.6
FONT_THICKNESS = 2
SUPPORTED_EXT = {'.png', '.jpg', '.jpeg', '.bmp'}
# ==========================================

def init_ocr():
    return PaddleOCR(use_angle_cls=True, lang="ch", show_log=False, use_gpu=False)

def extract_coordinates(text):
    match = re.search(r'[Xx]\s*:\s*(\d+)\s*[Yy]\s*:\s*(\d+)', text)
    if match:
        return {"x": int(match.group(1)), "y": int(match.group(2)), "raw": text}
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

def process_and_draw(img, ocr):
    """对单张图片执行OCR+绘图，返回带标注的图像"""
    overlay = np.zeros_like(img, dtype=np.uint8)
    h, w = img.shape[:2]

    # OCR识别
    result = ocr.ocr(img, cls=True)
    if result and result[0]:
        for line in result:
            for b, (text, conf) in line:
                coord = extract_coordinates(text)
                if coord:
                    draw_box_on_image(overlay, b, BOX_COLOR, 2)
                    x_min = int(min(p[0] for p in b))
                    y_max = int(max(p[1] for p in b))
                    label_tl = (x_min, y_max + 5)
                    label_br = (x_min + 190, y_max + 38)
                    draw_text_label(overlay, f"X:{coord['x']} Y:{coord['y']}", label_tl, label_br, TEXT_BOX_COLOR)

    alpha = 0.7
    return cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)

def main():
    # 收集所有支持格式的图片并排序
    images = sorted([
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
    ])

    if not images:
        print(f"❌ 文件夹 {IMAGE_FOLDER} 中没有找到图片")
        return

    print(f"📂 共加载 {len(images)} 张图片")
    print("⌨️  操作说明: ← → 切换图片 | 'q' 退出 | 's' 保存当前帧")

    ocr = init_ocr()
    idx = 0
    window_name = "OCR Realtime Debug"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        img = cv2.imread(images[idx])
        if img is None:
            print(f"⚠️ 无法读取: {images[idx]}")
            idx = (idx + 1) % len(images)
            continue

        canvas = process_and_draw(img, ocr)

        # 显示文件名提示
        filename = os.path.basename(images[idx])
        cv2.putText(canvas, f"[{idx+1}/{len(images)}] {filename}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow(window_name, canvas)

        key = cv2.waitKey(0) & 0xFF  # 👈 改为0：等待按键，不自动刷新
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_path = os.path.join(IMAGE_FOLDER, f"annotated_{filename}")
            cv2.imwrite(save_path, canvas)
            print(f"💾 已保存: {save_path}")
        elif key == 81 or key == 2424832:  # ← 左箭头
            idx = (idx - 1) % len(images)
        elif key == 83 or key == 2555904:  # → 右箭头
            idx = (idx + 1) % len(images)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()