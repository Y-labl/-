import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import './TasksPage.css';
import {
  api,
  type MechLedgerDailyResponse,
  type RecommendedResponse,
  type TaskCandidatesResponse,
  type TaskDoneLogResponse,
  type TaskTemplate,
} from '../api';
import { BizDatePickerField } from '../components/BizDatePickerField';
import { TablePaginationBar } from '../components/TablePaginationBar';
import { useLocalClock } from '../hooks/useLocalClock';
import { useTablePagination } from '../hooks/useTablePagination';
import { addLocalDays, localBizDate } from '../utils/bizDate';
import {
  artifactTaskTitleFromTaskName,
  normalizeArtifactDayPair,
  splitSelectedArtifactsByPhase,
} from '../utils/artifacts';
import { getClientPrefsSnapshot, patchClientPrefs } from '../utils/clientPrefsStore';
import { BIZ_DATE_PAGE } from '../utils/pageBizDate';
import { usePageBizDate } from '../utils/usePageBizDate';

const EMPTY_TASK_BF: TaskCandidatesResponse['items'] = [];
const EMPTY_TASK_LOG: TaskDoneLogResponse['items'] = [];

function toLocalDatetimeValue(d: Date) {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** 展示/解析：年-月-日 时:分:秒（本地） */
function formatTaskDateTime(d: Date) {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function parseTaskDateTime(s: string): Date | null {
  const t = s.trim();
  if (!t) return null;
  const m =
    /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$/.exec(t) ||
    /^(\d{4})-(\d{2})-(\d{2})$/.exec(t);
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const day = Number(m[3]);
  const h = m[4] != null ? Number(m[4]) : 0;
  const mi = m[5] != null ? Number(m[5]) : 0;
  const sec = m[6] != null ? Number(m[6]) : 0;
  const d = new Date(y, mo - 1, day, h, mi, sec);
  return Number.isNaN(d.getTime()) ? null : d;
}

function getTaskCompleteChainEnd(bizDate: string): string | null {
  const v = getClientPrefsSnapshot().taskCompleteChainEnd?.[bizDate];
  return typeof v === 'string' && v.length ? v : null;
}

function setTaskCompleteChainEnd(bizDate: string, endedAtIso: string) {
  const snap = getClientPrefsSnapshot();
  patchClientPrefs({
    taskCompleteChainEnd: { ...snap.taskCompleteChainEnd, [bizDate]: endedAtIso },
  });
}

/** 记账台累计计时时长对应的「计时起点」墙钟时间（与 MechanicalLedgerPage 一致；数据来自 mech_ledger_day_meta） */
function getLedgerWallStartMsFromDaily(day: MechLedgerDailyResponse): number | null {
  const base = Math.max(0, Math.floor(Number(day.ledgerBaseElapsedSec) || 0));
  const runStart =
    day.ledgerRunStartAtMs != null && Number.isFinite(Number(day.ledgerRunStartAtMs))
      ? Number(day.ledgerRunStartAtMs)
      : null;
  const now = Date.now();
  const runningExtra = runStart != null ? Math.max(0, Math.floor((now - runStart) / 1000)) : 0;
  const elapsedSec = base + runningExtra;
  if (elapsedSec <= 0) return null;
  return now - elapsedSec * 1000;
}

/**
 * 默认开始时刻：
 * - 当日首条（尚无上一任务结束时间）：取 业务日 10:00 与「记账台累计计时起点」的较大者（未点过开始计时则仅 10:00）。
 * - 之后：取「上一任务结束时间」与「记账台计时起点」的较大者，避免早于实际上机/计时起点。
 */
async function resolveDefaultTaskStartTime(bizDate: string, now: Date): Promise<Date> {
  const ten = new Date(`${bizDate}T10:00:00`);

  let wall: Date | null = null;
  try {
    const day = await api.mechLedgerDaily(bizDate);
    const w = getLedgerWallStartMsFromDaily(day);
    if (w != null && w <= now.getTime()) wall = new Date(w);
  } catch {
    /* ignore */
  }

  const chainIso = getTaskCompleteChainEnd(bizDate);
  let start: Date;

  if (chainIso) {
    const prev = new Date(chainIso);
    const prevOk = Number.isNaN(prev.getTime()) ? now : prev;
    if (wall) {
      start = prevOk.getTime() > wall.getTime() ? prevOk : wall;
    } else {
      start = ten.getTime() > prevOk.getTime() ? ten : prevOk;
    }
  } else if (wall) {
    start = ten.getTime() > wall.getTime() ? ten : wall;
  } else {
    start = ten;
  }

  if (start.getTime() > now.getTime()) {
    start = new Date(Math.max(0, now.getTime() - 60_000));
  }
  return start;
}

function formatDurationSec(sec: number | null | undefined) {
  if (sec == null || !Number.isFinite(sec) || sec < 0) return '—';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

/** 任务耗时（秒）= 结束时间 − 开始时间；与接口 durationSeconds 一致时优先用接口值 */
function taskRowDurationSeconds(row: {
  startedAt: string | null;
  endedAt: string | null;
  durationSeconds?: number | null;
}) {
  if (row.durationSeconds != null && Number.isFinite(row.durationSeconds)) {
    return row.durationSeconds;
  }
  if (!row.startedAt || !row.endedAt) return null;
  const a = new Date(row.startedAt).getTime();
  const b = new Date(row.endedAt).getTime();
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.max(0, Math.floor((b - a) / 1000));
}

function formatNow() {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function formatRefreshCountdown(ms: number) {
  const t = Math.max(0, Math.floor(ms / 1000));
  const d = Math.floor(t / 86400);
  const h = Math.floor((t % 86400) / 3600);
  const m = Math.floor((t % 3600) / 60);
  const s = t % 60;
  if (d > 0) return `${d}天${h}小时后刷新`;
  if (h > 0) return `${h}小时${m}分后刷新`;
  return `${m}分${s}秒后刷新`;
}

/**
 * 四天轮换副本：按固定节奏显示“xx后刷新”，不依赖你是否点过完成。
 * 业务日体系以 10:00 为常用日界；这里用一个固定锚点做 4 天滚动。
 */
function parseMs(isoLike: string | null | undefined) {
  if (!isoLike) return null;
  const d = new Date(isoLike);
  const ms = d.getTime();
  return Number.isNaN(ms) ? null : ms;
}

type TasksTab = 'recommended' | 'backfill' | 'log';

type BackfillRow = TaskCandidatesResponse['items'][number];

function formatTaskLogDateTime(iso: string | null) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return formatTaskDateTime(d);
}

function formatTaskBizDateAsDateTime(ymd: string | Date | null | undefined) {
  if (ymd == null) return '—';
  if (ymd instanceof Date) {
    if (Number.isNaN(ymd.getTime())) return '—';
    const d = new Date(ymd.getFullYear(), ymd.getMonth(), ymd.getDate(), 0, 0, 0);
    return formatTaskDateTime(d);
  }
  const s = String(ymd).trim();
  if (!s) return '—';
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const d = new Date(`${s}T00:00:00`);
    if (Number.isNaN(d.getTime())) return s;
    return formatTaskDateTime(d);
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
  if (m) {
    const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 0, 0, 0);
    if (!Number.isNaN(d.getTime())) return formatTaskDateTime(d);
  }
  const parsed = new Date(s);
  if (!Number.isNaN(parsed.getTime())) {
    const d = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate(), 0, 0, 0);
    return formatTaskDateTime(d);
  }
  return s;
}

function sourceLabel(src: string) {
  if (src === 'backfill') return '补录';
  if (src === 'complete') return '完成';
  return src;
}

/** 解析 scheduleLabel：如15:00–17:00 或 13:30–15:30、16:00–18:00 */
function parseScheduleWindowsFromLabel(label: string): { startM: number; endM: number }[] {
  if (!label || !String(label).trim()) return [];
  const parts = String(label)
    .split('、')
    .map((s) => s.trim())
    .filter(Boolean);
  const out: { startM: number; endM: number }[] = [];
  for (const p of parts) {
    const m = /^(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})/.exec(p);
    if (!m) continue;
    const startM = Number(m[1]) * 60 + Number(m[2]);
    const endM = Number(m[3]) * 60 + Number(m[4]);
    if (Number.isFinite(startM) && Number.isFinite(endM)) out.push({ startM, endM });
  }
  return out;
}

