# YOLO 模型训练完整流程指南

## 📋 概述

本指南带你完成从**零开始**到**训练出可用的 NPC 识别模型**的全过程。

---

## 🎯 数据需求

### 最低要求
- **图片数量**：800-1000 张标注图片
- **覆盖场景**：至少 3 个不同地点（如长安城、门派、野外）
- **标注质量**：每个 NPC 都要标注，框选准确

### 推荐配置
- **图片数量**：2000-3000 张标注图片
- **覆盖场景**：5+ 个地点，不同时间段
- **数据增强**：旋转、翻转、色彩变换

---

## 🚀 快速开始（4 步完成训练）

### 步骤 1：自动截图（10-30 分钟）

```bash
# 运行截图工具
cd d:\Program Files\mhxy\shimen
python tools/auto_screenshot.py
```

**操作步骤：**
1. 打开梦幻西游游戏
2. 运行截图脚本
3. 选择"批量自动截图"
4. 设置截图数量（建议 200-500 张）
5. 设置间隔时间（建议 3-5 秒）
6. 将游戏角色移动到 NPC 聚集地（如长安城）
7. 脚本自动截图

**建议地点：**
- ✅ 长安城（NPC 最多）
- ✅ 各门派内（师傅、师兄）
- ✅ 建邺城、傲来国
- ✅ 长寿村、地府等

---

### 步骤 2：自动标注（5-10 分钟）

```bash
# 运行自动标注工具
python tools/auto_labeler.py
```

**操作步骤：**
1. 选择"批量自动标注"
2. 输入图片目录（默认 `dataset/npc_images`）
3. 输入输出目录（默认 `dataset/yolo_dataset`）
4. 等待自动标注完成

**标注说明：**
- 首次使用没有模型，会使用**模拟标注**（基于颜色检测）
- 模拟标注准确率约 60-70%，需要人工修正
- 标注文件格式：YOLO 格式（class_id x y w h）

---

### 步骤 3：人工修正标注（30-60 分钟）

**方法 A：使用 LabelImg（推荐）**

```bash
# 安装 LabelImg
pip install labelImg

# 启动
labelImg
```

**操作步骤：**
1. 打开 LabelImg
2. 点击"Open Dir"，选择 `dataset/yolo_dataset/images`
3. 点击"Change Save Dir"，选择 `dataset/yolo_dataset/labels`
4. 选择"YOLO"标注格式
5. 逐张检查并修正标注

**修正要点：**
- ✅ 删除错误的检测框
- ✅ 补充漏标的 NPC
- ✅ 调整框选位置（要框住整个 NPC）
- ✅ 选择正确的类别

**快捷键：**
- `W`：绘制矩形框
- `A/D`：上一张/下一张
- `Ctrl+S`：保存
- `Del`：删除选中框
- `Ctrl+D`：复制当前标注到下一张

---

### 步骤 4：训练模型（1-2 小时）

```bash
# 运行训练脚本
python tools/train_yolo.py
```

**操作步骤：**
1. 选择模型大小：
   - `1` - YOLOv8n（nano，最快，推荐）
   - `2` - YOLOv8s（small，平衡）
   - `3` - YOLOv8m（medium，更准确）

2. 输入训练轮数（默认 100）

3. 等待训练完成

**训练输出：**
```
runs/detect/npc_detection/
├── weights/
│   ├── best.pt          # 最佳模型
│   └── last.pt          # 最后一轮模型
├── results.png          # 训练曲线
└── results.csv          # 训练数据
```

---

## 📊 模型评估

### 查看训练结果

```bash
# 评估模型
python tools/train_yolo.py eval
```

**关键指标：**
| 指标 | 含义 | 目标值 |
|------|------|--------|
| mAP@0.5 | IoU=0.5 时的平均精度 | > 0.85 |
| mAP@0.5:0.95 | 不同 IoU 下的平均精度 | > 0.60 |
| Precision | 查准率 | > 0.90 |
| Recall | 查全率 | > 0.85 |

### 可视化测试

```python
from ultralytics import YOLO

# 加载模型
model = YOLO('runs/detect/npc_detection/weights/best.pt')

# 测试图片
results = model('dataset/test_image.jpg')

# 显示结果
results[0].show()
```

---

## 🔄 迭代优化

### 第一轮训练后

1. **用模型预测新图片**
   ```bash
   python tools/auto_labeler.py
   ```

2. **修正错误标注**
   - 模型预测的结果通常有 70-80% 准确率
   - 人工修正错误部分

3. **重新训练**
   ```bash
   python tools/train_yolo.py
   ```

