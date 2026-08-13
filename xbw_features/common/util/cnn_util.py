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

    def _find_avatar_row(self, frame, top, height):
        """
        在 top 附近多行横向扫描 90 宽槽位，找最长连续高分(>0.5)段。
        真四小人界面头像成排 -> 连续段 >=3 个（约 90px+ 宽）；
        普通场景的孤立高分点是散的，构不成连续段。
        多行扫描兼容各设备头像行 y 偏移（如 18:08 在 y≈100~120，
        而最佳 ROI 的 top=80 那一行只有 2 个连续点）。
        :return: 连续段的中心 x（点击用）或 None
        """
        if frame is None:
            return None
        best_run = []
        for dy in range(-40, 81, 20):
            t = top + dy
            if t < 0 or t + height > 448:
                continue
            run = []
            for x0 in range(60, 700, 30):
                crop = frame[t:t + height, x0:x0 + 90]
                if crop.shape != (height, 90, 3):
                    continue
                prob = self.detector.predict_img(crop)
                if prob > 0.5:
                    run.append(x0)
                else:
                    if len(run) > len(best_run):
                        best_run = run
                    run = []
            if len(run) > len(best_run):
                best_run = run
        if len(best_run) >= 3:
            return best_run[0] + (best_run[-1] - best_run[0]) / 2 + 45
        return None

    def findFourPersonLocal(self, deviceId, left=None, top=None, width=None, height=None, curFrame=None, conf_threshold=None):
        """本地四小人：与功能测试页一致——截图后“在/请”定位 + 多候选 ROI 打分。

        入口判定由调用方 _is_show_four_person 负责。流程同测试页：
        findFourPersonDetectArea 定位（找不到回退默认区域）-> best_four_person_roi
        多候选打分（默认 + 在/请区域 + y 扫描）-> 最高分槽位。
        置信度必须 >=conf_threshold（默认 0.8）才点击（CNN 没认出弹窗绝不盲点，
        避免点错被系统踢下线），点 50% 高度，没关掉下移 55% 再点一次；仍不行返回 False，
        由调用方按 8.5 前图灵方式兜底。返回 True=本地点击成功，False=本地未成功。
        conf_threshold：图灵云不可用（如账户余额不足）时，调用方可传入更低阈值
        （如 0.5）再试一次；点击后仍有 predict>0.5 验证兜底，不会盲点连点。
        """
        frame = None
        if curFrame is not None:
            frame = curFrame
        else:
            frame = scrcpyUtil.getFrame(deviceId)
        if frame is None:
            orderLog(deviceId, "本地识别四小人：获取画面失败")
            return False
        # 1) 识别区域：优先用调用方传入的“在/请”定位；否则在本帧重新定位（同测试页）
        if left and top and width and height:
            det_roi = (left, top, width, height)
        else:
            det_roi = findFourPersonDetectArea(deviceId, curframe=frame)
            if not (det_roi and det_roi[0] != 0):
                det_roi = (227, 80, 360, 150)
        # 2) 多候选 ROI 打分（与测试页 best_four_person_roi 一致：默认 + 在/请区域 + y 扫描）
        best_roi, best_index, best_prob, _ = self.best_four_person_roi(
            frame, det_roi[0], det_roi[1], det_roi[2], det_roi[3])
        if best_roi is None:
            orderLog(deviceId, "本地识别四小人：候选 ROI 均无效，交给图灵验证")
            return False
        left, top, width, height = best_roi
        # 先保存原图（含 _is_show_four_person 误判的普通画面），便于排查
        _ts = time.strftime("%Y%m%d%H%M%S")
        cv_save_img(f"{logTmpPath()}/{_ts}_{deviceId}_FourPerson.png", frame)
        # 置信度门槛：CNN 没认出弹窗（如 _is_show_four_person 误判的普通画面）
        # 绝不点击，避免连续点错被系统强制掉线；交给 8.5 前图灵验证
        thr = conf_threshold if conf_threshold is not None else CONF_THRESHOLD
        if best_prob < thr:
            orderLog(deviceId, f"本地识别四小人最高置信度{best_prob:.4f}不足阈值({thr})，不点击，交给图灵验证")
            return False
        # 仅确认是四小人界面后才保存最佳槽位截图
        _best_crop = frame[top:top + height, left + 90 * best_index:left + 90 * best_index + 90]
        cv_save_img(f"{logTmpPath()}/{_ts}_{deviceId}_FourPerson_Slot{best_index}.png", _best_crop)
        # 点击识别到的槽位 50% 高度；没关掉就下移到 55% 高度再点一次，仍不行才图灵兜底
        for ratio in (0.5, 0.55):
            clickPoint = QPoint(left + 90 * best_index + 45, top + int(height * ratio))
            click(deviceId, clickPoint)
            orderLog(deviceId, f"本地识别四小人目标：槽{best_index} ,置信度 {best_prob:.4f}, ROI({left},{top},{width},{height}), 点击坐标 {clickPoint}")
            time.sleep(random.uniform(1, 1.5))
            # 点击后验证：四小人界面还在才继续下一次/图灵兜底
            still = False
            try:
                frame2 = scrcpyUtil.getFrame(deviceId)
                if frame2 is not None:
                    for i in range(4):
                        itemLeft = left + 90 * i
                        itemRoi = frame2[top:top + height, itemLeft:itemLeft + 90]
                        if itemRoi.shape != (height, 90, 3):
                            continue
                        if self.detector.predict_img(itemRoi) > 0.5:
                            still = True
                            break
            except Exception as e:
                logger.debug(f"点击后验证异常: {e}")
            if still:
                cv_save_img(f"{logTmpPath()}/{_ts}_{deviceId}_FourPerson_AfterClick.png", frame2)
                orderLog(deviceId, f"点击后四小人仍在（{ratio:.0%}高度），继续处理")
                continue
            orderLog(deviceId, f"点击后四小人已消失（{ratio:.0%}高度），处理完成")
            return True
        # 两次本地点击后弹窗仍在 -> 由调用方走 8.5 前图灵处理
        orderLog(deviceId, "本地点击两次后四小人仍在")
        return False


cnnUtil = CNNUtil()
