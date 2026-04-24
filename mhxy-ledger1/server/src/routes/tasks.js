import { Router } from 'express';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { todayStr, calendarDaysBetween, mondayOfWeek, addDaysStr } from '../utils/date.js';
import {
  evaluateSchedule,
  scheduleMatchesWeekday,
  timeToMinutes,
  evaluateTimedForRecommend,
  recommendDedupeKey,
  calendarActivityMatchesDay,
  isTimedCalendarRow,
  formatLabel,
  activityEarliestStartMinutes,
  activityLatestEndMinutes,
  nthWeekdayIndexInMonth,
} from '../utils/schedule.js';
import { getActivityFeed } from '../services/activityFeed.js';

export const tasksRouter = Router();
tasksRouter.use(authRequired);

tasksRouter.patch('/templates/:id', async (req, res) => {
  const id = Math.floor(Number(req.params.id));
  if (!Number.isFinite(id) || id < 1) return res.status(400).json({ error: '无效 id' });

  const b = req.body || {};
  const fields = [];
  const params = [];

  if (b.enabled !== undefined) {
    fields.push('enabled = ?');
    params.push(b.enabled ? 1 : 0);
  }
  if (b.manualSortOrder !== undefined) {
    const raw = b.manualSortOrder;
    const v = raw === null || raw === '' ? null : Math.floor(Number(raw));
    if (v === null) {
      fields.push('manual_sort_order = NULL');
    } else if (Number.isFinite(v)) {
      fields.push('manual_sort_order = ?');
      params.push(v);
    } else {
      return res.status(400).json({ error: 'manualSortOrder 无效' });
    }
  }

  if (!fields.length) return res.status(400).json({ error: '无更新字段' });

  const [r] = await pool.query(`UPDATE task_templates SET ${fields.join(', ')} WHERE id = ?`, [
    ...params,
    id,
  ]);
  if (!r || r.affectedRows === 0) return res.status(404).json({ error: '未找到' });

  const [[row]] = await pool.query(
    `SELECT id, name, description, frequency,
            sort_order AS sortOrder, enabled, manual_sort_order AS manualSortOrder,
            cooldown_days AS cooldownDays, schedule_weekdays, schedule_start, schedule_end, schedule_pin_early_minutes,
            cycle_anchor_at AS cycleAnchorAt
     FROM task_templates WHERE id = ?`,
    [id],
  );
  res.json(row);
});

tasksRouter.post('/templates/reorder', async (req, res) => {
  const idsRaw = req.body?.ids;
  if (!Array.isArray(idsRaw) || idsRaw.length === 0) {
    return res.status(400).json({ error: 'ids 不能为空' });
  }
  const ids = [];
  for (const x of idsRaw) {
    const n = Math.floor(Number(x));
    if (!Number.isFinite(n) || n < 1) continue;
    if (!ids.includes(n)) ids.push(n);
  }
  if (!ids.length) return res.status(400).json({ error: 'ids 无效' });

  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    for (let i = 0; i < ids.length; i++) {
      await conn.query('UPDATE task_templates SET manual_sort_order = ? WHERE id = ?', [i + 1, ids[i]]);
    }
    await conn.commit();
    res.json({ ok: true, count: ids.length });
  } catch (e) {
    try {
      await conn.rollback();
    } catch (_) {}
    throw e;
  } finally {
    conn.release();
  }
});

function nextFixedPeriodRefreshMs(nowMs, anchorAt, days) {
  if (!anchorAt) return null;
  const d = Math.max(1, Math.floor(Number(days) || 4));
  const periodMs = d * 24 * 60 * 60 * 1000;
  const anchorMs = new Date(anchorAt).getTime();
  if (Number.isNaN(anchorMs) || anchorMs <= 0) return null;
  if (nowMs < anchorMs) return anchorMs;
  const n = Math.floor((nowMs - anchorMs) / periodMs) + 1;
  return anchorMs + n * periodMs;
}

function templateStarsFromSort(sortOrder) {
  const o = Number(sortOrder) || 50;
  if (o <= 8) return 5;
  if (o <= 20) return 4;
  if (o <= 40) return 3;
  return 2;
}

/** 名称含「周末」的每日模板：仅周日(0)、周六(6)展示，避免「周末活动」等工作日误出 */
function skipWeekendNamedDailyOnWeekday(t, weekday) {
  if (String(t.frequency) !== 'daily') return false;
  if (!/周末/.test(String(t.name || ''))) return false;
  return weekday !== 0 && weekday !== 6;
}

/** 五开几乎不做的日常，仍可能在旧库留档：推荐/候选一律不出 */
function skipDiscouragedForWukai(t) {
  return /运镖/.test(String(t.name || ''));
}

/** 限时活动 feed 低于此星级不进「五开高收益」推荐（可调） */
const WUKAI_FEED_MIN_STARS = 4;

/** 五开较少刷的限时活动（仍展示）：排在「日常推荐」之后、已过期场次之前 */
const WUKAI_TAIL_KEYS = new Set(['huangong-feizei', 'miaoshou-renxin', 'tianxia-meishi']);

/** 五开不做的限时 feed：推荐榜与补录列表均不展示（含远程 feed 里同名活动） */
const WUKAI_EXCLUDE_LIVE_KEYS = new Set(['jianhui-tianxia', 'juesheng-zhaohuanshou']);

function skipWukaiExcludedLive(a) {
  if (!a) return false;
  if (a.key && WUKAI_EXCLUDE_LIVE_KEYS.has(String(a.key))) return true;
  const n = String(a.name || '');
  return /剑会天下/.test(n) || /决胜召唤兽/.test(n);
}

/**
 * migrate-v2 插入的 task_templates「活动：门派闯关」仅有周日、无「第几个周日」，
 * evaluateTimedForRecommend 在 monthWeek 为空时每个周日都会命中；月历/feed 已按第 1 个周日处理。
 */
function skipLegacyMenpaiTemplateWrongSundayOfMonth(t, bizDate, weekday) {
  if (weekday !== 0) return false;
  if (String(t.name || '') !== '活动：门派闯关') return false;
  const idx = nthWeekdayIndexInMonth(bizDate, 0);
  if (idx == null) return false;
  return idx !== 1;
}

