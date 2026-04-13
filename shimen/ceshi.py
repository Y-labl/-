import cv2
import numpy as np
import pyautogui
import  time
time.sleep(2)

def find_image_cv2(template_path, confidence=0.8, grayscale=True, show_result=False):
    """
    使用 OpenCV 在屏幕上查找图片

    :param template_path: 模板图片路径 (如 'button.png')
    :param confidence: 匹配阈值 (0~1)，越高要求越精确
    :param grayscale: 是否转为灰度图加快速度
    :param show_result: 是否显示匹配结果（调试用）
    :return: 匹配位置列表，每个元素为 (x, y, w, h)；未找到返回 []
    """
    # 1. 截图
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 2. 读取模板图像
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"无法加载模板图片: {template_path}")

    # 3. 处理透明 PNG（如果有 alpha 通道）
    if template.shape[2] == 4:
        if grayscale:
            # 分离 RGB 和 Alpha
            template_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
            alpha_mask = template[:, :, 3]  # 提取 alpha 通道作为掩码
            search_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
        else:
            template_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            template_gray = None
            alpha_mask = template[:, :, 3]
            result = cv2.matchTemplate(screenshot_cv, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
    else:
        if grayscale:
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            search_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        else:
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

    # 4. 找出所有匹配位置
    locations = np.where(result >= confidence)
    w, h = template.shape[1], template.shape[0]

    # 去重：使用非极大抑制（NMS）避免重叠框
    rectangles = []
    for pt in zip(*locations[::-1]):
        rectangles.append([int(pt[0]), int(pt[1]), w, h])

    # 转换为 NumPy 数组用于 NMS
    rectangles = np.array(rectangles)
    if len(rectangles) == 0:
        return []

    # 使用非极大抑制去重
    keep = cv2.dnn.NMSBoxes(rectangles[:, :4].tolist(), result[locations], confidence, 0.3)

    # 提取保留的矩形中心点
    points = []
    if len(keep) > 0:
        for i in keep.flatten():
            x, y, w, h = rectangles[i]
            center_x = x + w // 2
            center_y = y + h // 2
            points.append((center_x, center_y))

    # # 可选：显示结果
    # if show_result:
    #     for (x, y, w, h) in rectangles:
    #         cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #     cv2.imshow('Matches', screenshot_cv)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

    return points  # 返回所有匹配的中心坐标
print(1)
# === 使用示例 ===
# def main(djx,djy):
#
#     try:
#
#         results = find_image_cv2('images/shubiao.png', confidence=0.7, show_result=True)
#         if results:
#             print(f"✅ 找到 {len(results)} 个匹配项:")
#             for i, (x, y) in enumerate(results):
#
#              if x < djx and y<djy:
#                  pyautogui.move(3, 3, duration=0.05)
#              elif x < djx and y>djy:
#                  pyautogui.move(-3, -3, duration=0.05)
#              elif x > djx and y<djy:
#                  pyautogui.move(-3, 3, duration=0.05)
#              elif x > djx and y>djy:
#                  pyautogui.move(-3, -3, duration=0.05)
#         else:
#             print("❌ 未找到匹配的图像")
#     except Exception as e:
#         print(f"错误: {e}")

import pyautogui
import cv2
import numpy as np
import time


def find_image_cv2(template_path, confidence=0.8, region=None):



    if region:
        x, y, w, h = region
        screenshot = pyautogui.screenshot(region=region)  # 直接截取指定区域
    else:
        screenshot = pyautogui.screenshot()  # 截取整个屏幕

    #screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)






    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"无法加载模板图片: {template_path}")

    if template.shape[2] == 4:  # 处理带alpha通道的图片
        alpha_channel = template[:, :, 3]
        template_bgr = template[:, :, :3]
        result = cv2.matchTemplate(screenshot_cv, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_channel)
    else:
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= confidence)
    h, w = template.shape[:2]
    points = []
    for pt in zip(*locations[::-1]):
        center_x = pt[0] + w // 2
        center_y = pt[1] + h // 2
        points.append((center_x, center_y))
    return points


