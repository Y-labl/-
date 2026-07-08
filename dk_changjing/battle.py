# -*- coding: utf-8 -*-
"""战斗逻辑模块 - 基于原版 DKChangJingThread 重建

原版战斗流程（startDuiZhang）:
  1. isInPk(deviceId) → 检查"好友入口"图标是否消失（消失=战斗中）
  2. isShowFourPerson → 检测四小人遭遇 → findFourPersonAndClick
  3. 根据配置执行:
     - isZhua → findSideTargetPoints → 妙手空空技能
     - isTou  → findSideTargetPoints → 逐个点击目标（最多4次）
     - isPkJiNeng → findSideTargetPoints → 逐个点击攻击
     - isPkTaoPao → 点击逃跑
  4. checkXueLan → 颜色像素检测血量/蓝量百分比 → 加血/加蓝
  5. checkWuYi → 检测召唤兽忠诚度 → 找巫医NPC治疗
"""

import time, random, os
import cv2
import numpy as np

from core.img_util import find_template
from core.adb_util import AdbUtil

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
LOGIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "逻辑素材")  # 原版战斗模板


class BattleConfig:
    """战斗配置（对应原版 DKChangJingConfigModel）"""
    def __init__(self):
        self.mode = "auto"         # auto / skill / capture / steal / escape
        self.hp_threshold = 30     # 血量低于此百分比时加血
        self.mp_threshold = 20     # 蓝量低于此百分比时加蓝
        self.hp_mode = "item"      # item=战斗中使用药品 / rest=休息回血
        self.mp_mode = "item"      # item=战斗中使用药品 / rest=休息回蓝
        self.use_wuyi = True       # 是否使用巫医治疗召唤兽


