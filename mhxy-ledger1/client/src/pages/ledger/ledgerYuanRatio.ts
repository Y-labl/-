/**
 * 记账台：金价档位固定为「LEDGER_GAME_WAN_ANCHOR 万游戏币 ↔ 人民币」；
 * 只维护人民币金额，每 1 w 折合元 = yuan ÷ LEDGER_GAME_WAN_ANCHOR。与「每日收益」共用。
 * 持久化在服务端 mech_ledger_user_prefs；内存缓存，不写浏览器。
 */

import { api } from '../../api';

/** 金价锚定：多少「万」游戏币对应下面维护的人民币（当前固定 3000 万） */
export const LEDGER_GAME_WAN_ANCHOR = 3000;

export type LedgerGameYuanPair = {
  gameWan: number;
  yuan: number;
};

/** 人民币金额保留两位小数 */
export function roundLedgerYuan2(yuan: number): number {
  if (!Number.isFinite(yuan) || yuan < 0) return 0;
  return Math.round(yuan * 100) / 100;
}

function normalizePairToAnchor(gameWan: number, yuan: number): LedgerGameYuanPair | null {
  if (!Number.isFinite(gameWan) || gameWan <= 0 || !Number.isFinite(yuan) || yuan < 0) return null;
  const scaledYuan = (yuan / gameWan) * LEDGER_GAME_WAN_ANCHOR;
  return { gameWan: LEDGER_GAME_WAN_ANCHOR, yuan: roundLedgerYuan2(scaledYuan) };
}

/** 默认：3000 万 = 30 元 → 每 w 0.01 元，与早期示意一致 */
export const LEDGER_GAME_YUAN_DEFAULT: LedgerGameYuanPair = {
  gameWan: LEDGER_GAME_WAN_ANCHOR,
  yuan: 30,
};

let yuanMemory: LedgerGameYuanPair = { ...LEDGER_GAME_YUAN_DEFAULT };

/** 仅更新内存并广播，不请求服务端 */
export function writeGameYuanPairLocalOnly(pair: LedgerGameYuanPair): void {
  const norm = normalizePairToAnchor(Number(pair.gameWan), Number(pair.yuan));
  if (!norm) return;
  yuanMemory = { gameWan: norm.gameWan, yuan: norm.yuan };
}

export function loadGameYuanPair(): LedgerGameYuanPair {
  const norm = normalizePairToAnchor(yuanMemory.gameWan, yuanMemory.yuan);
  return norm ?? { ...LEDGER_GAME_YUAN_DEFAULT };
}

export function saveGameYuanPair(pair: LedgerGameYuanPair): void {
  const norm = normalizePairToAnchor(Number(pair.gameWan), Number(pair.yuan));
  if (!norm) return;
  yuanMemory = { gameWan: norm.gameWan, yuan: norm.yuan };
  try {
    window.dispatchEvent(new CustomEvent('mhxy-ledger-yuan-ratio'));
  } catch {
    /* ignore */
  }
  void api.mechLedgerPrefsPut({ yuan: norm.yuan }).catch(() => {});
}

/**
 * 登录后进 App 同步金价：以库为准；若无库记录则写入当前内存默认并落库。
 */
function tryReadLegacyYuanLocalStorage(): LedgerGameYuanPair | null {
  try {
    const raw = localStorage.getItem('mhxy_ledger_game_yuan_pair_v2');
    if (!raw?.trim()) return null;
    const o = JSON.parse(raw) as { gameWan?: number; yuan?: number };
    return normalizePairToAnchor(Number(o.gameWan), Number(o.yuan));
  } catch {
    return null;
  }
}

/**
 * 须在 `hydrateClientPrefs` 之前调用，以便读取 `mhxy_ledger_game_yuan_pair_v2` 后由后者 sweep 清掉。
 */
export async function hydrateGameYuanPairFromServer(): Promise<boolean> {
  try {
    const prefs = await api.mechLedgerPrefsGet();
    if (prefs.persisted) {
      const norm = normalizePairToAnchor(prefs.gameWan, prefs.yuan);
      if (!norm) return false;
      yuanMemory = norm;
      window.dispatchEvent(new CustomEvent('mhxy-ledger-yuan-ratio'));
      return true;
    }
    const fromLs = tryReadLegacyYuanLocalStorage();
    if (fromLs) {
      yuanMemory = fromLs;
      await api.mechLedgerPrefsPut({ yuan: fromLs.yuan });
      window.dispatchEvent(new CustomEvent('mhxy-ledger-yuan-ratio'));
      return true;
    }
    const local = loadGameYuanPair();
    await api.mechLedgerPrefsPut({ yuan: local.yuan });
    window.dispatchEvent(new CustomEvent('mhxy-ledger-yuan-ratio'));
    return true;
  } catch {
    return false;
  }
}

export function yuanPerWFromPair(pair: LedgerGameYuanPair): number {
  const { gameWan, yuan } = pair;
  if (!Number.isFinite(gameWan) || gameWan <= 0) return 0;
  if (!Number.isFinite(yuan) || yuan < 0) return 0;
  return yuan / gameWan;
}

export function loadYuanPerWanW(): number {
  return yuanPerWFromPair(loadGameYuanPair());
}

export function itemWTotalToYuan(itemWTotal: number, yuanPerW?: number): number {
  const rate = yuanPerW ?? loadYuanPerWanW();
  return itemWTotal * rate;
}
