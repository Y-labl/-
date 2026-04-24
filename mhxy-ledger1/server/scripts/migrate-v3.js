import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function tableExists(conn, db, name) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1`,
    [db, name]
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

  if (!(await tableExists(conn, database, 'task_done_entries'))) {
    await conn.query(`
      CREATE TABLE task_done_entries (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT UNSIGNED NOT NULL,
        biz_date DATE NOT NULL,
        dedupe_key VARCHAR(180) NOT NULL,
        task_id INT UNSIGNED NULL,
        title VARCHAR(256) NOT NULL,
        started_at DATETIME NULL,
        ended_at DATETIME NULL,
        source VARCHAR(32) NOT NULL DEFAULT 'complete',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY ux_done_user_date_key (user_id, biz_date, dedupe_key),
        KEY idx_done_user_date (user_id, biz_date),
        KEY idx_done_task (user_id, task_id),
        CONSTRAINT fk_done_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_done_template FOREIGN KEY (task_id) REFERENCES task_templates(id) ON DELETE SET NULL
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `);
    console.log('Created task_done_entries.');
  } else {
    console.log('task_done_entries exists, skip CREATE.');
  }

  await conn.query(`
    INSERT IGNORE INTO task_done_entries
      (user_id, biz_date, dedupe_key, task_id, title, started_at, ended_at, source)
    SELECT c.user_id, c.biz_date, CONCAT('db:', c.task_id), c.task_id, t.name,
           c.started_at, c.ended_at, 'migrated'
    FROM task_completions c
    INNER JOIN task_templates t ON t.id = c.task_id
  `);
  console.log('Synced legacy task_completions -> task_done_entries (INSERT IGNORE).');

  await conn.end();
  console.log('migrate-v3 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