/** 数字越小越靠前：① 进行中限时 → ② 即将开始限时 → ③ 全天/日常周常 → ④ 普通限时 → ⑤ 冷却中 → ⑥ 低优限时 → ⑦ 已过期 → ⑧ 已完成 */
function recommendSegment(e) {
  if (e.recordedDoneToday) return 7;
  if (e.schedulePassed) return 6;
  // 进行中：永远置顶（比“即将开始”更靠前）
  if (e.scheduleHot && !e.recordedDoneToday && !e.schedulePassed) return 0;
  // 即将开始：次级置顶
  if (e.schedulePinned && !e.recordedDoneToday && !e.schedulePassed) return 1;
  if (e.recommendKind === 'daily' || e.recommendKind === 'weekly') return 2;
  if (e.inCooldown) return 4;
  if (e.wukaiTail) return 5;
  return 3;
}

function lastMomentFromRow(row) {
  if (!row) return null;
  const a = row.ended_at ? new Date(row.ended_at).getTime() : 0;
  const b = row.created_at ? new Date(row.created_at).getTime() : 0;
  const t = Math.max(a, b);
  return t ? new Date(t) : null;
}

function weekdayFromBizDate(ymd) {
  const [y, m, d] = ymd.split('-').map(Number);
  return new Date(y, m - 1, d).getDay();
}

async function loadDoneKeys(uid, bizDate) {
  const [rows] = await pool.query(
    'SELECT dedupe_key AS k FROM task_done_entries WHERE user_id = ? AND biz_date = ?',
    [uid, bizDate]
  );
  return new Set(rows.map((r) => r.k));
}

async function loadLastByTaskId(uid) {
  const [rows] = await pool.query(
    `SELECT task_id AS taskId,
            MAX(GREATEST(COALESCE(ended_at, created_at), created_at)) AS lm
     FROM task_done_entries
     WHERE user_id = ? AND task_id IS NOT NULL
     GROUP BY task_id`,
    [uid]
  );
  const map = {};
  for (const r of rows) {
    map[r.taskId] = r.lm ? new Date(r.lm) : null;
  }
  return map;
}

function doneTodayDbIds(doneKeys) {
  const s = new Set();
  for (const k of doneKeys) {
    const m = /^db:(\d+)$/.exec(k);
    if (m) s.add(Number(m[1]));
  }
  return s;
}

function normalizeYmd(v) {
  if (v == null || v === '') return null;
  if (v instanceof Date) return todayStr(v);
  const str = String(v);
  return str.length >= 10 ? str.slice(0, 10) : str;
}

function monday00RangeByWall(d) {
  const x = new Date(d);
  if (Number.isNaN(x.getTime())) return null;
  const day = x.getDay(); // 0 Sun..6 Sat
  const diff = day === 0 ? -6 : 1 - day;
  x.setHours(0, 0, 0, 0);
  x.setDate(x.getDate() + diff);
  const start = x;
  const end = new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);
  return { start, end };
}

async function loadWeeklyTaskStats(uid, weekStartAt, weekEndAt) {
  const [rows] = await pool.query(
    `SELECT task_id AS taskId,
            COUNT(*) AS c,
            MAX(biz_date) AS lastBiz
     FROM task_done_entries
     WHERE user_id = ?
       AND task_id IS NOT NULL
       AND GREATEST(COALESCE(ended_at, created_at), created_at) >= ?
       AND GREATEST(COALESCE(ended_at, created_at), created_at) < ?
     GROUP BY task_id`,
    [uid, weekStartAt, weekEndAt]
  );
  const map = {};
  for (const r of rows) {
    map[Number(r.taskId)] = {
      count: Number(r.c),
      lastBiz: normalizeYmd(r.lastBiz),
    };
  }
  return map;
}

async function loadWeeklyGhostUsed(uid, weekStartAt, weekEndAt) {
  const [[row]] = await pool.query(
    `SELECT COALESCE(SUM(COALESCE(unit_count, 0)), 0) AS s
       FROM task_done_entries
      WHERE user_id = ? AND task_id = 2
        AND GREATEST(COALESCE(ended_at, created_at), created_at) >= ?
        AND GREATEST(COALESCE(ended_at, created_at), created_at) < ?`,
    [uid, weekStartAt, weekEndAt]
  );
  return Number(row?.s || 0);
}

function weeklyCapFromFrequency(freq) {
  if (freq === 'weekly_once') return 1;
  if (freq === 'weekly_twice') return 2;
  return 0;
}

/**
 * 周常副本推荐：周一～日为一个周期；未满次数始终出现；满次数则仅在「最后完成」业务日显示已完成，次日起不再出现。
 */
function buildWeeklyRecommendRow(t, bizDate, weekStats) {
  const cap = weeklyCapFromFrequency(t.frequency);
  if (!cap) return null;
  const st = weekStats[t.id] || { count: 0, lastBiz: null };
  const { count, lastBiz } = st;
  const remaining = cap - count;

  const base = {
    source: 'db',
    id: t.id,
    name: t.name,
    description: t.description,
    frequency: t.frequency,
    sortOrder: t.sortOrder,
    enabled: t.enabled === 1 || t.enabled === true,
    manualSortOrder: t.manualSortOrder ?? null,
    cooldownDays: t.cooldownDays,
    schedulePinned: false,
    scheduleLabel: null,
    hasSchedule: false,
    schedulePassed: false,
    stars: templateStarsFromSort(t.sortOrder),
    wukaiRank: Number(t.sortOrder) || 99,
    recommendKind: 'weekly',
    wukaiTail: false,
    _startM: null,
    _endM: null,
    weeklyCap: cap,
    weeklyRemaining: Math.max(0, remaining),
    capTimes: cap,
    remainingTimes: Math.max(0, remaining),
  };

  if (remaining > 0) {
    if (cap > 1) {
      base.scheduleLabel = `本周还可 ${remaining} 次`;
    }
    return base;
  }

  if (lastBiz && bizDate === lastBiz) {
    return {
      ...base,
      weeklyRemaining: 0,
      recordedDoneToday: true,
      scheduleLabel: '本周已完成',
    };
  }

  if (lastBiz && bizDate > lastBiz) {
    return null;
  }

  return null;
}

/** 剩余次数为 0 且本业务日未点「完成」：不显于推荐榜，仅在补录榜展示并标「等待更新」 */
function shouldMoveToBackfillForZeroRemain(e) {
  if (e.recordedDoneToday) return false;
  if (e.capTimes == null || e.remainingTimes == null) return false;
  return e.remainingTimes === 0 && e.capTimes > 0;
}

