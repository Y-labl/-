# 点卡场景自动化工具 v4

基于小霸王 v2.4 反编译 v2 完整逆向工程重构的丝绸之路挂机工具。

## 对比原版功能状态

### 已实现
- ADB 设备扫描 + 效卫投屏窗口截图 (PrintWindow)
- 颜色检测: 战斗状态、弹窗、四小人、护佑/暴击文字
- 像素扫描血蓝检测 (HP/MP/BB, 2.38%/px)
- 战斗操作: 自动/技能/普攻/防御/逃跑/捕捉/偷窃 (坐标点击)
- 巫医自动治疗 (简化版)
- 丝绸之路自动导航 (简化版)
- 血蓝自动补充 (秘制/红碗/蓝碗/酒肆, 含重试)
- PK 模式五选一互斥

### 与原版的差异 (需要模板图片资源)
| 功能 | 原版 | 新项目 | 状态 |
|------|------|--------|------|
| 截图方式 | pyscrcpy 实时流 | win32gui PrintWindow | 可用 |
| 战斗检测 | findPic 模板匹配 | 颜色检测 | 可用 |
| 捕捉宝宝 | findSideTargetPoints + 模板 | 坐标点击 | 简化 |
| 偷窃道具 | getTouTargetImgName + findPics | 坐标点击 | 简化 |
| 技能攻击 | getJiNengTargetImgName + findSideTargetPoints | 坐标点击 | 简化 |
| 巫医治疗 | findNpcAndClickLogic + 多地图NPC | 固定坐标点击 | 简化 |
| 地图导航 | randomClickMap_CiChouZhiLu + goToMapAction | 随机坐标点击 | 简化 |
| 后排宝宝检测 | findHouPaiBaoBao (scrcpy 拖动) | 未实现 | 缺失 |
| 偷窃溢出检查 | toutouDoOverCheck | 未实现 | 缺失 |
| 背包操作 | clickOpenPkg/doubleClickProduct | 未实现 | 缺失 |
| 多地图支持 | 12+ 地图区域识别 | 仅丝绸之路 | 缺失 |

### 配置对比
| 字段 | 原版 | 新项目 |
|------|------|--------|
| roleAddXueMode | ✅ 秘制/红碗/酒肆 | ✅ 一致 |
| roleAddLanMode | ✅ 秘制/蓝碗/酒肆 | ✅ 一致 |
| roleXuePercent | ✅ 默认30 | ✅ 一致 |
| roleLanPercent | ✅ 默认30 | ✅ 一致 |
| isZhua | ✅ | ✅ 一致 |
| isTou | ✅ | ✅ 一致 |
| isPkJiNeng | ✅ | ✅ 一致 |
| isPkPuGong | ✅ | ✅ 一致 |
| isPkFangYu | ✅ | ✅ 一致 |
| isPkAuto | ✅ 默认False | ⚠️ 默认True |
| isPkTaoPao | ✅ | ✅ 一致 |
| isDuiZhang | ✅ 默认True | ✅ 一致 |
| isWuYi | ❌ 原版无此配置 | ➕ 新增开关 |

## 目录
```
dk_changjing/
├── main.py              # 入口
├── 启动工具.bat/vbs      # 启动脚本
├── ui/main_window.py    # PySide6 GUI
├── core/
│   ├── adb_util.py      # ADB控制
│   ├── screenshot.py    # PrintWindow截图
│   ├── click_util.py    # 随机偏移点击
│   ├── img_util.py      # OpenCV模板匹配
│   ├── color_util.py    # 颜色/状态检测
│   ├── detect_position.py  # 游戏位置坐标常量
│   └── dk_thread.py     # 自动化状态机(v4)
├── config/dk_config.py  # 配置模型
└── output/              # 截图输出
```

## 运行
```powershell
cd D:\Program Files\mhxy-project\dk_changjing
.\启动工具.bat
```

## 依赖
复用 `小霸王\_internal`: cv2, numpy, PIL, adbutils, win32gui, PySide6

## TODO - 需要补充的模板图片资源
要完整实现原版功能，需要在 `小霸王\_internal` 或 `dk_changjing/assets/` 中放置以下模板图片:
- 战斗检测: 好友入口按钮图标
- 捕捉: 妙手空空选中目标、PK-妙手空空技能
- 偷窃: 各地图召唤兽目标模板 (PK-召唤兽-*)
- 血蓝: PK-补充气血、PK-补充魔法、PK-酒肆技能、PK-酒肆-休息
- 巫医: 没带宝宝、小猫-召唤兽忠诚度、摄妖香、洞冥草
- 导航: 打开地图、PK-取消自动战斗
