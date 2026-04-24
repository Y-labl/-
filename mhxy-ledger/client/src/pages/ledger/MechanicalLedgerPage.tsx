import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { Link } from 'react-router-dom';
import { api, getToken } from '../../api';
import type {
  ItemCatalogAllResponse,
  MechLedgerDailyResponse,
  MechLedgerHistoryRow,
  MechLedgerPointCardSegments,
} from '../../api';
import {
  DAILY_FIXED_ITEMS,
  DAILY_VAR_ITEMS,
  YAKSHA_COUNTER_KEYS,
  YAKSHA_REWARD,
  YAKSHA_WHITE,
  type LedgerItemDef,
} from './ledgerData';
import {
  LEDGER_LEVEL_OPTIONS,
  LEDGER_LINGSHI_TYPES,
  buildLedgerPickedDisplayName,
  getLedgerPickKind,
  getLedgerPickLevelOptions,
} from './ledgerSpecialPick';
import {
  RUYI_ELEMENTS,
  buildRuyiDanDisplayName,
  getRuyiDanPrice,
  loadRuyiDanPrices,
  type RuyiElement,
} from './ruyiDanCatalog';
import {
  buildBeastScrollDisplayName,
  loadBeastScrollRows,
} from './beastScrollCatalog';
import { getLingshiBookPrice } from './lingshiBookCatalog';
import { getTieredLedgerUnitPrice } from './tieredItemCatalog';
import { LEDGER_ICON_POOL_SIZE } from './ledgerIcons';
import { LedgerItemIcon } from './LedgerItemIcon';
import {
  itemTooltip,
  itemTooltipWithFloat,
  catalogRowToLedgerItem,
  rollFloatingPriceW,
  floatingPriceRangeW,
} from './catalogRowUtils';
import { localBizDate, pointCardPointsToYuan } from '../../utils/bizDate';
import {
  BIZ_DATE_PAGE,
  getLedgerBizDate,
  isLedgerBizDateLocked,
  lockLedgerBizDate,
  unlockLedgerBizDateAndAdvanceToToday,
} from '../../utils/pageBizDate';
import { usePageBizDate } from '../../utils/usePageBizDate';
import { TablePaginationBar } from '../../components/TablePaginationBar';
import { formatWanZhCN } from '../../utils/formatWanZhCN';
import { useTablePagination } from '../../hooks/useTablePagination';
import {
  LEDGER_GAME_WAN_ANCHOR,
  loadGameYuanPair,
  roundLedgerYuan2,
  saveGameYuanPair,
  yuanPerWFromPair,
} from './ledgerYuanRatio';
import {
  extractItemsGreedyFromTranscript,
  findBestVoiceLedgerItem,
  getBrowserSpeechRecognitionConstructor,
  parseVoiceLedgerCommand,
  splitVoiceSegments,
  type SpeechRecognitionLike,
} from './ledgerVoice';
import './MechanicalLedgerPage.css';

type MainTab = 'daily' | 'yaksha' | 'scene';
type RightTab = 'today' | 'history';

type TodayLine = {
  id: string;
  name: string;
  valueW: number;
  count: number;
  /** 来自物品库点击添加时写入，改单价时优先按 id 同步 catalog_items */
  catalogItemId?: number;
};

/** LedgerItemDef.id 来自物品库时为 `c${catalog_items.id}` */
function catalogItemIdFromLedgerDefId(itemId: string): number | null {
  const m = /^c(\d+)$/.exec(itemId);
  if (!m) return null;
  const n = Number(m[1]);
  return Number.isFinite(n) && n > 0 ? n : null;
}

