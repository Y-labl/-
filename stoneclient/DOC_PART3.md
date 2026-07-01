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

