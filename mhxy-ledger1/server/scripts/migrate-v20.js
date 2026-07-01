import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * 明确写入推荐榜所需时段：
 * - 皇宫飞贼：周一至周五 12:00–14:00
 * - 双龙神器争夺（每日夜场）：全周 22:00–23:30
 */
async function main() {
  const database = process.env.MYSQL_DATABASE || 'mhxy_ledger';
  const conn = await mysql.createConnection({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    multipleStatements: true,
  });
  await conn.query(`USE \`${database}\``);

  await conn.query(
    `INSERT INTO calendar_activities
      (act_key, name, description, schedule_weekdays, schedule_start, schedule_end,
       pin_early_minutes, stars, wukai_rank, sort_order, month_week, month_anchor_weekday, is_active)
     VALUES
       ('huangong-feizei', '活动：皇宫飞贼',
        '周一至周五，中午 12:00 至下午 14:00（即 12 点–下午 2 点；以游戏内为准）。',
        '1,2,3,4,5', '12:00:00', '14:00:00', 20, 5, 5, 5, NULL, NULL, 1),
       ('cal-shuanglong-shenqi-daily', '活动：双龙之战·神器争夺战（每日）',
        '每晚神器争夺：22:00–23:30（乱流来客、碎片争夺等阶段以游戏内为准）。',
        '0,1,2,3,4,5,6', '22:00:00', '23:30:00', 25, 5, 21, 21, NULL, NULL, 1)
     ON DUPLICATE KEY UPDATE
       name = VALUES(name),
       description = VALUES(description),
       schedule_weekdays = VALUES(schedule_weekdays),
       schedule_start = VALUES(schedule_start),
       schedule_end = VALUES(schedule_end),
       pin_early_minutes = VALUES(pin_early_minutes),
       stars = VALUES(stars),
       wukai_rank = VALUES(wukai_rank),
       sort_order = VALUES(sort_order),
       month_week = VALUES(month_week),
       month_anchor_weekday = VALUES(month_anchor_weekday),
       is_active = VALUES(is_active)`
 );

  await conn.end();
  console.log('migrate-v20 done: 皇宫飞贼 12:00–14:00 + 双龙夜场 22:00–23:30 已写入 calendar_activities。');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
