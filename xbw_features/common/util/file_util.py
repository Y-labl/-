# -*- coding: utf-8 -*-
# 反编译 file_util.py 适配版：去掉 QFileDialog（GUI 选择另由本工程处理）。

import os

from loguru import logger
from xbw_features.common.util.time_util import getLogTime
import cv2


def selectPngPath(self):
    return None


def cv_save_img(path, frame):
    try:
        dir_path = os.path.dirname(path)
        if dir_path:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        suffix = path.split(".")[-1]
        cv2.imencode(f".{suffix}", frame)[1].tofile(path)
    except Exception as e:
        try:
            logger.debug(f"cv_save_img异常: {e}")
        finally:
            e = None
            del e
