/** 记账台：点击特定物品时需先选等级 / 灵饰书另选种类 / 兽决另选种类 */

import { BEAST_SCROLL_ITEM_NAME } from './beastScrollCatalog';
import { getTieredLevelsForItem } from './tieredItemCatalog';

export const LEDGER_PICK_LEVEL_ITEM_NAMES = ['晶石', '附魔宝珠', '珍珠', '炼妖石', '种子'] as const;
export const LEDGER_PICK_BOOK_ITEM_NAME = '灵饰书';
export const LEDGER_PICK_BEAST_ITEM_NAME = BEAST_SCROLL_ITEM_NAME;

/** 等级选项（与 tieredItemCatalog 晶石一致；附魔宝珠/珍珠/炼妖石见 getLedgerPickLevelOptions） */
export const LEDGER_LEVEL_OPTIONS = ['60', '80', '100', '120', '140'] as const;

/** 记账台选等级下拉：分档物品用各自等级表，否则回退晶石档 */
export function getLedgerPickLevelOptions(itemName: string): readonly string[] {
  const lv = getTieredLevelsForItem(itemName.trim());
  if (lv?.length) return lv;
  return LEDGER_LEVEL_OPTIONS;
}

/** 灵饰书 · 种类 */
export const LEDGER_LINGSHI_TYPES = ['戒指', '耳饰', '手镯', '配饰'] as const;

export type LedgerPickKind = 'level' | 'book' | 'beast';

export function getLedgerPickKind(rawName: string): LedgerPickKind | null {
  const name = rawName.trim();
  if (name === LEDGER_PICK_BOOK_ITEM_NAME) return 'book';
  if (name === LEDGER_PICK_BEAST_ITEM_NAME) return 'beast';
  if ((LEDGER_PICK_LEVEL_ITEM_NAMES as readonly string[]).includes(name)) return 'level';
  return null;
}

export function buildLedgerPickedDisplayName(
  baseName: string,
  level: string,
  bookType?: string
): string {
  const lv = level.trim() || '?';
  if (bookType) return `${baseName.trim()} · ${lv}级 · ${bookType}`;
  return `${baseName.trim()} · ${lv}级`;
}
