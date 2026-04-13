from aip import AipOcr
import cv2
import numpy as np
import re

# 百度API配置
APP_ID = '43418693'
API_KEY = 'Zcho51QEUATXvb0GXKexv8a4'
SECRET_KEY = '8RV5bbFwlTF2MFHyLXGctgT9e9LWM0hI'
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def preprocess_image(file_path):
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError(f"图片读取失败！请检查路径：{file_path}")

    # 1. 先放大图片
    img_enlarged = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)

    # 2. 转换为HSV颜色空间
    hsv = cv2.cvtColor(img_enlarged, cv2.COLOR_BGR2HSV)

    # 3. 定义绿色的HSV范围（需根据实际图片调整，这里是大致范围）
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([77, 255, 255])

    # 4. 根据HSV范围创建掩码
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # 5. 对掩码进行形态学操作，去除噪声
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 6. 将掩码应用到原图，提取绿色文字区域
    green_text = cv2.bitwise_and(img_enlarged, img_enlarged, mask=mask)

    # 7. 转为灰度图
    gray = cv2.cvtColor(green_text, cv2.COLOR_BGR2GRAY)

    # 8. 二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 9. 查看并保存预处理图
    cv2.imshow("Preprocessed (Green Text)", binary)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()
    cv2.imwrite("preprocessed_green_text.png", binary)
    print("提取绿色文字后的预处理图已保存")

    # 转为字节流
    _, img_encoded = cv2.imencode('.png', binary)
    return img_encoded.tobytes()


def fix_coordinate_comma(text):
    """修复坐标中缺失的逗号，兼容多种格式"""
    coord_pattern = re.compile(r'\((\d+)\)')
    match = coord_pattern.search(text)
    if not match:
        return text

    numbers = match.group(1)
    total_len = len(numbers)
    fixed = numbers

    def is_valid(part):
        return len(part) == 0 or (part.isdigit() and int(part) <= 999)

    if total_len == 4:
        part1, part2 = numbers[:1], numbers[1:]
        if is_valid(part1) and is_valid(part2):
            fixed = f"{part1},{part2}"
        else:
            part1, part2 = numbers[:2], numbers[2:]
            if is_valid(part1) and is_valid(part2):
                fixed = f"{part1},{part2}"
    elif total_len == 5:
        part1, part2 = numbers[:2], numbers[2:]
        if is_valid(part1) and is_valid(part2):
            fixed = f"{part1},{part2}"
        else:
            part1, part2 = numbers[:3], numbers[3:]
            if is_valid(part1) and is_valid(part2):
                fixed = f"{part1},{part2}"
    elif total_len == 6:
        part1, part2 = numbers[:3], numbers[3:]
        if is_valid(part1) and is_valid(part2):
            fixed = f"{part1},{part2}"

    return coord_pattern.sub(f'({fixed})', text)


def extract_coordinates(result):
    """提取坐标，先匹配带逗号的，失败则补全逗号后再提取"""
    if 'words_result' not in result or len(result['words_result']) == 0:
        return "未识别到有效文字"

    full_text = ''.join([info['words'] for info in result['words_result']])
    print("完整识别文字：", full_text)

    # 尝试直接匹配带逗号的坐标
    coord_match = re.search(r'\((\d+),(\d+)\)', full_text)
    if coord_match:
        x = coord_match.group(1)
        y = coord_match.group(2)
        return f"X坐标：{x}，Y坐标：{y}"
    else:
        # 补全逗号后再次匹配
        fixed_text = fix_coordinate_comma(full_text)
        print("补全逗号后：", fixed_text)
        coord_match_fixed = re.search(r'\((\d+),(\d+)\)', fixed_text)
        if coord_match_fixed:
            x = coord_match_fixed.group(1)
            y = coord_match_fixed.group(2)
            return f"X坐标：{x}，Y坐标：{y}"
        else:
            return "未匹配到坐标格式（补全后仍失败）"


if __name__ == "__main__":
    image_path = "D:/Program Files/mhxy/shimendaima/shimen/img_1.png"

    try:
        processed_img = preprocess_image(image_path)
        result = client.basicAccurate(processed_img)

        print("\n百度API返回结果：", result)
        if result.get('words_result_num', 0) > 0:
            print("\n✅ 识别成功！")
            coordinates = extract_coordinates(result)
            print(coordinates)
        else:
            print("\n❌ 未识别到文字")

    except Exception as e:
        print(f"\n程序出错：{str(e)}")