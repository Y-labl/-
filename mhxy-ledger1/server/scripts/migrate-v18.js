import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/** 九色鹿、如梦奇谭：无固定整点场次，用全周+日间占位；周次数/刷新与戏票以游戏内为准 */
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
       ('cal-jiuse-jlq', '奇遇：九色鹿（上 / 下）',
        '奇遇副本；上与下次数/刷新不同（常见为下每周一刷新等），领取时段多为 8:00 后。此处为五开周常占位，详游戏规则。',
        '0,1,2,3,4,5,6', '08:00:00', '23:59:00', 30, 4, 26, 26, NULL, NULL, 1),
       ('cal-rumu-qitan', '副本：如梦奇谭（看戏）',
        '五更寒等看戏本；每周一 0 点刷新当周开放剧目，需戏票找癫散班主领取。无固定整点，占位便于插在空档。',
        '0,1,2,3,4,5,6', '08:00:00', '23:59:00', 30, 4, 27, 27, NULL, NULL, 1)
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
  console.log('migrate-v18 done: 九色鹿、如梦奇谭（看戏）已写入 calendar_activities.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
