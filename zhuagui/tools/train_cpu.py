"""
训练 YOLOv8 模型 - CPU 兼容版
"""

import os
os.environ['POLARS_SKIP_CPU_CHECK'] = '1'

from ultralytics import YOLO

print("=" * 60)
print("开始训练 YOLOv8 模型 - 抓鬼任务 NPC 识别")
print("=" * 60)

# 加载预训练模型
model = YOLO('yolov8n.pt')

# 训练
results = model.train(
    data=r'D:\Program Files\mhxy\zhuagui\dataset\data.yaml',
    epochs=50,
    batch=8,
    imgsz=640,
    workers=0,
    project=r'D:\Program Files\mhxy\zhuagui\trained_model',
    name='zhuagui_v1',
    amp=False  # 禁用自动混合精度
)

print("\n✅ 训练完成！")
print(f"📁 模型位置：D:\\Program Files\\mhxy\\zhuagui\\trained_model\\zhuagui_v1\\weights\\best.pt")
