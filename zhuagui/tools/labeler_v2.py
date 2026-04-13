"""
最简单的标注工具 - 修复版
"""

import cv2
import numpy as np
from pathlib import Path

# 配置
IMAGE_DIR = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\images")
LABEL_DIR = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\labels")
LABEL_DIR.mkdir(parents=True, exist_ok=True)

# 类别
CLASSES = ['马副将', '驿站老板', '黑无常', '钟馗', '主鬼', '小怪', '鼠标指针']

def main():
    images = list(IMAGE_DIR.glob("*.png"))
    current_idx = 0
    annotations = []
    current_class = 0
    
    # 状态变量
    drawing = False
    start_point = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_point, img_display
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_point = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                temp = img_display.copy()
                cv2.rectangle(temp, start_point, (x, y), (255, 0, 0), 2)
                cv2.imshow('标注工具', temp)
        
        elif event == cv2.EVENT_LBUTTONUP:
            nonlocal annotations
            drawing = False
            end_point = (x, y)
            
            x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
            x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
            
            img_h, img_w = img.shape[:2]
            annotations.append({
                'class_id': current_class,
                'x1': x1 / img_w,
                'y1': y1 / img_h,
                'x2': x2 / img_w,
                'y2': y2 / img_h
            })
            
            color = (0, 255, 0)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, CLASSES[current_class], (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            img_display = img.copy()
            cv2.imshow('标注工具', img)
            
            print(f"✓ 已标注：{CLASSES[current_class]}")
    
    def save_labels():
        if not annotations:
            return
        
        img_name = images[current_idx].stem
        label_file = LABEL_DIR / f"{img_name}.txt"
        
        with open(label_file, 'w') as f:
            for ann in annotations:
                x_center = (ann['x1'] + ann['x2']) / 2
                y_center = (ann['y1'] + ann['y2']) / 2
                width = ann['x2'] - ann['x1']
                height = ann['y2'] - ann['y1']
                f.write(f"{ann['class_id']} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        print(f"✓ 已保存：{label_file.name}")
    
    img = cv2.imread(str(images[0]))
    img_display = img.copy()
    
    cv2.namedWindow('标注工具', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('标注工具', mouse_callback)
    cv2.imshow('标注工具', img)
    
    print("=" * 60)
    print("标注工具 - 就绪")
    print("=" * 60)
    print(f"图片：{len(images)} 张")
    print("\n操作:")
    print("  1. 先按数字键 0-6 选择类别")
    print("  2. 鼠标拖动框选 NPC")
    print("  3. 按 N 下一张，S 保存，Q 退出")
    print("\n类别:")
    for i, cls in enumerate(CLASSES):
        print(f"  {i}: {cls}")
    print("=" * 60)
    
    while True:
        key = cv2.waitKey(0) & 0xFF
        
        if key == ord('q'):
            save_labels()
            break
        elif key == ord('n'):
            save_labels()
            if current_idx < len(images) - 1:
                current_idx += 1
                annotations = []
                img = cv2.imread(str(images[current_idx]))
                img_display = img.copy()
                cv2.imshow('标注工具', img)
                print(f"\n图片 {current_idx + 1}/{len(images)}")
        elif key == ord('s'):
            save_labels()
        elif key == ord('p'):
            save_labels()
            if current_idx > 0:
                current_idx -= 1
                annotations = []
                img = cv2.imread(str(images[current_idx]))
                img_display = img.copy()
                cv2.imshow('标注工具', img)
                print(f"\n图片 {current_idx + 1}/{len(images)}")
        elif key in [ord(str(i)) for i in range(len(CLASSES))]:
            current_class = int(chr(key)) - ord('0')
            print(f"\n当前类别：{CLASSES[current_class]}")
    
    cv2.destroyAllWindows()
    print("\n完成！")

if __name__ == "__main__":
    main()
