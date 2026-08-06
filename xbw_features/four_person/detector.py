# -*- coding: utf-8 -*-
# 反编译 four_person/detector.py 适配版：
# 原实现按 sys.executable 所在目录逐层拼接模型路径，合并后直接读
# const.FOURPERSON_CNN_PATH（本包 _internal/subor.onnx）。

import os
from pathlib import Path
import sys
import uuid

import cv2
import numpy as np
import onnxruntime as ort

from xbw_features.common.util.log_util import logUtil
from xbw_features.const import FOURPERSON_CNN_PATH

IMG_TARGET_SIZE = 90
CONF_THRESHOLD = 0.8
MEAN = np.array([0.5, 0.5, 0.5], dtype=(np.float32))
STD = np.array([0.5, 0.5, 0.5], dtype=(np.float32))


def resize_and_pad_cv2(img_bgr, target_size=90):
    h, w = img_bgr.shape[:2]
    scale = target_size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    img_res = cv2.resize(img_bgr, (new_w, new_h), interpolation=(cv2.INTER_AREA))
    pad_l = (target_size - new_w) // 2
    pad_r = target_size - new_w - pad_l
    pad_t = (target_size - new_h) // 2
    pad_b = target_size - new_h - pad_t
    img_pad = cv2.copyMakeBorder(img_res,
                                 pad_t, pad_b, pad_l, pad_r,
                                 (cv2.BORDER_CONSTANT), value=[0, 0, 0])
    return img_pad


class SingleImageDetector(object):

    def __init__(self, model_path=None):
        opt = ort.SessionOptions()
        opt.intra_op_num_threads = 1
        opt.inter_op_num_threads = 1
        opt.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.model_path = model_path or FOURPERSON_CNN_PATH
        self.session = ort.InferenceSession(
            self.model_path,
            sess_options=opt,
            providers=["CPUExecutionProvider"])
        self.in_name = self.session.get_inputs()[0].name
        self.out_name = self.session.get_outputs()[0].name

    def predict_img(self, img_bgr):
        """
        :param img_bgr: cv2读取的单人图片（你场景下尺寸90×100）
        :return: float 0~1 正面概率
        """
        img = resize_and_pad_cv2(img_bgr, IMG_TARGET_SIZE)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_rgb = img_rgb.astype(np.float32) / 255.0
        img_rgb = (img_rgb - MEAN) / STD
        tensor = np.transpose(img_rgb, (2, 0, 1))
        tensor = np.expand_dims(tensor, axis=0).astype(np.float32)
        res = self.session.run([self.out_name], {self.in_name: tensor})
        prob = float(res[0][0][0])
        return prob


if __name__ == "__main__":
    detector = SingleImageDetector()
    folder_path = "./four_person/test/test1"
    png_files = list(Path(folder_path).glob("*.png")) + list(Path(folder_path).glob("*.PNG"))
    detectInputImgPaths = []
    for file in png_files:
        filePath = str(file)
        detectInputImgPaths.append(filePath)
    result_list = []
    for path in detectInputImgPaths:
        img = cv2.imread(path)
        prob = detector.predict_img(img)
        result_list.append((path, prob))
        print(f"{path} 正面概率: {prob:.4f}")
        new_path = os.path.join(folder_path, f"{uuid.uuid4()}_{prob:.4f}.png")
        os.rename(path, new_path)
    best_item = max(result_list, key=(lambda x: x[1]))
    best_path, best_prob = best_item
    if best_prob > CONF_THRESHOLD:
        print(f"\n目标：{best_path} ,置信度 {best_prob:.4f}")
    else:
        print("最高置信度不足阈值，放弃")
