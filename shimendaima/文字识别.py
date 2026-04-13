import cv2
import numpy as np
import re
import logging
from paddleocr import PaddleOCR
from difflib import SequenceMatcher  # 用于计算字符串相似度

# 屏蔽PaddleOCR的DEBUG日志
logging.getLogger("ppocr").setLevel(logging.INFO)


# --------------------------
# 新增：字典加载与模糊匹配功能
# --------------------------
def load_dictionary(file_path):
    """加载字典文件（格式：编号-名称），返回名称列表"""
    words = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "-" in line:
                    _, name = line.split("-", 1)  # 分割编号和名称
                    words.append(name.strip())
    except FileNotFoundError:
        print(f"警告：未找到字典文件 {file_path}，已跳过该文件")
    return words


def get_similar_word(text, candidate_words, min_similarity=0.6):
    """从候选词库中找到与输入文本最相似的词（相似度≥阈值）"""
    max_similarity = 0
    best_match = None
    for word in candidate_words:
        # 计算字符串相似度（0-1，1为完全相同）
        similarity = SequenceMatcher(None, text, word).ratio()
        if similarity > max_similarity and similarity >= min_similarity:
            max_similarity = similarity
            best_match = word
    return best_match if best_match else text


def correct_text_with_dictionaries(text, candidate_words, min_similarity=0.7):
    """用候选词库纠正文本（修复copy错误，改为直接赋值）"""
    corrected = text  # 直接赋值，无需copy
    # 按候选词长度从长到短排序（优先匹配长词，避免短词干扰）
    candidate_words = sorted(candidate_words, key=lambda x: -len(x))

    for word in candidate_words:
        # 只替换与word相似度≥阈值的连续片段
        start = 0
        while True:
            # 查找word在corrected中的位置（从start开始）
            pos = corrected.find(word, start)
            if pos == -1:
                break

            # 提取word前后各1个字符，判断是否为独立词汇
            prev_char = corrected[pos - 1] if pos > 0 else " "
            next_char = corrected[pos + len(word)] if (pos + len(word) < len(corrected)) else " "
            if prev_char.isalnum() or next_char.isalnum():
                start = pos + 1
                continue  # 前后是字母/数字，跳过

            # 计算原始文本中对应位置的片段与word的相似度
            original_fragment = text[pos:pos + len(word)]
            similarity = SequenceMatcher(None, original_fragment, word).ratio()
            if similarity >= min_similarity:
                # 替换并跳过已处理位置
                corrected = corrected[:pos] + word + corrected[pos + len(word):]
            start = pos + 1
    return corrected


# --------------------------
# 原有功能：图像处理与OCR识别（核心修改：二值化前先放大）
# --------------------------
def binarize_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}")

    # 核心修改：二值化前先放大图片（放大2.5倍，用INTER_LANCZOS4插值保留文字细节）
    # fx/fy：放大倍数，可根据需求调整（如3.0表示放大3倍）
    img_enlarged = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)

    # 后续步骤不变：先转灰度图，再二值化
    gray = cv2.cvtColor(img_enlarged, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 返回放大后的二值化图和原始图（便于后续显示和识别）
    return binary, img_enlarged  # 注意：此处返回放大后的原图，而非原始尺寸原图


ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)


def ocr_and_sort(binary_img):
    result = ocr.ocr(binary_img, cls=True)
    if not result or result[0] is None:
        return []

    ocr_results = []
    for line in result[0]:
        # 初步清洗文本（去除标点）
        text = line[1][0].replace("，", "").replace("。", "").replace("》", "").replace("的", "的 ")
        y1 = int(line[0][1][1])  # 取文本框上方y坐标用于排序
        ocr_results.append({"text": text, "y": y1})

    # 按y坐标排序（从上到下）
    ocr_results.sort(key=lambda x: x["y"])
    return [res["text"] for res in ocr_results]


