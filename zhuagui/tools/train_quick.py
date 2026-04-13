"""
训练 YOLOv8 - 简化版（只训练 3 轮测试）
"""

import os
os.environ['POLARS_SKIP_CPU_CHECK'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from ultralytics import YOLO

if __name__ == '__main__':
    print("=" * 60)
    print("训练 YOLOv8 - 抓鬼任务 NPC 识别")
    print("=" * 60)
    
    # 加载模型
    model = YOLO('yolov8n.pt')
    
    print("\n数据集：97 张图片，7 个类别")
    print("配置：3 epochs（快速测试）, batch=4\n")
    
    # 训练
    results = model.train(
        data='data.yaml',
        epochs=3,
        batch=4,
        imgsz=640,
        workers=0,
        device='cpu',
        project='trained_model',
        name='quick_test',
        verbose=True,
        plots=False,
        save=True,
        amp=False
    )
    
    print("\n" + "=" * 60)
    print("✅ 训练完成！")
    print("=" * 60)
    print(f"📁 模型位置：trained_model/quick_test/weights/best.pt")
    
    # 验证
    print("\n正在验证模型...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
