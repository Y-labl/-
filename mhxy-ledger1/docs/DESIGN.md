# 梦幻西游账系统（MHXY Ledger）设计文档 v3

## 1. 背景与目标

为《梦幻西游》玩家提供一套**本地 Web 账系统**：记录每日**物品获得**、**现金变动**、**点卡消耗**；用**推荐任务榜**管理日常与「约四天一轮」的副本优先级；支持按**完成时间**追溯；并提供**日 / 周 / 月**收益总览。

v1 目标：**可登录、可记账、可刷榜、可看总览**，界面完整、数据进 MySQL，便于后续迭代。

## 2. 技术选型

| 层级 | 选型 | 说明 |
|------|------|------|
| 前端 | React 18 + Vite 6 + TypeScript | 组件化、热更新，适合交互较多的记账与推荐榜 |
| 后端 | Node.js 20+ + Express 4 | 轻量 REST API，与 MySQL 配合简单 |
| 数据库 | MySQL 8.x（本地） | 库名 `mhxy_ledger`，utf8mb4 |
| 认证 | JWT（Bearer） | v1 存 `localStorage`；后续可改 HttpOnly Cookie |

## 3. 用户与认证

- 用户注册 / 登录，密码 **bcrypt** 存储。
- 登录后签发 JWT，后续请求 `Authorization: Bearer <token>`。
- v1 默认种子用户：`demo` / `12345678`（与本地 MySQL 密码无关，仅为演示账号）。

## 4. 功能模块

### 4.1 个性化登录页

- **眼睛跟随鼠标**：多个「小人」眼珠根据指针与眼眶中心连线的角度做**有限位移**（clamp），避免飞出眼眶。
- **输入密码时「看向别处」**：密码框 `focus` 或显示明文时，眼珠转向侧面/下方，模拟「不偷看」趣味交互。
- 视觉：深色国风渐变 + 金色点缀，与「梦幻」主题协调。

### 4.2 物品记账（多页分类）

- 物品按 **分类** 分页展示（如：材料、兽决内丹、宝石、书铁、其他）。
- 每项展示 **图片**（v1 使用内置占位图 + emoji/文字；后续可换真实图标路径）。
- **点击物品**即记一条「当日获得」记录（默认数量 1，可在总览或后续版本扩展批量）。

### 4.3 现金与点卡

- **现金**：支持正负（收入/支出），带简短备注。
- **点卡**：记录消耗点数（一般为正数表示消耗），带备注。

### 4.4 每日任务推荐榜与「已刷」记录（v3）

- **模板任务**（`task_templates`）：无 `schedule_weekdays` 的日常 / 副本冷却逻辑与 v1 相同；**带固定时段的模板行不再上推荐榜**，改由下方「实时活动」统一提供，避免与远程活动重复。
- **实时活动**：服务端按可配置间隔 **拉取远程 JSON**（`ACTIVITIES_FEED_URL`），失败则使用 **内置日历**（`server/src/services/activityFeed.js`）。合并进推荐榜，置顶规则与 v2 一致。
- **已刷记录唯一来源**：表 `task_done_entries`。只有用户在推荐榜点 **完成**，或在 **补录完成** 页提交，才会写入；**未点完成的一律不记**。
- **dedupe_key**：模板任务为 `db:{task_id}`；实时活动为 `live:{key}:{biz_date}`。同一业务日同键不可重复写入。
- **推荐榜移除**（如限时活动结束）后，仍可在 **补录完成** 中按业务日找到对应项并补记（含已结束的活动）。
- **完成**时可填开始 / 结束时间，供总览展示耗时。

### 4.5 总览（日 / 周 / 月）

- **每日**：当日物品次数汇总、现金合计、点卡合计；可选列出当日任务完成记录及耗时。
- **每周 / 每月**：按自然周（周一至周日）、自然月聚合上述指标。
- v1 以 **卡片 + 简单柱状对比** 展示，不接复杂 BI。

### 4.6 额外想法（v1 已部分体现）

- **今日一行摘要**：顶栏显示今日现金净值、点卡、完成任务数。
- **空状态引导**：无数据时提示先去「物品 / 现金」记一笔或去完成推荐榜。

## 5. 数据库表结构

### 5.1 `users`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | |
| username | VARCHAR(64) UNIQUE | 登录名 |
| password_hash | VARCHAR(255) | bcrypt |
| created_at | DATETIME | |