/** 当日下一档尚未开始的场次开始时刻（分钟）；无则 null */
function nextUpcomingStartMinutes(windows: { startM: number; endM: number }[], wallM: number): number | null {
  const upcoming = windows.map((w) => w.startM).filter((sm) => wallM < sm);
  if (!upcoming.length) return null;
  return Math.min(...upcoming);
}

const PRESTART_REMINDER_OFFSETS = [30, 20, 5] as const;

function taskReminderKey(t: TaskTemplate): string {
  if (t.source === 'live' && t.externalKey) return `live:${t.externalKey}`;
  if (t.id != null) return `db:${t.id}`;
  return `name:${t.name}`;
}

function readPreStartStickyKeys(bizDate: string): Set<string> {
  const arr = getClientPrefsSnapshot().taskPrestartSticky?.[bizDate];
  if (!Array.isArray(arr)) return new Set();
  return new Set(arr.filter((x): x is string => typeof x === 'string'));
}

function writePreStartStickyKeys(bizDate: string, keys: Set<string>) {
  const snap = getClientPrefsSnapshot();
  patchClientPrefs({
    taskPrestartSticky: { ...snap.taskPrestartSticky, [bizDate]: [...keys] },
  });
}

function setsEqualString(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  for (const x of a) {
    if (!b.has(x)) return false;
  }
  return true;
}

/** 开场提醒触发后保持置顶：仅当本场尚未开始且任务仍在榜 */
function prunePreStartStickyKeys(sticky: Set<string>, list: TaskTemplate[], bizDate: string): Set<string> {
  if (bizDate !== localBizDate()) return sticky;
  const wallM = new Date().getHours() * 60 + new Date().getMinutes();
  const next = new Set<string>();
  for (const key of sticky) {
    const t = list.find((x) => taskReminderKey(x) === key);
    if (!t || t.recordedDoneToday || t.schedulePassed) continue;
    const label = t.scheduleLabel;
    if (!label) continue;
    const wins = parseScheduleWindowsFromLabel(label);
    if (!wins.length) continue;
    const startM = nextUpcomingStartMinutes(wins, wallM);
    if (startM != null && wallM < startM) next.add(key);
  }
  return next;
}

function taskStickyPinned(e: TaskTemplate, stickySet: Set<string>): boolean {
  if (!stickySet.size) return false;
  if (e.recordedDoneToday || e.schedulePassed || e.scheduleHot) return false;
  return stickySet.has(taskReminderKey(e));
}

/** 与 server recommendSegment 一致，另计「提醒置顶」 */
function clientRecommendSegment(e: TaskTemplate, stickySet: Set<string>): number {
  if (e.recordedDoneToday) return 7;
  if (e.schedulePassed) return 6;
  if (e.scheduleHot && !e.recordedDoneToday && !e.schedulePassed) return 0;
  const pinSoon = e.schedulePinned || taskStickyPinned(e, stickySet);
  if (pinSoon && !e.recordedDoneToday && !e.schedulePassed) return 1;
  if (e.recommendKind === 'daily' || e.recommendKind === 'weekly') return 2;
  if (e.inCooldown) return 4;
  if (e.wukaiTail) return 5;
  return 3;
}

function earliestUpcomingStartFromLabel(label: string | null | undefined, wallM: number): number | null {
  if (!label) return null;
  const wins = parseScheduleWindowsFromLabel(label);
  return nextUpcomingStartMinutes(wins, wallM);
}

