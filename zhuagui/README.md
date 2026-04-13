# 抓鬼任务 - 截图数据保存位置

## 📁 保存路径

所有截图数据都保存在：

```
D:\Program Files\mhxy\zhuagui\dataset\
```

### 具体目录结构

```
zhuagui/
└── dataset/
    ├── raw_screenshots/     ← 原始截图（自动保存）
    └── npc_images/          ← NPC 训练图片（用于标注）
```

---

## 📸 截图保存位置

### 1. 自动截图（批量模式）

**保存路径**：
```
D:\Program Files\mhxy\zhuagui\dataset\raw_screenshots\
```

**文件名格式**：
```
screenshot_20260320_211030.png
screenshot_20260320_211033.png
...
```

### 2. NPC 训练图片（NPC 截图模式）

**保存路径**：
```
D:\Program Files\mhxy\zhuagui\dataset\npc_images\
```

**文件名格式**：
```
npc_20260320_211030_0001.png
npc_20260320_211033_0002.png
...
```

---

## 🎯 查看截图

### 方法 1：文件资源管理器

1. 打开"此电脑"或"文件资源管理器"
2. 进入目录：`D:\Program Files\mhxy\zhuagui\`
3. 打开 `dataset` 文件夹
4. 查看截图：
   - `raw_screenshots` - 原始截图
   - `npc_images` - NPC 训练图片

### 方法 2：命令行

```cmd
cd D:\Program Files\mhxy\zhuagui\dataset
dir
```

---

## 📊 截图统计

### 查看截图数量

**方法 1：文件资源管理器**
- 右键文件夹 → 属性 → 查看文件数量

**方法 2：命令行**
```cmd
cd D:\Program Files\mhxy\zhuagui\dataset\npc_images
dir /b | find /c ".png"
```

---

## 🔄 下一步

截图完成后：

1. **检查截图质量**
   - 打开 `D:\Program Files\mhxy\zhuagui\dataset\npc_images\`
   - 随机打开几张查看
   - 确保 NPC 清晰可见，头顶名字能看到

2. **运行自动标注**
   ```cmd
   cd D:\Program Files\mhxy\shimen
   python tools\auto_labeler.py
   ```

3. **人工修正标注**
   - 使用 LabelImg 工具
   - 标注 NPC 位置

---

## 📝 截图计划

| NPC | 目标数量 | 保存位置 |
|-----|---------|---------|
| 马副将 | 150 张 | npc_images/ |
| 驿站老板 | 200 张 | npc_images/ |
| 黑无常 | 200 张 | npc_images/ |
| 钟馗 | 200 张 | npc_images/ |
| 主鬼 | 200 张 | npc_images/ |
| 小怪 | 150 张 | npc_images/ |
| **总计** | **1100 张** | - |

---

**最后更新**: 2026-03-20  
**文档状态**: 可用
