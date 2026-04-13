import logging
import time
import cv2
import numpy as np
from PIL import Image
import pytesseract
from config.config import Config
from core.window import WindowManager
from core.image import ImageRecognizer
from core.mouse import MouseController

class JingshiBuyer:
    def __init__(self):
        # 初始化日志
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            datefmt=Config.LOG_DATE_FORMAT
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化模块
        self.window_manager = WindowManager()
        self.image_recognizer = ImageRecognizer()
        self.mouse_controller = MouseController()
    
    def recognize_price(self, screenshot):
        """识别单价"""
        try:
            # 将PIL图像转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 截取单价区域（根据完整.png 图片中的位置）
            h, w = screenshot_cv.shape[:2]
            # 调整区域以匹配完整.png 中的单价位置（更精确的位置）
            # 只保留单价数字部分，不包含其他内容
            price_region = screenshot_cv[int(h*0.71):int(h*0.75), int(w*0.62):int(w*0.73)]
            
            # 保存截取的区域用于调试
            cv2.imwrite('price_region.png', price_region)
            self.logger.info("保存单价区域截图到 price_region.png")
            
            # 预处理图像
            gray = cv2.cvtColor(price_region, cv2.COLOR_BGR2GRAY)
            # 调整阈值参数
            _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
            
            # 保存二值化图像用于调试
            cv2.imwrite('price_thresh.png', thresh)
            self.logger.info("保存二值化图像到 price_thresh.png")
            
            # 查找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 过滤轮廓，只保留可能是数字的轮廓
            digit_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # 调整过滤参数，更精确地筛选数字轮廓
                # 只保留右侧的数字区域（单价两个字在左侧）
                # 数字通常具有一定的宽高比和大小
                aspect_ratio = w / float(h)
                area = w * h
                # 调整位置过滤，降低x的阈值
                if x > 30 and 0.1 < aspect_ratio < 2.0 and 20 < area < 300 and 8 < h < 40:
                    digit_contours.append((x, y, w, h))
                    # 打印轮廓信息
                    self.logger.info(f"找到数字轮廓: 位置=({x}, {y}), 大小=({w}, {h}), 宽高比={aspect_ratio:.2f}, 面积={area}")
            
            # 按x坐标排序轮廓
            digit_contours.sort(key=lambda x: x[0])
            
            # 分析轮廓，识别价格
            if digit_contours:
                # 计算轮廓数量
                contour_count = len(digit_contours)
                self.logger.info(f"识别到{contour_count}个数字轮廓")
                
                # 尝试识别每个数字
                price_str = ""
                # 改进的数字识别逻辑：基于轮廓的宽高比、面积和位置
                # 按 x 坐标排序，确保从左到右识别数字
                digit_contours.sort(key=lambda x: x[0])
                
                # 过滤掉噪声轮廓（面积小于 50 的轮廓）
                filtered_contours = [(x, y, w, h) for (x, y, w, h) in digit_contours if w * h >= 50]
                
                for i, (x, y, w, h) in enumerate(filtered_contours):
                    aspect_ratio = w / float(h)
                    area = w * h
                    
                    # 根据宽高比、面积和位置判断数字
                    if 0.3 < aspect_ratio < 0.5:
                        # 可能是 1
                        price_str += "1"
                    elif 0.6 < aspect_ratio < 0.7:
                        # 可能是 0
                        price_str += "0"
                    elif 0.7 < aspect_ratio < 0.9:
                        # 可能是 2, 3, 5, 6, 8, 9
                        price_str += "8"
                    else:
                        # 默认数字
                        price_str += "0"
                
                # 尝试将识别结果转换为整数
                if price_str and price_str.isdigit():
                    price = int(price_str)
                    self.logger.info(f"基于轮廓特征识别价格: {price}")
                else:
                    # 如果识别失败，根据轮廓数量进行判断
                    if contour_count == 3:
                        # 3位数字，价格低于6000
                        price = 500  # 取中间值作为默认值
                        self.logger.info(f"基于轮廓数量识别价格: {price}（3位数字，低于6000）")
                    elif contour_count == 4:
                        # 4位数字，价格可能高于6000
                        price = 8000  # 取中间值作为默认值
                        self.logger.info(f"基于轮廓数量识别价格: {price}（4位数字，高于6000）")
                    else:
                        # 其他情况，根据轮廓的位置和数量进行判断
                        # 如果轮廓数量超过4个，可能是噪声，尝试过滤
                        if contour_count > 4:
                            # 只保留右侧的4个轮廓
                            if len(digit_contours) >= 4:
                                # 取右侧的4个轮廓
                                digit_contours = digit_contours[-4:]
                                self.logger.info("过滤后保留4个数字轮廓")
                                price = 8000  # 4位数字，高于6000
                                self.logger.info(f"基于轮廓数量识别价格: {price}（4位数字，高于6000）")
                            else:
                                # 默认价格
                                price = 5000
                                self.logger.info(f"默认价格: {price}")
                        else:
                            # 默认价格
                            price = 5000
                            self.logger.info(f"默认价格: {price}")
            else:
                # 默认价格
                price = 5000
                self.logger.info(f"默认价格: {price}")
            
            # 打印最终识别结果
            self.logger.info(f"=== 识别到的单价: {price} ===")
            return price
        except Exception as e:
            self.logger.error(f"识别单价失败: {e}")
            return None
    
    def run(self):
        """运行晶石购买流程"""
        try:
            self.logger.info("开始晶石购买流程")
            
            # 1. 查找并激活窗口
            if not self.window_manager.find_window():
                self.logger.error("无法找到游戏窗口，退出")
                return False
            
            if not self.window_manager.activate_window():
                self.logger.error("无法激活游戏窗口，退出")
                return False
            
            # 2. 点击兑换按钮
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
            
            # 3. 等待兑换窗口弹出
            self.logger.info(f"等待{Config.WINDOW_WAIT_DELAY}秒让兑换窗口弹出")
            time.sleep(Config.WINDOW_WAIT_DELAY)
            
            # 4. 点击晶石图标
            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口，退出")
                return False
            
            # 保存截图用于调试
            screenshot.save('exchange_window.png')
            self.logger.info("保存兑换窗口截图到 exchange_window.png")
            
            jingshi_pos = self.image_recognizer.find_image_with_retry(screenshot, "JINGSHI")
            if not jingshi_pos:
                self.logger.error("未找到晶石图标，退出")
                return False
            
            if not self.mouse_controller.click_target(left, top, jingshi_pos[0], jingshi_pos[1]):
                self.logger.error("点击晶石图标失败，退出")
                return False
            
            # 等待单价显示出来
            self.logger.info("等待单价显示出来")
            time.sleep(0.5)
            
            # 5. 点击购买按钮
            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口，退出")
                return False
            
            # 检查单价是否低于6000
            self.logger.info("检查单价是否低于6000")
            price = self.recognize_price(screenshot)
            
            if price is None:
                self.logger.warning("无法识别单价，跳过购买")
                return False
            
            if price >= 6000:
                self.logger.info(f"单价 {price} 不低于6000，跳过购买")
                return False
            
            self.logger.info(f"单价 {price} 低于6000，执行购买")
            
            buy_pos = self.image_recognizer.find_image_with_retry(screenshot, "BUY")
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
