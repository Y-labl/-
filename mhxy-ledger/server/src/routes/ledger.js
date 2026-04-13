import { Router } from 'express';
import multer from 'multer';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { todayStr } from '../utils/date.js';

const speechUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 20 * 1024 * 1024 },
});

export const ledgerRouter = Router();
ledgerRouter.use(authRequired);

ledgerRouter.use((req, res, next) => {
  const n = Number(req.user?.id);
  if (!Number.isFinite(n) || n < 1) {
    return res.status(401).json({ error: '登录状态异常，请重新登录' });
  }
  req.user = { ...req.user, id: n };
  next();
});

/** 与客户端 ledgerYuanRatio LEDGER_GAME_WAN_ANCHOR 一致 */
const MECH_LEDGER_GAME_WAN_ANCHOR = 3000;

function parseBizDate(body, query) {
  const raw = body?.bizDate ?? query?.bizDate;
  const s = String(raw || '').trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  return todayStr();
}

/**
 * GET /mech-ledger/daily 的 elapsedSec：与记账台 HUD 一致的总秒数。
 * 跑表时库内 elapsed_sec 可能滞后（定时 save-meta）；须用 ledger_base + 墙钟 − runStart。
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

/** consumption_day_totals.catalog_lines_json → [{ catalogItemId, quantity, name }] */
function normalizeCatalogLinesFromDb(raw) {
  let arr = raw;
  if (arr == null || arr === '') return [];
  if (typeof Buffer !== 'undefined' && Buffer.isBuffer(arr)) {
    try {
      arr = JSON.parse(arr.toString('utf8'));
    } catch {
      return [];
    }
  }
  if (typeof arr === 'string') {
    try {
      arr = JSON.parse(arr);
    } catch {
      return [];
    }
  }
  if (!Array.isArray(arr)) return [];
  const out = [];
  for (const x of arr) {
    const catalogItemId = Math.floor(Number(x?.catalogItemId ?? x?.catalog_item_id));
    const quantity = Math.floor(Number(x?.quantity));
    const name = String(x?.name ?? '');
    if (!Number.isFinite(catalogItemId) || catalogItemId < 1) continue;
    if (!Number.isFinite(quantity) || quantity < 1) continue;
    out.push({ catalogItemId, quantity, name });
  }
  out.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
  return out;
}

function roundRmbYuan2(n) {
  const x = Number(n);
  if (!Number.isFinite(x) || x < 0) return 0;
  return Math.round(x * 100) / 100;
}

/** 记账台金价：人民币对应「MECH_LEDGER_GAME_WAN_ANCHOR 万」游戏币 */
ledgerRouter.get('/mech-ledger/prefs', async (req, res) => {
  const uid = req.user.id;
  try {
    const [rows] = await pool.query(
      'SELECT rmb_yuan AS rmbYuan FROM mech_ledger_user_prefs WHERE user_id = ? LIMIT 1',
      [uid]
    );
    if (!rows.length) {
      return res.json({
        gameWan: MECH_LEDGER_GAME_WAN_ANCHOR,
        yuan: 30,
        persisted: false,
      });
    }
    const y = roundRmbYuan2(rows[0].rmbYuan);
    res.json({ gameWan: MECH_LEDGER_GAME_WAN_ANCHOR, yuan: y, persisted: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 mech_ledger_user_prefs。请在 server 目录执行：npm run db:migrate-v8',
      });
    }
    throw e;
  }
});

ledgerRouter.put('/mech-ledger/prefs', async (req, res) => {
  const uid = req.user.id;
  const rawYuan = Number(req.body?.yuan);
  if (!Number.isFinite(rawYuan) || rawYuan < 0 || rawYuan > 99999999.99) {
    return res.status(400).json({ error: 'yuan 无效（需为 0～99999999.99 之间的金额）' });
  }
  const yuan = roundRmbYuan2(rawYuan);
  try {
    await pool.query(
      `INSERT INTO mech_ledger_user_prefs (user_id, rmb_yuan) VALUES (?, ?)
       ON DUPLICATE KEY UPDATE rmb_yuan = VALUES(rmb_yuan)`,
      [uid, yuan]
    );
    res.json({ gameWan: MECH_LEDGER_GAME_WAN_ANCHOR, yuan, persisted: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 mech_ledger_user_prefs。请在 server 目录执行：npm run db:migrate-v8',
      });
    }
    throw e;
  }
});

const MECH_ONLINE_PRESETS = [5, 10, 15, 20];

function teamSlotsFromPresetAndCount(onlinePresetRaw, onlineCount) {
  const c = Math.max(1, Math.min(50, Math.floor(Number(onlineCount) || 1)));
  const slotsFromCount = Math.max(1, Math.min(4, Math.floor(c / 5)));
  const p = Number(onlinePresetRaw);
  if (MECH_ONLINE_PRESETS.includes(p)) {
    const slotsFromPreset = Math.max(1, Math.min(4, p / 5));
    return Math.max(slotsFromPreset, slotsFromCount);
  }
  return slotsFromCount;
}

/** @param {unknown} raw */
function normalizeTeamPrincipalsForSave(raw, teamSlots) {
  const arr = Array.isArray(raw) ? raw : [];
  const out = [];
  for (let i = 0; i < teamSlots; i++) {
    const n = Number(arr[i]);
    out.push(Number.isFinite(n) && n >= 0 ? Math.min(1e12, n) : 0);
  }
  return out;
}

/** 净现金（万）= Σ(队 i 现金 − 队 i 本金)；队现金 ≤0 视为未填，该队不参与（不减本金） */
function netCashFromTeamRows(teamCashW, teamPrincipalsW, teamSlots) {
  let net = 0;
  for (let i = 0; i < teamSlots; i++) {
    const c = Number(teamCashW[i]) || 0;
    const p = Number(teamPrincipalsW[i]) || 0;
    if (c <= 0) continue;
    net += c - p;
  }
  return net;
}

/** @param {unknown} val */
function parseTeamPrincipalsColumn(val) {
  if (val == null || val === '') return [];
  let v = val;
  if (typeof Buffer !== 'undefined' && Buffer.isBuffer(v)) {
    try {
      v = JSON.parse(v.toString('utf8'));
    } catch {
      return [];
    }
  }
  if (typeof v === 'string') {
    try {
      v = JSON.parse(v);
    } catch {
      return [];
    }
  }
  if (!Array.isArray(v)) return [];
  return v.map((x) => {
    const n = Number(x);
    return Number.isFinite(n) && n >= 0 ? n : 0;
  });
}

const MECH_YAKSHA_KEYS = [
  'y1',
  'y2',
  'y3',
  'y4',
  'y5',
  'hm',
  'lg',
  'wn',
  'ym',
  'xx',
  'gj',
  'total',
  'turtle',
  'drop',
];

