"""
抓鬼任务 NPC 自动标注工具
专门用于标注抓鬼任务的 6 个 NPC + 鼠标指针
"""

import cv2
import numpy as np
import os
from typing import List, Dict
from datetime import datetime


class ZhuaguiLabeler:
    """
    抓鬼任务标注器
    标注：马副将、驿站老板、黑无常、钟馗、主鬼、小怪、鼠标指针
    """
    
    def __init__(self):
        """初始化标注器"""
        # 抓鬼任务 NPC 类别
        self.classes = [
            '马副将',
            '驿站老板', 
            '黑无常',
            '钟馗',
            '主鬼',
            '小怪',
            '鼠标指针'
        ]
        
        # 输入输出目录
        self.input_dir = "D:\\Program Files\\mhxy\\zhuagui\\dataset\\raw_screenshots"
        self.output_dir = "D:\\Program Files\\mhxy\\zhuagui\\dataset\\yolo_dataset"
        
        # 创建输出目录
        os.makedirs(os.path.join(self.output_dir, 'images'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'labels'), exist_ok=True)
    
    def detect_npc_positions(self, image: np.ndarray) -> List[Dict]:
        """
        检测 NPC 位置（模拟标注）
        实际使用时会被 YOLO 模型替换
        
        Args:
            image: 游戏截图
            
        Returns:
            NPC 位置列表
        """
        detections = []
        img_h, img_w = image.shape[:2]
        
        # 这里使用简单的颜色检测作为示例
        # 实际训练时需要用 YOLO 模型
        
        # 示例：检测黄色区域（可能是 NPC）
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 黄色范围
        lower_yellow = np.array([20, 80, 80])
        upper_yellow = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 2000 < area < 50000:  # 过滤太小或太大的区域
                x, y, w, h = cv2.boundingRect(cnt)
                
                # 转换为 YOLO 格式
                x_center = (x + w/2) / img_w
                y_center = (y + h/2) / img_h
                width = w / img_w
                height = h / img_h
                
                # 默认标注为钟馗（后续人工修正）
                detections.append({
                    'class_id': 3,  # 钟馗
                    'bbox': [x_center, y_center, width, height]
                })
        
        # 检测鼠标指针（白色/亮色区域）
        mouse_ptr = self.detect_mouse_pointer(image)
        if mouse_ptr:
            detections.append({
                'class_id': 6,  # 鼠标指针
                'bbox': mouse_ptr
            })
        
        return detections
    
    def detect_mouse_pointer(self, image: np.ndarray) -> List[float]:
        """
        检测鼠标指针位置
        
        Args:
            image: 游戏截图
            
        Returns:
            鼠标指针的 YOLO 格式坐标
        """
        img_h, img_w = image.shape[:2]
        
        # 方法 1：检测白色/亮色小区域（鼠标指针特征）
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 阈值检测（鼠标指针通常是白色）
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        # 查找轮廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 500:  # 鼠标指针较小
                x, y, w, h = cv2.boundingRect(cnt)
                
                # 检查是否是三角形/箭头形状（鼠标指针特征）
                if 0.3 < w/h < 1.5:  # 大致方形
                    # 转换为 YOLO 格式
                    x_center = (x + w/2) / img_w
                    y_center = (y + h/2) / img_h
                    width = w / img_w
                    height = h / img_h
                    
                    return [x_center, y_center, width, height]
        
        return None
    
    def label_batch(self):
        """批量标注所有图片"""
        print(f"[标注] 开始批量标注")
        print(f"[输入] {self.input_dir}")
        print(f"[输出] {self.output_dir}")
        
        # 获取所有图片
        import glob
        image_files = glob.glob(os.path.join(self.input_dir, "*.png"))
        
        print(f"[标注] 找到 {len(image_files)} 张图片")
        
        # 统计
        stats = {
            'total': 0,
            'labeled': 0,
            'with_mouse': 0,
            'by_class': {cls: 0 for cls in self.classes}
        }
        
        # 处理每张图片
        for i, image_path in enumerate(image_files):
            try:
                stats['total'] += 1
                
                # 读取图片
                image = cv2.imread(image_path)
                if image is None:
                    print(f"[{i+1}/{len(image_files)}] 读取失败：{image_path}")
                    continue
                
                # 检测 NPC 位置
                detections = self.detect_npc_positions(image)
                
                if len(detections) > 0:
                    stats['labeled'] += 1
                    
                    # 检查是否有鼠标指针
                    has_mouse = any(d['class_id'] == 6 for d in detections)
                    if has_mouse:
                        stats['with_mouse'] += 1
                    
                    # 复制图片到输出目录
                    filename = os.path.basename(image_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # 保存图片
                    output_image_path = os.path.join(self.output_dir, 'images', filename)
                    cv2.imwrite(output_image_path, image)
                    
                    # 保存标注（YOLO 格式）
                    label_path = os.path.join(self.output_dir, 'labels', f"{name_without_ext}.txt")
                    with open(label_path, 'w', encoding='utf-8') as f:
                        for det in detections:
                            # YOLO 格式：class_id x_center y_center width height
                            line = f"{det['class_id']} {' '.join([f'{v:.6f}' for v in det['bbox']])}\n"
                            f.write(line)
                            
                            # 更新统计
                            class_name = self.classes[det['class_id']]
                            stats['by_class'][class_name] += 1
                    
                    print(f"[{i+1}/{len(image_files)}] ✓ {filename} - {len(detections)} 个目标")
                else:
                    print(f"[{i+1}/{len(image_files)}] ○ {filename} - 无检测")
                
            except Exception as e:
                print(f"[错误] 处理 {image_path} 失败：{e}")
        
        # 打印统计
        print("\n" + "=" * 60)
        print("[标注] 完成统计")
        print("=" * 60)
        print(f"总图片数：{stats['total']}")
        print(f"已标注：{stats['labeled']}")
        print(f"未标注：{stats['total'] - stats['labeled']}")
        print(f"包含鼠标：{stats['with_mouse']}")
        print("\n各类别数量:")
        for class_name, count in stats['by_class'].items():
            if count > 0:
                print(f"  - {class_name}: {count}")
        print("=" * 60)
        
        print(f"\n[下一步]")
        print(f"  1. 使用 LabelImg 检查并修正标注")
        print(f"  2. 运行命令：labelImg")
        print(f"  3. 加载目录：{self.output_dir}")


# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("抓鬼任务 NPC 自动标注工具")
    print("=" * 60)
    print("\n标注对象：马副将、驿站老板、黑无常、钟馗、主鬼、小怪、鼠标指针\n")
    
    labeler = ZhuaguiLabeler()
    labeler.label_batch()
    
    print("\n标注完成！")
