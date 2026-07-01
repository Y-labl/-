/**
 * 用户客户端偏好：持久化在 MySQL `user_client_prefs`（接口 GET/PUT `/api/me/client-prefs`）。
 * 登录后由 `hydrateClientPrefs()`（在 `AppShell` 里调用）：
 *   1. 拉取服务端 prefs 写入内存；
 *   2. `migrateArtifactGuideFromLocalStorage`：旧 `mhxy_artifact_guide_v1` → 表 `artifact_guide_state`；
 *   3. 读取 localStorage/sessionStorage 遗留项合并进 prefs，必要时 PUT（带重试）；
 *   4. `migrateMechLedgerTimerFromLocalStorage`：旧 `mhxy_mech_ledger_timer_v1` → `mech_ledger_day_meta`；
 *   5. `sweepLegacyBrowserStorage()` 删除所有 `mhxy_` 前缀的 localStorage/sessionStorage（保留 `mhxy_ledger_token`）。
 * 运行时读写在内存 `prefsInternal`，变更经 `patchClientPrefs` 立即 PUT（串行队列）。
 */
import { api } from '../api';
import { migrateArtifactGuideFromLocalStorage } from './artifactGuideLegacyMigrate';
import { migrateMechLedgerTimerFromLocalStorage } from './mechLedgerLegacyMigrate';
import { isValidYmd, defaultBizDateNow } from './bizDate';
import {
  DEFAULT_UI_THEME,
  UI_THEME_STORAGE_KEY,
  applyUiThemeToDocument,
  isUiThemeId,
  readBootstrapUiTheme,
  resolvedUiThemeFromPrefs,
  type UiThemeId,
} from '../theme/uiTheme';

const PAGE_BIZ_IDS = [
  'ledger',
  'overview',
  'tasks',
  'consumption',
  'artifactGuide',
  'mechDaily',
] as const;

export type PageBizDateId = (typeof PAGE_BIZ_IDS)[number];

export type UserClientPrefs = {
  v?: number;
  pageBizDates?: Partial<Record<PageBizDateId, string>>;
  ledgerBizDateLocked?: boolean;
  tablePageSize?: number;
  taskCompleteChainEnd?: Record<string, string>;
  taskPrestartSticky?: Record<string, string[]>;
  beastScrollV2?: { v: number; rows: unknown[] };
  tierPrices?: Record<string, Record<string, number>>;
  ruyiDanPrices?: Record<string, number>;
  lingshiBookMatrix?: Record<string, Record<string, number>>;
  /** 旧版 HUD 会话标记，原 localStorage mhxy_ledger_hud_session_consumed* */
  ledgerHudSessionConsumed?: string;
  ledgerHudSessionConsumedV2?: string;
  /** 前端界面主题：赛博风 / 梦幻风，持久化在 prefs_json */
  uiTheme?: UiThemeId;
};

export const DEFAULT_CLIENT_PREFS: UserClientPrefs = {
  v: 1,
  pageBizDates: {},
  ledgerBizDateLocked: false,
  tablePageSize: 20,
  taskCompleteChainEnd: {},
  taskPrestartSticky: {},
  tierPrices: {},
};

const LEGACY_KEYS_EXACT = [
  'mhxy_app_biz_date_v1',
  'mhxy_app_biz_date_locked_v1',
  'mhxy_page_biz_date_locked_ledger_v1',
  'mhxy-ledger-table-page-size',
  'mhxy_ledger-table-page-size',
  'mhxy_ledger_game_yuan_pair_v2',
  'mhxy_ledger_yuan_per_wan_w_v1',
  'mhxy_artifact_guide_v1',
  'mhxy_beast_scroll_prices_v1',
  'mhxy_beast_scroll_prices_v2',
  'mhxy_ruyi_dan_prices_v1',
  'mhxy_lingshi_book_price_matrix_v1',
  'mhxy_mech_ledger_timer_v1',
  'mhxy_ledger_hud_session_consumed',
  'mhxy_ledger_hud_session_consumed_v2',
] as const;

const BROWSER_TOKEN_KEY = 'mhxy_ledger_token';

