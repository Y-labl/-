# 小霸王 - API接口文档

> 基础URL: http://111.229.123.236:3000
> Content-Type: application/json
> 认证方式: JWT Bearer Token (Authorization header)

---

## 1. 用户认证

### 1.1 登录

**POST /users/login**

请求参数:
```json
{
  "phone": "13800138000",
  "password": "abc123",
  "version": 30,
  "uuid": "abcd1234"
}
```

响应:
```json
{
  "obj": {
    "id": "user_id",
    "phone": "13800138000",
    "token": "jwt_token_string",
    "b": 100,
    "email": "",
    "enter": 1
  }
}
```

### 1.2 获取用户信息

**GET /users/userinfo**

Header: `Authorization: Bearer <token>`

响应:
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

### 1.3 更新登录类型

**POST /users/userinfo-user**

```json
{
  "logintype": 20
}
```

---

## 2. 订单管理

### 2.1 创建订单

**POST /dealorder/create**

```json
{
  "type": 20,
  "parth": 200,
  "deviceid": "device_uuid",
  "baotuconfig": "{}",
  "paoyuconfig": "{}",
  "cwchangjingconfig": "{}",
  "genduiconfig": "{}"
}
```

响应:
```json
{
  "obj": { ... }
}
```

### 2.2 获取订单列表

**GET /dealorder/mylist?parth=200&init=true&deviceid=xxx**

响应:
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
      "expiretime": "2026-07-02T00:00:00.000Z",
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

### 2.3 获取订单详情

**GET /dealorder/info?id=order_id**

### 2.4 更新订单

**POST /dealorder/user_update**

```json
{
  "id": "order_id",
  "winname": "device_serial",
  "remark": "新的备注",
  "dkchangjingconfig": "{\"roleAddXueMode\": ...}"
}
```

### 2.5 删除订单

**POST /dealorder/delete**

```json
{
  "id": "order_id"
}
```

---

## 3. 版本控制

### 3.1 获取版本列表

**GET /versioncontrol/list**

响应:
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

---

## 4. 其他

### 4.1 扣除游戏币

**POST /users/reduceb**

### 4.2 日志上报

**POST /stonelog/log**

---

## 5. 任务类型枚举

| 值 | 名称 | 消耗 |
|----|------|------|
| 20 | 宝图 | 2币/天 |
| 21 | 畅玩场景 | 4币/天 |
| 22 | 跑玉 | 3币/天 |
| 23 | 跟队 | 1币/天 |
| 24 | 点卡场景 | 2币/天 |

---

## 6. 模块编号

| parth | 窗口标题 |
|-------|----------|
| 200 | 小霸王1-10 |
| 201 | 小霸王11-20 |
| 202 | 小霸王21-30 |
