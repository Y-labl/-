import { Router } from 'express';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { todayStr, addDaysStr } from '../utils/date.js';
import { computeMechNetCashYuanForPeriod, monthDateRange } from '../utils/mechPeriodCash.js';

/** 与客户端 POINT_CARD_YUAN_PER_POINT 一致：1 点 = 0.1 元 */
const POINT_CARD_YUAN_PER_POINT = 0.1;

/**
 * 与 GET /mech-ledger/daily 的 elapsedSec 同口径：
 * 跑表时库内 elapsed_sec 可能滞后；用 ledger_base + 墙钟 − runStart 折算。
 */
function mechLedgerDisplayElapsedSecFromMetaRow(m) {
  if (!m) return null;
  const base = Math.max(0, Math.floor(Number(m.ledgerBaseElapsedSec) || 0));
  const runMs =
    m.ledgerRunStartAtMs != null && Number.isFinite(Number(m.ledgerRunStartAtMs))
      ? Math.floor(Number(m.ledgerRunStartAtMs))
      : null;
  if (runMs != null && runMs > 0) {
    const running = Math.max(0, Math.floor((Date.now() - runMs) / 1000));
    return base + running;
  }
  const col =
    m.elapsedSec != null && Number.isFinite(Number(m.elapsedSec))
      ? Math.max(0, Math.floor(Number(m.elapsedSec)))
      : 0;
  const out = Math.max(base, col);
  return out > 0 ? out : null;
}

async function sumDisplayElapsedSecBetween(pool, uid, dateStart, dateEnd) {
  const [rows] = await pool.query(
    `SELECT elapsed_sec AS elapsedSec,
            ledger_base_elapsed_sec AS ledgerBaseElapsedSec,
            ledger_run_start_at_ms AS ledgerRunStartAtMs
     FROM mech_ledger_day_meta
     WHERE user_id = ? AND biz_date BETWEEN ? AND ?`,
    [uid, dateStart, dateEnd],
  );
  let sum = 0;
  for (const r of rows || []) {
    const s = mechLedgerDisplayElapsedSecFromMetaRow(r);
    if (s != null && Number.isFinite(Number(s)) && Number(s) > 0) sum += Number(s);
  }
  return Math.max(0, Math.floor(sum));
}

/**
 * 区间内「点卡充值」人民币：优先 consumption_day_totals（消耗页「充值(元)」）；
 * 若为 0 再试旧表 consumption_entries；仍为 0 再试 point_card_entries（点数 × 0.1，如语音/快捷入账）。
 */
async function sumPointCardRechargeRmbBetween(pool, uid, dateStart, dateEnd) {
  let fromTotals = 0;
  try {
    const [[r]] = await pool.query(
      `SELECT COALESCE(SUM(rmb_amount),0) AS s FROM consumption_day_totals
       WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?`,
      [uid, dateStart, dateEnd]
    );
    fromTotals = Number(r?.s ?? 0);
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
  }

  if (fromTotals > 0) {
    return Math.round(fromTotals * 100) / 100;
  }

  let fromEntries = 0;
  try {
    const [[r]] = await pool.query(
      `SELECT COALESCE(SUM(rmb_amount),0) AS s FROM consumption_entries
       WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?`,
      [uid, dateStart, dateEnd]
    );
    fromEntries = Number(r?.s ?? 0);
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
  }

  if (fromEntries > 0) {
    return Math.round(fromEntries * 100) / 100;
  }

  try {
    const [[r]] = await pool.query(
      `SELECT COALESCE(SUM(points),0) AS p FROM point_card_entries
       WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?`,
      [uid, dateStart, dateEnd]
    );
    const pts = Number(r?.p ?? 0);
    const yuan = pts * POINT_CARD_YUAN_PER_POINT;
    return Math.round(yuan * 100) / 100;
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
    return 0;
  }
}

export const statsRouter = Router();
statsRouter.use(authRequired);

