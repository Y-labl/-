# 🪨 小石头系统 (stoneclient) — 完整开发文档

> **版本**: AppVersion 41 | **编译时间**: 2026-07-01 | **测试账号**: 13800138000 / test123456
> **反编译**: uncompyle6 3.9.3 / pycdc / 手工重建 | **源码**: Python 3.8 bytecode → source

---

## 1. 项目概览

**小石头系统 (stoneclient)** 是一个基于 PyQt5 的 Windows 桌面游戏自动化工具。
核心功能是在指定时间（每天 12:00 和 20:00）通过模拟器（逍遥/雷电）自动抢购游戏内"晶石"道具，
同时提供自动喊话、绿通抢购、梦幻互通修复等辅助功能。

### 核心能力

| 功能 | 描述 |
|------|------|
| 用户登录 | 手机号 + 密码登录，支持 UUID 绑定、版本检测、自动更新 |
| 模拟器管理 | 自动检测逍遥/雷电模拟器窗口，最多 12 窗口并发 |
| 定时抢购 | 每天 12:00 / 20:00 自动兑换功勋 + 抢购晶石 |
| 像素颜色识别 | 特定像素 RGB 阈值判断晶石存在/价格(120/140)/弹窗 |
| 后台鼠标模拟 | Win32 PostMessage 后台点击，不干扰前台操作 |
| 余额管理 | REST API + MySQL 持久化用户余额/充值记录 |
| 自动喊话 | 定时向游戏窗口发送文字消息（聊天/推广） |
| 绿通抢购 | 模拟点击绿通按钮并检测结果 |
| 日志系统 | 本地日志 + 远程上传石头记录 |
| 自动更新 | 版本检测 + stoneUpdater.exe 在线升级 |
| 工具箱 | 自动喊话窗口、梦幻互通修复、背包操作、解锁等 |

### 技术栈

| 层级 | 技术 |
|------|------|
| UI 框架 | PyQt5 (Qt 5) |
| 编程语言 | Python 3.8 (反编译自 bytecode) |
| 网络请求 | requests 库 |
| Windows API | win32gui, win32api, win32con (pywin32) |
| 硬件信息 | psutil, pynvml (NVIDIA GPU) |
| 配置存储 | QSettings (INI 文件) |
| 后端通信 | REST API → Flask mock / Express.js → MySQL |
| 打包分发 | PyInstaller (stone.exe + stoneUpdater.exe) |

---

## 2. 架构设计

### 整体架构

```
run.py (入口)
  └─ QApplication + LoginWin (340×240)
       └─ 登录成功 → IndexWindow (主窗口, 750×520)
            ├─ initClockTimer (30s 间隔) 校准系统时钟
            ├─ clockTimer (100ms 间隔) 时钟显示
            ├─ findstone_thread × N (最多 12) 抢购线程
            ├─ robot_thread × N (最多 10) 辅助线程
            │    ├─ startMhRepair   启动梦幻互通 + 修复
            │    ├─ enterMh         进入游戏
            │    ├─ openClock       解锁
            │    ├─ openGx          调出兑换功勋
            │    ├─ openPackage     打开/关闭背包
            │    └─ lvtongClick     绿通点击
            └─ REST API 调用 (登录/用户/余额/日志)
                 │
                 ├─ mouse_util.py     Win32 PostMessage 点击
                 ├─ color_util.py     RGB 阈值颜色检测
                 ├─ vmdiff_util.py    逍遥/雷电坐标差异适配
                 ├─ time_util.py      时间校准(sysTDur)
                 └─ computer_util.py  CPU/GPU/内存/网络检测
```

### 线程模型

| 变量 | 类 | 最大数量 | 用途 |
|------|-----|---------|------|
| thread1~12 | FindStoneThread | 12 | 每个模拟器窗口一个抢购线程 |
| robotThread1~10 | RobotThread | 10 | 维修/进游戏/喊话/绿通 |

