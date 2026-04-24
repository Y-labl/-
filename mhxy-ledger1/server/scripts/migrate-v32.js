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

/**
 * task_done_entries: add unit_count for tasks like 抓鬼周上限（200只）。
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

  if (!(await columnExists(conn, database, 'task_done_entries', 'unit_count'))) {
    await conn.query(`
      ALTER TABLE task_done_entries
      ADD COLUMN unit_count INT UNSIGNED NULL
      COMMENT 'Per-entry count for special tasks (e.g. weekly ghost captures).'
      AFTER duration_seconds
    `);
    console.log('Added task_done_entries.unit_count.');
  } else {
    console.log('unit_count already exists, skip.');
  }

  await conn.end();
  console.log('migrate-v32 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

