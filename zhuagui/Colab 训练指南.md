# 抓鬼任务 YOLO 模型训练 - Google Colab 方案

## 📋 步骤说明

### 1️⃣ 打开 Google Colab
访问：https://colab.research.google.com/

### 2️⃣ 上传标注数据
有两种方式：

**方式 A：直接上传（推荐，适合小数据集）**
1. 在 Colab 左侧点击"文件夹"图标 📁
2. 点击"上传"图标 ⬆️
3. 上传 `annotation_100` 文件夹

**方式 B：使用 Google Drive**
1. 将 `D:\Program Files\mhxy\zhuagui\dataset\annotation_100` 整个文件夹复制到你的 Google Drive
2. 在 Colab 中挂载 Drive

### 3️⃣ 运行训练

#### 完整训练流程（推荐）：
```python
# 1. 安装依赖
!pip install ultralytics -q

# 2. 导入库
from ultralytics import YOLO
import os

# 3. 检查 GPU
print(f"使用设备：CUDA" if torch.cuda.is_available() else "使用设备：CPU")

# 4. 加载模型
model = YOLO('yolov8n.pt')

# 5. 开始训练
results = model.train(
    data='data.yaml',
    epochs=100,
    batch=16,
    imgsz=640,
    device=0,  # 使用 GPU
    workers=2,
    project='trained_model',
    name='zhuagui_v1',
    verbose=True
)

# 6. 验证模型
metrics = model.val()
print(f"mAP50: {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")

# 7. 导出模型
model.export(format='onnx')
print("✅ 训练完成！")
```

### 4️⃣ 下载训练好的模型
训练完成后（约 5-10 分钟）：
1. 在 Colab 左侧文件浏览器找到 `trained_model/zhuagui_v1/weights/best.pt`
2. 右键下载

## 📊 预期结果
- **训练时间**：5-10 分钟（GPU）
- **预期 mAP50**：0.7-0.85
- **模型大小**：约 6MB

## 🎯 下一步
下载模型后，我可以帮你：
1. 集成到抓鬼自动化系统
2. 测试 NPC 识别效果
3. 优化识别性能

需要我创建完整的 Colab 笔记本文件吗？
