# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\widget_util.py
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

def clear_layout(layout):
    """
    清空 QGridLayout 中的所有 widget
    :param layout: 目标 QGridLayout 对象
    """
    if layout is None:
        return
    else:
        while True:
            if layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                child_layout = item.layout()
                if child_layout is not None:
                    clear_layout(child_layout)


def showPilImage(pil_image: Image.Image, showLabel, scale=1):
    """
    核心：将PIL.Image转换为QPixmap并展示到QLabel
    :param pil_image: adbutils返回的PIL.Image对象
    """
    if pil_image is None:
        return
    rgb_image = pil_image.convert("RGB")
    width, height = rgb_image.size
    image_bytes = rgb_image.tobytes()
    q_image = QImage(image_bytes, width, height, width * 3, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(q_image)
    scaled_pixmap = pixmap.scaled(showLabel.size() * scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    showLabel.setPixmap(scaled_pixmap)
