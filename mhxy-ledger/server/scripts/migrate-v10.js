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

async function columnExists(conn, db, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [db, table, column]
  );
  return rows.length > 0;
}

const CREATE_CHARACTERS = `
CREATE TABLE consumption_characters (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  character_name VARCHAR(64) NOT NULL,
  level_label VARCHAR(32) NOT NULL DEFAULT '',
  sect VARCHAR(32) NOT NULL DEFAULT '',
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY ux_cc_user_name (user_id, character_name),
  KEY idx_cc_user_sort (user_id, sort_order, id),
  CONSTRAINT fk_cc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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

  if (!(await tableExists(conn, database, 'consumption_characters'))) {
    await conn.query(CREATE_CHARACTERS);
    console.log('Created consumption_characters.');
  } else {
    console.log('consumption_characters exists, skip create.');
  }

  if (await tableExists(conn, database, 'consumption_entries')) {
    if (!(await columnExists(conn, database, 'consumption_entries', 'character_id'))) {
      await conn.query(
        `ALTER TABLE consumption_entries
         ADD COLUMN character_id BIGINT UNSIGNED NULL AFTER user_id,
         ADD CONSTRAINT fk_consumption_character FOREIGN KEY (character_id)
           REFERENCES consumption_characters(id) ON DELETE SET NULL`
      );
      console.log('Added consumption_entries.character_id.');
    }
    if (!(await columnExists(conn, database, 'consumption_entries', 'game_coin_w'))) {
      await conn.query(
        `ALTER TABLE consumption_entries
         ADD COLUMN game_coin_w DECIMAL(14,4) NOT NULL DEFAULT 0 COMMENT '游戏币消耗（万）' AFTER rmb_amount`
      );
      console.log('Added consumption_entries.game_coin_w.');
    }
  } else {
    console.warn('consumption_entries missing; run migrate-v7 first.');
  }

  await conn.end();
  console.log('migrate-v10 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