所有线程共享同一个 `mouseUtil` 单例 (`mouse_util.py` 全局变量)。
`FindStoneThread` 和 `RobotThread` 通过 `pyqtSignal` 与主 UI 线程通信。

### 时间校准机制

系统通过拼多多 API (`api.pinduoduo.com/api/server/_stm`) 获取服务器时间进行校准：

1. `initClock()` 请求拼多多时间接口，记录请求耗时 (apm)
2. 若 apm < 30ms 则采纳，计算本地系统时间与服务器时间差值 (`sysTDur`)
3. 所有时间调用通过 `time_util.getNow()` → `datetime.now() - timedelta(milliseconds=sysTDur)`
4. `initClockTimer` 每 30 秒重新校准一次

---

## 3. 模块清单

### 3.1 入口与窗口

| 文件 | 行数 | 职责 |
|------|------|------|
| `run.py` | 13 | 应用入口，异常钩子，启动 LoginWin |
| `login.py` | ~260 | 登录窗口 UI + 版本检测 + 自动更新 |
| `index.py` | ~718 | 主窗口 UI + 核心调度逻辑 |
| `more_setting.py` | ~160 | 更多设置子窗口（抢购时间/模式/功勋时间） |
| `more_userinfo.py` | ~80 | 用户余额记录子窗口 |

### 3.2 线程模块

| 文件 | 行数 | 职责 |
|------|------|------|
| `findstone_thread.py` | ~190 | 抢购线程：定时唤醒→颜色识别→点击购买 |
| `robot_thread.py` | ~160 | 辅助线程：6 种模式（维修/进游戏/解锁/功勋/背包/绿通） |

### 3.3 工具模块

| 文件 | 行数 | 职责 |
|------|------|------|
| `mouse_util.py` | ~50 | Win32 PostMessage 点击封装 |
| `color_util.py` | ~120 | RGB 颜色检测：晶石/价格/弹窗 |
| `const.py` | ~50 | 所有常量：API 端点、坐标点、枚举值 |
| `vmdiff_util.py` | ~30 | 逍遥 vs 雷电坐标偏移适配 |
| `time_util.py` | ~10 | 全局时间偏移校准 |
| `stone_util.py` | ~20 | Toast 通知 + QSettings 配置 |
| `computer_util.py` | ~80 | CPU/GPU/内存/网络检测 |
| `user.py` | ~15 | User 数据类（字典→对象） |
| `vm.py` | ~10 | VM 数据类（模拟器窗口描述） |

### 3.4 UI 组件

| 文件 | 行数 | 职责 |
|------|------|------|
| `userinfo_balance_item.py` | ~110 | 余额列表项自定义 UI 组件 |
| `balance_record.py` | ~30 | BalanceRecord 数据类 + JSON 反序列化 |
| `tools/tall/tall.py` | ~140 | 自动喊话窗口：窗口枚举+定时发送 |

### 3.5 后端/模拟服务器

| 文件 | 行数 | 职责 |
|------|------|------|
| `mock_server.py` | ~250 | Flask Mock API（登录/用户/余额/日志） |

### 3.6 外部可执行文件

| 文件 | 大小 | 用途 |
|------|------|------|
| `stone.exe` | ~2 MB | 主程序 PyInstaller 打包 |
| `stoneUpdater.exe` | ~1 MB | 自动更新程序（单独打包） |


## 4. 模块详细说明（按文件）

### 4.1 run.py — 应用入口

```python
import sys, traceback, os
from PyQt5.QtWidgets import QApplication

def log_exception(exc_type, exc_value, exc_tb):
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_tb)
sys.excepthook = log_exception

from login import LoginWin
os.chdir(os.path.dirname(os.path.abspath(__file__)))
app = QApplication(sys.argv)
win = LoginWin(); win.show()
sys.exit(app.exec_())
```

