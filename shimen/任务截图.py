import logging
from PIL import Image
from typing import Optional, Tuple
import pyautogui
import time
import win32gui
import win32con
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WindowManager:
    """窗口管理类，负责窗口查找、激活和截图"""

    def __init__(self, window_title=None):
        self.window_title = window_title
        self.window_handle = None  # 窗口句柄
        self.window_rect = None  # 窗口在屏幕上的坐标 (left, top, right, bottom)
        self.client_rect = None  # 窗口客户区坐标
        self.border_offset = (0, 0)  # 窗口边框和标题栏的偏移量
        self.dpi_scale = 1  # DPI缩放比例

    def find_and_activate_window(self) -> bool:
        """查找并激活指定标题的窗口"""
        self.window_handle = win32gui.FindWindow(None, self.window_title)
        if self.window_handle == 0:
            logger.error(f"未找到窗口: {self.window_title}")
            return False

        # 检查并恢复最小化窗口
        if win32gui.IsIconic(self.window_handle):
            win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)

        win32gui.ShowWindow(self.window_handle, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(self.window_handle)
        time.sleep(0.5)  # 等待窗口激活

        # 获取窗口位置和大小（包括边框和标题栏）
        self.window_rect = win32gui.GetWindowRect(self.window_handle)

        # 获取客户区位置和大小（不包括边框和标题栏）
        client_rect = win32gui.GetClientRect(self.window_handle)
        client_left, client_top = win32gui.ClientToScreen(self.window_handle, (0, 0))
        self.client_rect = (client_left, client_top, client_rect[2], client_rect[3])

        # 计算边框和标题栏的偏移量
        self.border_offset = (
            client_left - self.window_rect[0],
            client_top - self.window_rect[1]
        )

        # 尝试获取DPI缩放比例
        try:
            screen_width, screen_height = pyautogui.size()
            self.dpi_scale = screen_width / 96  # 假设96 DPI为基准
        except Exception as e:
            logger.error(f"获取DPI缩放比例失败，使用默认值1，错误: {e}")
            self.dpi_scale = 1

        logger.info(f"激活后窗口位置和大小: {self.window_rect}")
        logger.info(f"客户区位置和大小: {self.client_rect}")
        logger.info(f"窗口边框偏移: {self.border_offset}")
        logger.info(f"DPI缩放比例: {self.dpi_scale}")

        return True

    def capture_by_hwnd(self, hwnd: int, task_left: int, task_top: int, task_width: int, task_height: int) -> Optional[Image.Image]:
        """
        通过窗口句柄截图窗口内指定区域

        :param hwnd: 窗口句柄
        :param task_left: 目标区域相对窗口左边界的偏移
        :param task_top: 目标区域相对窗口上边界的偏移
        :param task_width: 目标区域宽度
        :param task_height: 目标区域高度
        :return: PIL图像对象，失败返回None
        """
        if hwnd == 0:
            logger.error("无效的窗口句柄")
            return None

        # 检查并恢复最小化窗口
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)  # 等待窗口激活

        # 获取窗口在屏幕上的坐标
        window_rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = window_rect
        logger.info(f"窗口坐标：左{left}, 上{top}, 右{right}, 下{bottom}")

        # 计算绝对坐标
        abs_left = left + task_left
        abs_top = top + task_top

        try:
            # 截图
            screenshot = pyautogui.screenshot(region=(abs_left, abs_top, task_width, task_height))
            return screenshot
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return None

    def save_screenshot_by_hwnd(self, hwnd: int, task_left: int, task_top: int, task_width: int, task_height: int, save_path: str) -> bool:
        """
        通过窗口句柄截图并保存窗口内指定区域

        :param hwnd: 窗口句柄
        :param task_left: 目标区域相对窗口左边界的偏移
        :param task_top: 目标区域相对窗口上边界的偏移
        :param task_width: 目标区域宽度
        :param task_height: 目标区域高度
        :param save_path: 保存路径
        :return: 是否保存成功
        """
        img = self.capture_by_hwnd(hwnd, task_left, task_top, task_width, task_height)
        if not img:
            return False

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            img.save(save_path)
            logger.info(f"截图已保存至: {save_path}")
            return True
        except Exception as e:
            logger.error(f"保存截图失败: {str(e)}")
            return False

    def is_window_visible(self) -> bool:
        """检查窗口是否可见"""
        if not self.window_handle:
            return False
        return win32gui.IsWindowVisible(self.window_handle)

    def capture_region(self,
                       rel_left: int,
                       rel_top: int,
                       width: int,
                       height: int,
                       use_client_area: bool = False) -> Optional[Image.Image]:
        """
        在窗口内指定相对位置截图

        :param rel_left: 相对于窗口左上角的左偏移（像素）
        :param rel_top: 相对于窗口左上角的上偏移（像素）
        :param width: 截图宽度
        :param height: 截图高度
        :param use_client_area: 是否基于客户区（不含标题栏）计算偏移
        :return: PIL图像对象，失败返回None
        """
        if not self.window_handle:
            logger.error("未找到窗口句柄，无法截图")
            return None

        if not self.is_window_visible():
            logger.warning("窗口不可见，可能影响截图结果")

        # 获取基准坐标（整个窗口/客户区）
        if use_client_area and self.client_rect:
            base_left, base_top, _, _ = self.client_rect
            logger.info(f"基于客户区坐标: ({base_left}, {base_top})")
        else:
            base_left, base_top, _, _ = self.window_rect
            logger.info(f"基于整个窗口坐标: ({base_left}, {base_top})")

        # 应用DPI缩放
        rel_left = int(rel_left / self.dpi_scale)
        rel_top = int(rel_top / self.dpi_scale)
        width = int(width / self.dpi_scale)
        height = int(height / self.dpi_scale)

        # 计算绝对坐标
        abs_left = base_left + rel_left
        abs_top = base_top + rel_top
        logger.debug(f"绝对坐标: ({abs_left}, {abs_top}), 尺寸: {width}x{height}")

        try:
            # 截图
            screenshot = pyautogui.screenshot(region=(abs_left, abs_top, width, height))
            return Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return None

    def save_screenshot(self,
                        rel_left: int,
                        rel_top: int,
                        width: int,
                        height: int,
                        save_path: str,
                        use_client_area: bool = False) -> bool:
        """截图并保存到文件"""
        img = self.capture_region(rel_left, rel_top, width, height, use_client_area)
        if not img:
            return False

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            img.save(save_path)
            logger.info(f"截图已保存至: {save_path}")
            return True
        except Exception as e:
            logger.error(f"保存截图失败: {str(e)}")
            return False


