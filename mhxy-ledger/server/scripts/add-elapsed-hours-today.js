/**
 * 在 mech_ledger_day_meta 上为指定用户、指定业务日增加在线时长（秒）。
 *
 * - **停表**（ledger_run_start_at_ms 为空）：加 ledger_base_elapsed_sec 与 elapsed_sec。
 * - **跑表中**：只把 ledger_run_start_at_ms 往前拨（减 5h 的毫秒数）。界面总时长 = 底数 + (now − runStart)，
 *   若只加底数会被记账台定时 save-meta 用本地 base=0 盖掉；拨开始时刻可与客户端一致且刷新即生效。
 *
 * 仅作一次性手工补偿（例如误清时长后补回），勿做定时任务；须在「API 正在用的那台 MySQL」上跑。
 *
 * 用法（在 server 目录）：
 *   node scripts/add-elapsed-hours-today.js              # 默认 user_id=1，业务日=本机自然日今天，+5 小时
 *   node scripts/add-elapsed-hours-today.js 2            # user_id=2，今天，+5 小时
 *   node scripts/add-elapsed-hours-today.js 1 2026-04-11 # 指定业务日
 *   HOURS=3 node scripts/add-elapsed-hours-today.js      # 改加 3 小时
 *
 * 也可在 MySQL 客户端执行 scripts/compensate-five-hours-oneoff.sql（改 YOUR_USER_ID 与日期）。
 */
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import mysql from 'mysql2/promise';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const CAP_SEC = 86400000; // 与 save-meta 一致
const DEFAULT_HOURS = Number(process.env.HOURS || 5);
const EXTRA_SEC = Math.round(DEFAULT_HOURS * 3600);

function localYmd(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

async function main() {
  const userId = Number(process.argv[2] || 1);
  const bizDate = process.argv[3] || localYmd();
  if (!Number.isFinite(userId) || userId < 1) {
    console.error('无效 user_id，用法: node scripts/add-elapsed-hours-today.js [userId] [bizDate]');
    process.exit(1);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(bizDate)) {
    console.error('无效 bizDate，需 YYYY-MM-DD');
    process.exit(1);
  }

  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'mhxy_ledger',
  });

  const [before] = await pool.query(
    `SELECT user_id, biz_date, elapsed_sec, ledger_base_elapsed_sec, ledger_run_start_at_ms
     FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?`,
    [userId, bizDate],
  );
  if (!before.length) {
    console.error(`无记录: user_id=${userId} biz_date=${bizDate}。请先在记账台产生当日 meta 或手动插入。`);
    await pool.end();
    process.exit(1);
  }

  console.log('更新前:', JSON.stringify(before[0], null, 2));
  console.log(`将增加 ${DEFAULT_HOURS} 小时（${EXTRA_SEC} 秒）`);

  const row = before[0];
  const runMsRaw = row.ledger_run_start_at_ms;
  const runMs =
    runMsRaw != null && Number.isFinite(Number(runMsRaw)) && Number(runMsRaw) > 0
      ? Math.floor(Number(runMsRaw))
      : null;
  const extraMs = EXTRA_SEC * 1000;

  let result;
  if (runMs != null) {
    const newStart = Math.max(1, runMs - extraMs);
    console.log('当前为跑表中：将 ledger_run_start_at_ms 提前', EXTRA_SEC, '秒');
    [result] = await pool.query(
      `UPDATE mech_ledger_day_meta
       SET
         ledger_run_start_at_ms = ?,
         elapsed_sec = LEAST(?, COALESCE(elapsed_sec, 0) + ?)
       WHERE user_id = ? AND biz_date = ?`,
      [newStart, CAP_SEC, EXTRA_SEC, userId, bizDate],
    );
  } else {
    [result] = await pool.query(
      `UPDATE mech_ledger_day_meta
       SET
         ledger_base_elapsed_sec = LEAST(?, COALESCE(ledger_base_elapsed_sec, 0) + ?),
         elapsed_sec = LEAST(?, COALESCE(elapsed_sec, 0) + ?)
       WHERE user_id = ? AND biz_date = ?`,
      [CAP_SEC, EXTRA_SEC, CAP_SEC, EXTRA_SEC, userId, bizDate],
    );
  }

  const [after] = await pool.query(
    `SELECT user_id, biz_date, elapsed_sec, ledger_base_elapsed_sec, ledger_run_start_at_ms
     FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?`,
    [userId, bizDate],
  );
  console.log('影响行数:', result.affectedRows);
  console.log('更新后:', JSON.stringify(after[0], null, 2));

  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
