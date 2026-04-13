"""
导标旗图像识别模块
使用传统图像识别技术（模板匹配 + OCR）
原因：
1. 导标旗界面规则，位置固定
2. 主要是文字识别，不需要复杂的目标检测
3. 开发成本低，维护简单
4. 速度快，准确率高
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import time


class FlagTemplateMatcher:
    """
    导标旗模板匹配器
    用于识别 ALT+T 界面中的导标旗图标和位置
    """
    
    def __init__(self, template_dir: str = "templates/flags"):
        """
        初始化模板匹配器
        
        Args:
            template_dir: 模板图片目录
        """
        self.template_dir = template_dir
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """加载导标旗模板图片"""
        import os
        
        # 导标旗相关模板
        template_files = {
            "flag_icon": "flag_icon.png",      # 导标旗小图标
            "flag_slot": "flag_slot.png",      # 导标旗插槽背景
            "selected": "selected.png",        # 选中状态标记
            "lock_icon": "lock_icon.png",      # 锁定图标（不可用）
        }
        
        for name, filename in template_files.items():
            path = os.path.join(self.template_dir, filename)
            if os.path.exists(path):
                template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                self.templates[name] = template
                print(f"[模板] 已加载：{name}")
            else:
                print(f"[模板] 未找到：{path}")
    
    def find_flag_slots(self, screenshot: np.ndarray) -> List[Dict]:
        """
        查找截图中所有导标旗插槽位置
        
        Args:
            screenshot: 游戏截图（BGR 格式）
            
        Returns:
            导标旗插槽位置列表
        """
        if 'flag_slot' not in self.templates:
            # 如果没有模板，返回预设位置（ALT+T 界面的固定位置）
            return self._get_default_slot_positions()
        
        # 转换为灰度图
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template = self.templates['flag_slot']
        
        # 模板匹配
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        
        # 设置匹配阈值
        threshold = 0.8
        locations = np.where(result >= threshold)
        
        # 处理匹配结果
        slots = []
        h, w = template.shape
        points = list(zip(*locations[::-1]))
        
        # 去重（合并相邻的检测结果）
        merged_points = self._merge_nearby_points(points, min_distance=10)
        
        for pt in merged_points:
            slots.append({
                'x': pt[0],
                'y': pt[1],
                'width': w,
                'height': h,
                'center_x': pt[0] + w // 2,
                'center_y': pt[1] + h // 2
            })
        
        return slots
    
    def _get_default_slot_positions(self) -> List[Dict]:
        """
        返回默认的导标旗插槽位置（ALT+T 界面的固定布局）
        实际使用时需要根据游戏界面调整
        """
        slots = []
        # 假设导标旗列表是垂直排列，每行 5 个，共 4 行
        start_x = 150
        start_y = 120
        slot_width = 60
        slot_height = 60
        gap_x = 10
        gap_y = 10
        
        for row in range(4):
            for col in range(5):
                x = start_x + col * (slot_width + gap_x)
                y = start_y + row * (slot_height + gap_y)
                slots.append({
                    'x': x,
                    'y': y,
                    'width': slot_width,
                    'height': slot_height,
                    'center_x': x + slot_width // 2,
                    'center_y': y + slot_height // 2
                })
        
        return slots
    
    def _merge_nearby_points(self, points: List[Tuple[int, int]], 
                            min_distance: int = 10) -> List[Tuple[int, int]]:
        """
        合并相邻的匹配点（避免重复检测）
        
        Args:
            points: 匹配点列表
            min_distance: 最小间距
            
        Returns:
            合并后的点列表
        """
        if not points:
            return []
        
        merged = []
        used = set()
        
        for i, pt1 in enumerate(points):
            if i in used:
                continue
            
            # 查找所有相邻点
            nearby = [pt1]
            for j, pt2 in enumerate(points[i+1:], i+1):
                if j in used:
                    continue
                
                dist = np.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)
                if dist <= min_distance:
                    nearby.append(pt2)
                    used.add(j)
            
            # 计算平均位置
            avg_x = sum(pt[0] for pt in nearby) // len(nearby)
            avg_y = sum(pt[1] for pt in nearby) // len(nearby)
            merged.append((avg_x, avg_y))
            used.add(i)
        
        return merged
    
    def detect_flag_status(self, screenshot: np.ndarray, slot_rect: Dict) -> Dict:
        """
        检测单个导标旗的状态（是否可用、是否选中）
        
        Args:
            screenshot: 游戏截图
            slot_rect: 插槽矩形区域
            
        Returns:
            导标旗状态字典
        """
        x, y, w, h = slot_rect['x'], slot_rect['y'], slot_rect['width'], slot_rect['height']
        roi = screenshot[y:y+h, x:x+w]
        
        status = {
            'has_flag': False,
            'is_locked': False,
            'is_selected': False
        }
        
        # 检测是否有导标旗（通过颜色或模板）
        # 简化实现：检测区域是否有足够的颜色变化
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        variance = np.var(gray_roi)
        status['has_flag'] = variance > 100  # 有旗帜时方差较大
        
        # 检测锁定状态（查找锁图标）
        if 'lock_icon' in self.templates:
            lock_template = self.templates['lock_icon']
            result = cv2.matchTemplate(gray_roi, lock_template, cv2.TM_CCOEFF_NORMED)
            if np.max(result) >= 0.8:
                status['is_locked'] = True
        
        # 检测选中状态
        if 'selected' in self.templates:
            selected_template = self.templates['selected']
            result = cv2.matchTemplate(gray_roi, selected_template, cv2.TM_CCOEFF_NORMED)
            if np.max(result) >= 0.8:
                status['is_selected'] = True
        
        return status


class FlagOCRRecognizer:
    """
    导标旗 OCR 识别器
    识别导标旗名称文字
    """
    
    def __init__(self, ocr_service):
        """
        初始化 OCR 识别器
        
        Args:
            ocr_service: OCR 服务实例（百度 OCR/PaddleOCR 等）
        """
        self.ocr_service = ocr_service
    
    def recognize_flag_name(self, screenshot: np.ndarray, 
                           slot_rect: Dict) -> Optional[str]:
        """
        识别单个导标旗的名称
        
        Args:
            screenshot: 游戏截图
            slot_rect: 插槽矩形区域
            
        Returns:
            导标旗名称，识别失败返回 None
        """
        x, y, w, h = slot_rect['x'], slot_rect['y'], slot_rect['width'], slot_rect['height']
        
        # 截取文字区域（通常在插槽下方或上方）
        # 假设文字在插槽下方 5 像素处，高度 20 像素
        text_y = y + h + 5
        text_height = 20
        text_roi = screenshot[text_y:text_y+text_height, x-10:x+w+10]
        
        # OCR 识别
        try:
            result = self.ocr_service.recognize(text_roi)
            if result:
                # 清理识别结果
                name = self._clean_text(result)
                return name
        except Exception as e:
            print(f"[OCR] 识别失败：{e}")
        
        return None
    
    def recognize_all_flags(self, screenshot: np.ndarray, 
                           slots: List[Dict]) -> List[Dict]:
        """
        批量识别所有导标旗
        
        Args:
            screenshot: 游戏截图
            slots: 插槽位置列表
            
        Returns:
            导标旗信息列表
        """
        flags = []
        
        for i, slot in enumerate(slots):
            print(f"[OCR] 识别第 {i+1}/{len(slots)} 个导标旗...")
            
            name = self.recognize_flag_name(screenshot, slot)
            
            if name:
                flags.append({
                    'index': i,
                    'name': name,
                    'position': slot,
                    'valid': True
                })
                print(f"[OCR] 识别到：{name}")
            else:
                flags.append({
                    'index': i,
                    'name': None,
                    'position': slot,
                    'valid': False
                })
        
        return flags
    
    def _clean_text(self, text: str) -> str:
        """
        清理 OCR 识别结果
        
        Args:
            text: 原始识别文本
            
        Returns:
            清理后的文本
        """
        import re
        
        # 去除特殊字符
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
        
        # 去除常见误识别
        noise_patterns = ['O', 'o', '0', '口', '囗']
        for pattern in noise_patterns:
            text = text.replace(pattern, '')
        
        # 去除前后空格
        text = text.strip()
        
        return text


class FlagInterfaceDetector:
    """
    导标旗界面检测器
    检测 ALT+T 界面是否打开，并定位界面区域
    """
    
    def __init__(self):
        """初始化界面检测器"""
        # 导标旗界面特征（右上角的"导标旗"标题）
        self.interface_template = None
        self.interface_rect = None
    
    def is_interface_open(self, screenshot: np.ndarray) -> bool:
        """
        检测导标旗界面是否已打开
        
        Args:
            screenshot: 游戏截图
            
        Returns:
            是否已打开
        """
        # 方法 1：检测界面特征区域的颜色
        # 导标旗界面有特定的背景色和布局
        
        # 方法 2：检测特定 UI 元素（如关闭按钮 X）
        # 简化实现：检测界面右上角区域
        
        interface_area = screenshot[50:150, 300:500]  # 示例区域
        
        # 检测界面特征（蓝色背景）
        hsv = cv2.cvtColor(interface_area, cv2.COLOR_BGR2HSV)
        
        # 蓝色范围
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 如果蓝色区域占比超过阈值，认为界面已打开
        blue_ratio = np.sum(mask > 0) / mask.size
        return blue_ratio > 0.3
    
    def get_interface_bounds(self, screenshot: np.ndarray) -> Optional[Dict]:
        """
        获取导标旗界面的边界
        
        Args:
            screenshot: 游戏截图
            
        Returns:
            界面边界信息
        """
        # 简化实现：返回固定位置
        # 实际需要根据界面检测动态计算
        return {
            'x': 100,
            'y': 80,
            'width': 600,
            'height': 400
        }


class FlagRecognitionSystem:
    """
    导标旗识别系统（总控制器）
    整合模板匹配和 OCR 识别
    """
    
    def __init__(self, ocr_service):
        """
        初始化导标旗识别系统
        
        Args:
            ocr_service: OCR 服务实例
        """
        self.template_matcher = FlagTemplateMatcher()
        self.ocr_recognizer = FlagOCRRecognizer(ocr_service)
        self.interface_detector = FlagInterfaceDetector()
    
    def detect_and_recognize(self, screenshot: np.ndarray) -> List[Dict]:
        """
        检测并识别导标旗
        
        Args:
            screenshot: 游戏截图
            
        Returns:
            导标旗信息列表
        """
        # 1. 检测界面是否打开
        if not self.interface_detector.is_interface_open(screenshot):
            print("[识别] 导标旗界面未打开")
            return []
        
        # 2. 查找所有导标旗插槽
        slots = self.template_matcher.find_flag_slots(screenshot)
        print(f"[识别] 找到 {len(slots)} 个导标旗插槽")
        
        # 3. 批量识别导标旗名称
        flags = self.ocr_recognizer.recognize_all_flags(screenshot, slots)
        
        # 4. 检测每个导标旗的状态
        for flag in flags:
            if flag['valid']:
                status = self.template_matcher.detect_flag_status(
                    screenshot, flag['position']
                )
                flag.update(status)
        
        # 5. 过滤掉无效的导标旗
        valid_flags = [f for f in flags if f['valid']]
        
        return valid_flags
    
    def open_flag_interface(self, window_manager):
        """
        打开导标旗界面
        
        Args:
            window_manager: 窗口管理器实例
        """
        print("[识别] 打开导标旗界面...")
        window_manager.press_hotkey('alt', 't')
        time.sleep(0.5)
        
        # 等待界面加载
        for i in range(10):
            screenshot = window_manager.capture_screen()
            if self.interface_detector.is_interface_open(screenshot):
                print("[识别] 界面已打开")
                return True
            time.sleep(0.2)
        
        print("[识别] 界面打开超时")
        return False
    
    def close_flag_interface(self, window_manager):
        """关闭导标旗界面"""
        print("[识别] 关闭导标旗界面...")
        window_manager.press_key('esc')
        time.sleep(0.3)


# 使用示例
if __name__ == "__main__":
    # 伪代码示例
    # ocr_service = OCRService()
    # flag_system = FlagRecognitionSystem(ocr_service)
    
    # # 打开界面
    # flag_system.open_flag_interface(window_manager)
    
    # # 截图识别
    # screenshot = window_manager.capture_screen()
    # flags = flag_system.detect_and_recognize(screenshot)
    
    # # 关闭界面
    # flag_system.close_flag_interface(window_manager)
    
    # for flag in flags:
    #     print(f"导标旗：{flag['name']} - 位置：{flag['position']}")
    pass
