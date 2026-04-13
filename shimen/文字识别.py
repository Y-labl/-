import cv2
import numpy as np
import re
import logging
from paddleocr import PaddleOCR

# 屏蔽PaddleOCR的DEBUG日志
logging.getLogger("ppocr").setLevel(logging.INFO)


class OCRExtractor:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)

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
        result = self.ocr.ocr(binary_img, cls=True)
        if not result or result[0] is None:
            return []

        ocr_results = []
        for line in result[0]:
            text = line[1][0]
            text = re.sub(r"[，。》】』”’（\(\)〔〕【《〈〉《」『\[\]\{\}]", "", text)
            text = text.strip()
            if text:
                y1 = int(line[0][1][1])
                ocr_results.append({"text": text, "y": y1})

        ocr_results.sort(key=lambda x: x["y"])
        return [res["text"] for res in ocr_results]

    def extract_key_info(self, ocr_texts):
        """提取关键信息（目标、物品、次数）"""
        # ... （你的现有逻辑保持不变）

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
            return {
                "success": False,
                "message": f"处理出错：{str(e)}"
            }


# 示例用法
if __name__ == "__main__":
    extractor = OCRExtractor()
    img_path = "renwu_images/task_images.png"

    import os
    if not os.path.exists(img_path):
        print(f"错误：图片文件不存在 -> {img_path}")
        exit(1)

    # 使用增强预处理
    result = extractor.process_image(img_path, use_enhanced_preprocess=True)

    print(f"Result type: {type(result)}, content: {result}")

    if isinstance(result, dict):
        if result.get("success"):
            print("识别的所有行文本：")
            for i, line in enumerate(result["lines"]):
                print(f"  {i+1}: {line}")

            print("\n提取的重点信息：")
            info = result["key_info"]
            print(f"目标：{info.get('目标', '未识别')}")
            print(f"物品：{info.get('物品', '未识别')}")
            print(f"次数：{info.get('次数', '未识别')}")
        else:
            print("错误：", result.get("message", "未知错误"))
    else:
        print("严重错误：process_image 返回了非字典类型，请检查代码逻辑！")
        print(f"返回值类型: {type(result)}, 值: {result}")