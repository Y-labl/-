"""
简单的标注工具 - 使用 OpenCV (改进版)
替代 LabelImg 的备选方案 - 使用键盘选择类别
"""

import cv2
import numpy as np
import json
from pathlib import Path

# 配置
IMAGE_DIR = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\images")
LABEL_DIR = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\labels")
LABEL_DIR.mkdir(parents=True, exist_ok=True)

# 类别
CLASSES = ['马副将', '驿站老板', '黑无常', '钟馗', '主鬼', '小怪', '鼠标指针']

# 当前图片索引
current_idx = 0
images = list(IMAGE_DIR.glob("*.png"))

# 标注数据
annotations = []
drawing = False
start_point = None
current_class_idx = 0
show_class_menu = False

def draw_rectangle(event, x, y, flags, param):
    global start_point, drawing, annotations, img, current_class_idx, show_class_menu
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_point = (x, y)
    
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_temp = img.copy()
            cv2.rectangle(img_temp, start_point, (x, y), (255, 0, 0), 2)
            cv2.imshow('标注工具', img_temp)
    
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_point = (x, y)
        
        # 确保 start_point 是左上角，end_point 是右下角
        x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
        x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
        
        # 保存标注
        img_w, img_h = img.shape[1], img.shape[0]
        annotations.append({
            'class': CLASSES[current_class_idx],
            'class_id': current_class_idx,
            'x1': x1 / img_w,
            'y1': y1 / img_h,
            'x2': x2 / img_w,
            'y2': y2 / img_h
        })
        
        # 画框
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, CLASSES[current_class_idx], (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow('标注工具', img)
        
        print(f"✓ 已标注：{CLASSES[current_class_idx]}")

def save_labels():
    """保存标注为 YOLO 格式"""
    if not annotations:
        return
    
    img_name = images[current_idx].stem
    label_file = LABEL_DIR / f"{img_name}.txt"
    
    with open(label_file, 'w') as f:
        for ann in annotations:
            # YOLO 格式：class x_center y_center width height
            x_center = (ann['x1'] + ann['x2']) / 2
            y_center = (ann['y1'] + ann['y2']) / 2
            width = ann['x2'] - ann['x1']
            height = ann['y2'] - ann['y1']
            f.write(f"{ann['class_id']} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    print(f"✓ 已保存：{label_file}")

def next_image():
    """下一张图片"""
    global current_idx, annotations, img
    
    if current_idx < len(images) - 1:
        # 保存当前标注
        save_labels()
        
        current_idx += 1
        annotations = []
        img = cv2.imread(str(images[current_idx]))
        cv2.imshow('标注工具', img)
        print(f"\n图片：{current_idx + 1}/{len(images)} - {images[current_idx].name}")

def previous_image():
    """上一张图片"""
    global current_idx, annotations, img
    
    if current_idx > 0:
        # 保存当前标注
        save_labels()
        
        current_idx -= 1
        annotations = []
        img = cv2.imread(str(images[current_idx]))
        cv2.imshow('标注工具', img)
        print(f"\n图片：{current_idx + 1}/{len(images)} - {images[current_idx].name}")

def main():
    global img, current_class_idx
    
    print("=" * 60)
    print("简易标注工具 - 改进版")
    print("=" * 60)
    print(f"图片目录：{IMAGE_DIR}")
    print(f"标注目录：{LABEL_DIR}")
    print(f"图片数量：{len(images)}")
    print("\n操作说明:")
    print("  鼠标左键拖动：框选 NPC")
    print("  数字键 0-6: 选择当前类别")
    print("  N: 下一张")
    print("  P: 上一张")
    print("  S: 保存")
    print("  Q: 退出")
    print("\n当前类别:")
    for i, cls in enumerate(CLASSES):
        print(f"  {i}: {cls}")
    print("=" * 60)
    
    # 加载第一张图
    img = cv2.imread(str(images[0]))
    cv2.imshow('标注工具', img)
    cv2.setMouseCallback('标注工具', draw_rectangle)
    
    print(f"\n开始标注第 1 张图片...")
    
    while True:
        key = cv2.waitKey(0) & 0xFF
        
        if key == ord('q'):  # 退出
            save_labels()
            break
        elif key == ord('n'):  # 下一张
            next_image()
        elif key == ord('p'):  # 上一张
            previous_image()
        elif key == ord('s'):  # 保存
            save_labels()
        elif key in [ord(str(i)) for i in range(len(CLASSES))]:  # 选择类别
            current_class_idx = int(chr(key)) - ord('0')
            print(f"\n当前类别：{CLASSES[current_class_idx]}")
        elif key == 27:  # ESC
            save_labels()
            break
    
    cv2.destroyAllWindows()
    print("\n标注完成！")

if __name__ == "__main__":
    main()
