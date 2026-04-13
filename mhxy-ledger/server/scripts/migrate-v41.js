import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column],
  );
  return rows.length > 0;
}

/**
 * calendar_activities：第二段时段（如英雄大会第二场），与 JSON `windows` 等价。
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

  if (!(await columnExists(conn, database, 'calendar_activities', 'schedule_start_2'))) {
    await conn.query(`
      ALTER TABLE calendar_activities
        ADD COLUMN schedule_start_2 TIME NULL COMMENT '第二段开始（可与第一段同一天）' AFTER schedule_end,
        ADD COLUMN schedule_end_2 TIME NULL COMMENT '第二段结束' AFTER schedule_start_2
    `);
    console.log('Added calendar_activities.schedule_start_2 / schedule_end_2.');
  } else {
    console.log('schedule_start_2 already exists, skip ALTER.');
  }

  const [r] = await conn.query(
    `UPDATE calendar_activities
     SET schedule_start = '13:30:00',
         schedule_end = '15:30:00',
         schedule_start_2 = '16:00:00',
         schedule_end_2 = '18:00:00',
         description = '每月第四周周日：比武 13:30–15:30、16:00–18:00（以游戏内为准）。'
     WHERE act_key = 'cal-yingxiong'`,
  );
  console.log(`migrate-v41: cal-yingxiong rows=${r.affectedRows}`);

  await conn.end();
  console.log('migrate-v41 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
