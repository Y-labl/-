# 小石头系统 逆向代码审查报告

**审查时间**: 2026-07-01
**代码来源**: D:\Program Files\mhxy\stoneclient\extracted\source_v2\
**原始文件**: D:\Program Files\mhxy\stoneclient\stone\stone.exe (PyInstaller 打包)
**反编译工具**: uncompyle6 v3.9.3 (Python 3.8.10 bytecode)

---

## 修复状态：已完成 ✅

所有 10+ 处问题已于 2026-07-01 修复。以下是修复详情。

---

## 一、项目概述

这是一个**梦幻西游游戏自动化辅助工具**（"小石头系统"），主要功能是在特定时间（如 11:59:59）通过像素识别和模拟点击，自动化抢购游戏内的"晶石"道具。支持逍遥模拟器和雷电模拟器，最多 12 开。

**技术栈**: Python 3.8 + PyQt5 + Win32 API

---

## 二、严重 Bug（会导致程序崩溃或功能完全失效）

### 1. findstone_thread.py — 4 个未定义变量（运行时 NameError）

第 74、82-83、138-139、169 行使用了 `perStoneSend`、`totalSend`、`perPriceSend`、`perPopSend` 四个变量，但在整个代码库中**从未定义**。

```python
# 第 74 行
while (datetime.now() - self.startFindT).total_seconds() < perStoneSend:  # NameError

# 第 82-83 行
if ((datetime.now() - self.startFindT).total_seconds() >= perStoneSend
        and self.curFindSend >= totalSend):  # 两个都是 NameError

# 第 138 行
curFindPriceSend += perPriceSend  # NameError

# 第 169 行
time.sleep(perPopSend)  # NameError
```

**影响**: 启动抢购后第一个线程就会抛出 NameError 崩溃。

### 2. login.py 第 192 行 — 语法错误

```python
uuid = uuid[0[:8]]  # SyntaxError: 应该是 uuid[0:8]
```

**影响**: 这是 `clickLogin` 方法中重复代码段（第 178-214 行）内的语法错误，如果执行到该分支会直接崩溃。

### 3. color_util.py — 多个函数 return 语句在循环内部（逻辑完全错误）

以下 6 个函数都存在 `return` 语句错误地放在 `for` 循环内部的问题，导致循环只执行一次就返回：

| 函数 | 行号 | 问题 |
|------|------|------|
| `isStone` | 19 | `return` 在 `for i in range(7):` 内部，只检查了 1 个像素 |
| `isStoneText` | 39-47 | `for i in range(10):` 的缩进层级错误，且 `return False` 在循环内 |
| `is120PointCount` | 70 | `return okPoint120` 在 `for point` 循环内，只检查了 1 个点 |
| `isResultPopShow` | 94 | `return False` 在 `for point` 循环内 |
| `islvtongResultPopShow` | 107 | 同上 |
| `isLvtongText` | 116-124 | 缩进层级错误，类似 `isStoneText` |

**影响**: 所有像素颜色检测功能全部失效。颜色检测是核心功能，这意味着抢购逻辑完全无法正常工作。

---

## 三、逻辑错误（程序能运行但行为不正确）

### 4. index.py 第 431 行 — 信号连接错误

```python
# 第 427-432 行，thread6 的处理中
elif index == 5:
    self.thread6 = FindStoneThread(...)
    self.thread6.fail_res_signal.connect(self.fightStoneFail)
    self.thread6.succ_res_signal.connect(self.fightStoneSucc)
    self.thread5.log_signal.connect(self.dLog)  # BUG: 应该是 self.thread6
    self.thread6.start()
```

thread6 的日志信号错误地连接到了 `self.thread5`，导致 thread6 的日志不会显示。

### 5. index.py — getMHWinList / getOpenMHWinList 逻辑反转

```python
# 第 531 行
if not (IsWindow and IsWindowEnabled and IsWindowVisible and GetClassName == VmXiaoyao):
    if GetClassName == VmXiaoyaoOtherType or GetClassName == VmLeidian:
        # 这里才添加 VM
```