**设计要点**：
- 全局异常钩子 `sys.excepthook` → 写入 `crash_log.txt`，避免静默崩溃
- `os.chdir` 确保工作目录始终为 exe 所在目录（相对路径 `config.ini`/`api_debug.log` 依赖）
- 标准 PyQt5 应用生命周期

---

### 4.2 login.py — 登录窗口

**LoginWin** (QMainWindow, 340×240)

**UI 布局**：
| 控件 | 类型 | 说明 |
|------|------|------|
| 手机号输入框 | QLineEdit | 正则 `^1[3-9]\\d{9}$` 校验 |
| 密码输入框 | QLineEdit | 正则 `[0-9A-Za-z]{8,16}` 校验 |
| 登录按钮 | QPushButton | 触发 `clickLogin()` |

**关键流程**：

```
__init__()
  ├─ 从 app_data(QSettings) 回填 phone/password
  ├─ 显示 "版本检测中..." → initVersion()
  └─ 绑定 updateVersionCheckSignal

initVersion()
  └─ 显示 "版本:41 (本地测试)"（mock_server 模式下跳过远程版本检测）

clickLogin()
  ├─ 校验手机号(11位) / 密码(≥6位)
  ├─ 获取 UUID: wmic csproduct get uuid → 取后 8 字符
  ├─ POST /users/login {phone, password, version, uuid}
  ├─ 成功 → 保存 phone/password/token → 创建 IndexWindow → close()
  └─ 失败 → toast 提示错误
```

**自动更新机制** (`startDownload`)：
- 下载 URL → 本地临时文件 → 启动 `stoneUpdater.exe` → `app.quit()`
- `stoneUpdater.exe` 负责解压覆盖 + 重启主程序

---

### 4.3 index.py — 主窗口

**IndexWindow** (QMainWindow, 750×520)

**UI 结构**：
```
QMainWindow
  ├─ MenuBar
  │    ├─ 工具箱: 自动喊话 / 12点抢绿通 / 20点抢绿通
  │    ├─ 便捷操作: 打开互通修复 / 进入游戏 / 解锁 / 兑换功勋 / 自动启动
  │    └─ 测试: 背包操作 / Ping
  └─ main_layout (QHBoxLayout)
       ├─ console_mine_widget (左: 1/4)
       │    ├─ 模拟器列表 (QGridLayout: 4×3 QPushButton)
       │    ├─ 手机号 / 余额显示
       │    ├─ 总共抢到 / 失败计数
       │    └─ 刷新 / 更多设置 / 我的记录 按钮
       └─ setting_log_widget (右: 3/4)
            ├─ 当前设置标签
            └─ 日志区域 (QScrollArea + QLabel)
```

**核心属性**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| thread1~12 | FindStoneThread | None | 最多 12 个抢购线程 |
| robotThread1~10 | RobotThread | None | 最多 10 个辅助线程 |
| buyTime | str | BuyTime1("110ms") | 抢购间隔 |
| buyType | str | Buy120("只抢120") | 都抢/只抢120/智能抢 |
| gxTimeMs | int | 930 | 功勋点击毫秒位(910-979) |
| mBanlance | int | 0 | 当前用户余额 |
| fightStoneSuccCount | int | 0 | 成功计数 |
| fightStoneFailCount | int | 0 | 失败计数 |
| vms | list[VM] | [] | 所有检测到的模拟器 |
| openMhVms | list | [] | 已打开的互通窗口 |

**时钟与核心循环**：

| 定时器 | 间隔 | 回调 |
|--------|------|------|
| initClockTimer | 30s | initClock() 时间校准 |
| clockTimer | 100ms | clockOperate() 更新时钟显示 |

**关键方法**：