# 主程序示例
def main():
    window_title = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - 紫月べ清风[37279872])"
    window_manager = WindowManager(window_title)

    # 方法1：通过窗口标题查找并截图
    if window_manager.find_and_activate_window():
        # 截图窗口内相对位置（示例）
        window_manager.save_screenshot(
            rel_left=100,
            rel_top=100,
            width=200,
            height=100,
            save_path="screenshot_by_title.png",
            use_client_area=False
        )

    # 方法2：通过窗口句柄截图
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd != 0:
        # 任务追踪区域参数（需根据实际调整）
        task_left = 800
        task_top = 150
        task_width = 200
        task_height = 100
        window_manager.save_screenshot_by_hwnd(
            hwnd=hwnd,
            task_left=task_left,
            task_top=task_top,
            task_width=task_width,
            task_height=task_height,
            save_path="renwu_images/task_images.png"
        )
    else:
        print("未找到窗口句柄")


def capture_task_tracking(window_title, save_path):
    """
    截取指定窗口的任务追踪区域并保存

    :param window_title: 目标窗口的标题
    :param save_path: 截图保存的路径
    :return: 是否截图成功（True/False）
    """
    # 查找窗口句柄
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        print(f"未找到标题为 '{window_title}' 的窗口")
        return False

    # 显示并激活窗口
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(1)  # 等待窗口完全激活

    # 获取窗口在屏幕上的坐标
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    print(f"窗口坐标：左{left}, 上{top}, 右{right}, 下{bottom}")

    # 计算任务追踪区域的坐标（窗口内右上角）
    task_left = right - 200
    task_top = top + 200
    task_width = 200
    task_height = 90

    try:
        # 截图并保存
        screenshot = pyautogui.screenshot(region=(task_left, task_top, task_width, task_height))
        screenshot.save(save_path)
        print(f"截图成功，已保存至 {save_path}")
        return True
    except Exception as e:
        print(f"截图失败：{e}")
        return False

if __name__ == "__main__":
    main()