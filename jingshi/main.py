import logging
import os
import time

import cv2
import numpy as np
from config.config import Config
from core.image import ImageRecognizer
from core.mouse import MouseController
from core.window import WindowManager


class JingshiBuyer:
    def __init__(self):
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            datefmt=Config.LOG_DATE_FORMAT,
        )
        self.logger = logging.getLogger(__name__)

        self.window_manager = WindowManager()
        self.image_recognizer = ImageRecognizer()
        self.mouse_controller = MouseController()

    def _save_debug_image(self, image, filename):
        if not Config.DEBUG_SAVE_IMAGES or image is None:
            return
        try:
            image.save(filename)
            self.logger.info(f"保存调试图片到 {filename}")
        except Exception as exc:
            self.logger.warning(f"保存调试图片失败 {filename}: {exc}")

    def recognize_price(self, screenshot):
        """识别单价。"""
        try:
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            h, w = screenshot_cv.shape[:2]
            price_region = screenshot_cv[int(h * 0.71):int(h * 0.75), int(w * 0.62):int(w * 0.73)]

            if price_region.size == 0:
                self.logger.warning("单价区域为空")
                return None

            if Config.DEBUG_SAVE_IMAGES:
                cv2.imwrite("price_region.png", price_region)

            gray = cv2.cvtColor(price_region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

            if Config.DEBUG_SAVE_IMAGES:
                cv2.imwrite("price_thresh.png", thresh)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            digit_boxes = []
            for contour in contours:
                x, y, box_w, box_h = cv2.boundingRect(contour)
                aspect_ratio = box_w / float(box_h)
                area = box_w * box_h
                if x > 30 and 0.1 < aspect_ratio < 2.0 and 20 < area < 300 and 8 < box_h < 40:
                    digit_boxes.append((x, y, box_w, box_h))

            digit_boxes.sort(key=lambda item: item[0])
            if not digit_boxes:
                self.logger.info("未识别到数字轮廓，返回默认值 None")
                return None

            digits = []
            for _, _, box_w, box_h in digit_boxes:
                aspect_ratio = box_w / float(box_h)
                if 0.3 < aspect_ratio < 0.5:
                    digits.append("1")
                elif 0.6 < aspect_ratio < 0.7:
                    digits.append("0")
                elif 0.7 < aspect_ratio < 0.9:
                    digits.append("8")
                else:
                    digits.append("0")

            price_str = "".join(digits)
            if price_str.isdigit():
                price = int(price_str)
                self.logger.info(f"识别价格: {price}")
                return price

            contour_count = len(digit_boxes)
            if contour_count == 3:
                return 500
            if contour_count >= 4:
                return 8000
            return 5000
        except Exception as e:
            self.logger.error(f"识别单价失败: {e}")
            return None

    def run(self):
        """运行晶石购买流程。"""
        try:
            self.logger.info("开始晶石购买流程")

            if not self.window_manager.find_window():
                self.logger.error("无法找到游戏窗口，退出")
                return False

            if not self.window_manager.activate_window():
                self.logger.error("无法激活游戏窗口，退出")
                return False

            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口，退出")
                return False

            exchange_pos = self.image_recognizer.find_image_with_retry(screenshot, "EXCHANGE")
            if not exchange_pos:
                self.logger.error("未找到兑换按钮，退出")
                return False

            window_rect = self.window_manager.get_window_rect()
            if not window_rect:
                self.logger.error("无法获取窗口位置，退出")
                return False

            left, top, _, _ = window_rect
            if not self.mouse_controller.click_target(left, top, exchange_pos[0], exchange_pos[1]):
                self.logger.error("点击兑换按钮失败，退出")
                return False

            self.logger.info(f"等待 {Config.WINDOW_WAIT_DELAY} 秒让兑换窗口弹出")
            time.sleep(Config.WINDOW_WAIT_DELAY)

            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口，退出")
                return False

            self._save_debug_image(screenshot, "exchange_window.png")

            jingshi_pos = self.image_recognizer.find_image_with_retry(
                lambda: self.window_manager.capture_window(),
                "JINGSHI",
            )
            if not jingshi_pos:
                self.logger.error("未找到晶石，退出")
                return False

            if not self.mouse_controller.click_target(left, top, jingshi_pos[0], jingshi_pos[1]):
                self.logger.error("点击晶石失败，退出")
                return False

            time.sleep(0.5)

            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口，退出")
                return False

            price = self.recognize_price(screenshot)
            if price is None:
                self.logger.warning("无法识别单价，跳过购买")
                return False

            if price >= 6000:
                self.logger.info(f"单价 {price} 不低于 6000，跳过购买")
                return False

            buy_pos = self.image_recognizer.find_image_with_retry(
                lambda: self.window_manager.capture_window(),
                "BUY",
            )
            if not buy_pos:
                self.logger.error("未找到购买按钮，退出")
                return False

            if not self.mouse_controller.click_target(left, top, buy_pos[0], buy_pos[1]):
                self.logger.error("点击购买按钮失败，退出")
                return False

            self.logger.info("晶石购买流程完成")
            return True
        except Exception as e:
            self.logger.error(f"执行过程中出现异常: {e}")
            return False


if __name__ == "__main__":
    buyer = JingshiBuyer()
    buyer.run()