/** 点卡分段落库 JSON字符串；无效则返回 null */
function normalizeLedgerPointCardJson(pcIn) {
  if (pcIn == null || typeof pcIn !== 'object') return null;
  const arr = Array.isArray(pcIn.closedSlices) ? pcIn.closedSlices : [];
  const closedSlices = [];
  for (let i = 0; i < Math.min(arr.length, 500); i++) {
    const s = arr[i];
    if (!s || typeof s !== 'object') continue;
    const durationSec = Math.max(0, Math.min(8640000, Math.floor(Number(s.durationSec) || 0)));
    const roles = Math.max(0, Math.min(999, Math.floor(Number(s.roles) || 0)));
    if (durationSec > 0) closedSlices.push({ durationSec, roles });
  }
  const segmentStartElapsed = Math.max(
    0,
    Math.min(8640000, Math.floor(Number(pcIn.segmentStartElapsed) || 0)),
  );
  return JSON.stringify({ closedSlices, segmentStartElapsed });
}

function parseLedgerPointCardFromRow(raw) {
  if (raw == null || raw === '') return null;
  let v = raw;
  if (typeof Buffer !== 'undefined' && Buffer.isBuffer(v)) {
    try {
      v = JSON.parse(v.toString('utf8'));
    } catch {
      return null;
    }
  }
  if (typeof v === 'string') {
    try {
      v = JSON.parse(v);
    } catch {
      return null;
    }
  }
  if (!v || typeof v !== 'object') return null;
  const arr = Array.isArray(v.closedSlices) ? v.closedSlices : [];
  const closedSlices = [];
  for (let i = 0; i < Math.min(arr.length, 500); i++) {
    const s = arr[i];
    if (!s || typeof s !== 'object') continue;
    const durationSec = Math.max(0, Math.min(8640000, Math.floor(Number(s.durationSec) || 0)));
    const roles = Math.max(0, Math.min(999, Math.floor(Number(s.roles) || 0)));
    if (durationSec > 0) closedSlices.push({ durationSec, roles });
  }
  const segmentStartElapsed = Math.max(
    0,
    Math.min(8640000, Math.floor(Number(v.segmentStartElapsed) || 0)),
  );
  return { closedSlices, segmentStartElapsed };
}

function normalizeMechSessionState(raw) {
  const o = raw && typeof raw === 'object' ? raw : {};
  const preset = MECH_ONLINE_PRESETS.includes(Number(o.onlinePreset)) ? Number(o.onlinePreset) : 5;
  const extra = Math.max(0, Math.min(999, Math.floor(Number(o.onlineExtra) || 0)));
  let baseElapsedSec = Math.max(0, Math.floor(Number(o.baseElapsedSec) || 0));
  if (baseElapsedSec > 8640000) baseElapsedSec = 8640000;
  let runStartAt = o.runStartAt != null ? Number(o.runStartAt) : null;
  if (runStartAt != null && (!Number.isFinite(runStartAt) || runStartAt <= 0)) runStartAt = null;
  let pointCard = undefined;
  const pcIn = o.pointCard && typeof o.pointCard === 'object' ? o.pointCard : null;
  if (pcIn) {
    const arr = Array.isArray(pcIn.closedSlices) ? pcIn.closedSlices : [];
    const closedSlices = [];
    const maxSlices = 500;
    for (let i = 0; i < Math.min(arr.length, maxSlices); i++) {
      const s = arr[i];
      if (!s || typeof s !== 'object') continue;
      const durationSec = Math.max(0, Math.min(8640000, Math.floor(Number(s.durationSec) || 0)));
      const roles = Math.max(0, Math.min(999, Math.floor(Number(s.roles) || 0)));
      if (durationSec > 0) closedSlices.push({ durationSec, roles });
    }
    const segmentStartElapsed = Math.max(
      0,
      Math.min(8640000, Math.floor(Number(pcIn.segmentStartElapsed) || 0)),
    );
    pointCard = { closedSlices, segmentStartElapsed };
  }
  const out = {
    onlinePreset: preset,
    onlineExtra: extra,
    baseElapsedSec,
    runStartAt,
  };
  if (pointCard) out.pointCard = pointCard;
  const lbRaw = String(o.ledgerBizDate ?? '').trim().slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(lbRaw)) {
    out.ledgerBizDate = lbRaw;
  }
  function norm4StrArr(arr) {
    if (!Array.isArray(arr) || arr.length < 1) return undefined;
    const pad = ['', '', '', ''];
    for (let i = 0; i < 4; i++) {
      pad[i] = String(arr[i] ?? '').slice(0, 48);
    }
    return pad;
  }
  const tp = norm4StrArr(o.teamPrincipalInputStrs);
  const tc = norm4StrArr(o.teamCashInputStrs);
  if (tp) out.teamPrincipalInputStrs = tp;
  if (tc) out.teamCashInputStrs = tc;
  return out;
}