| 方法 | 触发方式 | 功能 |
|------|----------|------|
| `initClock()` | 启动 + 30s 定时 | 拼多多 API 校时, 计算 sysTDur |
| `refreshUserInfo()` | 启动 + 手动刷新 | 获取余额/手机号, 若 <5 提示充值 |
| `checkBalance()` | 抢购前 | 刷新余额, 余额不足自动充值 |
| `reduceBalance()` | 扣款 | 调用 API 扣减余额并记录 |
| `startFindStone()` | 按钮点击 | 检测窗口 → 创建 FindStoneThread → start() |
| `initClockAPM()` | 自动 | 自动选择最优 apm(响应时间) |

---

### 4.4 findstone_thread.py — 抢购线程

**FindStoneThread** (QThread)

**信号**：
- `fail_res_signal` — 抢购失败
- `succ_res_signal` — 抢购成功
- `log_signal(str)` — 日志输出

**初始化参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| vm | VM | 模拟器信息(parent hwnd, child hwnd, type, name) |
| buyTime | str | "110ms" 或 "150ms" |
| buyType | str | 都抢/只抢120/智能抢 |
| gxTimeMs | int | 功勋点击毫秒(930) |

**执行流程** (`run()`)：

```
run()
  ├─ 计算距离开抢时间差 → sleep 等待
  ├─ 点击"兑换功勋"按钮 (vmdiff 坐标适配)
  └─ 扫描 20 个晶石点位 (stonePointList)
       ├─ isStone(img, point) → 有晶石
       │    ├─ buyType=都抢 → 直接购买
       │    ├─ buyType=只抢120 → is120PointCount() → 120则买
       │    └─ buyType=智能抢 → 1个晶石直接买, 2个以上挑120
       ├─ isResultPopShow() → 检测结果弹窗 → 失败计数++ / 成功计数++
       └─ 循环直到超时(perStoneSend 秒)
```

**时间线**：
| 关键时间 | 计算方式 |
|----------|----------|
| 功勋点击 | `GxTimePre(" 11:59:59.") + gxTimeMs + "Z"` |
| 抢购超时 | `startFindT + perStoneSend` (约 5 秒) |
| 点击间隔 | buyTime(110ms/150ms) |

**颜色识别细节** (`color_util.py`)：

| 函数 | 方法 |
|------|------|
| `isStone(img, point)` | 检查该点像素 RGB 是否为晶石颜色 |
| `isStoneText(img)` | 检查特定 6 个像素点是否为晶石文字颜色 |
| `is120PointCount(img)` | 检查 7 个点判断价格是否为 120 |
| `isResultPopShow(img)` | 检查 8 个点判断结果弹窗是否存在 |

**坐标差异适配** (`vmdiff_util.py`)：

| 常量 | 逍遥(VmXiaoyao) | 雷电(VmLeidian) |
|------|----------------|----------------|
| 窗口类名 | Qt5QWindowIcon | LDPlayerMainFrame |
| VmPointOffset | QPoint(0, -2) | QPoint(0, 0) |
| VmGxPoint | QPoint(680, 235) | QPoint(680, 204) |
| VmBuyPoint | QPoint(580, 435) | QPoint(580, 404) |

---

### 4.5 robot_thread.py — 辅助线程

**RobotThread** (QThread)

**模式枚举** (`type` 参数)：

| type | 方法 | 功能 |
|------|------|------|
| "startMhRepair" | `startMhRepair()` | 启动梦幻互通并修复：点击(127,160)→(32,140)→等待 |
| "enterMh" | `enterMh()` | 进入游戏：点击(131,40)→等待→检测弹窗 |
| "openClock" | `openClock()` | 解锁：输入密码"1111"→回车 |
| "openGx" | `openGx()` | 调出兑换功勋界面(杨戬)→点击NPC→对话框 |
| "openPackage" | `openPackage()` | Alt+E 打开/关闭背包 |
| "lvtongClick" | `lvtongClick()` | 绿通抢购：等待→点击→检测结果→循环 |

**点击实现**：使用 Win32 `PostMessage(WM_CHAR)` 模拟键盘输入

---

### 4.6 tools/tall/tall.py — 自动喊话窗口

**TallWin** (QMainWindow, 340×700)

