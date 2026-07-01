import { defaultBizDateNow, isValidYmd, localBizDate } from './bizDate';
import { getClientPrefsSnapshot, patchClientPrefs } from './clientPrefsStore';

/** 各页面独立业务日，持久化在 user_client_prefs（非浏览器） */
export const BIZ_DATE_PAGE = {
  ledger: 'ledger',
  overview: 'overview',
  tasks: 'tasks',
  consumption: 'consumption',
  artifactGuide: 'artifactGuide',
  mechDaily: 'mechDaily',
} as const;

export type BizDatePageId = (typeof BIZ_DATE_PAGE)[keyof typeof BIZ_DATE_PAGE];

function persistPageDate(pageId: string, next: string): void {
  if (!isValidYmd(next)) return;
  const snap = getClientPrefsSnapshot();
  const prev = snap.pageBizDates?.[pageId as BizDatePageId];
  if (prev === next) return;
  patchClientPrefs({
    pageBizDates: { ...snap.pageBizDates, [pageId]: next },
  });
}

function readStoredPageDate(pageId: string): string | null {
  const v = getClientPrefsSnapshot().pageBizDates?.[pageId as BizDatePageId];
  return isValidYmd(v) ? v : null;
}

/**
 * 读取某页业务日。
 * - 全站不做日期锁定：默认始终展示「今天」（跨自然日自动对齐）。
 * - 仍会把“今天”写回 prefs，便于服务端/多端状态一致，但不会长期停留在历史日期。
 */
export function getPageBizDate(pageId: string): string {
  const shouldBe = defaultBizDateNow();
  const cur = readStoredPageDate(pageId);
  if (cur !== shouldBe) persistPageDate(pageId, shouldBe);
  return shouldBe;
}

/**
 * 用户在某页修改业务日。
 * 仅记账台在计时锁定时禁止向前调到更晚日期。
 */
export function setPageBizDate(pageId: string, next: string): void {
  // 全站默认展示今天：忽略手动设置，保持对齐到 shouldBe。
  // 仍保留函数签名，避免调用方改动过大。
  const shouldBe = defaultBizDateNow();
  const cur = readStoredPageDate(pageId);
  if (cur !== shouldBe) persistPageDate(pageId, shouldBe);
}

export function getLedgerBizDate(): string {
  return getPageBizDate(BIZ_DATE_PAGE.ledger);
}

export function isLedgerBizDateLocked(): boolean {
  return false;
}

export function lockLedgerBizDate(bizDate: string): void {
  // 全站不支持锁定：强制回到今天
  void bizDate;
  unlockLedgerBizDateAndAdvanceToToday();
}

export function unlockLedgerBizDateAndAdvanceToToday(): void {
  const snap = getClientPrefsSnapshot();
  const today = localBizDate();
  patchClientPrefs({
    ledgerBizDateLocked: false,
    pageBizDates: { ...snap.pageBizDates, [BIZ_DATE_PAGE.ledger]: today },
  });
}
