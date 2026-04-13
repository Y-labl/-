"""
YOLO 训练快速启动脚本
一键完成：截图 → 标注 → 训练
"""

import os
import sys
from datetime import datetime


def print_banner(text: str):
    """打印横幅"""
    print("\n" + "=" * 60)
    print(text.center(60))
    print("=" * 60 + "\n")


def check_dependencies():
    """检查依赖"""
    print_banner("检查依赖")
    
    missing = []
    
    try:
        import cv2
        print("✓ OpenCV")
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import numpy
        print("✓ NumPy")
    except ImportError:
        missing.append("numpy")
    
    try:
        import pyautogui
        print("✓ PyAutoGUI")
    except ImportError:
        missing.append("pyautogui")
    
    try:
        from ultralytics import YOLO
        print("✓ Ultralytics (YOLOv8)")
    except ImportError:
        missing.append("ultralytics")
    
    try:
        import yaml
        print("✓ PyYAML")
    except ImportError:
        missing.append("pyyaml")
    
    if missing:
        print(f"\n[警告] 缺少依赖包：{', '.join(missing)}")
        print(f"[提示] 请运行：pip install {' '.join(missing)}")
        return False
    
    print("\n[成功] 所有依赖已安装")
    return True


def step1_screenshot():
    """步骤 1：截图"""
    print_banner("步骤 1：自动截图")
    
    print("此步骤将自动截取游戏窗口中的 NPC 图片")
    print("建议截图数量：500-1000 张")
    print("截图地点：长安城、各门派等 NPC 聚集地\n")
    
    try:
        from tools.auto_screenshot import GameWindowCapture, NPCScreenshotHelper
        
        capture_tool = GameWindowCapture()
        
        # 检查窗口
        info = capture_tool.get_window_info()
        if not info:
            print("[错误] 未找到游戏窗口，请先打开梦幻西游")
            return False
        
        print(f"[窗口] {info['title']}")
        print(f"[尺寸] {info['width']} x {info['height']}\n")
        
        # 选择截图模式
        print("请选择截图模式：")
        print("1. 批量自动截图（推荐）")
        print("2. 手动截图")
        
        choice = input("\n请选择（1/2）：").strip()
        
        helper = NPCScreenshotHelper(capture_tool)
        
        if choice == '1':
            # 批量截图
            try:
                count = int(input("截图数量（默认 500）：").strip() or "500")
                interval = float(input("间隔秒数（默认 3）：").strip() or "3")
            except:
                count, interval = 500, 3
            
            print(f"\n[提示] 请将游戏角色移动到 NPC 聚集地")
            input("准备好后按 Enter 开始...")
            
            helper.auto_capture_npc_areas(count=count, interval=interval)
        
        elif choice == '2':
            helper.manual_capture_mode()
        
        else:
            print("无效选择")
            return False
        
        print(f"\n[完成] 截图已保存到：dataset/npc_images")
        return True
        
    except Exception as e:
        print(f"[错误] 截图失败：{e}")
        return False


def step2_label():
    """步骤 2：自动标注"""
    print_banner("步骤 2：自动标注")
    
    print("此步骤将使用预训练模型自动标注 NPC")
    print("如果没有模型，将使用模拟标注（需要人工修正）\n")
    
    try:
        from tools.auto_labeler import AutoLabeler
        
        labeler = AutoLabeler(model_path=None)  # 首次使用没有模型
        
        image_dir = "dataset/npc_images"
        if not os.path.exists(image_dir):
            print(f"[错误] 找不到图片目录：{image_dir}")
            print("[提示] 请先完成步骤 1：截图")
            return False
        
        output_dir = "dataset/yolo_dataset"
        
        print(f"[输入] {image_dir}")
        print(f"[输出] {output_dir}\n")
        
        # 批量标注
        stats = labeler.label_batch(image_dir, output_dir)
        
        print(f"\n[标注统计]")
        print(f"  总图片：{stats['total']}")
        print(f"  已标注：{stats['labeled']}")
        print(f"  检测数：{stats['total_detections']}")
        
        print(f"\n[下一步]")
        print(f"  1. 使用 LabelImg 检查并修正标注")
        print(f"  2. 运行命令：labelImg")
        
        return True
        
    except Exception as e:
        print(f"[错误] 标注失败：{e}")
        return False


def step3_train():
    """步骤 3：训练模型"""
    print_banner("步骤 3：训练 YOLO 模型")
    
    print("此步骤将训练 NPC 识别模型")
    print("预计时间：30 分钟 - 2 小时（取决于 GPU）\n")
    
    try:
        from tools.train_yolo import quick_train
        
        dataset_path = "dataset/yolo_dataset"
        if not os.path.exists(dataset_path):
            print(f"[错误] 找不到数据集：{dataset_path}")
            print("[提示] 请先完成步骤 2：标注")
            return False
        
        # 开始训练
        quick_train()
        
        return True
        
    except Exception as e:
        print(f"[错误] 训练失败：{e}")
        return False


def main():
    """主函数"""
    print_banner("YOLO 训练快速启动")
    print("本工具将带你完成：截图 → 标注 → 训练 全流程\n")
    
    # 检查依赖
    if not check_dependencies():
        print("\n[提示] 安装依赖后请重新运行")
        return
    
    # 选择流程
    print("\n请选择：")
    print("1. 完整流程（推荐新手）")
    print("2. 仅截图")
    print("3. 仅标注")
    print("4. 仅训练")
    
    choice = input("\n请选择（1/2/3/4）：").strip()
    
    success = False
    
    if choice == '1':
        # 完整流程
        print("\n" + "=" * 60)
        print("开始完整流程")
        print("=" * 60)
        
        print("\n[步骤 1/3] 截图")
        if not step1_screenshot():
            print("[跳过] 截图失败")
        
        print("\n[步骤 2/3] 标注")
        if not step2_label():
            print("[跳过] 标注失败")
        
        print("\n[步骤 3/3] 训练")
        if not step3_train():
            print("[跳过] 训练失败")
        
        success = True
        
    elif choice == '2':
        success = step1_screenshot()
    
    elif choice == '3':
        success = step2_label()
    
    elif choice == '4':
        success = step3_train()
    
    else:
        print("无效选择")
        return
    
    # 完成
    if success:
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print("=" * 60)
        print("\n[输出文件]")
        print("  截图：dataset/npc_images/")
        print("  标注：dataset/yolo_dataset/")
        print("  模型：runs/detect/npc_detection/weights/best.pt")
        
        print("\n[下一步]")
        print("  1. 测试模型效果")
        print("  2. 集成到导航系统")
        print("  3. 继续收集困难样本，迭代优化")
        
        print("\n[提示]")
        print("  详细文档：docs/YOLO 训练完整流程.md")


if __name__ == "__main__":
    main()
