from paddleocr import PaddleOCR

if __name__ == "__main__":
    # 初始化 PaddleOCR 模型
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, det=True, rec=True, cls=True)

    # 进行文字检测、文本方向检测和文字识别
    result = ocr.ocr('../shimen/screenshot.png', cls=True)

    # 打印完整的 result 结构，确保理解其层次
    print("原始识别结果:")
    print(result)

    # 提取识别结果中的文本，并打印
    print("\n识别结果:")

    # 检查 result 是否为多页结构
    if isinstance(result[0], list):
        # 多页结构
        for page_idx, page in enumerate(result, 1):  # 遍历每一页
            print(f"\n第 {page_idx} 页:")
            for line_idx, line in enumerate(page, 1):  # 遍历每行
                text = line[1][0]  # 提取每行的文本内容
                confidence = line[1][1]  # 提取置信度
                print(f"第 {line_idx} 行: {text} (置信度: {confidence:.2f})")
    else:
        # 单页结构
        for line_idx, line in enumerate(result, 1):  # 遍历每行
            text = line[1][0]  # 提取每行的文本内容
            confidence = line[1][1]  # 提取置信度
            print(f"第 {line_idx} 行: {text} (置信度: {confidence:.2f})")