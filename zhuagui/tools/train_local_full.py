"""
训练 YOLOv8 - 完整版（本地训练 100 轮）
"""

import os
from pathlib import Path
os.environ['POLARS_SKIP_CPU_CHECK'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from ultralytics import YOLO
import time

if __name__ == '__main__':
    # 与 开始完整训练.bat 一致：工作目录为 dataset/
    _here = Path(__file__).resolve().parent
    _dataset = _here.parent / "dataset"
    os.chdir(_dataset)

    print("=" * 60)
    print("训练 YOLOv8 - 抓鬼任务 NPC 识别（完整版）")
    print("=" * 60)
    
    start_time = time.time()
    
    # 加载模型
    model = YOLO('yolov8n.pt')
    
    epochs = int(os.environ.get("ZHUAGUI_FULL_EPOCHS", "100"))
    patience = int(os.environ.get("ZHUAGUI_FULL_PATIENCE", "50"))
    print("\n数据集：annotation_100（100 张图 + labels，含 class6 鼠标若已运行 inject_mouse_only）")
    print(f"配置：{epochs} epochs, batch=8, imgsz=640")
    print("预计时间：视 CPU 与轮数而定\n")
    
    # 训练
    results = model.train(
        data='data.yaml',
        epochs=epochs,
        batch=8,
        imgsz=640,
        workers=0,
        device='cpu',
        project='trained_model',
        name='zhuagui_final',
        verbose=True,
        plots=False,
        save=True,
        cache=False,
        amp=False,
        patience=patience,
    )
    
    elapsed = (time.time() - start_time) / 60
    
    print("\n" + "=" * 60)
    print(f"✅ 训练完成！用时：{elapsed:.1f} 分钟")
    print("=" * 60)
    try:
        save_root = Path(model.trainer.save_dir)
    except Exception:
        save_root = Path("runs/detect/trained_model/zhuagui_final")
    best_pt = (save_root / "weights" / "best.pt").resolve()
    print(f"📁 模型位置：{best_pt}")
    
    # 验证
    print("\n正在验证模型...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    
    # 导出
    print("\n正在导出 ONNX 模型...")
    model.export(format='onnx')
    print("✅ ONNX 模型已导出")
