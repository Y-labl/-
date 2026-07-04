# -*- coding: utf-8 -*-
"""点卡场景自动化线程 v4 - 基于反编译 v2 完整原版逻辑重构

原版核心流程 (startDuiZhang):
  1. closePop + hideTaskAndChanel     → 关闭弹窗，隐藏任务栏/频道
  2. detectPosition                   → 检测当前位置（地图名+坐标）
  3. 丝绸之路特殊处理                → setCiChouRandomX
  4. while isRunning:
     ├── 弹窗处理 (isShowPopColorDK → dismiss)
     ├── PK检测 (isInPk)
     ├── 不在PK → 地图导航 (randomClickMap_CiChouZhiLu / goToMapAction)
     ├── 在PK中 → 战斗操作:
     │   ├── 四小人 (isShowFourPerson → findFourPersonAndClick)
     │   ├── [isZhua] 捕捉 → findSideTargetPoints → 妙手空空技能
     │   ├── [isTou] 偷窃 → getTouTargetImgName → findPics → 最多4次
     │   ├── [isPkJiNeng] 技能 → getJiNengTargetImgName → findSideTargetPoints
     │   ├── [isPkPuGong] 普通攻击
     │   ├── [isPkAuto] 直接自动
     │   └── [isPkTaoPao] 逃跑
     ├── 战斗结束 → checkWuYi + checkXueLan
     └── time.sleep(0.2~0.5)

注意:
  - 原版使用 pyscrcpy 实时屏幕流 + OpenCV 模板匹配 (findPic/findPics)
  - 新项目使用 win32gui PrintWindow 截图 + 颜色检测 + 模板匹配
  - 原版的地图导航依赖 game_action/map_action 模块（需要完整地图参数）
  - 原版的 NPC 交互依赖 findNpcAndClickLogic（需要完整 NPC 坐标库）
  - 以下标注 [TODO: 模板资源] 的功能需要补充对应的模板图片文件
  - 以下标注 [TODO: 地图模块] 的功能需要实现地图导航模块
"""
import os, time, random, glob, threading
from datetime import datetime
import cv2
import numpy as np
from core.adb_util import AdbUtil
from core.click_util import tap, random_sleep
from core.screenshot import ScreenCapture
from core.img_util import find_template, get_color, match_colors
from core import color_util
from config.dk_config import DKConfig

# 统一逻辑分辨率（原版 DeviceWidth/DeviceHeight）
_LOGIC_W, _LOGIC_H = 1080, 1920


# ---- 丝绸之路随机X偏移范围（原版 setCiChouRandomX） ----
# curX < 200  → (105, 270)
# curX < 400  → (290, 465)
# else        → (480, 690)
CI_CHOU_X_RANGES = {
    0: (105, 270),     # curX < 200
    1: (290, 465),     # 200 <= curX < 400
    2: (480, 690),     # curX >= 400
}


