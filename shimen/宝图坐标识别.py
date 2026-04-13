import cv2
import numpy as np
import re
import logging
from paddleocr import PaddleOCR
import os

# 屏蔽PaddleOCR的DEBUG日志
logging.getLogger("ppocr").setLevel(logging.INFO)


# --------------------------
# 字典加载与文本纠正功能
# --------------------------
def load_dictionary(file_path):
    """加载字典文件，每行一个地点，返回地点列表"""
    locations = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    location = line.strip()
                    if location:
                        locations.append(location)
        except Exception as e:
            print(f"加载字典文件 {file_path} 出错: {str(e)}")
    else:
        print(f"字典文件 {file_path} 不存在，使用默认地点列表")
        # 默认宝图地点列表
        locations = ["傲来国", "五庄观", "北俱芦洲", "建邺城", "江南野外", "东海湾", "大唐境外", "方寸山", "狮驼岭"]
    return locations


def get_similar_location(text, location_dict, min_similarity=0.6):
    """从地点字典中找到与输入文本最相似的地点"""
    max_similarity = 0
    best_match = "未识别"
    for location in location_dict:
        # 计算字符串相似度（0-1，1为完全相同）
        similarity = calculate_similarity(text, location)
        if similarity > max_similarity and similarity >= min_similarity:
            max_similarity = similarity
            best_match = location
    return best_match


def calculate_similarity(str1, str2):
    """计算两个字符串的相似度"""
    m = len(str1)
    n = len(str2)
    # 创建二维数组
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    # 初始化边界
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    # 填充dp数组
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + 1)
    # 计算相似度
    edit_distance = dp[m][n]
    similarity = 1 - edit_distance / max(m, n)
    return similarity


# --------------------------
# 图像处理功能
# --------------------------
def binarize_image(img_path):
    """图片二值化预处理"""
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 增强对比度
    gray = cv2.equalizeHist(gray)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


# 初始化OCR
ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)


def ocr_and_filter(binary_img):
    """OCR识别并筛选出包含坐标相关的文本行"""
    result = ocr.ocr(binary_img, cls=True)
    if not result or result[0] is None:
        return []

    filtered_results = []
    for line in result[0]:
        # 初步清洗文本（保留可能的坐标分隔符）
        text = line[1][0]
        text = re.sub(r"[）〕】』”’（〔【『「』）\]\{\}]", "", text)  # 移除干扰符号，保留逗号和点号
        text = text.strip()

        if text:
            # 只保留包含数字或"坐标"等关键词的行
            if re.search(r"\d", text) or re.search(r"坐标|位置", text):
                y1 = int(line[0][0][1])
                filtered_results.append({"text": text, "y": y1})

    # 按y坐标排序（从上到下）
    filtered_results.sort(key=lambda x: x["y"])
    return [res["text"] for res in filtered_results]


# --------------------------
# 信息提取功能
# --------------------------
def extract_key_info(ocr_texts, location_dict):
    """结合地点字典提取地点和坐标信息"""
    if not ocr_texts:
        return {"地点": "未识别", "坐标": "未识别"}

    full_text = "".join(ocr_texts)
    key_info = {"地点": "未识别", "坐标": "未识别"}

    # 1. 从OCR文本中提取可能的地点关键词
    place_candidates = []
    for text in ocr_texts:
        # 查找可能包含地点的文本行（包含"国"、"观"、"洲"等地点特征字）
        if re.search(r"[国观洲城野外湾境外]", text):
            place_candidates.append(text)

    # 2. 使用地点字典匹配最相似的地点
    best_place = "未识别"
    max_similarity = 0
    for candidate in place_candidates:
        for location in location_dict:
            if location in candidate:
                similarity = calculate_similarity(candidate, location)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_place = location
            # 检查是否部分匹配
            elif any(part in candidate for part in location):
                similarity = calculate_similarity(candidate, location)
                if similarity > max_similarity and similarity >= 0.5:
                    max_similarity = similarity
                    best_place = location

    key_info["地点"] = best_place if max_similarity >= 0.5 else "未识别"

    # 3. 提取坐标（支持数字+分隔符格式）
    coord_patterns = [
        r"(\d{1,4})[,.](\d{1,3})",  # 123,45 或 123.45
        r"坐标[:：]?(\d{1,4})[,.](\d{1,3})",  # 坐标:123,45
        r"位置[:：]?(\d{1,4})[,.](\d{1,3})",  # 位置:123.45
        r"(\d{3,4})(\d{2,3})"  # 无分隔符的坐标（如13721）
    ]
    for pattern in coord_patterns:
        match = re.search(pattern, full_text)
        if match:
            groups = match.groups()
            # 处理不同分组情况
            if len(groups) >= 2:
                x = groups[0].strip()
                y = groups[1].strip()
                # 验证坐标格式合理性
                if x.isdigit() and y.isdigit() and 3 <= len(x) <= 4 and 2 <= len(y) <= 3:
                    key_info["坐标"] = f"{x}.{y}"
            elif len(groups) == 1 and len(groups[0]) >= 5:
                # 处理无分隔符的长数字（如13721拆分为137和21）
                x = groups[0][:3]
                y = groups[0][3:5]
                if x.isdigit() and y.isdigit():
                    key_info["坐标"] = f"{x}.{y}"
            break

    return key_info


# --------------------------
# 主流程
# --------------------------
if __name__ == "__main__":
    # 1. 加载宝图地点字典
    location_dict = load_dictionary("dict/宝图地点.txt")
    print(f"已加载 {len(location_dict)} 个宝图地点\n")

    # 2. 处理图片
    img_path = "baotuzuobiao/baotuzuobiao.png"  # 替换为你的图片路径
    try:
        # 预处理
        binary_img = binarize_image(img_path)

        # OCR识别并筛选
        ocr_texts = ocr_and_filter(binary_img)
        print("识别到的坐标相关文本行：")
        for i, text in enumerate(ocr_texts):
            print(f"  {i + 1}: {text}")

        # 提取信息
        if ocr_texts:
            key_info = extract_key_info(ocr_texts, location_dict)
            print("\n提取的重点信息：")
            for k, v in key_info.items():
                print(f"{k}：{v}")
        else:
            print("\n未识别到坐标相关文本")

    except Exception as e:
        print(f"处理出错：{str(e)}")