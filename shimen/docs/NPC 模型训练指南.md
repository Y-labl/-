# NPC 识别模型训练指南

## 📋 概述

本文档说明如何训练用于 NPC 识别的 YOLO 模型。

## 🎯 为什么选择 YOLO？

| 特点 | 传统模板匹配 | YOLO 目标检测 |
|------|------------|-------------|
| NPC 移动 | ❌ 无法识别 | ✅ 任意位置 |
| 多类别 | ❌ 困难 | ✅ 支持 |
| 遮挡 | ❌ 失效 | ✅ 鲁棒 |
| 角度变化 | ❌ 失效 | ✅ 鲁棒 |
| 开发成本 | ⭐ 低 | ⭐⭐ 中等 |
| 识别速度 | ⭐⭐⭐⭐⭐ 极快 | ⭐⭐⭐⭐ 快 |

## 📦 准备工作

### 1. 环境安装

```bash
# 安装基础依赖
pip install opencv-python numpy pillow

# 安装 YOLOv8（推荐）
pip install ultralytics

# 或安装 ONNX Runtime（推理用）
pip install onnxruntime-gpu  # GPU 版本
# 或
pip install onnxruntime      # CPU 版本
```

### 2. 工具准备

- **截图工具**：游戏内截图（PrintScreen）或 OBS
- **标注工具**：[LabelImg](https://github.com/heartexlabs/labelImg) 或 [Roboflow](https://roboflow.com/)
- **训练平台**：本地 GPU 或 Google Colab

## 📸 数据收集

### 步骤 1：游戏截图

```
1. 进入游戏，到达 NPC 聚集地（如长安城、门派内）
2. 从不同角度、距离截图
3. 每个 NPC 至少收集 50-100 张样本
4. 覆盖不同时间段（白天/夜晚）
5. 覆盖不同天气（晴天/雨天）
```

### 步骤 2：数据量建议

| NPC 类型 | 最少样本 | 推荐样本 |
|---------|---------|---------|
| 重要 NPC（师傅） | 100 张 | 300 张 |
| 常见 NPC（老板） | 50 张 | 150 张 |
| 一般 NPC（村民） | 30 张 | 100 张 |

**总计**：预计需要 2000-5000 张标注图片

## 🏷️ 数据标注

### 使用 LabelImg 标注

```bash
# 安装 LabelImg
pip install labelImg

# 启动
labelImg
```

### 标注步骤

1. **打开图片**：加载游戏截图
2. **创建矩形框**：框选 NPC 身体（包含头部）
3. **选择类别**：从 npc_classes.txt 选择对应类别
4. **保存**：生成 XML 文件（Pascal VOC 格式）

### 标注规范

```
✅ 正确做法：
- 框选整个 NPC 身体
- 包含头顶名字（如果有）
- NPC 被部分遮挡时，框选可见部分

❌ 错误做法：
- 只框选头部或身体
- 框选范围过大（包含背景）
- 框选范围过小（遗漏部分身体）
```

## 📊 数据集划分

```
数据集结构：
dataset/
├── images/
│   ├── train/      # 训练集（80%）
│   ├── val/        # 验证集（20%）
│   └── test/       # 测试集（可选）
└── labels/
    ├── train/      # 训练标签
    ├── val/        # 验证标签
    └── test/       # 测试标签
```

## 🚀 模型训练

### 方案 A：使用 YOLOv8（推荐）

```python
from ultralytics import YOLO

# 1. 加载预训练模型
model = YOLO('yolov8n.pt')  # nano 版本（最快）
# 或 YOLOv8s.pt（small）、YOLOv8m.pt（medium）

# 2. 训练
model.train(
    data='data.yaml',      # 数据集配置
    epochs=100,            # 训练轮数
    imgsz=640,             # 输入尺寸
    batch=16,              # 批次大小
    device=0,              # GPU 设备
    workers=8,             # 数据加载线程数
    optimizer='SGD',       # 优化器
    lr0=0.01,              # 初始学习率
)

# 3. 验证
results = model.val()

# 4. 导出为 ONNX（用于部署）
model.export(format='onnx')
```

### 方案 B：使用 YOLOv5

```bash
# 克隆仓库
git clone https://github.com/ultralytics/yolov5
cd yolov5

# 安装依赖
pip install -r requirements.txt

# 训练
python train.py \
  --img 640 \
  --batch 16 \
  --epochs 100 \
  --data data.yaml \
  --weights yolov5s.pt \
  --name npc_detection
```

### 数据集配置（data.yaml）

```yaml
# data.yaml
train: ../dataset/images/train
val: ../dataset/images/val

# NPC 类别数量
nc: 34

# 类别名称
names:
  0: 门派师傅
  1: 门派师兄
  2: 门派师姐
  3: 门派守卫
  4: 杂货店老板
  5: 武器店老板
  6: 防具店老板
  7: 药店老板
  8: 客栈老板
  9: 驿站老板
  10: 捕快
  11: 衙门守卫
  12: 衙门师爷
  13: 商会会长
  14: 镖头
  15: 船夫
  16: 土地公公
  17: 太白金星
  18: 观音姐姐
  19: 店小二
  20: 小二
  21: 厨师
  22: 铁匠
  23: 裁缝
  24: 医生
  25: 当铺老板
  26: 书店老板
  27: 花店老板
  28: 渔夫
  29: 农夫
  30: 牧童
  31: 乞丐
  32: 商人
  33: 旅客
  34: 村民
```

## 📈 训练技巧

### 1. 数据增强

```python
# YOLOv8 自动数据增强
# 包括：翻转、旋转、色彩变换、Mosaic 等

# 自定义增强
augmentations = {
    'hsv_h': 0.015,    # 色调变化
    'hsv_s': 0.7,      # 饱和度变化
    'hsv_v': 0.4,      # 亮度变化
    'flipud': 0.0,     # 垂直翻转概率
    'fliplr': 0.5,     # 水平翻转概率
    'mosaic': 1.0,     # Mosaic 增强概率
}
```

### 2. 超参数调优

```bash
# 使用遗传算法调参
python train.py --evolve
```

### 3. 迁移学习

```python
# 使用预训练权重（推荐）
model = YOLO('yolov8n.pt')  # COCO 数据集预训练

# 冻结骨干网络（小数据集）
for param in model.model[:10].parameters():
    param.requires_grad = False
```

## 🧪 模型评估

### 评估指标

| 指标 | 含义 | 目标值 |
|------|------|--------|
| mAP@0.5 | IoU=0.5 时的平均精度 | > 0.85 |
| mAP@0.5:0.95 | 不同 IoU 下的平均精度 | > 0.60 |
| Precision | 查准率 | > 0.90 |
| Recall | 查全率 | > 0.85 |

### 可视化评估

```python
from ultralytics import YOLO
import cv2

model = YOLO('runs/detect/npc_detection/weights/best.pt')

# 测试图片
results = model('test_image.jpg')

# 可视化结果
results[0].show()
```

## 🚀 模型部署

### 导出为 ONNX

```python
# 导出模型
model.export(format='onnx', opset=12)

# 在 npc_recognition.py 中加载
detector = YOLODetector(model_path='npc_detection.onnx')
```

### 推理优化

```python
# 使用 TensorRT 加速（NVIDIA GPU）
model.export(format='engine', device=0)

# 使用 OpenVINO（Intel CPU）
model.export(format='openvino')
```

## 📝 常见问题

### Q1: 训练集损失下降，但验证集不下降？
**A**: 过拟合，解决方法：
- 增加训练数据
- 减少模型大小
- 增加数据增强
- 使用正则化

### Q2: 识别速度慢？
**A**: 
- 使用更小的模型（YOLOv8n）
- 降低输入分辨率（640→416）
- 使用 TensorRT 加速
- 批量推理

### Q3: 小 NPC 识别率低？
**A**:
- 增加小样本数据
- 使用更高分辨率训练
- 调整 anchor boxes
- 使用 P2 特征层

## 🎯 快速开始模板

### 1. 数据收集脚本

```python
import cv2
import time

def auto_screenshot(count=100):
    """自动截图"""
    cap = cv2.VideoCapture(0)  # 捕获游戏窗口
    
    for i in range(count):
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(f'dataset/raw/{i:04d}.png', frame)
            print(f'截图 {i+1}/{count}')
        time.sleep(0.5)
    
    cap.release()
```

### 2. 批量标注脚本

```python
# 使用预标注工具减少工作量
from roboflow import Roboflow

rf = Roboflow(api_key="YOUR_KEY")
project = rf.workspace().project("npc-detection")
project.upload(image_path='dataset/raw/')
```

### 3. 一键训练脚本

```bash
#!/bin/bash
# train.sh

# 准备数据
python prepare_dataset.py

# 训练模型
python train.py --epochs 100 --batch 16

# 评估
python val.py

# 导出
python export.py --format onnx
```

## 📚 参考资料

- [YOLOv8 官方文档](https://docs.ultralytics.com/)
- [YOLOv5 GitHub](https://github.com/ultralytics/yolov5)
- [LabelImg 标注工具](https://github.com/heartexlabs/labelImg)
- [Roboflow 数据集管理](https://roboflow.com/)

## 🎮 实战建议

### 第一阶段（1-2 天）
1. 收集 500 张截图
2. 标注 5 种重要 NPC（师傅、师兄、守卫等）
3. 训练基础模型

### 第二阶段（3-5 天）
1. 扩展到 2000 张截图
2. 标注所有 34 种 NPC
3. 优化模型性能

### 第三阶段（持续）
1. 收集困难样本
2. 迭代优化
3. 部署到生产环境

---

**最后更新**: 2026-03-20