# --------------------------
# 优化：加入字典纠正的信息提取
# --------------------------
def extract_key_info(ocr_texts, candidate_words, medicine_words, beast_words, equip_words, npc_words):
    # 1. 文本纠正（包含NPC词库的候选词）
    full_text = "".join(ocr_texts)
    corrected_text = correct_text_with_dictionaries(
        full_text,
        candidate_words,
        min_similarity=0.65  # 适当降低阈值，让“师交”更容易匹配“师傅”
    )
    print(f"原始识别文本：{full_text}")
    print(f"纠正后文本：{corrected_text}\n")

    # 2. 按长度排序各词库（优先匹配长词）
    item_words = sorted(medicine_words + equip_words, key=lambda x: -len(x))  # 物品（三药+装备）
    npc_sorted = sorted(npc_words, key=lambda x: -len(x))  # NPC词（如“师傅”“门派师傅”）
    beast_sorted = sorted(beast_words, key=lambda x: -len(x))  # 召唤兽

    # 3. 定义动作映射（目标提取优先用NPC词库）
    action_mapping = {
        "买": ("物品", re.compile(rf"买(.*?)({('|'.join(item_words))}|送给|上交)")),
        "抓": ("召唤兽", re.compile(rf"抓(.*?)({('|'.join(beast_sorted))}|到|给)")),
        "上交": ("物品", re.compile(rf"上交(.*?)({('|'.join(item_words))}|给|可)")),
        "送给": ("目标", re.compile(rf"送给(.*?)({('|'.join(npc_sorted))}|[的给交])"))  # 优先匹配NPC词
    }

    key_info = {}
    for action, (target_type, pattern) in action_mapping.items():
        if action in corrected_text:
            match = pattern.search(corrected_text)
            if match:
                fragment = match.group(1).strip()
                # 4. 根据类型匹配专属词库
                if target_type == "物品":
                    matched = get_similar_word(fragment, item_words, min_similarity=0.65)
                elif target_type == "召唤兽":
                    matched = get_similar_word(fragment, beast_sorted, min_similarity=0.65)
                elif target_type == "目标":  # 目标优先匹配NPC词库
                    matched = get_similar_word(fragment, npc_sorted, min_similarity=0.65)
                key_info[target_type] = matched

    # 提取次数
    times_match = re.search(r"第(\d+)次", corrected_text)
    if times_match:
        key_info["次数"] = times_match.group(1)

    return key_info


# --------------------------
# 主流程：整合所有功能（修复返回值接收问题）
# --------------------------
if __name__ == "__main__":
    # 1. 加载字典（代码不变）
    medicine_words = load_dictionary("dict/三药.txt")
    beast_words = load_dictionary("dict/召唤兽.txt")
    equip_words = load_dictionary("dict/装备.txt")
    npc_words = load_dictionary("dict/NPC.txt")
    candidate_words = list(set(medicine_words + beast_words + equip_words + npc_words))
    print(
        f"已加载：三药{len(medicine_words)}个，召唤兽{len(beast_words)}个，装备{len(equip_words)}个，NPC{len(npc_words)}个\n")

    # 2. 处理图片（修复核心错误）
    img_path = "shimen/img.png"
    try:
        # 正确接收两个返回值：二值化图 + 放大后的原图
        binary_img, enlarged_img = binarize_image(img_path)  # 重点修复：用两个变量接收

        # 可选：显示放大后的二值化图，确认效果
        # cv2.imshow("Enlarged Binarized Image", binary_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # 转换为PaddleOCR支持的格式（三通道BGR）
        binary_img_rgb = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
        ocr_texts = ocr_and_sort(binary_img_rgb)

        if ocr_texts:
            key_info = extract_key_info(
                ocr_texts,
                candidate_words,
                medicine_words,
                beast_words,
                equip_words,
                npc_words
            )
            print("提取的重点信息：")
            for k, v in key_info.items():
                print(f"{k}：{v}")
        else:
            print("未识别到文本")
    except Exception as e:
        print(f"处理出错：{str(e)}")  # 现在会显示具体错误信息