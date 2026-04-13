"""
YOLO 模型训练脚本
用于训练 NPC 识别模型
"""

import os
import yaml
from pathlib import Path
from datetime import datetime


def create_dataset_yaml(dataset_path: str, 
                       num_classes: int,
                       class_names: list):
    """
    创建 YOLO 数据集配置文件
    
    Args:
        dataset_path: 数据集路径
        num_classes: 类别数量
        class_names: 类别名称列表
    """
    dataset_yaml = {
        'path': dataset_path,
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        
        'nc': num_classes,
        'names': {i: name for i, name in enumerate(class_names)}
    }
    
    # 保存 YAML 文件
    yaml_path = os.path.join(dataset_path, 'data.yaml')
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(dataset_yaml, f, allow_unicode=True, default_flow_style=False)
    
    print(f"[配置] 已创建数据集配置：{yaml_path}")
    return yaml_path


def prepare_dataset_structure(raw_dataset_path: str):
    """
    准备 YOLO 数据集结构
    
    标准结构：
    dataset/
    ├── images/
    │   ├── train/
    │   ├── val/
    │   └── test/
    └── labels/
        ├── train/
        ├── val/
        └── test/
    
    Args:
        raw_dataset_path: 原始数据集路径（包含 images 和 labels 文件夹）
    """
    import shutil
    import random
    
    print(f"[数据集] 准备数据集结构：{raw_dataset_path}")
    
    # 创建目录结构
    splits = ['train', 'val', 'test']
    for split in splits:
        os.makedirs(os.path.join(raw_dataset_path, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(raw_dataset_path, 'labels', split), exist_ok=True)
    
    # 获取所有图片
    import glob
    image_files = glob.glob(os.path.join(raw_dataset_path, 'images', '*.png'))
    image_files.extend(glob.glob(os.path.join(raw_dataset_path, 'images', '*.jpg')))
    
    print(f"[数据集] 找到 {len(image_files)} 张图片")
    
    if len(image_files) == 0:
        print("[警告] 未找到图片文件")
        return
    
    # 划分数据集（80% 训练，10% 验证，10% 测试）
    random.shuffle(image_files)
    
    total = len(image_files)
    train_end = int(total * 0.8)
    val_end = int(total * 0.9)
    
    splits_data = {
        'train': image_files[:train_end],
        'val': image_files[train_end:val_end],
        'test': image_files[val_end:]
    }
    
    # 移动文件
    for split, files in splits_data.items():
        for image_path in files:
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # 移动图片
            src_img = image_path
            dst_img = os.path.join(raw_dataset_path, 'images', split, filename)
            if os.path.exists(src_img):
                shutil.move(src_img, dst_img)
            
            # 移动标注
            src_lbl = os.path.join(raw_dataset_path, 'labels', f"{name_without_ext}.txt")
            dst_lbl = os.path.join(raw_dataset_path, 'labels', split, f"{name_without_ext}.txt")
            if os.path.exists(src_lbl):
                shutil.move(src_lbl, dst_lbl)
    
    print(f"[数据集] 划分完成")
    print(f"  - 训练集：{len(splits_data['train'])} 张")
    print(f"  - 验证集：{len(splits_data['val'])} 张")
    print(f"  - 测试集：{len(splits_data['test'])} 张")


def train_yolov8(dataset_path: str,
                epochs: int = 100,
                batch_size: int = 16,
                img_size: int = 640,
                model_name: str = 'yolov8n.pt'):
    """
    训练 YOLOv8 模型
    
    Args:
        dataset_path: 数据集路径
        epochs: 训练轮数
        batch_size: 批次大小
        img_size: 输入图像尺寸
        model_name: 预训练模型（yolov8n.pt, yolov8s.pt, yolov8m.pt）
    """
    try:
        from ultralytics import YOLO
        
        print(f"[训练] 加载预训练模型：{model_name}")
        model = YOLO(model_name)
        
        print(f"[训练] 开始训练")
        print(f"  - 数据集：{dataset_path}")
        print(f"  - 轮数：{epochs}")
        print(f"  - 批次：{batch_size}")
        print(f"  - 图像尺寸：{img_size}")
        
        # 训练
        results = model.train(
            data=os.path.join(dataset_path, 'data.yaml'),
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            device=0,  # GPU，如果没有 GPU 改为 'cpu'
            workers=8,
            optimizer='SGD',
            lr0=0.01,
            lrf=0.1,
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3.0,
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,
            box=7.5,
            cls=0.5,
            dfl=1.0,
            patience=50,  # 早停
            save=True,
            save_period=-1,
            verbose=True,
            project='runs/detect',
            name='npc_detection',
            exist_ok=True
        )
        
        print(f"[训练] 训练完成！")
        print(f"[模型] 最佳模型保存位置：runs/detect/npc_detection/weights/best.pt")
        
        return results
        
    except ImportError:
        print("[错误] 未安装 ultralytics，请运行：pip install ultralytics")
        return None
    except Exception as e:
        print(f"[错误] 训练失败：{e}")
        return None


def export_model(model_path: str, export_format: str = 'onnx'):
    """
    导出训练好的模型
    
    Args:
        model_path: 模型路径（.pt 文件）
        export_format: 导出格式（onnx, torchscript, engine 等）
    """
    try:
        from ultralytics import YOLO
        
        print(f"[导出] 加载模型：{model_path}")
        model = YOLO(model_path)
        
        print(f"[导出] 导出为 {export_format} 格式")
        export_path = model.export(format=export_format)
        
        print(f"[导出] 模型已保存：{export_path}")
        return export_path
        
    except Exception as e:
        print(f"[错误] 导出失败：{e}")
        return None


def evaluate_model(model_path: str, dataset_path: str):
    """
    评估模型性能
    
    Args:
        model_path: 模型路径
        dataset_path: 数据集路径
    """
    try:
        from ultralytics import YOLO
        
        print(f"[评估] 加载模型：{model_path}")
        model = YOLO(model_path)
        
        print(f"[评估] 在验证集上评估")
        metrics = model.val(data=os.path.join(dataset_path, 'data.yaml'))
        
        print(f"\n[评估结果]")
        print(f"  - mAP@0.5: {metrics.box.map50:.4f}")
        print(f"  - mAP@0.5:0.95: {metrics.box.map:.4f}")
        print(f"  - Precision: {metrics.box.mp:.4f}")
        print(f"  - Recall: {metrics.box.mr:.4f}")
        
        return metrics
        
    except Exception as e:
        print(f"[错误] 评估失败：{e}")
        return None


# 一键训练脚本
def quick_train():
    """一键训练流程"""
    print("=" * 60)
    print("YOLOv8 NPC 识别模型 - 一键训练")
    print("=" * 60)
    
    # 1. 加载类别
    classes_path = "config/npc_classes.txt"
    if os.path.exists(classes_path):
        with open(classes_path, 'r', encoding='utf-8') as f:
            class_names = [line.strip() for line in f.readlines() if line.strip()]
    else:
        print(f"[错误] 找不到类别文件：{classes_path}")
        return
    
    num_classes = len(class_names)
    print(f"[信息] 类别数量：{num_classes}")
    
    # 2. 准备数据集
    raw_dataset_path = "dataset/yolo_dataset"
    if not os.path.exists(raw_dataset_path):
        print(f"[错误] 找不到数据集：{raw_dataset_path}")
        print("[提示] 请先运行 auto_labeler.py 生成标注数据")
        return
    
    print(f"[步骤 1] 准备数据集结构...")
    prepare_dataset_structure(raw_dataset_path)
    
    # 3. 创建配置文件
    print(f"[步骤 2] 创建数据集配置...")
    create_dataset_yaml(raw_dataset_path, num_classes, class_names)
    
    # 4. 训练模型
    print(f"[步骤 3] 训练模型...")
    print("\n请选择模型大小：")
    print("  1. YOLOv8n (nano - 最快，适合实时检测)")
    print("  2. YOLOv8s (small - 平衡)")
    print("  3. YOLOv8m (medium - 更准确)")
    
    choice = input("\n请选择（1/2/3，默认 1）：").strip()
    model_map = {
        '1': 'yolov8n.pt',
        '2': 'yolov8s.pt',
        '3': 'yolov8m.pt'
    }
    model_name = model_map.get(choice, 'yolov8n.pt')
    
    # 训练轮数
    epochs_input = input("请输入训练轮数（默认 100）：").strip()
    epochs = int(epochs_input) if epochs_input else 100
    
    # 开始训练
    results = train_yolov8(
        dataset_path=raw_dataset_path,
        epochs=epochs,
        batch_size=16,
        img_size=640,
        model_name=model_name
    )
    
    if results:
        # 5. 导出模型
        print(f"\n[步骤 4] 导出模型...")
        best_model_path = "runs/detect/npc_detection/weights/best.pt"
        if os.path.exists(best_model_path):
            export_model(best_model_path, 'onnx')
        else:
            print(f"[警告] 未找到训练好的模型：{best_model_path}")
    
    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"\n[输出文件]")
    print(f"  - 最佳模型：runs/detect/npc_detection/weights/best.pt")
    print(f"  - ONNX 模型：runs/detect/npc_detection/weights/best.onnx")
    print(f"  - 训练日志：runs/detect/npc_detection/results.csv")
    print(f"  - 训练图表：runs/detect/npc_detection/results.png")
    
    print(f"\n[下一步]")
    print(f"  1. 测试模型效果")
    print(f"  2. 集成到 npc_recognition.py")
    print(f"  3. 继续收集困难样本，迭代优化")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'train':
            # 一键训练
            quick_train()
        
        elif command == 'export':
            # 导出模型
            model_path = sys.argv[2] if len(sys.argv) > 2 else "runs/detect/npc_detection/weights/best.pt"
            export_format = sys.argv[3] if len(sys.argv) > 3 else 'onnx'
            export_model(model_path, export_format)
        
        elif command == 'eval':
            # 评估模型
            model_path = sys.argv[2] if len(sys.argv) > 2 else "runs/detect/npc_detection/weights/best.pt"
            dataset_path = sys.argv[3] if len(sys.argv) > 3 else "dataset/yolo_dataset"
            evaluate_model(model_path, dataset_path)
        
        else:
            print("未知命令")
            print("用法:")
            print("  python train_yolo.py train   - 一键训练")
            print("  python train_yolo.py export [model_path] [format]  - 导出模型")
            print("  python train_yolo.py eval [model_path] [dataset]   - 评估模型")
    else:
        # 交互式训练
        quick_train()