statsRouter.get('/overview', async (req, res) => {
  const bizDate = String(req.query.bizDate || todayStr());
  const uid = req.user.id;

  const [qcash, qpts, qgains, qtc, qcons] = await Promise.all([
    pool.query(
      'SELECT COALESCE(SUM(amount),0) AS s FROM cash_entries WHERE user_id = ? AND biz_date = ?',
      [uid, bizDate]
    ),
    pool.query(
      'SELECT COALESCE(point_card_points,0) AS s FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?',
      [uid, bizDate]
    ),
    pool.query(
      `SELECT COUNT(*) AS cnt, COALESCE(SUM(quantity),0) AS qty
       FROM item_gains WHERE user_id = ? AND biz_date = ?`,
      [uid, bizDate]
    ),
    pool.query(
      `SELECT d.id, d.task_id AS taskId, d.title AS taskName, d.started_at AS startedAt,
              d.ended_at AS endedAt, d.biz_date AS bizDate, d.dedupe_key AS dedupeKey
       FROM task_done_entries d
       WHERE d.user_id = ? AND d.biz_date = ?
       ORDER BY d.ended_at ASC, d.id ASC`,
      [uid, bizDate]
    ),
    /** 消耗页「当日记录」只写 consumption_day_totals；勿再叠加 consumption_entries，否则会重复累计 */
    (async () => {
      try {
        const [[r]] = await pool.query(
          `SELECT COALESCE(SUM(rmb_amount),0) AS s, COALESCE(SUM(dream_coin_w),0) AS cw
           FROM consumption_day_totals WHERE user_id = ? AND biz_date = ?`,
          [uid, bizDate]
        );
        return [[{ s: Number(r?.s ?? 0), cw: Number(r?.cw ?? 0) }], []];
      } catch (e) {
        if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
        try {
          const [[r]] = await pool.query(
            `SELECT COALESCE(SUM(rmb_amount),0) AS s, COALESCE(SUM(game_coin_w),0) AS cw
             FROM consumption_entries WHERE user_id = ? AND biz_date = ?`,
            [uid, bizDate]
          );
          return [[{ s: Number(r?.s ?? 0), cw: Number(r?.cw ?? 0) }], []];
        } catch (e2) {
          if (e2?.code === 'ER_NO_SUCH_TABLE') return [[{ s: 0, cw: 0 }], []];
          const msg = String(e2?.sqlMessage || e2?.message || '');
          if (!(e2?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('game_coin_w'))) throw e2;
          const [[r2]] = await pool.query(
            `SELECT COALESCE(SUM(rmb_amount),0) AS s FROM consumption_entries WHERE user_id = ? AND biz_date = ?`,
            [uid, bizDate]
          );
          return [[{ s: Number(r2?.s ?? 0), cw: 0 }], []];
        }
      }
    })(),
  ]);

  const cash = qcash[0];
  const pts = qpts[0];
  const gains = qgains[0];
  const tc = qtc[0];
  const cons = qcons[0];

  res.json({
    bizDate,
    cash: Number(cash[0]?.s ?? 0),
    pointCard: Number(pts[0]?.s ?? 0),
    consumptionRmb: Number(cons[0]?.s ?? 0),
    consumptionGameCoinW: Number(cons[0]?.cw ?? 0),
    itemGainCount: Number(gains[0]?.cnt ?? 0),
    itemQuantitySum: Number(gains[0]?.qty ?? 0),
    taskCompletions: tc,
  });
});

statsRouter.get('/weekly', async (req, res) => {
  const weekStart = String(req.query.weekStart || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(weekStart)) {
    return res.status(400).json({ error: 'weekStart 需为 YYYY-MM-DD（建议周一）' });
  }
  const weekEnd = addDaysStr(weekStart, 6);
  const uid = req.user.id;

  const [qcash, qcashRmb, qpts, qgains, qtasks, qOnlineMax, onlineElapsedSecSum, mechPeriod, pointCardRechargeYuan] =
    await Promise.all([
    pool.query(
      // "周现金" 统计记账台写入的现金梦幻币（万），来自 mech_ledger_day_meta.cash_game_gold_w
      'SELECT COALESCE(SUM(cash_game_gold_w),0) AS s FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date BETWEEN ? AND ?',
      [uid, weekStart, weekEnd]
    ),
    pool.query('SELECT COALESCE(SUM(amount),0) AS s FROM cash_entries WHERE user_id = ? AND biz_date BETWEEN ? AND ?', [
      uid,
      weekStart,
      weekEnd,
    ]),
    pool.query(
      `SELECT COALESCE(SUM(point_card_points),0) AS s FROM mech_ledger_day_meta
       WHERE user_id = ? AND biz_date BETWEEN ? AND ?`,
      [uid, weekStart, weekEnd]
    ),
    pool.query(
      // 物品数量（按日）：须用 DATE_FORMAT，避免 biz_date 经 JS Date/JSON 序列化成 UTC 后总览按日错位
      `SELECT DATE_FORMAT(biz_date, '%Y-%m-%d') AS d, COALESCE(SUM(quantity),0) AS qty
       FROM mech_catalog_line_agg WHERE user_id = ? AND biz_date BETWEEN ? AND ?
       GROUP BY biz_date ORDER BY biz_date`,
      [uid, weekStart, weekEnd]
    ),
    pool.query(
      `SELECT COUNT(*) AS c FROM task_done_entries WHERE user_id = ? AND biz_date BETWEEN ? AND ?`,
      [uid, weekStart, weekEnd]
    ),
    pool.query(
      `SELECT COALESCE(MAX(online_roles), 0) AS m FROM mech_ledger_day_meta
       WHERE user_id = ? AND biz_date BETWEEN ? AND ?`,
      [uid, weekStart, weekEnd]
    ),
    sumDisplayElapsedSecBetween(pool, uid, weekStart, weekEnd),
    computeMechNetCashYuanForPeriod(pool, uid, weekStart, weekEnd),
    sumPointCardRechargeRmbBetween(pool, uid, weekStart, weekEnd),
  ]);

  res.json({
    weekStart,
    weekEnd,
    cash: Number(qcash[0][0]?.s ?? 0),
    cashRmb: Number(qcashRmb[0][0]?.s ?? 0),
    pointCard: Number(qpts[0][0]?.s ?? 0),
    pointCardRechargeYuan,
    itemByDay: qgains[0],
    taskCompletionsCount: Number(qtasks[0][0]?.c ?? 0),
    onlineRolesWeekMax: Number(qOnlineMax[0][0]?.m ?? 0),
    onlineElapsedSecSum,
    netCashYuan: mechPeriod.ok ? mechPeriod.netCashYuan : null,
    totalCashYuan: mechPeriod.ok ? mechPeriod.totalCashYuan : null,
  });
});

