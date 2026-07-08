# 小霸王 - REST API 接口文档

> 更新日期: 2026-07-03
> 服务器: http://111.229.123.236:3000
> 认证方式: `Authorization: Bearer <token>` (登录后获取)

---

## 目录

1. [用户认证](#1-用户认证)
2. [订单管理](#2-订单管理)
3. [版本控制](#3-版本控制)
4. [第三方API](#4-第三方api)
5. [附录: 代码调用映射](#5-附录-代码调用映射)

---

## 1. 用户认证

### 1.1 POST /users/login - 登录

**用途**: 手机号+密码登录，获取JWT Token

**请求参数**:
```json
{
  "phone": "13800138000",
  "password": "abc123",
  "version": 30,
  "uuid": "abcd1234"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| phone | string | 手机号(11位) |
| password | string | 密码(6-16位字母数字) |
| version | int | 客户端版本号 |
| uuid | string | 机器码(WMI UUID前8位) |

**响应**:
```json
{
  "obj": {
    "id": "user_id",
    "phone": "13800138000",
    "token": "Bearer eyJhbGci...",
    "b": 100,
    "email": "",
    "enter": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | JWT Token (前端拼接成 "Bearer " + token 存储) |
| b | int | 余额(游戏币数量) |
| enter | int | 入口标识 |

**代码出处**: `subor_win.py` - `autoLogin()` -> `_dealPostRes()`

---

### 1.2 GET /users/userinfo - 获取用户信息

**用途**: 查询用户信息(余额)

**请求头**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "obj": {
    "id": "user_id",
    "phone": "13800138000",
    "b": 100,
    "enter": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| b | int | 余额(游戏币数量) |

**代码出处**: `main/main_win.py` - `fetchBalance()` -> `_dealFetchUserInfo()`

---

### 1.3 POST /users/userinfo-user - 更新登录类型

**用途**: 记录用户选择的功能入口类型

**请求参数**:
```json
{
  "logintype": 20
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| logintype | int | 任务类型代码 (见任务类型枚举) |

**代码出处**: `subor_win.py` - `uploadLoginType()` -> `_dealUploadLoginTypeRes()`

---

### 1.4 POST /users/reduceb - 扣除游戏币

**用途**: 扣除用户余额(按天计费)

**请求参数**:
```json
{
  "id": "order_id"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 订单ID |

**代码出处**: `main/detail_win.py` - 充值时调用

---

## 2. 订单管理

### 2.1 POST /dealorder/create - 创建订单

**用途**: 创建一个新的自动化任务订单

**请求参数**:
```json
{
  "type": 20,
  "parth": 200,
  "deviceid": "a1b2c3d4",
  "baotuconfig": "{\"isWaQiLinShan\": false}",
  "paoyuconfig": "{\"isWaQiLinShan\": false}",
  "cwchangjingconfig": "{\"isWaQiLinShan\": false}",
  "genduiconfig": "{\"...\": ...}"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | int | 任务类型(20-24) |
| parth | int | 模块编号(200/201/202) |
| deviceid | string | 设备机器码 |
| baotuconfig | string(JSON) | 宝图配置 |
| paoyuconfig | string(JSON) | 跑玉配置 |
| cwchangjingconfig | string(JSON) | 畅玩场景配置 |
| genduiconfig | string(JSON) | 跟队配置 |

**响应**:
```json
{
  "obj": { "...订单对象..." }
}
```

**代码出处**: `main/main_win.py` - `createOrder()` -> `createOrderRequest()` -> `_dealPostRes()`

---

### 2.2 GET /dealorder/mylist - 获取订单列表

**用途**: 获取当前用户的订单列表

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parth | int | 是 | 模块编号 |
| init | bool | 否 | 首次初始化标记 |
| deviceid | string | 否 | 设备机器码(init=true时必填) |

**示例**: `GET /dealorder/mylist?parth=200&init=true&deviceid=xxx`

**响应**:
```json
{
  "objs": [
    {
      "id": "order_id",
      "parth": 200,
      "type": 20,
      "phone": "13800138000",
      "deviceid": "xxx",
      "isactive": true,
      "expiretime": "2026-07-04T00:00:00.000Z",
      "isruning": false,
      "winname": "device_serial",
      "baotuconfig": "{}",
      "paoyuconfig": "{}",
      "cwchangjingconfig": "{}",
      "genduiconfig": "{}",
      "dkchangjingconfig": "{}",
      "remark": "备注",
      "funclist": "",
      "area": ""
    }
  ]
}
```

**订单对象字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 订单ID |
| parth | int | 模块编号 |
| type | int | 任务类型 |
| phone | string | 绑定手机号 |
| deviceid | string | 设备机器码 |
| isactive | bool | 是否激活 |
| expiretime | string(ISO8601) | 过期时间 |
| isruning | bool | 是否正在运行 |
| winname | string | 绑定设备ADB序列号 |
| baotuconfig | string(JSON) | 宝图配置 |
| paoyuconfig | string(JSON) | 跑玉配置 |
| cwchangjingconfig | string(JSON) | 畅玩场景配置 |
| genduiconfig | string(JSON) | 跟队配置 |
| dkchangjingconfig | string(JSON) | 点卡场景配置 |
| remark | string | 备注 |
| funclist | string | 功能列表 |
| area | string | 区域 |

**代码出处**: `main/main_win.py` - `fetchListData()` -> `_dealFetchRes()`

---

### 2.3 GET /dealorder/info - 获取订单详情

**用途**: 获取单个订单的详细信息

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 订单ID |

**示例**: `GET /dealorder/info?id=xxx`

**响应**:
```json
{
  "obj": { "...DealOrder对象..." }
}
```

**代码出处**: `main/detail_win.py` - `fetchOrderDetail()` -> `_dealFetchRes()`
`enter_win.py` - 版本检查时也使用了此接口

---

### 2.4 POST /dealorder/user_update - 更新订单

**用途**: 更新订单的各项配置

**请求参数** (按需包含以下任意字段):
```json
{
  "id": "order_id",
  "winname": "device_serial",
  "remark": "新的备注",
  "baotuconfig": "{\"...\": ...}",
  "paoyuconfig": "{\"...\": ...}",
  "cwchangjingconfig": "{\"...\": ...}",
  "genduiconfig": "{\"...\": ...}",
  "dkchangjingconfig": "{\"...\": ...}"
}
```

**代码出处** (多处调用):
| 场景 | 文件 | 说明 |
|------|------|------|
| 绑定设备 | `detail_win.py` -> `selectDevices()` | 更新winname |
| 设置备注 | `detail_win.py` -> `showSetRemark()` | 更新remark |
| 保存点卡配置 | `dk_changjing_config_win.py` -> `saveConfig()` | 更新dkchangjingconfig |
| 保存畅玩配置 | `cw_jingjing_config_win.py` | 更新cwchangjingconfig |
| 保存跟队配置 | `gendui_config_win.py` | 更新genduiconfig |

---

### 2.5 POST /dealorder/delete - 删除订单

**用途**: 删除指定订单

**请求参数**:
```json
{
  "id": "order_id"
}
```

**代码出处**: `main/detail_win.py` - `deleteOrder()` -> `_deleteDealOrderRes()`

---

## 3. 版本控制

### 3.1 GET /versioncontrol/list - 版本列表

**用途**: 获取版本控制信息，检查客户端是否需要更新

**响应**:
```json
{
  "objs": [
    {
      "openId": 1,
      "version": 30,
      "newVersion": 35,
      "forceVersion": 32,
      "content": "更新内容描述",
      "downloadUrl": "http://...",
      "config": "1.20"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| openId | int | 开放ID (匹配 const.py 的 OpenId) |
| version | int | 当前稳定版本 |
| newVersion | int | 最新版本号 |
| forceVersion | int | 强制更新版本号(低于此版本必须更新) |
| content | string | 更新内容描述 |
| downloadUrl | string | 安装器下载地址 |
| config | string | 配置字符串(传给SuborWin) |

**版本判断逻辑** (enter_win.py):
```
if newVersion > AppVersion:
    弹出更新对话框
    if AppVersion >= forceVersion:
        可选择"稍后"
    else:
        强制更新
```

**代码出处**: `enter_win.py` - `initVersion()` -> `_dealFetchRes()` -> `updateVersionCheck()`

---

## 4. 第三方API

### 4.1 POST http://www.tulingcloud.com/tuling/predict - NPC识别

**用途**: 识别游戏内重叠的多个NPC(四小人)，返回点击坐标

**请求参数**:
```json
{
  "username": "qq326646683",
  "password": "dashuai5",
  "ID": 48117555,
  "b64": "base64_encoded_screenshot_roi",
  "version": "3.1.1"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| username | string | 用户名(硬编码) |
| password | string | 密码(硬编码) |
| ID | int | API ID |
| b64 | string | 截图区域(base64编码的PNG) |
| version | string | API版本 |

**响应**:
```json
{
  "data": {
    "X坐标值": 100,
    "Y坐标值": 200
  }
}
```

**代码出处**: `common/util/img_util.py` - `findFourPersonAndClick()`

---

### 4.2 文件下载链接

**用途**: 下载ADB Write Secure Setting 授权工具
**URL**: `https://www.123865.com/s/xdUtVv-Zp05v`
**代码出处**: `common/util/adb_util.py` - `modifyDeviceXY()`

---

## 5. 附录: 代码调用映射

| 接口 | 被调用的源文件 | 功能场景 |
|------|---------------|----------|
| POST /users/login | subor_win.py | 用户登录 |
| GET /users/userinfo | main/main_win.py | 刷新余额 |
| POST /users/userinfo-user | subor_win.py | 记录功能入口 |
| POST /users/reduceb | main/detail_win.py | 扣费 |
| POST /dealorder/create | main/main_win.py | 创建订单 |
| GET /dealorder/mylist | main/main_win.py | 订单列表 |
| GET /dealorder/info | main/detail_win.py, enter_win.py | 订单详情 |
| POST /dealorder/user_update | detail_win.py, dk_changjing_config_win.py, cw_jingjing_config_win.py, gendui_config_win.py | 更新配置 |
| POST /dealorder/delete | main/detail_win.py | 删除订单 |
| GET /versioncontrol/list | enter_win.py | 版本检查 |
| POST http://www.tulingcloud.com/tuling/predict | common/util/img_util.py | NPC识别(第三方) |

---

## 6. 附录: 任务类型枚举 (const.py)

| 常量名 | 值 | 中文名 | 日消耗 |
|--------|-----|--------|--------|
| TYPE_PING | 6 | 测试(抢平转) | - |
| TYPE_BAOTU | 20 | 宝图 | 2币 |
| TYPE_CW_CHANGJING | 21 | 畅玩场景 | 4币 |
| TYPE_PAOYU | 22 | 跑玉 | 3币 |
| TYPE_GENDUI | 23 | 跟队 | 1币 |
| TYPE_DK_CHANGJING | 24 | 点卡场景 | 2币 |

---

## 7. 附录: parth 模块编号

| parth | 窗口标题 | 用途 |
|-------|----------|------|
| 200 | 小霸王1-10 | 第一个10订单模块 |
| 201 | 小霸王11-20 | 第二个10订单模块 |
| 202 | 小霸王21-30 | 第三个10订单模块 |

---

> 本文档基于反编译源码自动生成，所有接口路径、参数格式均来自 `const.py` 和各业务模块中的实际调用代码。
