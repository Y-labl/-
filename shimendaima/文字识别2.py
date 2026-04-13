import cv2
import numpy as np
import re
import logging
from paddleocr import PaddleOCR

# 屏蔽PaddleOCR的DEBUG日志
logging.getLogger("ppocr").setLevel(logging.INFO)  # 只保留INFO及以上级别（过滤DEBUG）


# 1. 二值化预处理
def binarize_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


# 2. OCR识别并按坐标排序
ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)


def ocr_and_sort(binary_img):
    result = ocr.ocr(binary_img, cls=True)
    if not result or result[0] is None:
        return []

    ocr_results = []
    for line in result[0]:
        text = line[1][0].replace("，", "").replace("。", "").replace("》", "").replace("的", "的 ")
        y1 = int(line[0][1][1])
        ocr_results.append({"text": text, "y": y1})

    ocr_results.sort(key=lambda x: x["y"])
    return [res["text"] for res in ocr_results]


# 3. 提取重点信息
def extract_key_info(ocr_texts):
    full_text = "".join(ocr_texts)
    print(f"合并后的完整文本：{full_text}\n")

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


# 完整流程
if __name__ == "__main__":
    img_path = "shimen/img.png"
    binary_img = binarize_image(img_path)
    ocr_texts = ocr_and_sort(binary_img)

    if ocr_texts:
        key_info = extract_key_info(ocr_texts)
        print("提取的重点信息：")
        for k, v in key_info.items():
            print(f"{k}：{v}")
    else:
        print("未识别到文本")