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

    def best_four_person_roi(self, frame, left, top, width, height):
        """
        多候选 ROI 打分取最高：
          - 默认标准区域 (227,80,360,150)
          - 检测区域 (left,top,width,height)
          - 检测区域 y 方向 -50 ~ +20 扫描（“请/在”字定位与真实头像行
            在不同设备/界面下存在 20~50px 偏差，固定 ROI 会裁到头像外）
        :return: (roi, best_index, best_prob, indexProbs) 或 (None,None,None,None)
        """
        candidates = [
            (227, 80, 360, 150),
            (left, top, width, height),
        ]
        for dy in range(-50, 21, 10):
            candidates.append((left, top + dy, width, height))
        seen = set()
        best_score = None
        best_indexProbs = None
        for l, t, w, h in candidates:
            if (l, t, w, h) in seen or l < 0 or t < 0 or l + w > 800 or t + h > 448:
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
            return None, None, None, None
        best_prob, best_index, best_roi = best_score
        return best_roi, best_index, best_prob, best_indexProbs

    def findFourPersonLocal(self, deviceId, left=227, top=80, width=360, height=150, curFrame=None):
        frame = None
        if curFrame is not None:
            frame = curFrame
        else:
            frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            orderLog(deviceId, "本地识别四小人：获取画面失败")
            return
        # “在/请”字检测区域可能返回 (0,0,0,0)，此时回退默认标准区域，
        # 与功能测试页签行为一致（默认区域 + y 扫描仍可识别）。
        if left <= 0 or top <= 0 or width <= 0 or height <= 0:
            left, top, width, height = 227, 80, 360, 150
        best_roi, best_index, best_prob, best_indexProbs = self.best_four_person_roi(
            frame, left, top, width, height)
        if best_roi is None:
            orderLog(deviceId, "本地识别四小人：候选 ROI 均无效")
            return
        left, top, width, height = best_roi
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
        if best_prob < 0.4:
            orderLog(deviceId, "本地判定非四小人界面（置信度过低），跳过")
            return
        # ===== 界面判定（点击与图灵兜底共用） =====
        # 严格判定（头像/好友入口/撤销）确认是四小人界面 -> 直接放行；
        # 严格判否时（部分真界面变体也判否），需要强证据才放行：
        #   最佳槽位 > 0.9 且 >=2 个槽位 >0.4 且画面为暗色面板（亮度 <70）。
        # 实测：真界面 22:28/18:08 放行；普通场景 23:11~23:17 全部拦截。
        try:
            _ui_confirmed = bool(isShowFourPerson(deviceId))
        except Exception:
            _ui_confirmed = True
        _slots04 = sum(1 for _, pr in best_indexProbs if pr > 0.4)
        _bright = float(frame.mean()) if frame is not None else 255.0
        if not _ui_confirmed and (best_prob < 0.9 or _slots04 < 2 or _bright >= 70):
            orderLog(deviceId,
                     f"严格判定非四小人且证据不足(best={best_prob:.3f} >0.4槽={_slots04} "
                     f"亮度={_bright:.0f})，跳过点击与图灵")
            return
        if best_prob > CONF_THRESHOLD:
            # 点击点取槽位高度 65% 处：部分 NPC 较矮，中心点击可能落空
            clickPoint = QPoint(left + 90 * best_index + 45, top + int(height * 0.65))
            click(deviceId, clickPoint)
            orderLog(deviceId, f"本地识别四小人目标：{best_index} ,置信度 {best_prob:.4f}, ROI({left},{top},{width},{height}), 点击坐标 {clickPoint}")
            time.sleep(random.uniform(1, 1.5))
        else:
            # 疑似但本地未达阈值(0.4~0.8) -> 图灵云兜底
            orderLog(deviceId, f"本地识别四小人最高置信度{best_prob:.4f}不足阈值(0.8)，调用图灵云识别")
            findFourPersonAndClick(deviceId)


cnnUtil = CNNUtil()
