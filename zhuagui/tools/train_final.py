"""
训练 YOLOv8 - 完整版
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
    
    print("\n开始训练...")
    print("数据集：97 张图片，7 个类别")
    print("配置：100 epochs, batch=8, imgsz=640\n")
    
    # 训练
    results = model.train(
        data='data.yaml',
        epochs=100,  # 100 轮
        batch=8,
        imgsz=640,
        workers=0,
        project='trained_model',
        name='zhuagui_v1',
        verbose=True,
        plots=False,
        save=True,
        patience=200  # 增加耐心值
    )
    
    print("\n" + "=" * 60)
    print("✅ 训练完成！")
    print("=" * 60)
    print(f"📁 模型位置：trained_model/zhuagui_v1/weights/best.pt")
    
    # 验证
    print("\n正在验证模型...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
