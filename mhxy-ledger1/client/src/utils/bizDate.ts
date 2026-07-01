/** 本地日历日 YYYY-MM-DD（与记账台、服务端 todayStr 一致） */
export function localBizDate(d = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function addLocalDays(dateStr: string, delta: number): string {
  const d = new Date(`${dateStr}T12:00:00`);
  d.setDate(d.getDate() + delta);
  return localBizDate(d);
}

/** 自然日切换阈值：00:00 后即为“今天”（用于未锁定时的默认业务日） */
export const APP_BIZDATE_CUTOFF_HOUR = 0;

/** 未锁定时的“默认业务日”：跨过 00:00 立刻返回今天 */
export function defaultBizDateNow(d = new Date(), cutoffHour = APP_BIZDATE_CUTOFF_HOUR): string {
  const today = localBizDate(d);
  if (d.getHours() < cutoffHour) return addLocalDays(today, -1);
  return today;
}

/** 包含 ymd 的「本地自然周」的周一（周一～周日），与总览 / 任务周逻辑一致 */
export function mondayOfLocalWeekContaining(ymd: string): string {
  const d = new Date(`${ymd}T12:00:00`);
  if (Number.isNaN(d.getTime())) return localBizDate();
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  return localBizDate(d);
}

/** 今天所在「自然周」的周一（与上方业务日期无关；总览「本周」默认用） */
export function mondayOfTodayCalendarWeek(): string {
  return mondayOfLocalWeekContaining(localBizDate());
}

export function isValidYmd(s: string | null | undefined): s is string {
  return typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s);
}

/** 本地展示：YYYY-MM-DD HH:mm:ss（与业务日期同一套数字格式） */
export function formatLocalDateTime(isoOrDate: string | Date | null | undefined): string {
  if (isoOrDate == null || isoOrDate === '') return '—';
  const d =
    typeof isoOrDate === 'string' || typeof isoOrDate === 'number' ? new Date(isoOrDate) : isoOrDate;
  if (Number.isNaN(d.getTime())) return '—';
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  const s = String(d.getSeconds()).padStart(2, '0');
  return `${y}-${m}-${day} ${h}:${min}:${s}`;
}

/** 点卡点数 → 人民币：1 点 = 1 毛 = 0.1 元 */
export const POINT_CARD_YUAN_PER_POINT = 0.1;

export function pointCardPointsToYuan(points: number): number {
  return points * POINT_CARD_YUAN_PER_POINT;
}
