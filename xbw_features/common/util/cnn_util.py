# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: common\util\cnn_util.py
import random, time
from xbw_features.qtcompat import QPoint
from loguru import logger
from xbw_features.common.util.click_util import click
from xbw_features.common.util.file_util import cv_save_img
from xbw_features.common.util.img_util import findFourPersonAndClick, isShowFourPerson
from xbw_features.common.util.log_util import logTmpPath, orderLog
from xbw_features.common.util.time_util import getLogTime, getLogTimeHour
from xbw_features.cw_changjing.cw_changjing_util import findFourPersonDetectArea
from xbw_features.four_person.detector import CONF_THRESHOLD, SingleImageDetector
from xbw_features.common.util.scrcpy_util import scrcpyUtil

class CNNUtil(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = (object.__new__)(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.detector = SingleImageDetector()

    def _score_roi(self, frame, left, top, width, height):
        """对 ROI 的 4 个 90 宽槽位做 CNN 打分，返回 (槽位列表, 最佳槽位, 最佳概率)。"""
        indexProbs = []
        for i in range(4):
            itemLeft = left + 90 * i
            itemRoi = frame[top:top + height, itemLeft:itemLeft + 90]
            prob = self.detector.predict_img(itemRoi)
            indexProbs.append((i, prob))
        best_index, best_prob = max(indexProbs, key=lambda x: x[1])
        return indexProbs, best_index, best_prob

    def findFourPersonLocal(self, deviceId, left=227, top=80, width=360, height=150, curFrame=None):
        frame = None
        if curFrame is not None:
            frame = curFrame
        else:
            frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            orderLog(deviceId, "本地识别四小人：获取画面失败")
            return
        # 多候选 ROI：默认标准区域(227,80,360,150) 与检测区域都试一遍，
        # 取最高分那一组，避免 findFourPersonDetectArea 的“在/请”字定位
        # 与真实头像错位导致点击落空（实测错位时默认区域仍可到 1.000）。
        candidates = [
            (227, 80, 360, 150),
            (left, top, width, height),
        ]
        seen = set()
        best_score = None      # (prob, index, roi)
        best_indexProbs = None
        for l, t, w, h in candidates:
            if (l, t, w, h) in seen:
                continue
            seen.add((l, t, w, h))
            try:
                indexProbs, b_idx, b_prob = self._score_roi(frame, l, t, w, h)
            except Exception as e:
                logger.debug(f"ROI({l},{t},{w},{h}) 打分异常: {e}")
                continue
            if best_score is None or b_prob > best_score[0]:
                best_score = (b_prob, b_idx, (l, t, w, h))
                best_indexProbs = indexProbs
        if best_score is None:
            orderLog(deviceId, "本地识别四小人：候选 ROI 均无效")
            return
        best_prob, best_index, (left, top, width, height) = best_score
        cv_save_img(f"{logTmpPath()}/{getLogTimeHour()}/{deviceId}-{getLogTime()}-FourPerson-LocalOrig.png", frame)
        for i, prob in best_indexProbs:
            itemLeft = left + 90 * i
            itemRoi = frame[top:top + height, itemLeft:itemLeft + 90]
            if prob > 0.8:
                cv_save_img(f"{logTmpPath()}/{getLogTimeHour()}/front/{deviceId}-{getLogTime()}-FourPerson-Local-Item{i}-Similar-{prob:.4f}.png", itemRoi)
            elif prob > 0.4:
                cv_save_img(f"{logTmpPath()}/{getLogTimeHour()}/notsure/{deviceId}-{getLogTime()}-FourPerson-Local-Item{i}-Similar-{prob:.4f}.png", itemRoi)
            else:
                cv_save_img(f"{logTmpPath()}/{getLogTimeHour()}/back/{deviceId}-{getLogTime()}-FourPerson-Local-Item{i}-Similar-{prob:.4f}.png", itemRoi)
        if best_prob > CONF_THRESHOLD:
            clickPoint = QPoint(left + 90 * best_index + 45, top + height // 2)
            click(deviceId, clickPoint)
            orderLog(deviceId, f"本地识别四小人目标：{best_index} ,置信度 {best_prob:.4f}, ROI({left},{top},{width},{height}), 点击坐标 {clickPoint}")
            time.sleep(random.uniform(1, 1.5))
        else:
            orderLog(deviceId, f"本地识别四小人最高置信度{best_prob:.4f}不足阈值(0.8)")
            # 网络兜底仅在“疑似但未达阈值”(0.4~0.8) 时触发；
            # 点击成功（>0.8）说明界面已处理，无需再走网络判定。
            if best_prob >= 0.4:
                if isShowFourPerson(deviceId):
                    d_left, d_top, d_width, d_height = findFourPersonDetectArea(deviceId)
                    if d_left != 0:
                        orderLog(deviceId, "网络-四小人识别区域227,80,360,150")
                        findFourPersonAndClick(deviceId)
                    else:
                        orderLog(deviceId, "网络-未找到四小人识别区域")
                else:
                    orderLog(deviceId, "本地疑似四小人，但严格判定为非四小人界面")
            else:
                orderLog(deviceId, "本地判定非四小人界面（置信度过低），跳过网络识别")


cnnUtil = CNNUtil()
