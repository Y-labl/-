/** 物品库：如意丹按五行分别定价（无等级）；单价存服务端 user_client_prefs。 */

import { getClientPrefsSnapshot, patchClientPrefs } from '../../utils/clientPrefsStore';

export const RUYI_DAN_ITEM_NAME = '如意丹';

export const RUYI_ELEMENTS = ['金', '木', '水', '火', '土'] as const;

export type RuyiElement = (typeof RUYI_ELEMENTS)[number];

export const RUYI_DAN_DEFAULT_PRICES: Record<RuyiElement, number> = {
  金: 18,
  木: 16,
  水: 20,
  火: 17,
  土: 15,
};

export function loadRuyiDanPrices(): Record<RuyiElement, number> {
  const base = { ...RUYI_DAN_DEFAULT_PRICES };
  try {
    const parsed = getClientPrefsSnapshot().ruyiDanPrices;
    if (!parsed) return base;
    for (const el of RUYI_ELEMENTS) {
      const n = Number(parsed[el]);
      if (Number.isFinite(n) && n >= 0) base[el] = n;
    }
  } catch {
    /* ignore */
  }
  return base;
}

export function saveRuyiDanPrices(p: Record<RuyiElement, number>): void {
  patchClientPrefs({ ruyiDanPrices: { ...p } });
}

export function getRuyiDanPrice(prices: Record<RuyiElement, number>, el: RuyiElement): number {
  const v = prices[el];
  return Number.isFinite(v) ? v : 0;
}

export function buildRuyiDanDisplayName(element: RuyiElement): string {
  return `${RUYI_DAN_ITEM_NAME} · ${element}`;
}

export function parseRuyiDanDisplayName(name: string): RuyiElement | null {
  const m = name.trim().match(/^如意丹\s*·\s*(金|木|水|火|土)\s*$/);
  if (!m) return null;
  const el = m[1] as RuyiElement;
  return (RUYI_ELEMENTS as readonly string[]).includes(el) ? el : null;
}

export function isRuyiDanCatalogName(name: string): boolean {
  const t = name.trim();
  return t === RUYI_DAN_ITEM_NAME || parseRuyiDanDisplayName(t) !== null;
}