# === 使用示例 ===
if __name__ == "__main__":
    start_time = time.perf_counter()
    djx=709
    djy=326
    pyautogui.moveTo(djx,djy)

    for i in range(50):
        try:
            image_path = 'images/shubiao11.png'
            a=djx-150
            b=djy-150
            c=djx+150
            d=djy+150
            region = (a,b,c,d)  # 示例区域，从 (500,300) 开始，宽400高200 的区域
            results = find_image_cv2(image_path, confidence=0.5, region=region)
            if results:
                first_match = results[0]
                x=first_match[0]-12+a
                y=first_match[1]-11+b

                if abs(x - djx) <= 3 and abs(y - djy) <= 3:
                        print("daoda")
                        pyautogui.click()
                        # 记录结束时间
                        end_time = time.perf_counter()

                        # 计算并打印耗时
                        elapsed_time = end_time - start_time
                        print(f"代码执行耗时: {elapsed_time:.4f} 秒")
                        break


                elif  x <= djx and y <= djy:
                    if abs(x - djx) > 5:
                        mx=abs(x - djx)/2
                    else:mx=2
                    if abs(y - djy) > 5:
                        my = abs(y - djy) / 2
                    else:
                        my = 2
                    pyautogui.move(mx, my)


                elif x <= djx and y >= djy:
                    if abs(x - djx) > 5:
                        mx = abs(x - djx) / 2
                    else:
                        mx = 2
                    if abs(y - djy) > 5:
                        my = abs(y - djy) / 2
                    else:
                        my = 2

                    pyautogui.move(mx, -my)
                elif x > djx and y < djy:
                    if abs(x - djx) > 5:
                        mx = abs(x - djx) / 2
                    else:
                        mx = 2
                    if abs(y - djy) > 5:
                        my = abs(y - djy) / 2
                    else:
                        my = 2
                    pyautogui.move(-mx, my)
                elif x > djx and y > djy:
                    if abs(x - djx) > 5:
                        mx = abs(x - djx) / 2
                    else:
                        mx = 2
                    if abs(y - djy) > 5:
                        my = abs(y - djy) / 2
                    else:
                        my = 2
                    pyautogui.move(-mx, -my)

            else:
                image_path = 'images/shubiao22.png'
                a = djx - 150
                b = djy - 150
                c = djx + 150
                d = djy + 150
                region = (a, b, c, d)  # 示例区域，从 (500,300) 开始，宽400高200 的区域
                results = find_image_cv2(image_path, confidence=0.5, region=region)
                if results:
                    print("找到备用鼠标")
                    first_match = results[0]
                    x = first_match[0] - 12 + a
                    y = first_match[1] - 11 + b

                    if abs(x - djx) <= 3 and abs(y - djy) <= 3:
                        print("daoda")
                        pyautogui.click()
                        # 记录结束时间
                        end_time = time.perf_counter()

                        # 计算并打印耗时
                        elapsed_time = end_time - start_time
                        print(f"代码执行耗时: {elapsed_time:.4f} 秒")

                        break
                    elif x <= djx and y <= djy:
                        if abs(x - djx) > 5:
                            mx = abs(x - djx) / 2
                        else:
                            mx = 2
                        if abs(y - djy) > 5:
                            my = abs(y - djy) / 2
                        else:
                            my = 2
                        pyautogui.move(mx, my)


                    elif x <= djx and y >= djy:
                        if abs(x - djx) > 5:
                            mx = abs(x - djx) / 2
                        else:
                            mx = 2
                        if abs(y - djy) > 5:
                            my = abs(y - djy) / 2
                        else:
                            my = 2

                        pyautogui.move(mx, -my)
                    elif x > djx and y < djy:
                        if abs(x - djx) > 5:
                            mx = abs(x - djx) / 2
                        else:
                            mx = 2
                        if abs(y - djy) > 5:
                            my = abs(y - djy) / 2
                        else:
                            my = 2
                        pyautogui.move(-mx, my)
                    elif x > djx and y > djy:
                        if abs(x - djx) > 5:
                            mx = abs(x - djx) / 2
                        else:
                            mx = 2
                        if abs(y - djy) > 5:
                            my = abs(y - djy) / 2
                        else:
                            my = 2
                        pyautogui.move(-mx, -my)


        except Exception as e:
            print(f"错误: {e}")