这个逻辑的含义是：当窗口**不是**有效可见的 XiaoYao 窗口时，才检查是否为其他类型或雷电。结果是：**标准逍遥窗口（"Qt5QWindowIcon"）永远不会被检测到**，只有其他类型的逍遥窗口（"Qt5152QWindowIcon"）和雷电窗口（"LDPlayerMainFrame"）能被检测。

正确的逻辑应该是：
```python
if IsWindow and IsWindowEnabled and IsWindowVisible:
    if GetClassName in (VmXiaoyao, VmXiaoyaoOtherType, VmLeidian):
        # 添加 VM
```

主窗口的 `getMHWinList`（第 530-538 行）和 `getOpenMHWinList`（第 653-661 行）都有这个问题。

### 6. robot_thread.py — lvtongClick 无 sleep 的死循环

```python
# 第 118-127 行
while True:
    screen = QApplication.primaryScreen()
    img = screen.grabWindow(self.parent).toImage()
    if islvtongResultPopShow(img):
        if isLvtongText(img):
            self.lvtong_signal.emit(...)
        else:
            self.lvtong_signal.emit(...)
    else:
        time.sleep(0.2)
    # 没有 break/return，如果 popup 出现则无限高速循环
```

当检测到弹窗后，信号发出了但没有退出循环，且 `time.sleep(0.2)` 只在 else 分支中。这会导致 CPU 100% 占用。

### 7. index.py — initClock 时间计算错误

```python
# 第 297 行
apm = ((e - s) / 1000).microseconds
```

`(e - s)` 是 timedelta，除以 1000 后还是 timedelta，`.microseconds` 只取微秒部分（0-999999），而不是总毫秒数。正确写法应为：
```python
apm = (e - s).total_seconds() * 1000
```

这会导致时间同步功能失效，`sysTDur` 计算错误，进而影响所有定时任务的精度。

### 8. index.py — thread13 未在 __init__ 中声明

第 469-474 行为 index==12 创建了 `self.thread13`，但 `__init__` 中只声明了 thread1 到 thread12。虽然 Python 允许运行时添加属性，但这是不规范的，且与注释"最多12开"矛盾。

---

## 四、反编译残留问题

### 9. login.py — clickLogin 方法代码完全重复

第 128-177 行和第 178-214 行是同一段登录逻辑的两个版本：
- 第一个版本（128-177）有英文/乱码的提示信息，相对完整
- 第二个版本（178-214）有中文提示信息，但包含语法错误和损坏的代码

这说明反编译工具 uncompyle6 对这段代码的反编译出现了问题，产生了重复的输出。实际运行时只有一个版本会被执行（第一个版本在成功/失败后会 return 或 close，不会执行到第二个版本），但第二个版本中第 189 行的 `uuid[0[:8]]` 如果在某种路径下被执行会崩溃。

### 10. tools_tall_tall.py — 完全重复的文件

该文件是 `tools/tall/tall.py` 的重复副本，可能是反编译过程中产生的冗余文件。

---

## 五、功能完整性评估

| 模块 | 状态 | 说明 |
|------|------|------|
| 登录 | 部分可用 | 含重复代码和语法错误，但第一个代码分支基本可用 |
| 用户信息刷新 | 基本可用 | API 调用逻辑正确 |
| 虚拟机窗口检测 | **不可用** | 逻辑反转，无法检测标准逍遥窗口 |
| 像素颜色检测 | **不可用** | 所有检测函数的 return 都在循环内 |
| 抢晶石线程 | **不可用** | 4 个未定义变量导致 NameError |
| 鼠标模拟 | 基本可用 | PostMessage API 调用逻辑正确 |
| 时间同步 | **不可用** | 时间差计算方式错误 |
| 绿通抢购 | **不可用** | 死循环 + 颜色检测函数有问题 |
| 自动喊话 | 基本可用 | 独立功能，逻辑相对简单 |
| 设置界面 | 基本可用 | UI 交互逻辑正确 |
| 版本更新 | 未测试 | 下载功能被注释掉 |
| 日志记录 | 基本可用 | 本地日志功能正常 |

---