function compareWukaiEnrichedEntries(a, b, wallMinutes) {
  const sa = recommendSegment(a);
  const sb = recommendSegment(b);
  if (sa !== sb) return sa - sb;

  const mo = (x) => {
    const n = x && x.manualSortOrder != null ? Number(x.manualSortOrder) : NaN;
    return Number.isFinite(n) ? n : null;
  };
  const ao = mo(a);
  const bo = mo(b);

  if (sa === 2) {
    if (ao != null || bo != null) {
      if ((ao ?? 1e9) !== (bo ?? 1e9)) return (ao ?? 1e9) - (bo ?? 1e9);
    }
    if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
    return (a.id || 0) - (b.id || 0);
  }

  if (sa === 7) {
    if (ao != null || bo != null) {
      if ((ao ?? 1e9) !== (bo ?? 1e9)) return (ao ?? 1e9) - (bo ?? 1e9);
    }
    if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
    return (a.id || 0) - (b.id || 0);
  }

  const oa = a.scheduleHot ? 0 : 1;
  const ob = b.scheduleHot ? 0 : 1;
  if (oa !== ob) return oa - ob;
  const pa = a.schedulePinned ? 0 : 1;
  const pb = b.schedulePinned ? 0 : 1;
  if (pa !== pb) return pa - pb;
  const starsCmp = (b.stars ?? 3) - (a.stars ?? 3);
  if (starsCmp !== 0) return starsCmp;
  const wr = (a.wukaiRank ?? 99) - (b.wukaiRank ?? 99);
  if (wr !== 0) return wr;
  if (a._startM != null && b._startM != null && !a.schedulePinned && !b.schedulePinned) {
    const aBefore = wallMinutes < a._startM;
    const bBefore = wallMinutes < b._startM;
    if (aBefore && bBefore && a._startM !== b._startM) return a._startM - b._startM;
  }
  if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
  if (a.source !== b.source) return a.source === 'live' ? -1 : 1;
  return (a.id || 0) - (b.id || 0);
}

function durationSecondsBetween(startedAt, endedAt) {
  if (!startedAt || !endedAt) return null;
  const a = startedAt.getTime();
  const b = endedAt.getTime();
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return null;
  return Math.floor((b - a) / 1000);
}

/** 未传开始时：业务日 10:00（与前端默认一致）；若晚于结束则退回结束前 1 分钟 */
function defaultStartedAtForDone(bizDate, endedAt) {
  const ten = new Date(`${String(bizDate)}T10:00:00`);
  if (!endedAt || Number.isNaN(endedAt.getTime())) {
    return Number.isNaN(ten.getTime()) ? new Date() : ten;
  }
  if (Number.isNaN(ten.getTime())) {
    return new Date(endedAt.getTime() - 60_000);
  }
  if (ten.getTime() <= endedAt.getTime()) return ten;
  return new Date(endedAt.getTime() - 60_000);
}

async function insertDoneEntry(req, { bizDate, dedupeKey, taskId, title, startedAt, endedAt, source, unitCount }) {
  let s = startedAt;
  if (!s || Number.isNaN(s.getTime())) {
    s = defaultStartedAtForDone(bizDate, endedAt);
  }
  if (s && endedAt && s.getTime() > endedAt.getTime()) {
    s = new Date(endedAt.getTime() - 60_000);
  }
  const dur = durationSecondsBetween(s, endedAt);
  const [ins] = await pool.query(
    `INSERT INTO task_done_entries (user_id, biz_date, dedupe_key, task_id, title, started_at, ended_at, duration_seconds, unit_count, source)
     VALUES (?,?,?,?,?,?,?,?,?,?)`,
    [req.user.id, bizDate, dedupeKey, taskId, title, s, endedAt, dur, unitCount ?? null, source]
  );
  return { id: ins.insertId, startedAt: s, endedAt, durationSeconds: dur };
}

