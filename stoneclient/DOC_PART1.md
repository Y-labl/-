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

