import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, db, table, col) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [db, table, col]
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

  if (!(await columnExists(conn, database, 'task_templates', 'schedule_weekdays'))) {
    await conn.query(`
      ALTER TABLE task_templates
        ADD COLUMN schedule_weekdays VARCHAR(32) NULL COMMENT '0=周日' AFTER cooldown_days,
        ADD COLUMN schedule_start TIME NULL AFTER schedule_weekdays,
        ADD COLUMN schedule_end TIME NULL AFTER schedule_start,
        ADD COLUMN schedule_pin_early_minutes INT UNSIGNED NOT NULL DEFAULT 30 AFTER schedule_end
    `);
    console.log('Added schedule columns to task_templates.');
  } else {
    console.log('Schedule columns already exist, skip ALTER.');
  }

  await conn.query(`
    INSERT IGNORE INTO task_templates
      (id, name, description, frequency, sort_order, cooldown_days, enabled,
       schedule_weekdays, schedule_start, schedule_end, schedule_pin_early_minutes)
    VALUES
      (13, '活动：门派闯关', '已改由 calendar_activities / 活动 feed 按「每月第 1 个周日」展示；本行停用', 'daily', 2, 1, 0,
       '0', '15:00:00', '17:00:00', 30),
      (14, '活动：帮派迷宫', '周一至周四 20:00–22:00', 'daily', 3, 1, 1,
       '1,2,3,4', '20:00:00', '22:00:00', 30),
      (15, '活动：天降星辰', '周一至周四 20:00–22:00', 'daily', 4, 1, 1,
       '1,2,3,4', '20:00:00', '22:00:00', 30)
  `);

  await conn.end();
  console.log('migrate-v2 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
