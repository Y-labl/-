# -*- coding: utf-8 -*-
"""颜色检测 - 游戏界面状态检测（参考小霸王 color_util.py + common_action_logic.py）"""
from core.img_util import get_color, match_colors, find_template

# ---- 弹窗检测 ----
_RESULT_POP_POINTS = [(165,406),(170,406),(175,410),(680,406),(685,406),(690,410)]

def is_popup_showing(frame_bgr):
    """检测战斗奖励弹窗"""
    def _c(r,g,b): return r < 52 and 13 < g < 73 and 25 < b < 85
    return match_colors(frame_bgr, _RESULT_POP_POINTS, _c, error_ratio=0.3)

def dismiss_popup_click_pos():
    return (400, 224)

# ---- 战斗状态检测 ----
def is_in_battle(frame_bgr):
    """检测是否在战斗中（参照原版 isInPk）
    
    原版: 找不到"好友入口"模板 = 战斗中（按钮被战斗UI遮挡）
    点卡服: 好友入口在战斗时被遮挡或位移
    """
    if frame_bgr is None: return False
    try:
        import os
        tpl_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "逻辑素材"
        )
        tpl_path = os.path.join(tpl_dir, "好友入口点卡服.png")
        if not os.path.exists(tpl_path):
            # 无模板回退到颜色点检测
            _HIDE_ENTER_POINTS = [(16,163),(17,163),(19,164),(20,163),(21,162),(25,163),(30,163),(31,163),(32,164),(33,163)]
            def _c(r,g,b): return r > 170 and g > 140 and b > 80
            return not match_colors(frame_bgr, _HIDE_ENTER_POINTS, _c, error_ratio=0.3)
        result = find_template(frame_bgr, tpl_path, threshold=0.70)
        # 找到好友入口 = 非战斗；找不到 = 战斗中
        return result is None
    except:
        return False

# ---- 血蓝检测（像素扫描，参考 check51AddXue） ----
def detect_hp_percent(frame_bgr):
    """通过血条像素扫描检测血量百分比（原版: 每匹配像素 += 2.38）"""
    if frame_bgr is None: return 100
    hp = 0.0
    try:
        h, w = frame_bgr.shape[:2]
        for x in range(756, min(799, w)):
            r, g, b = get_color(frame_bgr, x, 6)
            if r > 200 and 34 < g < 98 and b < 65:
                hp += 2.38
        return hp  # 原版不限制100%
    except: return 100.0

def detect_mp_percent(frame_bgr):
    """通过蓝条像素扫描检测蓝量百分比（原版: 每匹配像素 += 2.38）"""
    if frame_bgr is None: return 100
    mp = 0.0
    try:
        h, w = frame_bgr.shape[:2]
        for x in range(756, min(799, w)):
            r, g, b = get_color(frame_bgr, x, 14)
            if 87 > r > 10 and 120 < g < 175 and b > 205:
                mp += 2.38
        return mp  # 原版不限制100%
    except: return 100.0

def detect_bb_hp_percent(frame_bgr):
    """宝宝血量百分比（原版: 没宝宝时返回101, 有宝宝时扫描）"""
    if frame_bgr is None: return 101
    hp = 0.0
    try:
        h, w = frame_bgr.shape[:2]
        for x in range(654, min(697, w)):
            r, g, b = get_color(frame_bgr, x, 6)
            if r > 200 and 34 < g < 98 and b < 65:
                hp += 2.38
        if hp > 0:
            return hp  # 有宝宝, 返回扫描值
        return 101  # 没宝宝, 返回101（原版行为）
    except: return 101

# ---- 巫医检测 ----
def is_need_wuyi(frame_bgr):
    """检测是否需要巫医（小猫-召唤兽忠诚度）"""
    def _c(r,g,b): return r > 180 and g < 100 and b < 100
    return match_colors(frame_bgr, [(15,15)], _c, error_ratio=0.1)

# ---- PK护佑/暴击检测 ----
def is_huyou_text(frame_bgr):
    """检测护佑文字"""
    def _c(r,g,b): return r > 200 and g > 180 and b > 50
    region = [(300,50),(305,55),(310,52)]
    return match_colors(frame_bgr, region, _c, error_ratio=0.3)

def is_baoji_text(frame_bgr):
    """检测暴击文字"""
    def _c(r,g,b): return r > 220 and g > 200 and b > 20
    return match_colors(frame_bgr, [(310,60),(320,65)], _c, error_ratio=0.2)

# ---- 四小人检测 ----
def is_four_person_showing(frame_bgr):
    """检测四小人（参照原版 isShowFourPerson）
    
    原版逻辑: 战斗中检测"好友入口"模板，找不到=四小人出现。
    四小人出现时会遮挡角色头像区域，好友入口模板匹配不到。
    """
    if frame_bgr is None: return False
    try:
        import os
        tpl_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "逻辑素材"
        )
        tpl_path = os.path.join(tpl_dir, "好友入口点卡服.png")
        if not os.path.exists(tpl_path):
            # 无模板则回退到std检测（提高阈值）
            region = frame_bgr[80:180, 90:280]
            return region.std() > 80
        # 模板匹配好友入口，找不到=四小人
        result = find_template(frame_bgr, tpl_path, threshold=0.70)
        return result is None
    except: return False
