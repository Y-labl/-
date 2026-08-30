# -*- coding: utf-8 -*-
"""
场景 -> 偷窃/技能目标映射系统
基于 DKChangJingThread.pyc 字节码还原
"""

SCENE_MAPPING = {
    "龙窟五层": {
        "tou_targets": ["PK-召唤兽-蛟龙", "PK-召唤兽-蛟龙2", "PK-召唤兽-蛟龙3", "PK-召唤兽-蛟龙4"],
        "jineng_targets": ["PK-召唤兽-地狱战神", "PK-召唤兽-地狱战神2",
                           "PK-召唤兽-蛟龙", "PK-召唤兽-蛟龙2",
                           "PK-召唤兽-蛟龙3", "PK-召唤兽-蛟龙4",
                           "PK-召唤兽-变异地狱战神", "PK-召唤兽-变异蛟龙"],
        "map_click": {"x1": 87, "y1": 96, "x2": 609, "y2": 351},
        "support_type": "support",
    },
    "龙窟六层": {
        "tou_targets": ["PK-召唤兽-巡游天神", "PK-召唤兽-雨师"],
        "jineng_targets": ["PK-召唤兽-巡游天神", "PK-召唤兽-雨师"],
        "map_click": {"x1": 120, "y1": 20, "x2": 380, "y2": 450},
        "support_type": "support",
    },
    "凤巢三层": {
        "tou_targets": ["PK-召唤兽-凤凰", "PK-召唤兽-天将", "PK-召唤兽-金翼"],
        "jineng_targets": ["PK-召唤兽-天将", "PK-召唤兽-金翼", "PK-召唤兽-凤凰"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    "凤巢四层": {
        "tou_targets": ["PK-召唤兽-凤凰", "PK-召唤兽-天将", "PK-召唤兽-金翼"],
        "jineng_targets": ["PK-召唤兽-天将", "PK-召唤兽-金翼", "PK-召唤兽-凤凰"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    "凤巢五层": {
        "tou_targets": ["PK-召唤兽-凤凰", "PK-召唤兽-天将", "PK-召唤兽-金翼"],
        "jineng_targets": ["PK-召唤兽-凤凰", "PK-召唤兽-天将", "PK-召唤兽-金翼"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    "小西天": {
        "tou_targets": ["PK-召唤兽-炎魔神"],
        "jineng_targets": ["PK-召唤兽-金饶僧", "PK-召唤兽-噬天虎", "PK-召唤兽-炎魔神", "PK-召唤兽-夜罗刹"],
        "map_click": {"x1": 212, "y1": 21, "x2": 475, "y2": 415},
        "support_type": "support",
    },
    "子母河底": {
        "tou_targets": ["PK-召唤兽-鲛人", "PK-召唤兽-碧水夜叉", "PK-召唤兽-蚌精"],
        "jineng_targets": ["PK-召唤兽-鲛人", "PK-召唤兽-碧水夜叉", "PK-召唤兽-蚌精"],
        "map_click": {"x1": 150, "y1": 70, "x2": 535, "y2": 363},
        "support_type": "support",
    },
    "麒麟山": {
        "tou_targets": ["PK-召唤兽-鼠先锋", "PK-召唤兽-百足将军",
                        "PK-召唤兽-野猪精", "PK-召唤兽-镜妖", "PK-召唤兽-泪妖"],
        "jineng_targets": ["PK-召唤兽-鼠先锋", "PK-召唤兽-百足将军",
                           "PK-召唤兽-野猪精", "PK-召唤兽-镜妖", "PK-召唤兽-泪妖"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    "女娲神迹": {
        "tou_targets": ["PK-召唤兽-灵符女娲"],
        "jineng_targets": ["PK-召唤兽-律法女娲", "PK-召唤兽-灵符女娲", "PK-召唤兽-缘劫女娲"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
}


RESERVED_SCENES = [
    "长安城", "大唐国境", "大唐境外", "大唐官府", "长寿村",
    "长寿郊外", "傲来国", "花果山", "东海湾", "东海渊",
    "建邺城", "江南野外", "朱紫国", "宝象国", "西梁女国",
    "芙蓉国", "魔王寨", "狮驼岭", "神木林", "化生寺",
    "方寸山", "五庄观", "普陀山", "盘丝岭", "地府",
    "鬼市", "龙窟一层", "北俱芦洲", "墨家村", "天机城",
    "九黎城", "凌波城", "无底洞", "碗子山", "解阳山",
    "战神山", "女魃墓", "女儿村", "五行山", "伊阙龙门",
    "长安酒店", "蓬莱仙岛", "丝绸之路", "万界通廊", "幻境花果山",
]


def get_tou_targets(area):
    mapping = SCENE_MAPPING.get(area)
    return mapping["tou_targets"] if mapping else None


def get_jineng_targets(area):
    mapping = SCENE_MAPPING.get(area)
    return mapping["jineng_targets"] if mapping else None


def get_all_monsters(area):
    mapping = SCENE_MAPPING.get(area)
    if not mapping:
        return []
    seen = set()
    result = []
    for name in mapping["tou_targets"] + mapping["jineng_targets"]:
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def get_map_click_area(area):
    mapping = SCENE_MAPPING.get(area)
    return mapping["map_click"] if mapping else {"x1": 212, "y1": 21, "x2": 475, "y2": 415}


def is_supported_scene(area):
    mapping = SCENE_MAPPING.get(area)
    return mapping is not None and mapping.get("support_type") == "support"


def list_supported_scenes():
    return [k for k, v in SCENE_MAPPING.items() if v.get("support_type") == "support"]


def list_all_known_scenes():
    return list(SCENE_MAPPING.keys()) + RESERVED_SCENES


def get_tou_target_image_names(area):
    targets = get_tou_targets(area)
    if targets is None:
        return None
    return [targets]


def get_jineng_target_image_names(area):
    targets = get_jineng_targets(area)
    if targets is None:
        return None
    return [targets]
