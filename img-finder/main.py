"""
在窗口中查找图片位置（窗口内相对坐标）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_finder import ImageFinder


def main():
    # 请根据实际情况修改以下参数
    window_title = "Phone-4HDVB23218001313"
    template_path = r"d:\Program Files\mhxy-project\jingshi\兑换.png"

    if not os.path.exists(template_path):
        print(f"错误：图片文件不存在: {template_path}")
        return

    finder = ImageFinder(window_title)

    print(f"正在窗口 '{window_title}' 中查找图片: {template_path}")
    print("注意：返回的坐标是窗口内坐标（相对于窗口左上角），不是屏幕坐标")
    print("=" * 60)

    result = finder.find_image(
        template_path=template_path,
        confidence=0.5
    )

    if result:
        print("\n[找到]")
        print(f"  ├─ 窗口内左上角坐标: ({result['x']}, {result['y']})")
        print(f"  ├─ 窗口内中心坐标: ({result['center_x']}, {result['center_y']})")
        print(f"  ├─ 图片尺寸: {result['width']} x {result['height']}")
        print(f"  └─ 匹配置信度: {result['confidence']}")
    else:
        print("\n[未找到] 未在窗口中匹配到图片，请检查：")
        print("  1. 窗口标题是否正确")
        print("  2. 图片文件是否正确")
        print("  3. 图片是否在窗口可见区域内")


if __name__ == "__main__":
    main()