/** 写入当日 meta（现金/本金/在线人数；可选同步当前点卡累计，不更新 point_card_saved_at） */
ledgerRouter.post('/mech-ledger/save-meta', async (req, res) => {
  const uid = req.user.id;
  const rawMetaBiz = String(req.body?.bizDate ?? req.query?.bizDate ?? '').trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(rawMetaBiz)) {
    return res.status(400).json({ error: 'save-meta 必须提供有效 bizDate（YYYY-MM-DD），不可省略' });
  }
  const bizDate = rawMetaBiz;
  const onlineCount = Math.max(1, Math.min(50, Math.floor(Number(req.body?.onlineCount) || 1)));
  const teamSlots = teamSlotsFromPresetAndCount(req.body?.onlinePreset, onlineCount);

  const useTeamCash = Array.isArray(req.body?.teamCashGameGoldW);
  let cashGold;
  let teamCashJson;
  if (useTeamCash) {
    const teamCashGameGoldW = normalizeTeamPrincipalsForSave(req.body.teamCashGameGoldW, teamSlots);
    cashGold = teamCashGameGoldW.reduce((a, b) => a + b, 0);
    teamCashJson = JSON.stringify(teamCashGameGoldW);
  } else {
    const cashGameGoldW = Number(req.body?.cashGameGoldW ?? req.body?.cash_game_gold_w ?? 0);
    cashGold = Number.isFinite(cashGameGoldW) && cashGameGoldW >= 0 ? cashGameGoldW : NaN;
    teamCashJson = null;
  }
  if (Number.isNaN(cashGold)) {
    return res.status(400).json({ error: '现金梦幻币（万）无效' });
  }
  const teamPrincipalsW = normalizeTeamPrincipalsForSave(req.body?.teamPrincipalsW, teamSlots);
  const principalsJson = JSON.stringify(teamPrincipalsW);

  const bodyRaw = req.body ?? {};
  const hasElapsed =
    Object.prototype.hasOwnProperty.call(bodyRaw, 'elapsedSec') ||
    Object.prototype.hasOwnProperty.call(bodyRaw, 'elapsed_sec');
  const elapsedSecMeta = hasElapsed
    ? Math.max(0, Math.min(86400000, Math.floor(Number(bodyRaw.elapsedSec ?? bodyRaw.elapsed_sec) || 0)))
    : null;
  const elapsedCol = hasElapsed ? ', elapsed_sec' : '';
  const elapsedPh = hasElapsed ? ', ?' : '';
  const elapsedUpd = hasElapsed ? ', elapsed_sec = VALUES(elapsed_sec)' : '';

  const pcIn = req.body?.pointCardPoints;
  let syncPointCard = false;
  let pointCardPoints = 0;
  if (pcIn !== undefined && pcIn !== null && pcIn !== '') {
    const p = Number(pcIn);
    if (!Number.isFinite(p) || p < 0) {
      return res.status(400).json({ error: '点卡点数无效' });
    }
    syncPointCard = true;
    pointCardPoints = Math.max(0, p);
  }

  const hasLedgerHud =
    Object.prototype.hasOwnProperty.call(bodyRaw, 'ledgerBaseElapsedSec') ||
    Object.prototype.hasOwnProperty.call(bodyRaw, 'ledger_base_elapsed_sec') ||
    Object.prototype.hasOwnProperty.call(bodyRaw, 'ledgerRunStartAtMs') ||
    Object.prototype.hasOwnProperty.call(bodyRaw, 'ledgerRunStartAt') ||
    Object.prototype.hasOwnProperty.call(bodyRaw, 'ledgerPointCard') ||
    Object.prototype.hasOwnProperty.call(bodyRaw, 'ledger_point_card');

  let ledgerBase = null;
  let ledgerRunMs = null;
  let ledgerPcStr = null;
  if (hasLedgerHud) {
    ledgerBase = Math.max(
      0,
      Math.min(86400000, Math.floor(Number(bodyRaw.ledgerBaseElapsedSec ?? bodyRaw.ledger_base_elapsed_sec) || 0)),
    );
    const r = bodyRaw.ledgerRunStartAtMs ?? bodyRaw.ledgerRunStartAt;
    if (r == null || r === '') ledgerRunMs = null;
    else {
      const n = Number(r);
      ledgerRunMs = Number.isFinite(n) && n > 0 ? Math.floor(n) : null;
    }
    const pcRaw = bodyRaw.ledgerPointCard ?? bodyRaw.ledger_point_card;
    ledgerPcStr = normalizeLedgerPointCardJson(pcRaw);
  }
  const ledgerCols = hasLedgerHud ? ', ledger_base_elapsed_sec, ledger_run_start_at_ms, ledger_point_card_json' : '';
  const ledgerPh = hasLedgerHud ? ', ?, ?, CAST(? AS JSON)' : '';
  const ledgerUpd = hasLedgerHud
    ? ', ledger_base_elapsed_sec = VALUES(ledger_base_elapsed_sec), ledger_run_start_at_ms = VALUES(ledger_run_start_at_ms), ledger_point_card_json = VALUES(ledger_point_card_json)'
    : '';

  try {
    if (syncPointCard) {
      const params = [
        uid,
        bizDate,
        onlineCount,
        cashGold,
        principalsJson,
        teamCashJson,
        pointCardPoints,
        ...(hasElapsed ? [elapsedSecMeta] : []),
        ...(hasLedgerHud ? [ledgerBase, ledgerRunMs, ledgerPcStr] : []),
      ];
      await pool.query(
        `INSERT INTO mech_ledger_day_meta (user_id, biz_date, online_roles, cash_game_gold_w, team_principals_w, team_cash_game_gold_w, point_card_points${elapsedCol}${ledgerCols})
         VALUES (?,?,?,?,CAST(? AS JSON),CAST(? AS JSON),?${elapsedPh}${ledgerPh})
         ON DUPLICATE KEY UPDATE online_roles = VALUES(online_roles),
           cash_game_gold_w = VALUES(cash_game_gold_w), team_principals_w = VALUES(team_principals_w),
           team_cash_game_gold_w = VALUES(team_cash_game_gold_w),
           point_card_points = VALUES(point_card_points)${elapsedUpd}${ledgerUpd}`,
        params,
      );
    } else {
      const params = [
        uid,
        bizDate,
        onlineCount,
        cashGold,
        principalsJson,
        teamCashJson,
        ...(hasElapsed ? [elapsedSecMeta] : []),
        ...(hasLedgerHud ? [ledgerBase, ledgerRunMs, ledgerPcStr] : []),
      ];
      await pool.query(
        `INSERT INTO mech_ledger_day_meta (user_id, biz_date, online_roles, cash_game_gold_w, team_principals_w, team_cash_game_gold_w${elapsedCol}${ledgerCols})
         VALUES (?,?,?,?,CAST(? AS JSON),CAST(? AS JSON)${elapsedPh}${ledgerPh})
         ON DUPLICATE KEY UPDATE online_roles = VALUES(online_roles),
           cash_game_gold_w = VALUES(cash_game_gold_w), team_principals_w = VALUES(team_principals_w),
           team_cash_game_gold_w = VALUES(team_cash_game_gold_w)${elapsedUpd}${ledgerUpd}`,
        params,
      );
    }
    res.json({ ok: true, bizDate });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少记账台同步表。请在 server 目录执行：npm run db:migrate-v6',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR') {
      const msg = String(e?.sqlMessage || e?.message || '');
      if (msg.includes('elapsed_sec')) {
        return res.status(503).json({
          error: '数据库缺少在线时长字段。请在 server 目录执行：node scripts/migrate-v43.js',
        });
      }
      if (msg.includes('ledger_base_elapsed') || msg.includes('ledger_run_start') || msg.includes('ledger_point_card')) {
        return res.status(503).json({
          error: '数据库缺少记账台计时字段。请在 server 目录执行：node scripts/migrate-v44.js',
        });
      }
      if (msg.includes('team_principa')) {
        return res.status(503).json({
          error: '数据库缺少队伍本金字段。请在 server 目录执行：npm run db:migrate-v23',
        });
      }
      if (msg.includes('team_cash_game')) {
        return res.status(503).json({
          error: '数据库缺少各队现金字段。请在 server 目录执行：npm run db:migrate-v26',
        });
      }
    }
    throw e;
  }
});

