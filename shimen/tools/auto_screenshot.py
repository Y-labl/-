"""
游戏窗口自动截图工具
功能：
1. 自动捕获梦幻西游游戏窗口
2. 批量截图并保存
3. 支持定时截图和手动截图
"""

import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime
from typing import Optional, Tuple, List
import pygetwindow as gw


class GameWindowCapture:
    """
    游戏窗口截图工具
    """
    
    def __init__(self, window_title: str = None):
        """
        初始化窗口截图工具
        
        Args:
            window_title: 窗口标题（可选，自动检测梦幻西游窗口）
        """
        self.window_title = window_title
        self.window = None
        self.window_rect = None
        
        # 截图配置 - 使用 zhuagui 目录
        self.output_dir = "../zhuagui/dataset/raw_screenshots"
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"[配置] 截图保存目录：{self.output_dir}")
    
    def find_game_window(self) -> Optional[gw.Window]:
        """
        查找梦幻西游游戏窗口（优先查找主窗口，排除聊天窗口）
        
        Returns:
            窗口对象，未找到返回 None
        """
        # 可能的窗口标题关键词
        keywords = [
            "梦幻西游",
            "梦幻西游 ONLINE",
            "Fantasy Westward Journey",
            "MHXY"
        ]
        
        # 排除的关键词（聊天窗口等）
        exclude_keywords = [
            "聊天窗口",
            "聊天",
            "组队",
            "好友",
            "帮派",
            "邮件",
            "交易",
            "属性",
            "技能",
            "装备",
            "宠物",
            "坐骑",
            "精灵",
            "成就",
            "任务",
            "追踪",
            "设置",
            "系统",
            "登录",
            "启动"
        ]
        
        # 查找所有窗口
        all_windows = gw.getAllWindows()
        
        # 第一次遍历：查找主窗口（包含关键词但不包含排除关键词）
        for keyword in keywords:
            for window in all_windows:
                title_lower = window.title.lower()
                keyword_lower = keyword.lower()
                
                # 包含关键词
                if keyword_lower in title_lower:
                    # 检查是否包含排除关键词
                    is_excluded = False
                    for exclude in exclude_keywords:
                        if exclude.lower() in title_lower:
                            is_excluded = True
                            break
                    
                    # 不包含排除关键词，且窗口较大（主窗口特征）
                    if not is_excluded and window.width > 800 and window.height > 600:
                        print(f"[窗口] 找到游戏主窗口：{window.title}")
                        return window
        
        # 第二次遍历：如果没找到主窗口，返回最大的梦幻西游窗口
        for keyword in keywords:
            max_window = None
            max_area = 0
            
            for window in all_windows:
                if keyword.lower() in window.title.lower():
                    area = window.width * window.height
                    if area > max_area:
                        max_area = area
                        max_window = window
            
            if max_window:
                print(f"[窗口] 找到最大游戏窗口：{max_window.title}")
                return max_window
        
        print("[窗口] 未找到梦幻西游窗口")
        return None
    
    def activate_window(self, window_title: str = None) -> bool:
        """
        激活游戏窗口
        
        Args:
            window_title: 窗口标题
            
        Returns:
            是否成功激活
        """
        if window_title:
            self.window_title = window_title
        
        # 查找窗口
        self.window = self.find_game_window()
        
        if self.window is None:
            print("[错误] 找不到游戏窗口，请确保游戏已打开")
            return False
        
        # 获取窗口位置
        self.window_rect = {
            'left': self.window.left,
            'top': self.window.top,
            'width': self.window.width,
            'height': self.window.height
        }
        
        print(f"[窗口] 窗口位置：{self.window_rect}")
        
        # 激活窗口
        try:
            self.window.activate()
            time.sleep(0.5)  # 等待窗口激活
            print("[窗口] 窗口已激活")
            return True
        except Exception as e:
            print(f"[错误] 激活窗口失败：{e}")
            return False
    
    def capture(self, save: bool = True, filename: str = None) -> Optional[np.ndarray]:
        """
        捕获窗口截图
        
        Args:
            save: 是否保存到文件
            filename: 保存的文件名（可选，自动生成）
            
        Returns:
            截图（BGR 格式），失败返回 None
        """
        if self.window is None:
            if not self.activate_window():
                return None
        
        try:
            # 方法 1：使用 pyautogui 截取窗口区域
            screenshot = pyautogui.screenshot(
                region=(
                    self.window_rect['left'],
                    self.window_rect['top'],
                    self.window_rect['width'],
                    self.window_rect['height']
                )
            )
            
            # 转换为 OpenCV 格式（BGR）
            image = np.array(screenshot)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # 保存文件
            if save:
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"screenshot_{timestamp}.png"
                
                filepath = os.path.join(self.output_dir, filename)
                cv2.imwrite(filepath, image)
                print(f"[截图] 已保存：{filepath}")
            
            return image
            
        except Exception as e:
            print(f"[错误] 截图失败：{e}")
            return None
    
    def capture_batch(self, count: int, interval: float = 2.0) -> List[str]:
        """
        批量截图
        
        Args:
            count: 截图数量
            interval: 截图间隔（秒）
            
        Returns:
            保存的文件路径列表
        """
        print(f"[批量截图] 开始截图 {count} 张，间隔 {interval} 秒")
        
        saved_files = []
        
        # 确保窗口激活
        if not self.activate_window():
            return []
        
        for i in range(count):
            try:
                # 截图
                filename = f"batch_{i+1:04d}.png"
                filepath = os.path.join(self.output_dir, filename)
                
                image = self.capture(save=True, filename=filename)
                
                if image is not None:
                    saved_files.append(filepath)
                    print(f"[{i+1}/{count}] 截图成功")
                else:
                    print(f"[{i+1}/{count}] 截图失败")
                
                # 等待
                if i < count - 1:  # 最后一张不等待
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print(f"\n[中断] 用户中断截图，已完成 {i+1}/{count} 张")
                break
            except Exception as e:
                print(f"[错误] 第 {i+1} 张截图失败：{e}")
                continue
        
        print(f"[批量截图] 完成，成功 {len(saved_files)}/{count} 张")
        return saved_files
    
    def capture_with_hotkey(self, hotkey: str = 'f12'):
        """
        使用快捷键截图（监听模式）
        
        Args:
            hotkey: 快捷键
        """
        print(f"[快捷键截图] 按 '{hotkey}' 截图，按 'q' 退出")
        
        # 确保窗口激活
        if not self.activate_window():
            return
        
        count = 0
        
        while True:
            # 检测按键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # 简单实现：定时检查
            time.sleep(0.1)
            
            # 实际使用时可以用 pynput 监听键盘
            # 这里简化为每 5 秒自动截图
            count += 1
            filename = f"hotkey_{count:04d}.png"
            self.capture(save=True, filename=filename)
            print(f"[快捷键] 截图 {count}: {filename}")
    
    def get_window_info(self) -> dict:
        """
        获取窗口信息
        
        Returns:
            窗口信息字典
        """
        if self.window is None:
            self.window = self.find_game_window()
        
        if self.window:
            return {
                'title': self.window.title,
                'left': self.window.left,
                'top': self.window.top,
                'width': self.window.width,
                'height': self.window.height,
                'is_active': self.window.isActive
            }
        return {}


