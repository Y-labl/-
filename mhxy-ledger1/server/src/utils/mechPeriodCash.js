/**
 * 按记账台 + 消耗页：区间内「现金总额 / 现金净额（元）」与总览当日卡片一致。
 * 金价取 mech_ledger_user_prefs.rmb_yuan ÷ 3000 万 → 每 w 合元。
 */

const MECH_LEDGER_GAME_WAN_ANCHOR = 3000;

const MECH_ONLINE_PRESETS = [5, 10, 15, 20];

// 这些物品通常直接卖商人计入现金，净现金折算时应从物品收益中扣除避免重复计入。
const VENDOR_TRASH_NAMES = ['乐器', '花', '玫瑰花', '图册'];

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

/** 与 ledger GET /mech-ledger/daily 中 netCashGameGoldW 一致 */
function netGoldWanFromMeta(m) {
  if (!m) return 0;
  let teamPrincipalsW = [];
  try {
    teamPrincipalsW = parseTeamPrincipalsColumn(m.teamPrincipalsW);
  } catch {
    teamPrincipalsW = [];
  }
  const cashGameGoldW = m.cashGameGoldW != null ? Number(m.cashGameGoldW) : 0;
  const principalsSum = teamPrincipalsW.reduce((a, b) => a + b, 0);

  let tcParsed = [];
  let hasPerTeamCashColumn = false;
  try {
    const rawTc = m.teamCashGameGoldWRaw;
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

  const slotsFromRoles = teamSlotsFromPresetAndCount(null, m.onlineRoles != null ? Number(m.onlineRoles) : 1);
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

  if (hasPerTeamCashColumn && teamCashGameGoldW && teamCashGameGoldW.length > 0) {
    return netCashFromTeamRows(teamCashGameGoldW, principalsPad, teamSlotsMeta);
  }
  const g = Number.isFinite(cashGameGoldW) ? cashGameGoldW : 0;
  if (g <= 0) return 0;
  return g - principalsSum;
}

function roundRmbYuan2(n) {
  const x = Number(n);
  if (!Number.isFinite(x) || x < 0) return 0;
  return Math.round(x * 100) / 100;
}

/**
 * @returns {{ ok: true, netCashYuan: number, totalCashYuan: number, consumptionRmb: number } | { ok: false, netCashYuan: null, totalCashYuan: null, consumptionRmb: null }}
 */
export async function computeMechNetCashYuanForPeriod(pool, uid, dateStart, dateEnd) {
  let yuanPerWanW = 30 / MECH_LEDGER_GAME_WAN_ANCHOR;
  try {
    const [[r]] = await pool.query(
      'SELECT rmb_yuan AS y FROM mech_ledger_user_prefs WHERE user_id = ? LIMIT 1',
      [uid],
    );
    if (r && Number.isFinite(Number(r.y))) {
      yuanPerWanW = roundRmbYuan2(Number(r.y)) / MECH_LEDGER_GAME_WAN_ANCHOR;
    }
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
  }

  let itemW = 0;
  try {
    const [[r]] = await pool.query(
      `SELECT
         COALESCE(SUM(unit_price_w * quantity), 0) AS w,
         COALESCE(SUM(CASE WHEN item_name IN (?) THEN unit_price_w * quantity ELSE 0 END), 0) AS trashW
       FROM mech_catalog_line_agg
       WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?`,
      [VENDOR_TRASH_NAMES, uid, dateStart, dateEnd],
    );
    const totalW = Number(r?.w ?? 0);
    const trashW = Number(r?.trashW ?? 0);
    itemW = Math.max(0, totalW - trashW);
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
    return { ok: false, netCashYuan: null, totalCashYuan: null, consumptionRmb: null };
  }

  let metas = [];
  try {
    const [rows] = await pool.query(
      `SELECT cash_game_gold_w AS cashGameGoldW, team_principals_w AS teamPrincipalsW,
              team_cash_game_gold_w AS teamCashGameGoldWRaw, online_roles AS onlineRoles
       FROM mech_ledger_day_meta WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?`,
      [uid, dateStart, dateEnd],
    );
    metas = rows;
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
    return { ok: false, netCashYuan: null, totalCashYuan: null, consumptionRmb: null };
  }

  let goldNetWan = 0;
  for (const m of metas) {
    goldNetWan += netGoldWanFromMeta(m);
  }

  const totalCashYuan = itemW * yuanPerWanW + goldNetWan * yuanPerWanW;

  let consumptionRmb = 0;
  try {
    const [[r]] = await pool.query(
      `SELECT COALESCE(SUM(rmb_amount), 0) AS s FROM consumption_day_totals
       WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?`,
      [uid, dateStart, dateEnd],
    );
    consumptionRmb = Number(r?.s ?? 0);
  } catch (e) {
    if (e?.code !== 'ER_NO_SUCH_TABLE') throw e;
  }

  const netCashYuan = totalCashYuan - consumptionRmb;
  return { ok: true, netCashYuan, totalCashYuan, consumptionRmb };
}

/** 某月首尾日期 YYYY-MM-DD（本地日历月） */
export function monthDateRange(year, month) {
  const pad = (n) => String(n).padStart(2, '0');
  const lastDay = new Date(year, month, 0).getDate();
  return {
    start: `${year}-${pad(month)}-01`,
    end: `${year}-${pad(month)}-${pad(lastDay)}`,
  };
}
