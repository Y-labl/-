/**
 * 把「今天早上 9:00（运行本脚本的机器本地时区）→ 当前时刻」的秒数写入 meta，
 * 并设置 ledger_run_start_at_ms = 当前毫秒时间戳，使记账台刷新后：
 *   总在线时长 = 底数 + (now - runStart) = 从 9 点累计到现在，并继续走时。
 *
 * 用法（在 server 目录，须与 API 使用同一 MySQL）：
 *   node scripts/set-elapsed-from-9am-continue-timer.js
 *   node scripts/set-elapsed-from-9am-continue-timer.js 1 2026-04-11
 *
 * 可选环境变量 START_HOUR（默认 9）、START_MINUTE（默认 0）。
 * ELAPSED_ANCHOR_DATE=YYYY-MM-DD：「今早 9 点」落在哪一天（默认=运行脚本当日本地自然日）。
 *   业务日 biz_date 可以选历史日（如 2024-04-11），但计时时长仍按锚定日的 9:00→now，避免跨年级差被截断。
 */
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import mysql from 'mysql2/promise';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const CAP_SEC = 86400000;
const START_HOUR = Math.min(23, Math.max(0, Number(process.env.START_HOUR ?? 9)));
const START_MINUTE = Math.min(59, Math.max(0, Number(process.env.START_MINUTE ?? 0)));

function localYmd(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function nineAmLocalMs(ymd) {
  const [y, mo, da] = ymd.split('-').map(Number);
  return new Date(y, mo - 1, da, START_HOUR, START_MINUTE, 0, 0).getTime();
}

async function main() {
  const userId = Number(process.argv[2] || 1);
  const bizDate = process.argv[3] || localYmd();
  if (!Number.isFinite(userId) || userId < 1) {
    console.error('用法: node scripts/set-elapsed-from-9am-continue-timer.js [userId] [bizDate]');
    process.exit(1);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(bizDate)) {
    console.error('bizDate 需 YYYY-MM-DD');
    process.exit(1);
  }

  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'mhxy_ledger',
  });

  const [exists] = await pool.query(
    'SELECT 1 FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ? LIMIT 1',
    [userId, bizDate],
  );
  if (!exists.length) {
    console.log(`无 meta 行，插入占位行 user_id=${userId} biz_date=${bizDate}（online_roles=10，其余默认）`);
    await pool.query(
      `INSERT INTO mech_ledger_day_meta (user_id, biz_date, online_roles, cash_game_gold_w, point_card_points)
       VALUES (?, ?, 10, 0, 0)`,
      [userId, bizDate],
    );
  }

  const anchorYmd =
    process.env.ELAPSED_ANCHOR_DATE && /^\d{4}-\d{2}-\d{2}$/.test(process.env.ELAPSED_ANCHOR_DATE.trim())
      ? process.env.ELAPSED_ANCHOR_DATE.trim()
      : localYmd();
  const t9 = nineAmLocalMs(anchorYmd);
  const runMs = Date.now();
  let baseSec = Math.floor((runMs - t9) / 1000);
  if (!Number.isFinite(baseSec) || baseSec < 0) baseSec = 0;
  baseSec = Math.min(CAP_SEC, baseSec);

  console.log(
    `写入行 biz_date=${bizDate}；时长锚定日 anchorYmd=${anchorYmd} 本地 ${String(START_HOUR).padStart(2, '0')}:${String(START_MINUTE).padStart(2, '0')} → now`,
  );
  console.log(`ledger_base_elapsed_sec=${baseSec}, ledger_run_start_at_ms=${runMs}`);

  await pool.query(
    `UPDATE mech_ledger_day_meta
     SET
       ledger_base_elapsed_sec = ?,
       ledger_run_start_at_ms = ?,
       elapsed_sec = ?,
       ledger_point_card_json = CAST(? AS JSON)
     WHERE user_id = ? AND biz_date = ?`,
    [
      baseSec,
      runMs,
      baseSec,
      JSON.stringify({ closedSlices: [], segmentStartElapsed: baseSec }),
      userId,
      bizDate,
    ],
  );

  const [after] = await pool.query(
    `SELECT biz_date, elapsed_sec, ledger_base_elapsed_sec, ledger_run_start_at_ms,
            JSON_EXTRACT(ledger_point_card_json, '$.segmentStartElapsed') AS segStart
     FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?`,
    [userId, bizDate],
  );
  console.log('更新后:', JSON.stringify(after[0], null, 2));
  console.log('请刷新记账台；业务日须与上面 biz_date 一致。计时将延续。');

  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
