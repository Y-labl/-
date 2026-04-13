import pyautogui
import cv2
import numpy as np
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MouseController:
    """鼠标控制类，负责鼠标移动和点击操作"""

    def __init__(self):
        # 鼠标模板路径
        self.mouse_templates = [
            "shimen/images/shubiao11.png",
            "shimen/images/shubiao22.png"
        ]

    def move_to(self, x, y, duration=0.1):
        """
        移动鼠标到指定位置

        :param x: 目标X坐标
        :param y: 目标Y坐标
        :param duration: 移动持续时间
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            logger.info(f"鼠标已移动到 ({x}, {y})")
        except Exception as e:
            logger.error(f"移动鼠标时出错：{str(e)}")

    def click(self, x=None, y=None, button='left', clicks=1, interval=0.0):
        """
        执行点击操作

        :param x: 点击X坐标，None表示当前位置
        :param y: 点击Y坐标，None表示当前位置
        :param button: 点击按钮，'left'或'right'
        :param clicks: 点击次数
        :param interval: 点击间隔
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
                logger.info(f"已在 ({x}, {y}) 执行 {button} 键点击 {clicks} 次")
            else:
                pyautogui.click(clicks=clicks, interval=interval, button=button)
                logger.info(f"已在当前位置执行 {button} 键点击 {clicks} 次")
        except Exception as e:
            logger.error(f"点击鼠标时出错：{str(e)}")

    def move_to_target(self, djx, djy, max_attempts=50, search_radius=150, confidence=0.5):
        """
        核心功能：将鼠标移动到目标坐标 (djx, djy)，通过匹配鼠标模板图实现定位调整

        :param djx: 目标坐标X轴
        :param djy: 目标坐标Y轴
        :param max_attempts: 最大尝试次数
        :param search_radius: 每次查找的区域半径
        :param confidence: 图片匹配阈值
        :return: 成功返回 (True, 耗时秒数)；失败返回 (False, 错误信息)
        """
        start_time = time.perf_counter()
        # 初始将鼠标移动到目标坐标附近
        pyautogui.moveTo(djx, djy, duration=0.1)

        for attempt in range(max_attempts):
            try:
                # 计算当前搜索区域
                search_x = djx - search_radius
                search_y = djy - search_radius
                search_w = 2 * search_radius
                search_h = 2 * search_radius
                current_region = (search_x, search_y, search_w, search_h)

                # 优先匹配主鼠标模板
                current_mouse = None
                for template_path in self.mouse_templates:
                    matches = self.find_image_cv2(template_path, confidence, current_region)
                    if matches:
                        current_mouse = matches[0]
                        break

                if not current_mouse:
                    # 两次匹配都失败，跳过当前轮次
                    time.sleep(0.05)
                    continue

                # 计算鼠标当前位置
                mouse_x = current_mouse[0] - 12 + search_x
                mouse_y = current_mouse[1] - 11 + search_y

                # 判断是否到达目标坐标
                if abs(mouse_x - djx) <= 3 and abs(mouse_y - djy) <= 3:
                    elapsed_time = time.perf_counter() - start_time
                    logger.info(f"✅ 成功到达目标坐标 ({djx}, {djy})，尝试次数：{attempt + 1}")
                    logger.info(f"⏱️  总耗时：{elapsed_time:.4f} 秒")
                    return (True, elapsed_time)

                # 计算鼠标移动距离
                dx = abs(mouse_x - djx)
                dy = abs(mouse_y - djy)
                move_x = dx / 2 if dx > 5 else 2
                move_y = dy / 2 if dy > 5 else 2

                # 根据鼠标与目标的相对位置，确定移动方向
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
                logger.error(error_msg)
                time.sleep(0.1)

        # 达到最大尝试次数仍未成功
        elapsed_time = time.perf_counter() - start_time
        error_msg = f"❌ 达到最大尝试次数（{max_attempts}次），未到达目标坐标"
        logger.error(f"{error_msg}，总耗时：{elapsed_time:.4f} 秒")
        return (False, error_msg)

    def find_image_cv2(self, template_path, confidence=0.8, region=None):
        """
        使用 OpenCV 在指定区域/全屏查找模板图片，返回匹配中心坐标列表

        :param template_path: 模板图片路径
        :param confidence: 匹配阈值
        :param region: 查找区域
        :return: 匹配到的中心坐标列表
        """
        try:
            # 截取指定区域/全屏图像
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            # 图像格式转换
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            # 读取模板图片
            template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
            if template is None:
                raise FileNotFoundError(f"无法加载模板图片: {template_path}")

            # 模板匹配
            if template.shape[2] == 4:  # 存在alpha透明通道
                alpha_mask = template[:, :, 3]
                template_bgr = template[:, :, :3]
                result = cv2.matchTemplate(
                    screenshot_cv, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask
                )
            else:  # 无透明通道
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

            # 提取匹配位置并计算中心坐标
            locations = np.where(result >= confidence)
            template_h, template_w = template.shape[:2]
            match_centers = []

            for pt in zip(*locations[::-1]):
                center_x = pt[0] + template_w // 2
                center_y = pt[1] + template_h // 2
                match_centers.append((center_x, center_y))

            return match_centers
        except Exception as e:
            logger.error(f"查找图像时出错：{str(e)}")
            return []