const PAGE_BIZ_PREFIX = 'mhxy_page_biz_date_v1:';
const TIER_PREFIX = 'mhxy_tier_prices_';
const TASK_CHAIN_PREFIX = 'mhxy_task_complete_chain_end_';
const PRESTART_SESSION_PREFIX = 'mhxy_prestart_remind_sticky_v1_';

function isPlainObject(x: unknown): x is Record<string, unknown> {
  return x !== null && typeof x === 'object' && !Array.isArray(x);
}

function clonePrefs(base: UserClientPrefs): UserClientPrefs {
  return JSON.parse(JSON.stringify(base)) as UserClientPrefs;
}

function mergePrefs(prev: UserClientPrefs, patch: Partial<UserClientPrefs>): UserClientPrefs {
  const out = clonePrefs(prev);
  if (patch.pageBizDates) {
    out.pageBizDates = { ...out.pageBizDates, ...patch.pageBizDates };
  }
  if (patch.taskCompleteChainEnd) {
    out.taskCompleteChainEnd = { ...out.taskCompleteChainEnd, ...patch.taskCompleteChainEnd };
  }
  if (patch.taskPrestartSticky) {
    out.taskPrestartSticky = { ...out.taskPrestartSticky, ...patch.taskPrestartSticky };
  }
  if (patch.tierPrices) {
    out.tierPrices = { ...out.tierPrices, ...patch.tierPrices };
  }
  if (patch.v !== undefined) out.v = patch.v;
  if (patch.ledgerBizDateLocked !== undefined) out.ledgerBizDateLocked = patch.ledgerBizDateLocked;
  if (patch.tablePageSize !== undefined) out.tablePageSize = patch.tablePageSize;
  if (patch.beastScrollV2 !== undefined) out.beastScrollV2 = patch.beastScrollV2;
  if (patch.ruyiDanPrices !== undefined) out.ruyiDanPrices = patch.ruyiDanPrices;
  if (patch.lingshiBookMatrix !== undefined) out.lingshiBookMatrix = patch.lingshiBookMatrix;
  if (patch.ledgerHudSessionConsumed !== undefined) out.ledgerHudSessionConsumed = patch.ledgerHudSessionConsumed;
  if (patch.ledgerHudSessionConsumedV2 !== undefined) out.ledgerHudSessionConsumedV2 = patch.ledgerHudSessionConsumedV2;
  if (patch.uiTheme !== undefined) {
    out.uiTheme = isUiThemeId(patch.uiTheme) ? patch.uiTheme : DEFAULT_UI_THEME;
  }
  return out;
}

let prefsInternal: UserClientPrefs = clonePrefs(DEFAULT_CLIENT_PREFS);
let hydrated = false;
const listeners = new Set<() => void>();
let saveChain: Promise<void> = Promise.resolve();
let lastSavedPayloadJson: string | null = null;
let inFlightPayloadJson: string | null = null;