class BattleHandler:
    """战斗处理器 - 供场景线程调用"""

    def __init__(self, client, log_func=None):
        """
        Args:
            client: pyscrcpy Client 实例
            log_func: 日志函数 func(msg)
        """
        self._client = client
        self._log = log_func or print
        self._config = BattleConfig()
        self._target_names = []     # 当前场景的怪物名称列表
        self._battle_count = 0      # 战斗计数
        self._auto_toggled = False  # 自动按钮是否已点击
        self._cached_targets = []   # 当前战斗缓存的目标
        self._max_rounds = 30       # 单场战斗最大回合数

    # ================================================================
    # 配置
    # ================================================================
    def set_mode(self, mode: str):
        """设置战斗模式: auto / skill / capture / steal / escape"""
        self._config.mode = mode

    def set_hp_threshold(self, pct: int):
        self._config.hp_threshold = pct

    def set_mp_threshold(self, pct: int):
        self._config.mp_threshold = pct

    def set_target_names(self, names: list):
        """设置当前场景需要攻击/捕捉的怪物名称列表"""
        self._target_names = names

    # ================================================================
    # 战斗检测 - 原版 isInPk(): "好友入口"图标消失=在战斗中
    # ================================================================
    def is_in_battle(self):
        """检测是否在战斗中：战斗UI模板可见=战斗中（最可靠判断）"""
        frame = self._get_frame()
        if frame is None:
            return False
        fh, fw = frame.shape[:2]

        # 战斗UI模板：自动按钮、逃跑按钮、等待操作
        battle_tpls = [
            "PK-自动按钮点卡服.png",
            "PK-逃跑点卡服.png",
            "PK-等待操作点卡服.png",
            "PK-防御点卡服.png",
            "PK-右下取消自动战斗点卡服.png",
        ]
        for ui_name in battle_tpls:
            for tpl_dir in [LOGIC_DIR, IMAGES_DIR]:
                tpl_path = os.path.join(tpl_dir, ui_name)
                if not os.path.exists(tpl_path):
                    continue
                tpl = cv2.imdecode(np.fromfile(tpl_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if tpl is None:
                    continue
                # 只在画面下半部分搜索（战斗UI在底部）
                bottom = frame[int(fh*0.7):fh, 0:fw]
                if bottom.size == 0 or tpl.shape[0] > bottom.shape[0] or tpl.shape[1] > bottom.shape[1]:
                    continue
                result = cv2.matchTemplate(bottom, tpl, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val >= 0.6:
                    return True

        # 备选：画面整体偏暗/高对比（战斗中通常有特效）
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 战斗画面标准差通常更高（血条、技能栏等）
        if gray.std() > 55:
            return True

        return False

    # ================================================================
    # 主战斗回合
    # ================================================================
    def do_battle_round(self):
        """执行一回合战斗操作，返回 True=仍在战斗中"""
        self._battle_count += 1
        if self._battle_count > self._max_rounds:
            self._log(f"  战斗超 {self._max_rounds} 回合，强制退出")
            return False
        if not self.is_in_battle():
            self._cached_targets = []
            self._auto_toggled = False
            self._battle_count = 0
            return False

        mode = self._config.mode

        if mode == "escape":
            self._log("战斗: 逃跑")
            self._click_template("PK-逃跑.png", threshold=0.7)
            time.sleep(random.uniform(0.5, 1.0))
            return self.is_in_battle()

        if mode == "capture":
            # 捉宝宝：先找目标，再用妙手空空
            # 只搜一次，缓存结果
            if not self._cached_targets:
                self._cached_targets = self._find_side_targets()
            targets = self._cached_targets
            if targets:
                self._log(f"捕捉: 找到 {len(targets)} 个目标")
                self._click_template("PK-妙手空空技能.png", threshold=0.7)
                time.sleep(random.uniform(0.5, 0.8))
            else:
                # 没找到目标，防御
                self._click_template("PK-防御.png", threshold=0.7)
                time.sleep(random.uniform(0.3, 0.5))

        elif mode == "steal":
            # 偷窃：最多偷4次
            targets = self._find_side_targets()
            if targets:
                for tp in targets[:4]:
                    self._tap(tp[0] + tp[2] // 2, tp[1] + tp[3] // 2)
                    time.sleep(random.uniform(0.4, 0.6))
            else:
                self._log("战斗: 无目标，自动攻击")
                self._click_template("PK-自动按钮.png", threshold=0.7)
                time.sleep(random.uniform(0.8, 1.2))

        elif mode == "skill":
            # 技能攻击：找目标点击
            if not self._cached_targets:
                self._cached_targets = self._find_side_targets()
            targets = self._cached_targets
            if targets:
                for tp in targets:
                    self._tap(tp[0] + tp[2] // 2, tp[1] + tp[3] // 2)
                    time.sleep(random.uniform(0.1, 0.2))
            else:
                self._log("战斗: 无目标，自动攻击")
                self._click_template("PK-自动按钮.png", threshold=0.7)
                time.sleep(random.uniform(0.8, 1.2))

        else:  # auto 模式：首回合点自动，后续等待
            if not self._auto_toggled:
                self._log("战斗: 自动模式 - 开启自动战斗")
                self._click_template("PK-自动按钮.png", threshold=0.7)
                self._auto_toggled = True
                time.sleep(random.uniform(0.8, 1.2))
            else:
                time.sleep(random.uniform(0.3, 0.5))

        # 战斗中不加血蓝（战斗结束再处理）
        return self.is_in_battle()

    # ================================================================
    # 查找侧面目标 - 原版 findSideTargetPoints
    # ================================================================
    def _find_side_targets(self):
        """在战斗界面逐个扫描敌方怪物（参照原版 findSideTargetPoints + findHouPaiBaoBao）
        横屏下敌方在画面右侧，逐个扫描模板匹配
        """
        if not self._target_names:
            return []

        frame = self._get_frame()
        if frame is None:
            return []

        fh, fw = frame.shape[:2]
        # 横屏敌方区域：右半部分，中上区域
        # 前排大概在 y=0~fh*0.5, 后排 y=fh*0.5~fh*0.8
        search_zones = [
            ("后排", int(fw*0.55), int(fh*0.40), int(fw*0.40), int(fh*0.45)),
        ]

        targets = []
        for zone_name, left, top, roi_w, roi_h in search_zones:
            for name in self._target_names:
                for tpl_dir in [LOGIC_DIR, IMAGES_DIR]:
                    tpl_name = f"PK-召唤兽-{name}点卡服.png"
                    tpl_path = os.path.join(tpl_dir, tpl_name)
                    if not os.path.exists(tpl_path):
                        continue
                    try:
                        result = self._find_in_region(frame, tpl_path, left, top, roi_w, roi_h)
                        if result:
                            x, y, conf = result
                            is_dup = any(abs(x-tx)<60 and abs(y-ty)<60 for tx,ty,_,_,_ in targets)
                            if not is_dup:
                                tpl = cv2.imdecode(np.fromfile(tpl_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                                tw, th = (tpl.shape[1], tpl.shape[0]) if tpl is not None else (20, 20)
                                targets.append((x, y, tw, th, conf))
                                self._log(f"  发现{zone_name}: {name} ({x},{y}) conf={conf:.2f}")
                    except:
                        pass
        if not targets:
            self._log(f"  未找到目标 (搜索了{len(self._target_names)}种怪物, 前/后排)")
        return targets

    def _find_in_region(self, frame, img_path, left, top, width, height):
        """在指定区域内查找模板（img_path 为完整路径）"""
        fh, fw = frame.shape[:2]
        right = min(fw, left + width)
        bottom = min(fh, top + height)
        if right <= left or bottom <= top:
            return None
        roi = frame[top:bottom, left:right]
        template = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if template is None:
            return None
        th, tw = template.shape[:2]
        if th > roi.shape[0] or tw > roi.shape[1]:
            return None
        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.7:
            return (max_loc[0] + left, max_loc[1] + top, float(max_val))
        return None

    # ================================================================
    # 血量蓝量检测 - 原版 detectXueLanPercent（颜色像素扫描）
    # ================================================================
    def _check_hp_mp(self, in_battle=False):
        """检测并处理血量/蓝量（仅非战斗状态调用）"""
        if in_battle:
            return  # 战斗中无法加血蓝
        frame = self._get_frame()
        if frame is None:
            return

        fh, fw = frame.shape[:2]
        # 横屏下血量条在顶部偏左位置
        # 竖屏(1080w)坐标 x=756~799, y=6 → 横屏(1920w)坐标 x=1344~1422, y=6
        hp_x1 = int(756 * fw / 1080)
        hp_x2 = int(799 * fw / 1080)
        mp_x1 = int(756 * fw / 1080)
        mp_x2 = int(799 * fw / 1080)

        hp_percent = self._scan_color_bar(frame,
            hp_x1, hp_x2, 6, (200, 34, 65), mode="red")
        mp_percent = self._scan_color_bar(frame,
            mp_x1, mp_x2, 13, (80, 150, 200), mode="blue")

        if hp_percent > 0 or mp_percent > 0:
            self._log(f"  HP:{hp_percent}% MP:{mp_percent}%")

        # 加血
        if hp_percent < self._config.hp_threshold:
            self._log(f"  HP过低({hp_percent}%)，加血")
            if self._config.hp_mode == "item":
                self._tap(int(fw * 0.72), 15)  # 横屏 x≈775/1080≈0.72
                time.sleep(random.uniform(0.8, 1.2))
                self._click_template("PK-角色加血.png", threshold=0.7)

        # 加蓝
        if mp_percent < self._config.mp_threshold:
            self._log(f"  MP过低({mp_percent}%)，加蓝")
            if self._config.mp_mode == "item":
                self._tap(int(fw * 0.72), 15)  # 横屏 x≈775/1080≈0.72
                time.sleep(random.uniform(0.8, 1.2))
                self._click_template("PK-补充魔法.png", threshold=0.7)

    @staticmethod
    def _scan_color_bar(frame, x_start, x_end, y, thresholds, mode="red"):
        """扫描颜色条，统计匹配像素比例（模拟原版像素扫描）"""
        try:
            if frame is None:
                return 50
            matched = 0
            total = 0
            r_low, g_low, b_low = thresholds[0], thresholds[1] if len(thresholds) > 1 else 0, thresholds[2] if len(thresholds) > 2 else 0
            for x in range(max(0, x_start), min(frame.shape[1], x_end)):
                b, g, r = frame[y, x]
                if mode == "red":
                    if r > 200 and 34 < g < 98 and b < 65:
                        matched += 1
                elif mode == "blue":
                    if b > 200 and r < 80 and g < 150:
                        matched += 1
                total += 1
            if total > 0:
                return max(1, int(matched / total * 100))
        except Exception:
            pass
        return 50


    # ================================================================
    # 战斗状态检测（原版完整检测项）
    # ================================================================

    def check_battle_flags(self):
        """检测战斗中的各种特殊状态（护佑、暴击、四小人、变异宝宝）
        返回: dict of {flag_name: bool}
        """
        frame = self._get_frame()
        if frame is None:
            return {}

        flags = {}
        fh, fw = frame.shape[:2]
        sx, sy = fw / 1080.0, fh / 608.0  # 横屏缩放

        # 1. 护佑检测 - 怪物带护佑buff（黄色文字）
        flags["huyou"] = self._detect_color_text(frame,
            [(int(300*sx), int(50*sy)), (int(305*sx), int(55*sy)), (int(310*sx), int(52*sy))],
            lambda r,g,b: r > 200 and g > 180 and b > 50, ratio=0.3)

        # 2. 暴击检测 - 暴击文字出现（黄/橙色文字）
        flags["baoji"] = self._detect_color_text(frame,
            [(int(310*sx), int(60*sy)), (int(320*sx), int(65*sy))],
            lambda r,g,b: r > 220 and g > 200 and b > 20, ratio=0.2)

        # 3. 四小人检测 - 特殊遭遇遮住角色区域
        flags["four_person"] = self._detect_four_person(frame)

        # 4. 变异宝宝检测 - 蓝色"宝宝"或"变异"文字
        flags["baby_mutated"] = self._find_template("PK-召唤兽-变异.png", threshold=0.7) is not None
        flags["baby_blue"] = self._find_template("PK-召唤兽宝宝文字蓝色.png", threshold=0.7) is not None

        # 5. 召唤兽忠诚度 - 小猫图标
        flags["pet_loyalty"] = self._find_template("小猫-召唤兽忠诚度.png", threshold=0.7) is not None

        # 6. 没带宝宝
        flags["no_pet"] = self._find_template("没带宝宝.png", threshold=0.7) is not None

        if any(flags.values()):
            active = [k for k, v in flags.items() if v]
            self._log(f"  战斗状态: {', '.join(active)}")

        return flags

    @staticmethod
    def _detect_color_text(frame, points, check_fn, ratio=0.3):
        """多点多色检测（原版 match_colors / getColorFromFrame）"""
        try:
            ok = 0
            for px, py in points:
                if 0 <= py < frame.shape[0] and 0 <= px < frame.shape[1]:
                    b, g, r = frame[py, px]
                    if check_fn(r, g, b):
                        ok += 1
            return ok >= len(points) * (1 - ratio)
        except:
            return False

    def _detect_four_person(self, frame):
        """四小人检测：好友入口图标消失 + 角色区域异常"""
        if frame is None:
            return False
        # 检查角色头像区域是否有异常（标准差大=有遮挡）
        try:
            fh, fw = frame.shape[:2]
            sx, sy = fw / 1080.0, fh / 608.0
            region = frame[int(80*sy):int(180*sy), int(90*sx):int(280*sx)]
            return region.std() > 80
        except:
            return False

    def handle_battle_flags(self, flags: dict):
        """处理检测到的战斗状态"""
        if flags.get("four_person"):
            self._log("  四小人遭遇！随机点击处理")
            # 四小人出现时需点击特殊区域
            fh, fw = self._get_frame().shape[:2] if self._get_frame() is not None else (608, 1080)
            self._tap(fw // 2, fh // 2)
            time.sleep(random.uniform(0.3, 0.5))

        if flags.get("huyou"):
            self._log("  检测到护佑，切换目标")
            # 护佑怪物不应攻击，换目标或逃跑
            if self._config.mode in ("skill", "capture"):
                self._click_template("PK-逃跑.png", threshold=0.7)

        if flags.get("baby_mutated") or flags.get("baby_blue"):
            self._log("  检测到变异/宝宝，优先捕捉")
            if self._config.mode == "skill":
                # 临时切换到捕捉模式
                self._click_template("PK-妙手空空技能.png", threshold=0.7)


    # ================================================================
    # 辅助方法
    # ================================================================
    def _get_frame(self):
        if self._client is None:
            return None
        frame = self._client.last_frame
        if frame is not None:
            self._client.resolution = (frame.shape[1], frame.shape[0])
        return frame

    def _tap(self, x, y):
        """ADB 点击"""
        if self._client is None:
            return
        try:
            self._client.device.shell(f"input tap {int(x)} {int(y)}")
        except Exception as e:
            self._log(f"  点击失败: {e}")

    def _find_template(self, img_name, threshold=0.7):
        frame = self._get_frame()
        if frame is None:
            return None
        img_path = os.path.join(IMAGES_DIR, img_name)
        result = find_template(frame, img_path, threshold)
        return result

    def _click_template(self, img_name, threshold=0.7):
        r = self._find_template(img_name, threshold)
        if r is None:
            return False
        x, y, conf = r
        # 注意: 新 find_template 返回 (x, y, w, h, conf)，旧返回 (x, y, conf)
        if len(r) == 5:
            _, _, w, h, _ = r
            cx, cy = x + w // 2, y + h // 2
        else:
            cx, cy = x, y
        self._tap(cx, cy)
        return True

    def _load_template(self, img_name):
        img_path = os.path.join(IMAGES_DIR, img_name)
        if not os.path.exists(img_path):
            return None
        return cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)


# ================================================================
# 场景怪物映射表（原版 getZhuaTeshuBianYiTargetImgName 等）
# ================================================================
SCENE_MONSTERS = {
    "小西天": ["炎魔神", "夜罗刹", "噬天虎", "雾中仙", "灵鹤"],
    "丝绸之路": ["修罗傀儡鬼", "修罗傀儡妖", "曼珠沙华", "金身罗汉"],
    "须弥东界": ["毗舍童子", "真陀护法", "持国巡守"],
    "子母河底": ["蚌精", "碧水夜叉", "鲛人"],
    "龙窟五层": ["蛟龙", "地狱战神", "风伯"],
    "龙窟六层": ["蛟龙", "雨师", "巡游天神"],
    "凤巢四层": ["凤凰", "天兵", "芙蓉仙子"],
    "凤巢三层": ["天将", "如意仙子", "星灵仙子"],
    "麒麟山": ["野猪精", "百足将军", "鼠先锋"],
    "小雷音寺": ["大力金刚", "雾中仙", "灵鹤"],
    "女娲神迹": ["律法女娲", "灵符女娲", "净瓶女娲"],
    "伊阙龙门": ["蛟龙", "碧水夜叉", "鲛人"],
    "银华镜": ["涂山瞳", "金翼", "望月蛙"],
    "弥勒山": ["毗舍童子", "真陀护法"],
}


def get_monster_names(area: str) -> list:
    """获取指定场景的怪物名称列表"""
    return SCENE_MONSTERS.get(area, [])


if __name__ == "__main__":
    print("战斗逻辑模块")
    print("场景怪物映射:")
    for area, monsters in SCENE_MONSTERS.items():
        print(f"  {area}: {', '.join(monsters)}")
