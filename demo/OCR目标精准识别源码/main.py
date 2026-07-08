import easyocr
# 加载OCR模型 @大兵聊编程
reader = easyocr.Reader(['ch_sim','en'])

# 加载目标图片进行检测 @大兵聊编程
result = reader.readtext('2.png',detail=True,allowlist='武器店老板掌柜',text_threshold=0.9)

# 打印检测结果 @大兵聊编程
print(result)

for posxy, text, confidence in result:
    if '武器店掌柜' == text:
        # 左上角坐标是 bbox[0]
        top_left = posxy[0]
        # 转换为普通的 Python int（可选）
        print('坐标已找到:',int(top_left[0]), int(top_left[1]))