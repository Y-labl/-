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

async function rowCount(conn, table) {
  const [[r]] = await conn.query(`SELECT COUNT(*) AS c FROM \`${table}\``);
  return Number(r.c) || 0;
}

const CREATE_CATALOG_ITEMS = `
  CREATE TABLE catalog_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(128) NOT NULL,
    image_url VARCHAR(512) NOT NULL DEFAULT '',
    price_w DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    level_label VARCHAR(64) NOT NULL DEFAULT '',
    description VARCHAR(600) NOT NULL DEFAULT '',
    panel VARCHAR(32) NOT NULL DEFAULT 'fixed',
    sort_order INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_catalog_user_panel (user_id, panel, sort_order),
    CONSTRAINT fk_catalog_items_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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

  const hasNew = await tableExists(conn, database, 'catalog_items');
  const hasOld = await tableExists(conn, database, 'mech_catalog_items');

  if (hasOld && !hasNew) {
    await conn.query('RENAME TABLE mech_catalog_items TO catalog_items');
    console.log('Renamed mech_catalog_items -> catalog_items.');
  } else if (hasOld && hasNew) {
    const nNew = await rowCount(conn, 'catalog_items');
    if (nNew === 0) {
      await conn.query('DROP TABLE catalog_items');
      await conn.query('RENAME TABLE mech_catalog_items TO catalog_items');
      console.log('Dropped empty catalog_items, renamed mech_catalog_items -> catalog_items.');
    } else {
      console.log('Both tables exist and catalog_items has data; skip rename (please merge manually if needed).');
    }
  } else if (!hasNew && !hasOld) {
    await conn.query(CREATE_CATALOG_ITEMS);
    console.log('Created catalog_items.');
  } else {
    console.log('catalog_items exists, skip migrate-v5.');
  }

  await conn.end();
  console.log('migrate-v5 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
