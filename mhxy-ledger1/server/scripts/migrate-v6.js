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

const CREATE_LINES = `
CREATE TABLE mech_catalog_line_agg (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  item_name VARCHAR(191) NOT NULL,
  unit_price_w DECIMAL(14,4) NOT NULL,
  quantity INT UNSIGNED NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_mech_line_user_date (user_id, biz_date),
  CONSTRAINT fk_mech_line_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const CREATE_META = `
CREATE TABLE mech_ledger_day_meta (
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  point_card_points DECIMAL(14,2) NOT NULL DEFAULT 0,
  online_roles INT UNSIGNED NOT NULL DEFAULT 1,
  saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, biz_date),
  CONSTRAINT fk_mech_day_meta_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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

  const hasLines = await tableExists(conn, database, 'mech_catalog_line_agg');
  const hasMeta = await tableExists(conn, database, 'mech_ledger_day_meta');

  if (!hasLines) {
    await conn.query(CREATE_LINES);
    console.log('Created mech_catalog_line_agg.');
  }
  if (!hasMeta) {
    await conn.query(CREATE_META);
    console.log('Created mech_ledger_day_meta.');
  }
  if (hasLines && hasMeta) {
    console.log('mech ledger tables exist, skip migrate-v6.');
  }

  await conn.end();
  console.log('migrate-v6 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