## 六、总结

该逆向代码存在 **10+ 处严重问题**，核心抢购功能（颜色检测、VM 检测、找晶石线程）全部存在阻塞性 bug，**原始可执行文件不可能以这种状态正常运行**。

可能的原因：
1. **反编译不完整**: uncompyle6 对部分字节码反编译失败，导致缩进错误和代码重复
2. **变量名丢失**: Python 字节码不保留局部变量名，反编译器使用了错误的变量名（如 `perStoneSend` 等可能原始名称不同）
3. **逻辑重构错误**: `not` 条件反转和 `return` 位置错误可能是字节码分支指令反编译时产生的

**建议**: 如果要修复此代码使其可运行，需要：
- 找到原始字节码中 `perStoneSend` 等变量的真实值
- 修复 `color_util.py` 中所有检测函数的循环逻辑
- 修正 `getMHWinList` 的窗口检测条件
- 修复 `initClock` 的时间计算方式
- 清理 `login.py` 的重复代码
- 修正 `lvtongClick` 的死循环

---

## 七、修复记录 (2026-07-01)

### 修复 1: findstone_thread.py — 添加缺失变量 + 修正 run() 和 find120AndBuy() 流程

根据字节码反汇编 (`findstone_thread_disasm.txt`) 还原：
- `perStoneSend = 0.05` — 每次找晶石间隔
- `perPriceSend = 0.02` — 每次价格检测间隔
- `perPopSend = 0.2` — 每次弹窗检测间隔
- `totalSend = 5` — 超时阈值（约 5 秒）

`run()` 方法重写：
- 点击功勋按钮后重置 `startFindT`
- 使用 `while True` + `break` 结构替代原来的错误逻辑
- 超时后正确 return

`find120AndBuy()` 方法重写：
- 补回了反编译丢失的「先点击晶石再检测价格」逻辑（根据反汇编 lines 623-633）
- 时间计算使用 `.total_seconds() * 1000` 替代错误的 `timedelta.microseconds`

### 修复 2: color_util.py — 修正全部 6 个检测函数的循环缩进

| 函数 | 修复内容 |
|------|----------|
| `isStone` | `return` 移到循环外；同时在循环内提前 return True 以提升性能 |
| `isStoneText` | `for i in range(10):` 缩进到外层 `for point` 循环内部；`return False` 移到循环外 |
| `is120PointCount` | `return okPoint120` 移到循环外 |
| `isResultPopShow` | `return False` 移到循环外 |
| `islvtongResultPopShow` | `return False` 移到循环外；改用专门的 `lvtongResultPopShowPoints` |
| `isLvtongText` | `for i in range(10):` 缩进到外层 `for point` 循环内部；`return False` 移到循环外 |

### 修复 3: login.py — 删除重复代码段

- 删除了第 178-214 行完全重复且含语法错误的 `clickLogin` 第二段代码
- 保留了第一段（含 timeout=5 的完整请求逻辑）
- 统一了状态栏中文提示信息

### 修复 4: index.py — 修正 5 处错误

1. **线程 6 信号连接**: `self.thread5.log_signal` → `self.thread6.log_signal`
2. **`getMHWinList` 窗口检测逻辑反转**: `if not (...)` → `if (...)`，并修复为同时检测三种 VM 类型
3. **`getOpenMHWinList`**: 同上，并补回了对 `VmLeidian` 的支持
4. **`initClock` 时间计算**: `((e-s)/1000).microseconds` → `int((e-s).total_seconds()*1000)`
5. **`closeEvent`**: 删除创建第二个 QApplication 的错误代码，改用 `QApplication.quit()`
6. **额外**: 删除 `thread13` 冗余代码，添加 `self.clickGxTime = None` 初始化

### 修复 5: robot_thread.py — 死循环 + 代码风格

1. **`lvtongClick` 死循环**: 检测到弹窗后添加 `return` 退出
2. **`run()` 方法**: 嵌套 `if-else` 改为 `elif` 链
3. **弹窗坐标**: 导入 `lvtongResultPopShowPoints`（配合 color_util.py 修复）