export function subscribeClientPrefs(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function notifyAll(): void {
  listeners.forEach((cb) => {
    try {
      cb();
    } catch {
      /* ignore */
    }
  });
}

export function getClientPrefsSnapshot(): UserClientPrefs {
  return mergePrefs(DEFAULT_CLIENT_PREFS, prefsInternal);
}

export function isClientPrefsHydrated(): boolean {
  return hydrated;
}

export function clearClientPrefsMemory(): void {
  prefsInternal = clonePrefs(DEFAULT_CLIENT_PREFS);
  hydrated = false;
  lastSavedPayloadJson = null;
  inFlightPayloadJson = null;
  notifyAll();
  applyUiThemeToDocument(readBootstrapUiTheme());
}

export function patchClientPrefs(partial: Partial<UserClientPrefs>): void {
  const prev = getClientPrefsSnapshot();
  const next = mergePrefs(prev, partial);

  let prevJson = '';
  let nextJson = '';
  try {
    prevJson = JSON.stringify(prev);
    nextJson = JSON.stringify(next);
  } catch {
    /* ignore */
  }
  if (prevJson && nextJson && prevJson === nextJson) {
    if (partial.uiTheme !== undefined) {
      applyUiThemeToDocument(resolvedUiThemeFromPrefs(prev.uiTheme));
    }
    return;
  }

  prefsInternal = next;
  notifyAll();
  if (partial.uiTheme !== undefined) {
    applyUiThemeToDocument(resolvedUiThemeFromPrefs(prefsInternal.uiTheme));
  }
  void enqueueClientPrefsSave(getClientPrefsSnapshot());
}

function enqueueClientPrefsSave(payload: UserClientPrefs): Promise<void> {
  let payloadJson: string;
  try {
    payloadJson = JSON.stringify(payload);
  } catch {
    payloadJson = '';
  }

  if (payloadJson && payloadJson === lastSavedPayloadJson) {
    return saveChain;
  }
  if (payloadJson && payloadJson === inFlightPayloadJson) {
    return saveChain;
  }

  saveChain = saveChain
    .catch(() => {})
    .then(() => {
      if (payloadJson && payloadJson === lastSavedPayloadJson) return;
      inFlightPayloadJson = payloadJson || null;
      return api.clientPrefsPut({ prefs: payload as Record<string, unknown> })
        .then(() => {
          if (payloadJson) lastSavedPayloadJson = payloadJson;
        })
        .finally(() => {
          if (inFlightPayloadJson === payloadJson) inFlightPayloadJson = null;
        });
    })
    .then(() => {})
    .catch(() => {});
  return saveChain;
}

/** 立即写入（离页、敏感操作） */
export function flushClientPrefsNow(): Promise<void> {
  const payload = getClientPrefsSnapshot();
  return enqueueClientPrefsSave(payload);
}

function collectLegacyLocalStoragePatch(): Partial<UserClientPrefs> {
  const patch: Partial<UserClientPrefs> = {};
  try {
    const dates: Partial<Record<PageBizDateId, string>> = {};
    for (const id of PAGE_BIZ_IDS) {
      const v = localStorage.getItem(`${PAGE_BIZ_PREFIX}${id}`);
      if (isValidYmd(v)) dates[id] = v;
    }
    const leg = localStorage.getItem('mhxy_app_biz_date_v1');
    if (isValidYmd(leg)) {
      for (const id of PAGE_BIZ_IDS) {
        if (!dates[id]) dates[id] = leg;
      }
    }
    if (Object.keys(dates).length) patch.pageBizDates = dates;

    if (
      localStorage.getItem('mhxy_page_biz_date_locked_ledger_v1') === '1' ||
      localStorage.getItem('mhxy_app_biz_date_locked_v1') === '1'
    ) {
      patch.ledgerBizDateLocked = true;
    }

    const tps =
      localStorage.getItem('mhxy-ledger-table-page-size') ??
      localStorage.getItem('mhxy_ledger-table-page-size');
    const n = Number(tps);
    if (Number.isFinite(n) && [10, 20, 50, 100].includes(n)) {
      patch.tablePageSize = n;
    }

    const chain: Record<string, string> = {};
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (!k?.startsWith(TASK_CHAIN_PREFIX)) continue;
      const biz = k.slice(TASK_CHAIN_PREFIX.length);
      const v = localStorage.getItem(k);
      if (v && /^\d{4}-\d{2}-\d{2}T/.test(v)) chain[biz] = v;
    }
    if (Object.keys(chain).length) patch.taskCompleteChainEnd = chain;

    const sticky: Record<string, string[]> = {};
    try {
      for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        if (!k?.startsWith(PRESTART_SESSION_PREFIX)) continue;
        const biz = k.slice(PRESTART_SESSION_PREFIX.length);
        const raw = sessionStorage.getItem(k);
        if (!raw) continue;
        try {
          const arr = JSON.parse(raw) as unknown;
          if (Array.isArray(arr)) sticky[biz] = arr.map((x) => String(x));
        } catch {
          /* ignore */
        }
      }
    } catch {
      /* ignore */
    }
    if (Object.keys(sticky).length) patch.taskPrestartSticky = sticky;

    const beastRaw = localStorage.getItem('mhxy_beast_scroll_prices_v2');
    if (beastRaw) {
      try {
        const o = JSON.parse(beastRaw) as { v?: number; rows?: unknown };
        if (o && Array.isArray(o.rows)) patch.beastScrollV2 = { v: 2, rows: o.rows };
      } catch {
        /* ignore */
      }
    }

    const tier: Record<string, Record<string, number>> = {};
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (!k?.startsWith(TIER_PREFIX)) continue;
      const sk = k.slice(TIER_PREFIX.length);
      const raw = localStorage.getItem(k);
      if (!raw) continue;
      try {
        const o = JSON.parse(raw) as Record<string, unknown>;
        const out: Record<string, number> = {};
        for (const [lv, val] of Object.entries(o)) {
          const num = Number(val);
          if (Number.isFinite(num) && num >= 0) out[lv] = num;
        }
        if (Object.keys(out).length) tier[sk] = out;
      } catch {
        /* ignore */
      }
    }
    if (Object.keys(tier).length) patch.tierPrices = tier;

    const ruyiRaw = localStorage.getItem('mhxy_ruyi_dan_prices_v1');
    if (ruyiRaw) {
      try {
        const o = JSON.parse(ruyiRaw) as Record<string, unknown>;
        const out: Record<string, number> = {};
        for (const [kk, val] of Object.entries(o)) {
          const num = Number(val);
          if (Number.isFinite(num) && num >= 0) out[kk] = num;
        }
        if (Object.keys(out).length) patch.ruyiDanPrices = out;
      } catch {
        /* ignore */
      }
    }

    const lingRaw = localStorage.getItem('mhxy_lingshi_book_price_matrix_v1');
    if (lingRaw) {
      try {
        const o = JSON.parse(lingRaw) as Record<string, unknown>;
        if (isPlainObject(o)) {
          const mat: Record<string, Record<string, number>> = {};
          for (const [lv, row] of Object.entries(o)) {
            if (!isPlainObject(row)) continue;
            const r: Record<string, number> = {};
            for (const [t, val] of Object.entries(row)) {
              const num = Number(val);
              if (Number.isFinite(num) && num >= 0) r[t] = num;
            }
            if (Object.keys(r).length) mat[lv] = r;
          }
          if (Object.keys(mat).length) patch.lingshiBookMatrix = mat;
        }
      } catch {
        /* ignore */
      }
    }

    const hud1 = localStorage.getItem('mhxy_ledger_hud_session_consumed');
    if (hud1 != null && hud1 !== '') patch.ledgerHudSessionConsumed = hud1;
    const hud2 = localStorage.getItem('mhxy_ledger_hud_session_consumed_v2');
    if (hud2 != null && hud2 !== '') patch.ledgerHudSessionConsumedV2 = hud2;
  } catch {
    /* ignore */
  }
  return patch;
}