### 5.2 `item_categories`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AI | |
| name | VARCHAR(64) | 分类名 |
| sort_order | INT | 展示顺序 |

### 5.3 `items`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AI | |
| category_id | INT FK | |
| name | VARCHAR(128) | |
| image_url | VARCHAR(512) | 相对路径或外链 |
| sort_order | INT | |

### 5.4 `item_gains`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | |
| user_id | BIGINT FK | |
| biz_date | DATE | 业务日（按用户本机日历；v1 用服务器本地日期） |
| item_id | INT FK | |
| quantity | INT | 默认 1 |
| created_at | DATETIME | |

### 5.5 `cash_entries`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | |
| user_id | BIGINT FK | |
| biz_date | DATE | |
| amount | DECIMAL(14,2) | 正收入负支出 |
| note | VARCHAR(255) | |
| created_at | DATETIME | |

### 5.6 `point_card_entries`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | |
| user_id | BIGINT FK | |
| biz_date | DATE | |
| points | INT | 消耗点数（正数） |
| note | VARCHAR(255) | |
| created_at | DATETIME | |

### 5.7 `task_templates`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AI | |
| name | VARCHAR(128) | |
| description | VARCHAR(512) | |
| frequency | ENUM('daily','four_day') | |
| sort_order | INT | 推荐榜优先级 |
| cooldown_days | INT | four_day 默认 4 |
| schedule_weekdays | VARCHAR(32) NULL | v2：限时星期 |
| schedule_start / schedule_end | TIME NULL | v2 |
| schedule_pin_early_minutes | INT | v2 |
| created_at | DATETIME | |

### 5.8 `task_completions`（遗留）

- 历史表；**v3 起完成态以 `task_done_entries` 为准**。`npm run db:migrate-v3` 会将旧数据 **INSERT IGNORE** 同步到新表。

### 5.9 `task_done_entries`（v3 · 每日已刷）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | |
| user_id | BIGINT FK | |
| biz_date | DATE | 业务日 |
| dedupe_key | VARCHAR(180) | `db:{id}` 或 `live:{key}:{biz_date}` |
| task_id | INT NULL FK | 模板完成时有值；纯活动可为 NULL |
| title | VARCHAR(256) | 展示用快照 |
| started_at / ended_at | DATETIME NULL | |
| source | VARCHAR(32) | `complete` / `backfill` / `migrated` 等 |
| created_at | DATETIME | |

唯一索引：`(user_id, biz_date, dedupe_key)`。

索引建议：`item_gains(user_id, biz_date)`、`cash_entries(user_id, biz_date)`、`point_card_entries(user_id, biz_date)`、`task_done_entries(user_id, biz_date)`、`task_done_entries(user_id, task_id)`。

## 6. API 概要（REST）

- `POST /api/auth/register` `{ username, password }`
- `POST /api/auth/login` `{ username, password }` → `{ token, user }`
- `GET /api/me` 当前用户
- `GET /api/categories` / `GET /api/items?categoryId=`
- `POST /api/item-gains` `{ itemId, quantity?, bizDate? }`
- `POST /api/cash` `{ amount, note?, bizDate? }`
- `POST /api/points` `{ points, note?, bizDate? }`
- `GET /api/tasks/recommended?bizDate=&weekday=&wallMinutes=` → `tasks[]`（含 `source: db|live`、`activityFeed` 元数据）
- `GET /api/tasks/candidates?bizDate=` → 可 **补录** 的模板 + 实时活动（含已下榜）
- `POST /api/tasks/done` `{ bizDate, taskId? | externalKey?, title?, startedAt?, endedAt?, source? }` 写入 **已刷**
- `POST /api/tasks/:id/complete` 同 `done`（兼容旧前端）
- `POST /api/smart/parse` `{ text }` → `{ actions }`
- `POST /api/smart/ocr` `multipart/form-data` 字段 `image`
- `POST /api/smart/apply` `{ bizDate, actions }`
- `GET /api/stats/overview?bizDate=` 日聚合
- `GET /api/stats/weekly?weekStart=` 周聚合（周一为周起始）
- `GET /api/stats/monthly?year=&month=` 月聚合

## 7. 前端路由（v1）

