"""
训练 YOLOv8 - 本地测试版（最少配置）
"""

import os
os.environ['POLARS_SKIP_CPU_CHECK'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from ultralytics import YOLO

if __name__ == '__main__':
    print("=" * 60)
    print("训练 YOLOv8 - 抓鬼任务 NPC 识别（测试版）")
    print("=" * 60)
    
    # 加载模型
    model = YOLO('yolov8n.pt')
    
    print("\n数据集：97 张图片，7 个类别")
    print("配置：10 epochs（测试）, batch=4, imgsz=640")
    print("预计时间：10-15 分钟\n")
    
    # 训练 - 使用最少配置
    results = model.train(
        data='data.yaml',
        epochs=10,       # 只训练 10 轮测试
        batch=4,         # 减小批次
        imgsz=640,
        workers=0,       # 不使用多进程
        device='cpu',    # 强制使用 CPU
        project='trained_model',
        name='test_v1',
        verbose=True,
        plots=False,
        save=True,
        cache=False,     # 不缓存
        amp=False        # 禁用混合精度
    )
    
    print("\n" + "=" * 60)
    print("✅ 测试训练完成！")
    print("=" * 60)
    print(f"📁 模型位置：trained_model/test_v1/weights/best.pt")
    
    # 验证
    print("\n正在验证模型...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    
    print("\n💡 提示：如果测试成功，可以修改 epochs=100 进行完整训练")