async function buildWukaiEnrichedList(req) {
  const bizDate = String(req.query.bizDate || todayStr());
  const uid = req.user.id;

  /** 日历日以 bizDate 为准（勿用「今天星期几」顶替其它业务日） */
  const weekday = weekdayFromBizDate(bizDate);
  /** 非当天：展示该 weekday 全部限时场次；当天：按当前时间隐藏已结束场次 */
  const dayPlan = bizDate !== todayStr();
  const wallRaw = req.query.wallMinutes;
  const wallMinutes = dayPlan
    ? 12 * 60
    : wallRaw !== undefined && wallRaw !== ''
      ? Number(wallRaw)
      : new Date().getHours() * 60 + new Date().getMinutes();

  const [feed, qt, doneKeys, lastByTask] = await Promise.all([
    getActivityFeed(),
    pool.query(
      `SELECT id, name, description, frequency,
              sort_order AS sortOrder, enabled, manual_sort_order AS manualSortOrder,
              cooldown_days AS cooldownDays,
              schedule_weekdays, schedule_start, schedule_end, schedule_pin_early_minutes,
              cycle_anchor_at AS cycleAnchorAt
       FROM task_templates
       WHERE enabled = 1
       ORDER BY COALESCE(manual_sort_order, sort_order), sort_order, id`
    ),
    loadDoneKeys(uid, bizDate),
    loadLastByTaskId(uid),
  ]);

  const tasks = qt[0];
  const doneToday = doneTodayDbIds(doneKeys);
  const weekRange = monday00RangeByWall(new Date());
  const weekStats = weekRange ? await loadWeeklyTaskStats(uid, weekRange.start, weekRange.end) : {};
  const ghostWeekUsed = weekRange ? await loadWeeklyGhostUsed(uid, weekRange.start, weekRange.end) : 0;
  const enriched = [];
  /** 日历限时名称去重：跳过无时段的「日常：xxx」模板，避免盖住带 12:00–14:00 等的活动日历行 */
  const feedTimedDedupe = new Set();
  for (const a of feed.activities) {
    if (isTimedCalendarRow(a)) feedTimedDedupe.add(recommendDedupeKey(a.name));
  }
  /** live 同 act_key 只出现一次；语义键仅用于挡住与 feed 同名的 DB 限时模板 */
  const liveActKeysSeen = new Set();
  const semanticDedupeSeen = new Set();

  function tryPushLiveTimed(entry, actKey) {
    if (!actKey || liveActKeysSeen.has(actKey)) return;
    liveActKeysSeen.add(actKey);
    semanticDedupeSeen.add(recommendDedupeKey(entry.name));
    enriched.push(entry);
  }

  function tryPushDbTimed(entry, displayName) {
    const sem = recommendDedupeKey(displayName);
    if (semanticDedupeSeen.has(sem)) return;
    semanticDedupeSeen.add(sem);
    enriched.push(entry);
  }

  for (const a of feed.activities) {
    if (skipWukaiExcludedLive(a)) continue;
    let stars = Math.round(Number(a.stars));
    if (!Number.isFinite(stars)) stars = WUKAI_FEED_MIN_STARS;
    stars = Math.min(5, Math.max(1, stars));
    if (stars < WUKAI_FEED_MIN_STARS) continue;

    const row = {
      schedule_weekdays: a.schedule_weekdays,
      schedule_start: a.schedule_start,
      schedule_end: a.schedule_end,
      schedule_pin_early_minutes: a.schedule_pin_early_minutes ?? 30,
      monthWeek: a.monthWeek != null ? Number(a.monthWeek) : null,
      monthAnchorWeekday:
        a.monthAnchorWeekday != null ? Number(a.monthAnchorWeekday) : null,
      timeWindows: a.timeWindows,
    };
    const dk = `live:${a.key}:${bizDate}`;
    if (doneKeys.has(dk)) {
      if (!liveActKeysSeen.has(a.key)) {
        liveActKeysSeen.add(a.key);
        semanticDedupeSeen.add(recommendDedupeKey(a.name));
        const evDone = evaluateTimedForRecommend(row, weekday, wallMinutes, dayPlan, bizDate);
        const scheduleLabel =
          evDone?.scheduleLabel ?? formatLabel(a.schedule_start, a.schedule_end);
        enriched.push({
          source: 'live',
          externalKey: a.key,
          name: a.name,
          description: a.description,
          frequency: 'daily',
          sortOrder: a.sortOrder,
          cooldownDays: 1,
          schedulePinned: false,
          scheduleOngoing: false,
          scheduleJustEnded: false,
          scheduleHot: false,
          scheduleLabel,
          hasSchedule: !!scheduleLabel,
          schedulePassed: false,
          recordedDoneToday: true,
          stars,
          wukaiRank: Number(a.wukaiRank ?? a.sortOrder ?? 50) || 50,
          recommendKind: 'timed',
          wukaiTail: false,
          _startM: activityEarliestStartMinutes(row),
          _endM: activityLatestEndMinutes(row),
        });
      }
      continue;
    }
    const ev = evaluateTimedForRecommend(row, weekday, wallMinutes, dayPlan, bizDate);
    if (!ev) continue;
    const schedulePassed = !!ev.schedulePassed;
    const wukaiTail = WUKAI_TAIL_KEYS.has(a.key) && !schedulePassed;
    tryPushLiveTimed(
      {
        source: 'live',
        externalKey: a.key,
        name: a.name,
        description: a.description,
        frequency: 'daily',
        sortOrder: a.sortOrder,
        cooldownDays: 1,
        schedulePinned: ev.schedulePinned,
        scheduleHot: ev.scheduleHot,
        scheduleOngoing: ev.scheduleOngoing,
        scheduleJustEnded: ev.scheduleJustEnded,
        scheduleLabel: ev.scheduleLabel,
        hasSchedule: ev.hasSchedule,
        schedulePassed,
        stars,
        wukaiRank: Number(a.wukaiRank ?? a.sortOrder ?? 50) || 50,
        recommendKind: 'timed',
        wukaiTail,
        _startM: activityEarliestStartMinutes(row),
        _endM: activityLatestEndMinutes(row),
      },
      a.key
    );
  }

  for (const t of tasks) {
    if (!t.schedule_weekdays) continue;
    if (skipDiscouragedForWukai(t)) continue;
    if (skipLegacyMenpaiTemplateWrongSundayOfMonth(t, bizDate, weekday)) continue;

    const dk = `db:${t.id}`;
    const ev = evaluateTimedForRecommend(t, weekday, wallMinutes, dayPlan, bizDate);

    if (doneKeys.has(dk)) {
      const scheduleLabel =
        ev?.scheduleLabel ?? formatLabel(t.schedule_start, t.schedule_end);
      tryPushDbTimed(
        {
          source: 'db',
          id: t.id,
          name: t.name,
          description: t.description,
          frequency: t.frequency,
          sortOrder: t.sortOrder,
          enabled: t.enabled === 1 || t.enabled === true,
          manualSortOrder: t.manualSortOrder ?? null,
          cooldownDays: t.cooldownDays,
          schedulePinned: false,
          scheduleOngoing: false,
          scheduleJustEnded: false,
          scheduleHot: false,
          scheduleLabel,
          hasSchedule: !!scheduleLabel,
          schedulePassed: false,
          recordedDoneToday: true,
          stars: templateStarsFromSort(t.sortOrder),
          wukaiRank: Number(t.sortOrder) || 99,
          recommendKind: 'timed',
          wukaiTail: false,
          _startM: t.schedule_start ? timeToMinutes(t.schedule_start) : null,
          _endM: t.schedule_end ? timeToMinutes(t.schedule_end) : null,
          capTimes: 1,
          remainingTimes: 0,
        },
        t.name
      );
      continue;
    }

    if (!ev) continue;

    let cooldownOk = true;
    if (t.frequency === 'daily') cooldownOk = !doneToday.has(t.id);
    else {
      const last = lastByTask[t.id];
      if (last) {
        const lastStr = `${last.getFullYear()}-${String(last.getMonth() + 1).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`;
        const diff = calendarDaysBetween(lastStr, bizDate);
        cooldownOk = diff >= t.cooldownDays;
      }
    }
    if (!cooldownOk) continue;

    const schedulePassed = !!ev.schedulePassed;
    tryPushDbTimed(
      {
        source: 'db',
        id: t.id,
        name: t.name,
        description: t.description,
        frequency: t.frequency,
        sortOrder: t.sortOrder,
        enabled: t.enabled === 1 || t.enabled === true,
        manualSortOrder: t.manualSortOrder ?? null,
        cooldownDays: t.cooldownDays,
        schedulePinned: ev.schedulePinned,
        scheduleHot: ev.scheduleHot,
        scheduleOngoing: ev.scheduleOngoing,
        scheduleJustEnded: ev.scheduleJustEnded,
        scheduleLabel: ev.scheduleLabel,
        hasSchedule: ev.hasSchedule,
        schedulePassed,
        stars: templateStarsFromSort(t.sortOrder),
        wukaiRank: Number(t.sortOrder) || 99,
        recommendKind: 'timed',
        wukaiTail: false,
        _startM: t.schedule_start ? timeToMinutes(t.schedule_start) : null,
        _endM: t.schedule_end ? timeToMinutes(t.schedule_end) : null,
        capTimes: 1,
        remainingTimes: 1,
      },
      t.name
    );
  }

  for (const t of tasks) {
    if (t.schedule_weekdays) continue;
    if (skipDiscouragedForWukai(t)) continue;
    if (skipWeekendNamedDailyOnWeekday(t, weekday)) continue;
    if (feedTimedDedupe.has(recommendDedupeKey(t.name))) continue;

    if (t.frequency === 'weekly_once' || t.frequency === 'weekly_twice') {
      const row = buildWeeklyRecommendRow(t, bizDate, weekStats);
      if (row) {
        const sem = recommendDedupeKey(t.name);
        if (!semanticDedupeSeen.has(sem)) {
          semanticDedupeSeen.add(sem);
          enriched.push(row);
        }
      }
      continue;
    }

    const ev = evaluateSchedule(t, weekday, wallMinutes);
    const dk = `db:${t.id}`;
    const last = t.id != null ? lastByTask[t.id] : null;

    if (doneKeys.has(dk)) {
      let nextRefreshAt = null;
      let inCooldown = false;
      if (t.frequency === 'four_day') {
        // Fixed rotation tasks should still show next refresh even if recorded done today.
        const nowMs = Date.now();
        const nextMs = nextFixedPeriodRefreshMs(nowMs, t.cycleAnchorAt, t.cooldownDays);
        if (nextMs != null) {
          nextRefreshAt = new Date(nextMs).toISOString();
          const periodMs = Math.max(1, Math.floor(Number(t.cooldownDays) || 4)) * 24 * 60 * 60 * 1000;
          const cycleStartMs = nextMs - periodMs;
          inCooldown = Boolean(last && last.getTime() >= cycleStartMs && last.getTime() < nextMs);
        } else if (last) {
          const readyAtMs = last.getTime() + (Number(t.cooldownDays) || 0) * 24 * 60 * 60 * 1000;
          nextRefreshAt = new Date(readyAtMs).toISOString();
          inCooldown = readyAtMs > nowMs;
        }
      }
      enriched.push({
        source: 'db',
        id: t.id,
        name: t.name,
        description: t.description,
        frequency: t.frequency,
        sortOrder: t.sortOrder,
        enabled: t.enabled === 1 || t.enabled === true,
        manualSortOrder: t.manualSortOrder ?? null,
        cooldownDays: t.cooldownDays,
        lastDoneAt: last ? last.toISOString() : null,
        inCooldown,
        nextRefreshAt,
        schedulePinned: false,
        scheduleLabel: ev.scheduleLabel,
        hasSchedule: ev.hasSchedule,
        schedulePassed: false,
        recordedDoneToday: true,
        stars: templateStarsFromSort(t.sortOrder),
        wukaiRank: Number(t.sortOrder) || 99,
        recommendKind: 'daily',
        wukaiTail: false,
        _startM: null,
        _endM: null,
        capTimes: 1,
        remainingTimes: 0,
      });
      continue;
    }

    if (ev.hasSchedule && !ev.visible) continue;

    let cooldownOk = true;
    let inCooldown = false;
    let nextRefreshAt = null;

    if (t.frequency === 'daily') {
      cooldownOk = !doneToday.has(t.id);
    } else if (t.frequency === 'four_day') {
      // Fixed rotation: always show; compute refresh from persisted anchor when possible.
      const nowMs = Date.now();
      const nextMs = nextFixedPeriodRefreshMs(nowMs, t.cycleAnchorAt, t.cooldownDays);
      if (nextMs != null) {
        nextRefreshAt = new Date(nextMs).toISOString();
        // In fixed rotation, availability depends on whether user already completed during current cycle.
        const periodMs = Math.max(1, Math.floor(Number(t.cooldownDays) || 4)) * 24 * 60 * 60 * 1000;
        const cycleStartMs = nextMs - periodMs;
        inCooldown = Boolean(last && last.getTime() >= cycleStartMs && last.getTime() < nextMs);
      } else if (last) {
        const readyAtMs = last.getTime() + (Number(t.cooldownDays) || 0) * 24 * 60 * 60 * 1000;
        nextRefreshAt = new Date(readyAtMs).toISOString();
        inCooldown = readyAtMs > nowMs;
      }
      cooldownOk = !inCooldown;
    } else if (last) {
      // other non-daily: keep legacy day-based cooldown (hide until days passed)
      const lastStr = `${last.getFullYear()}-${String(last.getMonth() + 1).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`;
      const diff = calendarDaysBetween(lastStr, bizDate);
      cooldownOk = diff >= t.cooldownDays;
    }

    if (!cooldownOk && t.frequency !== 'four_day') continue;

    enriched.push({
      source: 'db',
      id: t.id,
      name: t.name,
      description: t.description,
      frequency: t.frequency,
      sortOrder: t.sortOrder,
      enabled: t.enabled === 1 || t.enabled === true,
      manualSortOrder: t.manualSortOrder ?? null,
      cooldownDays: t.cooldownDays,
      lastDoneAt: last ? last.toISOString() : null,
      inCooldown,
      nextRefreshAt,
      schedulePinned: ev.schedulePinned,
      scheduleLabel: ev.scheduleLabel,
      hasSchedule: ev.hasSchedule,
      schedulePassed: false,
      stars: templateStarsFromSort(t.sortOrder),
      wukaiRank: Number(t.sortOrder) || 99,
      recommendKind: 'daily',
      wukaiTail: false,
      _startM: null,
      _endM: null,
      ...(t.id === 2
        ? (() => {
            const capUnits = 200;
            const remUnits = Math.max(0, capUnits - ghostWeekUsed);
            const capTimes = Math.floor(capUnits / 10);
            const remTimes = Math.floor(remUnits / 10);
            return {
              weeklyCap: capUnits,
              weeklyRemaining: remUnits,
              capTimes,
              remainingTimes: remTimes,
            };
          })()
        : (() => {
            const capTimes = 1;
            const remainingTimes = t.frequency === 'four_day' ? (inCooldown ? 0 : 1) : 1;
            return { capTimes, remainingTimes };
          })()),
    });
  }

  return { enriched, bizDate, weekday, wallMinutes, dayPlan, feed };
}