class NPCScreenshotHelper:
    """
    NPC 截图辅助工具
    专门用于收集 NPC 训练数据
    """
    
    def __init__(self, capture_tool: GameWindowCapture):
        """
        初始化 NPC 截图工具
        
        Args:
            capture_tool: 窗口截图工具实例
        """
        self.capture_tool = capture_tool
        self.npc_output_dir = "../zhuagui/dataset/npc_images"
        os.makedirs(self.npc_output_dir, exist_ok=True)
    
    def auto_capture_npc_areas(self, count: int = 100, 
                               interval: float = 3.0) -> List[str]:
        """
        自动捕获 NPC 聚集区域
        适用于长安城、门派等 NPC 密集地点
        
        Args:
            count: 截图数量
            interval: 截图间隔（秒）
            
        Returns:
            保存的文件路径列表
        """
        print(f"[NPC 截图] 开始自动截图 {count} 张")
        print("[提示] 请将游戏角色移动到 NPC 聚集区域（如长安城、门派内）")
        
        saved_files = []
        
        # 激活窗口
        if not self.capture_tool.activate_window():
            return []
        
        # 等待用户准备
        print("[倒计时] 5 秒后开始截图...")
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        # 批量截图
        for i in range(count):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"npc_{timestamp}_{i:04d}.png"
                filepath = os.path.join(self.npc_output_dir, filename)
                
                # 截图
                image = self.capture_tool.capture(save=True, filename=filename)
                
                if image is not None:
                    saved_files.append(filepath)
                    
                    # 显示预览（可选）
                    # cv2.imshow('Preview', image)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
                    
                    print(f"[{i+1}/{count}] NPC 截图完成")
                
                # 间隔等待
                if i < count - 1:
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print(f"\n[中断] 用户中断，已完成 {i+1}/{count} 张")
                break
        
        print(f"[NPC 截图] 完成，共 {len(saved_files)} 张")
        return saved_files
    
    def manual_capture_mode(self):
        """
        手动截图模式
        按空格键截图，按 q 退出
        """
        print("[手动模式] 按空格键截图，按 q 退出")
        
        if not self.capture_tool.activate_window():
            return
        
        count = 0
        
        print("[提示] 请切换到游戏窗口，然后按空格截图")
        
        # 使用 OpenCV 简单实现
        while True:
            # 显示提示
            print(f"\n已截图：{count} 张")
            action = input("按 Enter 截图，输入 'q' 退出：").strip().lower()
            
            if action == 'q':
                break
            
            # 截图
            count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manual_{timestamp}_{count:04d}.png"
            
            self.capture_tool.capture(save=True, filename=filename)
            print(f"✓ 已保存：{filename}")
    
    def rotate_capture(self, angles: List[int] = [90, 180, 270]):
        """
        旋转截图（数据增强）
        
        Args:
            angles: 旋转角度列表
        """
        print(f"[数据增强] 对已有截图进行旋转增强：{angles}")
        
        # 获取所有截图
        import glob
        files = glob.glob(os.path.join(self.npc_output_dir, "*.png"))
        
        enhanced_count = 0
        
        for filepath in files:
            try:
                image = cv2.imread(filepath)
                if image is None:
                    continue
                
                # 对每个角度旋转并保存
                for angle in angles:
                    # 旋转图像
                    if angle == 90:
                        rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                    elif angle == 180:
                        rotated = cv2.rotate(image, cv2.ROTATE_180)
                    elif angle == 270:
                        rotated = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    else:
                        continue
                    
                    # 保存增强后的图片
                    base_name = os.path.splitext(os.path.basename(filepath))[0]
                    new_filename = f"{base_name}_rot{angle}.png"
                    new_filepath = os.path.join(self.npc_output_dir, new_filename)
                    
                    cv2.imwrite(new_filepath, rotated)
                    enhanced_count += 1
                
            except Exception as e:
                print(f"[错误] 处理 {filepath} 失败：{e}")
        
        print(f"[数据增强] 完成，生成 {enhanced_count} 张增强图片")


