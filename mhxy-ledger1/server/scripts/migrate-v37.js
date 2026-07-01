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

  if (!(await columnExists(conn, database, 'mech_ledger_day_meta', 'point_card_saved_at'))) {
    await conn.query(`
      ALTER TABLE mech_ledger_day_meta
      ADD COLUMN point_card_saved_at DATETIME NULL
        COMMENT '点卡快照写入时刻；仅点「保存收益」/「保存并清除计时」时更新'
      AFTER point_card_points
    `);
    console.log('Added mech_ledger_day_meta.point_card_saved_at.');
  } else {
    console.log('mech_ledger_day_meta.point_card_saved_at exists, skip.');
  }

  await conn.end();
  console.log('migrate-v37 done: add point_card_saved_at.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