tasksRouter.get('/recommended', async (req, res) => {
  const { enriched, bizDate, weekday, wallMinutes, dayPlan, feed } = await buildWukaiEnrichedList(req);
  const toSort = enriched.filter((e) => !shouldMoveToBackfillForZeroRemain(e));
  toSort.sort((a, b) => compareWukaiEnrichedEntries(a, b, wallMinutes));
  const tasksOut = toSort.map(({ _startM, _endM, ...rest }) => rest);

  res.json({
    bizDate,
    weekday,
    wallMinutes,
    dayPlan,
    tasks: tasksOut,
    pinnedSummary: toSort
      .filter((x) => x.schedulePinned && !x.schedulePassed && !x.recordedDoneToday)
      .map((x) => x.name),
    activityFeed: {
      source: feed.source,
      fetched: feed.fetched,
      error: feed.error,
      updatedAt: feed.updatedAt,
      count: feed.activities.length,
    },
  });
});

tasksRouter.get('/candidates', async (req, res) => {
  const bizDate = String(req.query.bizDate || todayStr());
  const uid = req.user.id;
  const wd = weekdayFromBizDate(bizDate);
  const rng = monday00RangeByWall(new Date());
  const [doneKeys, lastByTask, qt, feed, weekStats] = await Promise.all([
    loadDoneKeys(uid, bizDate),
    loadLastByTaskId(uid),
    pool.query(
      `SELECT id, name, description, frequency,
              sort_order AS sortOrder, enabled, manual_sort_order AS manualSortOrder,
              cooldown_days AS cooldownDays,
              schedule_weekdays, schedule_start, schedule_end, schedule_pin_early_minutes
       FROM task_templates
       WHERE enabled = 0
       ORDER BY COALESCE(manual_sort_order, sort_order), sort_order, id`
    ),
    getActivityFeed(),
    rng ? loadWeeklyTaskStats(uid, rng.start, rng.end) : Promise.resolve({}),
  ]);
  const list = [];

  for (const t of qt[0] || []) {
    if (t.schedule_weekdays) continue;
    if (skipWeekendNamedDailyOnWeekday(t, wd)) continue;
    if (skipDiscouragedForWukai(t)) continue;
    if (!scheduleMatchesWeekday(t, wd)) continue;

    if (t.frequency === 'weekly_once' || t.frequency === 'weekly_twice') {
      const cap = weeklyCapFromFrequency(t.frequency);
      const st = weekStats[t.id] || { count: 0, lastBiz: null };
      if (st.count >= cap) continue;
      list.push({
        source: 'db',
        id: t.id,
        name: t.name,
        description: t.description,
        frequency: t.frequency,
        enabled: t.enabled === 1 || t.enabled === true,
        manualSortOrder: t.manualSortOrder ?? null,
        kind: 'weekly_template',
        weeklyCap: cap,
        weeklyRemaining: cap - st.count,
      });
      continue;
    }

    const dk = `db:${t.id}`;
    if (doneKeys.has(dk)) continue;

    if (t.frequency === 'daily') {
      list.push({
        source: 'db',
        id: t.id,
        name: t.name,
        description: t.description,
        frequency: t.frequency,
        enabled: t.enabled === 1 || t.enabled === true,
        manualSortOrder: t.manualSortOrder ?? null,
        kind: t.schedule_weekdays ? 'timed_template' : 'daily_template',
      });
    } else {
      const last = lastByTask[t.id];
      let ok = true;
      if (last) {
        const lastStr = `${last.getFullYear()}-${String(last.getMonth() + 1).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`;
        ok = calendarDaysBetween(lastStr, bizDate) >= t.cooldownDays;
      }
      if (ok) {
        list.push({
          source: 'db',
          id: t.id,
          name: t.name,
          description: t.description,
          frequency: t.frequency,
          enabled: t.enabled === 1 || t.enabled === true,
          manualSortOrder: t.manualSortOrder ?? null,
          kind: 'four_day',
        });
      }
    }
  }

  for (const a of feed.activities) {
    if (skipWukaiExcludedLive(a)) continue;
    if (!calendarActivityMatchesDay(a, wd, bizDate)) continue;
    const dk = `live:${a.key}:${bizDate}`;
    if (doneKeys.has(dk)) continue;
    list.push({
      source: 'live',
      externalKey: a.key,
      name: a.name,
      description: a.description,
      frequency: 'daily',
      kind: 'live_activity',
    });
  }

  try {
    const wukai = await buildWukaiEnrichedList(req);
    const forBf = wukai.enriched.filter(shouldMoveToBackfillForZeroRemain);
    const seen = new Set(list.map((x) => `${x.source}:${x.id ?? ''}:${x.externalKey ?? ''}`));
    for (const e of forBf) {
      const k = `${e.source}:${e.id ?? ''}:${e.externalKey ?? ''}`;
      if (seen.has(k)) continue;
      seen.add(k);
      const row = {
        source: e.source,
        id: e.id,
        externalKey: e.externalKey,
        name: e.name,
        description: e.description,
        frequency: e.frequency,
        enabled: e.enabled !== false,
        manualSortOrder: e.manualSortOrder ?? null,
        kind: 'waiting_update',
        capTimes: e.capTimes,
        remainingTimes: 0,
      };
      if (e.weeklyCap != null) {
        row.weeklyCap = e.weeklyCap;
        row.weeklyRemaining = e.weeklyRemaining ?? 0;
      }
      list.push(row);
    }
  } catch {
    /* 与推荐榜同构失败时不阻断补录页 */
  }

  list.sort((a, b) => {
    const na = a.name || '';
    const nb = b.name || '';
    return na.localeCompare(nb, 'zh-CN');
  });

  res.json({ bizDate, weekday: wd, items: list, activityFeed: { source: feed.source, updatedAt: feed.updatedAt } });
});

