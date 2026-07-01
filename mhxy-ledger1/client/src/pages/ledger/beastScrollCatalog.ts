/**
 * 物品库 / 记账台：兽决按「种类」定价（无等级）；单价存服务端 user_client_prefs。
 */

import { getClientPrefsSnapshot, patchClientPrefs } from '../../utils/clientPrefsStore';

export const BEAST_SCROLL_ITEM_NAME = '兽决';

/** 种类简称（默认行，可在物品库改名称 / 增删行） */
export const BEAST_SCROLL_TYPES = [
  '夜',
  '质量',
  '吸收小法法系',
  '反防抵永强合盾',
  '飞冥精',
  '连迟慧',
  '迹再隐',
  '神佑',
  '鬼否',
] as const;

export type BeastScrollCategory = (typeof BEAST_SCROLL_TYPES)[number];

export type BeastScrollRow = {
  id: string;
  label: string;
  priceW: number;
};

/** 默认单价（万 w） */
export const BEAST_SCROLL_DEFAULT_PRICES: Record<BeastScrollCategory, number> = {
  夜: 90,
  质量: 87,
  吸收小法法系: 84,
  反防抵永强合盾: 80,
  飞冥精: 79,
  连迟慧: 79,
  迹再隐: 75,
  神佑: 65,
  鬼否: 57,
};

function defaultRows(): BeastScrollRow[] {
  return BEAST_SCROLL_TYPES.map((t, i) => ({
    id: `def-${i}`,
    label: t,
    priceW: BEAST_SCROLL_DEFAULT_PRICES[t],
  }));
}

function normalizeRows(raw: unknown): BeastScrollRow[] | null {
  if (!Array.isArray(raw) || raw.length === 0) return null;
  const out: BeastScrollRow[] = [];
  for (let i = 0; i < raw.length; i++) {
    const r = raw[i];
    if (!r || typeof r !== 'object') continue;
    const o = r as Record<string, unknown>;
    const id = String(o.id ?? '').trim() || `row-${i}-${Date.now()}`;
    const label = String(o.label ?? '').trim();
    const priceW = Number(o.priceW);
    out.push({
      id,
      label: label || '未命名',
      priceW: Number.isFinite(priceW) && priceW >= 0 ? priceW : 0,
    });
  }
  return out.length ? out : null;
}

export function loadBeastScrollRows(): BeastScrollRow[] {
  try {
    const v2 = getClientPrefsSnapshot().beastScrollV2;
    if (v2 && Array.isArray(v2.rows)) {
      const rows = normalizeRows(v2.rows);
      if (rows) return rows;
    }
  } catch {
    /* ignore */
  }
  return defaultRows();
}

export function saveBeastScrollRows(rows: BeastScrollRow[]): void {
  const cleaned = rows.map((r) => ({
    ...r,
    label: r.label.trim() || '未命名',
  }));
  patchClientPrefs({ beastScrollV2: { v: 2, rows: cleaned } });
}

export function getBeastScrollRowById(rows: BeastScrollRow[], id: string): BeastScrollRow | undefined {
  return rows.find((r) => r.id === id);
}

export function getBeastScrollRowByLabel(rows: BeastScrollRow[], label: string): BeastScrollRow | undefined {
  const t = label.trim();
  return rows.find((r) => r.label.trim() === t);
}

export function buildBeastScrollDisplayName(label: string): string {
  return `${BEAST_SCROLL_ITEM_NAME} · ${label.trim()}`;
}

/** 解析「兽决 · xxx」中的种类文案（不校验是否在默认列表内） */
export function parseBeastScrollDisplayName(name: string): string | null {
  const m = name.trim().match(/^兽决\s*·\s*(.+)$/);
  if (!m) return null;
  const cat = m[1].trim();
  return cat.length ? cat : null;
}

export function isBeastScrollCatalogName(name: string): boolean {
  const t = name.trim();
  if (t === BEAST_SCROLL_ITEM_NAME) return true;
  return parseBeastScrollDisplayName(t) !== null;
}

/** 记账台：按种类名称取单价（万 w） */
export function getBeastScrollLedgerUnitPrice(categoryLabel: string): number {
  const row = getBeastScrollRowByLabel(loadBeastScrollRows(), categoryLabel);
  return row ? row.priceW : 0;
}
