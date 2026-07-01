/**
 * 核对指定业务日是否在数据库里（mech_ledger_day_meta + mech_catalog_line_agg）。
 * 用于「保存并清除」后确认数据是否写入、应去每日收益选哪一天。
 *
 * 用法（在 server 目录）：
 *   node scripts/peek-mech-ledger-day.js 2026-04-12
 *   node scripts/peek-mech-ledger-day.js 2026-04-12 你的登录名
 */
import path from 'path';
import dotenv from 'dotenv';
import mysql from 'mysql2/promise';

dotenv.config({ path: path.join(process.cwd(), '.env') });

const biz = (process.argv[2] || '').trim() || '2026-04-12';
const username = (process.argv[3] || '').trim();

if (!/^\d{4}-\d{2}-\d{2}$/.test(biz)) {
  console.error('用法: node scripts/peek-mech-ledger-day.js YYYY-MM-DD [用户名]');
  process.exit(1);
}

async function main() {
  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'mhxy_ledger',
  });

  let userId = null;
  if (username) {
    const [urows] = await pool.query('SELECT id, username FROM users WHERE username = ? LIMIT 1', [username]);
    if (!urows.length) {
      console.error(`未找到用户: ${username}`);
      await pool.end();
      process.exit(1);
    }
    userId = urows[0].id;
    console.log(`用户: ${urows[0].username} (id=${userId})\n`);
  }

  const uidCondMeta = userId != null ? 'AND m.user_id = ?' : '';
  const uidCondAgg = userId != null ? 'AND user_id = ?' : '';
  const paramsMeta = userId != null ? [biz, userId] : [biz];
  const paramsAgg = userId != null ? [biz, userId] : [biz];

  const [meta] = await pool.query(
    `SELECT m.user_id, u.username, m.biz_date, m.point_card_points, m.online_roles, m.elapsed_sec,
            m.cash_game_gold_w, m.saved_at, m.point_card_saved_at
     FROM mech_ledger_day_meta m
     LEFT JOIN users u ON u.id = m.user_id
     WHERE m.biz_date = ? ${uidCondMeta}
     ORDER BY m.user_id`,
    paramsMeta,
  );

  const [lineAgg] = await pool.query(
    `SELECT user_id, COUNT(*) AS lineKinds, SUM(quantity) AS totalQty
     FROM mech_catalog_line_agg
     WHERE biz_date = ? ${uidCondAgg}
     GROUP BY user_id`,
    paramsAgg,
  );

  const [lineSample] = await pool.query(
    `SELECT a.user_id, u.username, a.item_name, a.unit_price_w, a.quantity
     FROM mech_catalog_line_agg a
     LEFT JOIN users u ON u.id = a.user_id
     WHERE a.biz_date = ? ${userId != null ? 'AND a.user_id = ?' : ''}
     ORDER BY a.user_id, a.id
     LIMIT 30`,
    paramsAgg,
  );

  console.log(`业务日 ${biz} — mech_ledger_day_meta 行数: ${meta.length}`);
  console.log(JSON.stringify(meta, null, 2));
  console.log(`\n物品行汇总（按 user）:`);
  console.log(JSON.stringify(lineAgg, null, 2));
  console.log(`\n物品行样例（最多 30 条）:`);
  console.log(JSON.stringify(lineSample, null, 2));

  if (!meta.length && !lineAgg.length) {
    console.log(
      '\n该日在库中无任何 meta / 物品行。可能：① 从未写入；② 写到了别的业务日（跨天保存选了「昨天」）；③ 登录的不是同一数据库用户。',
    );
    console.log('可再执行: node scripts/peek-mech-ledger-day.js 2026-04-11');
    console.log('           node scripts/peek-mech-ledger-day.js 2024-04-12');
  } else {
    console.log('\n数据在库里 → 前端请打开「每日收益」，日期选成上述 biz_date（与总览日期无关时要手动选对）。');
  }

  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
