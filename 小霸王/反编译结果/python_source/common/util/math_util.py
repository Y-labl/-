# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\math_util.py
import hashlib, re, socket
from typing import Optional
import numpy as np
from PyQt5.QtCore import QPoint
from loguru import logger
from numpy import double
from common.util.scrcpy_util import scrcpyUtil

def distance_between_points(point1: QPoint, point2: QPoint) -> float:
    dx = point2.x() - point1.x()
    dy = point2.y() - point1.y()
    return (dx ** 2 + dy ** 2) ** 0.5


title = "sgIHJ7UMUlRVnDTI4CrenxLsaqqTskLhFXlOLKGQTxMz"

def plusReduce(data):
    output = ""
    j = 0
    for i in range(len(data)):
        output += chr(ord(data[i]) ^ ord(title[j]))
        j = (j + 1) % len(title)
    else:
        return output


def isframeSame(frame1: Optional[np.ndarray], frame2: Optional[np.ndarray], similar: float=0.95) -> bool:
    if frame1 is None or frame2 is None:
        return False
    if frame1.shape != frame2.shape:
        return False
    ssim_value = calculate_ssim(frame1, frame2)
    return ssim_value >= similar


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    计算结构相似性 SSIM（专门适配界面图像、ADB 投屏）
    :param img1: np.ndarray 格式图像（必填，不能为 None）
    :param img2: np.ndarray 格式图像（必填，不能为 None）
    :return: 0~1 之间的相似度，1 为完全相同
    """
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mu1 = img1.mean()
    mu2 = img2.mean()
    sigma1 = np.mean((img1 - mu1) ** 2)
    sigma2 = np.mean((img2 - mu2) ** 2)
    sigma12 = np.mean((img1 - mu1) * (img2 - mu2))
    C1 = 6.502500000000001
    C2 = 58.522499999999994
    ssim = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2) / ((mu1 ** 2 + mu2 ** 2 + C1) * (sigma1 + sigma2 + C2))
    return float(ssim)


def calculate_per_color(deviceId, left, top, width, height):
    frame = scrcpyUtil.getFrame(deviceId)
    roi = frame[(top[:top + height], left[:left + width])]
    b, g, r = np.mean(roi, axis=(0, 1))
    return (r, g, b)


def getPerBi(typeName):
    match = re.search("(\\d+\\.?\\d*)币", typeName)
    if match:
        return float(match.group(1))
    return 0.0


def isSameBi(typeName1, typeName2):
    coin1 = re.findall("(\\d+)币", typeName1)
    coin2 = re.findall("(\\d+)币", typeName2)
    return coin1 == coin2
