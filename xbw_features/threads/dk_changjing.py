# -*- coding: utf-8 -*-
"""
行囊环/卡计数 + 切场条件

由反编译 threads/dk_changjing_thread.py 的 startDuiZhang“偷偷检查背包”段
提炼为纯函数（去掉 QThread 依赖，I/O 走 xbw_features.backend）：

1. 每 550~700 秒（或首次）打开背包；
2. getHasProductPoints 按 20 格（5x4）网格 + 对角线取色判断占用；
3. 与上次快照 get_diff_points 求新增槽位；
4. 逐个点击新物品，模板匹配“装备条件”（环）/“怪物卡片”（卡）累计计数；
5. 达到 changeHuanCount / changeCardCount（或时间满）即触发切换场。
"""

import random
import re
import time

from xbw_features.qtcompat import QPoint
from xbw_features.common.util.log_util import orderLog
from xbw_features.common.util.color_util import PKG_CENTER_CUR_PKG, getHasProductPoints
from xbw_features.common.util.math_util import get_diff_points
from xbw_features.common.util.img_util import checkAtDaoJu, findPic
from xbw_features.common.util.click_util import click
from xbw_features.common.util.scrcpy_util import scrcpyUtil
from xbw_features.common.util.detect_position_util import detectPosition
from xbw_features.game_action.unit.common_unit import (
    clickOpenPkg,
    clickClosePkg,
    doubleClickProduct,
    closePop,
)
from xbw_features.game_action.map_action import dianXiangAreas, goToMapAction

# 与原版 random.uniform(550, 700) 一致的检查间隔范围（秒）
PKG_CHECK_INTERVAL = (550, 700)


def parse_require(text):
    """
    解析配置文本：
      "得3个环" -> 3, "得2张卡片" -> 2, "满180分钟" -> 180
      "无要求"/None/空 -> None（不触发）
    """
    if text is None:
        return None
    text = str(text).strip()
    if not text or text in ("无要求", "无", "不限"):
        return None
    m = re.search(r"\d+", text)
    if m:
        return int(m.group(0))
    return None


def next_check_interval():
    """返回下次检查背包的随机间隔（秒），与原版 550~700 一致。"""
    return random.uniform(*PKG_CHECK_INTERVAL)


def check_backpack(deviceId, prev_snapshot=None, stop_event=None):
    """
    打开背包 -> 取 20 格占用快照 -> 与上次快照 diff 出新增槽位 ->
    逐个点击并模板匹配“装备条件/怪物卡片”，返回环/卡数量、位置与背包截图。

    :return: dict(snapshot, add_huan, add_card, ring_points, card_points, bag_frame)
    """
    def stopped():
        return stop_event is not None and stop_event.is_set()

    orderLog(deviceId, "偷偷检查背包")
    clickOpenPkg(deviceId)
    bag_frame = None
    try:
        bag_frame = scrcpyUtil.getFrame(deviceId)
        tmp_products = getHasProductPoints(deviceId, firstCenterPoint=PKG_CENTER_CUR_PKG)
        add_huan = 0
        add_card = 0
        ring_points = []
        card_points = []
        if prev_snapshot:
            add_points = get_diff_points(prev_snapshot, tmp_products)
            for add_p in add_points:
                if stopped():
                    break
                click(deviceId, add_p)
                time.sleep(random.uniform(1.5, 2.8))
                if findPic(deviceId, "装备条件", width=400):
                    add_huan += 1
                    ring_points.append((add_p.x(), add_p.y()))
                if findPic(deviceId, "怪物卡片", width=400):
                    add_card += 1
                    card_points.append((add_p.x(), add_p.y()))
        return {
            "snapshot": tmp_products,
            "add_huan": add_huan,
            "add_card": add_card,
            "ring_points": ring_points,
            "card_points": card_points,
            "bag_frame": bag_frame,
        }
    finally:
        if not stopped():
            clickClosePkg(deviceId)


def should_switch_scene(rings_require, cards_require, huan_count, card_count):
    """环/卡计数达标即切场；要求为 None（无要求）时不触发。"""
    r_req = parse_require(rings_require)
    c_req = parse_require(cards_require)
    if r_req is not None and huan_count >= r_req:
        return True
    if c_req is not None and card_count >= c_req:
        return True
    return False


def check_backpack_and_maybe_switch(deviceId, rings_require, cards_require,
                                    huan_count, card_count, prev_snapshot=None,
                                    stop_event=None):
    """
    检查一次背包并累计环/卡计数；达标时返回 reason。

    :return: (新快照, 累计环数, 累计卡数, reason 或 None)
    """
    result = check_backpack(deviceId, prev_snapshot, stop_event=stop_event)
    huan_count += result["add_huan"]
    card_count += result["add_card"]
    reason = None
    if should_switch_scene(rings_require, cards_require, huan_count, card_count):
        reason = "环/卡达标"
    return result["snapshot"], huan_count, card_count, reason


def go_to_chang_jing(deviceId, target_area):
    """
    去目标场景（对应反编译 goToChangJing）：
    点卡服区域先摄妖香 -> goToMapAction 导航 -> 到达后点卡区域再洞冥草。
    """
    orderLog(deviceId, f"去场景:{target_area}")
    closePop(deviceId)
    area, x, y = detectPosition(deviceId)
    if area != target_area:
        if target_area in dianXiangAreas:
            clickOpenPkg(deviceId)
            doubleClickProduct(deviceId, preImgName="摄妖香",
                               preFunc=lambda: checkAtDaoJu(deviceId))
            clickClosePkg(deviceId)
        orderLog(deviceId, f"去地图:{area}")
        goToMapAction(deviceId, target_area)
        if target_area in dianXiangAreas:
            clickOpenPkg(deviceId)
            doubleClickProduct(deviceId, preImgName="洞冥草",
                               preFunc=lambda: checkAtDaoJu(deviceId))
            clickClosePkg(deviceId)
    return area