# 主程序示例
if __name__ == "__main__":
    print("=" * 50)
    print("梦幻西游 NPC 截图工具")
    print("=" * 50)
    
    # 创建截图工具
    capture_tool = GameWindowCapture()
    
    # 显示窗口信息
    info = capture_tool.get_window_info()
    if info:
        print(f"\n[窗口信息]")
        print(f"标题：{info['title']}")
        print(f"位置：{info['left']}, {info['top']}")
        print(f"尺寸：{info['width']} x {info['height']}")
    else:
        print("\n[警告] 未找到游戏窗口，请先打开游戏")
    
    # 选择模式
    print("\n请选择截图模式：")
    print("1. 批量自动截图（推荐）")
    print("2. 手动截图")
    
    choice = input("\n请输入选择（1/2）：").strip()
    
    if choice == '1':
        # 批量截图
        try:
            count = int(input("请输入截图数量（默认 100）：").strip() or "100")
            interval = float(input("请输入间隔秒数（默认 3）：").strip() or "3")
        except:
            count, interval = 100, 3
        
        helper = NPCScreenshotHelper(capture_tool)
        helper.auto_capture_npc_areas(count=count, interval=interval)
        
    elif choice == '2':
        # 手动截图
        helper = NPCScreenshotHelper(capture_tool)
        helper.manual_capture_mode()
    
    else:
        print("无效选择")
    
    print("\n截图完成！")
    print(f"保存目录：{os.path.abspath('dataset/npc_images')}")
    print("\n下一步：使用 LabelImg 标注工具进行标注")
