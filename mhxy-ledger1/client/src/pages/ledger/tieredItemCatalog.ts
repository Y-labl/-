/**
 * 物品库 / 记账台：仅按等级定价、无种类的物品（晶石、附魔宝珠、珍珠、炼妖石、种子）
 * 定价存服务端 user_client_prefs.tierPrices。
 */

import { getClientPrefsSnapshot, patchClientPrefs } from '../../utils/clientPrefsStore';

export type TieredPickBaseName = '晶石' | '附魔宝珠' | '珍珠' | '炼妖石' | '种子';

/** 与 ledger 灵饰书/晶石共用 60–140 */
export const JINGSHI_STONE_LEVELS = ['60', '80', '100', '120', '140'] as const;

export const FUMO_ORB_LEVELS = ['80', '100', '110', '120', '130', '140', '150', '160'] as const;

export const PEARL_LEVELS = [
  '50',
  '60',
  '70',
  '80',
  '90',
  '100',
  '110',
  '120',
  '130',
  '140',
  '150',
  '160',
] as const;

export const LIANYAO_STONE_LEVELS = ['105', '115', '125', '135', '145'] as const;

/** 摇钱树等：物品库基础名「种子」，2/3/4 级分档 */
export const SEED_LEVELS = ['2', '3', '4'] as const;

function defaultsFromLevels(levels: readonly string[], start: number, step: number): Record<string, number> {
  const o: Record<string, number> = {};
  levels.forEach((lv, i) => {
    o[lv] = Math.round((start + i * step) * 100) / 100;
  });
  return o;
}

export const TIERED_ITEM_CONFIG: Record<
  TieredPickBaseName,
  { levels: readonly string[]; defaults: Record<string, number>; storageKey: string }
> = {
  晶石: {
    levels: JINGSHI_STONE_LEVELS as unknown as string[],
    defaults: {
      '60': 30,
      '80': 190,
      '100': 352,
      '120': 725,
      '140': 725,
    },
    storageKey: 'jing_shi',
  },
  附魔宝珠: {
    levels: FUMO_ORB_LEVELS as unknown as string[],
    defaults: {
      '80': 1120,
      '100': 2310,
      '110': 2100,
      '120': 2150,
      '130': 3700,
      '140': 4000,
      '150': 4000,
      '160': 7000,
    },
    storageKey: 'fumo_orb',
  },
  珍珠: {
    levels: PEARL_LEVELS as unknown as string[],
    defaults: defaultsFromLevels(PEARL_LEVELS, 3, 2),
    storageKey: 'pearl',
  },
  炼妖石: {
    levels: LIANYAO_STONE_LEVELS as unknown as string[],
    defaults: defaultsFromLevels(LIANYAO_STONE_LEVELS, 12, 5),
    storageKey: 'lianyao',
  },
  种子: {
    levels: SEED_LEVELS as unknown as string[],
    defaults: { '2': 3, '3': 8, '4': 25 },
    storageKey: 'seed',
  },
};

export function isTieredPickBaseName(name: string): name is TieredPickBaseName {
  return Object.prototype.hasOwnProperty.call(TIERED_ITEM_CONFIG, name.trim());
}

export function getTieredLevelsForItem(itemName: string): readonly string[] | null {
  const b = itemName.trim() as TieredPickBaseName;
  return TIERED_ITEM_CONFIG[b]?.levels ?? null;
}

export function parseTieredCatalogDisplayName(
  name: string
): { base: TieredPickBaseName; level: string } | null {
  const t = name.trim();
  for (const base of Object.keys(TIERED_ITEM_CONFIG) as TieredPickBaseName[]) {
    const esc = base.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`^${esc}\\s*·\\s*(\\d+)\\s*级\\s*$`);
    const m = t.match(re);
    if (m) return { base, level: m[1] };
  }
  return null;
}

export function isTieredCatalogName(name: string): boolean {
  const t = name.trim();
  return isTieredPickBaseName(t) || parseTieredCatalogDisplayName(t) !== null;
}

function cloneDefaults(base: TieredPickBaseName): Record<string, number> {
  return { ...TIERED_ITEM_CONFIG[base].defaults };
}

export function loadTieredPricesByBase(base: TieredPickBaseName): Record<string, number> {
  const cfg = TIERED_ITEM_CONFIG[base];
  const out = cloneDefaults(base);
  try {
    const stored = getClientPrefsSnapshot().tierPrices?.[cfg.storageKey];
    if (!stored) return out;
    for (const lv of cfg.levels) {
      const n = Number(stored[lv]);
      if (Number.isFinite(n) && n >= 0) out[lv] = n;
    }
  } catch {
    /* ignore */
  }
  return out;
}

export function saveTieredPricesByBase(base: TieredPickBaseName, prices: Record<string, number>): void {
  const cfg = TIERED_ITEM_CONFIG[base];
  const snap = getClientPrefsSnapshot();
  patchClientPrefs({
    tierPrices: { ...snap.tierPrices, [cfg.storageKey]: { ...prices } },
  });
}

/** 分档中的最低价及对应等级（用于列表/格子默认展示） */
export function getTieredMinPriceAndLevel(base: TieredPickBaseName): { min: number; level: string } {
  const m = loadTieredPricesByBase(base);
  const cfg = TIERED_ITEM_CONFIG[base];
  let min = Infinity;
  let level = cfg.levels[0] ?? '0';
  for (const lv of cfg.levels) {
    const v = m[lv];
    if (Number.isFinite(v) && v >= 0 && v < min) {
      min = v;
      level = lv;
    }
  }
  if (!Number.isFinite(min) || min === Infinity) {
    return { min: 0, level: cfg.levels[0] ?? '0' };
  }
  return { min, level };
}

export function getTieredMinPriceForBase(base: TieredPickBaseName): number {
  return getTieredMinPriceAndLevel(base).min;
}

export function getTieredUnitPrice(base: TieredPickBaseName, level: string): number {
  const m = loadTieredPricesByBase(base);
  const v = m[level.trim()];
  return Number.isFinite(v) ? v : 0;
}

/** 记账台：格子名为基础名时按等级取价；非分档物品返回 0 */
export function getTieredLedgerUnitPrice(itemBaseName: string, level: string): number {
  const b = itemBaseName.trim() as TieredPickBaseName;
  if (!isTieredPickBaseName(b)) return 0;
  return getTieredUnitPrice(b, level);
}
