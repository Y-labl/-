import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column]
  );
  return rows.length > 0;
}

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

  if (!(await columnExists(conn, database, 'calendar_activities', 'month_anchor_weekday'))) {
    await conn.query(`
      ALTER TABLE calendar_activities
      ADD COLUMN month_anchor_weekday TINYINT UNSIGNED NULL
      COMMENT '与 month_week 联用：当月第几个「周几」，0=周日..6=周六；与月度周日玩法配合'
      AFTER month_week
    `);
    console.log('Added calendar_activities.month_anchor_weekday.');
  } else {
    console.log('month_anchor_weekday already exists, skip ALTER.');
  }

  await conn.query(`
    UPDATE calendar_activities
    SET month_anchor_weekday = 0
    WHERE month_week IS NOT NULL AND month_anchor_weekday IS NULL
  `);

  await conn.query(
    `INSERT INTO calendar_activities
      (act_key, name, description, schedule_weekdays, schedule_start, schedule_end,
       pin_early_minutes, stars, wukai_rank, sort_order, month_week, month_anchor_weekday, is_active)
     VALUES
       ('cal-shuanglong', '活动：双龙之战',
        '每月第二周周六下午场次（前哨/大决战等，以当周维护公告为准）',
        '6', '14:00:00', '17:00:00', 30, 5, 24, 24, 2, 6, 1),
       ('cal-guixu-zhuagui', '副本：归墟·抓鬼',
        '需归墟之证；无整点统一开放，全周可进。每日次数与星级以游戏为准，此处时段为五开常见约队占位。',
        '0,1,2,3,4,5,6', '10:00:00', '23:59:00', 30, 5, 5, 5, NULL, NULL, 1)
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
  console.log('migrate-v17 done: 双龙之战 + 归墟·抓鬼；month_anchor_weekday 支持每月第N个周六等。');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
