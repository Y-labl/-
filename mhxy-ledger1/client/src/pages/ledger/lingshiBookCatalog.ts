import { getClientPrefsSnapshot, patchClientPrefs } from '../../utils/clientPrefsStore';
import {
  LEDGER_LINGSHI_TYPES,
  LEDGER_LEVEL_OPTIONS,
  LEDGER_PICK_BOOK_ITEM_NAME,
  buildLedgerPickedDisplayName,
} from './ledgerSpecialPick';

export type LingshiBookType = (typeof LEDGER_LINGSHI_TYPES)[number];

/**
 * 灵饰书：等级 × 种类 → 单价（万 w）
 * 默认见 LINGSHI_BOOK_PRICE_MATRIX；改价存服务端 user_client_prefs。
 */
export const LINGSHI_BOOK_PRICE_MATRIX: Record<string, Record<LingshiBookType, number>> = {
  '60': { 戒指: 12, 耳饰: 13, 手镯: 14, 配饰: 11 },
  '80': { 戒指: 28, 耳饰: 30, 手镯: 32, 配饰: 26 },
  '100': { 戒指: 55, 耳饰: 58, 手镯: 62, 配饰: 50 },
  '120': { 戒指: 85, 耳饰: 92, 手镯: 98, 配饰: 78 },
  '140': { 戒指: 2200, 耳饰: 2200, 手镯: 350, 配饰: 430 },
};

function cloneDefaultLingshiMatrix(): Record<string, Record<LingshiBookType, number>> {
  const out: Record<string, Record<LingshiBookType, number>> = {};
  for (const lv of LEDGER_LEVEL_OPTIONS) {
    out[lv] = { ...LINGSHI_BOOK_PRICE_MATRIX[lv] };
  }
  return out;
}

/** 合并本地缓存与默认表（物品库弹窗编辑后会 save） */
export function loadLingshiBookMatrix(): Record<string, Record<LingshiBookType, number>> {
  const base = cloneDefaultLingshiMatrix();
  try {
    const parsed = getClientPrefsSnapshot().lingshiBookMatrix;
    if (!parsed) return base;
    for (const lv of LEDGER_LEVEL_OPTIONS) {
      const row = parsed[lv];
      if (!row || typeof row !== 'object') continue;
      for (const t of LEDGER_LINGSHI_TYPES) {
        const n = Number(row[t]);
        if (Number.isFinite(n) && n >= 0) base[lv][t] = n;
      }
    }
  } catch {
    /* ignore */
  }
  return base;
}

export function saveLingshiBookMatrix(m: Record<string, Record<LingshiBookType, number>>): void {
  patchClientPrefs({ lingshiBookMatrix: JSON.parse(JSON.stringify(m)) as Record<string, Record<string, number>> });
}

export function getPriceFromMatrix(
  matrix: Record<string, Record<LingshiBookType, number>>,
  level: string,
  bookType: string
): number {
  const row = matrix[level.trim()];
  if (!row) return 0;
  const v = row[bookType as LingshiBookType];
  return Number.isFinite(v) ? v : 0;
}

export function getLingshiBookPrice(level: string, bookType: string): number {
  return getPriceFromMatrix(loadLingshiBookMatrix(), level, bookType);
}

/** 解析「灵饰书 · 120级 · 戒指」 */
export function parseLingshiBookDisplayName(name: string): { level: string; type: LingshiBookType } | null {
  const m = name
    .trim()
    .match(/^灵饰书\s*·\s*(\d+)\s*级\s*·\s*(戒指|耳饰|手镯|配饰)\s*$/);
  if (!m) return null;
  const type = m[2] as LingshiBookType;
  if (!(LEDGER_LINGSHI_TYPES as readonly string[]).includes(type)) return null;
  return { level: m[1], type };
}

export function isLingshiBookCatalogName(name: string): boolean {
  const t = name.trim();
  return t === LEDGER_PICK_BOOK_ITEM_NAME || parseLingshiBookDisplayName(t) !== null;
}

export { LEDGER_LEVEL_OPTIONS, LEDGER_LINGSHI_TYPES, LEDGER_PICK_BOOK_ITEM_NAME, buildLedgerPickedDisplayName };
