# -*- coding: utf-8 -*-
"""
游戏界面中文 OCR 识别脚本（优化版）
适用于类似“帮师傅抓到法力高深...”这种复杂排版文字
"""

import cv2
import numpy as np
from paddleocr import PaddleOCR
import os

def preprocess_image(image_path):
    """
    图像预处理：灰度化 + 自适应阈值二值化 + 锐化
    目的是提高字符清晰度和边缘对比度
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"无法读取图像文件: {image_path}")

    # 转为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 使用自适应阈值进行二值化（适合不均匀光照）
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # 可选：锐化图像以增强边缘
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(binary, -1, kernel)

    return sharpened


def post_process_text(results):
    """
    后处理：合并文本、修正常见错误
    """
    # 按照 y 轴坐标排序，然后是 x 轴坐标，以获得正确的阅读顺序
    results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))  # 假设每个文本块的第一个点为左上角

    lines = []
    for res in results:
        text, confidence = res[1]  # 提取文本及其置信度
        if isinstance(text, str) and confidence > 0.5:  # 过滤掉低置信度的文本
            lines.append(text)

    # 尝试修复常见错误
    corrections = {
        '帮师傅抑到': '帮师傅抓到',
        '口能': '',
        '当前第2次。': '当前第2次。',
    }

    corrected_text = ' '.join(lines)  # 简单地用空格连接所有文本
    for wrong, correct in corrections.items():
        corrected_text = corrected_text.replace(wrong, correct)

    return corrected_text.strip()


def main(image_path):
    """
    主函数：执行 OCR 流程
    """
    print(f"[INFO] 正在处理图像: {image_path}")

    try:
        # 预处理图像
        processed_img = preprocess_image(image_path)
        print("[INFO] 图像预处理完成")

        # 初始化 PaddleOCR（参数优化）
        ocr = PaddleOCR(
            use_gpu=False,
            det_algorithm='DB',  # 检测算法
            det_db_thresh=0.3,     # 检测置信度阈值
            det_db_box_thresh=0.6, # 检测框阈值
            det_db_unclip_ratio=1.8,  # 扩大检测框范围，避免截断
            rec_algorithm='SVTR_LCNet',  # 识别模型
            drop_score=0.3,          # 降低丢弃分数，保留更多候选
            max_text_length=50,      # 最大文本长度
            use_angle_cls=True,      # 是否使用方向分类
            cls_thresh=0.8,          # 分类置信度阈值
            rec_char_dict_path='D:\\Program Files\\python3.9\\lib\\site-packages\\paddleocr\\ppocr\\utils\\ppocr_keys_v1.txt',
            lang='ch',               # 中文
            show_log=True,
            image_dir=None           # 不指定目录，直接传图片
        )

        # 执行 OCR
        result = ocr.ocr(processed_img, cls=True)
        print(f"[INFO] OCR 识别完成，共检测到 {len(result)} 行")

        # 调试：打印原始结果
        print("\n[DEBUG] 原始 OCR 结果:")
        print("-" * 50)
        for i, res in enumerate(result):
            print(f"检测区域 {i+1}:")
            if isinstance(res, (list, tuple)) and len(res) > 0:
                for item in res:
                    print(item)
            else:
                print(res)
        print("-" * 50)

        # 提取结果
        text = post_process_text(result)
        print("\n" + "="*50)
        print("✅ 识别结果（已后处理）:")
        print("="*50)
        print(text)
        print("="*50)

        # 保存结果到文件
        output_file = "ocr_result.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\n[INFO] 结果已保存至: {output_file}")

    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")


if __name__ == "__main__":
    # 修改为你的图片路径
    image_path = "shimen/yellow_screenshot.png"  # 👈 替换为你的图片路径，比如 D:/test.png

    if not os.path.exists(image_path):
        print(f"[ERROR] 图片不存在: {image_path}")
        exit(1)

    main(image_path)