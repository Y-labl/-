"""
训练 YOLOv8 模型 - 简化版
"""

from ultralytics import YOLO

def train():
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
        name='zhuagui_v1'
    )
    
    print("\n训练完成！")
    print(f"模型位置：D:\\Program Files\\mhxy\\zhuagui\\trained_model\\zhuagui_v1\\weights\\best.pt")

if __name__ == '__main__':
    train()