/** 今日行 id 添加时为 `c${catalogId}${Date.now()}`，用于无 catalogItemId 时的兜底解析 */
function parseCatalogItemIdFromTodayLineId(lineId: string): number | null {
  if (!lineId.startsWith('c')) return null;
  const tail = lineId.slice(1);
  if (tail.length <= 13) return null;
  const tsStr = tail.slice(-13);
  if (!/^\d{13}$/.test(tsStr)) return null;
  const idStr = tail.slice(0, -13);
  if (!idStr.length) return null;
  const n = Number(idStr);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function formatElapsed(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return `${h}小时${m}分${s}秒`;
}

function formatLocalHms(d: Date) {
  const h = d.getHours();
  const m = d.getMinutes();
  const s = d.getSeconds();
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatLocalYmd(d: Date) {
  const y = d.getFullYear();
  const m = d.getMonth() + 1;
  const day = d.getDate();
  return `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function ymdAddDays(ymd: string, deltaDays: number) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ymd)) return ymd;
  const [yy, mm, dd] = ymd.split('-').map((x) => Number(x));
  const dt = new Date(yy, mm - 1, dd);
  dt.setDate(dt.getDate() + deltaDays);
  return formatLocalYmd(dt);
}

function isInLateNightBizDatePickWindow(d: Date) {
  const sec = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds();
  // 23:59:59 ~ 06:00:00（含端点）
  return sec >= 23 * 3600 + 59 * 60 + 59 || sec <= 6 * 3600;
}

function initYakshaCounts(): Record<string, number> {
  const o: Record<string, number> = {};
  for (const { key } of YAKSHA_COUNTER_KEYS) o[key] = 0;
  o.total = 0;
  o.turtle = 0;
  o.drop = 0;
  return o;
}

const TEAM_PRINCIPAL_SLOT_COUNT = 4;
const TEAM_PRINCIPAL_CN = ['一', '二', '三', '四'] as const;

function emptyTeamPrincipalStrs(): [string, string, string, string] {
  return ['', '', '', ''];
}

/** 库内「万」转「两」展示时，若单格数值极大则视为历史误存（按两原样显示） */
const TEAM_MONEY_LIANG_THRESHOLD = 1_000_000;

/** 点「清除计时」后：该业务日再进入记账台不应用 /daily 回填，直至用户录入物品或现金/本金（两） */
const MECH_LEDGER_SKIP_HYDRATE_BIZ_KEY = 'mhxy_mech_ledger_skip_hydrate_biz';

function readSkipHydrateBizFromSession(): string {
  try {
    const s = sessionStorage.getItem(MECH_LEDGER_SKIP_HYDRATE_BIZ_KEY);
    if (!s || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return '';
    return s;
  } catch {
    return '';
  }
}

function shouldSkipHydrateFromServer(biz: string): boolean {
  const hold = readSkipHydrateBizFromSession();
  return Boolean(hold && hold === biz);
}

function clearLedgerSkipHydrateBizFromSession(): void {
  try {
    sessionStorage.removeItem(MECH_LEDGER_SKIP_HYDRATE_BIZ_KEY);
  } catch {
    /* ignore */
  }
}

/** 库内「万」→ 输入框「两」（×10000）；若单格极大则视为历史误存按两原样显示 */
function teamWanNumsToInputStrs(nums: number[] | undefined | null): [string, string, string, string] {
  const o = emptyTeamPrincipalStrs();
  if (!nums?.length) return o;
  const active = nums
    .slice(0, TEAM_PRINCIPAL_SLOT_COUNT)
    .map((x) => Number(x))
    .filter((n) => Number.isFinite(n) && n > 0);
  const legacyLiangStored = active.some((n) => n >= TEAM_MONEY_LIANG_THRESHOLD);
  for (let i = 0; i < Math.min(TEAM_PRINCIPAL_SLOT_COUNT, nums.length); i++) {
    const n = Number(nums[i]);
    if (!Number.isFinite(n) || n <= 0) continue;
    o[i] = legacyLiangStored ? String(Math.round(n)) : String(Math.round(n * 10000));
  }
  return o;
}

/** 在线人数：常用档位 + 临时加减（点卡按 常用 + 临时 合计） */
const ONLINE_COUNT_PRESETS = [5, 10, 15, 20] as const;
type OnlinePreset = (typeof ONLINE_COUNT_PRESETS)[number];

/** 每帧末尾与 save-meta 对齐；flushSync 后立即 build 时读此快照，避免分散 ref 尚未与本帧 state 同步的窗口 */
type MechLedgerHudMetaSnapshotForSave = {
  onlinePreset: OnlinePreset;
  onlineExtra: number;
  teamPrincipalWanStrs: [string, string, string, string];
  teamCashWanStrs: [string, string, string, string];
  pointCardPoints: number;
  elapsedSec: number;
  baseElapsedSec: number;
  runStartAt: number | null;
  pointCardSeg: MechLedgerPointCardSegments;
};

/** 新建会话的默认常用人数 */
const DEFAULT_ONLINE_PRESET: OnlinePreset = 5;

/** 与 save-meta / 服务端 teamSlots 一致：常用档与合计在线人数取较大队数（每 5 人一队，上限 4） */
function mechTeamSlotCount(preset: number, onlineEffective: number): number {
  const slotsFromPreset = Math.max(1, Math.floor(preset / 5));
  const slotsFromCount = Math.max(1, Math.min(4, Math.floor(onlineEffective / 5)));
  return Math.min(4, Math.max(slotsFromPreset, slotsFromCount));
}

/** 有录入的本金/现金所占行数，避免库内两队数据但常用 5 人时只显示一队 */
function principalCashInputSpan(
  tp: readonly [string, string, string, string],
  tc: readonly [string, string, string, string],
): number {
  let n = 0;
  for (let i = 0; i < TEAM_PRINCIPAL_SLOT_COUNT; i++) {
    const a = String(tp[i] ?? '').trim();
    const b = String(tc[i] ?? '').trim();
    if (a !== '' || b !== '') n = i + 1;
  }
  return n;
}

/** meta.online_roles（合计人数）→ 常用档位 + 临时加人 */
function splitOnlinePresetExtra(roles: number): { preset: OnlinePreset; extra: number } {
  const R = Math.max(0, Math.floor(Number(roles) || 0));
  if (R <= 0) return { preset: DEFAULT_ONLINE_PRESET, extra: 0 };
  if ((ONLINE_COUNT_PRESETS as readonly number[]).includes(R)) {
    return { preset: R as OnlinePreset, extra: 0 };
  }
  let preset: OnlinePreset = DEFAULT_ONLINE_PRESET;
  for (const p of ONLINE_COUNT_PRESETS) {
    if (p <= R) preset = p as OnlinePreset;
  }
  return { preset, extra: Math.max(0, R - preset) };
}

/** 从 daily 恢复点卡分段；无 JSON 时用 fallbackSegmentStart（常为当前计时底数 b） */
function pointCardSegFromDaily(
  raw: MechLedgerPointCardSegments | null | undefined,
  fallbackSegmentStart: number,
): MechLedgerPointCardSegments {
  if (raw == null || typeof raw !== 'object') {
    return { closedSlices: [], segmentStartElapsed: fallbackSegmentStart };
  }
  const closedSlices = Array.isArray(raw.closedSlices)
    ? raw.closedSlices.map((x) => ({
        durationSec: Math.max(0, Math.floor(Number(x.durationSec) || 0)),
        roles: Math.max(0, Math.floor(Number(x.roles) || 0)),
      }))
    : [];
  const segmentStartElapsed = Math.max(0, Math.floor(Number(raw.segmentStartElapsed) || 0));
  return { closedSlices, segmentStartElapsed };
}

function lineKey(l: Pick<TodayLine, 'name' | 'valueW'>) {
  return `${l.name}\t${l.valueW}`;
}

/** 服务端行与当前界面合并：同名称+单价取较大数量；展示顺序为「最近操作的在前」 */
function mergeTodayLinesFromServer(
  biz: string,
  serverRows: { name: string; valueW: number; count: number }[],
  prev: TodayLine[]
): TodayLine[] {
  const serverMap = new Map<string, TodayLine>();
  for (let i = 0; i < serverRows.length; i++) {
    const l = serverRows[i];
    const row: TodayLine = {
      id: `srv:${biz}:${i}`,
      name: l.name,
      valueW: Number(l.valueW),
      count: Math.max(1, Math.floor(Number(l.count) || 1)),
    };
    serverMap.set(lineKey(row), row);
  }
  const seen = new Set<string>();
  const front: TodayLine[] = [];
  for (const l of prev) {
    const k = lineKey(l);
    const ex = serverMap.get(k);
    if (ex) {
      front.push({ ...ex, count: Math.max(ex.count, l.count) });
      seen.add(k);
    } else {
      front.push(l);
    }
  }
  const rest: TodayLine[] = [];
  for (let i = serverRows.length - 1; i >= 0; i--) {
    const l = serverRows[i];
    const row: TodayLine = {
      id: `srv:${biz}:${i}`,
      name: l.name,
      valueW: Number(l.valueW),
      count: Math.max(1, Math.floor(Number(l.count) || 1)),
    };
    const k = lineKey(row);
    if (!seen.has(k)) rest.push(row);
  }
  return [...front, ...rest];
}

export default function MechanicalLedgerPage() {
  const [bizDate] = usePageBizDate(BIZ_DATE_PAGE.ledger);
  const [mainTab, setMainTab] = useState<MainTab>('daily');
  const [rightTab, setRightTab] = useState<RightTab>('today');
  const [onlinePreset, setOnlinePreset] = useState<OnlinePreset>(DEFAULT_ONLINE_PRESET);
  const [onlineExtra, setOnlineExtra] = useState(0);
  const onlineEffective = onlinePreset + onlineExtra;
  const [pointCardSeg, setPointCardSeg] = useState<MechLedgerPointCardSegments>({
    closedSlices: [],
    segmentStartElapsed: 0,
  });
  /** 已写入 meta 的点卡累计（点），与当前会话分段相加；随每日加载 / 「清除计时」重置。「保存收益」打正式快照、不改此页实时点卡累计 */
  const [pointCardBaseline, setPointCardBaseline] = useState(0);
  const [teamPrincipalWanStrs, setTeamPrincipalWanStrs] = useState<
    [string, string, string, string]
  >(() => emptyTeamPrincipalStrs());
  const [baseElapsedSec, setBaseElapsedSec] = useState(0);
  const [runStartAt, setRunStartAt] = useState<number | null>(null);
  const [timerTick, setTimerTick] = useState(0);
  /** 标题「业务日期」旁本地时分秒，每秒刷新 */
  const [, setHeaderClockTick] = useState(0);
  const [saveBizDatePick, setSaveBizDatePick] = useState<null | {
    today: string;
    yesterday: string;
  }>(null);
  const saveBizDatePickCbRef = useRef<null | ((pickedBizDate: string) => void)>(null);
  const [fixedPrice, setFixedPrice] = useState(true);
  const [exactPrice, setExactPrice] = useState(false);
  const [gameYuan, setGameYuan] = useState(() => loadGameYuanPair());
  const [yuanInputStr, setYuanInputStr] = useState(() =>
    roundLedgerYuan2(loadGameYuanPair().yuan).toFixed(2),
  );
  const yuanPerWanW = useMemo(() => yuanPerWFromPair(gameYuan), [gameYuan]);
  const [todayLines, setTodayLines] = useState<TodayLine[]>([]);
  /** 各队现金梦幻币（界面按「两」录入）；落库为万（÷10000） */
  const [teamCashWanStrs, setTeamCashWanStrs] = useState<[string, string, string, string]>(() =>
    emptyTeamPrincipalStrs(),
  );
  const teamSlotCount = useMemo(
    () =>
      Math.min(
        TEAM_PRINCIPAL_SLOT_COUNT,
        Math.max(
          1,
          mechTeamSlotCount(onlinePreset, onlineEffective),
          principalCashInputSpan(teamPrincipalWanStrs, teamCashWanStrs),
        ),
      ),
    [onlinePreset, onlineEffective, teamPrincipalWanStrs, teamCashWanStrs],
  );
  const teamPrincipalsParsedW = useMemo(() => {
    const out: number[] = [];
    for (let i = 0; i < teamSlotCount; i++) {
      const n = Number(teamPrincipalWanStrs[i]);
      out.push(Number.isFinite(n) && n >= 0 ? n : 0);
    }
    return out;
  }, [teamPrincipalWanStrs, teamSlotCount]);
  const principalsSumW = useMemo(
    () => teamPrincipalsParsedW.reduce((a, b) => a + b, 0),
    [teamPrincipalsParsedW],
  );
  /** 供离页 flush 使用，避免防抖未跑完时库内仍是旧值 */
  const onlinePresetRef = useRef<OnlinePreset>(DEFAULT_ONLINE_PRESET);
  const onlineExtraRef = useRef(0);
  const teamPrincipalWanStrsRef = useRef<[string, string, string, string]>(emptyTeamPrincipalStrs());
  const teamCashWanStrsRef = useRef<[string, string, string, string]>(emptyTeamPrincipalStrs());
  const pointCardPointsRef = useRef(0);
  const baseElapsedSecRef = useRef(0);
  const runStartAtRef = useRef<number | null>(null);
  const pointCardSegRef = useRef<MechLedgerPointCardSegments>({
    closedSlices: [],
    segmentStartElapsed: 0,
  });
  const hudSnapshotForSaveRef = useRef<MechLedgerHudMetaSnapshotForSave | null>(null);
  const flushPendingMetaSaveRef = useRef<
    (biz: string, opts?: { keepalive?: boolean; force?: boolean; toastOnError?: boolean }) => void
  >(() => {});
  const teamCashParsedW = useMemo(() => {
    const out: number[] = [];
    for (let i = 0; i < teamSlotCount; i++) {
      const n = Number(teamCashWanStrs[i]);
      out.push(Number.isFinite(n) && n >= 0 ? n : 0);
    }
    return out;
  }, [teamCashWanStrs, teamSlotCount]);
  const cashGrossWPreview = useMemo(
    () => teamCashParsedW.reduce((a, b) => a + b, 0),
    [teamCashParsedW],
  );
  /** 净现金 = Σ(队伍现金−队伍本金)；输入均为「两」；若队伍现金为 0 则不计入（视为未填/不参与） */
  const netCashPreviewW = useMemo(() => {
    let net = 0;
    for (let i = 0; i < teamSlotCount; i++) {
      const cash = teamCashParsedW[i] ?? 0;
      if (cash === 0) continue;
      net += cash - (teamPrincipalsParsedW[i] ?? 0);
    }
    return net;
  }, [teamCashParsedW, teamPrincipalsParsedW, teamSlotCount]);
  /** 库内/总览用「万」展示 */
  const netCashPreviewWan = useMemo(() => netCashPreviewW / 10000, [netCashPreviewW]);
  const cashGrossWPreviewWan = useMemo(() => cashGrossWPreview / 10000, [cashGrossWPreview]);
  const principalsSumWWan = useMemo(() => principalsSumW / 10000, [principalsSumW]);
  const [yaksha, setYaksha] = useState(initYakshaCounts);
  const [toast, setToast] = useState<string | null>(null);
  const [historyRows, setHistoryRows] = useState<MechLedgerHistoryRow[]>([]);
  const [historyErr, setHistoryErr] = useState('');
  const [historyLoading, setHistoryLoading] = useState(false);
  const [priceEditStrsByLineId, setPriceEditStrsByLineId] = useState<Record<string, string>>({});
  const [removeLineTarget, setRemoveLineTarget] = useState<TodayLine | null>(null);
  const [removeQtyStr, setRemoveQtyStr] = useState('1');
  const [saveProfitConfirmOpen, setSaveProfitConfirmOpen] = useState(false);
  const [clearTimerConfirmOpen, setClearTimerConfirmOpen] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceLiveText, setVoiceLiveText] = useState('');
  const [speechMode, setSpeechMode] = useState<'browser' | 'server'>('browser');
  const [serverSpeechAvailable, setServerSpeechAvailable] = useState(false);
  const voiceRecRef = useRef<SpeechRecognitionLike | null>(null);
  const voiceLiveTextRef = useRef('');
  const voiceShouldRunRef = useRef(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaChunksRef = useRef<BlobPart[]>([]);
  const [catalog, setCatalog] = useState<ItemCatalogAllResponse | null>(null);
  /** 仅在为 true 时使用内置 ledgerData；成功拉取 API 后即使各分区为空也不再回退到占位「材料 N」 */
  const [catalogErr, setCatalogErr] = useState(false);

  const [pickModal, setPickModal] = useState<{
    item: LedgerItemDef;
    valueW: number;
    kind: 'level' | 'book' | 'beast' | 'ruyi';
  } | null>(null);
  const [pickLevel, setPickLevel] = useState('120');
  const [pickBookType, setPickBookType] = useState<string>(LEDGER_LINGSHI_TYPES[0]);
  const [pickBeastId, setPickBeastId] = useState('');
  const [pickRuyiElement, setPickRuyiElement] = useState<RuyiElement>(RUYI_ELEMENTS[0]);

  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleSyncTodayLines = useCallback((lines: TodayLine[]) => {
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    syncTimerRef.current = setTimeout(() => {
      syncTimerRef.current = null;
      const payload = lines.map((l) => ({ name: l.name, valueW: l.valueW, count: l.count }));
      api.mechLedgerPutTodayLines({ bizDate: getLedgerBizDate(), lines: payload }).catch(() => {
        setToast('物品列表同步失败，请检查网络或是否已登录');
        window.setTimeout(() => setToast(null), 2800);
      });
    }, 120);
  }, [bizDate]);

  const flushSyncTodayLines = useCallback(async (lines: TodayLine[]) => {
    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    const payload = lines.map((l) => ({ name: l.name, valueW: l.valueW, count: l.count }));
    await api.mechLedgerPutTodayLines({ bizDate: getLedgerBizDate(), lines: payload });
  }, [bizDate]);

  const todayLinesRef = useRef<TodayLine[]>([]);
  todayLinesRef.current = todayLines;
  /** 上一次已加载记账明细的业务日；变化时应用服务端行，避免换日后仍合并进上一日的本地行 */
  const lastLoadedBizDateRef = useRef<string | null>(null);
  /** 当前 biz 的 HUD 是否已从 /daily 应用；未就绪前禁止自动 save-meta，避免用初始空状态覆盖库里已有数据 */
  const hudHydratedForBizRef = useRef<string | null>(null);
  /** 回填后的短时间内禁止对「当前 biz」的自动 save-meta（schedule/非 keepalive flush），避免 ref 尚未与 state 同步时写库成空 */
  const suppressAutoMetaSaveBizRef = useRef<string | null>(null);
  const suppressAutoMetaSaveUntilRef = useRef(0);
  /**
   * 为 false 时，HUD/计时的「依赖项 effect」不写库。避免：改成 10 的请求还在飞 → 刷新 → 新页用刚拉到的 5 再 save-meta，把库里的 10 盖回 5。
   * 用户操作人数/本金/现金/计时后再置 true；显式 flush（确认档位、±人、离页）不读此开关。
   */
  const hudMetaEffectSaveEnabledRef = useRef(false);

  useEffect(() => {
    const syncGold = () => {
      const p = loadGameYuanPair();
      setGameYuan(p);
      setYuanInputStr(roundLedgerYuan2(p.yuan).toFixed(2));
    };
    window.addEventListener('mhxy-ledger-yuan-ratio', syncGold);
    const onVis = () => {
      if (document.visibilityState === 'visible') syncGold();
    };
    document.addEventListener('visibilitychange', onVis);
    return () => {
      window.removeEventListener('mhxy-ledger-yuan-ratio', syncGold);
      document.removeEventListener('visibilitychange', onVis);
    };
  }, []);

  /** 尚有防抖未发出时立即写入，避免切页丢数据 */
  const flushPendingSync = useCallback(() => {
    if (syncTimerRef.current === null) return;
    clearTimeout(syncTimerRef.current);
    syncTimerRef.current = null;
    const lines = todayLinesRef.current;
    const payload = lines.map((l) => ({ name: l.name, valueW: l.valueW, count: l.count }));
    void api.mechLedgerPutTodayLines({ bizDate: getLedgerBizDate(), lines: payload }).catch(() => {});
  }, [bizDate]);

  /** 业务日切换时先把上一日的物品行写入 agg（须早于下方拉取新日，且仅用 ref 避免 Strict Mode cleanup 误写库） */
  const prevBizNavRef = useRef<string | null>(null);
  useEffect(() => {
    const cur = getLedgerBizDate();
    const prev = prevBizNavRef.current;
    prevBizNavRef.current = cur;
    if (prev == null || prev === cur) return;
    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    const lines = todayLinesRef.current;
    const payload = lines.map((l) => ({ name: l.name, valueW: l.valueW, count: l.count }));
    void api.mechLedgerPutTodayLines({ bizDate: prev, lines: payload }).catch(() => {});
    flushPendingMetaSaveRef.current(prev, { force: true });
    // 未锁定时全站业务日可能自动从「昨天」跳到「今天」，物品已写入 prev；不提示易被误认为丢失
    if (prev < cur && payload.length > 0) {
      setToast(
        `业务日已从 ${prev} 变为 ${cur}：${payload.length} 条物品已写入 ${prev}。要看这些内容请在上方日期选回 ${prev}。`,
      );
      window.setTimeout(() => setToast(null), 5200);
    }
  }, [bizDate]);

  /**
   * 当日物品行 + HUD：仅从 /daily（库）恢复；换机/换浏览器同一账号以数据库为准。
   * 若本机曾对该业务日点「清除计时」，则同业务日再进页不应用 /daily 回填，直至用户录入物品或现金/本金。
   * ledger_run_start_at_ms 非空 = 上次落库时计时未停（未点停表），刷新后按同一墙钟起点继续计时；为空则停表，仅显示底数（停表后可用 elapsed_sec 兜底总秒数）。
   */
  useEffect(() => {
    let cancelled = false;
    const biz = getLedgerBizDate();
    hudHydratedForBizRef.current = null;
    hudMetaEffectSaveEnabledRef.current = false;
    const prevBiz = lastLoadedBizDateRef.current;
    const bizKeyChanged = prevBiz !== biz;
    lastLoadedBizDateRef.current = biz;
    (async () => {
      try {
        const skipFromServer = shouldSkipHydrateFromServer(biz);
        if (skipFromServer) {
          if (cancelled) return;
          setOnlinePreset(DEFAULT_ONLINE_PRESET);
          setOnlineExtra(0);
          setBaseElapsedSec(0);
          setRunStartAt(null);
          setPointCardSeg({ closedSlices: [], segmentStartElapsed: 0 });
          setPointCardBaseline(0);
          setTodayLines([]);
          setTeamPrincipalWanStrs(emptyTeamPrincipalStrs());
          setTeamCashWanStrs(emptyTeamPrincipalStrs());
          if (!cancelled) {
            hudHydratedForBizRef.current = biz;
            suppressAutoMetaSaveBizRef.current = biz;
            suppressAutoMetaSaveUntilRef.current = Date.now() + 900;
          }
        } else {
        let day: MechLedgerDailyResponse | null = null;
        try {
          day = await api.mechLedgerDaily(biz);
        } catch {
          day = null;
        }
        if (cancelled) return;
        const rows = day?.lines || [];
        const hasSavedDayMeta = Boolean(day?.pointCardSavedAt);
        const baselinePts = Number.isFinite(Number(day?.pointCardPoints)) ? Number(day?.pointCardPoints) : 0;
        const teamFromMeta = teamWanNumsToInputStrs(day?.teamPrincipalsW);
        const hasPerTeamCash =
          day?.teamCashGameGoldW != null &&
          Array.isArray(day.teamCashGameGoldW) &&
          day.teamCashGameGoldW.length > 0;
        const cashFromMeta =
          hasPerTeamCash && day ? teamWanNumsToInputStrs(day.teamCashGameGoldW) : null;
        const legacyCashStrs = emptyTeamPrincipalStrs();
        if (!hasPerTeamCash && day) {
          const cg = Number(day.cashGameGoldW ?? 0);
          if (Number.isFinite(cg) && cg > 0) {
            legacyCashStrs[0] =
              cg >= TEAM_MONEY_LIANG_THRESHOLD
                ? String(Math.round(cg))
                : String(Math.round(cg * 10000));
          }
        }
        const cashInit = hasPerTeamCash && cashFromMeta ? cashFromMeta : legacyCashStrs;
        const splitRoles = splitOnlinePresetExtra(day?.onlineRoles ?? 0);
        let op = splitRoles.preset;
        let oe = splitRoles.extra;
        let b = Math.max(0, Math.floor(Number(day?.ledgerBaseElapsedSec) || 0));
        let r =
          day?.ledgerRunStartAtMs != null && Number.isFinite(Number(day.ledgerRunStartAtMs))
            ? Number(day.ledgerRunStartAtMs)
            : null;
        if (r == null && day?.elapsedSec != null) {
          const es = Math.floor(Number(day.elapsedSec));
          if (Number.isFinite(es) && es > b) b = es;
        }
        let teamP = teamFromMeta;
        let teamC = cashInit;
        let baselinePtsState = 0;
        let pcSeg: MechLedgerPointCardSegments;
        if (hasSavedDayMeta) {
          baselinePtsState = baselinePts;
          pcSeg = pointCardSegFromDaily(day?.ledgerPointCard, b);
        } else if (day?.ledgerPointCard) {
          baselinePtsState = 0;
          pcSeg = pointCardSegFromDaily(day.ledgerPointCard, 0);
        } else {
          baselinePtsState = 0;
          pcSeg = { closedSlices: [], segmentStartElapsed: 0 };
        }

        setOnlinePreset(op);
        setOnlineExtra(oe);
        setBaseElapsedSec(b);
        setRunStartAt(r);
        if (r != null) lockLedgerBizDate(biz);
        setTodayLines((prev) => {
          const rowsNewestFirst = (): TodayLine[] => {
            const out: TodayLine[] = [];
            for (let i = rows.length - 1; i >= 0; i--) {
              const l = rows[i];
              out.push({
                id: `srv:${biz}:${i}`,
                name: l.name,
                valueW: Number(l.valueW),
                count: Math.max(1, Math.floor(Number(l.count) || 1)),
              });
            }
            return out;
          };
          if (bizKeyChanged) {
            return rowsNewestFirst();
          }
          if (prev.length === 0) {
            return rowsNewestFirst();
          }
          return mergeTodayLinesFromServer(biz, rows, prev);
        });
        setPointCardBaseline(baselinePtsState);
        setPointCardSeg(pcSeg);
        setTeamPrincipalWanStrs(teamP);
        setTeamCashWanStrs(teamC);
        if (!cancelled) {
          hudHydratedForBizRef.current = biz;
          suppressAutoMetaSaveBizRef.current = biz;
          suppressAutoMetaSaveUntilRef.current = Date.now() + 900;
        }
        }
      } catch {
        /* 未登录或表未建 */
      } finally {
        if (!cancelled) {
          window.setTimeout(() => setSessionReady(true), 0);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [bizDate]);

  useEffect(() => {
    const load = () => {
      api
        .itemCatalogAll()
        .then((r) => {
          setCatalog(r);
          setCatalogErr(false);
        })
        .catch(() => {
          setCatalog(null);
          setCatalogErr(true);
        });
    };
    load();
    const onVis = () => {
      if (document.visibilityState === 'visible') load();
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  const catalogFromApi = Boolean(catalog && !catalogErr);

  const totalCatalogRows = useMemo(() => {
    if (!catalog) return 0;
    return Object.values(catalog.panels).reduce((s, p) => s + (Array.isArray(p) ? p.length : 0), 0);
  }, [catalog]);

  /** 已成功从数据库加载物品库（含空库）；用于文案，不再依赖「是否有行」 */
  const usingDb = catalogFromApi;

  const fixedItems = useMemo(() => {
    if (catalogFromApi && catalog) {
      return (catalog.panels.fixed ?? []).map((r, i) => catalogRowToLedgerItem(r, i));
    }
    if (catalogErr) {
      return DAILY_FIXED_ITEMS;
    }
    return [];
  }, [catalog, catalogErr, catalogFromApi]);

  const varItems = useMemo(() => {
    if (catalogFromApi && catalog) {
      return (catalog.panels.var ?? []).map((r, i) => catalogRowToLedgerItem(r, i));
    }
    if (catalogErr) {
      return DAILY_VAR_ITEMS;
    }
    return [];
  }, [catalog, catalogErr, catalogFromApi]);

  const yakWhiteItems = useMemo(() => {
    if (catalogFromApi && catalog) {
      return (catalog.panels.yaksha_white ?? []).map((r, i) => catalogRowToLedgerItem(r, i));
    }
    if (catalogErr) {
      return YAKSHA_WHITE;
    }
    return [];
  }, [catalog, catalogErr, catalogFromApi]);

  const yakRewardItems = useMemo(() => {
    if (catalogFromApi && catalog) {
      return (catalog.panels.yaksha_reward ?? []).map((r, i) => catalogRowToLedgerItem(r, i));
    }
    if (catalogErr) {
      return YAKSHA_REWARD;
    }
    return [];
  }, [catalog, catalogErr, catalogFromApi]);

  const sceneItems = useMemo(() => {
    if (catalogFromApi && catalog) {
      return (catalog.panels.scene ?? []).map((r, i) => catalogRowToLedgerItem(r, i));
    }
    if (catalogErr) {
      return Array.from({ length: 24 }, (_, i) => ({
        id: `sc${i}`,
        iconIndex: i % LEDGER_ICON_POOL_SIZE,
        iconFile: `sheet-var-${String((i % 16) + 1).padStart(2, '0')}.png`,
        emoji: '🗡️',
        name: `场景掉落 ${i + 1}`,
        valueW: 5 + (i % 8) * 3,
      })) as LedgerItemDef[];
    }
    return [];
  }, [catalog, catalogErr, catalogFromApi]);

  /** 语音匹配用：合并各页格子，同名保留先出现的定义 */
  const voiceCatalogItems = useMemo(() => {
    const all = [...fixedItems, ...varItems, ...yakWhiteItems, ...yakRewardItems, ...sceneItems];
    const seen = new Set<string>();
    const out: LedgerItemDef[] = [];
    for (const it of all) {
      if (seen.has(it.name)) continue;
      seen.add(it.name);
      out.push(it);
    }
    return out;
  }, [fixedItems, varItems, yakWhiteItems, yakRewardItems, sceneItems]);

  const voiceRecognitionSupported = useMemo(
    () => typeof window !== 'undefined' && !!getBrowserSpeechRecognitionConstructor(),
    [],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { enabled } = await api.mechLedgerSpeechTranscribeConfig();
        if (!cancelled) setServerSpeechAvailable(!!enabled);
      } catch {
        if (!cancelled) setServerSpeechAvailable(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const voiceButtonDisabled = useMemo(() => {
    if (speechMode === 'server') return !serverSpeechAvailable;
    return !voiceRecognitionSupported;
  }, [speechMode, serverSpeechAvailable, voiceRecognitionSupported]);

  const isTimerRunning = runStartAt != null;

  const elapsedSec = useMemo(() => {
    return (
      baseElapsedSec +
      (runStartAt != null ? Math.floor((Date.now() - runStartAt) / 1000) : 0)
    );
  }, [baseElapsedSec, runStartAt, timerTick]);

  const elapsedSecRef = useRef(elapsedSec);
  elapsedSecRef.current = elapsedSec;
  const onlineEffectiveRef = useRef(onlineEffective);
  onlineEffectiveRef.current = onlineEffective;

  useEffect(() => {
    if (!isTimerRunning) return;
    const id = window.setInterval(() => setTimerTick((x) => x + 1), 1000);
    return () => window.clearInterval(id);
  }, [isTimerRunning]);

  useEffect(() => {
    const id = window.setInterval(() => setHeaderClockTick((n) => n + 1), 1000);
    return () => window.clearInterval(id);
  }, []);

  function toggleLedgerTimer() {
    hudMetaEffectSaveEnabledRef.current = true;
    if (runStartAt != null) {
      const add = Math.floor((Date.now() - runStartAt) / 1000);
      setBaseElapsedSec((b) => b + add);
      setRunStartAt(null);
    } else {
      const now = Date.now();
      // 锁定全项目业务日：跨过 23:59:59 也不自动跳天，直到保存/清除后再推进。
      lockLedgerBizDate(getLedgerBizDate());
      setRunStartAt(now);
    }
    // 启停后由下方「计时」effect 落库（此时 ref 已与 state 对齐）
  }

  /** 结束当前点卡计费区间并开始新区间（新区间从「此刻」计时，人数为即将生效的 onlineEffective） */
  const closeOpenPointCardSegment = useCallback((rolesForClosingSlice: number) => {
    const el = elapsedSecRef.current;
    setPointCardSeg((pc) => {
      const dur = Math.max(0, el - pc.segmentStartElapsed);
      const closedSlices =
        dur > 0 && rolesForClosingSlice >= 0
          ? [...pc.closedSlices, { durationSec: dur, roles: rolesForClosingSlice }]
          : pc.closedSlices;
      return { closedSlices, segmentStartElapsed: el };
    });
  }, []);

  /** 与 flushPendingMetaSave 同源；人数档位等关键操作须 await 直写库，不能只排队（否则刷新早于队列执行会丢 5→10） */
  const buildMechLedgerMetaPayload = useCallback((biz: string) => {
    const h = hudSnapshotForSaveRef.current;
    const op = h?.onlinePreset ?? onlinePresetRef.current;
    const oe = h?.onlineExtra ?? onlineExtraRef.current;
    const onlineEff = op + oe;
    const slots = mechTeamSlotCount(op, onlineEff);
    const tp = h?.teamPrincipalWanStrs ?? teamPrincipalWanStrsRef.current;
    const tc = h?.teamCashWanStrs ?? teamCashWanStrsRef.current;
    const principalSend = Array.from({ length: slots }, (_, i) => (Number(tp[i]) || 0) / 10000);
    const cashSend = Array.from({ length: slots }, (_, i) => (Number(tc[i]) || 0) / 10000);
    const pointForPayload = h?.pointCardPoints ?? pointCardPointsRef.current;
    const elapsedForPayload = Math.max(
      0,
      Math.floor(h != null ? h.elapsedSec : elapsedSecRef.current),
    );
    const baseB = h?.baseElapsedSec ?? baseElapsedSecRef.current;
    const runR = h?.runStartAt !== undefined ? h.runStartAt : runStartAtRef.current;
    const pcSeg = h?.pointCardSeg ?? pointCardSegRef.current;
    return {
      bizDate: biz,
      onlineCount: op + oe,
      onlinePreset: op,
      pointCardPoints: pointForPayload,
      elapsedSec: elapsedForPayload,
      teamCashGameGoldW: cashSend,
      teamPrincipalsW: principalSend,
      ledgerBaseElapsedSec: baseB,
      ledgerRunStartAtMs: runR,
      ledgerPointCard: pcSeg,
    };
  }, []);

  useEffect(() => {
    if (!removeLineTarget) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setRemoveLineTarget(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [removeLineTarget]);

  useEffect(() => {
    if (!clearTimerConfirmOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setClearTimerConfirmOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [clearTimerConfirmOpen]);

  useEffect(() => {
    if (!saveProfitConfirmOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSaveProfitConfirmOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [saveProfitConfirmOpen]);

  const applyOnlineAddOne = useCallback(async () => {
    hudMetaEffectSaveEnabledRef.current = true;
    const biz = getLedgerBizDate();
    flushSync(() => {
      closeOpenPointCardSegment(onlineEffectiveRef.current);
      setOnlineExtra((oe) => {
        const next = oe + 1;
        onlineExtraRef.current = next;
        return next;
      });
    });
    try {
      await api.mechLedgerSaveMeta(buildMechLedgerMetaPayload(biz));
    } catch (e) {
      setToast(e instanceof Error ? e.message : '在线人数保存失败，请检查网络或是否已登录');
      window.setTimeout(() => setToast(null), 3200);
    }
  }, [closeOpenPointCardSegment, bizDate, buildMechLedgerMetaPayload]);

  const applyOnlineSubOne = useCallback(async () => {
    hudMetaEffectSaveEnabledRef.current = true;
    const biz = getLedgerBizDate();
    flushSync(() => {
      closeOpenPointCardSegment(onlineEffectiveRef.current);
      setOnlineExtra((oe) => {
        const next = Math.max(0, oe - 1);
        onlineExtraRef.current = next;
        return next;
      });
    });
    try {
      await api.mechLedgerSaveMeta(buildMechLedgerMetaPayload(biz));
    } catch (e) {
      setToast(e instanceof Error ? e.message : '在线人数保存失败，请检查网络或是否已登录');
      window.setTimeout(() => setToast(null), 3200);
    }
  }, [closeOpenPointCardSegment, bizDate, buildMechLedgerMetaPayload]);

  /** 切换常用档位：立即落库（与今日物品行一致）；临时 + 人数清零，点卡从本刻起按新合计人数累计 */
  const applyOnlinePresetNow = useCallback(
    async (next: OnlinePreset) => {
      if (next === onlinePreset) return;
      hudMetaEffectSaveEnabledRef.current = true;
      const biz = getLedgerBizDate();
      flushSync(() => {
        closeOpenPointCardSegment(onlineEffectiveRef.current);
        onlinePresetRef.current = next;
        onlineExtraRef.current = 0;
        setOnlinePreset(next);
        setOnlineExtra(0);
      });
      try {
        await api.mechLedgerSaveMeta(buildMechLedgerMetaPayload(biz));
        setToast(`在线人数已切换为 ${next} 人（已写入数据库）`);
        window.setTimeout(() => setToast(null), 2200);
      } catch (e) {
        setToast(e instanceof Error ? e.message : '在线人数保存失败，请检查网络或是否已登录');
        window.setTimeout(() => setToast(null), 3200);
      }
    },
    [closeOpenPointCardSegment, bizDate, buildMechLedgerMetaPayload, onlinePreset],
  );

  useEffect(() => {
    if (!pickModal) return;
    if (pickModal.kind === 'book') {
      setPickBookType(LEDGER_LINGSHI_TYPES[0]);
      setPickLevel('120');
      return;
    }
    if (pickModal.kind === 'beast') {
      const br = loadBeastScrollRows();
      setPickBeastId(br[0]?.id ?? '');
      return;
    }
    if (pickModal.kind === 'ruyi') {
      setPickRuyiElement(RUYI_ELEMENTS[0]);
      return;
    }
    const opts = getLedgerPickLevelOptions(pickModal.item.name);
    const pick =
      (opts.includes('120') ? '120' : null) ??
      opts[Math.floor(opts.length / 2)] ??
      opts[0] ??
      '120';
    setPickLevel(pick);
  }, [pickModal]);

  useEffect(() => {
    if (!pickModal) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setPickModal(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [pickModal]);

  /** 点卡：每个在线角色每小时 6 点 ⇒ 秒 × 角色数 × (6/3600)；人数变化靠 closedSlices 分段，开放段用当前 onlineEffective */
  const POINT_CARD_PER_ROLE_PER_HOUR = 6;
  const pointCardSessionPoints = useMemo(() => {
    const rate = POINT_CARD_PER_ROLE_PER_HOUR / 3600;
    let pts = 0;
    for (const s of pointCardSeg.closedSlices) {
      pts += s.durationSec * s.roles * rate;
    }
    const sumClosedDur = pointCardSeg.closedSlices.reduce((a, s) => a + s.durationSec, 0);
    /** segmentStartElapsed 与已闭合时长之差的「前段」若未出现在 closedSlices 里（如库脚本只抬高了起点），用当前人数补齐，避免漏算 0→segmentStart 整段 */
    let gapDur = Math.max(0, pointCardSeg.segmentStartElapsed - sumClosedDur);
    if (pointCardBaseline > 0) {
      gapDur = 0;
    }
    pts += gapDur * onlineEffective * rate;
    const openDur = Math.max(0, elapsedSec - pointCardSeg.segmentStartElapsed);
    pts += openDur * onlineEffective * rate;
    return pts;
  }, [elapsedSec, onlineEffective, pointCardSeg, pointCardBaseline]);
  const pointCardPoints = pointCardBaseline + pointCardSessionPoints;
  onlinePresetRef.current = onlinePreset;
  onlineExtraRef.current = onlineExtra;
  teamPrincipalWanStrsRef.current = teamPrincipalWanStrs;
  teamCashWanStrsRef.current = teamCashWanStrs;
  pointCardPointsRef.current = pointCardPoints;
  baseElapsedSecRef.current = baseElapsedSec;
  runStartAtRef.current = runStartAt;
  pointCardSegRef.current = pointCardSeg;
  hudSnapshotForSaveRef.current = {
    onlinePreset,
    onlineExtra,
    teamPrincipalWanStrs,
    teamCashWanStrs,
    pointCardPoints,
    elapsedSec,
    baseElapsedSec,
    runStartAt,
    pointCardSeg,
  };

  /** 弹窗内：当前所选等级/种类对应的入账单价（与「加入今日」一致） */
  const pickPreviewW = useMemo(() => {
    if (!pickModal) return 0;
    const { item, valueW, kind } = pickModal;
    if (kind === 'book') {
      const p = getLingshiBookPrice(pickLevel, pickBookType);
      return p > 0 ? p : valueW;
    }
    if (kind === 'beast') {
      const row = loadBeastScrollRows().find((r) => r.id === pickBeastId);
      const p = row?.priceW;
      return p != null && p > 0 ? p : valueW;
    }
    if (kind === 'ruyi') {
      const p = getRuyiDanPrice(loadRuyiDanPrices(), pickRuyiElement);
      return p > 0 ? p : valueW;
    }
    const p = getTieredLedgerUnitPrice(item.name, pickLevel);
    return p > 0 ? p : valueW;
  }, [pickModal, pickLevel, pickBookType, pickBeastId, pickRuyiElement]);

  const itemProfitW = useMemo(
    () => todayLines.reduce((sum, l) => sum + l.valueW * l.count, 0),
    [todayLines]
  );

  const todayLinesPg = useTablePagination(todayLines);
  const historyViewRows = useMemo(() => {
    return historyRows.map((r) => {
      const profitYuan = (Number(r.profitW) || 0) * yuanPerWanW;
      const note = r.onlineRoles > 0 ? `${r.onlineRoles}开` : '—';
      return {
        date: r.bizDate,
        profitYuan: Number.isFinite(profitYuan) ? Math.round(profitYuan * 100) / 100 : 0,
        note,
      };
    });
  }, [historyRows, yuanPerWanW]);
  const historyPg = useTablePagination(historyViewRows);

  useEffect(() => {
    if (rightTab !== 'history') return;
    let cancel = false;
    (async () => {
      try {
        setHistoryLoading(true);
        setHistoryErr('');
        const r = await api.mechLedgerHistory(3650);
        if (cancel) return;
        setHistoryRows(Array.isArray(r.items) ? r.items : []);
      } catch (e) {
        if (cancel) return;
        setHistoryRows([]);
        setHistoryErr(e instanceof Error ? e.message : '历史收益加载失败');
      } finally {
        if (!cancel) setHistoryLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [rightTab]);

  const addTodayItem = useCallback(
    (item: LedgerItemDef) => {
      if (item.valueW <= 0) {
        setToast(
          '该物品单价为 0，未加入今日收益。请到「物品库」固定价格区为该物品填写单价（万 w）。',
        );
        window.setTimeout(() => setToast(null), 2200);
        return;
      }
      clearLedgerSkipHydrateBizFromSession();
      const cid = catalogItemIdFromLedgerDefId(item.id);
      setTodayLines((prev) => {
        const idx = prev.findIndex((p) => p.name === item.name);
        let next: TodayLine[];
        if (idx >= 0) {
          const updated = {
            ...prev[idx],
            count: prev[idx].count + 1,
            ...(cid != null && prev[idx].catalogItemId == null ? { catalogItemId: cid } : {}),
          };
          next = [updated, ...prev.filter((_, i) => i !== idx)];
        } else {
          next = [
            {
              id: item.id + Date.now(),
              name: item.name,
              valueW: item.valueW,
              count: 1,
              ...(cid != null ? { catalogItemId: cid } : {}),
            },
            ...prev,
          ];
        }
        scheduleSyncTodayLines(next);
        return next;
      });
    },
    [scheduleSyncTodayLines]
  );

  const handleDailyFixedClick = useCallback(
    (it: LedgerItemDef) => {
      const kind = getLedgerPickKind(it.name);
      if (kind) {
        setPickModal({ item: it, valueW: it.valueW, kind });
        return;
      }
      addTodayItem(it);
    },
    [addTodayItem]
  );

  const handleDailyVarClick = useCallback(
    (it: LedgerItemDef) => {
      const valueW = fixedPrice ? it.valueW : Math.round(it.valueW * (0.85 + Math.random() * 0.3));
      const kind = getLedgerPickKind(it.name);
      if (kind) {
        setPickModal({ item: it, valueW, kind });
        return;
      }
      addTodayItem({ ...it, valueW });
    },
    [addTodayItem, fixedPrice]
  );

  const handleSceneItemClick = useCallback(
    (it: LedgerItemDef) => {
      const valueW = fixedPrice ? it.valueW : rollFloatingPriceW(it.valueW);
      const kind = getLedgerPickKind(it.name);
      if (kind) {
        setPickModal({ item: it, valueW, kind });
        return;
      }
      addTodayItem({ ...it, valueW });
    },
    [addTodayItem, fixedPrice]
  );

  const confirmPickModal = useCallback(() => {
    if (!pickModal) return;
    const { item, valueW, kind } = pickModal;
    let name: string;
    let w = valueW;
    if (kind === 'book') {
      name = buildLedgerPickedDisplayName(item.name, pickLevel, pickBookType);
      const p = getLingshiBookPrice(pickLevel, pickBookType);
      if (p > 0) w = p;
    } else if (kind === 'beast') {
      const row = loadBeastScrollRows().find((r) => r.id === pickBeastId);
      if (!row) {
        setToast('未找到兽决种类，请在物品库检查');
        window.setTimeout(() => setToast(null), 2400);
        return;
      }
      name = buildBeastScrollDisplayName(row.label);
      if (row.priceW > 0) w = row.priceW;
    } else if (kind === 'ruyi') {
      name = buildRuyiDanDisplayName(pickRuyiElement);
      const p = getRuyiDanPrice(loadRuyiDanPrices(), pickRuyiElement);
      if (p > 0) w = p;
    } else {
      name = buildLedgerPickedDisplayName(item.name, pickLevel);
      const p = getTieredLedgerUnitPrice(item.name, pickLevel);
      if (p > 0) w = p;
    }
    addTodayItem({ ...item, name, valueW: w });
    setPickModal(null);
  }, [pickModal, pickLevel, pickBookType, pickBeastId, pickRuyiElement, addTodayItem]);

  const removeLine = useCallback(
    (id: string) => {
      setTodayLines((prev) => {
        const next = prev.filter((l) => l.id !== id);
        scheduleSyncTodayLines(next);
        return next;
      });
    },
    [scheduleSyncTodayLines]
  );

  const decreaseLineCount = useCallback(
    (id: string, delta: number) => {
      const d = Math.max(1, Math.floor(delta));
      setTodayLines((prev) => {
        const next = prev
          .map((l) => {
            if (l.id !== id) return l;
            const c = l.count - d;
            return c <= 0 ? null : { ...l, count: c };
          })
          .filter((x): x is TodayLine => x != null);
        scheduleSyncTodayLines(next);
        return next;
      });
    },
    [scheduleSyncTodayLines]
  );

  const requestRemoveLine = useCallback(
    (l: TodayLine) => {
      if (l.count <= 1) {
        removeLine(l.id);
        return;
      }
      setRemoveLineTarget(l);
      setRemoveQtyStr('1');
    },
    [removeLine]
  );

  const bumpYaksha = useCallback((key: string, delta: number) => {
    setYaksha((prev) => {
      const next = { ...prev, [key]: Math.max(0, (prev[key] ?? 0) + delta) };
      if (/^y[1-5]$/.test(key)) {
        next.total = (['y1', 'y2', 'y3', 'y4', 'y5'] as const).reduce((s, k) => s + (next[k] ?? 0), 0);
      }
      return next;
    });
  }, []);

  const onRewardIcon = useCallback(
    (item: LedgerItemDef) => {
      bumpYaksha('y1', 1);
      addTodayItem({ ...item, valueW: exactPrice ? item.valueW * 1.2 : item.valueW });
    },
    [addTodayItem, bumpYaksha, exactPrice]
  );

  const yakshaRates = useMemo(() => {
    const total = yaksha.total || 0;
    const wn = yaksha.wn || 0;
    const hm = yaksha.hm || 0;
    const turtle = yaksha.turtle || 0;
    const drop = yaksha.drop || 0;
    const pct = (n: number, d: number) => (d > 0 ? ((n / d) * 100).toFixed(1) : '0.0');
    return {
      withWn: pct(wn + hm, total || 1),
      turtleRate: pct(turtle, total || 1),
      dropRate: pct(drop, total || 1),
    };
  }, [yaksha]);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2200);
  }, []);
  const showToastRef = useRef<(msg: string) => void>(() => {});
  showToastRef.current = showToast;

  /** 自然日已跨天但记账台仍锁在昨日：不清空内容，直接把“本轮计时”归到今天 */
  const advanceLedgerBizToTodayKeepingTimer = useCallback(async () => {
    if (!sessionReady) return;
    const today = localBizDate();
    const curBiz = getLedgerBizDate();
    if (curBiz === today) return;
    if (!isLedgerBizDateLocked()) {
      unlockLedgerBizDateAndAdvanceToToday();
      return;
    }
    const ok = window.confirm(
      `检测到自然日已是 ${today}，但记账台业务日仍为 ${curBiz}（计时锁定）。\n\n` +
        `是否换日到今天并保留计时？\n` +
        `- 不会清空本页物品/现金/本金/点卡\n` +
        `- 会把“正在计时”的状态写入今天（避免刷新又回到昨天）`,
    );
    if (!ok) return;

    hudMetaEffectSaveEnabledRef.current = true;
    const elapsedNow = Math.max(0, Math.floor(elapsedSecRef.current));
    const wasRunning = runStartAtRef.current != null;
    const now = Date.now();

    // 先把昨天的“跑表”停掉（保留已累计时长），避免库里出现两个业务日都在跑
    try {
      await api.mechLedgerSaveMeta({
        ...buildMechLedgerMetaPayload(curBiz),
        elapsedSec: elapsedNow,
        ledgerBaseElapsedSec: elapsedNow,
        ledgerRunStartAtMs: null,
      });
    } catch {
      // ignore: 仍尝试推进到今天；若失败刷新可能仍被锁回昨日
    }

    // 把本地计时切成“以当前累计为底数，从此刻继续跑”
    setBaseElapsedSec(elapsedNow);
    baseElapsedSecRef.current = elapsedNow;
    const nextRunStart = wasRunning ? now : null;
    setRunStartAt(nextRunStart);
    runStartAtRef.current = nextRunStart;

    unlockLedgerBizDateAndAdvanceToToday();
    try {
      await api.mechLedgerSaveMeta(buildMechLedgerMetaPayload(today));
      showToast(`已换日到 ${today}（保留计时）`);
    } catch (e) {
      showToast(e instanceof Error ? e.message : '换日写入失败，请检查网络或是否已登录');
    }
  }, [buildMechLedgerMetaPayload, sessionReady, showToast]);

  const commitLineUnitPrice = useCallback(
    async (lineId: string) => {
      const raw = (priceEditStrsByLineId[lineId] ?? '').trim();
      if (!raw) return;
      const n = Number(raw);
      if (!Number.isFinite(n) || n <= 0) {
        showToast('单价(w)请输入 >0 的数字');
        return;
      }

      const target = todayLinesRef.current.find((x) => x.id === lineId) || null;
      setTodayLines((prev) => {
        const idx = prev.findIndex((x) => x.id === lineId);
        if (idx < 0) return prev;
        if (Math.abs(Number(prev[idx].valueW) - n) < 1e-9) return prev;
        const updated = { ...prev[idx], valueW: n };
        const next = [updated, ...prev.filter((_, i) => i !== idx)];
        scheduleSyncTodayLines(next);
        return next;
      });

      setPriceEditStrsByLineId((m) => {
        const { [lineId]: _, ...rest } = m;
        return rest;
      });

      const name = target?.name;
      if (!catalog?.panels) return;

      const flat = Object.values(catalog.panels).flat();
      const cid =
        target?.catalogItemId ??
        (lineId ? parseCatalogItemIdFromTodayLineId(lineId) : null) ??
        null;
      let row = cid != null ? flat.find((r) => r.id === cid) : undefined;
      if (!row && name) row = flat.find((r) => r.name === name);
      if (!row) {
        if (name) showToast(`未在物品库找到「${name}」，已仅修改今日单价`);
        return;
      }

      try {
        const updated = await api.itemCatalogUpdate(row.id, { priceW: n });
        setCatalog((prev) => {
          if (!prev) return prev;
          const nextPanels: ItemCatalogAllResponse['panels'] = { ...prev.panels };
          for (const k of Object.keys(nextPanels) as (keyof ItemCatalogAllResponse['panels'])[]) {
            nextPanels[k] = nextPanels[k].map((it) => (it.id === updated.id ? updated : it));
          }
          return { ...prev, panels: nextPanels };
        });
        showToast(`已同步物品库：${row.name} 单价 ${n} w`);
      } catch (e) {
        showToast(e instanceof Error ? e.message : '同步物品库失败（已修改今日单价）');
      }
    },
    [catalog, priceEditStrsByLineId, scheduleSyncTodayLines, showToast]
  );

  const persistDaySnapshot = useCallback(async (snapshotBizDate: string) => {
    for (let i = 0; i < teamSlotCount; i++) {
      const raw = String(teamCashWanStrs[i] ?? '').trim();
      if (raw === '') continue;
      const n = Number(raw);
      if (!Number.isFinite(n) || n < 0) {
        throw new Error(`队伍${TEAM_PRINCIPAL_CN[i]}现金（两）无效，请填数字或留空`);
      }
    }
    const principalSend = teamPrincipalsParsedW.map((x) => x / 10000);
    const cashSend = teamCashParsedW.map((x) => x / 10000);
    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    const payload = todayLines.map((l) => ({ name: l.name, valueW: l.valueW, count: l.count }));
    await api.mechLedgerPutTodayLines({ bizDate: snapshotBizDate, lines: payload });
    // meta 须成功：失败则抛错，禁止「保存收益」在未完整落库时误判成功（原 try/catch 会吞错）
    await api.mechLedgerSaveMeta({
      bizDate: snapshotBizDate,
      onlineCount: onlineEffective,
      onlinePreset,
      pointCardPoints,
      elapsedSec: Math.max(0, Math.floor(elapsedSec)),
      teamCashGameGoldW: cashSend,
      teamPrincipalsW: principalSend,
      ledgerBaseElapsedSec: baseElapsedSec,
      ledgerRunStartAtMs: runStartAt,
      ledgerPointCard: pointCardSeg,
    });
    return api.mechLedgerSaveDay({
      bizDate: snapshotBizDate,
      pointCardPoints,
      onlineCount: onlineEffective,
      onlinePreset,
      elapsedSec: Math.max(0, Math.floor(elapsedSec)),
      teamCashGameGoldW: cashSend,
      teamPrincipalsW: principalSend,
    });
  }, [
    teamSlotCount,
    teamCashWanStrs,
    teamPrincipalsParsedW,
    teamCashParsedW,
    todayLines,
    pointCardPoints,
    onlineEffective,
    onlinePreset,
    elapsedSec,
    baseElapsedSec,
    runStartAt,
    pointCardSeg,
  ]);

  /** 现金/本金/在线人数变更立即落库；在线时长与点卡由下方定时器每 5 分钟写入（不更新 point_card_saved_at） */
  const flushPendingMetaSave = useCallback(
    (biz: string, opts?: { keepalive?: boolean; force?: boolean; toastOnError?: boolean }) => {
    if (
      !opts?.force &&
      !opts?.keepalive &&
      biz === suppressAutoMetaSaveBizRef.current &&
      Date.now() < suppressAutoMetaSaveUntilRef.current
    ) {
      return;
    }
    const buildBody = () => buildMechLedgerMetaPayload(biz);
    if (opts?.keepalive) {
      api.mechLedgerSaveMetaKeepalive(buildBody());
    } else {
      void api
        .mechLedgerSaveMeta(buildBody())
        .then(() => {
          // 总览/每日收益等页面读取 DB：这里同步成功后广播一次，便于它们及时刷新点卡/现金等 meta。
          window.dispatchEvent(new CustomEvent('mhxy-mech-day-meta-saved', { detail: { bizDate: biz } }));
        })
        .catch((e) => {
          if (opts?.toastOnError) {
            showToastRef.current(
              e instanceof Error ? e.message : '记账台保存失败，请检查网络或是否已登录',
            );
          }
        });
    }
  },
  [buildMechLedgerMetaPayload],
);
  flushPendingMetaSaveRef.current = flushPendingMetaSave;

  /** 在线人数（常用档位 + 临时加减）、各队本金/现金：用户改动后写 meta（含当前点卡与时长快照）；回填触发的变更不写，避免盖掉未完成的保存。 */
  useEffect(() => {
    if (!sessionReady) return;
    if (!hudMetaEffectSaveEnabledRef.current) return;
    const biz = getLedgerBizDate();
    if (hudHydratedForBizRef.current !== biz) return;
    flushPendingMetaSave(biz, { force: true });
  }, [
    sessionReady,
    bizDate,
    onlinePreset,
    onlineExtra,
    teamPrincipalWanStrs,
    teamCashWanStrs,
    flushPendingMetaSave,
  ]);

  /** 计时启停、点卡分段：仅用户已操作过 HUD 后再由 effect 落库（同 block，避免刷新后 Hydrate 写回旧人数） */
  useEffect(() => {
    if (!sessionReady) return;
    if (!hudMetaEffectSaveEnabledRef.current) return;
    const biz = getLedgerBizDate();
    if (hudHydratedForBizRef.current !== biz) return;
    flushPendingMetaSave(biz, { force: true });
  }, [
    sessionReady,
    bizDate,
    baseElapsedSec,
    runStartAt,
    pointCardSeg,
    pointCardBaseline,
    flushPendingMetaSave,
  ]);

  /** 在线时长、消耗点卡累计值：仅定时落库（每 5 分钟），避免每秒请求 */
  useEffect(() => {
    if (!sessionReady) return;
    const biz = getLedgerBizDate();
    const tick = () => {
      if (hudHydratedForBizRef.current === biz) flushPendingMetaSave(biz);
    };
    const id = window.setInterval(tick, 300_000);
    return () => window.clearInterval(id);
  }, [sessionReady, bizDate, flushPendingMetaSave]);

  /** 仅重置本页状态：不向服务器写入物品行、meta、client-prefs 等；库中数据不变。刷新或重进页面会从 /daily 恢复。 */
  const applyClearLedgerTimer = useCallback(() => {
    const resetLocal = (opts?: { baseline?: number; toast?: string }) => {
      if (opts?.baseline != null) setPointCardBaseline(opts.baseline);
      setBaseElapsedSec(0);
      setRunStartAt(null);
      setPointCardSeg({ closedSlices: [], segmentStartElapsed: 0 });
      setTeamPrincipalWanStrs(emptyTeamPrincipalStrs());
      setTeamCashWanStrs(emptyTeamPrincipalStrs());
      setTodayLines([]);
      setOnlinePreset(DEFAULT_ONLINE_PRESET);
      setOnlineExtra(0);
      setYaksha(initYakshaCounts());
      setMainTab('daily');
      setRightTab('today');
      setFixedPrice(true);
      setExactPrice(false);
      setPriceEditStrsByLineId({});
      setPickModal(null);
      setTimerTick((x) => x + 1);
      // 同步 ref，保证随后显式写 meta 时不会带上旧的 runStartAt/计时
      baseElapsedSecRef.current = 0;
      runStartAtRef.current = null;
      pointCardSegRef.current = { closedSlices: [], segmentStartElapsed: 0 };
      onlinePresetRef.current = DEFAULT_ONLINE_PRESET;
      onlineExtraRef.current = 0;
      if (opts?.toast) showToast(opts.toast);
    };

    for (let i = 0; i < teamSlotCount; i++) {
      const raw = String(teamCashWanStrs[i] ?? '').trim();
      if (raw === '') continue;
      const n = Number(raw);
      if (!Number.isFinite(n) || n < 0) {
        showToast(`队伍${TEAM_PRINCIPAL_CN[i]}现金（两）无效，请填数字或留空后再清除计时`);
        return;
      }
    }

    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    // 避免紧随其后的 HUD effect 用「已清空」状态立刻 save-meta 覆盖库内数据
    hudMetaEffectSaveEnabledRef.current = false;
    resetLocal({ baseline: 0 });
    try {
      sessionStorage.setItem(MECH_LEDGER_SKIP_HYDRATE_BIZ_KEY, getLedgerBizDate());
    } catch {
      /* private mode / disabled storage */
    }
    showToast(
      '已重置记账台本页显示（计时、今日收益表、夜叉、本金/现金等）。未改服务器数据；同一业务日离开再进本页也不会自动从库回填，录入物品或现金/本金后即恢复与库同步。',
    );
  }, [showToast, teamCashWanStrs, teamSlotCount]);

  const confirmClearLedger = useCallback(async () => {
    setClearTimerConfirmOpen(false);
    const prevBiz = getLedgerBizDate();
    applyClearLedgerTimer();
    // 结束本轮计时：把“停止计时（runStartAt=null）”写回服务端，避免刷新后 /daily 又把业务日锁回旧日
    try {
      await api.mechLedgerSaveMeta(buildMechLedgerMetaPayload(prevBiz));
    } catch (e) {
      showToast(e instanceof Error ? e.message : '停止计时写入失败，请检查网络或是否已登录');
    }
    // 解锁记账台业务日并推进到自然日“今天”
    unlockLedgerBizDateAndAdvanceToToday();
  }, [applyClearLedgerTimer, buildMechLedgerMetaPayload, showToast]);

  const confirmRemoveLineQty = useCallback(() => {
    if (!removeLineTarget) return;
    const n = Math.floor(Number(removeQtyStr));
    if (!Number.isFinite(n) || n < 1) {
      showToast('请输入 ≥1 的整数数量');
      return;
    }
    const rm = Math.min(n, removeLineTarget.count);
    if (rm >= removeLineTarget.count) {
      removeLine(removeLineTarget.id);
    } else {
      decreaseLineCount(removeLineTarget.id, rm);
    }
    setRemoveLineTarget(null);
  }, [removeLineTarget, removeQtyStr, removeLine, decreaseLineCount, showToast]);

  useEffect(() => {
    const flushMetaIfHydrated = () => {
      const b = getLedgerBizDate();
      /** 未等 /daily 回填完成就 keepalive 写库，会用初始空 HUD 覆盖库里本金（Strict Mode 假卸载、刷新首帧常见） */
      if (hudHydratedForBizRef.current !== b) return;
      /** 仅用户本会话动过 HUD 才 keepalive 写 meta。否则刷新/关页时 ref 仍为 false，快照里计时为 0 会把库里脚本写入的跑表状态盖没 */
      if (!hudMetaEffectSaveEnabledRef.current) return;
      flushPendingMetaSave(b, { keepalive: true });
    };
    const onVis = () => {
      if (document.visibilityState === 'hidden') {
        flushPendingSync();
        flushMetaIfHydrated();
      }
    };
    const onPageHide = () => {
      flushPendingSync();
      flushMetaIfHydrated();
    };
    window.addEventListener('pagehide', onPageHide);
    document.addEventListener('visibilitychange', onVis);
    return () => {
      document.removeEventListener('visibilitychange', onVis);
      window.removeEventListener('pagehide', onPageHide);
      flushPendingSync();
      flushMetaIfHydrated();
    };
  }, [bizDate, flushPendingMetaSave, flushPendingSync]);

  /** 侧栏切到其他路由时也会卸载本页，不触发 visibilitychange；离页前强制落库 */
  useEffect(() => {
    return () => {
      const b = getLedgerBizDate();
      if (hudHydratedForBizRef.current !== b) return;
      if (!hudMetaEffectSaveEnabledRef.current) return;
      flushPendingMetaSaveRef.current(b, { keepalive: true });
    };
  }, [bizDate]);

  const resolveVoiceItemPrice = useCallback(
    (item: LedgerItemDef): LedgerItemDef => {
      if (fixedItems.some((f) => f.name === item.name)) return { ...item };
      const v = varItems.find((x) => x.name === item.name);
      if (v) {
        const valueW = fixedPrice ? v.valueW : Math.round(v.valueW * (0.85 + Math.random() * 0.3));
        return { ...v, valueW };
      }
      const yw = yakWhiteItems.find((x) => x.name === item.name);
      if (yw) return { ...yw };
      const yr = yakRewardItems.find((x) => x.name === item.name);
      if (yr) return { ...yr };
      const s = sceneItems.find((x) => x.name === item.name);
      if (s) {
        const valueW = fixedPrice ? s.valueW : rollFloatingPriceW(s.valueW);
        return { ...s, valueW };
      }
      return { ...item };
    },
    [fixedItems, varItems, yakWhiteItems, yakRewardItems, sceneItems, fixedPrice],
  );

  /** 0 未匹配；1 已直接加行；2 已打开需选等级/种类弹窗 */
  const applyVoiceTranscript = useCallback(
    (transcript: string, silent = false): 0 | 1 | 2 => {
      const { quantity, nameQuery } = parseVoiceLedgerCommand(transcript);
      if (!nameQuery.trim()) {
        return 0;
      }
      const hit = findBestVoiceLedgerItem(nameQuery, voiceCatalogItems);
      if (!hit) {
        if (!silent) {
          showToast(
            `未匹配「${nameQuery}」。请说格子上的准确名称，或用逗号/空格隔开多项后再点「结束录入」。`,
          );
        }
        return 0;
      }
      const resolved = resolveVoiceItemPrice(hit);
      const kind = getLedgerPickKind(resolved.name);
      if (kind) {
        setPickModal({ item: resolved, valueW: resolved.valueW, kind });
        setRightTab('today');
        showToast(
          silent
            ? `「${resolved.name}」需先选等级/种类，请完成弹窗后点「加入今日」`
            : quantity > 1
              ? `「${resolved.name}」需先选等级/种类，请先完成弹窗后再语音添加`
              : `请为「${resolved.name}」选择等级或种类后点「加入今日」`,
        );
        return 2;
      }
      for (let i = 0; i < quantity; i++) {
        addTodayItem(resolved);
      }
      setRightTab('today');
      if (!silent) {
        showToast(quantity > 1 ? `已添加 ${resolved.name} × ${quantity}` : `已添加 ${resolved.name}`);
      }
      return 1;
    },
    [voiceCatalogItems, resolveVoiceItemPrice, addTodayItem, showToast],
  );

  /** 结束录入时：用当前听写全文再匹配一轮（连续识别往往只有停录后才定型） */
  const flushVoiceSessionSnapshot = useCallback(
    (raw: string) => {
      const text = raw.trim();
      if (!text) {
        setVoiceLiveText('');
        voiceLiveTextRef.current = '';
        return;
      }
      const parts = splitVoiceSegments(text);
      let addCount = 0;
      let sawModal = false;
      for (const p of parts) {
        const r = applyVoiceTranscript(p, true);
        if (r === 2) {
          sawModal = true;
          break;
        }
        if (r === 1) addCount += 1;
      }
      if (!sawModal && addCount === 0) {
        const r = applyVoiceTranscript(text, true);
        if (r === 2) sawModal = true;
        else if (r === 1) addCount += 1;
      }
      const anyOk = addCount > 0 || sawModal;
      if (addCount > 0 && !sawModal) {
        showToast(addCount > 1 ? `已加入 ${addCount} 条` : '已加入今日收益');
      }
      if (!anyOk) {
        const greedy = extractItemsGreedyFromTranscript(text, voiceCatalogItems);
        if (greedy.length === 0) {
          showToast(
            `未能匹配物品。识别内容：「${text.length > 40 ? `${text.slice(0, 40)}…` : text}」`,
          );
        } else {
          let blocked = false;
          for (const it of greedy) {
            const resolved = resolveVoiceItemPrice(it);
            const kind = getLedgerPickKind(resolved.name);
            if (kind) {
              setPickModal({ item: resolved, valueW: resolved.valueW, kind });
              setRightTab('today');
              showToast(
                `「${resolved.name}」需先选等级/种类；连读已拆出 ${greedy.length} 项，请先完成弹窗`,
              );
              blocked = true;
              break;
            }
            addTodayItem(resolved);
          }
          if (!blocked) {
            setRightTab('today');
            showToast(`已添加 ${greedy.length} 项（连读自动拆分）`);
          }
        }
      }
      setVoiceLiveText('');
      voiceLiveTextRef.current = '';
    },
    [applyVoiceTranscript, voiceCatalogItems, resolveVoiceItemPrice, addTodayItem, showToast],
  );

  const stopServerVoiceRecorder = useCallback(() => {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') {
      try {
        mr.stop();
      } catch {
        mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
        mediaStreamRef.current = null;
        mediaRecorderRef.current = null;
        setVoiceListening(false);
      }
    } else {
      mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
      mediaRecorderRef.current = null;
      setVoiceListening(false);
    }
  }, []);

  const startServerVoiceRecorder = useCallback(async () => {
    if (!serverSpeechAvailable) {
      showToast('未开启服务端语音识别：请在 server/.env 配置 SPEECH_OPENAI_API_KEY（或 OPENAI_API_KEY）后重启后端');
      return;
    }
    if (!getToken()) {
      showToast('请先登录后再使用服务器语音识别');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : '';
      const mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      const outMime = mr.mimeType || mime || 'audio/webm';
      mediaChunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data?.size) mediaChunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        mediaStreamRef.current = null;
        mediaRecorderRef.current = null;
        setVoiceListening(false);
        const parts = mediaChunksRef.current;
        mediaChunksRef.current = [];
        if (!parts.length) {
          showToast('没有录到有效音频');
          return;
        }
        const blob = new Blob(parts, { type: outMime });
        try {
          showToast('正在识别语音…');
          const { text } = await api.mechLedgerSpeechTranscribe(blob);
          const t = (text || '').trim();
          if (!t) {
            showToast('未识别到文字，请再说清晰些');
            return;
          }
          flushVoiceSessionSnapshot(t);
        } catch (e) {
          showToast(e instanceof Error ? e.message : '识别失败');
        }
      };
      mr.onerror = () => {
        stream.getTracks().forEach((x) => x.stop());
        mediaStreamRef.current = null;
        mediaRecorderRef.current = null;
        setVoiceListening(false);
        showToast('录音异常');
      };
      mediaRecorderRef.current = mr;
      mr.start(500);
      setVoiceListening(true);
      setVoiceLiveText('录音中…（点「结束录入」后上传并解析）');
      voiceLiveTextRef.current = '';
      setRightTab('today');
    } catch {
      showToast('无法打开麦克风');
    }
  }, [serverSpeechAvailable, flushVoiceSessionSnapshot, showToast]);

  const toggleVoiceRecognition = useCallback(() => {
    if (speechMode === 'server') {
      if (voiceListening) {
        stopServerVoiceRecorder();
        return;
      }
      void startServerVoiceRecorder();
      return;
    }
    const Ctor = getBrowserSpeechRecognitionConstructor();
    if (!Ctor) {
      showToast('当前浏览器不支持语音识别（请用 Chrome / Edge 桌面版并允许麦克风）');
      return;
    }
    if (voiceListening) {
      const snapshot = voiceLiveTextRef.current.trim();
      voiceShouldRunRef.current = false;
      try {
        voiceRecRef.current?.stop();
      } catch {
        /* ignore */
      }
      voiceRecRef.current = null;
      setVoiceListening(false);
      if (snapshot) {
        flushVoiceSessionSnapshot(snapshot);
      } else {
        setVoiceLiveText('');
        voiceLiveTextRef.current = '';
      }
      return;
    }
    try {
      const rec = new Ctor();
      rec.lang = 'zh-CN';
      rec.continuous = true;
      rec.interimResults = true;
      try {
        rec.maxAlternatives = 5;
      } catch {
        /* ignore */
      }
      rec.onresult = (event) => {
        let line = '';
        for (let i = 0; i < event.results.length; i++) {
          line += event.results[i]?.[0]?.transcript ?? '';
        }
        const trimmed = line.trim();
        voiceLiveTextRef.current = trimmed;
        setVoiceLiveText(trimmed);
      };
      rec.onerror = (ev) => {
        const code = ev.error;
        if (code === 'aborted' || code === 'no-speech') {
          return;
        }
        if (code === 'not-allowed') {
          voiceShouldRunRef.current = false;
          setVoiceListening(false);
          showToast('麦克风权限被拒绝，请在浏览器设置中允许');
          return;
        }
        if (code === 'network') {
          voiceShouldRunRef.current = false;
          setVoiceListening(false);
          showToast(
            'Chrome 报 network：无法连接在线语音识别。可改用上方「服务器转写」，或试 Edge、检查代理/扩展与网络。',
          );
          return;
        }
        if (code === 'service-not-allowed') {
          voiceShouldRunRef.current = false;
          setVoiceListening(false);
          showToast('语音服务被禁用或不可用（策略/地区限制），无法使用在线识别。');
          return;
        }
        if (code === 'audio-capture') {
          voiceShouldRunRef.current = false;
          setVoiceListening(false);
          showToast('未检测到可用麦克风，请检查设备连接与系统权限。');
          return;
        }
        voiceShouldRunRef.current = false;
        setVoiceListening(false);
        showToast(`语音识别出错：${code}`);
      };
      rec.onend = () => {
        if (voiceShouldRunRef.current && voiceRecRef.current === rec) {
          window.setTimeout(() => {
            if (!voiceShouldRunRef.current || voiceRecRef.current !== rec) return;
            try {
              rec.start();
            } catch {
              voiceShouldRunRef.current = false;
              setVoiceListening(false);
              voiceRecRef.current = null;
              setVoiceLiveText('');
            }
          }, 120);
        } else {
          setVoiceListening(false);
          voiceRecRef.current = null;
          setVoiceLiveText('');
        }
      };
      voiceShouldRunRef.current = true;
      voiceRecRef.current = rec;
      rec.start();
      setVoiceListening(true);
      setVoiceLiveText('');
      voiceLiveTextRef.current = '';
      setRightTab('today');
    } catch {
      showToast('无法启动语音识别');
      voiceShouldRunRef.current = false;
      setVoiceListening(false);
    }
  }, [
    speechMode,
    voiceListening,
    showToast,
    flushVoiceSessionSnapshot,
    startServerVoiceRecorder,
    stopServerVoiceRecorder,
  ]);

  useEffect(() => {
    return () => {
      voiceShouldRunRef.current = false;
      try {
        voiceRecRef.current?.stop();
      } catch {
        /* ignore */
      }
      voiceRecRef.current = null;
      const mr = mediaRecorderRef.current;
      if (mr && mr.state !== 'inactive') {
        try {
          mr.stop();
        } catch {
          /* ignore */
        }
      }
      mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
      mediaRecorderRef.current = null;
    };
  }, []);

  const saveProfit = async (snapshotBizDate: string) => {
    const cashSend = teamCashParsedW.map((x) => x / 10000);
    const cashGameGoldWWan = cashSend.reduce((a, b) => a + b, 0);
    try {
      // 防止“看似保存成功但实际保存了全 0”
      const principalSend = teamPrincipalsParsedW.map((x) => x / 10000);
      const principalsSum = principalSend.reduce((a, b) => a + (Number(b) || 0), 0);
      const hasAnyLine = todayLines.length > 0;
      const hasAnyCash = cashSend.some((x) => (Number(x) || 0) > 0);
      const hasAnyPrincipal = principalsSum > 0;
      const hasAnyPoint = pointCardPoints > 0;
      if (!hasAnyLine && !hasAnyCash && !hasAnyPrincipal && !hasAnyPoint) {
        showToast('当前没有可保存的数据（物品/点卡/现金/本金均为 0 或为空）。请先录入后再点「保存收益」。');
        return;
      }

      await persistDaySnapshot(snapshotBizDate);
      // 保存后回读 DB 核对，避免“接口成功但写入为空/日期不一致”误判
      let verified: MechLedgerDailyResponse | null = null;
      try {
        verified = await api.mechLedgerDaily(snapshotBizDate);
      } catch {
        verified = null;
      }
      const netW = netCashPreviewWan;
      const cashHint =
        cashGameGoldWWan > 0
          ? `；现金（毛）${formatWanZhCN(cashGameGoldWWan)}` +
            (principalsSumWWan > 0
              ? `，本金合计 ${formatWanZhCN(principalsSumWWan)}，净 ${formatWanZhCN(netW)}`
              : '')
          : '';
      const savedBiz = snapshotBizDate;
      const dbOk = (() => {
        if (!verified) return false;
        if (String(verified.bizDate || '').slice(0, 10) !== savedBiz) return false;
        if ((verified.lines?.length || 0) > 0) return true;
        if ((verified.cashGameGoldW ?? 0) > 0) return true;
        if ((verified.netCashGameGoldW ?? 0) > 0) return true;
        if ((verified.pointCardPoints ?? 0) > 0) return true;
        const ps = verified.teamPrincipalsW?.reduce((a: number, b: number) => a + (Number(b) || 0), 0) ?? 0;
        return ps > 0;
      })();
      showToast(
        `已保存到数据库（业务日 ${savedBiz}）：物品 ${todayLines.length} 行共 ${itemProfitW.toFixed(1)} w；点卡 ${pointCardPoints.toFixed(2)} 点（${onlineEffective} 角色）${cashHint}` +
          (dbOk ? '。可在侧栏「每日收益」查看。' : '。但回读数据库仍为空/全 0：请检查业务日期与录入内容。')
      );
    } catch (e) {
      showToast(e instanceof Error ? e.message : '保存失败（请确认已登录且已执行 db:migrate-v6）');
    }
  };

  /** 点「保存收益」时二选一：跨天时段直接出日期选择；否则出「保存当日正式收益？」确认（不嵌套两个弹窗） */
  const openSaveProfitEntry = useCallback(() => {
    if (isInLateNightBizDatePickWindow(new Date())) {
      const today = getLedgerBizDate();
      const yesterday = ymdAddDays(today, -1);
      saveBizDatePickCbRef.current = (picked) => void saveProfit(picked);
      setSaveBizDatePick({ today, yesterday });
      return;
    }
    setSaveProfitConfirmOpen(true);
  }, [bizDate, saveProfit]);

  const confirmSaveProfit = useCallback(() => {
    setSaveProfitConfirmOpen(false);
    void saveProfit(getLedgerBizDate());
  }, [saveProfit]);

  return (
    <div className="mech-ledger-root">
      <div className="mech-inner">
        <header className="mech-titlebar">
          <h1 style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
            <span>多开记账台</span>
            <span
              className="badge"
              title="保存收益/每日收益明细都按这个业务日期落库与查询（跨过 00:00 就是当天）。后为当前本地时刻。"
              style={{ opacity: 0.92 }}
            >
              业务日期 {bizDate}{' '}
              <span className="mech-bizdate-hms" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {formatLocalHms(new Date())}
              </span>
            </span>
          </h1>
          <nav className="mech-menubar">
            <a href="#menu">菜单</a>
            <Link to="/app/ledger/catalog">物品库</Link>
            <Link to="/app/cash">消耗</Link>
            <Link to="/app/ledger/daily">每日收益</Link>
            <a href="#skin">皮肤</a>
            <a href="#about">关于</a>
          </nav>
        </header>
        {!catalog && !catalogErr && (
          <p className="mech-note" style={{ marginBottom: '0.5rem' }}>
            正在加载物品库…
          </p>
        )}
        {catalogErr && (
          <p className="mech-note" style={{ marginBottom: '0.5rem' }}>
            无法加载物品库，当前显示内置默认格子与价格（请确认已登录且网络正常）。
            <Link to="/app/ledger/catalog"> 打开物品库 </Link>
            维护并保存后，刷新本页即可优先使用数据库中的名称与单价（w）。
          </p>
        )}
        {usingDb && totalCatalogRows === 0 && (
          <p className="mech-note" style={{ marginBottom: '0.5rem' }}>
            物品库中暂无物品，记账台格子为空。
            <Link to="/app/ledger/catalog"> 打开物品库 </Link>
            导入预设或新增物品后即可在此显示。
          </p>
        )}

        {!sessionReady && (
          <p className="mech-note" role="status" style={{ marginBottom: '0.5rem' }}>
            正在加载当日在线人数、本金与计时…完成前请勿操作，以免与服务器数据冲突。
          </p>
        )}
        <section className="mech-hud-row">
          <div className="mech-hud-cell mech-hud-cell--online-count">
            <div className="mech-hud-label">在线人数</div>
            <div className="mech-online-count-row">
              <label className="mech-online-count-field">
                <select
                  className="mech-hud-select"
                  disabled={!sessionReady}
                  value={String(onlinePreset)}
                  title="切换后立即写入数据库；临时 + 人数会清零，点卡从本刻起按新人数累计"
                  onChange={(e) => {
                    const n = Number(e.target.value);
                    if (!(ONLINE_COUNT_PRESETS as readonly number[]).includes(n)) return;
                    if (n === onlinePreset) return;
                    const ok = window.confirm(
                      `确认切换在线人数档位：${onlinePreset} → ${n}？\n\n` +
                        `- 临时 + 人数将清零\n` +
                        `- 点卡从此刻起按新合计人数分段累计\n` +
                        `- 将立即写入数据库（刷新/跳页仍生效）`,
                    );
                    if (!ok) return;
                    void applyOnlinePresetNow(n as OnlinePreset);
                  }}
                >
                  {ONLINE_COUNT_PRESETS.map((k) => (
                    <option key={k} value={String(k)}>
                      {k} 人
                    </option>
                  ))}
                </select>
              </label>
              <div className="mech-online-count-actions">
                <button
                  type="button"
                  className="mech-btn mech-btn--online-delta"
                  disabled={!sessionReady}
                  title="立即写入数据库"
                  onClick={() => void applyOnlineAddOne()}
                >
                  +1 人
                </button>
                <button
                  type="button"
                  className="mech-btn mech-btn--online-delta"
                  disabled={!sessionReady}
                  title="立即写入数据库"
                  onClick={() => {
                    if (onlineExtra <= 0) {
                      setToast('当前没有临时加人');
                      window.setTimeout(() => setToast(null), 2200);
                      return;
                    }
                    void applyOnlineSubOne();
                  }}
                >
                  -1 人
                </button>
              </div>
            </div>
            <div className="mech-team-principals" aria-label="队伍本金">
              <div className="mech-team-principals-title">队伍本金（两）</div>
              <div className="mech-team-principal-row">
                {Array.from({ length: teamSlotCount }, (_, i) => (
                  <label key={i} className="mech-team-principal-field">
                    <span className="mech-team-principal-label">队伍{TEAM_PRINCIPAL_CN[i]}</span>
                    <input
                      className="mech-hud-input mech-team-principal-input"
                      type="number"
                      min={0}
                      step="0.0001"
                      placeholder="0"
                      disabled={!sessionReady}
                      value={teamPrincipalWanStrs[i]}
                      onChange={(e) => {
                        hudMetaEffectSaveEnabledRef.current = true;
                        const v = e.target.value;
                        setTeamPrincipalWanStrs((prev) => {
                          const next: [string, string, string, string] = [
                            prev[0],
                            prev[1],
                            prev[2],
                            prev[3],
                          ];
                          next[i] = v;
                          if (next.some((x) => String(x).trim() !== '')) clearLedgerSkipHydrateBizFromSession();
                          return next;
                        });
                      }}
                      aria-label={`队伍${TEAM_PRINCIPAL_CN[i]}本金（两）`}
                    />
                  </label>
                ))}
              </div>
            </div>
          </div>
          <div className="mech-hud-cell mech-hud-cell--elapsed">
            <div className="mech-hud-label">在线时长</div>
            <div className="mech-elapsed-row">
              <div
                className={`mech-hud-value mech-elapsed-time ${isTimerRunning ? 'timer-run' : 'timer-paused'}`}
              >
                {formatElapsed(elapsedSec)}
              </div>
              <button
                type="button"
                className="mech-btn mech-btn--elapsed-clear"
                disabled={!sessionReady}
                onClick={() => setClearTimerConfirmOpen(true)}
              >
                清除计时
              </button>
            </div>
            <div className="mech-team-principals mech-team-cash-below-timer" aria-label="各队现金">
              <div className="mech-team-principals-title">现金梦幻币（两）</div>
              <div className="mech-team-principal-row">
                {Array.from({ length: teamSlotCount }, (_, i) => (
                  <label key={i} className="mech-team-principal-field">
                    <span className="mech-team-principal-label">队伍{TEAM_PRINCIPAL_CN[i]}现金</span>
                    <input
                      className="mech-hud-input mech-team-principal-input"
                      type="number"
                      min={0}
                      step="0.0001"
                      placeholder="0"
                      disabled={!sessionReady}
                      value={teamCashWanStrs[i]}
                      onChange={(e) => {
                        hudMetaEffectSaveEnabledRef.current = true;
                        const v = e.target.value;
                        setTeamCashWanStrs((prev) => {
                          const next: [string, string, string, string] = [
                            prev[0],
                            prev[1],
                            prev[2],
                            prev[3],
                          ];
                          next[i] = v;
                          if (next.some((x) => String(x).trim() !== '')) clearLedgerSkipHydrateBizFromSession();
                          return next;
                        });
                      }}
                      aria-label={`队伍${TEAM_PRINCIPAL_CN[i]}现金梦幻币（两）`}
                    />
                  </label>
                ))}
              </div>
              {(principalsSumW > 0 || cashGrossWPreview > 0) && (
                <p className="mech-team-principals-hint" style={{ marginTop: '0.35rem' }}>
                  净现金约 {formatWanZhCN(netCashPreviewWan)}
                </p>
              )}
            </div>
          </div>
          <div className="mech-hud-cell mech-hud-cell--live-stats">
            <div className="mech-hud-label">实时消耗 / 收益</div>
            <div className="mech-live-stats">
              <div className="mech-live-stats-col">
                <div className="mech-live-stats-main">消耗点卡: {pointCardPoints.toFixed(2)} 点</div>
                <div className="mech-live-stats-sub">
                  当前 {onlineEffective} 人 · 分段累计（约合 {pointCardPointsToYuan(pointCardPoints).toFixed(2)} 元）
                </div>
              </div>
              <div className="mech-live-stats-col">
                <div className="mech-live-stats-main">物品收益: {itemProfitW.toFixed(1)} w</div>
                <div className="mech-live-stats-sub">
                  物品（约合 {(itemProfitW * yuanPerWanW).toFixed(2)} 元）
                </div>
              </div>
            </div>
          </div>
          <div className="mech-hud-cell mech-hud-cell--gold-rate">
            <div className="mech-hud-label">金价折算</div>
            <div
              className="mech-gold-rate-row"
              title="与「每日收益」共用；档位固定 3000 万，只改人民币；折算：物品元 = 物品 w ×（元 ÷ 3000）"
            >
              <div className="mech-gold-rate-field mech-gold-rate-field--fixed">
                <span className="mech-gold-rate-sublabel">游戏币</span>
                <span className="mech-gold-rate-fixed-wrap">
                  <span className="mech-gold-rate-fixed">{LEDGER_GAME_WAN_ANCHOR}</span>
                  <span className="mech-gold-rate-unit">万</span>
                </span>
              </div>
              <span className="mech-gold-rate-eq">=</span>
              <label className="mech-gold-rate-field">
                <span className="mech-gold-rate-sublabel">人民币</span>
                <span className="mech-gold-rate-yuan-wrap">
                  <input
                    className="mech-hud-input mech-hud-input--yuan"
                    type="text"
                    inputMode="decimal"
                    autoComplete="off"
                    value={yuanInputStr}
                    onChange={(e) => setYuanInputStr(e.target.value)}
                    onBlur={() => {
                      const raw = yuanInputStr.trim().replace(/,/g, '');
                      if (raw === '') {
                        setYuanInputStr(roundLedgerYuan2(gameYuan.yuan).toFixed(2));
                        return;
                      }
                      const n = Number(raw);
                      if (!Number.isFinite(n) || n < 0) {
                        setYuanInputStr(roundLedgerYuan2(gameYuan.yuan).toFixed(2));
                        return;
                      }
                      const y = roundLedgerYuan2(n);
                      const next = { gameWan: LEDGER_GAME_WAN_ANCHOR, yuan: y };
                      setGameYuan(next);
                      setYuanInputStr(y.toFixed(2));
                      saveGameYuanPair(next);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
                    }}
                  />
                  <span className="mech-gold-rate-unit">元</span>
                </span>
              </label>
              <span className="mech-gold-rate-derived">
                折合每 1 w ≈ {Number(yuanPerWanW.toFixed(6))} 元
              </span>
            </div>
            <div className="mech-hud-gold-rate-actions">
              <div className="mech-voice-bar mech-voice-bar--hud" aria-label="语音录入">
                {serverSpeechAvailable ? (
                  <div className="mech-voice-mode" role="group" aria-label="语音识别方式">
                    <label className="mech-voice-mode-label">
                      <input
                        type="radio"
                        name="mechSpeechModeHud"
                        checked={speechMode === 'browser'}
                        disabled={voiceListening}
                        onChange={() => setSpeechMode('browser')}
                      />
                      浏览器识别
                    </label>
                    <label className="mech-voice-mode-label">
                      <input
                        type="radio"
                        name="mechSpeechModeHud"
                        checked={speechMode === 'server'}
                        disabled={voiceListening}
                        onChange={() => setSpeechMode('server')}
                      />
                      服务器转写（推荐 Chrome）
                    </label>
                  </div>
                ) : null}
                <div className="mech-voice-transcript-hud" aria-live="polite">
                  {voiceLiveText || ''}
                </div>
              </div>
              <div className="mech-actions-btns mech-actions-btns--in-gold">
                <button
                  type="button"
                  className="mech-btn"
                  disabled={!sessionReady}
                  onClick={toggleLedgerTimer}
                >
                  {isTimerRunning ? '暂停计时' : baseElapsedSec > 0 ? '继续计时' : '开始计时'}
                </button>
                {sessionReady && localBizDate() !== getLedgerBizDate() && (
                  <button type="button" className="mech-btn" onClick={() => void advanceLedgerBizToTodayKeepingTimer()}>
                    换日到今天
                  </button>
                )}
                <button
                  type="button"
                  className={`mech-btn ${voiceListening ? 'mech-btn--voice-active' : ''}`}
                  disabled={voiceButtonDisabled}
                  aria-pressed={voiceListening}
                  aria-label={voiceListening ? '结束语音录入' : '开始语音录入'}
                  onClick={toggleVoiceRecognition}
                >
                  {voiceListening ? '结束录入' : '语音录入'}
                </button>
                <button type="button" className="mech-btn" onClick={openSaveProfitEntry}>
                  保存收益
                </button>
              </div>

            </div>
          </div>
        </section>

        <div className="mech-body">
          <div className="mech-panel-block">
            <div className="mech-tabs">
              {(
                [
                  ['daily', '日常记录'],
                  ['yaksha', '夜叉记录'],
                  ['scene', '场景记录'],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  className={`mech-tab ${mainTab === id ? 'active' : ''}`}
                  onClick={() => setMainTab(id)}
                >
                  {label}
                </button>
              ))}
            </div>

            {mainTab === 'daily' && (
              <>
                <div className="mech-subtitle">
                  固定价格区（灵饰书 / 兽决 / 晶石等会先弹窗选等级或种类，单价在弹窗内预览，加入后计入上方「物品收益」）
                </div>
                <div className="mech-icon-grid mech-icon-grid--labeled">
                  {fixedItems.map((it) => (
                    <button
                      key={it.id}
                      type="button"
                      className="mech-icon-cell mech-icon-cell--with-label"
                      title={itemTooltip(it)}
                      onClick={() => handleDailyFixedClick(it)}
                    >
                      <span className="mech-icon-cell-img-wrap">
                        <LedgerItemIcon
                          iconIndex={it.iconIndex}
                          emoji={it.emoji}
                          name={it.name}
                          iconFile={it.iconFile}
                          imageUrl={it.imageUrl}
                        />
                      </span>
                      <span className="mech-icon-cell-label-stack">
                        <span className="mech-icon-cell-label">{it.name}</span>
                      </span>
                    </button>
                  ))}
                </div>
                <div className="mech-subtitle">非固定价格</div>
                {!fixedPrice && (
                  <p className="mech-note" style={{ marginBottom: '0.4rem' }}>
                    下方每个格子标注「最低–最高」万 w，与取消勾选「固定价格」后的随机区间一致。
                  </p>
                )}
                <div className="mech-icon-grid mech-icon-grid--labeled">
                  {varItems.map((it) => {
                    const fr = floatingPriceRangeW(it.valueW);
                    return (
                      <button
                        key={it.id}
                        type="button"
                        className="mech-icon-cell mech-icon-cell--with-label"
                        title={itemTooltipWithFloat(it, fixedPrice)}
                        onClick={() => handleDailyVarClick(it)}
                      >
                        <span className="mech-icon-cell-img-wrap">
                          <LedgerItemIcon
                            iconIndex={it.iconIndex}
                            emoji={it.emoji}
                            name={it.name}
                            iconFile={it.iconFile}
                            imageUrl={it.imageUrl}
                          />
                        </span>
                        <span className="mech-icon-cell-label-stack">
                          <span className="mech-icon-cell-label">{it.name}</span>
                          {!fixedPrice && (
                            <span className="mech-icon-cell-float-range">
                              {fr.min}–{fr.max} w
                            </span>
                          )}
                        </span>
                      </button>
                    );
                  })}
                </div>
                <div className="mech-check-row">
                  <label>
                    <input type="checkbox" checked={fixedPrice} onChange={(e) => setFixedPrice(e.target.checked)} />
                    固定价格
                  </label>
                  <label>
                    <input type="checkbox" checked={exactPrice} onChange={(e) => setExactPrice(e.target.checked)} />
                    精确价格
                  </label>
                </div>
              </>
            )}

            {mainTab === 'yaksha' && (
              <>
                <div className="mech-subtitle">白玩区</div>
                <div className="mech-icon-grid" style={{ maxWidth: 200 }}>
                  {yakWhiteItems.map((it) => (
                    <button key={it.id} type="button" className="mech-icon-cell" title={itemTooltip(it)}>
                      <LedgerItemIcon
                        iconIndex={it.iconIndex}
                        emoji={it.emoji}
                        name={it.name}
                        iconFile={it.iconFile}
                        imageUrl={it.imageUrl}
                      />
                    </button>
                  ))}
                </div>
                <p className="mech-note">不计算出龟率不用点（示意）</p>
                <div className="mech-subtitle">奖励区</div>
                <div className="mech-icon-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)', maxWidth: 320 }}>
                  {yakRewardItems.map((it) => (
                    <button
                      key={it.id}
                      type="button"
                      className="mech-icon-cell"
                      title={itemTooltip(it)}
                      onClick={() => onRewardIcon(it)}
                    >
                      <LedgerItemIcon
                        iconIndex={it.iconIndex}
                        emoji={it.emoji}
                        name={it.name}
                        iconFile={it.iconFile}
                        imageUrl={it.imageUrl}
                      />
                    </button>
                  ))}
                </div>
                <div className="mech-check-row">
                  <label>
                    <input type="checkbox" checked={fixedPrice} onChange={(e) => setFixedPrice(e.target.checked)} />
                    固定价格
                  </label>
                  <label>
                    <input type="checkbox" checked={exactPrice} onChange={(e) => setExactPrice(e.target.checked)} />
                    精确价格
                  </label>
                </div>
                <div className="mech-subtitle">夜叉信息显示</div>
                <div className="mech-stats-grid">
                  {YAKSHA_COUNTER_KEYS.map(({ key, label, color }) => (
                    <div key={key} className="mech-stat-card" style={{ borderColor: `${color}44` }}>
                      <span style={{ color }}>{label}</span>
                      <div className="mech-stat-ctrl">
                        <button type="button" aria-label={`${label}减`} onClick={() => bumpYaksha(key, -1)}>
                          −
                        </button>
                        <span className="mech-stat-val" style={{ color }}>
                          {yaksha[key] ?? 0}
                        </span>
                        <button type="button" aria-label={`${label}加`} onClick={() => bumpYaksha(key, 1)}>
                          +
                        </button>
                      </div>
                    </div>
                  ))}
                  {(['total', 'turtle', 'drop'] as const).map((key) => (
                    <div key={key} className="mech-stat-card">
                      <span style={{ color: '#94a3b8' }}>
                        {key === 'total' ? '总数' : key === 'turtle' ? '出龟' : '出货'}
                      </span>
                      <div className="mech-stat-ctrl">
                        <button type="button" onClick={() => bumpYaksha(key, -1)}>
                          −
                        </button>
                        <span className="mech-stat-val">{yaksha[key] ?? 0}</span>
                        <button type="button" onClick={() => bumpYaksha(key, 1)}>
                          +
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mech-summary-lines">
                  <div>含万年龟率（示意）: {yakshaRates.withWn}%</div>
                  <div>出龟率: {yakshaRates.turtleRate}%</div>
                  <div>出货率: {yakshaRates.dropRate}%</div>
                </div>
              </>
            )}

            {mainTab === 'scene' && (
              <>
                <div className="mech-subtitle">场景记录（占位）</div>
                <div className="mech-icon-grid">
                  {sceneItems.map((it) => (
                    <button
                      key={it.id}
                      type="button"
                      className="mech-icon-cell"
                      title={itemTooltipWithFloat(it, fixedPrice)}
                      onClick={() => handleSceneItemClick(it)}
                    >
                      <LedgerItemIcon
                        iconIndex={it.iconIndex}
                        emoji={it.emoji}
                        name={it.name}
                        iconFile={it.iconFile}
                        imageUrl={it.imageUrl}
                      />
                    </button>
                  ))}
                </div>
                <p className="mech-note">点击格子加入右侧今日收益列表，可与日常/夜叉共用。</p>
              </>
            )}
          </div>

          <div className="mech-panel-block">
            <div className="mech-right-head">
              <div className="mech-right-tabs mech-tabs">
                <button
                  type="button"
                  className={`mech-tab ${rightTab === 'today' ? 'active' : ''}`}
                  onClick={() => setRightTab('today')}
                >
                  今日收益
                </button>
                <button
                  type="button"
                  className={`mech-tab ${rightTab === 'history' ? 'active' : ''}`}
                  onClick={() => setRightTab('history')}
                >
                  历史收益
                </button>
              </div>
            </div>

            {rightTab === 'today' && (
              <>
                <div className="mech-table-wrap">
                  <table className="mech-table">
                    <thead>
                      <tr>
                        <th>物品</th>
                        <th className="num mech-table-col-price">单价(w)</th>
                        <th className="num mech-table-col-qty">数量</th>
                        <th className="num mech-table-col-sub">小计</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {todayLines.length === 0 ? (
                        <tr>
                          <td colSpan={5} style={{ color: '#5c6d7e', padding: '1rem' }}>
                            左侧点选图标，或使用顶部「语音录入」
                          </td>
                        </tr>
                      ) : (
                        todayLinesPg.slice.map((l) => (
                          <tr key={l.id}>
                            <td>{l.name}</td>
                            <td className="num mech-table-col-price">
                              <input
                                className="input mech-table-price-input"
                                type="number"
                                min={0}
                                step="0.1"
                                value={priceEditStrsByLineId[l.id] ?? String(l.valueW)}
                                onChange={(e) =>
                                  setPriceEditStrsByLineId((m) => ({ ...m, [l.id]: e.target.value }))
                                }
                                onBlur={() => void commitLineUnitPrice(l.id)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') {
                                    (e.currentTarget as HTMLInputElement).blur();
                                  }
                                }}
                                aria-label={`${l.name} 单价(w)`}
                              />
                            </td>
                            <td className="num mech-table-col-qty">{l.count}</td>
                            <td className="num mech-table-col-sub">{(l.valueW * l.count).toFixed(1)}</td>
                            <td>
                              <button type="button" className="mech-row-del" onClick={() => requestRemoveLine(l)}>
                                ✕
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                  <TablePaginationBar
                    page={todayLinesPg.page}
                    totalPages={todayLinesPg.totalPages}
                    total={todayLinesPg.total}
                    pageSize={todayLinesPg.pageSize}
                    onPageChange={todayLinesPg.setPage}
                    onPageSizeChange={todayLinesPg.setPageSize}
                  />
                </div>
                <div className="mech-total-bar">
                  <span>物品合计</span>
                  <span>{itemProfitW.toFixed(1)} w</span>
                </div>
              </>
            )}

            {rightTab === 'history' && (
              <div className="mech-table-wrap">
                {historyErr && <p style={{ color: 'var(--danger)', margin: '0.25rem 0 0.65rem' }}>{historyErr}</p>}
                {historyLoading && !historyErr && (
                  <p className="muted" style={{ margin: '0.25rem 0 0.65rem' }}>
                    加载中…
                  </p>
                )}
                <table className="mech-table">
                  <thead>
                    <tr>
                      <th>日期</th>
                      <th className="num">收益(元)</th>
                      <th>统计</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyPg.total === 0 ? (
                      <tr>
                        <td colSpan={3} style={{ color: '#5c6d7e', padding: '1rem' }}>
                          暂无历史记录（请先在某业务日点「保存收益」或录入物品/现金使其写入库）。
                        </td>
                      </tr>
                    ) : (
                      <>
                        {historyPg.slice.map((row) => (
                          <tr key={row.date}>
                            <td>{row.date}</td>
                            <td className="num">{row.profitYuan}</td>
                            <td>{row.note}</td>
                          </tr>
                        ))}
                      </>
                    )}
                  </tbody>
                </table>
                <TablePaginationBar
                  page={historyPg.page}
                  totalPages={historyPg.totalPages}
                  total={historyPg.total}
                  pageSize={historyPg.pageSize}
                  onPageChange={historyPg.setPage}
                  onPageSizeChange={historyPg.setPageSize}
                />
              </div>
            )}
          </div>
        </div>

        {clearTimerConfirmOpen && (
          <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setClearTimerConfirmOpen(false);
            }}
          >
            <div
              className="modal card mech-clear-timer-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="mech-clear-timer-title"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <h2 id="mech-clear-timer-title">确认清除？</h2>
              <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
                将清空本页：计时、今日收益表、夜叉、本金/现金等，并
                <strong style={{ color: '#e2e8f0' }}>停止计时（写入服务端 meta：runStartAt 置空）</strong>，随后
                <strong style={{ color: '#e2e8f0' }}>解锁记账台业务日并换日到今天</strong>。
                同一业务日<strong style={{ color: '#e2e8f0' }}>离开再进本页</strong>也不会用库里的数据自动填满，直至你再次录入物品或现金/本金（两）；之后照常同步到库。
              </p>
              <div className="mech-pick-actions">
                <button type="button" className="btn btn-primary" onClick={confirmClearLedger}>
                  确认清除
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setClearTimerConfirmOpen(false)}>
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {saveProfitConfirmOpen && (
          <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setSaveProfitConfirmOpen(false);
            }}
          >
            <div
              className="modal card mech-clear-timer-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="mech-save-profit-title"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <h2 id="mech-save-profit-title">保存当日正式收益？</h2>
              <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
                将把<strong style={{ color: '#e2e8f0' }}>物品行</strong>与当前{' '}
                <strong style={{ color: '#e2e8f0' }}>HUD</strong>
                （在线时长当前 {formatElapsed(elapsedSec)}、点卡累计、各队现金与本金、在线人数等）写入数据库，并更新
                <strong style={{ color: '#e2e8f0' }}>当日正式收益</strong>记录（含点卡快照时刻等）。与仅自动同步不同，此为完整「保存收益」落库。
                队伍现金须为有效数字或留空；
                <strong style={{ color: '#fbbf24' }}>任一步写入失败则不会完成正式快照</strong>。若该业务日已有正式保存，将被本次数据覆盖。
              </p>
              <div className="mech-pick-actions">
                <button type="button" className="btn btn-primary" onClick={confirmSaveProfit}>
                  保存收益
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setSaveProfitConfirmOpen(false)}>
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {saveBizDatePick && (
          <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setSaveBizDatePick(null);
            }}
          >
            <div
              className="modal card mech-clear-timer-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="mech-bizdate-pick-title"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <h2 id="mech-bizdate-pick-title">选择本次保存的业务日期</h2>
              <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
                现在处于跨天时段（23:59:59～06:00:00）。本次「保存收益」要落到哪一天？
              </p>
              <div className="mech-pick-actions" style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    const cb = saveBizDatePickCbRef.current;
                    const picked = saveBizDatePick.today;
                    setSaveBizDatePick(null);
                    saveBizDatePickCbRef.current = null;
                    cb?.(picked);
                  }}
                >
                  保存到今天（{saveBizDatePick.today}）
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    const cb = saveBizDatePickCbRef.current;
                    const picked = saveBizDatePick.yesterday;
                    setSaveBizDatePick(null);
                    saveBizDatePickCbRef.current = null;
                    cb?.(picked);
                  }}
                >
                  保存到昨天（{saveBizDatePick.yesterday}）
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setSaveBizDatePick(null);
                    saveBizDatePickCbRef.current = null;
                  }}
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {removeLineTarget && (
          <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setRemoveLineTarget(null);
            }}
          >
            <div
              className="modal card mech-clear-timer-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="mech-remove-line-title"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <h2 id="mech-remove-line-title">删除「{removeLineTarget.name}」</h2>
              <p style={{ margin: '0 0 0.75rem', fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
                当前数量 <strong>{removeLineTarget.count}</strong>。可<strong>全部删除</strong>，或输入数量后<strong>按数量减少</strong>
                （剩余 1 个及以上会保留该行）。
              </p>
              <div style={{ marginBottom: '0.85rem' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.8rem',
                    color: 'var(--text-dim)',
                    marginBottom: '0.35rem',
                  }}
                >
                  减少数量（1～{removeLineTarget.count}）
                </label>
                <input
                  className="input"
                  type="number"
                  min={1}
                  max={removeLineTarget.count}
                  value={removeQtyStr}
                  onChange={(e) => setRemoveQtyStr(e.target.value)}
                  style={{ maxWidth: '8rem' }}
                />
              </div>
              <div className="mech-pick-actions" style={{ flexWrap: 'wrap', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    removeLine(removeLineTarget.id);
                    setRemoveLineTarget(null);
                  }}
                >
                  全部删除
                </button>
                <button type="button" className="btn btn-ghost" onClick={confirmRemoveLineQty}>
                  按数量减少
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setRemoveLineTarget(null)}>
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {pickModal && (
          <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setPickModal(null);
            }}
          >
            <div
              className="modal card mech-pick-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="mech-pick-title"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <h2 id="mech-pick-title">
                {pickModal.kind === 'book'
                  ? '灵饰书：选择等级与种类'
                  : pickModal.kind === 'beast'
                    ? '兽决：选择种类'
                    : pickModal.kind === 'ruyi'
                      ? '如意丹：选择五行'
                      : `${pickModal.item.name}：选择等级`}
              </h2>
              <p style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                {pickModal.kind === 'book'
                  ? `单价优先用物品库灵饰书定价表；未设置时用格子价 ${pickModal.valueW} w。`
                  : pickModal.kind === 'beast'
                    ? `单价优先用物品库兽决种类定价；未设置时用格子价 ${pickModal.valueW} w。`
                    : pickModal.kind === 'ruyi'
                      ? `单价按物品库「如意丹」金木水火土分别定价；未设置时用格子价 ${pickModal.valueW} w。`
                      : `单价优先用物品库各等级定价；未设置时用格子价 ${pickModal.valueW} w。`}
              </p>
              {pickModal.kind === 'beast' ? (
                <fieldset className="mech-pick-radio-group" style={{ margin: '0.75rem 0 1rem' }}>
                  <legend>种类（万 w 价在物品库维护）</legend>
                  <div className="mech-pick-radios mech-pick-radios--stack mech-pick-radios--beast">
                    {loadBeastScrollRows().map((r) => (
                      <label key={r.id} className="mech-pick-radio-label">
                        <input
                          type="radio"
                          name="ledger-beast-type"
                          value={r.id}
                          checked={pickBeastId === r.id}
                          onChange={() => setPickBeastId(r.id)}
                        />
                        <span>{r.label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              ) : pickModal.kind === 'ruyi' ? (
                <fieldset className="mech-pick-radio-group" style={{ margin: '0.75rem 0 1rem' }}>
                  <legend>五行</legend>
                  <div className="mech-pick-radios">
                    {RUYI_ELEMENTS.map((el) => (
                      <label key={el} className="mech-pick-radio-label">
                        <input
                          type="radio"
                          name="ledger-ruyi-element"
                          value={el}
                          checked={pickRuyiElement === el}
                          onChange={() => setPickRuyiElement(el)}
                        />
                        <span>{el}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              ) : (
                <div className="mech-pick-form">
                  <fieldset className="mech-pick-radio-group">
                    <legend>等级</legend>
                    <div className="mech-pick-radios mech-pick-radios--stack">
                      {(pickModal.kind === 'book'
                        ? LEDGER_LEVEL_OPTIONS
                        : getLedgerPickLevelOptions(pickModal.item.name)
                      ).map((lv) => (
                        <label key={lv} className="mech-pick-radio-label">
                          <input
                            type="radio"
                            name="mech-pick-level"
                            value={lv}
                            checked={pickLevel === lv}
                            onChange={() => setPickLevel(lv)}
                          />
                          <span>{lv} 级</span>
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  {pickModal.kind === 'book' && (
                    <fieldset className="mech-pick-radio-group">
                      <legend>种类</legend>
                      <div className="mech-pick-radios">
                        {LEDGER_LINGSHI_TYPES.map((t) => (
                          <label key={t} className="mech-pick-radio-label">
                            <input
                              type="radio"
                              name="ledger-lingshi-type"
                              value={t}
                              checked={pickBookType === t}
                              onChange={() => setPickBookType(t)}
                            />
                            <span>{t}</span>
                          </label>
                        ))}
                      </div>
                    </fieldset>
                  )}
                </div>
              )}
              <p className="mech-pick-preview">
                将按 <strong>{pickPreviewW.toFixed(2)} w</strong> 计入右侧「今日收益」列表
                {pickModal.kind === 'ruyi' ? '（改五行会即时变化）' : '（改等级/种类会即时变化）'}
              </p>
              <div className="mech-pick-actions">
                <button type="button" className="btn btn-primary" onClick={confirmPickModal}>
                  加入今日
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setPickModal(null)}>
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {toast && (
          <div
            style={{
              position: 'fixed',
              bottom: 24,
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 100,
              padding: '0.5rem 1rem',
              background: 'rgba(0,30,40,0.95)',
              border: '1px solid #00e5ff',
              color: '#00e5ff',
              fontSize: '0.75rem',
              boxShadow: '0 0 20px rgba(0,229,255,0.3)',
            }}
          >
            {toast}
          </div>
        )}
      </div>
    </div>
  );
}