**配置**：
| 字段 | 默认值 |
|------|--------|
| 喊话内容 | "神器任务抢晶石交流群++++++++++++++++++++++++++++++++++++" |
| 推广内容 | "326646683这是微+后邀请进群" |
| 喊话频率 | 9 秒 |

**工作流程**：
1. 点击"刷新窗口" → `EnumWindows` 枚举所有 `WSGAME` 类窗口
2. 每个窗口生成一行 UI: [窗口名] [启动] [停止] [推广]
3. 启动 → QTimer 定时调用 `dotall()` → `PostMessage(WM_CHAR)` 逐字发送
4. 推广 → `PostMessage(WM_CHAR)` 发送一次推广内容

---

### 4.7 more_setting.py — 更多设置窗口

**MoreSettingWin** (QMainWindow, 480×750)

**配置项**：
- **商品时长**: 110ms / 150ms（`BuyTime1` / `BuyTime2`）
- **抢购模式**: 都抢 / 只抢120 / 智能抢
- **功勋点击时间**: 11:59:59.xxx ms (910-979，默认 930)

**信号**：通过 `pyqtSignal` 将变更实时同步到主窗口 (`buytype_signal`, `buytime_signal`, `gxtimems_signal`)

---

### 4.8 more_userinfo.py — 余额记录窗口

**MoreUserInfoWin** (QMainWindow, 480×750)

**功能**：
- API 获取 `/balancerecords/mylist` → 最近 50 条余额记录
- 每条记录显示为 `UserInfoBalanceItem`（自定义 QListWidgetItem）
- 标题汇总: "总计充值 X 小石头, 抢到了 Y 个"

---

### 4.9 mouse_util.py — 鼠标模拟

**MouseUtil 单例** (`mouseUtil`)

```python
def click(hwnd, mouseInfo: MouseInfo):
    if win32gui.IsWindow(hwnd):
        position = win32api.MAKELONG(pt.x(), pt.y())
        win32api.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, position)
        win32api.PostMessage(hwnd, WM_LBUTTONUP, MK_LBUTTON, position)
    # doubleClick 同上, 中间加 0.1s sleep
```

**核心特点**：
- 使用 `PostMessage` 而非 `SendMessage` → 异步投递，不等待处理
- `MAKELONG(x, y)` 将坐标打包为 LPARAM
- **后台点击**：即使模拟器窗口最小化/被遮挡，点击仍然生效
- 每次点击发射 `mouse_log_singal` 用于日志显示

---

### 4.10 computer_util.py — 硬件信息检测

**computerInfo()** 返回格式化字符串包含：
- **CPU**: 名称(py), 核心数, 使用率
- **GPU** (NVIDIA): 名称, 数量, 显存总量/已用/剩余
- **内存**: 总量, 使用率, 已用

**ping(host)**：调用系统 ping 命令检测网络连通性

---

### 4.11 const.py — 常量定义

**API 端点**：
```
API_HOST = "http://127.0.0.1:3000"
API_LOGIN            = "/users/login"
API_USERINFO         = "/users/userinfo"
API_REDUCEBALANCE    = "/users/reducebalance"
API_MYBALANCE_LIST   = "/balancerecords/mylist"
API_ISCHARGED        = "/balancerecords/chargecount"
API_STONELOG         = "/stonelog/log"
```

**晶石检测坐标**：
- `stonePointList`: 20 个点位 (4 列 × 5 行)
- `stoneTextPointList`: 6 个点位（晶石文字检测）
- `pointList120_5or6`: 7 个点位（价格 120 检测）
- `resultPopShowPoints`: 8 个点位（结果弹窗检测）
- `lvtongResultPopShowPoints`: 8 个点位（绿通结果检测）
- `lvtongTextPointList`: 6 个点位（绿通文字检测）

