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

/** 各队现金梦幻币（万）JSON；毛合计仍写入 cash_game_gold_w；净 = Σ max(0, 现金_i−本金_i) */
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

  if (!(await columnExists(conn, database, 'mech_ledger_day_meta', 'team_cash_game_gold_w'))) {
    await conn.query(`
      ALTER TABLE mech_ledger_day_meta
      ADD COLUMN team_cash_game_gold_w JSON NULL
      COMMENT '各队现金梦幻币(万) JSON数组，与队伍本金档一一对应；NULL 表示旧版单字段毛收入'
      AFTER team_principals_w
    `);
    console.log('Added mech_ledger_day_meta.team_cash_game_gold_w.');
  } else {
    console.log('team_cash_game_gold_w already exists, skip.');
  }

  await conn.end();
  console.log('migrate-v26 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
