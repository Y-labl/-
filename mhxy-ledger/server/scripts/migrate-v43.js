import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column],
  );
  return rows.length > 0;
}

/**
 * 每日收益汇总：保存「保存收益」时刻记账台累计在线时长（秒）
 */
async function main() {
  const database = process.env.MYSQL_DATABASE || 'mhxy_ledger';
  const conn = await mysql.createConnection({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '12345678',
    multipleStatements: true,
  });
  await conn.query(`USE \`${database}\``);

  if (!(await columnExists(conn, database, 'mech_ledger_day_meta', 'elapsed_sec'))) {
    await conn.query(`
      ALTER TABLE mech_ledger_day_meta
      ADD COLUMN elapsed_sec INT UNSIGNED NULL
        COMMENT '保存收益快照时的累计在线时长（秒）；与记账台计时一致'
      AFTER online_roles
    `);
    console.log('Added mech_ledger_day_meta.elapsed_sec.');
  } else {
    console.log('mech_ledger_day_meta.elapsed_sec exists, skip.');
  }

  await conn.end();
  console.log('migrate-v43 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
