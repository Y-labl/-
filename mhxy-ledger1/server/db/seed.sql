USE mhxy_ledger;

-- 演示账号由 `npm run db:seed`（Node + bcrypt）创建，避免 SQL 内写死哈希。

INSERT IGNORE INTO item_categories (id, name, sort_order) VALUES
(1, '材料', 1),
(2, '兽决 · 内丹', 2),
(3, '宝石 · 星辉', 3),
(4, '书铁 · 装备', 4),
(5, '其他', 99);

INSERT IGNORE INTO items (id, category_id, name, image_url, sort_order) VALUES
(1, 1, '强化石包', '/item-placeholder.svg?c=1', 1),
(2, 1, '五宝盒', '/item-placeholder.svg?c=2', 2),
(3, 1, '藏宝图', '/item-placeholder.svg?c=3', 3),
(4, 1, '环装', '/item-placeholder.svg?c=4', 4),
(5, 2, '低级兽决', '/item-placeholder.svg?c=5', 1),
(6, 2, '高级兽决', '/item-placeholder.svg?c=6', 2),
(7, 2, '内丹', '/item-placeholder.svg?c=7', 3),
(8, 3, '宝石', '/item-placeholder.svg?c=8', 1),
(9, 3, '星辉石', '/item-placeholder.svg?c=9', 2),
(10, 4, '制造书', '/item-placeholder.svg?c=10', 1),
(11, 4, '百炼精铁', '/item-placeholder.svg?c=11', 2),
(12, 5, '金币袋', '/item-placeholder.svg?c=12', 1),
(13, 5, '活动积分', '/item-placeholder.svg?c=13', 2);

INSERT IGNORE INTO task_templates (id, name, description, frequency, sort_order, cooldown_days) VALUES
(1, '师门任务', '稳定现金与储备，优先完成', 'daily', 10, 1),
(2, '抓鬼 · 鬼王', '钟馗日常 + 黑无常鬼王，五开一条就够，勿重复勾选', 'daily', 20, 1),
(4, '日常：神器任务（起）', '新起神器任务线；与「转」为两条独立日常。', 'daily', 40, 1),
(16, '日常：神器任务（转）', '已起神器后的转换、洗炼等；与「起」为两条独立日常。', 'daily', 41, 1),
(5, '天命：大闹天宫', '附魔宝珠等高价值，五开优先清', 'four_day', 50, 4),
(6, '天命：金兜洞', '现金、物品均衡，轮换必刷', 'four_day', 51, 4),
(7, '天命：乌鸡国', '流程短、性价比高', 'four_day', 52, 4),
(8, '天命：齐天大圣', '天命轮换位，按周期补齐', 'four_day', 53, 4),
(9, '侠士天命：通天河', '周期长，附魔期望高', 'four_day', 60, 4),
(10, '周末活动', '文韵墨香 / 门派闯关 等', 'daily', 5, 1),
(11, '日常：百晓星君', '快速日常', 'daily', 35, 1);

-- New dungeons (auto id); keep in four_day block
INSERT IGNORE INTO task_templates (name, description, frequency, sort_order, cooldown_days) VALUES
('副本：秘境降妖', '四天一刷副本（推荐榜可手动排序）', 'four_day', 61, 4),
('副本：猴王出世', '四天一刷副本（推荐榜可手动排序）', 'four_day', 62, 4);

INSERT IGNORE INTO task_templates (id, name, description, frequency, sort_order, cooldown_days, schedule_weekdays, schedule_start, schedule_end, schedule_pin_early_minutes) VALUES
(12, '活动：皇宫飞贼', '周一至周五，中午 12:00 至下午 14:00（即 12 点–下午 2 点；以游戏内为准）。', 'daily', 36, 1, '1,2,3,4,5', '12:00:00', '14:00:00', 20);
