# 梦幻西游 自动打怪 控制面板

## 功能
- 🖥️ 手动选择/绑定 ADB 设备（模拟器）
- 👥 **特殊场景（队伍抓特殊）**：设备入队、分配场景与角色，设置队长后一键启动整队；
  队长=猎术号（捕捉特殊/宝宝+妙手空空），队员=防御等待队长抓完
- ⚙️ 可视化设置 HP/MP 阈值、补药方式（九转/94蓝碗/秘制/酒肆）
- 🗺️ 地图选择：小西天 / 女娲神迹
- 🃏 **妙手空空场景配置**：支持多场景勾选、环数/卡片/时间要求、后续操作（参考设置页）
- 🧠 **本地四小人识别（ONNX）**：小霸王反编译功能合并，CNN 本地识别，失败自动降级图灵云 API
- 🗺️ **真实切场导航**：小霸王 `goToMapAction` 66 区域分支（飞行符/飞行旗/驿站/NPC 对话链）
- 🎒 **背包环/卡计数**：定时“偷偷检查背包”，20 格快照 diff 新增物品，模板匹配累计环/卡，达标自动切场
- 📊 实时 HP/MP/BB 数据显示
- 📋 实时运行日志
- 💾 配置自动保存

> 注意：当前仅 **小西天** 逻辑已完善，其他场景（龙窟五层、凤巢四层、子母河底、小雷音寺、女娲神迹、须弥东界等）已在 UI 中预留配置，运行时会提示跳过。

## 环境要求

### 1. Python 3.8+
### 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：`opencv-python`、`numpy`、`adbutils`、`pyscrcpy`、`ttkbootstrap`。

> 小霸王三功能合并包（`xbw_features/`）额外依赖 `onnxruntime`（本地四小人
> ONNX 推理）与 `loguru`（日志）；项目 `.venv` 已内置两者。

> 如果 pyscrcpy 安装失败，可跳过，程序会自动回退到 ADB 截图模式。

### 3. ADB 工具

确保 `adb` 在系统 PATH 中，或安装 `adbutils` 后自动检测。

## 使用步骤

### 1. 游戏准备
- 在游戏快捷栏设置：**F1=九转**、**F2=94蓝碗**、**F5=秘制**
- 角色站在目标地图（小西天或女娲神迹）

### 2. 启动程序
```bash
# 方式一：双击 run.bat
# 方式二：命令行
cd D:\mhxy-auto-fight
python 小西天自动打怪_GUI.py
```

### 3. 操作流程
1. 选择设备 → 点击 **绑定窗口**
2. 设置 HP/MP 补给方式（九转/94蓝碗/秘制/酒肆）和阈值
3. 点击 **妙手空空场景设置**，勾选要运行的场景并设置条件
4. 选择地图（小西天/女娲神迹）
5. 勾选战斗操作（妙手空空、逃跑、自动寻路等）
   - **本地四小人识别**：勾选后四小人界面优先用 ONNX 本地识别
   - **背包环/卡计数**：勾选后每隔 550~700 秒自动检查背包，累计环/卡达标切场
   - **真实切场导航**：勾选后切场时用小霸王 goToMapAction 真实跑图
6. 设置战后酒肆恢复阈值
7. 点击 **▶ 启动**

### 特殊场景（队伍）页

主界面第 2 个 tab「特殊场景」：

1. 「刷新设备」列出 ADB 设备；
2. 勾选要入队的设备，每台分配 **场景**（引擎已支持的 9 个地图）与 **角色**
   （队长-猎术号抓 / 队员-防御）；
3. 点「▶ 一键启动队伍」按 队长→队员 顺序启动（每台设备按自己场景执行抓捕逻辑）；
4. 「⏹ 停止队伍」统一停止；队伍配置自动保存到 `special_team_config.json`。

> 不同场景的抓捕目标/模板来自 `target_mapping`（MAP_CONFIG），
> 队员强制 防御后自动战斗、关闭捕捉与妙手空空。

## 项目结构

```
mhxy-auto-fight/
├── 小西天自动打怪_GUI.py    # 新版 UI 主程序
├── mhxy_engine.py            # 自动化引擎（原脚本核心逻辑）
├── xbw_features/             # 小霸王三功能合并包（本地四小人/切换场/背包计数）
│   ├── four_person/          # ONNX 四小人检测器（subor.onnx）
│   ├── game_action/          # goToMapAction 66 区域分支 + 67/7 地图参数
│   ├── common/util/          # findPic/色点/背包 20 格/位置识别等工具
│   ├── threads/dk_changjing.py # 背包环/卡计数 + 切场条件（函数版）
│   └── tests/test_smoke.py   # 冒烟测试（不依赖真机）
├── run.bat                   # 一键启动脚本
├── requirements.txt          # 依赖列表
├── gui_config.json           # 配置文件（自动生成）
├── README.md
├── image/                    # 模板图片（294 个 UI/怪物模板）
└── images/                   # 辅助图片
```

## 小霸王三功能（反编译合并）说明

三个功能反编译自安装版“小霸王”并整理合并进本工程，位于 `xbw_features/`：

| 功能 | 关键文件 | 实现 |
| --- | --- | --- |
| 本地四小人识别 | `four_person/detector.py`、`common/util/cnn_util.py` | ONNX CNN（`_internal/subor.onnx`，90x90 输入），ROI 切 4 个 90 宽槽位推理，概率 >0.8 点最高槽位；`isShowFourPerson`/`findFourPersonDetectArea` 判定界面与区域，失败降级图灵云 API |
| 切换场 | `game_action/map_action.py`、`threads/dk_changjing.py` | `goToMapAction` 66 区域分支 + 67 点卡/7 畅玩地图参数；`goToPositionAction` 走图、`_feiXingQi` 飞旗；触发条件=时间满或环/卡达标 |
| 行囊环/卡计数 | `threads/dk_changjing.py`、`common/util/color_util.py` | 20 格（5x4）网格 + 对角线取色判占用 → 与上次快照 diff 新增槽位 → 逐个点击 → 模板匹配“装备条件”（环）/"怪物卡片"（卡）累计 → 达标切场 |

I/O 全部走 `xbw_features/backend.py`（默认 ADB，引擎运行时自动注入自身截图/点击）。
独立冒烟测试：`.venv\Scripts\python.exe xbw_features\tests\test_smoke.py`
