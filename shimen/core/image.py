import time
from typing import Optional, Dict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageRecognizer:
    """图像识别类，负责在窗口中定位图像"""

    def __init__(self, window_manager):
        self.window_manager = window_manager

    def find_image_with_retry(
        self,
        template_path: str,
        max_attempts: int = 50,
        confidence: float = 0.8,
        initial_wait: float = 0.0,
        retry_wait: float = 0.2,
        save_every_n: int = 5,
        return_relative: bool = True
    ) -> Optional[Dict[str, int]]:
        """
        持续查找图像，直到找到或达到最大尝试次数

        :param template_path: 模板图像路径
        :param max_attempts: 最大查找尝试次数
        :param confidence: 图像匹配阈值
        :param initial_wait: 函数启动后的初始等待时间
        :param retry_wait: 每次查找失败后的重试间隔
        :param save_every_n: 每n次尝试保存一次匹配结果图
        :param return_relative: 是否返回相对于目标窗口的坐标
        :return: 匹配成功时返回字典，失败返回None
        """
        # 初始等待
        if initial_wait > 0:
            logger.info(f"[初始化] 等待 {initial_wait:.1f} 秒（目标窗口/图像加载中）...")
            time.sleep(initial_wait)

        # 循环尝试查找图像
        for attempt in range(1, max_attempts + 1):
            try:
                # 决定当前尝试是否保存调试图
                need_save = (attempt % save_every_n == 0)
                logger.info(f"[尝试 {attempt:2d}/{max_attempts}] 查找模板：{template_path} "
                            f"（匹配阈值：{confidence:.1f}）")

                # 调用底层定位函数
                locate_result = self.window_manager.locate_image_on_screen(
                    template_path=template_path,
                    confidence=confidence,
                    save_result=need_save
                )

                # 解析底层结果，生成完整坐标信息
                if locate_result:
                    # 假设底层函数返回：(rel_x, rel_y, width, height, window_abs_x, window_abs_y)
                    rel_x, rel_y, img_width, img_height, win_abs_x, win_abs_y = locate_result

                    # 计算绝对坐标
                    abs_x = win_abs_x + rel_x
                    abs_y = win_abs_y + rel_y

                    # 计算匹配区域中心坐标
                    center_x = abs_x + (img_width // 2)
                    center_y = abs_y + (img_height // 2)

                    # 构建返回字典
                    result = {
                        "abs_x": abs_x,
                        "abs_y": abs_y,
                        "width": img_width,
                        "height": img_height,
                        "center_x": center_x,
                        "center_y": center_y
                    }
                    # 若需要返回相对坐标，补充到结果中
                    if return_relative:
                        result.update({
                            "rel_x": rel_x,
                            "rel_y": rel_y
                        })

                    # 打印成功日志
                    logger.info(f"[成功] 找到匹配图像！\n"
                                f"  - 屏幕绝对坐标（左上角）：({abs_x}, {abs_y})\n"
                                f"  - 匹配区域尺寸：{img_width}x{img_height}\n"
                                f"  - 屏幕中心坐标：({center_x}, {center_y})")
                    return result

                # 若未找到，打印提示
                logger.info(f"[尝试 {attempt:2d}/{max_attempts}] 未找到匹配图像，{retry_wait:.1f} 秒后重试...")

            # 捕获并处理异常
            except Exception as e:
                # 区分「致命错误」和「非致命错误」
                if "窗口不存在" in str(e) or "窗口未激活" in str(e):
                    logger.error(f"[致命错误] 目标窗口异常：{str(e)}，终止查找")
                    return None
                # 非致命错误，记录后继续重试
                logger.error(f"[尝试 {attempt:2d}/{max_attempts}] 查找出错：{str(e)}，{retry_wait:.1f} 秒后重试...")

            # 重试前等待
            time.sleep(retry_wait)

        # 达到最大尝试次数，返回失败
        logger.error(f"[失败] 已达到最大尝试次数（{max_attempts}次），仍未找到模板：{template_path}")
        return None

    def locate_image(self, template_path, confidence=0.8):
        """
        在窗口中定位图像

        :param template_path: 模板图像路径
        :param confidence: 匹配阈值
        :return: 匹配结果或None
        """
        try:
            result = self.window_manager.locate_image_on_screen(template_path, confidence)
            if result:
                rel_x, rel_y, img_width, img_height, win_abs_x, win_abs_y = result
                abs_x = win_abs_x + rel_x
                abs_y = win_abs_y + rel_y
                center_x = abs_x + (img_width // 2)
                center_y = abs_y + (img_height // 2)
                return {
                    "abs_x": abs_x,
                    "abs_y": abs_y,
                    "width": img_width,
                    "height": img_height,
                    "center_x": center_x,
                    "center_y": center_y,
                    "rel_x": rel_x,
                    "rel_y": rel_y
                }
            return None
        except Exception as e:
            logger.error(f"定位图像时出错：{str(e)}")
            return None
