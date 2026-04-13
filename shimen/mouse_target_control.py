# mouse_target_control.py
import pyautogui
import cv2
import numpy as np
import time


def find_image_cv2(template_path, confidence=0.8, region=None):
    """
    使用 OpenCV 在指定区域/全屏查找模板图片，返回匹配中心坐标列表

    :param template_path: 模板图片路径（如 'images/shubiao11.png'）
    :param confidence: 匹配阈值（0~1），值越高匹配越严格
    :param region: 查找区域（x, y, w, h），x/y为区域左上角坐标，w/h为宽高；None表示全屏
    :return: 匹配到的中心坐标列表，每个元素为 (center_x, center_y)；未匹配到返回空列表
    """
    # 1. 截取指定区域/全屏图像
    try:
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
    except Exception as e:
        raise RuntimeError(f"截图失败: {str(e)}")

    # 2. 图像格式转换（PyAutoGUI截图为RGB，OpenCV为BGR）
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 3. 读取模板图片（处理透明通道）
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"无法加载模板图片: {template_path}")

    # 4. 模板匹配（支持透明PNG的alpha通道掩码）
    if template.shape[2] == 4:  # 存在alpha透明通道
        alpha_mask = template[:, :, 3]  # 提取透明掩码
        template_bgr = template[:, :, :3]  # 提取RGB通道
        result = cv2.matchTemplate(
            screenshot_cv, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask
        )
    else:  # 无透明通道（普通RGB图片）
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

    # 5. 提取匹配位置并计算中心坐标
    locations = np.where(result >= confidence)
    template_h, template_w = template.shape[:2]  # 模板图片的高、宽
    match_centers = []

    for pt in zip(*locations[::-1]):  # pt为匹配区域左上角坐标 (x, y)
        center_x = pt[0] + template_w // 2  # 计算中心x坐标
        center_y = pt[1] + template_h // 2  # 计算中心y坐标
        match_centers.append((center_x, center_y))

    return match_centers


def move_mouse_to_target(djx, djy, max_attempts=50, search_radius=150, confidence=0.5):
    """
    核心功能：将鼠标移动到目标坐标 (djx, djy)，通过匹配鼠标模板图实现定位调整

    :param djx: 目标坐标X轴（必填）
    :param djy: 目标坐标Y轴（必填）
    :param max_attempts: 最大尝试次数（默认50次，防止无限循环）
    :param search_radius: 每次查找的区域半径（默认150像素，围绕当前鼠标位置）
    :param confidence: 图片匹配阈值（默认0.5，可根据模板清晰度调整）
    :return: 成功返回 (True, 耗时秒数)；失败返回 (False, 错误信息)
    """
    start_time = time.perf_counter()
    # 初始将鼠标移动到目标坐标附近（减少初始搜索范围）
    pyautogui.moveTo(djx, djy, duration=0.1)  # duration=0.1 增加移动平滑度

    for attempt in range(max_attempts):
        try:
            # 1. 计算当前搜索区域（围绕目标坐标的正方形区域）
            search_x = djx - search_radius
            search_y = djy - search_radius
            search_w = 2 * search_radius  # 宽度 = 2*半径
            search_h = 2 * search_radius  # 高度 = 2*半径
            current_region = (search_x, search_y, search_w, search_h)

            # 2. 优先匹配主鼠标模板（shubiao11.png）
            main_template = "images/shubiao11.png"
            main_matches = find_image_cv2(main_template, confidence, current_region)

            if main_matches:
                current_mouse = main_matches[0]  # 取第一个匹配结果
            else:
                # 3. 主模板匹配失败，尝试备用模板（shubiao22.png）
                backup_template = "images/shubiao22.png"
                backup_matches = find_image_cv2(backup_template, confidence, current_region)
                if not backup_matches:
                    # 两次匹配都失败，跳过当前轮次（继续尝试）
                    time.sleep(0.05)  # 短暂休眠，减少CPU占用
                    continue
                current_mouse = backup_matches[0]
                print(f"第{attempt + 1}次尝试：使用备用鼠标模板匹配")

            # 4. 计算鼠标当前位置（修正搜索区域的坐标偏移）
            # 注：模板匹配的坐标是相对于搜索区域的，需加上搜索区域的左上角X/Y
            mouse_x = current_mouse[0] - 12 + search_x  # -12 为原代码中的偏移修正
            mouse_y = current_mouse[1] - 11 + search_y  # -11 为原代码中的偏移修正

            # 5. 判断是否到达目标坐标（误差≤3像素）
            if abs(mouse_x - djx) <= 3 and abs(mouse_y - djy) <= 3:
                # pyautogui.click()  # 到达目标后点击
                elapsed_time = time.perf_counter() - start_time
                print(f"✅ 成功到达目标坐标 ({djx}, {djy})，尝试次数：{attempt + 1}")
                print(f"⏱️  总耗时：{elapsed_time:.4f} 秒")
                return (True, elapsed_time)

            # 6. 计算鼠标移动距离（按误差的1/2移动，加快收敛）
            dx = abs(mouse_x - djx)
            dy = abs(mouse_y - djy)
            move_x = dx / 2 if dx > 5 else 2  # 误差>5像素时按比例移动，否则固定移动2像素
            move_y = dy / 2 if dy > 5 else 2

            # 7. 根据鼠标与目标的相对位置，确定移动方向
            if mouse_x <= djx and mouse_y <= djy:
                pyautogui.move(move_x, move_y, duration=0.02)
            elif mouse_x <= djx and mouse_y >= djy:
                pyautogui.move(move_x, -move_y, duration=0.02)
            elif mouse_x > djx and mouse_y < djy:
                pyautogui.move(-move_x, move_y, duration=0.02)
            elif mouse_x > djx and mouse_y >= djy:
                pyautogui.move(-move_x, -move_y, duration=0.02)

            # 短暂休眠，避免操作过快
            time.sleep(0.05)

        except Exception as e:
            error_msg = f"第{attempt + 1}次尝试出错：{str(e)}"
            print(error_msg)
            time.sleep(0.1)  # 出错后稍等再重试

    # 达到最大尝试次数仍未成功
    elapsed_time = time.perf_counter() - start_time
    error_msg = f"❌ 达到最大尝试次数（{max_attempts}次），未到达目标坐标"
    print(f"{error_msg}，总耗时：{elapsed_time:.4f} 秒")
    return (False, error_msg)


# ------------------- 测试用例（直接运行该文件时执行）-------------------
if __name__ == "__main__":
    # 测试：将目标坐标设为 (709, 326)（原代码默认值）
    target_x = 709
    target_y = 326
    print(f"开始执行鼠标移动任务，目标坐标：({target_x}, {target_y})")

    # 调用核心函数
    success, info = move_mouse_to_target(target_x, target_y)
    if success:
        print(f"任务完成，耗时：{info:.4f} 秒")
    else:
        print(f"任务失败：{info}")