class DKChangJingThread(threading.Thread):
    """点卡场景自动化 - 丝绸之路/多地图挂机（基于反编译 v2 原版逻辑）"""

    # 丝绸之路 Y 轴随机范围
    CI_CHOU_Y_RANGE = (20, 50)

    def __init__(self, serial, config=None, screenshot=None):
        super().__init__(daemon=True)
        self.serial = serial
        self.config = config or DKConfig()
        self.screenshot = screenshot or ScreenCapture()
        self._running = False
        self._state = "INIT"
        self._battle_count = 0
        self._ci_chou_random_x = (105, 270)  # 默认范围
        self._last_nav_time = 0
        self._last_frame = None
        self._four_person_count = 0  # 四小人连续检测计数
        self._callbacks = []

    # ---- 回调系统 ----
    def add_callback(self, name, func):
        self._callbacks.append((name, func))

    def _emit(self, name, *a):
        for n, f in self._callbacks:
            if n == name:
                try: f(*a)
                except: pass

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        full = f"[{ts}] {msg}"
        print(full)
        self._emit("log", full)

    @property
    def state(self): return self._state
    @property
    def battle_count(self): return self._battle_count
    @property
    def running(self): return self._running

    def stop(self):
        self._running = False
        self._log("正在停止...")

    # ================================================================
    # 入口
    # ================================================================

    def run(self):
        self._running = True
        self._log("=== 点卡场景 v4 启动 ===")
        self._log(f"设备:{self.serial} 区域:丝绸之路")
        self._log(f"HP阈值:{self.config.role_xue_percent}% MP阈值:{self.config.role_lan_percent}%")
        self._log(f"捕捉:{self.config.is_zhua} 偷窃:{self.config.is_tou} 巫医:{self.config.is_wuyi}")
        self._log(f"自动寻路:{self.config.is_duizhang}")

        try:
            self._start_duizhang()
        except Exception as e:
            self._log(f"主循环崩溃: {e}")
            import traceback
            self._log(traceback.format_exc())
        finally:
            self._running = False
            self._log("=== 已停止 ===")

    # ================================================================
    # 主循环 - 参照原版 startDuiZhang 完整逻辑
    # ================================================================

    def _start_duizhang(self):
        """主循环（参照原版 startDuiZhang 2364字节码）"""
        # 步骤1: 初始化清理
        self._close_pop()
        self._hide_task_channel()

        # 步骤2: 检测当前位置（参照原版 detectPosition → _detectAreaByTemplate）
        area = self._detect_area()
        if area is None:
            self._log("场景检测失败，默认丝绸之路")
            area = "丝绸之路"
        self._log(f"刷场景地点: {area}")

        if area is None:
            self._log("无法检测位置，请停止")
            return

        # 步骤3: 丝绸之路特殊处理 - 根据当前X坐标设置随机范围
        # 简化: 使用默认X范围，实际应通过 detectPosition 获取 curX
        self._ci_chou_random_x = CI_CHOU_X_RANGES[2]  # 默认最右侧范围

        # 步骤4: 主循环
        while self._running:
            frame = self._get_frame()
            if frame is None:
                time.sleep(0.5)
                continue

            if not self.config.is_duizhang:
                time.sleep(0.5)
                continue

            # --- 弹窗处理（最高优先级）---
            if color_util.is_popup_showing(frame):
                self._dismiss_popup()
                time.sleep(0.2)
                continue

            # --- PK检测 ---
            in_battle = color_util.is_in_battle(frame)

            if not in_battle:
                # === 非战斗: 地图导航 ===
                self._four_person_count = 0
                self._navigate_area(area)
                time.sleep(random.uniform(0.2, 0.5))
                continue

            # === 战斗中: 战斗操作 ===
            self._state = "IN_BATTLE"

            # 弹窗处理（战斗中也可能有弹窗）
            frame = self._get_frame()
            if frame is not None and color_util.is_popup_showing(frame):
                self._dismiss_popup()
                time.sleep(0.2)

            # 四小人检测（战斗中随机事件，连续5次未清除则跳过）
            if self._four_person_count < 5:
                if color_util.is_four_person_showing(frame):
                    self._four_person_count += 1
                    self._log(f"出现四小人! (第{self._four_person_count}次)")
                    self._do_tap("四小人", 240, 120)
                    time.sleep(random.uniform(0.5, 1.0))
                    continue
            elif not color_util.is_four_person_showing(frame):
                self._four_person_count = 0

            # 战斗操作
            self._log("操作战斗")
            self._do_battle_operations(area)

            # 等待操作生效
            time.sleep(random.uniform(1, 2))

            # 检测战斗是否结束
            frame = self._get_frame()
            if frame is not None and not color_util.is_in_battle(frame):
                self._battle_count += 1
                self._four_person_count = 0
                self._log(f"战斗结束! 累计:{self._battle_count}场")
                self._emit("state_update", self._state, self._battle_count)

                # 取消自动战斗
                self._cancel_auto_battle()

                # 战后维护: 巫医 + 血蓝
                if self.config.is_duizhang:
                    self._check_wuyi(area)
                    self._check_xue_lan(0)

                self._state = "IDLE"

            time.sleep(random.uniform(0.2, 0.5))

    # ================================================================
    # 战斗操作 - 参照原版完整逻辑
    # ================================================================

    def _tpl(self, name):
        """获取逻辑素材模板路径"""
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "逻辑素材")
        return os.path.join(base, name)

    def _detect_area(self):
        """检测当前场景（参照原版 _detectAreaByTemplate）
        
        在截图右侧位置栏区域用模板匹配识别场景名。
        返回场景名，无法识别时返回 None。
        """
        frame = self._get_frame()
        if frame is None:
            return None

        tpl_dir = self._tpl("")
        pattern = os.path.join(tpl_dir, "位置栏-*点卡服.png")
        tpl_files = glob.glob(pattern)
        if not tpl_files:
            return None

        h, w = frame.shape[:2]
        # 位置栏区域（原版: x=100~320, y=50~95，基于1080x1920）
        region = (100, 50, 220, 50)

        best_area = None
        best_val = 0.0
        for tpl_path in tpl_files:
            # 从文件名提取场景名: 位置栏-小西天点卡服.png → 小西天
            basename = os.path.basename(tpl_path)
            name = basename.replace("位置栏-", "", 1).replace("点卡服.png", "", 1)
            result = find_template(frame, tpl_path, threshold=0.6, region=region)
            if result and result[2] > best_val:
                best_val = result[2]
                best_area = name

        if best_area:
            self._log(f"检测场景: {best_area} 相似度={best_val:.3f}")
        return best_area

    def _find_side_targets(self, target_names_list):
        """在战斗右侧找到目标对象（参考原版 findSideTargetPoints）"""
        frame = self._get_frame()
        if frame is None:
            return []
        target_points = []
        for target_names in target_names_list:
            for tpl_name in target_names:
                tpl_path = self._tpl(tpl_name)
                result = find_template(frame, tpl_path, threshold=0.75, region=(95, 35, 365, 270))
                if result:
                    x, y, conf = result
                    is_exist = any(abs(x - px) < 50 and abs(y - py) < 50 for px, py in target_points)
                    if not is_exist:
                        target_points.append((x, y))
                        break
        return target_points

    def _do_battle_operations(self, area):
        """战斗操作（参考原版逻辑重构）"""

        # ---- 捕捉 (isZhua) ----
        if self.config.is_zhua:
            self._log("PK-捕捉模式")
            target_names = self._get_zhua_target_names(area)
            side_targets = self._find_side_targets(target_names) if target_names else []
            if side_targets:
                tx, ty = side_targets[0]
                self._do_tap("捕捉目标", tx, ty)
                time.sleep(random.uniform(0.1, 0.2))
                tpl = self._tpl("PK-妙手空空技能点卡服.png")
                result = find_template(self._get_frame(), tpl, threshold=0.7)
                if result:
                    self._do_tap("妙手空空", result[0], result[1])
                else:
                    self._do_tap("妙手空空", 270, 270)
                self._log("PK-捕捉完成")
            else:
                self._log("未找到捕捉目标，跳过")
            time.sleep(random.uniform(0.5, 0.8))
            return

        # ---- 偷窃 (isTou) ----
        if self.config.is_tou:
            self._log("PK-偷窃模式")
            if self.config.is_pk_auto:
                tpl = self._tpl("PK-取消自动战斗点卡服.png")
                result = find_template(self._get_frame(), tpl, threshold=0.7)
                if result:
                    self._do_tap("取消自动", result[0], result[1])
                time.sleep(random.uniform(0.3, 0.5))
            target_names = self._get_tou_target_names(area)
            side_targets = self._find_side_targets(target_names) if target_names else []
            tou_count = 0
            if side_targets:
                for tx, ty in side_targets:
                    if tou_count >= 4:
                        break
                    self._do_tap("偷窃目标" + str(tou_count+1), tx, ty)
                    time.sleep(random.uniform(0.4, 0.6))
                    tou_count += 1
            if tou_count == 0:
                self._log("没有合适目标或偷满4次，选择逃跑")
                tpl = self._tpl("PK-逃跑点卡服.png")
                result = find_template(self._get_frame(), tpl, threshold=0.7)
                if result:
                    self._do_tap("逃跑", result[0], result[1])
                else:
                    self._do_tap("逃跑", 708, 147)
            return

        # ---- 技能攻击 (isPkJiNeng) ----
        if self.config.is_pk_jineng:
            self._log("PK-技能攻击")
            if self.config.is_pk_auto:
                tpl = self._tpl("PK-取消自动战斗点卡服.png")
                result = find_template(self._get_frame(), tpl, threshold=0.7)
                if result:
                    self._do_tap("取消自动", result[0], result[1])
                time.sleep(random.uniform(0.3, 0.5))
            target_names = self._get_jineng_target_names(area)
            side_targets = self._find_side_targets(target_names) if target_names else []
            if side_targets:
                tx, ty = side_targets[0]
                self._do_tap("技能目标", tx, ty)
                time.sleep(random.uniform(0.1, 0.2))
                self._do_tap("普通攻击", 270, 365)
                self._log("PK-攻击完成")
            else:
                self._log("找不到攻击目标，防御")
                tpl = self._tpl("PK-防御点卡服.png")
                result = find_template(self._get_frame(), tpl, threshold=0.7)
                if result:
                    self._do_tap("防御", result[0], result[1])
                else:
                    self._do_tap("防御", 400, 365)
            return

        # ---- 普通攻击 (isPkPuGong) ----
        if self.config.is_pk_pugong:
            self._log("PK-普通攻击")
            if self.config.is_pk_auto:
                tpl = self._tpl("PK-取消自动战斗点卡服.png")
                result = find_template(self._get_frame(), tpl, threshold=0.7)
                if result:
                    self._do_tap("取消自动", result[0], result[1])
                time.sleep(random.uniform(0.3, 0.5))
            target_names = self._get_jineng_target_names(area)
            side_targets = self._find_side_targets(target_names) if target_names else []
            if side_targets:
                tx, ty = side_targets[0]
                self._do_tap("攻击目标", tx, ty)
                time.sleep(random.uniform(0.1, 0.2))
            self._do_tap("普通攻击", 270, 270)
            return

        # ---- 防御 (isPkFangYu) ----
        if self.config.is_pk_fangyu:
            self._log("PK-防御")
            tpl = self._tpl("PK-防御点卡服.png")
            result = find_template(self._get_frame(), tpl, threshold=0.7)
            if result:
                self._do_tap("防御", result[0], result[1])
            else:
                self._do_tap("防御", 400, 365)
            return

        # ---- 逃跑 (isPkTaoPao) ----
        if self.config.is_pk_taopao:
            self._log("PK-逃跑")
            tpl = self._tpl("PK-逃跑点卡服.png")
            result = find_template(self._get_frame(), tpl, threshold=0.7)
            if result:
                self._do_tap("逃跑", result[0], result[1])
            else:
                self._do_tap("逃跑", 708, 147)
            return

        # ---- 直接自动战斗 (isPkAuto) ----
        if self.config.is_pk_auto:
            self._log("PK-自动战斗")
            tpl = self._tpl("PK-自动按钮点卡服.png")
            result = find_template(self._get_frame(), tpl, threshold=0.7)
            if result:
                self._do_tap("自动战斗", result[0], result[1])
            else:
                self._do_tap("自动战斗", 765, 147)
            return

        # 默认: 自动战斗
        self._do_tap("自动战斗", 765, 147)

    def _get_zhua_target_names(self, area):
        if not area: return []
        a = area or ""
        if "小西天" in a: return [["PK-召唤兽-变异龙鲤点卡服.png","PK-召唤兽-变异雷帝点卡服.png"],["PK-召唤兽-变异凤凰点卡服.png"]]
        if "子母河底" in a: return [["PK-召唤兽-变异巡游天神点卡服.png"],["PK-召唤兽-变异凤凰点卡服.png"]]
        if "须弥东界" in a: return [["PK-召唤兽-变异持国巡守点卡服.png","PK-召唤兽-持国巡守点卡服.png"]]
        if "龙窟五层" in a: return [["PK-召唤兽-变异龙鲤点卡服.png"],["PK-召唤兽-变异雷帝点卡服.png"]]
        if "龙窟六层" in a: return [["PK-召唤兽-变异雷帝点卡服.png"]]
        if "女娲神迹" in a: return [["PK-召唤兽-变异龙鲤点卡服.png"],["PK-召唤兽-变异凤凰点卡服.png"]]
        return []

    def _get_tou_target_names(self, area):
        a = area or ""
        if "小西天" in a: return [["PK-召唤兽-燕子点卡服.png","PK-召唤兽-夜影点卡服.png","PK-召唤兽-夜罗剌点卡服.png"]]
        if "丝绸之路" in a: return [["PK-召唤兽-龙鲤点卡服.png","PK-召唤兽-凤凰点卡服.png"]]
        if "子母河底" in a: return [["PK-召唤兽-巡游天神点卡服.png"]]
        if "龙窟五层" in a: return [["PK-召唤兽-龙鲤点卡服.png","PK-召唤兽-雷帝点卡服.png","PK-召唤兽-蚶精点卡服.png"]]
        if "龙窟六层" in a: return [["PK-召唤兽-雷帝点卡服.png","PK-召唤兽-蚶精点卡服.png"]]
        if "女娲神迹" in a: return [["PK-召唤兽-燕子点卡服.png","PK-召唤兽-夜罗剌点卡服.png"]]
        return []

    def _get_jineng_target_names(self, area):
        a = area or ""
        if "小西天" in a: return [["PK-召唤兽-燕子点卡服.png","PK-召唤兽-夜影点卡服.png","PK-召唤兽-夜罗剌点卡服.png"]]
        if "丝绸之路" in a: return [["PK-召唤兽-龙鲤点卡服.png","PK-召唤兽-凤凰点卡服.png"]]
        if "子母河底" in a: return [["PK-召唤兽-巡游天神点卡服.png"]]
        if "龙窟五层" in a: return [["PK-召唤兽-龙鲤点卡服.png","PK-召唤兽-雷帝点卡服.png"]]
        if "龙窟六层" in a: return [["PK-召唤兽-雷帝点卡服.png"]]
        if "女娲神迹" in a: return [["PK-召唤兽-燕子点卡服.png","PK-召唤兽-夜罗剌点卡服.png"]]
        return []

    def _navigate_area(self, area):
        """地图导航（参照原版: 不在PK时导航）"""
        now = time.time()
        if now - self._last_nav_time < 3:
            return

        self._state = "NAVIGATE"
        frame = self._get_frame()

        # 第一步：打开地图（模板匹配 + fallback坐标）
        tpl_map = self._tpl("打开地图点卡服.png")
        result = find_template(frame, tpl_map, threshold=0.7) if frame is not None else None
        if result:
            self._do_tap("打开地图", result[0], result[1])
        else:
            self._do_tap("打开地图", 1535, 514)
        time.sleep(random.uniform(0.8, 1.2))

        # 第二步：在地图上点击寻路
        frame = self._get_frame()
        if area == "丝绸之路":
            x = random.randint(*self._ci_chou_random_x)
            y = random.randint(*self.CI_CHOU_Y_RANGE)
            self._do_tap(f"寻路({x},{y})", x, y)
            self._log(f"丝绸之路寻路: ({x}, {y})")
        elif area == "小西天":
            # 用"点卡小西天地图.png"模板匹配地图区域，在识别范围内随机点击
            x, y = self._click_in_map_template(frame, "点卡小西天地图.png", area)
        else:
            # 其他地图通用兜底：在地图中央区域随机点
            h, w = frame.shape[:2] if frame is not None else (_LOGIC_H, _LOGIC_W)
            x = random.randint(int(w * 0.40), int(w * 0.75))
            y = random.randint(int(h * 0.10), int(h * 0.50))
            self._do_tap(f"寻路({x},{y})", x, y)
            self._log(f"寻路({area}): ({x}, {y})")
        self._last_nav_time = now

    def _click_in_map_template(self, frame, tpl_name, area):
        """用地图模板匹配寻路区域，在匹配范围内随机点击
        
        返回 (x, y) 点击坐标。匹配失败时 fallback 到地图中央。
        """
        if frame is None:
            x, y = 540, 700
            self._do_tap(f"寻路({x},{y})", x, y)
            return x, y

        tpl_path = self._tpl(tpl_name)
        result = find_template(frame, tpl_path, threshold=0.6)
        if result:
            mx, my, conf = result
            # 读取模板尺寸确定匹配区域
            tpl = cv2.imdecode(np.fromfile(tpl_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if tpl is not None:
                tw, th = tpl.shape[1], tpl.shape[0]
                # 在匹配区域内随机点击（留 15% 边距避免点到边缘/关闭按钮）
                pad_x = int(tw * 0.15)
                pad_y = int(th * 0.15)
                x = random.randint(mx + pad_x, mx + tw - pad_x)
                y = random.randint(my + pad_y, my + th - pad_y)
                self._do_tap(f"寻路({area}):({x},{y})", x, y)
                self._log(f"{area}地图匹配成功 conf={conf:.3f} 点击({x},{y})")
                return x, y

        # fallback: 地图中央随机
        x = random.randint(400, 680)
        y = random.randint(400, 1000)
        self._do_tap(f"寻路({area})fallback:({x},{y})", x, y)
        self._log(f"{area}地图匹配失败，fallback点击({x},{y})")
        return x, y

    # ================================================================
    # 四小人处理 - 参照原版 isShowFourPerson → findFourPersonAndClick
    # ================================================================

    def _check_four_person(self):
        """检测并处理四小人"""
        frame = self._get_frame()
        if frame is None:
            return False

        if color_util.is_four_person_showing(frame):
            self._log("出现四小人!")
            # 原版: findFourPersonAndClick → click(targetP)
            self._do_tap("四小人", 200, 120)
            time.sleep(random.uniform(0.5, 1.0))
            return True
        return False

    # ================================================================
    # 血蓝检查 - 参照原版 checkXueLan + detectXueLanPercent
    # ================================================================

    def _check_xue_lan(self, try_t):
        """血蓝检查与自动补充（参照原版 checkXueLan, 含重试机制）"""
        if try_t > 6:
            self._log("血蓝补充重试超过6次, 跳过")
            return

        # 原版: 如果加血和加蓝都是"秘制"则跳过（秘制自动生效）
        if self.config.role_add_xue_mode == "秘制" and self.config.role_add_lan_mode == "秘制":
            return

        frame = self._get_frame()
        if frame is None:
            return

        xue_pct, lan_pct, bb_xue_pct = self._detect_xue_lan_percent(frame)
        self._log(f"血蓝检测: HP={xue_pct:.0f}% MP={lan_pct:.0f}% BB={bb_xue_pct:.0f}%")

        # 宝宝血量补充
        if bb_xue_pct < int(self.config.role_xue_percent):
            self._do_tap("宝宝头像", 675, 15)
            time.sleep(random.uniform(0.5, 0.8))
            # 原版: findPic("PK-补充气血")
            self._do_tap("补充宝宝血", 675, 80)

        # 人物血量补充
        if xue_pct < int(self.config.role_xue_percent):
            try_t += 1
            if self.config.role_add_xue_mode == "秘制":
                self._do_tap("人物头像", 775, 15)
                time.sleep(random.uniform(0.8, 1.2))
                # 原版: findPic("PK-补充气血")
                self._do_tap("补充人物血", 775, 80)
            elif self.config.role_add_xue_mode == "红碗":
                # 原版: findPic("PK-使用红碗")
                self._do_tap("红碗", 775, 80)
            elif self.config.role_add_xue_mode == "酒肆":
                # 原版: findPic("PK-酒肆技能") → findPic("PK-酒肆-休息")
                self._do_tap("酒肆", 775, 80)
                time.sleep(random.uniform(0.8, 1.2))
                self._do_tap("酒肆休息", 540, 960)
            time.sleep(random.uniform(0.8, 1.2))
            self._check_xue_lan(try_t)
            return

        # 人物蓝量补充
        if lan_pct < int(self.config.role_lan_percent):
            try_t += 1
            if self.config.role_add_lan_mode == "秘制":
                self._do_tap("人物头像", 775, 15)
                time.sleep(random.uniform(0.8, 1.2))
                # 原版: findPic("PK-补充魔法")
                self._do_tap("补充人物蓝", 775, 110)
            elif self.config.role_add_lan_mode == "蓝碗":
                self._do_tap("蓝碗", 775, 110)
            elif self.config.role_add_lan_mode == "酒肆":
                # 原版: findPic("PK-酒肆技能") → findPic("PK-酒肆-休息")
                self._do_tap("酒肆", 775, 80)
                time.sleep(random.uniform(0.8, 1.2))
                self._do_tap("酒肆休息", 540, 960)
            time.sleep(random.uniform(0.8, 1.2))
            self._check_xue_lan(try_t)

    def _detect_xue_lan_percent(self, frame):
        """血蓝百分比检测（参照原版 detectXueLanPercent）
        
        原版算法:
          HP: x∈[756,799], y=6, 条件 R>200, 34<G<98, B<65, 每像素+=2.38
          MP: x∈[756,799], y=14, 条件 10<R<87, 120<G<175, B>205, 每像素+=2.38
          BB: x∈[654,697], y=6, 同上HP条件, 每像素+=2.38
          先检测是否"没带宝宝" (findPic("没带宝宝") is None → isHasBB=True)
        """
        xue_percent = 0.0
        lan_percent = 0.0
        bb_xue_percent = 0.0

        if frame is None:
            return (100, 100, 100)

        try:
            h, w = frame.shape[:2]

            # 人物血量扫描
            for x in range(756, min(799, w)):
                r, g, b = get_color(frame, x, 6)
                if r > 200 and 34 < g < 98 and b < 65:
                    xue_percent += 2.38

            # 人物蓝量扫描
            for x in range(756, min(799, w)):
                r, g, b = get_color(frame, x, 14)
                if 87 > r > 10 and 120 < g < 175 and b > 205:
                    lan_percent += 2.38

            # 宝宝血量扫描（原版: isHasBB = findPic("没带宝宝") is None）
            # [TODO: 模板资源] 需要"没带宝宝"模板来检测是否有宝宝
            bb_xue_percent = 101  # 原版: 没宝宝时 = 101
            # 如果有宝宝:
            # for x in range(654, min(697, w)):
            #     r, g, b = get_color(frame, x, 6)
            #     if r > 200 and 34 < g < 98 and b < 65:
            #         bb_xue_percent += 2.38

        except Exception as e:
            self._log(f"血蓝检测异常: {e}")

        return (xue_percent, lan_percent, bb_xue_percent)

    # ================================================================
    # 巫医检查 - 参照原版 checkWuYi (896字节)
    # ================================================================

    def _check_wuyi(self, area):
        """巫医检查（参照原版 checkWuYi）
        
        原版完整流程:
          1. 检测"没带宝宝" 和 "小猫-召唤兽忠诚度"
          2. isNeedWuYiColor 确认颜色
          3. 打开背包 → 双击"摄妖香" → 关闭背包
          4. 根据地图找到NPC对话"我要同时补满召唤兽"
          5. 打开背包 → 双击"洞冥草" → 关闭背包
        
        支持地图: 子母河底, 龙窟五层/六层, 凤巢四层, 麒麟山, 小西天, 
                  小雷音寺, 女娲神迹, 伊阙龙门, 须弥东界, 银华镜, 弥勒山, 丝绸之路
        """
        if not self.config.is_wuyi:
            return

        frame = self._get_frame()
        if frame is None:
            return

        # 原版: isShowMaoEnter = findPic("没带宝宝") is None and findPic("小猫-召唤兽忠诚度") is not None
        # 简化: 使用颜色检测
        if color_util.is_need_wuyi(frame):
            self._log("检测到召唤兽需要巫医治疗")

            # [TODO: 模板资源 + NPC交互模块]
            # 原版完整流程需要:
            # 1. clickOpenPkg → doubleClickProduct("摄妖香") → clickClosePkg
            # 2. 根据 area 查找 NPC 坐标并对话
            # 3. clickOpenPkg → doubleClickProduct("洞冥草") → clickClosePkg

            # 简化版: 直接点击巫医位置
            wuyi_points = {
                "丝绸之路": (540, 1700),
                "子母河底": (540, 1700),
                "龙窟五层": (540, 1700),
                "龙窟六层": (540, 1700),
                "凤巢四层": (540, 1700),
                "麒麟山": (540, 1700),
                "小西天": (540, 1700),
                "小雷音寺": (540, 1700),
                "女娲神迹": (540, 1700),
                "伊阙龙门": (540, 1700),
                "须弥东界": (540, 1700),
                "银华镜": (540, 1700),
                "弥勒山": (540, 1700),
            }
            wx, wy = wuyi_points.get(area, (540, 1700))
            self._do_tap("巫医治疗", wx, wy)
            time.sleep(random.uniform(0.5, 1.0))

    # ================================================================
    # 辅助方法
    # ================================================================

    def _get_frame(self):
        """获取当前截图，统一缩放到 1080x1920 逻辑分辨率"""
        try:
            frame = self.screenshot.capture_array()
            if frame is not None:
                # 统一缩放到逻辑分辨率，保证模板/坐标/颜色点一致
                frame = cv2.resize(frame, (_LOGIC_W, _LOGIC_H))
                self._last_frame = frame
            return frame
        except Exception:
            return self._last_frame

    def _close_pop(self):
        """关闭弹窗（参照原版 closePop）"""
        frame = self._get_frame()
        if frame is not None and color_util.is_popup_showing(frame):
            self._dismiss_popup()

    def _hide_task_channel(self):
        """隐藏任务栏和聊天频道（参照原版 hideTaskAndChanel）"""
        # 原版随机15%概率执行
        if random.random() < 0.15:
            self._do_tap("隐藏任务", 700, 50)
            time.sleep(random.uniform(0.5, 1.0))

    def _dismiss_popup(self):
        """关闭弹窗"""
        x, y = color_util.dismiss_popup_click_pos()
        self._do_tap("关闭弹窗", x, y)
        time.sleep(random.uniform(0.2, 0.4))

    def _cancel_auto_battle(self):
        """取消自动战斗（参照原版: findPic("PK-取消自动战斗")）"""
        # 原版用模板匹配找到按钮后点击
        self._do_tap("取消自动战斗", 765, 147)
        time.sleep(random.uniform(0.3, 0.5))

    def _do_tap(self, label, x, y):
        """执行点击（带随机偏移）"""
        ox = random.randint(-5, 5)
        oy = random.randint(-5, 5)
        AdbUtil.tap(self.serial, x + ox, y + oy)
