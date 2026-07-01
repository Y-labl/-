import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

async function tableExists(conn, db, name) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1`,
    [db, name]
  );
  return rows.length > 0;
}

const CREATE = `
CREATE TABLE consumption_entries (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  character_name VARCHAR(64) NOT NULL DEFAULT '',
  level_label VARCHAR(32) NOT NULL DEFAULT '',
  sect VARCHAR(32) NOT NULL DEFAULT '',
  rmb_amount DECIMAL(10,2) NOT NULL,
  note VARCHAR(255) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_consumption_user_date (user_id, biz_date),
  CONSTRAINT fk_consumption_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

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

  if (!(await tableExists(conn, database, 'consumption_entries'))) {
    await conn.query(CREATE);
    console.log('Created consumption_entries.');
  } else {
    console.log('consumption_entries exists, skip migrate-v7.');
  }

  await conn.end();
  console.log('migrate-v7 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
