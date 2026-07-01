/** manifest 覆盖名 → 文件；否则 ledgerData.iconFile（sheet-*.png）；再否则 item-01… 池 */

import manifest from './itemIconManifest.json';

export const LEDGER_ICON_POOL_SIZE = 11;

function publicPrefix(): string {
  const base = import.meta.env.BASE_URL;
  return base.endsWith('/') ? base : `${base}/`;
}

/** 从 public/mhxy-items 取任意文件名 */
export function ledgerPublicItemUrl(file: string): string {
  return `${publicPrefix()}mhxy-items/${file.trim()}`;
}

/** 仅图标池（回退用） */
export function ledgerPoolIconUrl(iconIndex: number): string {
  const n = (Math.abs(iconIndex) % LEDGER_ICON_POOL_SIZE) + 1;
  const pad = n < 10 ? `0${n}` : String(n);
  return `${publicPrefix()}mhxy-items/item-${pad}.png`;
}

/** 若 manifest 中为该名称配置了文件名则返回 URL，否则 null */
export function ledgerManifestIconUrl(name: string): string | null {
  const file = (manifest as { byName: Record<string, string> }).byName[name];
  if (typeof file !== 'string' || !file.trim()) return null;
  return ledgerPublicItemUrl(file.trim());
}
