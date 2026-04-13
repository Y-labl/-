import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column]
  );
  return rows.length > 0;
}

/** 多开队伍本金（万）JSON 数组，与 5 人一队对应；净现金 = cash_game_gold_w - sum(本金) */
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

  if (!(await columnExists(conn, database, 'mech_ledger_day_meta', 'team_principals_w'))) {
    await conn.query(`
      ALTER TABLE mech_ledger_day_meta
      ADD COLUMN team_principals_w JSON NULL
      COMMENT '队伍本金(万) JSON数组，5开1个10开2个…'
      AFTER cash_game_gold_w
    `);
    console.log('Added mech_ledger_day_meta.team_principals_w.');
  } else {
    console.log('team_principals_w already exists, skip.');
  }

  await conn.end();
  console.log('migrate-v23 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
