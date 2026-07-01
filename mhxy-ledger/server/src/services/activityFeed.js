/**
 * 五开必刷 / 限时活动：远程 JSON + 仓库内 data 文件 + 极简回退。
 *
 * - ACTIVITIES_FEED_URL — GET JSON（自建图床/GitHub raw 等），格式见仓库 server/data/wukai-activities-feed.json
 * - WUKAI_FEED_URL — 未设上一项时，可再设此 URL 作为第二网络源（同样返回 { activities: [...] }）
 * - weekdays 为空 []：全周可刷、无时段（不参与限时置顶窗口）
 * - stars / 推荐星级：1–5；wukaiRank：五开榜基准顺序，数字越小越靠前
 */

import { readFileSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { pool } from '../db/pool.js';

const TTL_MS = Number(process.env.ACTIVITIES_FEED_TTL_MS || 5 * 60 * 1000);

const __dirname = dirname(fileURLToPath(import.meta.url));

let cache = {
  expiresAt: 0,
  payload: null,
  url: null,
  error: null,
  fetched: false,
};

function clampStars(n) {
  const x = Number(n);
  if (Number.isNaN(x)) return 3;
  return Math.min(5, Math.max(1, Math.round(x)));
}

function parseMonthAnchorWeekday(raw) {
  const v = raw?.monthAnchorWeekday ?? raw?.month_anchor_weekday;
  if (v === undefined || v === null || v === '') return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function normalizeActivity(raw) {
  if (!raw || typeof raw.key !== 'string' || !raw.name) return null;
  const stars = clampStars(raw.stars ?? raw.推荐星级 ?? 3);
  const wukaiRank = Number(raw.wukaiRank ?? raw.wukai_rank ?? raw.sortOrder ?? 50) || 50;
  const weekdays = Array.isArray(raw.weekdays)
    ? raw.weekdays.map(Number).filter((n) => n >= 0 && n <= 6)
    : [];

  const monthWeekRaw = raw.monthWeek ?? raw.month_week;
  const monthWeek =
    monthWeekRaw !== undefined && monthWeekRaw !== null && monthWeekRaw !== ''
      ? Number(monthWeekRaw)
      : null;
  const monthWeekNorm = Number.isFinite(monthWeek) ? monthWeek : null;
  const monthAnchorNorm = parseMonthAnchorWeekday(raw);

  const builtTimeWindows =
    Array.isArray(raw.windows) && raw.windows.length > 0
      ? raw.windows.map((w) => {
          const s = String(w.start || '00:00').slice(0, 5);
          const e = String(w.end || '23:59').slice(0, 5);
          return { schedule_start: `${s}:00`, schedule_end: `${e}:00` };
        })
      : null;

  if (!weekdays.length) {
    return {
      key: String(raw.key).replace(/[^\w\-:.]/g, '_').slice(0, 64),
      name: String(raw.name).slice(0, 128),
      description: String(raw.description || '').slice(0, 512),
      weekdays: [],
      schedule_weekdays: null,
      schedule_start: null,
      schedule_end: null,
      schedule_pin_early_minutes: 0,
      sortOrder: Number(raw.sortOrder ?? raw.sort_order ?? 50) || 50,
      stars,
      wukaiRank,
      monthWeek: monthWeekNorm,
      monthAnchorWeekday: monthAnchorNorm,
      ...(builtTimeWindows ? { timeWindows: builtTimeWindows } : {}),
    };
  }

  const start = builtTimeWindows
    ? builtTimeWindows[0].schedule_start.slice(0, 5)
    : String(raw.start || '00:00').slice(0, 5);
  const end = builtTimeWindows
    ? builtTimeWindows[builtTimeWindows.length - 1].schedule_end.slice(0, 5)
    : String(raw.end || '23:59').slice(0, 5);
  return {
    key: String(raw.key).replace(/[^\w\-:.]/g, '_').slice(0, 64),
    name: String(raw.name).slice(0, 128),
    description: String(raw.description || '').slice(0, 512),
    weekdays,
    schedule_weekdays: weekdays.join(','),
    schedule_start: `${start}:00`,
    schedule_end: `${end}:00`,
    schedule_pin_early_minutes: Number(raw.pinEarly ?? raw.pin_early ?? 30) || 30,
    sortOrder: Number(raw.sortOrder ?? raw.sort_order ?? 50) || 50,
    stars,
    wukaiRank,
    monthWeek: monthWeekNorm,
    monthAnchorWeekday: monthAnchorNorm,
    ...(builtTimeWindows ? { timeWindows: builtTimeWindows } : {}),
  };
}

function loadActivitiesFromDataFile() {
  const p = join(__dirname, '../../data/wukai-activities-feed.json');
  if (!existsSync(p)) return [];
  try {
    const data = JSON.parse(readFileSync(p, 'utf8'));
    const list = Array.isArray(data.activities) ? data.activities : [];
    return list.map(normalizeActivity).filter(Boolean);
  } catch {
    return [];
  }
}

/** 极简回退（数据文件丢失时） */
function getEmergencyBuiltinActivities() {
  return [
    normalizeActivity({
      key: 'maze-montothu',
      name: '活动：帮派迷宫',
      description: '周一、周三固定开放；周五仅无帮战时开放（应急内置；以游戏内为准）',
      weekdays: [1, 3, 5],
      start: '20:00',
      end: '22:00',
      pinEarly: 30,
      sortOrder: 10,
      stars: 4,
      wukaiRank: 10,
    }),
    normalizeActivity({
      key: 'xingchen-montothu',
      name: '活动：天降星辰',
      description: '周一至周四晚间（应急内置）',
      weekdays: [1, 2, 3, 4],
      start: '20:00',
      end: '22:00',
      pinEarly: 30,
      sortOrder: 11,
      stars: 4,
      wukaiRank: 11,
    }),
    normalizeActivity({
      key: 'huangong-feizei',
      name: '活动：皇宫飞贼',
      description: '周一至周五，中午 12:00 至下午 14:00（应急内置；请尽快跑 db:migrate-v16/v20 写库）。',
      weekdays: [1, 2, 3, 4, 5],
      start: '12:00',
      end: '14:00',
      pinEarly: 20,
      sortOrder: 5,
      stars: 5,
      wukaiRank: 5,
    }),
    normalizeActivity({
      key: 'cal-shuanglong-shenqi-daily',
      name: '活动：双龙之战·神器争夺战（每日）',
      description: '每晚 22:00–23:30（应急内置；请跑 db:migrate-v19/v20）。',
      weekdays: [0, 1, 2, 3, 4, 5, 6],
      start: '22:00',
      end: '23:30',
      pinEarly: 25,
      sortOrder: 21,
      stars: 5,
      wukaiRank: 21,
    }),
  ].filter(Boolean);
}

/** DB 行 calendar_activities → 与 normalizeActivity 相同结构 */
function timeToHhMmSql(t) {
  if (t == null) return '00:00';
  if (typeof t === 'object' && t !== null && typeof t.toSQL === 'function') {
    const s = t.toSQL();
    if (typeof s === 'string') return s.slice(0, 5);
  }
  const s = String(t);
  if (/^\d{1,2}:\d{2}/.test(s)) return s.slice(0, 5);
  if (s.includes('T') && /\d{2}:\d{2}/.test(s)) {
    const m = s.match(/(\d{2}):(\d{2})/);
    if (m) return `${m[1]}:${m[2]}`;
  }
  return s.slice(0, 5);
}

function dbCalendarRowToActivity(r) {
  const weekdays = String(r.scheduleWeekdays || '')
    .split(',')
    .map((x) => Number(x.trim()))
    .filter((n) => !Number.isNaN(n) && n >= 0 && n <= 6);
  if (!weekdays.length) return null;
  const start = timeToHhMmSql(r.scheduleStart);
  const end = timeToHhMmSql(r.scheduleEnd);
  const pin = Number(r.pinEarly) || 30;
  const key = String(r.actKey || '').replace(/[^\w\-:.]/g, '_').slice(0, 64);
  if (!key) return null;
  const mw = r.monthWeek != null ? Number(r.monthWeek) : null;
  const monthWeek = Number.isFinite(mw) ? mw : null;
  const ma = r.monthAnchorWeekday != null ? Number(r.monthAnchorWeekday) : null;
  const monthAnchorWeekday = Number.isFinite(ma) ? ma : null;

  const s2raw = r.scheduleStart2 ?? r.schedule_start_2;
  const e2raw = r.scheduleEnd2 ?? r.schedule_end_2;
  const start2 =
    s2raw != null && s2raw !== '' ? timeToHhMmSql(s2raw) : null;
  const end2 =
    e2raw != null && e2raw !== '' ? timeToHhMmSql(e2raw) : null;
  const hasSecond =
    start2 != null &&
    end2 != null &&
    String(start2).length > 0 &&
    String(end2).length > 0;
  const timeWindows = hasSecond
    ? [
        { schedule_start: `${start}:00`, schedule_end: `${end}:00` },
        { schedule_start: `${start2}:00`, schedule_end: `${end2}:00` },
      ]
    : undefined;

  return {
    key,
    name: String(r.name).slice(0, 128),
    description: String(r.description || '').slice(0, 512),
    weekdays,
    schedule_weekdays: weekdays.join(','),
    schedule_start: `${start}:00`,
    schedule_end: hasSecond ? `${end2}:00` : `${end}:00`,
    schedule_pin_early_minutes: pin,
    sortOrder: Number(r.sortOrder) || 50,
    stars: clampStars(r.stars),
    wukaiRank: Number(r.wukaiRank) || 50,
    monthWeek,
    monthAnchorWeekday,
    ...(timeWindows ? { timeWindows } : {}),
  };
}

/** 含第二时段（英雄大会等） */
const CALENDAR_SELECT_WITH_SECOND = `SELECT act_key AS actKey, name, description, schedule_weekdays AS scheduleWeekdays,
       schedule_start AS scheduleStart, schedule_end AS scheduleEnd,
       schedule_start_2 AS scheduleStart2, schedule_end_2 AS scheduleEnd2,
       pin_early_minutes AS pinEarly, stars, wukai_rank AS wukaiRank, sort_order AS sortOrder,
       month_week AS monthWeek, month_anchor_weekday AS monthAnchorWeekday
FROM calendar_activities
WHERE is_active = 1
ORDER BY wukai_rank ASC, sort_order ASC, id ASC`;

const CALENDAR_SELECT_FULL = `SELECT act_key AS actKey, name, description, schedule_weekdays AS scheduleWeekdays,
       schedule_start AS scheduleStart, schedule_end AS scheduleEnd,
       pin_early_minutes AS pinEarly, stars, wukai_rank AS wukaiRank, sort_order AS sortOrder,
       month_week AS monthWeek, month_anchor_weekday AS monthAnchorWeekday
FROM calendar_activities
WHERE is_active = 1
ORDER BY wukai_rank ASC, sort_order ASC, id ASC`;

const CALENDAR_SELECT_LEGACY = `SELECT act_key AS actKey, name, description, schedule_weekdays AS scheduleWeekdays,
       schedule_start AS scheduleStart, schedule_end AS scheduleEnd,
       pin_early_minutes AS pinEarly, stars, wukai_rank AS wukaiRank, sort_order AS sortOrder,
       month_week AS monthWeek
FROM calendar_activities
WHERE is_active = 1
ORDER BY wukai_rank ASC, sort_order ASC, id ASC`;

export async function loadCalendarActivitiesFromDb() {
  const tries = [
    { sql: CALENDAR_SELECT_WITH_SECOND, legacyMonthAnchor: false },
    { sql: CALENDAR_SELECT_FULL, legacyMonthAnchor: false },
    { sql: CALENDAR_SELECT_LEGACY, legacyMonthAnchor: true },
  ];
  for (let i = 0; i < tries.length; i++) {
    const { sql, legacyMonthAnchor } = tries[i];
    try {
      const [rows] = await pool.query(sql);
      return rows
        .map((r) =>
          legacyMonthAnchor
            ? dbCalendarRowToActivity({ ...r, monthAnchorWeekday: null })
            : dbCalendarRowToActivity(r),
        )
        .filter(Boolean);
    } catch (e) {
      const code = e && typeof e === 'object' && 'code' in e ? String(e.code) : '';
      const isBadCol = code === 'ER_BAD_FIELD_ERROR';
      if (!isBadCol || i === tries.length - 1) return [];
    }
  }
  return [];
}

/** 同名 act_key 以 DB 为准（覆盖 JSON/远程） */
function mergeActivitiesDbOverBase(dbList, baseList) {
  const m = new Map();
  for (const a of baseList || []) {
    if (a?.key) m.set(a.key, a);
  }
  for (const a of dbList || []) {
    if (a?.key) m.set(a.key, a);
  }
  return Array.from(m.values());
}

export function getBuiltinActivities() {
  const fromFile = loadActivitiesFromDataFile();
  if (fromFile.length) return fromFile;
  return getEmergencyBuiltinActivities();
}

async function fetchRemote(url) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), Number(process.env.ACTIVITIES_FEED_TIMEOUT_MS || 12000));
  try {
    const res = await fetch(url, {
      signal: ac.signal,
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const list = Array.isArray(data.activities) ? data.activities : [];
    const activities = list.map(normalizeActivity).filter(Boolean);
    return { activities, rawUpdatedAt: data.updatedAt || data.updated_at || null };
  } finally {
    clearTimeout(t);
  }
}

function payloadFromActivities(activities, source, fetched, error, updatedAt) {
  return {
    activities,
    source,
    fetched,
    error,
    updatedAt: updatedAt || new Date().toISOString(),
  };
}

export async function getActivityFeed() {
  const primary = (process.env.ACTIVITIES_FEED_URL || '').trim();
  const secondary = (process.env.WUKAI_FEED_URL || '').trim();
  const cacheKey = primary || secondary || '__file__';
  const now = Date.now();
  if (cache.payload && now < cache.expiresAt && cache.url === cacheKey) {
    return cache.payload;
  }

  const dbList = await loadCalendarActivitiesFromDb();
  const baseFile = loadActivitiesFromDataFile();

  const finalize = (baseList, source, fetched, err, updatedAt) => {
    const merged = mergeActivitiesDbOverBase(dbList, baseList || []);
    const activities = merged.length ? merged : getEmergencyBuiltinActivities();
    const src = dbList.length > 0 ? `${source}+db` : source;
    const payload = payloadFromActivities(activities, src, fetched, err, updatedAt);
    cache = { expiresAt: now + TTL_MS, payload, url: cacheKey, error: err, fetched };
    return payload;
  };

  if (primary) {
    try {
      const remote = await fetchRemote(primary);
      const base = remote.activities.length ? remote.activities : baseFile;
      return finalize(
        base,
        remote.activities.length ? 'remote' : 'file_fallback_empty',
        true,
        null,
        remote.rawUpdatedAt || undefined
      );
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e);
      const base = baseFile.length ? baseFile : getEmergencyBuiltinActivities();
      return finalize(base, 'file_fallback_error', false, err);
    }
  }

  if (secondary) {
    try {
      const remote = await fetchRemote(secondary);
      const base = remote.activities.length ? remote.activities : baseFile;
      return finalize(
        base,
        remote.activities.length ? 'wukai_remote' : 'file_fallback_empty',
        true,
        null,
        remote.rawUpdatedAt || undefined
      );
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e);
      const base = baseFile.length ? baseFile : getEmergencyBuiltinActivities();
      return finalize(base, 'file_fallback_net_error', false, err);
    }
  }

  return finalize(baseFile, 'data_file', true, null);
}