/** 读取旧版 session（仅用于一次性迁移到 mech_ledger_day_meta；新客户端不再写入此表） */
ledgerRouter.get('/mech-ledger/session-state', async (req, res) => {
  const uid = req.user.id;
  try {
    const [rows] = await pool.query(
      'SELECT state_json AS stateJson FROM mech_ledger_session_state WHERE user_id = ? LIMIT 1',
      [uid],
    );
    if (!rows.length) {
      return res.json({ persisted: false, state: null });
    }
    const state = normalizeMechSessionState(rows[0].stateJson);
    res.json({ persisted: true, state });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 mech_ledger_session_state。请在 server 目录执行：npm run db:migrate-v9',
      });
    }
    throw e;
  }
});

/** 兼容旧客户端；新前端不依赖写入 */
ledgerRouter.put('/mech-ledger/session-state', async (req, res) => {
  const uid = req.user.id;
  const state = normalizeMechSessionState(req.body?.state);
  try {
    await pool.query(
      `INSERT INTO mech_ledger_session_state (user_id, state_json) VALUES (?, ?)
       ON DUPLICATE KEY UPDATE state_json = VALUES(state_json)`,
      [uid, JSON.stringify(state)],
    );
    res.json({ ok: true, state });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 mech_ledger_session_state。请在 server 目录执行：npm run db:migrate-v9',
      });
    }
    throw e;
  }
});

/** 记账台迁移：session 已写入 day_meta 后删除，避免下次再用旧 JSON 覆盖 */
ledgerRouter.delete('/mech-ledger/session-state', async (req, res) => {
  const uid = req.user.id;
  try {
    await pool.query('DELETE FROM mech_ledger_session_state WHERE user_id = ?', [uid]);
    res.json({ ok: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.json({ ok: true });
    }
    throw e;
  }
});

function clampLine(raw) {
  const name = String(raw?.name ?? '').trim().slice(0, 191);
  const valueW = Number(raw?.valueW);
  const count = Math.max(0, Math.min(99999, Math.floor(Number(raw?.count))));
  if (!name || Number.isNaN(valueW) || valueW < 0 || count < 1) return null;
  return { name, valueW, count };
}

/** 覆盖写入当日物品行（记账台右侧列表同步） */
ledgerRouter.put('/mech-ledger/today-lines', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  const linesIn = Array.isArray(req.body?.lines) ? req.body.lines : [];
  if (linesIn.length > 800) {
    return res.status(400).json({ error: '行数过多' });
  }
  const lines = [];
  for (const row of linesIn) {
    const c = clampLine(row);
    if (c) lines.push(c);
  }
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    await conn.query('DELETE FROM mech_catalog_line_agg WHERE user_id = ? AND biz_date = ?', [uid, bizDate]);
    if (lines.length) {
      const values = lines.map(() => '(?,?,?,?,?)').join(',');
      const flat = lines.flatMap((l) => [uid, bizDate, l.name, l.valueW, l.count]);
      await conn.query(
        `INSERT INTO mech_catalog_line_agg (user_id, biz_date, item_name, unit_price_w, quantity) VALUES ${values}`,
        flat
      );
    }
    await conn.commit();
    res.json({ ok: true, bizDate, lineCount: lines.length });
  } catch (e) {
    await conn.rollback();
    const code = e?.code;
    if (code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少记账台同步表。请在 server 目录执行：npm run db:migrate-v6',
      });
    }
    throw e;
  } finally {
    conn.release();
  }
});