/** 与 server compareWukaiEnrichedEntries 对齐，并支持提醒置顶 */
function compareRecommendedTasksClient(
  a: TaskTemplate,
  b: TaskTemplate,
  wallMinutes: number,
  stickySet: Set<string>,
): number {
  const sa = clientRecommendSegment(a, stickySet);
  const sb = clientRecommendSegment(b, stickySet);
  if (sa !== sb) return sa - sb;

  const mo = (x: TaskTemplate) => {
    const n = x.manualSortOrder != null ? Number(x.manualSortOrder) : NaN;
    return Number.isFinite(n) ? n : null;
  };
  const ao = mo(a);
  const bo = mo(b);

  if (sa === 2 || sa === 7) {
    if (ao != null || bo != null) {
      if ((ao ?? 1e9) !== (bo ?? 1e9)) return (ao ?? 1e9) - (bo ?? 1e9);
    }
    if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
    return (a.id || 0) - (b.id || 0);
  }

  const oa = a.scheduleHot ? 0 : 1;
  const ob = b.scheduleHot ? 0 : 1;
  if (oa !== ob) return oa - ob;
  const pinA = !!a.schedulePinned || taskStickyPinned(a, stickySet);
  const pinB = !!b.schedulePinned || taskStickyPinned(b, stickySet);
  const pa = pinA ? 0 : 1;
  const pb = pinB ? 0 : 1;
  if (pa !== pb) return pa - pb;
  const starsCmp = (b.stars ?? 3) - (a.stars ?? 3);
  if (starsCmp !== 0) return starsCmp;
  const wr = (a.wukaiRank ?? 99) - (b.wukaiRank ?? 99);
  if (wr !== 0) return wr;
  if (!pinA && !pinB) {
    const aStart = earliestUpcomingStartFromLabel(a.scheduleLabel, wallMinutes);
    const bStart = earliestUpcomingStartFromLabel(b.scheduleLabel, wallMinutes);
    if (aStart != null && bStart != null && wallMinutes < aStart && wallMinutes < bStart && aStart !== bStart) {
      return aStart - bStart;
    }
  }
  if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
  if (a.source !== b.source) return a.source === 'live' ? -1 : 1;
  return (a.id || 0) - (b.id || 0);
}

/** 补录榜「分类」列：服务端 kind → 中文 */
function backfillCandidateKindLabel(kind: string): string {
  const map: Record<string, string> = {
    waiting_update: '次数用尽',
    live_activity: '限时活动',
    daily_template: '日常模板',
    timed_template: '定时模板',
    weekly_template: '周常模板',
    four_day: '四天副本',
  };
  return map[kind] ?? kind;
}

function StarRow({ n }: { n: number }) {
  const s = Math.min(5, Math.max(1, Math.round(Number(n) || 3)));
  return (
    <span className="tasks-wukai-stars" style={{ color: 'var(--gold-bright, #e8c547)' }} aria-label={`${s} 星`}>
      {'★'.repeat(s)}
      <span style={{ opacity: 0.35 }}>{'★'.repeat(5 - s)}</span>
    </span>
  );
}

