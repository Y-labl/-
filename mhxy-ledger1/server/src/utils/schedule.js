/** MySQL TIME string 'HH:MM:SS' or Date -> minutes from midnight */
export function timeToMinutes(t) {
  if (t == null) return null;
  if (typeof t === 'string') {
    const parts = t.split(':');
    const h = Number(parts[0]);
    const m = Number(parts[1] || 0);
    if (Number.isNaN(h)) return null;
    return h * 60 + m;
  }
  return t.getHours() * 60 + t.getMinutes();
}

export function parseWeekdays(s) {
  if (s == null || s === '') return null;
  return String(s)
    .split(',')
    .map((x) => Number(x.trim()))
    .filter((n) => !Number.isNaN(n) && n >= 0 && n <= 6);
}

/** 仅判断星期是否匹配（补录用：忽略当日是否已过结束时间） */
export function scheduleMatchesWeekday(task, weekday) {
  const days = parseWeekdays(task.schedule_weekdays);
  if (!days || !days.length) return true;
  return days.includes(weekday);
}

/**
 * @param {object} task row with schedule_* fields
 * @param {number} weekday 0 Sun .. 6 Sat (client local)
 * @param {number} wallMinutes minutes from midnight (client local)
 */
export function evaluateSchedule(task, weekday, wallMinutes) {
  const days = parseWeekdays(task.schedule_weekdays);
  const startM = timeToMinutes(task.schedule_start);
  const endM = timeToMinutes(task.schedule_end);
  const pinEarly = Number(task.schedule_pin_early_minutes ?? 30) || 0;

  if (!days || startM == null || endM == null) {
    return {
      hasSchedule: false,
      visible: true,
      schedulePinned: false,
      scheduleLabel: null,
    };
  }

  const wdOk = days.includes(weekday);
  if (!wdOk) {
    return {
      hasSchedule: true,
      visible: false,
      schedulePinned: false,
      scheduleLabel: formatLabel(task.schedule_start, task.schedule_end),
    };
  }

  if (wallMinutes > endM) {
    return {
      hasSchedule: true,
      visible: false,
      schedulePinned: false,
      scheduleLabel: formatLabel(task.schedule_start, task.schedule_end),
    };
  }

  const pinFrom = Math.max(0, startM - pinEarly);
  const schedulePinned = wallMinutes >= pinFrom && wallMinutes <= endM;

  return {
    hasSchedule: true,
    visible: true,
    schedulePinned,
    scheduleLabel: formatLabel(task.schedule_start, task.schedule_end),
  };
}

export function formatLabel(start, end) {
  const a = String(start || '').slice(0, 5);
  const b = String(end || '').slice(0, 5);
  if (!a || !b) return null;
  return `${a}–${b}`;
}

/** 'H:MM' / 'HH:MM:SS' → 'HH:MM:SS' */
function padTimeSql(t) {
  const s = String(t ?? '00:00').trim();
  const full = /^\d{1,2}:\d{2}:\d{2}$/.test(s);
  if (full) {
    const p = s.split(':');
    return `${String(p[0]).padStart(2, '0')}:${p[1]}:${p[2]}`;
  }
  const m = /^(\d{1,2}):(\d{2})$/.exec(s);
  if (!m) return '00:00:00';
  return `${String(m[1]).padStart(2, '0')}:${m[2]}:00`;
}

/**
 * 限时活动的时段列表（单段兼容 schedule_start/end；多段来自 JSON `windows` → timeWindows）
 * @returns {{ schedule_start: string, schedule_end: string }[]}
 */
export function getActivityTimeWindows(task) {
  if (Array.isArray(task.timeWindows) && task.timeWindows.length > 0) {
    return task.timeWindows.map((w) => ({
      schedule_start: padTimeSql(w.schedule_start ?? w.start),
      schedule_end: padTimeSql(w.schedule_end ?? w.end),
    }));
  }
  const days = parseWeekdays(task.schedule_weekdays);
  if (!days?.length) return [];
  if (task.schedule_start == null || task.schedule_end == null) return [];
  const startM = timeToMinutes(task.schedule_start);
  const endM = timeToMinutes(task.schedule_end);
  if (startM == null || endM == null) return [];
  return [
    {
      schedule_start: padTimeSql(task.schedule_start),
      schedule_end: padTimeSql(task.schedule_end),
    },
  ];
}

export function activityEarliestStartMinutes(task) {
  const wins = getActivityTimeWindows(task);
  let min = null;
  for (const w of wins) {
    const m = timeToMinutes(w.schedule_start);
    if (m != null && (min == null || m < min)) min = m;
  }
  return min;
}

export function activityLatestEndMinutes(task) {
  const wins = getActivityTimeWindows(task);
  let max = null;
  for (const w of wins) {
    const m = timeToMinutes(w.schedule_end);
    if (m != null && (max == null || m > max)) max = m;
  }
  return max;
}

/** 业务日当天是当月第几个「周 targetWd」（不是该星期返回 null；0=周日..6=周六） */
export function nthWeekdayIndexInMonth(ymd, targetWd) {
  const [y, m, d] = String(ymd || '').split('-').map(Number);
  if (!y || !m || !d) return null;
  const wd = Number(targetWd);
  if (!Number.isFinite(wd) || wd < 0 || wd > 6) return null;
  const dt = new Date(y, m - 1, d);
  if (dt.getDay() !== wd) return null;
  let n = 0;
  for (let day = 1; day <= d; day++) {
    if (new Date(y, m - 1, day).getDay() === wd) n++;
  }
  return n;
}

