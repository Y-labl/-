"""
NPC 识别模块
使用 YOLO 目标检测 + OCR 文字识别
原因：
1. NPC 会移动，位置不固定 → YOLO 适合检测任意位置目标
2. NPC 种类繁多 → YOLO 支持多类别识别
3. 需要抗遮挡、抗干扰 → YOLO 鲁棒性强
4. 头顶名字辅助确认 → OCR 文字识别
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import time


class YOLODetector:
    """
    YOLO 目标检测器
    用于检测游戏画面中的 NPC
    """
    
    def __init__(self, model_path: str = "models/npc_detection.onnx",
                 classes_path: str = "config/npc_classes.txt"):
        """
        初始化 YOLO 检测器
        
        Args:
            model_path: YOLO 模型路径（ONNX 格式）
            classes_path: 类别文件路径
        """
        self.model_path = model_path
        self.classes_path = classes_path
        self.model = None
        self.classes = []
        self.input_size = (640, 640)  # YOLO 输入尺寸
        
        # 加载模型
        self.load_model()
        # 加载类别
        self.load_classes()
    
    def load_model(self):
        """加载 YOLO 模型"""
        try:
            import onnxruntime as ort
            
            # 加载 ONNX 模型
            self.model = ort.InferenceSession(
                self.model_path,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            
            # 获取输入输出信息
            self.input_name = self.model.get_inputs()[0].name
            self.output_name = self.model.get_outputs()[0].name
            
            print(f"[YOLO] 模型加载成功：{self.model_path}")
            
        except Exception as e:
            print(f"[YOLO] 模型加载失败：{e}")
            print("[YOLO] 将使用模拟检测（需训练实际模型）")
            self.model = None
    
    def load_classes(self):
        """加载 NPC 类别列表"""
        import os
        
        if os.path.exists(self.classes_path):
            with open(self.classes_path, 'r', encoding='utf-8') as f:
                self.classes = [line.strip() for line in f.readlines()]
            print(f"[YOLO] 加载 {len(self.classes)} 个 NPC 类别")
        else:
            # 默认 NPC 类别（示例）
            self.classes = [
                "门派师傅", "门派师兄", "门派守卫",
                "杂货店老板", "武器店老板", "防具店老板",
                "药店老板", "客栈老板", "驿站老板",
                "捕快", "衙门守卫", "衙门师爷",
                "商会会长", "镖头", "船夫",
                "土地公公", "太白金星", "观音姐姐",
                "店小二", "小二", "厨师",
                "铁匠", "裁缝", "医生"
            ]
            print(f"[YOLO] 使用默认 {len(self.classes)} 个 NPC 类别")
    
    def detect(self, image: np.ndarray, 
               confidence_threshold: float = 0.5,
               nms_threshold: float = 0.4) -> List[Dict]:
        """
        检测图像中的 NPC
        
        Args:
            image: 游戏截图（BGR 格式）
            confidence_threshold: 置信度阈值
            nms_threshold: NMS 阈值
            
        Returns:
            检测结果列表
        """
        if self.model is None:
            # 模型未加载时，返回模拟结果（用于演示）
            return self._mock_detect(image)
        
        # 1. 图像预处理
        input_image = self._preprocess(image)
        
        # 2. 模型推理
        outputs = self.model.run([self.output_name], {self.input_name: input_image})[0]
        
        # 3. 后处理
        detections = self._postprocess(
            outputs, 
            image.shape,
            confidence_threshold,
            nms_threshold
        )
        
        return detections
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 原始图像
            
        Returns:
            预处理后的图像（归一化、缩放）
        """
        # 转换为 RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 缩放至输入尺寸
        resized = cv2.resize(rgb_image, self.input_size)
        
        # 归一化到 0-1
        normalized = resized.astype(np.float32) / 255.0
        
        # 转换为 NCHW 格式（Batch, Channel, Height, Width）
        batched = np.expand_dims(normalized, axis=0)
        batched = np.transpose(batched, (0, 3, 1, 2))
        
        return batched
    
    def _postprocess(self, outputs: np.ndarray,
                    image_shape: Tuple[int, int, int],
                    conf_threshold: float,
                    nms_threshold: float) -> List[Dict]:
        """
        模型输出后处理
        
        Args:
            outputs: 模型输出
            image_shape: 原始图像尺寸
            conf_threshold: 置信度阈值
            nms_threshold: NMS 阈值
            
        Returns:
            检测结果
        """
        detections = []
        
        # 解析输出（YOLO 输出格式：[x, y, w, h, conf, class_scores...]）
        for output in outputs[0]:
            # 获取置信度和类别
            scores = output[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            # 过滤低置信度检测
            if confidence < conf_threshold:
                continue
            
            # 获取边界框
            x, y, w, h = output[0:4]
            
            # 缩放到原始图像尺寸
            scale_x = image_shape[1] / self.input_size[0]
            scale_y = image_shape[0] / self.input_size[1]
            
            x1 = int((x - w/2) * scale_x)
            y1 = int((y - h/2) * scale_y)
            x2 = int((x + w/2) * scale_x)
            y2 = int((y + h/2) * scale_y)
            
            detections.append({
                'class_id': int(class_id),
                'class_name': self.classes[int(class_id)],
                'confidence': float(confidence),
                'bbox': [x1, y1, x2 - x1, y2 - y1],  # [x, y, w, h]
                'center_x': int((x1 + x2) / 2),
                'center_y': int((y1 + y2) / 2)
            })
        
        # 应用 NMS（非极大值抑制）去除重叠框
        if len(detections) > 0:
            detections = self._apply_nms(detections, nms_threshold)
        
        return detections
    
    def _apply_nms(self, detections: List[Dict], 
                   nms_threshold: float) -> List[Dict]:
        """
        非极大值抑制（NMS）
        
        Args:
            detections: 检测结果列表
            nms_threshold: NMS 阈值
            
        Returns:
            NMS 后的检测结果
        """
        boxes = [d['bbox'] for d in detections]
        scores = [d['confidence'] for d in detections]
        
        # OpenCV NMS
        indices = cv2.dnn.NMSBoxes(
            boxes, scores, 
            score_threshold=0.3, 
            nms_threshold=nms_threshold
        )
        
        if len(indices) > 0:
            return [detections[i] for i in indices]
        return []
    
    def _mock_detect(self, image: np.ndarray) -> List[Dict]:
        """
        模拟检测（用于模型训练前的演示）
        实际使用时会被真实检测替换
        """
        # 这里可以集成传统方法作为临时方案
        # 例如：颜色识别 + 轮廓检测
        
        # 示例：检测黄色 NPC（假设门派师傅穿黄衣服）
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 黄色范围
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:  # 过滤小目标
                x, y, w, h = cv2.boundingRect(cnt)
                detections.append({
                    'class_id': 0,
                    'class_name': '门派师傅（模拟）',
                    'confidence': 0.6,
                    'bbox': [x, y, w, h],
                    'center_x': x + w//2,
                    'center_y': y + h//2
                })
        
        return detections[:3]  # 最多返回 3 个


class NPCTextRecognizer:
    """
    NPC 文字识别器
    识别 NPC 头顶的名字，辅助确认身份
    """
    
    def __init__(self, ocr_service):
        """
        初始化文字识别器
        
        Args:
            ocr_service: OCR 服务实例
        """
        self.ocr_service = ocr_service
        # NPC 名字区域通常在检测框上方
        self.name_region_offset = (-20, -60, 20, -20)  # (x_offset, y_top, x_width, y_height)
    
    def recognize_name(self, image: np.ndarray, 
                      detection: Dict) -> Optional[str]:
        """
        识别 NPC 头顶名字
        
        Args:
            image: 游戏截图
            detection: YOLO 检测结果
            
        Returns:
            NPC 名字
        """
        x, y, w, h = detection['bbox']
        
        # 截取名字区域（检测框上方）
        name_x = x + w // 4
        name_y = y + self.name_region_offset[0]
        name_w = w // 2
        name_h = 40
        
        # 确保不越界
        name_y = max(0, name_y)
        name_roi = image[name_y:name_y+name_h, name_x:name_x+name_w]
        
        if name_roi.size == 0:
            return None
        
        # OCR 识别
        try:
            text = self.ocr_service.recognize(name_roi)
            if text:
                # 清理文本
                cleaned = self._clean_name(text)
                return cleaned
        except Exception as e:
            print(f"[NPC-OCR] 识别失败：{e}")
        
        return None
    
    def _clean_name(self, text: str) -> str:
        """
        清理 OCR 识别结果
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的名字
        """
        import re
        
        # 去除特殊字符
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
        
        # 去除常见 NPC 后缀
        suffixes = ['老板', '师傅', '师兄', '守卫', '店小二']
        for suffix in suffixes:
            if text.endswith(suffix):
                return text
        
        return text


class NPCMatcher:
    """
    NPC 匹配器
    根据检测结果和任务需求，匹配目标 NPC
    """
    
    def __init__(self):
        """初始化匹配器"""
        # NPC 别名映射
        self.name_aliases = {
            '师傅': ['门派师傅', '师父', '师尊'],
            '师兄': ['门派师兄', '师哥'],
            '老板': ['杂货店老板', '武器店老板', '药店老板'],
            '守卫': ['门派守卫', '衙门守卫', '捕快'],
        }
    
    def match_target(self, detections: List[Dict], 
                    target_name: str) -> Optional[Dict]:
        """
        从检测结果中匹配目标 NPC
        
        Args:
            detections: YOLO 检测结果
            target_name: 目标 NPC 名称
            
        Returns:
            匹配的检测结果
        """
        if not detections:
            return None
        
        # 1. 精确匹配
        for det in detections:
            if det['class_name'] == target_name:
                print(f"[NPC] 精确匹配：{target_name}")
                return det
        
        # 2. 别名匹配
        for alias_group in self.name_aliases.values():
            if target_name in alias_group:
                for alias in alias_group:
                    for det in detections:
                        if det['class_name'] == alias:
                            print(f"[NPC] 别名匹配：{target_name} → {alias}")
                            return det
        
        # 3. 模糊匹配（包含关键词）
        keywords = target_name.split()
        for det in detections:
            if any(kw in det['class_name'] for kw in keywords):
                print(f"[NPC] 模糊匹配：{det['class_name']}")
                return det
        
        # 4. 返回置信度最高的
        print(f"[NPC] 无匹配，返回置信度最高的")
        return max(detections, key=lambda x: x['confidence'])
    
    def find_nearest_npc(self, detections: List[Dict],
                        screen_center: Tuple[int, int]) -> Optional[Dict]:
        """
        查找距离屏幕中心最近的 NPC
        
        Args:
            detections: 检测结果
            screen_center: 屏幕中心坐标
            
        Returns:
            最近的 NPC
        """
        if not detections:
            return None
        
        nearest = min(
            detections,
            key=lambda d: np.sqrt(
                (d['center_x'] - screen_center[0])**2 + 
                (d['center_y'] - screen_center[1])**2
            )
        )
        
        return nearest


class NPCRecognitionSystem:
    """
    NPC 识别系统（总控制器）
    整合 YOLO 检测、OCR 识别和匹配逻辑
    """
    
    def __init__(self, ocr_service):
        """
        初始化 NPC 识别系统
        
        Args:
            ocr_service: OCR 服务实例
        """
        self.yolo_detector = YOLODetector()
        self.text_recognizer = NPCTextRecognizer(ocr_service)
        self.matcher = NPCMatcher()
    
    def detect_and_recognize(self, image: np.ndarray,
                            target_name: str = None) -> List[Dict]:
        """
        检测并识别 NPC
        
        Args:
            image: 游戏截图
            target_name: 目标 NPC 名称（可选）
            
        Returns:
            识别结果列表
        """
        # 1. YOLO 检测
        detections = self.yolo_detector.detect(image)
        print(f"[NPC] 检测到 {len(detections)} 个 NPC")
        
        # 2. 识别每个 NPC 的名字（辅助确认）
        for det in detections:
            name = self.text_recognizer.recognize_name(image, det)
            if name:
                det['recognized_name'] = name
        
        # 3. 如果指定了目标名称，进行匹配
        if target_name:
            matched = self.matcher.match_target(detections, target_name)
            if matched:
                return [matched]  # 只返回匹配的
            return []
        
        return detections
    
    def find_npc(self, image: np.ndarray, 
                npc_name: str) -> Optional[Dict]:
        """
        查找指定 NPC
        
        Args:
            image: 游戏截图
            npc_name: NPC 名称
            
        Returns:
            NPC 位置信息
        """
        results = self.detect_and_recognize(image, npc_name)
        
        if results:
            npc = results[0]
            print(f"[NPC] 找到目标：{npc_name}")
            print(f"  - 位置：[{npc['center_x']}, {npc['center_y']}]")
            print(f"  - 置信度：{npc['confidence']:.2f}")
            return npc
        
        print(f"[NPC] 未找到：{npc_name}")
        return None
    
    def navigate_to_npc(self, window_manager, npc_name: str,
                       max_attempts: int = 10) -> bool:
        """
        导航到 NPC 位置
        
        Args:
            window_manager: 窗口管理器
            npc_name: NPC 名称
            max_attempts: 最大尝试次数
            
        Returns:
            是否成功
        """
        print(f"[NPC 导航] 开始导航至：{npc_name}")
        
        for attempt in range(max_attempts):
            # 1. 截图
            screenshot = window_manager.capture_screen()
            
            # 2. 检测 NPC
            npc = self.find_npc(screenshot, npc_name)
            
            if npc:
                # 3. 点击 NPC
                window_manager.click(npc['center_x'], npc['center_y'])
                time.sleep(0.5)
                
                # 4. 检测是否打开对话
                if self._is_dialog_open(screenshot):
                    print(f"[NPC 导航] 成功与 {npc_name} 对话")
                    return True
                
                # 5. 如果距离较远，使用 ALT+G 寻路
                if npc['confidence'] < 0.7:
                    print(f"[NPC 导航] 距离较远，使用坐标寻路")
                    self._navigate_by_coordinate(window_manager, npc)
            
            time.sleep(1)
        
        print(f"[NPC 导航] 导航失败：{npc_name}")
        return False
    
    def _is_dialog_open(self, image: np.ndarray) -> bool:
        """检测是否打开了对话窗口"""
        # 简化实现：检测对话窗口特征
        # 实际需要根据游戏 UI 实现
        return False
    
    def _navigate_by_coordinate(self, window_manager, npc: Dict):
        """使用坐标寻路接近 NPC"""
        # 按 ALT+G，输入大致坐标
        pass


# 使用示例
if __name__ == "__main__":
    # 伪代码示例
    # ocr_service = OCRService()
    # npc_system = NPCRecognitionSystem(ocr_service)
    
    # # 查找门派师傅
    # screenshot = window_manager.capture_screen()
    # master = npc_system.find_npc(screenshot, "门派师傅")
    
    # if master:
    #     window_manager.click(master['center_x'], master['center_y'])
    pass