statsRouter.get('/monthly', async (req, res) => {
  const year = Number(req.query.year || new Date().getFullYear());
  const month = Number(req.query.month || new Date().getMonth() + 1);
  if (!year || month < 1 || month > 12) return res.status(400).json({ error: 'year/month 无效' });
  const uid = req.user.id;

  const { start: monthStart, end: monthEnd } = monthDateRange(year, month);

  const [qcash, qcashRmb, qpts, qgains, qtasks, onlineElapsedSecSum, mechPeriod, pointCardRechargeYuan] = await Promise.all([
    pool.query(
      // "月现金" 统计记账台写入的现金梦幻币（万）
      `SELECT COALESCE(SUM(cash_game_gold_w),0) AS s FROM mech_ledger_day_meta
       WHERE user_id = ? AND YEAR(biz_date) = ? AND MONTH(biz_date) = ?`,
      [uid, year, month]
    ),
    pool.query(
      'SELECT COALESCE(SUM(amount),0) AS s FROM cash_entries WHERE user_id = ? AND biz_date BETWEEN ? AND ?',
      [uid, monthStart, monthEnd]
    ),
    pool.query(
      `SELECT COALESCE(SUM(point_card_points),0) AS s FROM mech_ledger_day_meta
       WHERE user_id = ? AND YEAR(biz_date) = ? AND MONTH(biz_date) = ?`,
      [uid, year, month]
    ),
    pool.query(
      `SELECT DATE_FORMAT(biz_date, '%Y-%m-%d') AS d, COALESCE(SUM(quantity),0) AS qty
       FROM mech_catalog_line_agg WHERE user_id = ? AND YEAR(biz_date) = ? AND MONTH(biz_date) = ?
       GROUP BY biz_date ORDER BY biz_date`,
      [uid, year, month]
    ),
    pool.query(
      `SELECT COUNT(*) AS c FROM task_done_entries
       WHERE user_id = ? AND YEAR(biz_date) = ? AND MONTH(biz_date) = ?`,
      [uid, year, month]
    ),
    sumDisplayElapsedSecBetween(pool, uid, monthStart, monthEnd),
    computeMechNetCashYuanForPeriod(pool, uid, monthStart, monthEnd),
    sumPointCardRechargeRmbBetween(pool, uid, monthStart, monthEnd),
  ]);

  // 平均每日在线时长：自然日口径
  const endDay = Number(String(monthEnd).slice(-2)) || 30; // YYYY-MM-DD
  const now = new Date();
  const isCurrentMonth = now.getFullYear() === year && now.getMonth() + 1 === month;
  const todayDay = now.getDate();
  const avgDayCount = Math.max(1, isCurrentMonth ? Math.min(endDay, todayDay) : endDay);

  res.json({
    year,
    month,
    cash: Number(qcash[0][0]?.s ?? 0),
    cashRmb: Number(qcashRmb[0][0]?.s ?? 0),
    pointCard: Number(qpts[0][0]?.s ?? 0),
    pointCardRechargeYuan,
    itemByDay: qgains[0],
    taskCompletionsCount: Number(qtasks[0][0]?.c ?? 0),
    onlineElapsedSecSum,
    onlineAvgDayCount: avgDayCount,
    netCashYuan: mechPeriod.ok ? mechPeriod.netCashYuan : null,
    totalCashYuan: mechPeriod.ok ? mechPeriod.totalCashYuan : null,
  });
});
