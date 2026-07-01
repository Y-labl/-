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
CREATE TABLE mech_ledger_session_state (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  state_json JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_mech_sess_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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

  if (!(await tableExists(conn, database, 'mech_ledger_session_state'))) {
    await conn.query(CREATE);
    console.log('Created mech_ledger_session_state.');
  } else {
    console.log('mech_ledger_session_state exists, skip migrate-v9.');
  }

  await conn.end();
  console.log('migrate-v9 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