async function processTaskDone(req, res) {
  const bizDate = String(req.body?.bizDate || todayStr());
  let taskId = null;
  if (req.body?.taskId !== undefined && req.body?.taskId !== null && req.body?.taskId !== '') {
    const n = Number(req.body.taskId);
    if (Number.isFinite(n) && n > 0) taskId = n;
  } else if (req.params?.id !== undefined && req.params?.id !== '') {
    const n = Number(req.params.id);
    if (Number.isFinite(n) && n > 0) taskId = n;
  }
  const externalKey = req.body?.externalKey != null ? String(req.body.externalKey).trim() : '';
  let title = String(req.body?.title || '').trim();
  let startedAt = req.body?.startedAt ? new Date(req.body.startedAt) : null;
  let endedAt = req.body?.endedAt ? new Date(req.body.endedAt) : new Date();
  if (Number.isNaN(endedAt.getTime())) endedAt = new Date();
  if (startedAt && Number.isNaN(startedAt.getTime())) startedAt = null;
  const source = String(req.body?.source || 'complete').slice(0, 32);
  const rawUnitCount = req.body?.unitCount;
  let unitCount = rawUnitCount != null && rawUnitCount !== '' ? Number(rawUnitCount) : null;
  if (unitCount != null) {
    unitCount = Math.floor(unitCount);
    if (!Number.isFinite(unitCount) || unitCount <= 0) unitCount = null;
  }

  if (taskId && externalKey) {
    return res.status(400).json({ error: '请勿同时传 taskId 与 externalKey' });
  }

  if (taskId) {
    const [idRows] = await pool.query(
      'SELECT id, name, frequency, cooldown_days AS cooldownDays FROM task_templates WHERE id = ?',
      [taskId]
    );
    let task = idRows[0];
    /** 推荐榜 id 与库不一致时（未跑 seed、改过表、历史数据等），可按正文标题精确匹配模板名 */
    if (!task && title) {
      const [byName] = await pool.query(
        'SELECT id, name, frequency, cooldown_days AS cooldownDays FROM task_templates WHERE name = ?',
        [title]
      );
      if (byName.length === 1) {
        task = byName[0];
        taskId = task.id;
      } else if (byName.length > 1) {
        return res.status(400).json({ error: '存在同名任务模板，无法匹配唯一任务' });
      }
    }
    if (!task) return res.status(404).json({ error: '任务不存在' });
    if (!title) title = task.name;

    // 抓鬼周上限：每周最多 200 只（可多次保存，每次记录 unit_count，默认 10）。
    if (taskId === 2) {
      const per = unitCount ?? 10;
      if (per % 10 !== 0) {
        return res.status(400).json({ error: '抓鬼数量请按 10 的倍数填写（10,20,30...）' });
      }
      const rng = monday00RangeByWall(endedAt || new Date());
      if (!rng) return res.status(400).json({ error: '结束时间无效' });
      const [[sumRow]] = await pool.query(
        `SELECT COALESCE(SUM(COALESCE(unit_count, 0)), 0) AS s,
                COUNT(*) AS c
           FROM task_done_entries
          WHERE user_id = ? AND task_id = ?
            AND GREATEST(COALESCE(ended_at, created_at), created_at) >= ?
            AND GREATEST(COALESCE(ended_at, created_at), created_at) < ?`,
        [req.user.id, taskId, rng.start, rng.end]
      );
      const used = Number(sumRow?.s || 0);
      const entries = Number(sumRow?.c || 0);
      if (used + per > 200) {
        return res.status(409).json({ error: `本周抓鬼上限 200，只剩 ${Math.max(0, 200 - used)} 只可记录` });
      }
      const wk = todayStr(rng.start);
      const dedupeKey = `db:${taskId}:w${wk}:g${entries + 1}`;
      const saved = await insertDoneEntry(req, {
        bizDate,
        dedupeKey,
        taskId,
        title,
        startedAt,
        endedAt,
        source,
        unitCount: per,
      });
      return res.json({
        id: saved.id,
        taskId,
        bizDate,
        dedupeKey,
        startedAt: saved.startedAt,
        endedAt: saved.endedAt,
        durationSeconds: saved.durationSeconds,
        unitCount: per,
        weekCap: 200,
        weekUsed: used + per,
        weekRemaining: Math.max(0, 200 - (used + per)),
      });
    }

    const wCap = weeklyCapFromFrequency(task.frequency);
    if (wCap > 0) {
      const rng = monday00RangeByWall(endedAt || new Date());
      if (!rng) return res.status(400).json({ error: '结束时间无效' });
      const [cntRows] = await pool.query(
        `SELECT COUNT(*) AS c FROM task_done_entries
         WHERE user_id = ? AND task_id = ?
           AND GREATEST(COALESCE(ended_at, created_at), created_at) >= ?
           AND GREATEST(COALESCE(ended_at, created_at), created_at) < ?`,
        [req.user.id, taskId, rng.start, rng.end]
      );
      const count = Number(cntRows[0]?.c || 0);
      if (count >= wCap) {
        return res.status(409).json({ error: '本周次数已用完' });
      }
      const wk = todayStr(rng.start);
      const dedupeKey = `db:${taskId}:w${wk}:${count + 1}`;
      const [dupW] = await pool.query(
        'SELECT id FROM task_done_entries WHERE user_id = ? AND biz_date = ? AND dedupe_key = ? LIMIT 1',
        [req.user.id, bizDate, dedupeKey]
      );
      if (dupW.length) {
        return res.status(409).json({ error: '该任务在此业务日已记录完成' });
      }
      const saved = await insertDoneEntry(req, {
        bizDate,
        dedupeKey,
        taskId,
        title,
        startedAt,
        endedAt,
        source,
        unitCount: null,
      });
      return res.json({
        id: saved.id,
        taskId,
        bizDate,
        dedupeKey,
        startedAt: saved.startedAt,
        endedAt: saved.endedAt,
        durationSeconds: saved.durationSeconds,
      });
    }

    const dedupeKey = `db:${taskId}`;
    const [dup] = await pool.query(
      'SELECT id FROM task_done_entries WHERE user_id = ? AND biz_date = ? AND dedupe_key = ? LIMIT 1',
      [req.user.id, bizDate, dedupeKey]
    );
    if (dup.length) return res.status(409).json({ error: '该任务在此业务日已记录完成' });

    if (task.frequency === 'daily') {
      /* ok */
    } else {
      const [prev] = await pool.query(
        `SELECT ended_at, created_at FROM task_done_entries WHERE user_id = ? AND task_id = ?`,
        [req.user.id, taskId]
      );
      let last = null;
      for (const c of prev) {
        const lm = lastMomentFromRow(c);
        if (!lm) continue;
        if (!last || lm > last) last = lm;
      }
      if (last) {
        const lastStr = `${last.getFullYear()}-${String(last.getMonth() + 1).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`;
        if (calendarDaysBetween(lastStr, bizDate) < task.cooldownDays) {
          return res.status(409).json({ error: '仍在冷却中' });
        }
      }
    }

    const saved = await insertDoneEntry(req, {
      bizDate,
      dedupeKey,
      taskId,
      title,
      startedAt,
      endedAt,
      source,
      unitCount: null,
    });
    return res.json({
      id: saved.id,
      taskId,
      bizDate,
      dedupeKey,
      startedAt: saved.startedAt,
      endedAt: saved.endedAt,
      durationSeconds: saved.durationSeconds,
    });
  }

  if (!externalKey) return res.status(400).json({ error: '缺少 taskId 或 externalKey' });
  const safeKey = externalKey.replace(/[^\w\-]/g, '_').slice(0, 64);
  const dedupeKey = `live:${safeKey}:${bizDate}`;
  if (!title) title = safeKey;

  const [dup] = await pool.query(
    'SELECT id FROM task_done_entries WHERE user_id = ? AND biz_date = ? AND dedupe_key = ? LIMIT 1',
    [req.user.id, bizDate, dedupeKey]
  );
  if (dup.length) return res.status(409).json({ error: '该活动在此业务日已记录完成' });

  const saved = await insertDoneEntry(req, {
    bizDate,
    dedupeKey,
    taskId: null,
    title,
    startedAt,
    endedAt,
    source,
    unitCount: null,
  });
  return res.json({
    id: saved.id,
    externalKey: safeKey,
    bizDate,
    dedupeKey,
    startedAt: saved.startedAt,
    endedAt: saved.endedAt,
    durationSeconds: saved.durationSeconds,
  });
}

