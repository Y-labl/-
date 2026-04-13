"""
训练 YOLOv8 - 单轮训练（避免崩溃）
"""

import os
os.environ['POLARS_SKIP_CPU_CHECK'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from ultralytics import YOLO

if __name__ == '__main__':
    print("=" * 60)
    print("训练 YOLOv8 - 单轮训练模式")
    print("=" * 60)
    
    # 加载模型
    model = YOLO('yolov8n.pt')
    
    print("\n每次训练 1 轮，共训练 10 次")
    print("这样可以避免程序崩溃\n")
    
    # 训练 10 次，每次 1 轮
    for i in range(1, 11):
        print(f"\n{'='*60}")
        print(f"开始第 {i} 轮训练...")
        print(f"{'='*60}\n")
        
        results = model.train(
            data='data.yaml',
            epochs=1,        # 只训练 1 轮
            batch=4,
            imgsz=640,
            workers=0,
            device='cpu',
            project='trained_model',
            name='step_by_step',
            verbose=True,
            plots=False,
            save=True,
            cache=False,
            amp=False,
            resume=(i > 1)   # 从第 2 次开始恢复训练
        )
        
        print(f"\n✅ 第 {i} 轮完成！")
        
        # 保存检查点
        if i == 10:
            print("\n🎉 所有训练完成！")
            print(f"📁 模型位置：trained_model/step_by_step/weights/best.pt")