/** 保存当日点卡消耗快照（点「保存收益」时调用） */
ledgerRouter.post('/mech-ledger/save-day', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  const pointCardPoints = Math.max(0, Number(req.body?.pointCardPoints));
  const onlineCount = Math.max(1, Math.min(50, Math.floor(Number(req.body?.onlineCount) || 1)));
  const teamSlots = teamSlotsFromPresetAndCount(req.body?.onlinePreset, onlineCount);
  const useTeamCash = Array.isArray(req.body?.teamCashGameGoldW);
  let cashGold;
  let teamCashJson;
  let teamCashGameGoldW;
  if (useTeamCash) {
    teamCashGameGoldW = normalizeTeamPrincipalsForSave(req.body.teamCashGameGoldW, teamSlots);
    cashGold = teamCashGameGoldW.reduce((a, b) => a + b, 0);
    teamCashJson = JSON.stringify(teamCashGameGoldW);
  } else {
    teamCashGameGoldW = null;
    const cashGameGoldW = Number(req.body?.cashGameGoldW ?? req.body?.cash_game_gold_w ?? 0);
    cashGold = Number.isFinite(cashGameGoldW) && cashGameGoldW >= 0 ? cashGameGoldW : NaN;
    teamCashJson = null;
  }
  if (Number.isNaN(pointCardPoints)) {
    return res.status(400).json({ error: '点卡点数无效' });
  }
  if (Number.isNaN(cashGold)) {
    return res.status(400).json({ error: '现金梦幻币（万）无效' });
  }
  const teamPrincipalsW = normalizeTeamPrincipalsForSave(req.body?.teamPrincipalsW, teamSlots);
  const principalsJson = JSON.stringify(teamPrincipalsW);
  const elapsedRaw = req.body?.elapsedSec ?? req.body?.elapsed_sec;
  const elapsedSec =
    elapsedRaw !== undefined && elapsedRaw !== null && elapsedRaw !== ''
      ? Math.max(0, Math.min(86400000, Math.floor(Number(elapsedRaw) || 0)))
      : null;
  try {
    await pool.query(
      `INSERT INTO mech_ledger_day_meta (user_id, biz_date, point_card_points, online_roles, elapsed_sec, cash_game_gold_w, team_principals_w, team_cash_game_gold_w)
       VALUES (?,?,?,?,?,?,CAST(? AS JSON),CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE point_card_points = VALUES(point_card_points), online_roles = VALUES(online_roles),
         elapsed_sec = VALUES(elapsed_sec),
         cash_game_gold_w = VALUES(cash_game_gold_w), team_principals_w = VALUES(team_principals_w),
         team_cash_game_gold_w = VALUES(team_cash_game_gold_w),
         point_card_saved_at = CURRENT_TIMESTAMP,
         saved_at = CURRENT_TIMESTAMP`,
      [uid, bizDate, pointCardPoints, onlineCount, elapsedSec, cashGold, principalsJson, teamCashJson]
    );
    res.json({
      ok: true,
      bizDate,
      pointCardPoints,
      onlineCount,
      cashGameGoldW: cashGold,
      teamPrincipalsW,
      ...(teamCashGameGoldW ? { teamCashGameGoldW } : {}),
    });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少记账台同步表。请在 server 目录执行：npm run db:migrate-v6',
      });
    }
    const msg = String(e?.sqlMessage || e?.message || '');
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('cash_game_gold_w')) {
      return res.status(503).json({
        error: '数据库缺少现金梦幻币字段。请在 server 目录执行：npm run db:migrate-v13',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('team_principa')) {
      return res.status(503).json({
        error: '数据库缺少队伍本金字段。请在 server 目录执行：npm run db:migrate-v23',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('team_cash_game')) {
      return res.status(503).json({
        error: '数据库缺少各队现金字段。请在 server 目录执行：npm run db:migrate-v26',
      });
    }
    throw e;
  }
});

/** 单日明细：物品行 + 点卡快照 */
ledgerRouter.get('/mech-ledger/daily', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  try {
    const [rows] = await pool.query(
      `SELECT item_name AS name, unit_price_w AS valueW, quantity AS count
       FROM mech_catalog_line_agg WHERE user_id = ? AND biz_date = ?
       ORDER BY id ASC`,
      [uid, bizDate]
    );

    // 这些物品通常直接卖商人计入现金，净现金折算时应从物品收益中扣除避免重复计入。
    const VENDOR_TRASH_NAMES = new Set(['乐器', '花', '玫瑰花', '图册']);
    let vendorTrashW = 0;
    for (const r of rows) {
      const nm = String(r?.name ?? '');
      if (VENDOR_TRASH_NAMES.has(nm)) {
        vendorTrashW += (Number(r.valueW) || 0) * (Number(r.count) || 0);
      }
    }

    const [meta] = await pool.query(
      `SELECT point_card_points AS pointCardPoints, point_card_saved_at AS pointCardSavedAt, online_roles AS onlineRoles,
              elapsed_sec AS elapsedSec, cash_game_gold_w AS cashGameGoldW, team_principals_w AS teamPrincipalsW,
              team_cash_game_gold_w AS teamCashGameGoldWRaw, saved_at AS savedAt,
              ledger_base_elapsed_sec AS ledgerBaseElapsedSec, ledger_run_start_at_ms AS ledgerRunStartAtMs,
              ledger_point_card_json AS ledgerPointCardJsonRaw
       FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date = ?`,
      [uid, bizDate]
    );
    const m = meta[0];
    let teamPrincipalsW = [];
    try {
      teamPrincipalsW = m ? parseTeamPrincipalsColumn(m.teamPrincipalsW) : [];
    } catch {
      teamPrincipalsW = [];
    }
    const cashGameGoldW = m && m.cashGameGoldW != null ? Number(m.cashGameGoldW) : 0;
    const principalsSum = teamPrincipalsW.reduce((a, b) => a + b, 0);

    let tcParsed = [];
    let hasPerTeamCashColumn = false;
    try {
      const rawTc = m?.teamCashGameGoldWRaw;
      hasPerTeamCashColumn =
        rawTc != null &&
        rawTc !== '' &&
        !(typeof rawTc === 'string' && String(rawTc).trim() === 'null');
      if (hasPerTeamCashColumn) {
        tcParsed = parseTeamPrincipalsColumn(m.teamCashGameGoldWRaw);
        if (!Array.isArray(tcParsed) || tcParsed.length === 0) {
          hasPerTeamCashColumn = false;
          tcParsed = [];
        }
      }
    } catch {
      hasPerTeamCashColumn = false;
      tcParsed = [];
    }

    const slotsFromRoles = teamSlotsFromPresetAndCount(null, m ? Number(m.onlineRoles) : 1);
    /** 与记账台两队一致：不能仅靠 online_roles，否则存了 10 开但 roles 为 5 时会只算一队，总览净额成 0 */
    const teamSlotsMeta = Math.min(
      4,
      Math.max(slotsFromRoles, teamPrincipalsW.length, tcParsed.length, 1),
    );

    const principalsPad = [];
    for (let i = 0; i < teamSlotsMeta; i++) {
      principalsPad.push(Number.isFinite(Number(teamPrincipalsW[i])) ? Number(teamPrincipalsW[i]) : 0);
    }

    let teamCashGameGoldW = null;
    if (hasPerTeamCashColumn) {
      teamCashGameGoldW = [];
      for (let i = 0; i < teamSlotsMeta; i++) {
        const x = Number(tcParsed[i]);
        teamCashGameGoldW.push(Number.isFinite(x) && x >= 0 ? x : 0);
      }
    }

    const netCashGameGoldW =
      hasPerTeamCashColumn && teamCashGameGoldW && teamCashGameGoldW.length > 0
        ? netCashFromTeamRows(teamCashGameGoldW, principalsPad, teamSlotsMeta)
        : cashGameGoldW > 0
          ? cashGameGoldW - principalsSum
          : 0;
    const ledgerPointCard = m ? parseLedgerPointCardFromRow(m.ledgerPointCardJsonRaw) : null;
    res.json({
      bizDate,
      lines: rows.map((r) => ({
        name: r.name,
        valueW: Number(r.valueW),
        count: Number(r.count),
      })),
      pointCardPoints: m ? Number(m.pointCardPoints) : 0,
      pointCardSavedAt: m?.pointCardSavedAt ? new Date(m.pointCardSavedAt).toISOString() : null,
      onlineRoles: m ? Number(m.onlineRoles) : 0,
      cashGameGoldW,
      vendorTrashW,
      teamPrincipalsW,
      ...(teamCashGameGoldW ? { teamCashGameGoldW } : {}),
      netCashGameGoldW,
      savedAt: m?.savedAt ?? null,
      elapsedSec: mechLedgerDisplayElapsedSecFromMetaRow(m),
      ledgerBaseElapsedSec:
        m && m.ledgerBaseElapsedSec != null && Number.isFinite(Number(m.ledgerBaseElapsedSec))
          ? Number(m.ledgerBaseElapsedSec)
          : null,
      ledgerRunStartAtMs:
        m && m.ledgerRunStartAtMs != null && Number.isFinite(Number(m.ledgerRunStartAtMs))
          ? Number(m.ledgerRunStartAtMs)
          : null,
      ...(ledgerPointCard ? { ledgerPointCard } : {}),
    });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少记账台同步表。请在 server 目录执行：npm run db:migrate-v6',
      });
    }
    const msg = String(e?.sqlMessage || e?.message || '');
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('elapsed_sec')) {
      return res.status(503).json({
        error: '数据库缺少在线时长字段。请在 server 目录执行：node scripts/migrate-v43.js',
      });
    }
    if (
      e?.code === 'ER_BAD_FIELD_ERROR' &&
      (msg.includes('ledger_base_elapsed') || msg.includes('ledger_run_start') || msg.includes('ledger_point_card'))
    ) {
      return res.status(503).json({
        error: '数据库缺少记账台计时字段。请在 server 目录执行：node scripts/migrate-v44.js',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('cash_game_gold_w')) {
      return res.status(503).json({
        error: '数据库缺少现金梦幻币字段。请在 server 目录执行：npm run db:migrate-v13',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('team_principa')) {
      return res.status(503).json({
        error: '数据库缺少队伍本金字段。请在 server 目录执行：npm run db:migrate-v23',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('team_cash_game')) {
      return res.status(503).json({
        error: '数据库缺少各队现金字段。请在 server 目录执行：npm run db:migrate-v26',
      });
    }
    throw e;
  }
});

/** 有数据的日期列表（最近 limit 条） */
ledgerRouter.get('/mech-ledger/day-dates', async (req, res) => {
  const uid = req.user.id;
  const limit = Math.min(200, Math.max(1, Math.floor(Number(req.query?.limit) || 90)));
  try {
    const [rows] = await pool.query(
      `SELECT d FROM (
         SELECT DATE_FORMAT(biz_date, '%Y-%m-%d') AS d FROM mech_catalog_line_agg WHERE user_id = ?
         UNION
         SELECT DATE_FORMAT(biz_date, '%Y-%m-%d') AS d FROM mech_ledger_day_meta WHERE user_id = ?
       ) u
       ORDER BY d DESC LIMIT ?`,
      [uid, uid, limit]
    );
    res.json({ dates: rows.map((r) => r.d) });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少记账台同步表。请在 server 目录执行：npm run db:migrate-v6',
      });
    }
    throw e;
  }
});