**枚举值**：
| 常量 | 值 | 说明 |
|------|-----|------|
| VmXiaoyao | "Qt5QWindowIcon" | 逍遥模拟器窗口类 |
| VmLeidian | "LDPlayerMainFrame" | 雷电模拟器窗口类 |
| BuyTime1 | "110ms" | 短间隔抢购 |
| BuyTime2 | "150ms" | 长间隔抢购 |
| AppVersion | 41 | 当前版本号 |
| PerStoneBalance | 1 | 每颗晶石消耗余额 |

**关键时间点**（相对于日期的字符串）：
```
AutoStartTime  = " 11:55:00.000Z"   # 自动启动
GxTimePre      = " 11:59:59."      # 功勋时间前缀
CountDownTime  = " 11:59:30.000Z"  # 倒计时
LastDealTime   = " 12:00:10.500Z"  # 最后交易时间
LvtongTime12   = " 11:59:59.970Z"  # 12点绿通
LvtongTime20   = " 19:59:59.970Z"  # 20点绿通
```

---

### 4.12 mock_server.py — 模拟后端 API

Flask 应用，监听 `0.0.0.0:3000`，提供完整 REST API：

**数据库**: SQLite (`stoneclient.db`)
- 表 `users`: id, phone, password, token, balance, uuid, version, created_at
- 表 `balance_records`: id, user_id, balance, type, wincount, buytype, rmb, userbalance, created_at
- 表 `charge_records`: id, user_id, amount, created_at
- 表 `stone_logs`: id, user_id, buy_type, result, stone_count, created_at

**API 列表**：
| 方法 | 路由 | 功能 |
|------|------|------|
| POST | /users/login | 登录，校验 uuid/version，返回 token |
| GET | /users/userinfo | 获取用户信息（余额/手机号） |
| POST | /users/reducebalance | 扣减余额 + 写记录 |
| GET | /balancerecords/mylist | 最近 50 条余额记录 |
| GET | /balancerecords/chargecount | 充值次数统计 |
| POST | /stonelog/log | 上传抢石头日志 |

**认证方式**: Bearer Token（`/users/login` 返回，存储于 `config.ini`）

---

### 4.13 配置存储 (config.ini)

通过 `QSettings("config.ini", QSettings.IniFormat)` 读写，文件位于 exe 同目录：

| Key | 类型 | 说明 |
|-----|------|------|
| phone | str | 登录手机号（自动回填） |
| password | str | 登录密码（自动回填） |
| token | str | Bearer token，API 认证 |
| buyTime | str | "110ms" 或 "150ms" |
| buyType | str | "都抢" / "只抢120" / "智能抢" |
| gxTimeMs | int | 910-979，功勋点击毫秒 |
| waitReduceBanlance | int | 待扣减余额，重启后自动处理 |


## 5. REST API 参考

基础 URL: `http://127.0.0.1:3000` (可在 `const.py` 中修改 `API_HOST`)

### 5.1 POST /users/login

**请求体**：
```json
{
  "phone": "13800138000",
  "password": "test123456",
  "version": 41,
  "uuid": "ABCDEF01"
}
```

**成功响应**：
```json
{
  "status": "success",
  "obj": { "id": 1, "phone": "13800138000", "balance": 100, "token": "eyJ...", "version": 41 }
}
```

**逻辑**：校验 phone+password、uuid 硬件绑定、version 强制更新检查

### 5.2 GET /users/userinfo

**Headers**: `Authorization: Bearer <token>`

### 5.3 POST /users/reducebalance

**请求体**：
```json
{ "rmb": 10.0, "balance": -15, "buytype": "只抢120", "wincount": 3 }
```

更新 `users.balance`, 插入 `balance_records` + `stone_logs`

### 5.4 GET /balancerecords/mylist
返回最近 50 条余额记录, 按时间倒序

### 5.5 GET /balancerecords/chargecount
返回当前用户充值次数: `{"status":"success","count":5}`

### 5.6 POST /stonelog/log
上传抢石头日志

---

## 6. 数据库设计

