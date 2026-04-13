import cv2
import numpy as np
import re
import logging
from paddleocr import PaddleOCR

# 屏蔽PaddleOCR的DEBUG日志
logging.getLogger("ppocr").setLevel(logging.INFO)


class OCRExtractor:
    """图片文字识别与关键信息提取工具"""

    def __init__(self):
        """初始化OCR模型（仅加载一次，提升性能）"""
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)

    def preprocess_image(self, img_path):
        """图片二值化预处理"""
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"无法读取图片：{img_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def ocr_and_sort(self, binary_img):
        """OCR识别并按坐标排序文本"""
        result = self.ocr.ocr(binary_img, cls=True)
        if not result or result[0] is None:
            return []

        ocr_results = []
        for line in result[0]:
            text = line[1][0].replace("，", "").replace("。", "").replace("》", "").replace("的", "的 ")
            y1 = int(line[0][1][1])
            ocr_results.append({"text": text, "y": y1})

        ocr_results.sort(key=lambda x: x["y"])
        return [res["text"] for res in ocr_results]

    def extract_key_info(self, ocr_texts):
        """提取关键信息（目标、物品、次数）"""
        if not ocr_texts:
            return {}

        full_text = "".join(ocr_texts)

        key_patterns = {
            "目标": re.compile(r"抓到(.+?)法力"),
            "物品": re.compile(r"值的(.+?)当前"),
            "次数": re.compile(r"第(\d+)次")
        }

        key_info = {}
        for name, pattern in key_patterns.items():
            match = pattern.search(full_text)
            if match:
                key_info[name] = match.group(1).strip()

        return key_info

    def process_image(self, img_path):
        """处理图片并返回识别结果"""
        try:
            # 1. 预处理
            binary_img = self.preprocess_image(img_path)
            # 2. OCR识别
            ocr_texts = self.ocr_and_sort(binary_img)
            # 3. 提取关键信息
            key_info = self.extract_key_info(ocr_texts)

            if key_info:
                return {
                    "success": True,
                    "full_text": "".join(ocr_texts),
                    "key_info": key_info
                }
            else:
                return {
                    "success": False,
                    "message": "未识别到有效文本"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"处理出错：{str(e)}"
            }


# 示例用法（直接运行时测试）
if __name__ == "__main__":
    extractor = OCRExtractor()
    img_path = "renwu_images/task_images.png"  # 替换为实际图片路径

    result = extractor.process_image(img_path)
    if result["success"]:
        print("合并后的完整文本：", result["full_text"])
        print("\n提取的重点信息：")
        for k, v in result["key_info"].items():
            print(f"{k}：{v}")
    else:
        print("错误：", result["message"])