ledgerRouter.post('/item-gains', async (req, res) => {
  const itemId = Number(req.body?.itemId);
  const quantity = Math.max(1, Number(req.body?.quantity || 1));
  const bizDate = String(req.body?.bizDate || todayStr());
  if (!itemId) return res.status(400).json({ error: '缺少 itemId' });
  const [r] = await pool.query(
    'INSERT INTO item_gains (user_id, biz_date, item_id, quantity) VALUES (?,?,?,?)',
    [req.user.id, bizDate, itemId, quantity]
  );
  res.json({ id: r.insertId, itemId, quantity, bizDate });
});

ledgerRouter.post('/cash', async (req, res) => {
  const amount = Number(req.body?.amount);
  const note = String(req.body?.note || '').slice(0, 255);
  const bizDate = String(req.body?.bizDate || todayStr());
  if (Number.isNaN(amount)) return res.status(400).json({ error: '金额无效' });
  const [r] = await pool.query(
    'INSERT INTO cash_entries (user_id, biz_date, amount, note) VALUES (?,?,?,?)',
    [req.user.id, bizDate, amount, note]
  );
  res.json({ id: r.insertId, amount, note, bizDate });
});

ledgerRouter.post('/points', async (req, res) => {
  const points = Math.max(0, Number(req.body?.points));
  const note = String(req.body?.note || '').slice(0, 255);
  const bizDate = String(req.body?.bizDate || todayStr());
  if (Number.isNaN(points)) return res.status(400).json({ error: '点数无效' });
  const [r] = await pool.query(
    'INSERT INTO point_card_entries (user_id, biz_date, points, note) VALUES (?,?,?,?)',
    [req.user.id, bizDate, points, note]
  );
  res.json({ id: r.insertId, points, note, bizDate });
});

/** 消耗页维护的角色名单（名称/等级/门派固定，每日记账时只填金额与游戏币） */
ledgerRouter.get('/consumption-characters', async (req, res) => {
  const uid = req.user.id;
  try {
    const [rows] = await pool.query(
      `SELECT id, character_name AS characterName, level_label AS levelLabel, sect,
              sort_order AS sortOrder, created_at AS createdAt
       FROM consumption_characters
       WHERE user_id = ?
       ORDER BY sort_order ASC, id ASC`,
      [uid]
    );
    res.json({ items: rows });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 consumption_characters 表。请在 server 目录执行：npm run db:migrate-v10',
      });
    }
    throw e;
  }
});

ledgerRouter.post('/consumption-characters', async (req, res) => {
  const uid = req.user.id;
  const characterName = String(req.body?.characterName ?? '').trim().slice(0, 64);
  const levelLabel = String(req.body?.levelLabel ?? '').trim().slice(0, 32);
  const sect = String(req.body?.sect ?? '').trim().slice(0, 32);
  const sortOrder = Math.floor(Number(req.body?.sortOrder));
  if (!characterName) return res.status(400).json({ error: '请填写角色名称' });
  try {
    let so;
    if (Number.isFinite(sortOrder)) {
      so = sortOrder;
    } else {
      const [[mx]] = await pool.query(
        'SELECT COALESCE(MAX(sort_order),0) AS m FROM consumption_characters WHERE user_id = ?',
        [uid]
      );
      so = Number(mx?.m ?? 0) + 1;
    }
    const [r] = await pool.query(
      `INSERT INTO consumption_characters (user_id, character_name, level_label, sect, sort_order)
       VALUES (?,?,?,?,?)`,
      [uid, characterName, levelLabel, sect, so]
    );
    res.json({
      id: r.insertId,
      characterName,
      levelLabel,
      sect,
      sortOrder: so,
    });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 consumption_characters 表。请在 server 目录执行：npm run db:migrate-v10',
      });
    }
    if (e?.code === 'ER_DUP_ENTRY') {
      return res.status(409).json({ error: '已存在同名角色，请改名或编辑原记录' });
    }
    throw e;
  }
});

ledgerRouter.patch('/consumption-characters/:id', async (req, res) => {
  const uid = req.user.id;
  const id = Math.floor(Number(req.params.id));
  if (!Number.isFinite(id) || id < 1) return res.status(400).json({ error: '无效 id' });
  const characterName = req.body?.characterName != null ? String(req.body.characterName).trim().slice(0, 64) : null;
  const levelLabel = req.body?.levelLabel != null ? String(req.body.levelLabel).trim().slice(0, 32) : null;
  const sect = req.body?.sect != null ? String(req.body.sect).trim().slice(0, 32) : null;
  const sortOrder = req.body?.sortOrder != null ? Math.floor(Number(req.body.sortOrder)) : null;
  const sets = [];
  const vals = [];
  if (characterName !== null) {
    if (!characterName) return res.status(400).json({ error: '角色名称不能为空' });
    sets.push('character_name = ?');
    vals.push(characterName);
  }
  if (levelLabel !== null) {
    sets.push('level_label = ?');
    vals.push(levelLabel);
  }
  if (sect !== null) {
    sets.push('sect = ?');
    vals.push(sect);
  }
  if (sortOrder !== null) {
    if (!Number.isFinite(sortOrder)) return res.status(400).json({ error: '排序无效' });
    sets.push('sort_order = ?');
    vals.push(sortOrder);
  }
  if (!sets.length) return res.status(400).json({ error: '无更新字段' });
  vals.push(id, uid);
  try {
    const [r] = await pool.query(
      `UPDATE consumption_characters SET ${sets.join(', ')} WHERE id = ? AND user_id = ?`,
      vals
    );
    if (!r.affectedRows) return res.status(404).json({ error: '未找到角色' });
    res.json({ ok: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 consumption_characters 表。请在 server 目录执行：npm run db:migrate-v10',
      });
    }
    if (e?.code === 'ER_DUP_ENTRY') {
      return res.status(409).json({ error: '已存在同名角色' });
    }
    throw e;
  }
});

