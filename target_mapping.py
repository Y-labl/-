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
        "map_click": {"x1": 128, "y1": 100, "x2": 562, "y2": 342},
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
    "小雷音寺": {
        # 小雷音寺怪物：灵鹤、雾中仙、大力金刚；只对灵鹤偷卡。
        "tou_targets": ["PK-召唤兽-灵鹤"],
        "jineng_targets": ["PK-召唤兽-灵鹤", "PK-召唤兽-雾中仙", "PK-召唤兽-大力金刚"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
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
    # ===== 特殊场景（队伍抓特殊，参考小霸王逆向）=====
    # 须弥东界: 真陀护法、毗舍童子、持国巡守（含变异）；妙手空空只偷 毗舍童子/变异毗舍童子。
    "须弥东界": {
        "tou_targets": ["PK-召唤兽-毗舍童子"],
        "jineng_targets": ["PK-召唤兽-真陀护法", "PK-召唤兽-毗舍童子", "PK-召唤兽-持国巡守"],
        # 跑图点击范围（800x448 流坐标）：x=239,y=36,w=209,h=370
        "map_click": {"x1": 239, "y1": 36, "x2": 448, "y2": 406},
        "support_type": "support",
    },
    # 银华境（游戏内 OCR 场景名为“银华境”，特殊面板习惯写作“银华镜”，见 SCENE_ALIASES）：
    # 真陀护法、毗舍童子、广目巡守（含变异）；妙手空空只偷 毗舍童子/变异毗舍童子。
    "银华境": {
        "tou_targets": ["PK-召唤兽-毗舍童子"],
        "jineng_targets": ["PK-召唤兽-真陀护法", "PK-召唤兽-毗舍童子", "PK-召唤兽-广目巡守"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    # 弥勒山: 九色鹿、翼马(一)、芙蓉仙子、涂山瞳(一~三)；妙手空空回退到全部模板。
    "弥勒山": {
        "tou_targets": ["PK-召唤兽-九色鹿", "PK-召唤兽-翼马", "PK-召唤兽-芙蓉仙子", "PK-召唤兽-涂山瞳"],
        "jineng_targets": ["PK-召唤兽-九色鹿", "PK-召唤兽-翼马", "PK-召唤兽-芙蓉仙子", "PK-召唤兽-涂山瞳"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    # 丝绸之路: 逆向文档称不支持自动换场景（随机点地图巡逻），无固定的“放大镜”怪物表，
    # 故偷卡/技能目标留空（引擎允许“仅捕捉模式”），队伍队长仍可按对面“宝宝”文字捕捉。
    "丝绸之路": {
        "tou_targets": [],
        "jineng_targets": [],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    # 伊阙龙门（抓特殊）：灵鹤、巡游天神(一、二)、雾中仙、多闻巡守（含变异）。
    # 特殊高价值 = 多闻巡守（“巡守”关键字）。妙手空空目标 = 灵鹤/变异灵鹤。
    "伊阙龙门": {
        "tou_targets": ["PK-召唤兽-灵鹤", "PK-召唤兽-多闻巡守"],
        "jineng_targets": ["PK-召唤兽-灵鹤", "PK-召唤兽-巡游天神", "PK-召唤兽-多闻巡守", "PK-召唤兽-雾中仙"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    # 无名鬼域（抓特殊）：吸血鬼、幽灵(一、二)、画魂、鬼将（含变异）。
    # 特殊高价值 = 画魂 / 鬼将。妙手空空目标 = 幽灵/变异幽灵。
    "无名鬼域": {
        "tou_targets": ["PK-召唤兽-幽灵", "PK-召唤兽-画魂", "PK-召唤兽-鬼将"],
        "jineng_targets": ["PK-召唤兽-吸血鬼", "PK-召唤兽-幽灵", "PK-召唤兽-画魂", "PK-召唤兽-鬼将"],
        "map_click": {"x1": 180, "y1": 220, "x2": 500, "y2": 380},
        "support_type": "support",
    },
    # 青丘（抓特殊）：望月蛙、月光虫、雾中仙(一)、胡不归、月魅(一~三)、花铃(一、二)、
    # 阿宝、镜妖(一)、涂山瞳(一~三)（含变异）。
    # 特殊高价值 = 涂山瞳。妙手空空未单列，回退全部模板。
    "青丘": {
        "tou_targets": ["PK-召唤兽-涂山瞳", "PK-召唤兽-雾中仙", "PK-召唤兽-镜妖"],
        "jineng_targets": ["PK-召唤兽-涂山瞳", "PK-召唤兽-雾中仙", "PK-召唤兽-镜妖",
                           "PK-召唤兽-望月蛙", "PK-召唤兽-月光虫", "PK-召唤兽-胡不归",
                           "PK-召唤兽-月魅", "PK-召唤兽-花铃", "PK-召唤兽-阿宝"],
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
    "长安酒店", "蓬莱仙岛", "万界通廊", "幻境花果山",
]


# ===== 特殊抓宠场景（队伍抓特殊，与「偷卡场景」分开管理）=====
# 这些场景走「有 特殊/变异/宝宝 → 捕捉；没有 → 挂自动击杀」，且变异识别会用
# 放大镜变异* 称号模板。偷卡场景不在此集合，变异识别保持默认（变异蛟龙/变异地狱战神）。
SPECIAL_CAPTURE_SCENES = [
    "须弥东界",
    "银华境",       # 特殊面板写“银华镜”，运行时经 SCENE_ALIASES 归一
    "弥勒山",
    "丝绸之路",
    "伊阙龙门",
    "无名鬼域",
    "青丘",
]


# 游戏内场景名与特殊面板写法不一致的别名：正常化后统一返回 SCENE_MAPPING 里的规范键。
# 例：面板下拉写“银华镜”，但 OCR/地图读取场景名为“银华境”，二者实为同一场景。
SCENE_ALIASES = {
    "银华镜": "银华境",
}


def _normalize_scene(area):
    """把别名场景名映射到 SCENE_MAPPING 规范键；未知场景原样返回。"""
    if not area:
        return area
    return SCENE_ALIASES.get(area, area)


def get_tou_targets(area):
    area = _normalize_scene(area)
    mapping = SCENE_MAPPING.get(area)
    return mapping["tou_targets"] if mapping else None


def get_jineng_targets(area):
    area = _normalize_scene(area)
    mapping = SCENE_MAPPING.get(area)
    return mapping["jineng_targets"] if mapping else None


def get_all_monsters(area):
    area = _normalize_scene(area)
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
    area = _normalize_scene(area)
    mapping = SCENE_MAPPING.get(area)
    return mapping["map_click"] if mapping else {"x1": 212, "y1": 21, "x2": 475, "y2": 415}


# 特殊场景「点法术后点杀目标」：没有特殊/变异/宝宝时，点法术(710,100)后点击的普通怪。
# 排除各场景的特殊/高价值怪（有特殊/宝宝时走捕捉不会进这条路径；排除是防误点）。
PRE_AUTO_TARGETS = {
    "须弥东界": ["PK-召唤兽-毗舍童子", "PK-召唤兽-真陀护法"],   # 排除 持国巡守
    "银华境": ["PK-召唤兽-毗舍童子", "PK-召唤兽-真陀护法"],     # 排除 广目巡守
    "弥勒山": ["PK-召唤兽-九色鹿", "PK-召唤兽-翼马",
              "PK-召唤兽-芙蓉仙子", "PK-召唤兽-涂山瞳"],
    # 丝绸之路无固定怪物表：不配置，引擎回退到 get_all_monsters/宽松检测
    "伊阙龙门": ["PK-召唤兽-灵鹤", "PK-召唤兽-巡游天神",
                "PK-召唤兽-雾中仙"],                            # 排除 多闻巡守
    "无名鬼域": ["PK-召唤兽-吸血鬼", "PK-召唤兽-幽灵"],         # 排除 画魂/鬼将
    "青丘": ["PK-召唤兽-雾中仙", "PK-召唤兽-镜妖", "PK-召唤兽-望月蛙",
            "PK-召唤兽-月光虫", "PK-召唤兽-胡不归", "PK-召唤兽-月魅",
            "PK-召唤兽-花铃", "PK-召唤兽-阿宝"],                # 排除 涂山瞳
}


def get_pre_auto_targets(area):
    """特殊场景点法术后的点杀目标（排除高价值特殊怪）；未配置的场景回退全部怪物。"""
    area = _normalize_scene(area)
    targets = PRE_AUTO_TARGETS.get(area)
    return list(targets) if targets else get_all_monsters(area)


def is_supported_scene(area):
    area = _normalize_scene(area)
    mapping = SCENE_MAPPING.get(area)
    return mapping is not None and mapping.get("support_type") == "support"


def is_special_capture_scene(area):
    """判断某场景是否为「特殊抓宠场景」。支持别名归一（银华镜→银华境）。"""
    area = _normalize_scene(area)
    return area in SPECIAL_CAPTURE_SCENES


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