### users
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| phone | TEXT UNIQUE | 手机号 |
| password | TEXT | 密码 |
| token | TEXT | Bearer token |
| balance | INTEGER | 余额(小石头) |
| uuid | TEXT | 硬件 UUID |
| version | INTEGER | 客户端版本 |
| created_at | TEXT | 创建时间 |

### balance_records
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| user_id | INTEGER FK | 用户 ID |
| balance | INTEGER | 变动量(正=充值/负=扣减) |
| type | INTEGER | 0=充值 / 1=新用户 / 2=推广 / 3=其他 |
| wincount | INTEGER | 抢到数量 |
| buytype | TEXT | 抢购模式 |
| rmb | REAL | 人民币金额 |
| userbalance | INTEGER | 变动后余额 |
| created_at | TEXT | 记录时间 |

### stone_logs
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| user_id | INTEGER FK | 用户 ID |
| buy_type | TEXT | 抢购模式 |
| result | INTEGER | 1=扣减成功 |
| stone_count | INTEGER | 晶石数量 |
| created_at | TEXT | 记录时间 |

---

## 7. 部署与运行

### 开发环境

```
pip install PyQt5 requests psutil pynvml pywin32 flask flask-cors pyqt-toast
python mock_server.py    # 终端1: 启动后端
python run.py            # 终端2: 启动客户端
```

### 生产目录结构

```
stone.exe
stoneUpdater/
  stoneUpdater.exe
  python38.dll
  base_library.zip
  libcrypto-1_1.dll
  libssl-1_1.dll
config.ini          (自动生成)
api_debug.log       (自动生成)
```

### 首次配置步骤
1. 启动 mock_server.py 或 Express.js 后端
2. 运行 run.py → 登录界面
3. 输入测试账号 13800138000 / test123456
4. 点击主界面模拟器按钮 → 自动检测模拟器窗口
5. 打开模拟器中游戏道具商店界面
6. 设置抢购时间/模式 (更多设置)
7. 等待 12:00 / 20:00 自动执行

---

## 8. 常见问题

**Q: 登录提示版本过低**
修改 `const.py` 中 `AppVersion` 或 mock_server `forceVersion`

**Q: 点击启动没反应**
检查模拟器窗口类名(逍遥=Qt5QWindowIcon / 雷电=LDPlayerMainFrame); 检查 token 有效性; 检查 api_debug.log

**Q: 提示没有晶石**
检查 stonePointList 坐标匹配模拟器分辨率; 调整 color_util.py RGB 阈值; 模拟器缩放率需 100%

**Q: 左下角乱码**
确保 config.ini 编码为 UTF-8 without BOM; QSettings.setIniCodec("UTF-8")

**Q: 只抢到 140 价格的晶石**
调整 pointList120_5or6 坐标或切换"都抢"模式测试

**Q: 登录没反应**
检查 mock_server 是否运行(端口3000); 查看 api_debug.log / crash_log.txt

---

## 9. 反编译备注

| 工具 | 版本 | 用途 |
|------|------|------|
| uncompyle6 | 3.9.3 | Python 3.8 bytecode → .py |
| pycdc | - | 辅助反编译 |

**手工修复项**：
- index.py 中 qt_resource_data/name/struct 为 PyQt5 rcc 编译的图标资源，保持原样
- login.py clickLogin 存在两个版本，以第一个为准
- config.ini 中文需 UTF-8 编码

**反编译文件元信息**：
| 文件 | 编译时间 | 原始大小 |
|------|----------|----------|
| login.py | 2026-07-01 07:28:36 | 6726 bytes |
| index.py | 2026-07-01 07:29:31 | 25423 bytes |
| more_setting.py | 2026-07-01 07:29:31 | 3533 bytes |

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 41 | 2026-07-01 | 反编译重构 + 文档化 |

---

*文档生成时间: 2026-07-01 | 基于 uncompyle6 反编译结果 + 手工整理*