function legacyPatchMeaningful(patch: Partial<UserClientPrefs>): boolean {
  if (patch.pageBizDates && Object.keys(patch.pageBizDates).length) return true;
  if (patch.ledgerBizDateLocked) return true;
  if (patch.tablePageSize != null && patch.tablePageSize !== DEFAULT_CLIENT_PREFS.tablePageSize) return true;
  if (patch.taskCompleteChainEnd && Object.keys(patch.taskCompleteChainEnd).length) return true;
  if (patch.taskPrestartSticky && Object.keys(patch.taskPrestartSticky).length) return true;
  if (patch.beastScrollV2?.rows?.length) return true;
  if (patch.tierPrices && Object.keys(patch.tierPrices).length) return true;
  if (patch.ruyiDanPrices && Object.keys(patch.ruyiDanPrices).length) return true;
  if (patch.lingshiBookMatrix && Object.keys(patch.lingshiBookMatrix).length) return true;
  if (patch.ledgerHudSessionConsumed !== undefined) return true;
  if (patch.ledgerHudSessionConsumedV2 !== undefined) return true;
  return false;
}

function resolveLedgerBizDateForHydrate(prefs: UserClientPrefs): string {
  const d = prefs.pageBizDates?.ledger;
  if (isValidYmd(d)) return d;
  return defaultBizDateNow();
}