4. **重复 2-3 轮**，准确率可达 90%+

---

## 💡 数据增强

### 方法 1：截图工具自带增强

```bash
python tools/auto_screenshot.py
# 选择"数据增强"选项
# 自动旋转、翻转生成新图片
```

### 方法 2：手动增强

```python
import cv2
import os

# 读取图片
image = cv2.imread('image.jpg')

# 旋转
rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

# 翻转
flipped = cv2.flip(image, 1)

# 色彩调整
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
hsv[:, :, 2] = hsv[:, :, 2] * 1.2  # 增亮

# 保存
cv2.imwrite('image_aug.jpg', augmented)
```

---

## 📦 模型导出

### 导出为 ONNX（推荐）

```bash
python tools/train_yolo.py export runs/detect/npc_detection/weights/best.pt onnx
```

**用途：**
- ✅ 部署到生产环境
- ✅ 跨平台使用
- ✅ 推理速度快

### 导出为 TensorRT（NVIDIA GPU）

```bash
python tools/train_yolo.py export best.pt engine
```

**优势：**
- ✅ 推理速度提升 3-5 倍
- ✅ 适合实时检测

---

## 🎮 实战技巧

### 技巧 1：优先标注核心 NPC

**优先级：**
1. ⭐⭐⭐⭐⭐ 门派师傅（最重要）
2. ⭐⭐⭐⭐ 门派师兄、守卫
3. ⭐⭐⭐ 各种店老板
4. ⭐⭐ 其他 NPC

### 技巧 2：困难样本重点标注

**困难场景：**
- NPC 被遮挡
- 夜晚/雨天光线暗
- NPC 距离远
- 多个 NPC 聚集

**处理方法：**
- 单独收集这些场景
- 增加标注密度
- 训练时增加权重

### 技巧 3：增量训练

**场景：**
- 发现新 NPC 类型识别不了
- 某些场景识别率特别低

**方法：**
1. 收集困难样本（100-200 张）
2. 标注
3. 在原有模型基础上继续训练
   ```bash
   python tools/train_yolo.py --weights best.pt --epochs 50
   ```

---

## 🐛 常见问题

### Q1: 训练时报错 CUDA out of memory？
**A**: 显存不足，解决方法：
- 减小 batch_size（16 → 8 → 4）
- 减小 img_size（640 → 416）
- 使用更小的模型（YOLOv8n）

### Q2: 训练损失不下降？
**A**: 
- 检查标注质量（可能有错误标注）
- 增加学习率（lr0: 0.01 → 0.02）
- 增加数据增强

### Q3: 验证集准确率高，但实际效果差？
**A**: 过拟合
- 增加训练数据
- 减少训练轮数（早停）
- 增加数据增强
- 使用更小的模型

### Q4: 小 NPC（远距离）识别不到？
**A**:
- 使用更高分辨率训练（img_size: 640 → 1280）
- 增加小样本数据
- 调整模型 anchor boxes

---

## 📈 训练计划

### 第一天：数据收集
- [ ] 截图 500-1000 张
- [ ] 覆盖 3+ 个地点
- [ ] 包含不同时间段

### 第二天：标注
- [ ] 自动标注（30 分钟）
- [ ] 人工修正（2-3 小时）
- [ ] 目标：标注 800+ 张

### 第三天：训练
- [ ] 运行训练脚本（1-2 小时）
- [ ] 查看训练结果
- [ ] 测试模型效果

### 第四天及以后：优化
- [ ] 收集困难样本
- [ ] 迭代训练 2-3 轮
- [ ] 集成到导航系统

---

## 🎯 预期效果

### 第一轮训练后
- mAP@0.5: 0.70-0.80
- 核心 NPC 识别率：80%+
- 可用于辅助标注

### 第二轮训练后
- mAP@0.5: 0.85-0.90
- 核心 NPC 识别率：90%+
- 可用于生产环境

### 第三轮训练后
- mAP@0.5: 0.90-0.95
- 综合识别率：90%+
- 满足师门任务需求

---

## 📚 参考资料

- [YOLOv8 官方文档](https://docs.ultralytics.com/)
- [LabelImg 标注工具](https://github.com/heartexlabs/labelImg)
- [YOLO 数据增强技巧](https://docs.ultralytics.com/guides/augmentation/)

---

## 🆘 获取帮助

遇到问题？
1. 查看训练日志：`runs/detect/npc_detection/results.csv`
2. 查看可视化结果：`runs/detect/npc_detection/results.png`
3. 检查数据集结构是否符合标准

---

**最后更新**: 2026-03-20  
**文档版本**: v1.0
