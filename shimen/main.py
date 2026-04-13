import time
import os
import sys
import logging
import traceback
import pyautogui

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入模块
try:
    from config.config import Config
    from core.window import WindowManager
    from core.image import ImageRecognizer
    from core.mouse import MouseController
    from core.ocr import OCRExtractor
    logger.info("模块导入成功")
except Exception as e:
    logger.error(f"模块导入失败: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)


def capture_task_tracking(window_title, save_path):
    """
    截取指定窗口的任务追踪区域并保存

    :param window_title: 目标窗口的标题
    :param save_path: 截图保存的路径
    :return: 是否截图成功（True/False）
    """
    try:
        import pygetwindow as gw
        
        # 查找窗口
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            logger.error(f"未找到标题为 '{window_title}' 的窗口")
            return False
        
        window = windows[0]
        
        # 检查并恢复最小化窗口
        if window.isMinimized:
            window.restore()
        
        # 尝试激活窗口，但即使失败也继续执行
        try:
            window.activate()
        except Exception as e:
            logger.warning(f"激活窗口时出错：{e}，继续执行截图")
        
        time.sleep(1)  # 等待窗口完全激活

        # 获取窗口在屏幕上的坐标
        left = window.left
        top = window.top
        right = left + window.width
        bottom = top + window.height
        logger.info(f"窗口坐标：左{left}, 上{top}, 右{right}, 下{bottom}")

        # 计算任务追踪区域的坐标（窗口内）
        task_left = left + Config.TASK_TRACKING["LEFT"]
        task_top = top + Config.TASK_TRACKING["TOP"]
        task_width = Config.TASK_TRACKING["WIDTH"]
        task_height = Config.TASK_TRACKING["HEIGHT"]

        # 截图并保存
        screenshot = pyautogui.screenshot(region=(task_left, task_top, task_width, task_height))
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        screenshot.save(save_path)
        logger.info(f"截图成功，已保存至 {save_path}")
        return True
    except Exception as e:
        logger.error(f"截图失败：{e}")
        logger.error(traceback.format_exc())
        return False


def main():
    """主程序"""
    try:
        logger.info("开始执行梦幻西游师门任务自动化脚本")
        
        # 1. 初始化各个模块
        window_manager = WindowManager(Config.WINDOW_TITLE)
        image_recognizer = ImageRecognizer(window_manager)
        mouse_controller = MouseController()
        ocr_extractor = OCRExtractor()
        
        # 2. 查找并激活窗口
        logger.info("正在查找并激活游戏窗口...")
        if not window_manager.find_and_activate_window():
            logger.error("无法找到或激活游戏窗口，退出脚本")
            return
        
        # 3. 截取任务追踪区域并识别文字
        logger.info("正在截取任务追踪区域...")
        task_image_path = "renwu_images/task_images.png"
        if capture_task_tracking(Config.WINDOW_TITLE, task_image_path):
            logger.info("正在识别任务文本...")
            result = ocr_extractor.process_image(task_image_path, use_enhanced_preprocess=True)
            if result["success"]:
                logger.info("合并后的完整文本：" + result["full_text"])
                logger.info("\n提取的重点信息：")
                for k, v in result["key_info"].items():
                    logger.info(f"{k}：{v}")
            else:
                logger.error("错误：" + result["message"])
        
        # 4. 识别并点击坐标
        logger.info("正在识别坐标...")
        zuobiao_path = Config.get_template_path("ZUOBIAO")
        if zuobiao_path:
            zuobiao_result = image_recognizer.find_image_with_retry(
                zuobiao_path,
                max_attempts=Config.MAX_ATTEMPTS,
                confidence=Config.CONFIDENCE,
                retry_wait=Config.RETRY_WAIT
            )
            
            if zuobiao_result:
                x = zuobiao_result["center_x"]
                y = zuobiao_result["center_y"]
                logger.info(f"找到坐标位置: ({x}, {y})")
                
                # 移动鼠标到坐标位置
                success, info = mouse_controller.move_to_target(x, y)
                if success:
                    logger.info(f"任务完成，耗时：{info:.4f} 秒")
                else:
                    logger.error(f"任务失败：{info}")
            else:
                logger.error("未找到坐标，退出脚本")
        else:
            logger.error("无法获取坐标模板路径")
        
        logger.info("师门任务自动化脚本执行完毕")
        
    except Exception as e:
        logger.error(f"脚本执行过程中出错：{str(e)}")


if __name__ == "__main__":
    main()
