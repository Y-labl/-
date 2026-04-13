/**
 * 恢复指定业务日的记账台 HUD（在线人数、队伍本金、计时起点等），不删物品聚合行。
 *
 * 用法（在 server 目录，与 API 同一 MySQL）：
 *   node scripts/restore-mech-day-hud.js
 *   node scripts/restore-mech-day-hud.js 1 2026-04-12
 *
 * 环境变量（可选）：
 *   ONLINE_ROLES   默认 10
 *   TEAM1_W        队伍一本金（万）默认 90
 *   TEAM2_W        队伍二本金（万）默认 370
 *   START_HOUR     上号时点，默认 7
 *   START_MINUTE   默认 50
 *   ANCHOR_YMD     上号日期，默认与 biz_date 相同
 */
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import mysql from 'mysql2/promise';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const CAP_SEC = 86400000;

function localYmd(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function localStartMs(ymd, hour, minute) {
  const [y, mo, da] = ymd.split('-').map(Number);
  return new Date(y, mo - 1, da, hour, minute, 0, 0).getTime();
}

async function main() {
  const userId = Number(process.argv[2] || 1);
  const bizDate = process.argv[3] || localYmd();
  if (!Number.isFinite(userId) || userId < 1) {
    console.error('用法: node scripts/restore-mech-day-hud.js [userId] [bizDate]');
    process.exit(1);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(bizDate)) {
    console.error('bizDate 需 YYYY-MM-DD');
    process.exit(1);
  }

  const onlineRoles = Math.max(1, Math.min(50, Math.floor(Number(process.env.ONLINE_ROLES ?? 10))));
  const t1 = Math.max(0, Number(process.env.TEAM1_W ?? 90));
  const t2 = Math.max(0, Number(process.env.TEAM2_W ?? 370));
  const startH = Math.min(23, Math.max(0, Math.floor(Number(process.env.START_HOUR ?? 7))));
  const startM = Math.min(59, Math.max(0, Math.floor(Number(process.env.START_MINUTE ?? 50))));
  const anchorYmd =
    process.env.ANCHOR_YMD && /^\d{4}-\d{2}-\d{2}$/.test(process.env.ANCHOR_YMD.trim())
      ? process.env.ANCHOR_YMD.trim()
      : bizDate;

  const teamSlots = Math.max(1, Math.min(4, Math.floor(onlineRoles / 5)));
  const principalsArr = [];
  for (let i = 0; i < teamSlots; i++) {
    if (i === 0) principalsArr.push(t1);
    else if (i === 1) principalsArr.push(t2);
    else principalsArr.push(0);
  }
  const cashArr = Array.from({ length: teamSlots }, () => 0);
  const principalsJson = JSON.stringify(principalsArr);
  const cashJson = JSON.stringify(cashArr);

  const runStartMs = localStartMs(anchorYmd, startH, startM);
  const now = Date.now();
  let elapsedSec = Math.floor((now - runStartMs) / 1000);
  if (!Number.isFinite(elapsedSec) || elapsedSec < 0) elapsedSec = 0;
  elapsedSec = Math.min(CAP_SEC, elapsedSec);

  const ledgerPcJson = JSON.stringify({
    closedSlices: [],
    segmentStartElapsed: 0,
  });

  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'mhxy_ledger',
  });

  const [before] = await pool.query(
    `SELECT user_id, biz_date, online_roles, team_principals_w, team_cash_game_gold_w,
            ledger_base_elapsed_sec, ledger_run_start_at_ms, elapsed_sec, point_card_points
     FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?`,
    [userId, bizDate],
  );
  console.log('更新前:', before.length ? JSON.stringify(before[0], null, 2) : '(无行，将插入)');

  await pool.query(
    `INSERT INTO mech_ledger_day_meta (
       user_id, biz_date, online_roles, cash_game_gold_w, team_principals_w, team_cash_game_gold_w,
       point_card_points, elapsed_sec, ledger_base_elapsed_sec, ledger_run_start_at_ms, ledger_point_card_json
     ) VALUES (?, ?, ?, 0, CAST(? AS JSON), CAST(? AS JSON), 0, ?, 0, ?, CAST(? AS JSON))
     ON DUPLICATE KEY UPDATE
       online_roles = VALUES(online_roles),
       cash_game_gold_w = VALUES(cash_game_gold_w),
       team_principals_w = VALUES(team_principals_w),
       team_cash_game_gold_w = VALUES(team_cash_game_gold_w),
       elapsed_sec = VALUES(elapsed_sec),
       ledger_base_elapsed_sec = VALUES(ledger_base_elapsed_sec),
       ledger_run_start_at_ms = VALUES(ledger_run_start_at_ms),
       ledger_point_card_json = VALUES(ledger_point_card_json)`,
    [userId, bizDate, onlineRoles, principalsJson, cashJson, elapsedSec, runStartMs, ledgerPcJson],
  );

  const [after] = await pool.query(
    `SELECT user_id, biz_date, online_roles, team_principals_w, team_cash_game_gold_w,
            ledger_base_elapsed_sec, ledger_run_start_at_ms, elapsed_sec, point_card_points, saved_at
     FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?`,
    [userId, bizDate],
  );
  console.log('更新后:', JSON.stringify(after[0], null, 2));
  console.log(
    `\n说明: 计时从 ${anchorYmd} ${String(startH).padStart(2, '0')}:${String(startM).padStart(2, '0')} 起算；刷新记账台后应显示约 ${Math.floor(elapsedSec / 60)} 分钟在线（并继续走时）。点卡累计未改（新插入为 0）；物品行在 mech_catalog_line_agg，本脚本不删。`,
  );

  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
