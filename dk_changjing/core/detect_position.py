# -*- coding: utf-8 -*-
"""游戏位置检测 - 关键点击坐标（参考小霸王 detect_position_util.py）

所有坐标基于 1080x1920 分辨率（梦幻西游手游默认竖屏分辨率）
实际使用时需根据设备分辨率等比缩放
"""

# ---- 场景战斗操作 ----

# 自动战斗按钮（场景挂机时）
BTN_AUTO_BATTLE = (980, 1750)

# 场景挂机中的"攻击"按钮
BTN_ATTACK = (540, 1700)

# "继续"按钮（战斗结束后）
BTN_CONTINUE = (540, 1550)

# ---- 角色状态操作 ----

# 角色头像位置（点击打开角色面板）
BTN_ROLE_AVATAR = (80, 1820)

# 加血按钮（秘制/红碗）
BTN_ADD_HP = (300, 1500)

# 加蓝按钮（秘制/蓝碗）
BTN_ADD_MP = (500, 1500)

# ---- 弹窗处理 ----

# 弹窗关闭位置（点击空白处关闭）
BTN_DISMISS_POPUP = (540, 960)

# "确定"按钮通用位置
BTN_CONFIRM = (540, 1300)

# ---- 道具栏 ----

# 道具栏入口
BTN_ITEM_BAR = (1020, 1850)

# ---- 捕捉操作 ----

# 捕捉按钮
BTN_CATCH = (540, 1600)

# ---- 偷窃操作 ----

# 偷窃按钮（妙手空空）
BTN_STEAL = (400, 1600)

# ---- PK 操作 ----

# 技能按钮
BTN_SKILL = (200, 1700)

# 普通攻击按钮
BTN_NORMAL_ATTACK = (400, 1700)

# 防御按钮
BTN_DEFEND = (600, 1700)

# 逃跑按钮
BTN_FLEE = (800, 1700)

# ---- 队伍操作 ----

# 队伍入口
BTN_TEAM = (940, 1820)

# 自动寻路按钮（队长）
BTN_AUTO_PATH = (900, 1750)


def scale_coordinates(base_w=1080, base_h=1920, target_w=1080, target_h=1920):
    """根据设备分辨率缩放坐标"""
    scale_x = target_w / base_w
    scale_y = target_h / base_h
    return scale_x, scale_y


def get_scaled_pos(x, y, target_w=1080, target_h=1920, base_w=1080, base_h=1920):
    """获取缩放后的坐标"""
    sx, sy = scale_coordinates(base_w, base_h, target_w, target_h)
    return int(x * sx), int(y * sy)
