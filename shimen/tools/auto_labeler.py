"""
NPC 自动标注工具
使用预训练 YOLO 模型进行预标注，人工修正
功能：
1. 加载预训练 YOLO 模型
2. 批量预测截图中的 NPC
3. 生成 YOLO 格式的标注文件
4. 支持人工修正界面
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Tuple
from datetime import datetime


class AutoLabeler:
    """
    自动标注器
    使用 YOLO 模型预标注 NPC 位置
    """
    
    def __init__(self, model_path: str = None):
        """
        初始化自动标注器
        
        Args:
            model_path: YOLO 模型路径（如果没有，使用模拟标注）
        """
        self.model_path = model_path
        self.model = None
        self.classes = self._load_classes()
        
        # 尝试加载模型
        self._try_load_model()
    
    def _load_classes(self) -> List[str]:
        """加载 NPC 类别列表"""
        classes_path = "config/npc_classes.txt"
        
        if os.path.exists(classes_path):
            with open(classes_path, 'r', encoding='utf-8') as f:
                classes = [line.strip() for line in f.readlines() if line.strip()]
            print(f"[类别] 加载 {len(classes)} 个 NPC 类别")
            return classes
        else:
            # 默认类别
            default_classes = [
                '门派师傅', '门派师兄', '门派守卫',
                '杂货店老板', '武器店老板', '药店老板',
                '驿站老板', '商会会长', '店小二'
            ]
            print(f"[类别] 使用默认 {len(default_classes)} 个类别")
            return default_classes
    
    def _try_load_model(self):
        """尝试加载 YOLO 模型"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                print(f"[模型] 加载成功：{self.model_path}")
            except Exception as e:
                print(f"[模型] 加载失败：{e}")
                print("[提示] 将使用模拟标注模式")
                self.model = None
        else:
            print("[模型] 模型文件不存在，使用模拟标注")
            print("[提示] 首次使用需要手动标注一部分数据训练初始模型")
    
    def predict(self, image: np.ndarray, 
                confidence_threshold: float = 0.5) -> List[Dict]:
        """
        预测图片中的 NPC
        
        Args:
            image: 图片（BGR 格式）
            confidence_threshold: 置信度阈值
            
        Returns:
            检测结果列表
        """
        if self.model is None:
            # 模拟标注（用于演示）
            return self._mock_predict(image)
        
        # YOLO 预测
        results = self.model.predict(
            image,
            conf=confidence_threshold,
            verbose=False
        )
        
        # 解析结果
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                # 获取坐标
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                
                # 获取类别和置信度
                cls_id = int(box.cls[0].cpu().numpy())
                conf = float(box.conf[0].cpu().numpy())
                
                # 转换为 YOLO 格式（x_center, y_center, w, h）归一化
                img_h, img_w = image.shape[:2]
                x_center = ((x1 + x2) / 2) / img_w
                y_center = ((y1 + y2) / 2) / img_h
                width = (x2 - x1) / img_w
                height = (y2 - y1) / img_h
                
                detections.append({
                    'class_id': cls_id,
                    'class_name': self.classes[cls_id] if cls_id < len(self.classes) else f'class_{cls_id}',
                    'confidence': conf,
                    'bbox_xyxy': [x1, y1, x2, y2],
                    'bbox_yolo': [x_center, y_center, width, height]
                })
        
        return detections
    
    def _mock_predict(self, image: np.ndarray) -> List[Dict]:
        """
        模拟预测（用于没有模型时的演示）
        实际使用时会被真实模型替换
        """
        # 这里可以集成一些简单的启发式方法
        # 例如：颜色检测、轮廓检测等
        
        # 示例：检测黄色区域（假设门派师傅穿黄衣服）
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 黄色范围
        lower_yellow = np.array([20, 80, 80])
        upper_yellow = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 2000 < area < 50000:  # 过滤太小或太大的区域
                x, y, w, h = cv2.boundingRect(cnt)
                
                # 转换为 YOLO 格式
                img_h, img_w = image.shape[:2]
                x_center = (x + w/2) / img_w
                y_center = (y + h/2) / img_h
                width = w / img_w
                height = h / img_h
                
                detections.append({
                    'class_id': 0,
                    'class_name': '门派师傅（预标注）',
                    'confidence': 0.6,
                    'bbox_xyxy': [x, y, x+w, y+h],
                    'bbox_yolo': [x_center, y_center, width, height]
                })
        
        # 限制最多返回 5 个
        return detections[:5]
    
    def label_batch(self, image_dir: str, 
                   output_dir: str,
                   confidence_threshold: float = 0.5) -> Dict:
        """
        批量标注图片
        
        Args:
            image_dir: 图片目录
            output_dir: 标注输出目录（YOLO 格式）
            confidence_threshold: 置信度阈值
            
        Returns:
            标注统计信息
        """
        print(f"[批量标注] 开始处理：{image_dir}")
        
        # 创建输出目录
        images_output = os.path.join(output_dir, 'images')
        labels_output = os.path.join(output_dir, 'labels')
        os.makedirs(images_output, exist_ok=True)
        os.makedirs(labels_output, exist_ok=True)
        
        # 获取所有图片
        import glob
        image_files = glob.glob(os.path.join(image_dir, "*.png"))
        image_files.extend(glob.glob(os.path.join(image_dir, "*.jpg")))
        
        print(f"[批量标注] 找到 {len(image_files)} 张图片")
        
        # 统计信息
        stats = {
            'total': 0,
            'labeled': 0,
            'total_detections': 0,
            'by_class': {}
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
                
                # 预测
                detections = self.predict(image, confidence_threshold)
                
                if len(detections) > 0:
                    stats['labeled'] += 1
                    stats['total_detections'] += len(detections)
                    
                    # 复制图片到输出目录
                    filename = os.path.basename(image_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # 保存图片
                    output_image_path = os.path.join(images_output, filename)
                    cv2.imwrite(output_image_path, image)
                    
                    # 保存标注（YOLO 格式）
                    label_path = os.path.join(labels_output, f"{name_without_ext}.txt")
                    with open(label_path, 'w') as f:
                        for det in detections:
                            # YOLO 格式：class_id x_center y_center width height
                            line = f"{det['class_id']} {' '.join([f'{v:.6f}' for v in det['bbox_yolo']])}\n"
                            f.write(line)
                    
                    # 更新统计
                    for det in detections:
                        class_name = det['class_name']
                        stats['by_class'][class_name] = stats['by_class'].get(class_name, 0) + 1
                    
                    print(f"[{i+1}/{len(image_files)}] ✓ {filename} - {len(detections)} 个 NPC")
                else:
                    print(f"[{i+1}/{len(image_files)}] ○ {filename} - 无 NPC")
                
            except Exception as e:
                print(f"[错误] 处理 {image_path} 失败：{e}")
        
        # 打印统计
        print("\n" + "=" * 50)
        print("[批量标注] 完成统计")
        print("=" * 50)
        print(f"总图片数：{stats['total']}")
        print(f"已标注：{stats['labeled']}")
        print(f"未标注：{stats['total'] - stats['labeled']}")
        print(f"总检测数：{stats['total_detections']}")
        print("\n各类别数量:")
        for class_name, count in sorted(stats['by_class'].items(), key=lambda x: -x[1]):
            print(f"  - {class_name}: {count}")
        print("=" * 50)
        
        return stats
    
    def visualize_annotations(self, image_path: str, 
                             label_path: str = None,
                             output_path: str = None):
        """
        可视化标注结果
        
        Args:
            image_path: 图片路径
            label_path: 标注文件路径（可选，不传则自动预测）
            output_path: 输出路径（可选）
        """
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            print(f"[错误] 读取图片失败：{image_path}")
            return
        
        # 获取标注
        if label_path and os.path.exists(label_path):
            # 读取已有标注
            detections = self._read_yolo_label(label_path, image.shape)
        else:
            # 自动预测
            detections = self.predict(image)
        
        # 绘制标注
        colors = [
            (0, 255, 0),    # 绿色
            (255, 0, 0),    # 蓝色
            (0, 0, 255),    # 红色
            (255, 255, 0),  # 青色
            (255, 0, 255),  # 紫色
        ]
        
        for i, det in enumerate(detections):
            color = colors[i % len(colors)]
            
            # 获取坐标
            x1, y1, x2, y2 = [int(v) for v in det['bbox_xyxy']]
            
            # 绘制矩形框
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # 绘制文字
            label = f"{det['class_name']} {det['confidence']:.2f}"
            cv2.putText(image, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 显示或保存
        if output_path:
            cv2.imwrite(output_path, image)
            print(f"[可视化] 已保存：{output_path}")
        else:
            cv2.imshow('Annotations', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    def _read_yolo_label(self, label_path: str, 
                        image_shape: Tuple) -> List[Dict]:
        """
        读取 YOLO 格式标注文件
        
        Args:
            label_path: 标注文件路径
            image_shape: 图片尺寸
            
        Returns:
            检测结果列表
        """
        img_h, img_w = image_shape[:2]
        detections = []
        
        with open(label_path, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # 转换为 xyxy 格式
                x1 = int((x_center - width/2) * img_w)
                y1 = int((y_center - height/2) * img_h)
                x2 = int((x_center + width/2) * img_w)
                y2 = int((y_center + height/2) * img_h)
                
                detections.append({
                    'class_id': class_id,
                    'class_name': self.classes[class_id] if class_id < len(self.classes) else f'class_{class_id}',
                    'confidence': 1.0,  # 标注文件没有置信度
                    'bbox_xyxy': [x1, y1, x2, y2]
                })
        
        return detections


# 使用示例
if __name__ == "__main__":
    print("=" * 50)
    print("NPC 自动标注工具")
    print("=" * 50)
    
    # 创建标注器
    labeler = AutoLabeler(model_path=None)  # 首次使用没有模型
    
    # 选择功能
    print("\n请选择功能：")
    print("1. 批量自动标注")
    print("2. 可视化标注结果")
    
    choice = input("\n请输入选择（1/2）：").strip()
    
    if choice == '1':
        # 批量标注
        image_dir = input("请输入图片目录（默认 dataset/npc_images）：").strip()
        if not image_dir:
            image_dir = "dataset/npc_images"
        
        output_dir = input("请输入输出目录（默认 dataset/yolo_dataset）：").strip()
        if not output_dir:
            output_dir = "dataset/yolo_dataset"
        
        # 执行批量标注
        stats = labeler.label_batch(image_dir, output_dir)
        
        print("\n[下一步]")
        print("1. 检查标注结果")
        print("2. 使用 LabelImg 修正标注")
        print("3. 训练 YOLO 模型")
        
    elif choice == '2':
        # 可视化
        image_path = input("请输入图片路径：").strip()
        label_path = input("请输入标注文件路径（可选，直接回车自动预测）：").strip()
        
        if not label_path:
            label_path = None
        
        labeler.visualize_annotations(image_path, label_path)
    
    else:
        print("无效选择")
    
    print("\n标注完成！")
