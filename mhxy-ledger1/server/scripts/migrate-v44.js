import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column],
  );
  return rows.length > 0;
}

/**
 * 记账台 HUD：计时器暂停底数、运行起点、点卡分段 — 全部落在 day_meta，不再依赖 mech_ledger_session_state
 */
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

  if (!(await columnExists(conn, database, 'mech_ledger_day_meta', 'ledger_base_elapsed_sec'))) {
    await conn.query(`
      ALTER TABLE mech_ledger_day_meta
      ADD COLUMN ledger_base_elapsed_sec INT UNSIGNED NULL
        COMMENT '记账台计时：暂停态累计秒（与 run 分离）'
      AFTER elapsed_sec,
      ADD COLUMN ledger_run_start_at_ms BIGINT NULL
        COMMENT '记账台计时：正在跑时 performance 墙钟 ms，停表则为 NULL'
      AFTER ledger_base_elapsed_sec,
      ADD COLUMN ledger_point_card_json JSON NULL
        COMMENT '点卡分段 closedSlices + segmentStartElapsed'
      AFTER ledger_run_start_at_ms
    `);
    console.log('Added mech_ledger_day_meta ledger_* timer columns.');
  } else {
    console.log('mech_ledger_day_meta ledger_* columns exist, skip.');
  }

  await conn.end();
  console.log('migrate-v44 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
