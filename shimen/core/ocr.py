import cv2
import numpy as np
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OCRExtractor:
    """文字识别类，负责识别任务文本信息"""

    def __init__(self):
        # 延迟导入easyocr以提高启动速度
        self.ocr = None
        pass

    def preprocess_image(self, img_path):
        """普通图片二值化预处理"""
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"无法读取图片：{img_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def enhanced_preprocess_image(self, img_path):
        """针对黄字黑底的图片进行增强预处理"""
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"无法读取图片：{img_path}")

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([25, 100, 100])
        upper_yellow = np.array([40, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        yellow_only = cv2.bitwise_and(img, img, mask=mask)
        gray = cv2.cvtColor(yellow_only, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        return binary

    def ocr_and_sort(self, binary_img):
        """OCR识别并按坐标排序文本"""
        try:
            # 延迟导入easyocr
            if self.ocr is None:
                from easyocr import Reader
                self.ocr = Reader(['ch_sim'], gpu=False)
            
            # 使用easyocr进行OCR
            if isinstance(binary_img, np.ndarray):
                # 对于numpy数组，直接使用
                result = self.ocr.readtext(binary_img)
            else:
                # 对于文件路径，读取图像
                img = cv2.imread(binary_img)
                result = self.ocr.readtext(img)
            
            ocr_results = []
            for detection in result:
                text = detection[1].strip()
                if text:
                    # 过滤掉空字符串和噪声
                    text = re.sub(r"[，。》】』”’（\(\)〔〕【《〈〉《」『\[\]\{\}]", "", text)
                    text = text.strip()
                    if text:
                        # 获取文本区域的顶部坐标
                        y = int(detection[0][0][1])
                        ocr_results.append({"text": text, "y": y})
            
            ocr_results.sort(key=lambda x: x["y"])
            return [res["text"] for res in ocr_results]
        except Exception as e:
            logger.error(f"OCR识别出错：{str(e)}")
            return []

    def extract_key_info(self, ocr_texts):
        """提取关键信息（目标、物品、次数）"""
        key_info = {
            "目标": "未识别",
            "物品": "未识别",
            "次数": "未识别",
            "地点": "未识别",
            "坐标": "未识别"
        }

        # 简单的关键词匹配
        for text in ocr_texts:
            if "寻找" in text or "找到" in text:
                key_info["目标"] = text
            elif "购买" in text or "物品" in text:
                key_info["物品"] = text
            elif "第" in text and "次" in text:
                key_info["次数"] = text
            elif "坐标" in text or "位于" in text:
                key_info["坐标"] = text
            elif "长安" in text or "建业" in text or "傲来" in text or "长寿" in text:
                key_info["地点"] = text

        return key_info

    def process_image(self, img_path, use_enhanced_preprocess=False):
        """处理图片并返回识别结果"""
        try:
            # 根据参数选择预处理方法
            if use_enhanced_preprocess:
                binary_img = self.enhanced_preprocess_image(img_path)
            else:
                binary_img = self.preprocess_image(img_path)

            ocr_texts = self.ocr_and_sort(binary_img)
            key_info = self.extract_key_info(ocr_texts)

            if ocr_texts:
                return {
                    "success": True,
                    "full_text": "".join(ocr_texts),
                    "key_info": key_info,
                    "lines": ocr_texts
                }
            else:
                return {
                    "success": False,
                    "message": "未识别到任何文本"
                }

        except Exception as e:
            logger.error(f"处理图像时出错：{str(e)}")
            return {
                "success": False,
                "message": f"处理出错：{str(e)}"
            }
