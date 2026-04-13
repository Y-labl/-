import time
from typing import Optional, Tuple, Dict  # 引入类型提示，提升代码可读性和维护性


def find_image_with_retry(
    window_manager,
    template_path: str,
    max_attempts: int = 50,
    confidence: float = 0.8,
    initial_wait: float = 0.0,
    retry_wait: float = 0.2,
    save_every_n: int = 5,
    return_relative: bool = True  # 新增：是否返回相对于目标窗口的坐标（默认是）
) -> Optional[Dict[str, int]]:
    """
    持续查找图像，直到找到或达到最大尝试次数，明确返回匹配坐标及相关信息

    :param window_manager: 窗口管理器实例（需包含窗口坐标获取、截图等核心方法）
    :param template_path: 模板图像路径（如 'templates/button.png'）
    :param max_attempts: 最大查找尝试次数，超过则返回None，默认50次
    :param confidence: 图像匹配阈值（0~1），值越高匹配越严格，默认0.8
    :param initial_wait: 函数启动后的初始等待时间（秒），用于等待目标窗口/图像加载，默认0秒
    :param retry_wait: 每次查找失败后的重试间隔（秒），默认0.2秒（平衡效率与资源占用）
    :param save_every_n: 每n次尝试保存一次匹配结果图（调试用），默认每5次保存一次
    :param return_relative: 是否返回「相对于目标窗口」的坐标（True）或「屏幕绝对坐标」（False），默认True
    :return: 匹配成功时返回字典（含坐标和尺寸），失败返回None。
             字典结构：{
                 "abs_x": 屏幕绝对X坐标（左上角）,
                 "abs_y": 屏幕绝对Y坐标（左上角）,
                 "rel_x": 相对于窗口的X坐标（左上角，仅return_relative=True时存在）,
                 "rel_y": 相对于窗口的Y坐标（左上角，仅return_relative=True时存在）,
                 "width": 模板图像宽度,
                 "height": 模板图像高度,
                 "center_x": 匹配区域屏幕绝对中心X坐标,
                 "center_y": 匹配区域屏幕绝对中心Y坐标
             }
    """
    # 1. 初始等待（确保目标窗口/图像有足够时间加载，避免启动即失败）
    if initial_wait > 0:
        print(f"[初始化] 等待 {initial_wait:.1f} 秒（目标窗口/图像加载中）...")
        time.sleep(initial_wait)

    # 2. 循环尝试查找图像
    for attempt in range(1, max_attempts + 1):  # 从1开始计数，更符合用户直觉
        try:
            # 决定当前尝试是否保存调试图（每save_every_n次保存一次）
            need_save = (attempt % save_every_n == 0)
            print(f"[尝试 {attempt:2d}/{max_attempts}] 查找模板：{template_path} "
                  f"（匹配阈值：{confidence:.1f}，{'将保存调试图' if need_save else '不保存调试图'}）")

            # 调用底层定位函数（假设 window_manager.locate_image_on_screen 返回基础匹配信息）
            # 此处默认底层函数返回 Tuple[相对X, 相对Y, 宽度, 高度, 窗口绝对X, 窗口绝对Y]
            # 若底层函数返回格式不同，需根据实际情况调整下方解析逻辑
            locate_result = window_manager.locate_image_on_screen(
                template_path=template_path,
                confidence=confidence,
                save_result=need_save
            )

            # 3. 解析底层结果，生成完整坐标信息
            if locate_result:
                # 假设底层函数返回：(rel_x, rel_y, width, height, window_abs_x, window_abs_y)
                rel_x, rel_y, img_width, img_height, win_abs_x, win_abs_y = locate_result

                # 计算绝对坐标（相对窗口坐标 + 窗口绝对坐标）
                abs_x = win_abs_x + rel_x
                abs_y = win_abs_y + rel_y

                # 计算匹配区域中心坐标（便于后续鼠标点击等操作）
                center_x = abs_x + (img_width // 2)
                center_y = abs_y + (img_height // 2)

                # 构建返回字典（根据 return_relative 决定是否包含相对坐标）
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

                # 打印成功日志（包含关键坐标，方便调试）
                print(f"[成功] 找到匹配图像！\n"
                      f"  - 屏幕绝对坐标（左上角）：({abs_x}, {abs_y})\n"
                      f"  - 匹配区域尺寸：{img_width}x{img_height}\n"
                      f"  - 屏幕中心坐标：({center_x}, {center_y})")
                return result

            # 若未找到，打印提示（不报错，仅告知状态）
            print(f"[尝试 {attempt:2d}/{max_attempts}] 未找到匹配图像，{retry_wait:.1f} 秒后重试...")

        # 4. 捕获并处理异常（避免单次错误导致整个循环终止）
        except Exception as e:
            # 区分「致命错误」和「非致命错误」：若窗口不存在，直接终止（无需继续重试）
            if "窗口不存在" in str(e) or "窗口未激活" in str(e):
                print(f"[致命错误] 目标窗口异常：{str(e)}，终止查找（无需继续重试）")
                return None
            # 非致命错误（如截图临时失败、模板读取异常），记录后继续重试
            print(f"[尝试 {attempt:2d}/{max_attempts}] 查找出错（非致命）：{str(e)}，{retry_wait:.1f} 秒后重试...")

        # 5. 重试前等待（避免高频循环占用过多CPU）
        time.sleep(retry_wait)

    # 6. 达到最大尝试次数，返回失败
    print(f"[失败] 已达到最大尝试次数（{max_attempts}次），仍未找到模板：{template_path}")
    return None