ledgerRouter.delete('/consumption-characters/:id', async (req, res) => {
  const uid = req.user.id;
  const id = Math.floor(Number(req.params.id));
  if (!Number.isFinite(id) || id < 1) return res.status(400).json({ error: '无效 id' });
  try {
    const [r] = await pool.query('DELETE FROM consumption_characters WHERE id = ? AND user_id = ?', [id, uid]);
    if (!r.affectedRows) return res.status(404).json({ error: '未找到角色' });
    res.json({ ok: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 consumption_characters 表。请在 server 目录执行：npm run db:migrate-v10',
      });
    }
    throw e;
  }
});

/** 点卡充值/购买（人民币）+ 角色信息；可选从维护名单选角，并记录游戏币消耗（万） */
ledgerRouter.post('/consumption-entries', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  const characterIdRaw = req.body?.characterId;
  const characterId =
    characterIdRaw != null && characterIdRaw !== ''
      ? Math.floor(Number(characterIdRaw))
      : null;
  let characterName = String(req.body?.characterName ?? '').trim().slice(0, 64);
  let levelLabel = String(req.body?.levelLabel ?? '').trim().slice(0, 32);
  let sect = String(req.body?.sect ?? '').trim().slice(0, 32);
  const rmbAmount = Number(req.body?.rmbAmount);
  const gameCoinW = Number(req.body?.gameCoinW ?? req.body?.game_coin_w);
  const note = String(req.body?.note ?? '').trim().slice(0, 255);
  const coinW = Number.isFinite(gameCoinW) && gameCoinW >= 0 ? gameCoinW : NaN;
  const rmb = Number.isFinite(rmbAmount) && rmbAmount >= 0 ? rmbAmount : NaN;

  let cid = null;
  if (characterId != null && Number.isFinite(characterId) && characterId >= 1) {
    try {
      const [crow] = await pool.query(
        'SELECT id, character_name, level_label, sect FROM consumption_characters WHERE id = ? AND user_id = ? LIMIT 1',
        [characterId, uid]
      );
      if (!crow.length) return res.status(400).json({ error: '角色不在维护名单中' });
      cid = crow[0].id;
      characterName = String(crow[0].character_name || '').slice(0, 64);
      levelLabel = String(crow[0].level_label || '').slice(0, 32);
      sect = String(crow[0].sect || '').slice(0, 32);
    } catch (e) {
      if (e?.code === 'ER_NO_SUCH_TABLE') {
        return res.status(503).json({
          error: '数据库缺少 consumption_characters 表。请在 server 目录执行：npm run db:migrate-v10',
        });
      }
      throw e;
    }
  }

  if (!characterName) return res.status(400).json({ error: '请选择维护名单中的角色，或填写角色名称' });
  if (Number.isNaN(rmb) || Number.isNaN(coinW)) {
    return res.status(400).json({ error: '金额或游戏币（万）格式无效' });
  }
  if (!(rmb > 0 || coinW > 0)) {
    return res.status(400).json({ error: '人民币与游戏币至少填一项且须大于 0' });
  }

  try {
    const [r] = await pool.query(
      `INSERT INTO consumption_entries
       (user_id, character_id, biz_date, character_name, level_label, sect, rmb_amount, game_coin_w, note)
       VALUES (?,?,?,?,?,?,?,?,?)`,
      [uid, cid, bizDate, characterName, levelLabel, sect, rmb, coinW, note]
    );
    res.json({
      id: r.insertId,
      bizDate,
      characterId: cid,
      characterName,
      levelLabel,
      sect,
      rmbAmount: rmb,
      gameCoinW: coinW,
      note,
    });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 consumption_entries 表。请在 server 目录执行：npm run db:migrate-v7',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && String(e.sqlMessage || '').includes('game_coin_w')) {
      return res.status(503).json({
        error: '数据库缺少 game_coin_w 等字段。请在 server 目录执行：npm run db:migrate-v10',
      });
    }
    throw e;
  }
});

ledgerRouter.get('/consumption-entries', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  const limit = Math.min(200, Math.max(1, Math.floor(Number(req.query?.limit) || 40)));
  try {
    const [rows] = await pool.query(
      `SELECT id, character_id AS characterId, biz_date AS bizDate, character_name AS characterName,
              level_label AS levelLabel, sect, rmb_amount AS rmbAmount, game_coin_w AS gameCoinW,
              note, created_at AS createdAt
       FROM consumption_entries
       WHERE user_id = ? AND biz_date = ?
       ORDER BY id DESC
       LIMIT ?`,
      [uid, bizDate, limit]
    );
    res.json({ items: rows });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 consumption_entries 表。请在 server 目录执行：npm run db:migrate-v7',
      });
    }
    if (e?.code === 'ER_BAD_FIELD_ERROR' && String(e.sqlMessage || '').includes('game_coin_w')) {
      return res.status(503).json({
        error: '数据库缺少 game_coin_w 等字段。请在 server 目录执行：npm run db:migrate-v10',
      });
    }
    throw e;
  }
});

/** 按业务日 + 维护角色：当日一行（consumption_day_totals），物品消耗存 JSON 列 */
ledgerRouter.get('/consumption-day-board', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  try {
    const [chars] = await pool.query(
      `SELECT id, character_name AS characterName, level_label AS levelLabel, sect
       FROM consumption_characters WHERE user_id = ? ORDER BY sort_order ASC, id ASC`,
      [uid]
    );
    const [totals] = await pool.query(
      `SELECT character_id AS characterId, rmb_amount AS rmbAmount, dream_coin_w AS dreamCoinW, note,
              catalog_lines_json AS catalogLinesJson
       FROM consumption_day_totals WHERE user_id = ? AND biz_date = ?`,
      [uid, bizDate]
    );
    const totalsByChar = new Map(totals.map((t) => [Number(t.characterId), t]));
    const rows = chars.map((c) => {
      const t = totalsByChar.get(Number(c.id));
      return {
        characterId: c.id,
        characterName: c.characterName,
        levelLabel: c.levelLabel,
        sect: c.sect,
        rmbAmount: t ? Number(t.rmbAmount) : 0,
        dreamCoinW: t ? Number(t.dreamCoinW) : 0,
        note: t?.note ?? '',
        catalogLines: t ? normalizeCatalogLinesFromDb(t.catalogLinesJson) : [],
      };
    });
    res.json({ bizDate, rows });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少当日消耗表。请在 server 目录执行：npm run db:migrate-v11',
      });
    }
    const msg = String(e?.sqlMessage || e?.message || '');
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('catalog_lines_json')) {
      return res.status(503).json({
        error: '数据库缺少 catalog_lines_json 字段。请在 server 目录执行：npm run db:migrate-v12',
      });
    }
    throw e;
  }
});

