"""
训练 YOLOv8 模型 - 抓鬼任务 NPC 识别
"""

from ultralytics import YOLO
import os

def train():
    # 配置
    data_yaml = r"D:\Program Files\mhxy\zhuagui\dataset\data.yaml"
    save_dir = r"D:\Program Files\mhxy\zhuagui\trained_model"
    
    print("=" * 60)
    print("开始训练 YOLOv8 模型")
    print("=" * 60)
    print(f"数据集：{data_yaml}")
    print(f"保存目录：{save_dir}")
    
    # 加载预训练模型（使用最小的 nano 版本）
    model = YOLO('yolov8n.pt')
    
    # 开始训练
    results = model.train(
        data=data_yaml,
        epochs=100,          # 训练 100 轮
        batch=16,            # 批次大小
        imgsz=640,           # 输入图片大小
        device=0 if os.name != 'nt' else 'cpu',  # GPU or CPU
        workers=0,           # 数据加载线程数
        optimizer='SGD',     # 优化器
        lr0=0.01,            # 初始学习率
        lrf=0.1,             # 最终学习率
        momentum=0.937,      # 动量
        weight_decay=0.0005, # 权重衰减
        warmup_epochs=3,     # 预热轮数
        save=True,           # 保存检查点
        save_period=-1,      # 每个 epoch 都保存
        project=save_dir,
        name='zhuagui_v1',
        exist_ok=True
    )
    
    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"模型保存位置：{save_dir}\\zhuagui_v1\\weights\\best.pt")
    
    # 验证模型
    print("\n正在验证模型...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    
    # 导出为 ONNX 格式
    print("\n正在导出 ONNX 模型...")
    model.export(format='onnx')
    print(f"ONNX 模型：{save_dir}\\zhuagui_v1\\weights\\best.onnx")
    
    return results

if __name__ == "__main__":
    train()