export function TasksPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const tasksTab: TasksTab =
    tabParam === 'backfill' ? 'backfill' : tabParam === 'log' ? 'log' : 'recommended';

  const setTasksTab = useCallback(
    (t: TasksTab) => {
      if (t === 'backfill') setSearchParams({ tab: 'backfill' });
      else if (t === 'log') setSearchParams({ tab: 'log' });
      else setSearchParams({});
    },
    [setSearchParams]
  );

  const [bizDate, setBizDate] = usePageBizDate(BIZ_DATE_PAGE.tasks);
  const { wallMinutes } = useLocalClock(15000);
  const [recommendedDayPlan, setRecommendedDayPlan] = useState(false);
  const [tasks, setTasks] = useState<TaskTemplate[]>([]);
  const [feedMeta, setFeedMeta] = useState<RecommendedResponse['activityFeed'] | null>(null);
  const [pinnedSummary, setPinnedSummary] = useState<string[]>([]);
  const tasksRef = useRef<TaskTemplate[]>([]);
  const preStartFiredRef = useRef<Set<string>>(new Set());
  /** 已弹过 30/20/5 分提醒的限时任务，本场开始前保持置顶（user_client_prefs 按业务日） */
  const [stickyRemindedKeys, setStickyRemindedKeys] = useState<Set<string>>(() => new Set());
  const [err, setErr] = useState('');
  const [pick, setPick] = useState<TaskTemplate | null>(null);
  const [completeModalErr, setCompleteModalErr] = useState('');
  const [completeSubmitting, setCompleteSubmitting] = useState(false);
  const [startedAt, setStartedAt] = useState('');
  const [endedAt, setEndedAt] = useState(() => formatTaskDateTime(new Date()));
  const [ghostUnitCount, setGhostUnitCount] = useState(10);
  const [clockStr, setClockStr] = useState(formatNow);
  const [nowMs, setNowMs] = useState(() => Date.now());

  const [bfData, setBfData] = useState<TaskCandidatesResponse | null>(null);
  const [bfPick, setBfPick] = useState<BackfillRow | null>(null);
  const [bfStartedAt, setBfStartedAt] = useState('');
  const [bfEndedAt, setBfEndedAt] = useState(toLocalDatetimeValue(new Date()));
  const [bfMsg, setBfMsg] = useState('');
  const [artifactSelected, setArtifactSelected] = useState<string[]>([]);
  const [logData, setLogData] = useState<TaskDoneLogResponse | null>(null);
  const [logRangeFrom, setLogRangeFrom] = useState(() => bizDate);
  const [logRangeTo, setLogRangeTo] = useState(() => bizDate);

  const artifactByPhase = useMemo(() => splitSelectedArtifactsByPhase(artifactSelected), [artifactSelected]);

  useEffect(() => {
    void api
      .artifactDaySelectedGet(bizDate)
      .then((r) => {
        const raw = Array.isArray(r.selected) ? r.selected.slice(0, 2) : [];
        setArtifactSelected(raw.length === 2 ? normalizeArtifactDayPair(raw) : raw);
      })
      .catch(() => setArtifactSelected([]));
  }, [bizDate]);

  const loadRecommended = useCallback(async () => {
    setErr('');
    try {
      const today = localBizDate();
      const viewingToday = bizDate === today;
      const r = await api.tasksRecommended(bizDate, viewingToday ? { wallMinutes } : undefined);
      setTasks(r.tasks);
      setFeedMeta(r.activityFeed);
      setPinnedSummary(r.pinnedSummary);
      setRecommendedDayPlan(!!r.dayPlan);
      setClockStr(formatNow());
    } catch (e) {
      setErr(e instanceof Error ? e.message : '加载失败');
    }
  }, [bizDate, wallMinutes]);

  const loadBackfill = useCallback(async () => {
    setErr('');
    setBfMsg('');
    try {
      const r = await api.taskCandidates(bizDate);
      setBfData(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : '加载失败');
    }
  }, [bizDate]);

  const persistManualOrder = useCallback(async (nextTasks: TaskTemplate[]) => {
    const ids = nextTasks
      .filter((t) => t.source === 'db' && t.enabled !== false && t.id != null)
      .map((t) => Number(t.id))
      .filter((x) => Number.isFinite(x) && x > 0);
    if (!ids.length) return;
    await api.taskTemplateReorder(ids);
  }, []);

  const toggleTemplateEnabled = useCallback(
    async (id: number, enabled: boolean) => {
      await api.taskTemplateUpdate(id, { enabled });
      await Promise.all([loadRecommended(), loadBackfill()]);
    },
    [loadBackfill, loadRecommended]
  );

  const loadTaskLog = useCallback(async () => {
    setErr('');
    try {
      const from = logRangeFrom.trim();
      const to = logRangeTo.trim();
      if (!from || !to) {
        setErr('请填写任务记录的起止业务日');
        return;
      }
      if (from > to) {
        setErr('起始业务日不能晚于结束业务日');
        return;
      }
      const r = await api.tasksDoneLog({ fromBizDate: from, toBizDate: to });
      setLogData(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : '加载失败');
      setLogData(null);
    }
  }, [logRangeFrom, logRangeTo]);

  useEffect(() => {
    setLogRangeFrom(bizDate);
    setLogRangeTo(bizDate);
  }, [bizDate]);

  useEffect(() => {
    setStickyRemindedKeys(readPreStartStickyKeys(bizDate));
  }, [bizDate]);

  const clientStickySortApplies =
    tasksTab === 'recommended' && !recommendedDayPlan && bizDate === localBizDate();

  const displayTasks = useMemo(() => {
    if (!clientStickySortApplies) return tasks;
    return [...tasks].sort((a, b) => compareRecommendedTasksClient(a, b, wallMinutes, stickyRemindedKeys));
  }, [tasks, wallMinutes, stickyRemindedKeys, clientStickySortApplies]);

  const recPg = useTablePagination(displayTasks);
  const bfPg = useTablePagination(bfData?.items ?? EMPTY_TASK_BF);
  const logPg = useTablePagination(logData?.items ?? EMPTY_TASK_LOG);

  const moveTemplate = useCallback(
    async (id: number, dir: -1 | 1) => {
      setTasks((prev) => {
        const sorted = clientStickySortApplies
          ? [...prev].sort((a, b) =>
              compareRecommendedTasksClient(a, b, wallMinutes, stickyRemindedKeys),
            )
          : prev;
        const idx = sorted.findIndex((t) => t.source === 'db' && Number(t.id) === id);
        if (idx < 0) return prev;
        const row = sorted[idx];
        if (row.enabled === false) return prev;
        const targetIdx = idx + dir;
        if (targetIdx < 0 || targetIdx >= sorted.length) return prev;
        const target = sorted[targetIdx];
        if (target.source !== 'db' || target.enabled === false) return prev;
        const ia = prev.indexOf(row);
        const ib = prev.indexOf(target);
        if (ia < 0 || ib < 0) return prev;
        const next = [...prev];
        next[ia] = target;
        next[ib] = row;
        const persistOrder = clientStickySortApplies
          ? [...next].sort((a, b) =>
              compareRecommendedTasksClient(a, b, wallMinutes, stickyRemindedKeys),
            )
          : next;
        void persistManualOrder(persistOrder).catch(() => {});
        return next;
      });
    },
    [persistManualOrder, clientStickySortApplies, wallMinutes, stickyRemindedKeys],
  );

  useEffect(() => {
    if (tasksTab !== 'recommended') return;
    loadRecommended();
  }, [tasksTab, loadRecommended]);

  useEffect(() => {
    if (tasksTab !== 'recommended') return;
    const id = window.setInterval(loadRecommended, 30000);
    return () => window.clearInterval(id);
  }, [tasksTab, loadRecommended]);

  useEffect(() => {
    if (tasksTab !== 'backfill') return;
    loadBackfill();
  }, [tasksTab, loadBackfill]);

  useEffect(() => {
    if (tasksTab !== 'log') return;
    loadTaskLog();
  }, [tasksTab, loadTaskLog]);

  useEffect(() => {
    setErr('');
    setBfMsg('');
  }, [tasksTab]);

  useEffect(() => {
    const id = window.setInterval(() => setClockStr(formatNow()), 1000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (tasksTab !== 'recommended') return;
    const id = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [tasksTab]);

  useEffect(() => {
    tasksRef.current = tasks;
  }, [tasks]);

  useEffect(() => {
    preStartFiredRef.current = new Set();
  }, [bizDate]);

  const tickPreStartReminders = useCallback(() => {
    if (bizDate !== localBizDate()) return;
    const list = tasksRef.current;
    let namesAlert: string[] = [];

    setStickyRemindedKeys((prev) => {
      let next = prunePreStartStickyKeys(prev, list, bizDate);
      const now = new Date();
      const wallM = now.getHours() * 60 + now.getMinutes();
      namesAlert = [];
      for (const t of list) {
        if (t.recordedDoneToday || t.schedulePassed) continue;
        const label = t.scheduleLabel;
        if (!label) continue;
        const wins = parseScheduleWindowsFromLabel(label);
        if (!wins.length) continue;
        const startM = nextUpcomingStartMinutes(wins, wallM);
        if (startM == null || wallM >= startM) continue;
        let matchedOff: (typeof PRESTART_REMINDER_OFFSETS)[number] | null = null;
        for (const off of PRESTART_REMINDER_OFFSETS) {
          if (wallM === startM - off) {
            matchedOff = off;
            break;
          }
        }
        if (matchedOff == null) continue;
        const slotKey = `${bizDate}|${taskReminderKey(t)}|${matchedOff}`;
        if (preStartFiredRef.current.has(slotKey)) continue;
        preStartFiredRef.current.add(slotKey);
        next.add(taskReminderKey(t));
        namesAlert.push(t.name);
      }
      if (setsEqualString(prev, next)) return prev;
      writePreStartStickyKeys(bizDate, next);
      return next;
    });

    if (namesAlert.length) {
      const msg = `限时活动即将开始（开场前提醒）：\n\n${namesAlert.join('、')}`;
      window.alert(msg);
    }
  }, [bizDate]);

  useEffect(() => {
    if (tasksTab !== 'recommended') return;
    tickPreStartReminders();
    const id = window.setInterval(tickPreStartReminders, 15 * 1000);
    return () => window.clearInterval(id);
  }, [tasksTab, tickPreStartReminders]);

  async function openComplete(t: TaskTemplate) {
    setCompleteModalErr('');
    setPick(t);
    setGhostUnitCount(10);
    const now = new Date();
    const start = await resolveDefaultTaskStartTime(bizDate, now);
    setStartedAt(formatTaskDateTime(start));
    setEndedAt(formatTaskDateTime(now));
  }

  async function confirmComplete() {
    if (!pick || completeSubmitting) return;
    setCompleteModalErr('');
    setErr('');

    const endD = (endedAt ? parseTaskDateTime(endedAt) : null) ?? new Date();
    if (Number.isNaN(endD.getTime())) {
      setCompleteModalErr('结束时间格式无效，请使用 年-月-日 时:分:秒');
      return;
    }
    let startDate = startedAt.trim() ? parseTaskDateTime(startedAt) : null;
    if (!startDate || Number.isNaN(startDate.getTime())) {
      startDate = await resolveDefaultTaskStartTime(bizDate, endD);
    }
    if (startDate.getTime() > endD.getTime()) {
      startDate = new Date(endD.getTime() - 60_000);
    }
    const s = startDate.toISOString();
    const e = endD.toISOString();

    const canDb = pick.source === 'db' && pick.id != null && Number(pick.id) > 0;
    const canLive = pick.source === 'live' && pick.externalKey;
    if (!canDb && !canLive) {
      setCompleteModalErr('无法识别任务，请刷新推荐榜后重试');
      return;
    }

    setCompleteSubmitting(true);
    try {
      if (canLive) {
        await api.taskDone({
          bizDate,
          externalKey: pick.externalKey!,
          title: pick.name,
          startedAt: s,
          endedAt: e,
          source: 'complete',
        });
      } else {
        const artTitle =
          /神器任务/.test(String(pick.name || '')) && artifactSelected.length === 2
            ? artifactTaskTitleFromTaskName(pick.name, artifactSelected)
            : null;
        await api.taskDone({
          bizDate,
          taskId: Number(pick.id),
          title: artTitle || pick.name,
          startedAt: s,
          endedAt: e,
          ...(Number(pick.id) === 2 ? { unitCount: ghostUnitCount } : {}),
          source: 'complete',
        });
      }
      setTaskCompleteChainEnd(bizDate, e);
      setPick(null);
      setCompleteModalErr('');
      await loadRecommended();
      void loadTaskLog();
    } catch (ex) {
      const msg = ex instanceof Error ? ex.message : '完成失败';
      setCompleteModalErr(msg);
      setErr(msg);
    } finally {
      setCompleteSubmitting(false);
    }
  }

  function openBackfillRow(r: BackfillRow) {
    setBfPick(r);
    const now = new Date();
    const start = new Date(now.getTime() - 45 * 60000);
    setBfStartedAt(toLocalDatetimeValue(start));
    setBfEndedAt(toLocalDatetimeValue(now));
  }

  async function confirmBackfill() {
    if (!bfPick) return;
    setErr('');
    try {
      const s = bfStartedAt ? new Date(bfStartedAt).toISOString() : null;
      const e = bfEndedAt ? new Date(bfEndedAt).toISOString() : new Date().toISOString();
      if (bfPick.source === 'live' && bfPick.externalKey) {
        await api.taskDone({
          bizDate,
          externalKey: bfPick.externalKey,
          title: bfPick.name,
          startedAt: s,
          endedAt: e,
          source: 'backfill',
        });
      } else if (bfPick.id) {
        const artTitle =
          /神器任务/.test(String(bfPick.name || '')) && artifactSelected.length === 2
            ? artifactTaskTitleFromTaskName(bfPick.name, artifactSelected)
            : null;
        await api.taskDone({
          bizDate,
          taskId: bfPick.id,
          title: artTitle || bfPick.name,
          startedAt: s,
          endedAt: e,
          source: 'backfill',
        });
      }
      setBfMsg(`已补录：${bfPick.name}`);
      setBfPick(null);
      await loadBackfill();
      void loadTaskLog();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : '补录失败');
    }
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <h2>搬砖日历 · 五开必刷任务榜</h2>
          <p className="muted" style={{ margin: '0.25rem 0 0', fontSize: '0.85rem' }}>
            本地时间 {clockStr}
            {tasksTab === 'recommended'
              ? ' · 推荐榜仅「有具体时段」的五开高收益活动；换日历时按该日星期列出。'
              : tasksTab === 'backfill'
                ? ' · 补录仅写入已完成记录，不刷新推荐排序。'
                : ' · 任务记录可按业务日区间筛选，时间均为本地显示。'}
          </p>
        </div>
        <div className="row" style={{ alignItems: 'center' }}>
          {tasksTab === 'recommended' && (
            <button type="button" className="btn btn-ghost" onClick={loadRecommended}>
              刷新
            </button>
          )}
          {tasksTab === 'backfill' && (
            <button type="button" className="btn btn-ghost" onClick={loadBackfill}>
              刷新
            </button>
          )}
          {tasksTab === 'log' && (
            <button type="button" className="btn btn-ghost" onClick={loadTaskLog}>
              刷新
            </button>
          )}
        </div>
      </div>

      <div className="row" style={{ marginBottom: '0.85rem', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          type="button"
          className={`btn ${tasksTab === 'recommended' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTasksTab('recommended')}
        >
          推荐榜
        </button>
        <button
          type="button"
          className={`btn ${tasksTab === 'log' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTasksTab('log')}
        >
          任务记录
        </button>
        <button
          type="button"
          className={`btn ${tasksTab === 'backfill' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTasksTab('backfill')}
        >
          补录
        </button>
      </div>

      {tasksTab === 'recommended' && (
        <>
          <p className="muted">
            排序：<strong>① 全天/日常与周常</strong>（时段列为「全天」或周常次数等）→ <strong>② 普通限时</strong>（具体钟点时段）→ <strong>③ 五开较少刷的限时</strong>→ <strong>④ 今日已过期限时</strong>→ <strong>⑤ 已完成</strong>。
            距某限时开场 ≤30 分钟且尚未开场时，该任务<strong>置顶</strong>并覆盖上述顺序；查看<strong>今天</strong>推荐榜时，系统会在开场前 <strong>30 分、20 分、5 分</strong>各弹框提醒一次，开场后不再提醒。
            任一档提醒弹出后，该活动在本场开始前会<strong>保持置顶</strong>，状态列为<strong>即将开始</strong>（刷新页面仍有效，开场或已过期限后自动取消）。
            非当日为整日预览。数据：<code>ACTIVITIES_FEED_URL</code> / <code>wukai-activities-feed.json</code>（限时星级 ≥4）。
          </p>
          {feedMeta && (
            <p className="muted" style={{ fontSize: '0.82rem' }}>
              数据源：{feedMeta.source}
              {feedMeta.fetched ? '（成功）' : '（失败回退）'}
              {feedMeta.error ? ` · ${feedMeta.error}` : ''} · 活动条数 {feedMeta.count} · {feedMeta.updatedAt}
            </p>
          )}
        </>
      )}

      {tasksTab === 'backfill' && (
        <p className="muted">
          已从推荐榜消失或未点「完成」的任务不会写入「每日已刷」。在此按业务日补录；列表含当日星期匹配的日常/副本与限时活动（含已结束的活动）。
        </p>
      )}

      {tasksTab === 'log' && (
        <>
          <p className="muted">
            以下为已写入库的任务：开始时间、结束时间（本地 <code>年-月-日 时:分:秒</code>）、任务耗时（时:分:秒）。切换上方日历时，下列区间会同步为当日；亦可自行改区间后点「按区间加载」。耗时存于数据库字段{' '}
            <code>duration_seconds</code>。
          </p>
          <div
            className="row"
            style={{ flexWrap: 'wrap', alignItems: 'center', gap: '0.65rem', marginBottom: '0.85rem' }}
          >
            <label className="muted" style={{ fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: 6 }}>
              业务日起
              <BizDatePickerField id="tasks-log-from" value={logRangeFrom} onChange={setLogRangeFrom} />
            </label>
            <label className="muted" style={{ fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: 6 }}>
              业务日止
              <BizDatePickerField id="tasks-log-to" value={logRangeTo} onChange={setLogRangeTo} />
            </label>
            <button type="button" className="btn btn-ghost" onClick={() => void loadTaskLog()}>
              按区间加载
            </button>
          </div>
        </>
      )}

      <div className="tasks-cal-wrap">
        <button
          type="button"
          className="tasks-cal-nav"
          aria-label="上一天"
          onClick={() => setBizDate(addLocalDays(bizDate, -1))}
        >
          ‹
        </button>
        <div className="tasks-cal-center">
          <div className="tasks-cal-oneline">
            {(() => {
              const d = new Date(`${bizDate}T12:00:00`);
              const y = d.getFullYear();
              const mo = d.getMonth() + 1;
              const dd = String(d.getDate()).padStart(2, '0');
              const wk = d.toLocaleDateString('zh-CN', { weekday: 'long' });
              return (
                <>
                  <span className="tasks-cal-ymd">{y}年{mo}月</span>
                  <span className="tasks-cal-bigday">{dd}</span>
                  <span className="tasks-cal-weekday">{wk}</span>
                  {tasksTab === 'recommended' && recommendedDayPlan && (
                    <span className="tasks-cal-badge">整日预览</span>
                  )}
                </>
              );
            })()}
          </div>
        </div>
        <button
          type="button"
          className="tasks-cal-nav"
          aria-label="下一天"
          onClick={() => setBizDate(addLocalDays(bizDate, 1))}
        >
          ›
        </button>
        <button type="button" className="btn btn-ghost tasks-cal-today" onClick={() => setBizDate(localBizDate())}>
          今天
        </button>
        <BizDatePickerField id="tasks-biz-date" value={bizDate} onChange={setBizDate} />
      </div>

      {tasksTab === 'backfill' && bfData && (
        <p className="muted" style={{ fontSize: '0.82rem' }}>
          活动源：{bfData.activityFeed.source} · 更新 {bfData.activityFeed.updatedAt}
        </p>
      )}

      {bfMsg && tasksTab === 'backfill' && <p style={{ color: 'var(--accent)' }}>{bfMsg}</p>}
      {tasksTab === 'log' && logData && !logData.items.length && !err && (
        <p className="muted">该业务日尚无任务记录。</p>
      )}
      {err && <p style={{ color: 'var(--danger)' }}>{err}</p>}

      {tasksTab === 'recommended' && pinnedSummary.length > 0 && (
        <div className="card" style={{ padding: '0.65rem 1rem', marginBottom: '0.75rem', borderColor: 'rgba(232,197,71,0.45)' }}>
          <strong style={{ color: 'var(--gold)' }}>即将开场（置顶）：</strong>
          <span className="muted">{pinnedSummary.join('、')}</span>
        </div>
      )}

      {tasksTab === 'recommended' && tasks.length === 0 && !err && (
        <p className="muted">当前没有待办推荐（可能都已做完、在冷却或限时活动已结束）。</p>
      )}

      {tasksTab === 'recommended' && displayTasks.length > 0 && (
        <div className="tasks-wukai-table-wrap">
          <table className="tasks-wukai-table">
            <thead>
              <tr>
                <th className="tasks-wukai-rank">#</th>
                <th className="tasks-wukai-stars">推荐星级</th>
                <th>任务</th>
                <th className="tasks-wukai-status">状态</th>
                <th className="tasks-wukai-slot">时段</th>
                <th className="tasks-wukai-kind">推荐</th>
                <th className="tasks-wukai-freq">频率</th>
                <th className="tasks-wukai-ghost">次数</th>
                <th className="tasks-wukai-actions"> </th>
              </tr>
            </thead>
            <tbody>
              {recPg.slice.map((t, idx) => (
                <tr
                  key={t.source === 'live' ? `live-${t.externalKey}` : `db-${t.id}`}
                  className={
                    t.recordedDoneToday || t.schedulePassed ? 'tasks-wukai-row-done' : undefined
                  }
                >
                  <td className="tasks-wukai-rank">{(recPg.page - 1) * recPg.pageSize + idx + 1}</td>
                  <td className="tasks-wukai-stars">
                    <StarRow n={t.stars ?? 3} />
                  </td>
                  <td className="tasks-wukai-task" title={t.description}>
                    <span className="tasks-wukai-name">{t.name}</span>
                    {/神器/.test(String(t.name || '')) ? (
                      artifactSelected.length === 2 ? (
                        /（\s*起\s*）/.test(String(t.name || '')) && artifactByPhase.qi ? (
                          <span className="tasks-wukai-subline">神器：{artifactByPhase.qi}</span>
                        ) : /（\s*转\s*）/.test(String(t.name || '')) && artifactByPhase.zhuan ? (
                          <span className="tasks-wukai-subline">神器：{artifactByPhase.zhuan}</span>
                        ) : (
                          <span className="tasks-wukai-subline">
                            神器：{artifactByPhase.qi || artifactSelected[0]}、{artifactByPhase.zhuan || artifactSelected[1]}
                          </span>
                        )
                      ) : (
                        <span className="tasks-wukai-subline">神器：未设置（去「神器攻略」粘贴截图）</span>
                      )
                    ) : null}
                  </td>
                  <td className="tasks-wukai-status">
                    {t.recordedDoneToday ? (
                      <span className="badge" style={{ borderColor: 'rgba(120,220,160,0.45)' }}>
                        已完成
                      </span>
                    ) : t.schedulePassed ? (
                      <span className="badge" style={{ opacity: 0.85, borderColor: 'rgba(255,120,120,0.45)' }}>
                        已结束
                      </span>
                    ) : t.scheduleOngoing ? (
                      <span className="badge badge-4d">进行中</span>
                    ) : t.scheduleJustEnded ? (
                      <span className="badge badge-4d">刚结束</span>
                    ) : t.schedulePinned || taskStickyPinned(t, stickyRemindedKeys) ? (
                      <span className="badge badge-4d">即将开始</span>
                    ) : t.scheduleLabel ? (
                      <span className="badge">限时</span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td className="tasks-wukai-slot">
                    {t.scheduleLabel ? <span className="badge">{t.scheduleLabel}</span> : <span className="muted">全天</span>}
                  </td>
                  <td className="tasks-wukai-kind">
                    <div className="tasks-wukai-kind-cell">
                      {t.source === 'db' && t.id != null && t.enabled !== false ? (
                        <div className="tasks-wukai-sort-arrows" aria-label="排序">
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => void moveTemplate(Number(t.id), -1)}
                            title="上移"
                          >
                            ↑
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => void moveTemplate(Number(t.id), 1)}
                            title="下移"
                          >
                            ↓
                          </button>
                        </div>
                      ) : null}
                      <span className="badge">
                        {t.recommendKind === 'weekly'
                          ? '周常推荐'
                          : t.recommendKind === 'daily'
                            ? '日常推荐'
                            : t.wukaiTail
                              ? '限时·低优'
                              : '限时'}
                      </span>
                    </div>
                  </td>
                  <td className="tasks-wukai-freq">
                    <span
                      className={`badge ${
                        t.frequency === 'daily'
                          ? 'badge-daily'
                          : t.frequency === 'weekly_once' || t.frequency === 'weekly_twice'
                            ? 'badge-daily'
                            : 'badge-4d'
                      }`}
                      style={t.inCooldown ? { opacity: 0.85 } : undefined}
                    >
                      {t.frequency === 'daily'
                        ? '日常'
                        : t.frequency === 'weekly_once'
                          ? '周常×1'
                          : t.frequency === 'weekly_twice'
                            ? '周常×2'
                            : t.frequency === 'four_day'
                              ? (() => {
                                  const nextMs = parseMs(t.nextRefreshAt);
                                  if (nextMs != null) return formatRefreshCountdown(nextMs - nowMs);
                                  return `${t.cooldownDays}天`;
                                })()
                              : `${t.cooldownDays}天`}
                    </span>
                  </td>
                  <td className="tasks-wukai-ghost">
                    <div className="tasks-wukai-times-cell">
                      {t.source === 'db' && t.id != null ? (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm tasks-wukai-disable-btn"
                          onClick={() => void toggleTemplateEnabled(Number(t.id), false)}
                          title="停用：从推荐榜移到补录页"
                        >
                          停用
                        </button>
                      ) : null}
                      {t.source === 'db' && Number(t.id) === 2 && t.weeklyCap != null && t.weeklyRemaining != null ? (
                        <span className="badge" style={{ opacity: 0.9 }}>
                          剩 {t.weeklyRemaining}/{t.weeklyCap}
                        </span>
                      ) : t.source === 'db' && t.capTimes != null && t.remainingTimes != null ? (
                        <span className="badge" style={{ opacity: 0.9 }}>
                          剩 {t.remainingTimes}/{t.capTimes}
                        </span>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </div>
                  </td>
                  <td className="tasks-wukai-actions">
                    {t.recordedDoneToday ? (
                      <button type="button" className="btn btn-ghost" disabled>
                        已完成
                      </button>
                    ) : (
                      <button type="button" className="btn btn-primary" onClick={() => void openComplete(t)}>
                        完成
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <TablePaginationBar
            page={recPg.page}
            totalPages={recPg.totalPages}
            total={recPg.total}
            pageSize={recPg.pageSize}
            onPageChange={recPg.setPage}
            onPageSizeChange={recPg.setPageSize}
          />
        </div>
      )}

      {tasksTab === 'backfill' && !bfData?.items.length && !err && (
        <p className="muted">当前业务日没有可补录项（可能都已记录）。</p>
      )}

      {tasksTab === 'backfill' && bfData?.items.length ? (
        <div className="tasks-bf-table-wrap">
          <table className="tasks-bf-table">
            <thead>
              <tr>
                <th className="tasks-bf-type">类型</th>
                <th className="tasks-bf-task">任务</th>
                <th className="tasks-bf-kind">分类</th>
                <th className="tasks-bf-status">状态</th>
                <th className="tasks-bf-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              {bfPg.slice.map((r) => (
                <tr key={`${r.source}-${r.id ?? r.externalKey}`}>
                  <td className="tasks-bf-type">
                    <span className="badge">{r.source === 'live' ? '限时活动' : '模板'}</span>
                  </td>
                  <td className="tasks-bf-task" title={r.description || r.name}>
                    <div className="tasks-bf-name">{r.name}</div>
                    {r.description ? <div className="tasks-bf-desc muted">{r.description}</div> : null}
                    {r.kind === 'waiting_update' && Number(r.id) === 2 && r.weeklyCap != null ? (
                      <div className="tasks-bf-desc muted" style={{ marginTop: 4 }}>
                        本周剩 0/{r.weeklyCap} 只（下周一重置后可回推荐榜）
                      </div>
                    ) : r.kind === 'waiting_update' && r.capTimes != null ? (
                      <div className="tasks-bf-desc muted" style={{ marginTop: 4 }}>
                        次数 剩 0/{r.capTimes}（周期刷新后可回推荐榜）
                      </div>
                    ) : null}
                  </td>
                  <td className="tasks-bf-kind">
                    <span className={r.kind === 'waiting_update' ? 'badge badge-4d' : 'badge badge-daily'}>
                      {backfillCandidateKindLabel(r.kind)}
                    </span>
                  </td>
                  <td className="tasks-bf-status">
                    {r.kind === 'waiting_update' ? (
                      <span className="badge" style={{ borderColor: 'rgba(232,197,71,0.45)' }}>
                        等待更新
                      </span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td className="tasks-bf-actions">
                    <div className="tasks-bf-actions-row">
                      {r.source === 'db' && r.id != null ? (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => void toggleTemplateEnabled(Number(r.id), true)}
                          title="启用：显示在推荐榜"
                        >
                          启用
                        </button>
                      ) : null}
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => openBackfillRow(r)}>
                        补录
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <TablePaginationBar
            page={bfPg.page}
            totalPages={bfPg.totalPages}
            total={bfPg.total}
            pageSize={bfPg.pageSize}
            onPageChange={bfPg.setPage}
            onPageSizeChange={bfPg.setPageSize}
          />
        </div>
      ) : null}

      {pick && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="card modal">
            <h2>记录完成：{pick.name}</h2>
            <p className="muted" style={{ fontSize: '0.88rem' }}>
              时间格式 <code style={{ fontSize: '0.8rem' }}>年-月-日 时:分:秒</code>
              （本地）。首次：开始不早于 <strong>当日 10:00</strong>；若记账台已开始计时，则与「开始计时」对应的累计起点取较晚者。之后：在「上一任务结束」与「记账台计时起点」中取较晚者。结束默认为当前时间。若清空开始时间，将按上述规则自动补全并写入数据库。
            </p>
            {completeModalErr ? (
              <p style={{ color: 'var(--danger)', margin: '0.5rem 0', fontSize: '0.88rem' }} role="alert">
                {completeModalErr}
              </p>
            ) : null}
            <label className="muted" style={{ fontSize: '0.82rem' }}>
              开始时间
            </label>
            <input
              className="input"
              type="text"
              autoComplete="off"
              placeholder="例如 2026-04-06 22:30:00"
              value={startedAt}
              disabled={completeSubmitting}
              onChange={(e) => setStartedAt(e.target.value)}
            />
            <label className="muted" style={{ fontSize: '0.82rem', marginTop: 8, display: 'block' }}>
              结束时间
            </label>
            <input
              className="input"
              type="text"
              autoComplete="off"
              placeholder="例如 2026-04-06 23:15:00"
              value={endedAt}
              disabled={completeSubmitting}
              onChange={(e) => setEndedAt(e.target.value)}
            />
            {pick.source === 'db' && Number(pick.id) === 2 && (
              <div style={{ marginTop: 12 }}>
                <label className="muted" style={{ fontSize: '0.82rem', display: 'block' }}>
                  本次抓鬼数量（只）
                </label>
                <div className="row" style={{ gap: 8, alignItems: 'center', marginTop: 6 }}>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={completeSubmitting}
                    onClick={() => setGhostUnitCount((v) => Math.max(10, v - 10))}
                  >
                    -10
                  </button>
                  <div style={{ minWidth: 72, textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                    <strong>{ghostUnitCount}</strong>
                  </div>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={completeSubmitting}
                    onClick={() => setGhostUnitCount((v) => Math.min(200, v + 10))}
                    aria-label="加 10 只"
                  >
                    +10
                  </button>
                  <span className="muted" style={{ fontSize: '0.82rem' }}>
                    本周剩余 {Math.max(0, (pick.weeklyRemaining ?? 200) - ghostUnitCount)} / 200
                  </span>
                </div>
              </div>
            )}
            <div className="row" style={{ marginTop: '1rem' }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={completeSubmitting}
                onClick={() => void confirmComplete()}
              >
                {completeSubmitting ? '提交中…' : '确认完成'}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={completeSubmitting}
                onClick={() => {
                  setPick(null);
                  setCompleteModalErr('');
                }}
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {tasksTab === 'log' && logData && logData.items.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                {logData.fromBizDate !== logData.toBizDate ? (
                  <th style={{ padding: '0.65rem 1rem' }}>业务日</th>
                ) : null}
                <th style={{ padding: '0.65rem 1rem' }}>任务</th>
                <th style={{ padding: '0.65rem 1rem' }}>开始时间</th>
                <th style={{ padding: '0.65rem 1rem' }}>结束时间</th>
                <th style={{ padding: '0.65rem 1rem' }}>任务耗时</th>
                <th style={{ padding: '0.65rem 1rem' }}>来源</th>
              </tr>
            </thead>
            <tbody>
              {logPg.slice.map((row) => (
                <tr key={row.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  {logData.fromBizDate !== logData.toBizDate ? (
                    <td style={{ padding: '0.55rem 1rem', fontVariantNumeric: 'tabular-nums' }}>
                      {formatTaskBizDateAsDateTime(row.bizDate ?? null)}
                    </td>
                  ) : null}
                  <td style={{ padding: '0.55rem 1rem', fontWeight: 600 }}>{row.title}</td>
                  <td style={{ padding: '0.55rem 1rem', fontVariantNumeric: 'tabular-nums' }}>{formatTaskLogDateTime(row.startedAt)}</td>
                  <td style={{ padding: '0.55rem 1rem', fontVariantNumeric: 'tabular-nums' }}>{formatTaskLogDateTime(row.endedAt)}</td>
                  <td style={{ padding: '0.55rem 1rem', fontVariantNumeric: 'tabular-nums' }}>
                    {formatDurationSec(taskRowDurationSeconds(row))}
                  </td>
                  <td style={{ padding: '0.55rem 1rem' }}>
                    <span className="badge">{sourceLabel(row.source)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '0 1rem 0.65rem' }}>
            <TablePaginationBar
              page={logPg.page}
              totalPages={logPg.totalPages}
              total={logPg.total}
              pageSize={logPg.pageSize}
              onPageChange={logPg.setPage}
              onPageSizeChange={logPg.setPageSize}
            />
          </div>
        </div>
      )}

      {bfPick && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="card modal">
            <h2>补录：{bfPick.name}</h2>
            <label className="muted" style={{ fontSize: '0.82rem' }}>
              开始时间
            </label>
            <input className="input" type="datetime-local" value={bfStartedAt} onChange={(e) => setBfStartedAt(e.target.value)} />
            <label className="muted" style={{ fontSize: '0.82rem', marginTop: 8, display: 'block' }}>
              结束时间
            </label>
            <input className="input" type="datetime-local" value={bfEndedAt} onChange={(e) => setBfEndedAt(e.target.value)} />
            <div className="row" style={{ marginTop: '1rem' }}>
              <button type="button" className="btn btn-primary" onClick={confirmBackfill}>
                确认写入
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setBfPick(null)}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