- `/login` 登录 / 注册切换
- `/app` 布局内：
  - `/app` 总览
  - `/app/items` 物品分类入口
  - `/app/items/:categoryId` 物品网格（点击记账）
  - `/app/cash` 现金与点卡
  - `/app/tasks` 推荐榜
  - `/app/tasks/backfill` 补录完成

## 8. 非功能与安全

- 密码不明文落库；JWT 密钥来自环境变量。
- v1 默认仅本机访问（`localhost`）；若暴露局域网需 HTTPS + 更强密码策略。
- 业务日 `bizDate` v1 默认传当日；后续可加「跨日熬夜」时区/手动选日。

## 9. v2 补充：语音/截图智能录入

- **语音**：浏览器 **Web Speech API**（推荐 Chrome / Edge，`zh-CN`），在本地转文字后调用后端 **规则解析**（非大模型），识别现金（含「万」）、点卡/点数、物品名（与 `items` 表模糊匹配，长名称优先）。
- **截图**：上传图片到 `POST /api/smart/ocr`，服务端 **Tesseract.js**（`chi_sim` + `eng`）OCR，首跑会下载语言包，耗时较长；可通过环境变量 `SMART_OCR_DISABLED=1` 关闭 OCR。
- **写入**：`POST /api/smart/parse` 仅解析；`POST /api/smart/apply` 将解析结果批量写入 `cash_entries` / `point_card_entries` / `item_gains`。
- 前端在「现金·点卡」与「物品分类-网格」页提供统一 **智能录入面板**。

## 10. v2 补充：限时活动推荐与提醒

- `task_templates` 增加字段：`schedule_weekdays`（`0=周日`…`6=周六`，逗号分隔）、`schedule_start` / `schedule_end`、`schedule_pin_early_minutes`（默认 30，即开始前 30 分钟进入「置顶窗口」）。
- **展示规则（与客户端本地钟点同步）**：请求 `GET /api/tasks/recommended` 时携带 `weekday`、`wallMinutes`（由浏览器根据本机时间计算）。在匹配星期且当前时刻 **未超过 `schedule_end`** 时活动可见；在 `[start - pin_early, end]` 内 **置顶排序优先**；超过 `schedule_end` 的当日活动 **从列表移除**。
- **实时刷新**：前端约 **15s** 更新钟点依赖、**30s** 拉取列表；业务日选「今天」时用实时时间，选历史日时用该日星期 + 23:59 模拟当日末快照。
- **系统通知**：用户点击授权后，若存在置顶活动，每 **10 分钟** 浏览器 `Notification` 提醒一次（需页面允许通知）。

## 11. v3 补充：远程实时活动 JSON

- 环境变量 **`ACTIVITIES_FEED_URL`**：GET 返回 JSON，字段示例见 `server/data/activities-feed.example.json`。
- 服务端 **`activityFeed` 服务** 默认缓存约 **5 分钟**（`ACTIVITIES_FEED_TTL_MS`），超时 `ACTIVITIES_FEED_TIMEOUT_MS`。
- 拉取失败或数组为空时回退 **内置活动列表**；响应头 `activityFeed` 标明 `source` / `fetched` / `error`。
- 推荐榜中的限时条目 `source: live`，完成时写 `live:{key}:{bizDate}`。

## 12. 本地运行（v1–v3）

1. 确保 MySQL 已启动；`npm run db:schema` 会执行 schema + seed + **migrate-v2 + migrate-v3**。
2. **已有旧库**：在 `server` 下依次执行（均可重复执行）：`npm run db:migrate-v2`、`npm run db:migrate-v3`。
3. 后端：`npm install` → `npm run dev`（`http://127.0.0.1:3001`）。可选配置 `.env` 中 `ACTIVITIES_FEED_URL`。
4. 前端：`npm install` → `npm run dev`（`http://127.0.0.1:5173`）。
5. 演示账号：`demo` / `12345678`。

> 面向使用者的说明见同目录 **[PRODUCT.md](./PRODUCT.md)**（产品文档，随功能迭代同步更新）。

## 13. 迭代方向（非当前版本）

- 物品参考价、自动折算现金；导出 Excel；多角色/多号；副本真实 CD 与游戏日历同步；管理后台维护物品图。

---

**文档版本**：v1.3（技术设计）  
**日期**：2026-04-05
