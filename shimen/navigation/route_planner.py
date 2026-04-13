"""
导标旗识别与自动路线规划模块
功能：
1. 识别导标旗（ALT+T 界面）
2. 根据任务目标自动规划最优路线
3. 支持导标旗传送 + 坐标寻路的混合导航
"""

import time
import json
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class NavigationMethod(Enum):
    """导航方式枚举"""
    FLAG = "flag"  # 导标旗传送
    COORDINATE = "coordinate"  # 坐标寻路
    WALK = "walk"  # 步行


@dataclass
class FlagInfo:
    """导标旗信息类"""
    name: str  # 导标旗名称
    map_name: str  # 所在地图
    x: int  # X 坐标
    y: int  # Y 坐标
    enabled: bool = True  # 是否可用


@dataclass
class RouteSegment:
    """路线段类"""
    from_point: str  # 起点
    to_point: str  # 终点
    method: NavigationMethod  # 导航方式
    target: str  # 目标（导标旗名称或坐标）
    estimated_time: int  # 预计时间（秒）


@dataclass
class Route:
    """完整路线类"""
    segments: List[RouteSegment]  # 路线段列表
    total_time: int  # 总预计时间
    description: str  # 路线描述


class FlagManager:
    """
    导标旗管理模块
    负责导标旗的识别、配置和管理
    """
    
    def __init__(self, window_manager, ocr_service):
        """
        初始化导标旗管理器
        
        Args:
            window_manager: 窗口管理器实例
            ocr_service: OCR 服务实例
        """
        self.window_manager = window_manager
        self.ocr_service = ocr_service
        self.flags: Dict[str, FlagInfo] = {}
        self.config_file = "config/flags_config.json"
        self.load_flags()
    
    def load_flags(self):
        """从配置文件加载导标旗信息"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self.flags[name] = FlagInfo(
                            name=name,
                            map_name=info['map'],
                            x=info['x'],
                            y=info['y'],
                            enabled=info.get('enabled', True)
                        )
                print(f"[导标旗] 已加载 {len(self.flags)} 个导标旗配置")
            except Exception as e:
                print(f"[导标旗] 加载配置文件失败：{e}")
        else:
            print(f"[导标旗] 配置文件不存在，使用默认配置")
            self._init_default_flags()
    
    def _init_default_flags(self):
        """初始化默认导标旗配置（示例）"""
        default_flags = {
            "长安城酒店": FlagInfo("长安城酒店", "长安城", 450, 100),
            "长安城驿站": FlagInfo("长安城驿站", "长安城", 380, 20),
            "长安城商会": FlagInfo("长安城商会", "长安城", 520, 180),
            "建邺城衙门": FlagInfo("建邺城衙门", "建邺城", 120, 80),
            "傲来国驿站": FlagInfo("傲来国驿站", "傲来国", 200, 150),
        }
        self.flags.update(default_flags)
        self.save_flags()
    
    def save_flags(self):
        """保存导标旗配置到文件"""
        data = {}
        for name, flag in self.flags.items():
            data[name] = {
                'map': flag.map_name,
                'x': flag.x,
                'y': flag.y,
                'enabled': flag.enabled
            }
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def detect_flags(self) -> List[str]:
        """
        检测当前可用的导标旗
        通过 ALT+T 打开导标旗界面，OCR 识别可用导标旗
        
        Returns:
            可用导标旗名称列表
        """
        print("[导标旗] 开始检测可用导标旗...")
        
        # 1. 按 ALT+T 打开导标旗界面
        self.window_manager.press_hotkey('alt', 't')
        time.sleep(0.5)
        
        # 2. 截图导标旗界面区域
        # 假设导标旗界面在固定位置
        flag_interface_rect = (100, 100, 400, 500)  # 示例坐标
        screenshot = self.window_manager.capture_region(*flag_interface_rect)
        
        # 3. OCR 识别导标旗名称
        flag_names = []
        try:
            ocr_result = self.ocr_service.recognize(screenshot)
            # 解析 OCR 结果，提取导标旗名称
            flag_names = self._parse_flag_names(ocr_result)
            print(f"[导标旗] 检测到 {len(flag_names)} 个可用导标旗：{flag_names}")
        except Exception as e:
            print(f"[导标旗] OCR 识别失败：{e}")
        
        # 4. 关闭导标旗界面（ESC）
        self.window_manager.press_key('esc')
        time.sleep(0.3)
        
        return flag_names
    
    def _parse_flag_names(self, ocr_text: str) -> List[str]:
        """
        从 OCR 文本中解析导标旗名称
        
        Args:
            ocr_text: OCR 识别的原始文本
            
        Returns:
            导标旗名称列表
        """
        flag_names = []
        # 简单的按行解析，实际需要根据界面布局优化
        lines = ocr_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:  # 过滤空行和过短文本
                # 检查是否是导标旗名称（可根据命名规则优化）
                if any(keyword in line for keyword in ['驿站', '酒店', '衙门', '镖局', '传送']):
                    flag_names.append(line)
        
        return flag_names
    
    def get_flag_by_name(self, name: str) -> Optional[FlagInfo]:
        """根据名称获取导标旗信息"""
        return self.flags.get(name)
    
    def get_flags_by_map(self, map_name: str) -> List[FlagInfo]:
        """获取指定地图的所有导标旗"""
        return [flag for flag in self.flags.values() 
                if flag.map_name == map_name and flag.enabled]
    
    def add_flag(self, name: str, map_name: str, x: int, y: int):
        """添加新的导标旗配置"""
        self.flags[name] = FlagInfo(name, map_name, x, y)
        self.save_flags()
        print(f"[导标旗] 已添加：{name} ({map_name} [{x},{y}])")


class RoutePlanner:
    """
    路线规划模块
    根据任务目标和可用导标旗，自动规划最优路线
    """
    
    def __init__(self, flag_manager: FlagManager):
        """
        初始化路线规划器
        
        Args:
            flag_manager: 导标旗管理器实例
        """
        self.flag_manager = flag_manager
        self.map_connections = self._init_map_connections()
    
    def _init_map_connections(self) -> Dict[str, List[str]]:
        """初始化地图连接关系（用于寻路算法）"""
        return {
            "长安城": ["建邺城", "傲来国", "大唐官府", "化生寺", "方寸山"],
            "建邺城": ["长安城", "东海湾", "沉船"],
            "傲来国": ["长安城", "花果山", "北俱芦洲"],
            "大唐官府": ["长安城"],
            "化生寺": ["长安城"],
            "方寸山": ["长安城"],
            "东海湾": ["建邺城", "长寿村"],
            "长寿村": ["东海湾", "长寿郊外"],
            "花果山": ["傲来国"],
            "北俱芦洲": ["傲来国", "地府"],
            "地府": ["北俱芦洲", "大唐境外"],
            # ... 更多地图连接
        }
    
    def plan_route(self, 
                   target_map: str, 
                   target_x: int, 
                   target_y: int,
                   current_map: str = None,
                   current_x: int = None,
                   current_y: int = None) -> Route:
        """
        规划从当前位置到目标位置的路线
        
        Args:
            target_map: 目标地图
            target_x: 目标 X 坐标
            target_y: 目标 Y 坐标
            current_map: 当前地图（可选，自动检测）
            current_x: 当前 X 坐标（可选，自动检测）
            current_y: 当前 Y 坐标（可选，自动检测）
        
        Returns:
            Route: 规划好的路线
        """
        print(f"[路线规划] 规划路线：当前 → {target_map}[{target_x},{target_y}]")
        
        # 1. 获取可用导标旗
        available_flags = [name for name, flag in self.flag_manager.flags.items() 
                          if flag.enabled]
        print(f"[路线规划] 可用导标旗：{available_flags}")
        
        # 2. 查找目标地图附近的导标旗
        target_flags = self.flag_manager.get_flags_by_map(target_map)
        
        segments = []
        
        # 3. 如果有目标地图的导标旗，优先使用
        if target_flags:
            # 选择距离目标坐标最近的导标旗
            best_flag = min(target_flags, 
                           key=lambda f: abs(f.x - target_x) + abs(f.y - target_y))
            
            # 第一段：使用导标旗传送到目标地图
            segments.append(RouteSegment(
                from_point="当前位置",
                to_point=best_flag.name,
                method=NavigationMethod.FLAG,
                target=best_flag.name,
                estimated_time=3  # 导标旗传送约 3 秒
            ))
            
            # 第二段：从导标旗位置步行到目标坐标
            walk_time = self._estimate_walk_time(best_flag.x, best_flag.y, target_x, target_y)
            segments.append(RouteSegment(
                from_point=best_flag.name,
                to_point=f"{target_map}[{target_x},{target_y}]",
                method=NavigationMethod.WALK,
                target=f"{target_x},{target_y}",
                estimated_time=walk_time
            ))
        else:
            # 4. 如果没有目标地图的导标旗，使用坐标寻路
            segments.append(RouteSegment(
                from_point="当前位置",
                to_point=f"{target_map}[{target_x},{target_y}]",
                method=NavigationMethod.COORDINATE,
                target=f"{target_x},{target_y}",
                estimated_time=10  # 坐标寻路约 10 秒
            ))
        
        # 5. 构建路线
        total_time = sum(seg.estimated_time for seg in segments)
        description = " → ".join([f"{seg.to_point}({seg.method.value})" for seg in segments])
        
        route = Route(
            segments=segments,
            total_time=total_time,
            description=description
        )
        
        print(f"[路线规划] 规划完成：{description} (预计{total_time}秒)")
        return route
    
    def _estimate_walk_time(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """
        估算步行时间（简化版，实际需要考虑障碍物）
        
        Returns:
            预计时间（秒）
        """
        distance = abs(x1 - x2) + abs(y1 - y2)
        # 假设每秒走 10 个单位
        return max(1, distance // 10)
    
    def find_nearest_flag(self, map_name: str, x: int, y: int) -> Optional[FlagInfo]:
        """
        查找指定地图距离给定坐标最近的导标旗
        
        Args:
            map_name: 地图名称
            x: X 坐标
            y: Y 坐标
            
        Returns:
            最近的导标旗信息
        """
        flags = self.flag_manager.get_flags_by_map(map_name)
        if not flags:
            return None
        
        return min(flags, key=lambda f: abs(f.x - x) + abs(f.y - y))


class NavigationExecutor:
    """
    导航执行模块
    负责执行规划好的路线
    """
    
    def __init__(self, window_manager, flag_manager: FlagManager):
        """
        初始化导航执行器
        
        Args:
            window_manager: 窗口管理器实例
            flag_manager: 导标旗管理器实例
        """
        self.window_manager = window_manager
        self.flag_manager = flag_manager
    
    def execute_route(self, route: Route):
        """
        执行路线
        
        Args:
            route: 规划好的路线
        """
        print(f"[导航] 开始执行路线：{route.description}")
        
        for i, segment in enumerate(route.segments, 1):
            print(f"[导航] 执行第 {i}/{len(route.segments)} 段：{segment.to_point}")
            
            if segment.method == NavigationMethod.FLAG:
                self._execute_flag_teleport(segment.target)
            elif segment.method == NavigationMethod.COORDINATE:
                self._execute_coordinate_navigation(segment.target)
            elif segment.method == NavigationMethod.WALK:
                self._execute_walking(segment.target)
            
            # 等待移动完成
            time.sleep(segment.estimated_time)
        
        print("[导航] 路线执行完成")
    
    def _execute_flag_teleport(self, flag_name: str):
        """
        执行导标旗传送
        
        Args:
            flag_name: 导标旗名称
        """
        print(f"[导航] 使用导标旗：{flag_name}")
        
        # 1. 按 ALT+T 打开导标旗界面
        self.window_manager.press_hotkey('alt', 't')
        time.sleep(0.5)
        
        # 2. 查找并点击导标旗
        # 这里需要实现 UI 查找逻辑，简化示例：
        self._click_flag_by_name(flag_name)
        
        # 3. 等待传送完成
        time.sleep(2)
        
        # 4. 关闭界面
        self.window_manager.press_key('esc')
    
    def _click_flag_by_name(self, flag_name: str):
        """
        根据名称点击导标旗（需要图像识别或 OCR）
        简化实现，实际需要完善
        """
        # TODO: 实现导标旗列表的图像识别和点击
        print(f"[导航] 点击导标旗：{flag_name} (待实现)")
    
    def _execute_coordinate_navigation(self, coordinates: str):
        """
        执行坐标寻路（ALT+G）
        
        Args:
            coordinates: 坐标字符串 "x,y"
        """
        print(f"[导航] 坐标寻路：{coordinates}")
        
        # 1. 按 ALT+G 打开坐标输入框
        self.window_manager.press_hotkey('alt', 'g')
        time.sleep(0.5)
        
        # 2. 输入坐标
        self.window_manager.type_text(coordinates)
        
        # 3. 按回车确认
        self.window_manager.press_key('enter')
        
        # 4. 等待寻路完成
        time.sleep(1)
    
    def _execute_walking(self, target: str):
        """
        执行步行导航
        
        Args:
            target: 目标坐标
        """
        print(f"[导航] 步行至：{target}")
        # 简化实现，实际需要点击地面移动
        # 可以使用 ALT+G 短距离寻路


class NavigationSystem:
    """
    导航系统总控制器
    整合导标旗管理、路线规划和导航执行
    """
    
    def __init__(self, window_manager, ocr_service):
        """
        初始化导航系统
        
        Args:
            window_manager: 窗口管理器实例
            ocr_service: OCR 服务实例
        """
        self.window_manager = window_manager
        self.ocr_service = ocr_service
        
        # 初始化各模块
        self.flag_manager = FlagManager(window_manager, ocr_service)
        self.route_planner = RoutePlanner(self.flag_manager)
        self.executor = NavigationExecutor(window_manager, self.flag_manager)
    
    def navigate_to_task_target(self, task_info) -> bool:
        """
        导航到任务目标位置
        
        Args:
            task_info: 任务信息（包含目标位置）
            
        Returns:
            是否成功到达
        """
        try:
            # 1. 解析任务目标
            target_map = task_info.get('map')
            target_x = task_info.get('x')
            target_y = task_info.get('y')
            
            if not all([target_map, target_x, target_y]):
                print("[导航] 任务目标信息不完整")
                return False
            
            # 2. 规划路线
            route = self.route_planner.plan_route(
                target_map=target_map,
                target_x=target_x,
                target_y=target_y
            )
            
            # 3. 执行路线
            self.executor.execute_route(route)
            
            return True
            
        except Exception as e:
            print(f"[导航] 导航失败：{e}")
            return False
    
    def add_custom_flag(self, name: str, map_name: str, x: int, y: int):
        """添加自定义导标旗配置"""
        self.flag_manager.add_flag(name, map_name, x, y)


# 使用示例
if __name__ == "__main__":
    # 伪代码示例
    # window_manager = WindowManager()
    # ocr_service = OCRService()
    
    # nav_system = NavigationSystem(window_manager, ocr_service)
    
    # 示例：导航到长安城商会
    # task_info = {
    #     'map': '长安城',
    #     'x': 520,
    #     'y': 180
    # }
    # nav_system.navigate_to_task_target(task_info)
    pass