async function putClientPrefsMerged(attempts = 3): Promise<boolean> {
  const payload = getClientPrefsSnapshot() as Record<string, unknown>;
  for (let i = 0; i < attempts; i++) {
    try {
      await api.clientPrefsPut({ prefs: payload });
      return true;
    } catch {
      if (i < attempts - 1) {
        await new Promise((r) => setTimeout(r, 350 * (i + 1)));
      }
    }
  }
  return false;
}

function sweepLegacyBrowserStorage(): void {
  try {
    for (const k of LEGACY_KEYS_EXACT) {
      try {
        localStorage.removeItem(k);
      } catch {
        /* ignore */
      }
    }
    const toRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (!k) continue;
      if (
        k.startsWith(PAGE_BIZ_PREFIX) ||
        k.startsWith(TASK_CHAIN_PREFIX) ||
        k.startsWith(TIER_PREFIX)
      ) {
        toRemove.push(k);
      }
    }
    for (const k of toRemove) {
      try {
        localStorage.removeItem(k);
      } catch {
        /* ignore */
      }
    }
    const ssRemove: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const k = sessionStorage.key(i);
      if (k?.startsWith(PRESTART_SESSION_PREFIX)) ssRemove.push(k);
    }
    for (const k of ssRemove) {
      try {
        sessionStorage.removeItem(k);
      } catch {
        /* ignore */
      }
    }

    const lsMhxy: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (!k || k === BROWSER_TOKEN_KEY || k === UI_THEME_STORAGE_KEY) continue;
      if (k.startsWith('mhxy_') || k.startsWith('mhxy-')) lsMhxy.push(k);
    }
    for (const k of lsMhxy) {
      try {
        localStorage.removeItem(k);
      } catch {
        /* ignore */
      }
    }

    const ssMhxy: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const k = sessionStorage.key(i);
      if (!k || (!k.startsWith('mhxy_') && !k.startsWith('mhxy-'))) continue;
      ssMhxy.push(k);
    }
    for (const k of ssMhxy) {
      try {
        sessionStorage.removeItem(k);
      } catch {
        /* ignore */
      }
    }
  } catch {
    /* ignore */
  }
}

export async function hydrateClientPrefs(): Promise<void> {
  /** GET 成功则说明服务端可用：legacy 已读入内存后即可删浏览器，与 PUT 是否成功无关（后续操作会再 PUT）。 */
  let sweepAfterSuccessfulPrefsGet = false;
  try {
    const { prefs } = await api.clientPrefsGet();
    sweepAfterSuccessfulPrefsGet = true;
    const fromServer =
      prefs && typeof prefs === 'object' && !Array.isArray(prefs)
        ? (prefs as unknown as UserClientPrefs)
        : {};
    prefsInternal = mergePrefs(DEFAULT_CLIENT_PREFS, fromServer);

    const legacy = collectLegacyLocalStoragePatch();
    if (legacyPatchMeaningful(legacy)) {
      prefsInternal = mergePrefs(prefsInternal, legacy);
    }

    await migrateArtifactGuideFromLocalStorage();
    await migrateMechLedgerTimerFromLocalStorage(resolveLedgerBizDateForHydrate(prefsInternal));

    if (legacyPatchMeaningful(legacy)) {
      await putClientPrefsMerged();
    }

    hydrated = true;
    notifyAll();
  } catch {
    prefsInternal = mergePrefs(DEFAULT_CLIENT_PREFS, collectLegacyLocalStoragePatch());
    hydrated = true;
    notifyAll();
  } finally {
    applyUiThemeToDocument(resolvedUiThemeFromPrefs(getClientPrefsSnapshot().uiTheme));
    if (sweepAfterSuccessfulPrefsGet) {
      sweepLegacyBrowserStorage();
    }
  }
}

/** 供 pageBizDate：记账台未锁定时的「应对齐到今天」逻辑 */
export function getDefaultBizDateForInit(): string {
  return defaultBizDateNow();
}

export { PAGE_BIZ_IDS, PAGE_BIZ_PREFIX, TASK_CHAIN_PREFIX, PRESTART_SESSION_PREFIX };
