import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function tableExists(conn, database, table) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1`,
    [database, table],
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

  if (!(await tableExists(conn, database, 'artifact_day_selected'))) {
    await conn.query(`
      CREATE TABLE artifact_day_selected (
        user_id BIGINT UNSIGNED NOT NULL,
        biz_date DATE NOT NULL,
        selected_json JSON NOT NULL,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, biz_date),
        CONSTRAINT fk_artifact_day_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    `);
    console.log('Created artifact_day_selected.');
  } else {
    console.log('artifact_day_selected exists, skip.');
  }

  await conn.end();
  console.log('migrate-v38 done: create artifact_day_selected.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

