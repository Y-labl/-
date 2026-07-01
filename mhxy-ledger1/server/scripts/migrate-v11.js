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

/** 消耗页「当日 × 角色」一行：人民币、梦幻币、备注、物品库消耗（JSON，单表承载） */
const CREATE_TOTALS = `
CREATE TABLE consumption_day_totals (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  character_id BIGINT UNSIGNED NOT NULL,
  rmb_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  dream_coin_w DECIMAL(14,4) NOT NULL DEFAULT 0 COMMENT '梦幻币消耗（万）',
  note VARCHAR(255) NOT NULL DEFAULT '',
  catalog_lines_json JSON NOT NULL DEFAULT ('[]') COMMENT '物品消耗 [{catalogItemId,quantity,name}]',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY ux_cdt_user_date_char (user_id, biz_date, character_id),
  KEY idx_cdt_user_date (user_id, biz_date),
  CONSTRAINT fk_cdt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_cdt_character FOREIGN KEY (character_id) REFERENCES consumption_characters(id) ON DELETE CASCADE
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

  if (!(await tableExists(conn, database, 'consumption_day_totals'))) {
    await conn.query(CREATE_TOTALS);
    console.log('Created consumption_day_totals (with catalog_lines_json).');
  } else {
    console.log('consumption_day_totals exists, skip create. If upgrading from old v11, run migrate-v12.');
  }

  await conn.end();
  console.log('migrate-v11 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
