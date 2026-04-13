import type { ItemCatalogRow } from '../../api';
import type { LedgerItemDef } from './ledgerData';
import { LEDGER_ICON_POOL_SIZE } from './ledgerIcons';
import { getTieredMinPriceForBase, isTieredPickBaseName } from './tieredItemCatalog';

export function catalogRowToLedgerItem(row: ItemCatalogRow, i: number): LedgerItemDef {
  const url = (row.imageUrl || '').trim();
  const name = row.name.trim();
  const valueW = isTieredPickBaseName(name)
    ? getTieredMinPriceForBase(name)
    : Number(row.priceW) || 0;
  return {
    id: `c${row.id}`,
    name: row.name,
    valueW,
    iconIndex: i % LEDGER_ICON_POOL_SIZE,
    imageUrl: url || undefined,
    emoji: '📦',
    levelLabel: row.levelLabel || undefined,
    description: row.description || undefined,
  };
}

/** 与记账台「非固定价格」点击逻辑一致：在基准价 ×0.85～×1.15 内随机 */
export const FLOAT_PRICE_MULT_MIN = 0.85;
export const FLOAT_PRICE_MULT_MAX = 1.15;

export function floatingPriceRangeW(baseW: number): { min: number; max: number } {
  const w = Number(baseW) || 0;
  return {
    min: Math.round(w * FLOAT_PRICE_MULT_MIN),
    max: Math.round(w * FLOAT_PRICE_MULT_MAX),
  };
}

/** 随机浮动价（整数 w） */
export function rollFloatingPriceW(baseW: number): number {
  const w = Number(baseW) || 0;
  const span = FLOAT_PRICE_MULT_MAX - FLOAT_PRICE_MULT_MIN;
  return Math.round(w * (FLOAT_PRICE_MULT_MIN + Math.random() * span));
}

export function itemTooltip(it: LedgerItemDef) {
  const parts = [`${it.name}`, `${it.valueW} w`];
  if (it.levelLabel) parts.push(`等级 ${it.levelLabel}`);
  if (it.description) parts.push(it.description);
  return parts.join(' · ');
}

export function itemTooltipWithFloat(it: LedgerItemDef, fixedPrice: boolean) {
  if (fixedPrice) return itemTooltip(it);
  const { min, max } = floatingPriceRangeW(it.valueW);
  return `${itemTooltip(it)} · 浮动 ${min}–${max} w`;
}
