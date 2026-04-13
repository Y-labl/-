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

async function indexExists(conn, database, table, indexName) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.STATISTICS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND INDEX_NAME = ? LIMIT 1`,
    [database, table, indexName]
  );
  return rows.length > 0;
}

/** 任务记录：耗时（秒）、按结束时间查询索引；补全历史 started_at、duration_seconds */
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

  if (!(await columnExists(conn, database, 'task_done_entries', 'duration_seconds'))) {
    await conn.query(`
      ALTER TABLE task_done_entries
      ADD COLUMN duration_seconds INT UNSIGNED NULL
      COMMENT 'started_at 到 ended_at 的秒数'
      AFTER ended_at
    `);
    console.log('Added task_done_entries.duration_seconds.');
  } else {
    console.log('duration_seconds already exists, skip.');
  }

  if (!(await indexExists(conn, database, 'task_done_entries', 'idx_done_user_ended'))) {
    await conn.query(`
      ALTER TABLE task_done_entries
      ADD INDEX idx_done_user_ended (user_id, ended_at)
    `);
    console.log('Added idx_done_user_ended.');
  } else {
    console.log('idx_done_user_ended already exists, skip.');
  }

  await conn.query(`
    UPDATE task_done_entries
    SET started_at = biz_date
    WHERE started_at IS NULL AND ended_at IS NOT NULL
  `);
  await conn.query(`
    UPDATE task_done_entries
    SET duration_seconds = TIMESTAMPDIFF(SECOND, started_at, ended_at)
    WHERE started_at IS NOT NULL AND ended_at IS NOT NULL
      AND (duration_seconds IS NULL OR duration_seconds = 0)
      AND ended_at >= started_at
  `);

  await conn.end();
  console.log('migrate-v24 done: duration + index + backfill started_at/duration.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
