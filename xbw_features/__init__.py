# -*- coding: utf-8 -*-
"""
小霸王三功能合并包（反编译代码整理后并入 mhxy-auto-fight 工程）

功能 1  本地四小人识别：four_person.detector + common.util.cnn_util
        （ONNX CNN，subor.onnx，90x90 输入，概率>0.8 点击最高槽位，
          失败降级图灵云 API）
功能 2  切换场：game_action.map_action（goToMapAction 区域分支 +
        67 点卡 / 7 畅玩地图参数 + 飞行符/飞行旗/驿站/NPC 对话链）
功能 3  行囊环/卡计数：threads.dk_changjing（20 格 5x4 网格 + 对角线取色
        diff 新增槽位 -> 模板匹配“装备条件/怪物卡片”累计 -> 达标切场）

I/O 说明：所有截图 / 点击 / 日志都经过 backend.py；引擎集成时调用
`xbw_features.backend.setup(...)` 注入自己的实现，否则回退到 ADB。
"""

from xbw_features import const, backend
from xbw_features.qtcompat import QPoint, QColor

# ---- 功能 1：四小人 ----
from xbw_features.four_person.detector import SingleImageDetector, CONF_THRESHOLD, IMG_TARGET_SIZE
from xbw_features.common.util.cnn_util import cnnUtil, CNNUtil
from xbw_features.common.util.img_util import (
    isShowFourPerson,
    findFourPersonAndClick,
    findPic,
    findPics,
    checkAtDaoJu,
)
from xbw_features.cw_changjing.cw_changjing_util import findFourPersonDetectArea

# ---- 功能 2：切换场 ----
from xbw_features.game_action.map_action import (
    goToMapAction,
    goToPositionAction,
    getMapParams,
    AreaParams,
    dianXiangAreas,
    resetDeviceSaiXuanMap,
)
from xbw_features.common.util.detect_position_util import detectPosition

# ---- 功能 3：行囊环/卡计数 + 切场条件 ----
from xbw_features.threads.dk_changjing import (
    check_backpack,
    parse_require,
    should_switch_scene,
    go_to_chang_jing,
    check_backpack_and_maybe_switch,
    next_check_interval,
)

__all__ = [
    "const", "backend", "QPoint", "QColor",
    "SingleImageDetector", "cnnUtil", "CNNUtil",
    "isShowFourPerson", "findFourPersonAndClick", "findPic", "findPics", "checkAtDaoJu",
    "findFourPersonDetectArea",
    "goToMapAction", "goToPositionAction", "getMapParams", "AreaParams",
    "dianXiangAreas", "resetDeviceSaiXuanMap", "detectPosition",
    "check_backpack", "parse_require", "should_switch_scene", "go_to_chang_jing",
    "check_backpack_and_maybe_switch", "next_check_interval",
]