function rowTimeMs(v) {
  if (v == null) return NaN;
  if (v instanceof Date) return v.getTime();
  const t = new Date(v).getTime();
  return Number.isNaN(t) ? NaN : t;
}

function rowDurationSecondsStored(r) {
  const raw =
    r.durationSeconds ??
    r.duration_seconds ??
    r.durationseconds ??
    (typeof r === 'object' && r !== null
      ? Object.entries(r).find(([k]) => k.replace(/_/g, '').toLowerCase() === 'durationseconds')?.[1]
      : undefined);
  if (raw == null) return null;
  const n = typeof raw === 'bigint' ? Number(raw) : Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** mysql2 对 DATE 可能返回 JS Date；String(date) 会变成「Mon Apr 06 2026…」，前端无法展示 */
function rowBizDateToYmd(v) {
  if (v == null) return undefined;
  if (v instanceof Date) {
    if (Number.isNaN(v.getTime())) return undefined;
    const y = v.getFullYear();
    const m = String(v.getMonth() + 1).padStart(2, '0');
    const d = String(v.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  const s = String(v).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  const t = new Date(s);
  if (!Number.isNaN(t.getTime())) {
    const y = t.getFullYear();
    const m = String(t.getMonth() + 1).padStart(2, '0');
    const d = String(t.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  return s;
}

/** 任务耗时 = 结束时间 − 开始时间（秒）；优先用起止时刻当场计算，避免 driver 字段名或历史 NULL */
function mapDoneLogRow(r) {
  const a = rowTimeMs(r.startedAt);
  const b = rowTimeMs(r.endedAt);
  let dur = null;
  if (!Number.isNaN(a) && !Number.isNaN(b)) {
    dur = Math.max(0, Math.floor((b - a) / 1000));
  }
  if (dur == null || !Number.isFinite(dur)) {
    const stored = rowDurationSecondsStored(r);
    if (stored != null && Number.isFinite(stored)) dur = stored;
  }
  return {
    id: Number(r.id),
    title: String(r.title),
    startedAt: r.startedAt ? new Date(r.startedAt).toISOString() : null,
    endedAt: r.endedAt ? new Date(r.endedAt).toISOString() : null,
    durationSeconds: dur != null && Number.isFinite(dur) ? dur : null,
    source: String(r.source),
    createdAt: new Date(r.createdAt).toISOString(),
    bizDate: rowBizDateToYmd(r.bizDateRow ?? r.biz_date),
  };
}

tasksRouter.get('/done-log', async (req, res) => {
  const uid = req.user.id;
  const fromBiz =
    req.query.fromBizDate != null && String(req.query.fromBizDate).trim() !== ''
      ? String(req.query.fromBizDate).trim()
      : null;
  const toBiz =
    req.query.toBizDate != null && String(req.query.toBizDate).trim() !== ''
      ? String(req.query.toBizDate).trim()
      : null;

  if (fromBiz && toBiz) {
    if (fromBiz > toBiz) {
      return res.status(400).json({ error: 'fromBizDate 不能大于 toBizDate' });
    }
    const [rows] = await pool.query(
      `SELECT id, title, started_at AS startedAt, ended_at AS endedAt,
              duration_seconds AS durationSeconds, source, created_at AS createdAt, biz_date AS bizDateRow
       FROM task_done_entries
       WHERE user_id = ? AND biz_date >= ? AND biz_date <= ?
       ORDER BY COALESCE(ended_at, started_at, created_at) ASC, id ASC`,
      [uid, fromBiz, toBiz]
    );
    const items = rows.map((r) => mapDoneLogRow(r));
    return res.json({ fromBizDate: fromBiz, toBizDate: toBiz, items });
  }

  const bizDate = String(req.query.bizDate || todayStr());
  const [rows] = await pool.query(
    `SELECT id, title, started_at AS startedAt, ended_at AS endedAt,
            duration_seconds AS durationSeconds, source, created_at AS createdAt, biz_date AS bizDateRow
     FROM task_done_entries
     WHERE user_id = ? AND biz_date = ?
     ORDER BY COALESCE(ended_at, started_at, created_at) ASC, id ASC`,
    [uid, bizDate]
  );
  const items = rows.map((r) => mapDoneLogRow(r));
  res.json({ fromBizDate: bizDate, toBizDate: bizDate, items });
});

tasksRouter.post('/done', processTaskDone);
tasksRouter.post('/:id/complete', processTaskDone);
