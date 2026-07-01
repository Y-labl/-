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

  if (!(await tableExists(conn, database, 'mech_ledger_day_meta'))) {
    console.log('mech_ledger_day_meta missing; run migrate-v6 first.');
    await conn.end();
    process.exit(1);
  }

  if (!(await columnExists(conn, database, 'mech_ledger_day_meta', 'cash_game_gold_w'))) {
    await conn.query(
      `ALTER TABLE mech_ledger_day_meta
       ADD COLUMN cash_game_gold_w DECIMAL(14,4) NOT NULL DEFAULT 0
       COMMENT '刷得现金游戏币（万），与物品单价w无关'
       AFTER online_roles`
    );
    console.log('Added mech_ledger_day_meta.cash_game_gold_w.');
  } else {
    console.log('mech_ledger_day_meta.cash_game_gold_w already exists, skip.');
  }

  await conn.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
