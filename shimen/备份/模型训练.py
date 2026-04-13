import torch
from ultralytics import YOLO

# 加载模型
model = YOLO('yolov8s.pt')

# 检查 GPU 可用性
if torch.cuda.is_available():
    print(f"发现 {torch.cuda.device_count()} 个 GPU，使用 GPU 训练...")
    device = 0
else:
    print("未发现 GPU，使用 CPU 训练（可能较慢）...")
    device = 'cpu'

# 训练模型
model.train(
    data='./data.yaml',
    epochs=50,
    imgsz=640,
    batch=8,
    device=device,
    save=True,
    cache=True
)