ledgerRouter.put('/consumption-day-board/row', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req.body, req.query);
  const characterId = Math.floor(Number(req.body?.characterId));
  if (!Number.isFinite(characterId) || characterId < 1) {
    return res.status(400).json({ error: '无效角色' });
  }
  const rmbAmount = Number(req.body?.rmbAmount);
  const dreamCoinW = Number(req.body?.dreamCoinW ?? req.body?.dream_coin_w);
  const note = String(req.body?.note ?? '').trim().slice(0, 255);
  const rmb = Number.isFinite(rmbAmount) && rmbAmount >= 0 ? Math.round(rmbAmount * 100) / 100 : NaN;
  const dream = Number.isFinite(dreamCoinW) && dreamCoinW >= 0 ? dreamCoinW : NaN;
  if (Number.isNaN(rmb) || Number.isNaN(dream)) {
    return res.status(400).json({ error: '金额或梦幻币无效' });
  }
  const rawLines = Array.isArray(req.body?.catalogLines) ? req.body.catalogLines : [];
  const catalogLines = [];
  for (const x of rawLines) {
    const cid = Math.floor(Number(x?.catalogItemId ?? x?.catalog_item_id));
    const qty = Math.floor(Number(x?.quantity));
    if (!Number.isFinite(cid) || cid < 1) continue;
    if (!Number.isFinite(qty) || qty < 1) continue;
    catalogLines.push({ catalogItemId: cid, quantity: qty });
  }
  const hasItems = catalogLines.length > 0;
  const hasMoney = rmb > 0 || dream > 0;
  const hasNote = note.length > 0;
  const empty = !hasMoney && !hasNote && !hasItems;

  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    const [ch] = await conn.query('SELECT id FROM consumption_characters WHERE id = ? AND user_id = ? LIMIT 1', [
      characterId,
      uid,
    ]);
    if (!ch.length) {
      await conn.rollback();
      return res.status(400).json({ error: '角色不在维护名单中' });
    }

    if (empty) {
      await conn.query(
        'DELETE FROM consumption_day_totals WHERE user_id = ? AND biz_date = ? AND character_id = ?',
        [uid, bizDate, characterId]
      );
    } else {
      const storedLines = [];
      for (const line of catalogLines) {
        const [it] = await conn.query('SELECT id, name FROM catalog_items WHERE id = ? AND user_id = ? LIMIT 1', [
          line.catalogItemId,
          uid,
        ]);
        if (!it.length) {
          await conn.rollback();
          return res.status(400).json({ error: '物品不在物品库中' });
        }
        storedLines.push({
          catalogItemId: line.catalogItemId,
          quantity: line.quantity,
          name: String(it[0].name || ''),
        });
      }
      storedLines.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
      const catalogJson = JSON.stringify(storedLines);
      await conn.query(
        `INSERT INTO consumption_day_totals
         (user_id, biz_date, character_id, rmb_amount, dream_coin_w, note, catalog_lines_json)
         VALUES (?,?,?,?,?,?,?)
         ON DUPLICATE KEY UPDATE rmb_amount = VALUES(rmb_amount), dream_coin_w = VALUES(dream_coin_w),
           note = VALUES(note), catalog_lines_json = VALUES(catalog_lines_json), updated_at = CURRENT_TIMESTAMP`,
        [uid, bizDate, characterId, rmb, dream, note, catalogJson]
      );
    }
    await conn.commit();
    res.json({ ok: true, bizDate, characterId });
  } catch (e) {
    try {
      await conn.rollback();
    } catch (_) {
      /* ignore */
    }
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少当日消耗表。请在 server 目录执行：npm run db:migrate-v11',
      });
    }
    const msg = String(e?.sqlMessage || e?.message || '');
    if (e?.code === 'ER_BAD_FIELD_ERROR' && msg.includes('catalog_lines_json')) {
      return res.status(503).json({
        error: '数据库缺少 catalog_lines_json 字段。请在 server 目录执行：npm run db:migrate-v12',
      });
    }
    throw e;
  } finally {
    conn.release();
  }
});

/** 是否启用服务端语音转写（OpenAI Whisper 兼容接口，供 Chrome 等无法使用浏览器在线识别时） */
ledgerRouter.get('/mech-ledger/speech-transcribe/config', async (_req, res) => {
  const key = process.env.SPEECH_OPENAI_API_KEY || process.env.OPENAI_API_KEY;
  res.json({ enabled: Boolean(String(key || '').trim()) });
});

ledgerRouter.post('/mech-ledger/speech-transcribe', speechUpload.single('audio'), async (req, res) => {
  const key = String(process.env.SPEECH_OPENAI_API_KEY || process.env.OPENAI_API_KEY || '').trim();
  if (!key) {
    return res.status(503).json({
      error:
        '未配置服务端语音识别：在 server/.env 设置 SPEECH_OPENAI_API_KEY 或 OPENAI_API_KEY（Whisper 兼容 API）',
    });
  }
  const buf = req.file?.buffer;
  if (!buf?.length) {
    return res.status(400).json({ error: '缺少录音文件（字段名 audio）' });
  }
  const mime = req.file.mimetype || 'audio/webm';
  const base = String(process.env.SPEECH_OPENAI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
  const model = String(process.env.SPEECH_OPENAI_MODEL || 'whisper-1').trim() || 'whisper-1';
  const lang = String(process.env.SPEECH_TRANSCRIBE_LANG || 'zh').trim();

  try {
    const form = new FormData();
    form.append('model', model);
    const u8 = new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
    form.append('file', new Blob([u8], { type: mime }), 'recording.webm');
    if (lang && lang !== 'auto') {
      form.append('language', lang);
    }

    const url = `${base}/audio/transcriptions`;
    const r = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}` },
      body: form,
    });
    const raw = await r.text();
    let data;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = { raw };
    }
    if (!r.ok) {
      const msg = data?.error?.message || data?.message || String(raw || '').slice(0, 240) || r.statusText;
      console.error('[speech-transcribe]', r.status, msg);
      return res.status(502).json({ error: `转写服务返回错误：${msg}` });
    }
    const text = String(data?.text ?? '').trim();
    res.json({ text });
  } catch (e) {
    console.error('[speech-transcribe]', e);
    return res.status(502).json({ error: e?.message || '语音识别请求失败（请检查服务器网络能否访问转写 API）' });
  }
});