/** @deprecated 请用 nthWeekdayIndexInMonth(ymd, 0) */
export function sundayWeekIndexInMonth(ymd) {
  return nthWeekdayIndexInMonth(ymd, 0);
}

/** 限时活动是否落在该业务日的日历规则内（含每月第 N 个「锚定星期」） */
export function calendarActivityMatchesDay(task, weekday, bizDate) {
  const days = parseWeekdays(task.schedule_weekdays);
  const monthWeek = task.monthWeek != null ? Number(task.monthWeek) : null;
  if (monthWeek != null) {
    const anchor =
      task.monthAnchorWeekday != null ? Number(task.monthAnchorWeekday) : 0;
    const idx = nthWeekdayIndexInMonth(bizDate, anchor);
    if (idx !== monthWeek) return false;
  }
  if (!days?.length) return true;
  return days.includes(weekday);
}

/** 与任务页「开场前 30/20/5 分」首档提醒一致：置顶窗不少于此前提（避免 pinEarly=20 时 9:30已提醒但 9:40 才置顶） */
const MECH_RECOMMEND_PIN_LEAD_MIN = 30;

/** 是否有完整「星期 + 起止时段」（搬砖日历推荐仅用这类） */
export function isTimedCalendarRow(task) {
  const days = parseWeekdays(task.schedule_weekdays);
  if (!days?.length) return false;
  const wins = getActivityTimeWindows(task);
  if (!wins.length) return false;
  for (const w of wins) {
    if (timeToMinutes(w.schedule_start) == null || timeToMinutes(w.schedule_end) == null) return false;
  }
  return true;
}

/**
 * 限时活动上「五开推荐榜」：仅星期匹配；dayPlan 时展示该日全部时段；当天若已过结束点仍返回一行并带 schedulePassed（排榜尾 + 补录）。
 * @returns {{ schedulePinned: boolean, scheduleHot: boolean, scheduleOngoing: boolean, scheduleJustEnded: boolean, scheduleLabel: string|null, hasSchedule: boolean, schedulePassed: boolean } | null}
 *          schedulePinned：距开场 ≤schedule_pin_early_minutes（默认 30）且尚未到开场时刻，用于置顶与客户端提醒
 */
export function evaluateTimedForRecommend(task, weekday, wallMinutes, dayPlan, bizDate) {
  if (!isTimedCalendarRow(task)) return null;
  const days = parseWeekdays(task.schedule_weekdays);
  const monthWeek = task.monthWeek != null ? Number(task.monthWeek) : null;
  if (monthWeek != null) {
    const anchor =
      task.monthAnchorWeekday != null ? Number(task.monthAnchorWeekday) : 0;
    if (!bizDate || nthWeekdayIndexInMonth(bizDate, anchor) !== monthWeek) return null;
  }
  if (!days?.includes(weekday)) return null;

  const wins = getActivityTimeWindows(task);
  if (!wins.length) return null;

  const pinEarlyConfigured = Number(task.schedule_pin_early_minutes ?? 30) || 0;
  const pinEarly = Math.max(pinEarlyConfigured, MECH_RECOMMEND_PIN_LEAD_MIN);
  const endGrace = 10; // end + 10 min, then demote/move down
  const labelParts = wins
    .map((w) => formatLabel(w.schedule_start, w.schedule_end))
    .filter(Boolean);
  const scheduleLabel = labelParts.length ? labelParts.join('、') : null;

  if (dayPlan) {
    return {
      schedulePinned: false,
      scheduleHot: false,
      scheduleOngoing: false,
      scheduleJustEnded: false,
      scheduleLabel,
      hasSchedule: true,
      schedulePassed: false,
    };
  }

  let schedulePassed = true;
  let scheduleOngoing = false;
  let scheduleJustEnded = false;
  let schedulePinned = false;

  for (const w of wins) {
    const startM = timeToMinutes(w.schedule_start);
    const endM = timeToMinutes(w.schedule_end);
    if (startM == null || endM == null) continue;
    if (wallMinutes <= endM + endGrace) schedulePassed = false;
    if (wallMinutes >= startM && wallMinutes <= endM) scheduleOngoing = true;
    if (wallMinutes > endM && wallMinutes <= endM + endGrace) scheduleJustEnded = true;
    const pinFrom = Math.max(0, startM - pinEarly);
    if (wallMinutes >= pinFrom && wallMinutes < startM) schedulePinned = true;
  }

  if (schedulePassed) {
    return {
      schedulePinned: false,
      scheduleHot: false,
      scheduleOngoing: false,
      scheduleJustEnded: false,
      scheduleLabel,
      hasSchedule: true,
      schedulePassed: true,
    };
  }

  const scheduleHot = scheduleOngoing || scheduleJustEnded;
  return {
    schedulePinned,
    scheduleHot,
    scheduleOngoing,
    scheduleJustEnded,
    scheduleLabel,
    hasSchedule: true,
    schedulePassed: false,
  };
}

/** 与 feed / DB 重复的限时活动去重（天降星辰/辰星、帮派迷宫、门派闯关等） */
export function recommendDedupeKey(name) {
  const raw = String(name || '');
  const n = raw.replace(/^(活动：|帮战相关：|日常：|副本：|侠士)/, '').trim();
  if (/天降/.test(n) && /(星辰|辰星)/.test(n)) return 'dedupe:tianjiang';
  if (/帮派/.test(n) && /迷宫/.test(n)) return 'dedupe:bangpai-maze';
  if (/门派闯关/.test(n)) return 'dedupe:menpai';
  return `dedupe:${n}`;
}
