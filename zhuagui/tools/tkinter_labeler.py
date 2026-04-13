"""
简易标注工具 - Tkinter 版本
稳定可靠的标注工具
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from pathlib import Path

# 配置
IMAGE_DIR = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\images")
LABEL_DIR = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\labels")
LABEL_DIR.mkdir(parents=True, exist_ok=True)

# 类别
CLASSES = ['马副将', '驿站老板', '黑无常', '钟馗', '主鬼', '小怪', '鼠标指针']

class LabelingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("梦幻西游抓鬼任务标注工具")
        
        # 当前状态
        self.current_idx = 0
        self.images = list(IMAGE_DIR.glob("*.png"))
        self.annotations = []
        self.current_class = 0
        
        # 绘图变量
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        
        # 创建界面
        self.create_ui(root)
        
        # 加载第一张图
        self.load_image(0)
        
    def create_ui(self, root):
        # 顶部工具栏
        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(toolbar, text="当前类别:").pack(side=tk.LEFT, padx=5)
        
        self.class_var = tk.StringVar(value=CLASSES[0])
        class_menu = tk.OptionMenu(toolbar, self.class_var, *CLASSES,
                                   command=self.change_class)
        class_menu.pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="上一张 (P)", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="下一张 (N)", command=self.next_image).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="保存 (S)", command=self.save_labels).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="退出 (Q)", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # 类别快捷键提示
        class_frame = tk.Frame(self.root)
        class_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(class_frame, text="快捷键: 0=马副将，1=驿站老板，2=黑无常，3=钟馗，4=主鬼，5=小怪，6=鼠标指针",
                fg="blue").pack()
        
        # 画布
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Key>", self.on_key)
        
        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def load_image(self, idx):
        if idx < 0 or idx >= len(self.images):
            return
        
        self.current_idx = idx
        img_path = self.images[idx]
        
        # 加载图片
        self.pil_image = Image.open(img_path)
        self.pil_image = self.pil_image.convert("RGB")
        
        # 调整大小适应窗口
        img_width = min(800, self.pil_image.width)
        img_height = min(600, self.pil_image.height)
        self.pil_image = self.pil_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        
        # 显示图片
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        
        # 加载已有标注
        self.load_existing_labels()
        
        # 更新状态
        self.status_var.set(f"图片：{idx + 1}/{len(self.images)} - {img_path.name}")
        
    def load_existing_labels(self):
        """加载已保存的标注"""
        self.annotations = []
        label_file = LABEL_DIR / f"{self.images[self.current_idx].stem}.txt"
        
        if label_file.exists():
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        x_center, y_center, width, height = map(float, parts[1:5])
                        
                        # 转换为像素坐标
                        img_w, img_h = self.pil_image.width, self.pil_image.height
                        x1 = (x_center - width/2) * img_w
                        y1 = (y_center - height/2) * img_h
                        x2 = (x_center + width/2) * img_w
                        y2 = (y_center + height/2) * img_h
                        
                        # 绘制已存在的框
                        color = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink'][class_id % 7]
                        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
                        self.canvas.create_text(x1, y1-5, text=CLASSES[class_id], 
                                              anchor=tk.SW, fill=color, font=('Arial', 10))
                        
                        self.annotations.append({
                            'class_id': class_id,
                            'x1': x1 / img_w,
                            'y1': y1 / img_h,
                            'x2': x2 / img_w,
                            'y2': y2 / img_h
                        })
    
    def change_class(self, value):
        self.current_class = CLASSES.index(value)
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
    def on_drag(self, event):
        if self.start_x is not None:
            if self.current_rect:
                self.canvas.delete(self.current_rect)
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2
            )
    
    def on_release(self, event):
        if self.start_x is not None and self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            
            # 确保坐标正确
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            
            # 保存标注
            img_w, img_h = self.pil_image.width, self.pil_image.height
            self.annotations.append({
                'class_id': self.current_class,
                'x1': x1 / img_w,
                'y1': y1 / img_h,
                'x2': x2 / img_w,
                'y2': y2 / img_h
            })
            
            # 绘制框
            color = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink'][self.current_class % 7]
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            self.canvas.create_text(x1, y1-5, text=CLASSES[self.current_class],
                                  anchor=tk.SW, fill=color, font=('Arial', 10))
            
            print(f"✓ 已标注：{CLASSES[self.current_class]}")
            
            self.start_x = None
            self.start_y = None
    
    def save_labels(self):
        """保存标注为 YOLO 格式"""
        if not self.annotations:
            return
        
        img_name = self.images[self.current_idx].stem
        label_file = LABEL_DIR / f"{img_name}.txt"
        
        with open(label_file, 'w') as f:
            for ann in self.annotations:
                # YOLO 格式：class x_center y_center width height
                x_center = (ann['x1'] + ann['x2']) / 2
                y_center = (ann['y1'] + ann['y2']) / 2
                width = ann['x2'] - ann['x1']
                height = ann['y2'] - ann['y1']
                f.write(f"{ann['class_id']} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        self.status_var.set(f"✓ 已保存：{label_file.name}")
        print(f"✓ 已保存：{label_file}")
    
    def next_image(self):
        if self.current_idx < len(self.images) - 1:
            self.save_labels()
            self.load_image(self.current_idx + 1)
    
    def prev_image(self):
        if self.current_idx > 0:
            self.save_labels()
            self.load_image(self.current_idx - 1)
    
    def on_key(self, event):
        key = event.char.lower()
        
        if key == 'q':
            self.save_labels()
            self.root.quit()
        elif key == 'n':
            self.next_image()
        elif key == 'p':
            self.prev_image()
        elif key == 's':
            self.save_labels()
        elif key in '0123456':
            idx = int(key)
            if idx < len(CLASSES):
                self.current_class = idx
                self.class_var.set(CLASSES[idx])
                self.status_var.set(f"当前类别：{CLASSES[idx]}")

def main():
    root = tk.Tk()
    
    # 设置窗口大小
    root.geometry("1000x700")
    
    app = LabelingTool(root)
    
    print("=" * 60)
    print("标注工具已启动")
    print("=" * 60)
    print(f"图片数量：{len(app.images)}")
    print("\n操作说明:")
    print("  鼠标拖动：框选 NPC")
    print("  数字键 0-6: 选择类别")
    print("  N: 下一张")
    print("  P: 上一张")
    print("  S: 保存")
    print("  Q: 退出")
    print("=" * 60)
    
    root.mainloop()
    
    print("\n标注完成！")

if __name__ == "__main__":
    main()
