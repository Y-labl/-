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
CREATE TABLE mech_ledger_user_prefs (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  rmb_yuan DECIMAL(12,2) NOT NULL DEFAULT 30.00 COMMENT '锚定万数游戏币对应的人民币，万数与客户端 LEDGER_GAME_WAN_ANCHOR 一致',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_mech_prefs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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

  if (!(await tableExists(conn, database, 'mech_ledger_user_prefs'))) {
    await conn.query(CREATE);
    console.log('Created mech_ledger_user_prefs.');
  } else {
    console.log('mech_ledger_user_prefs exists, skip migrate-v8.');
  }

  await conn.end();
  console.log('migrate-v8 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
