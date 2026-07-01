import { addLocalDays, defaultBizDateNow, isValidYmd, localBizDate } from './bizDate';
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
 * - 记账台：严格保留用户手动选择的业务日；仅在无存储值时初始化为今天。
 * - 其它页：无存储时默认今天；存储为「昨天」时在0 点过后自动对齐到今天；更早的手动查看日保留（各页独立）。
 */
export function getPageBizDate(pageId: string): string {
  const shouldBe = defaultBizDateNow();
  const cur = readStoredPageDate(pageId);

  if (pageId === BIZ_DATE_PAGE.ledger) {
    if (cur) return cur;
    const n = isLedgerBizDateLocked() ? localBizDate() : shouldBe;
    persistPageDate(pageId, n);
    return n;
  }

  if (!cur) {
    persistPageDate(pageId, shouldBe);
    return shouldBe;
  }
  const yesterday = addLocalDays(shouldBe, -1);
  if (cur === yesterday) {
    persistPageDate(pageId, shouldBe);
    return shouldBe;
  }
  return cur;
}

/**
 * 用户在某页修改业务日。
 * 仅记账台在计时锁定时禁止向前调到更晚日期。
 */
export function setPageBizDate(pageId: string, next: string): void {
  if (!isValidYmd(next)) return;
  const cur = readStoredPageDate(pageId);
  if (
    pageId === BIZ_DATE_PAGE.ledger &&
    isLedgerBizDateLocked() &&
    isValidYmd(cur) &&
    next > cur
  ) {
    return;
  }
  persistPageDate(pageId, next);
}

export function getLedgerBizDate(): string {
  return getPageBizDate(BIZ_DATE_PAGE.ledger);
}

export function isLedgerBizDateLocked(): boolean {
  return getClientPrefsSnapshot().ledgerBizDateLocked === true;
}

export function lockLedgerBizDate(bizDate: string): void {
  if (!isValidYmd(bizDate)) return;
  const snap = getClientPrefsSnapshot();
  patchClientPrefs({
    ledgerBizDateLocked: true,
    pageBizDates: { ...snap.pageBizDates, [BIZ_DATE_PAGE.ledger]: bizDate },
  });
}

export function unlockLedgerBizDateAndAdvanceToToday(): void {
  const snap = getClientPrefsSnapshot();
  const today = localBizDate();
  patchClientPrefs({
    ledgerBizDateLocked: false,
    pageBizDates: { ...snap.pageBizDates, [BIZ_DATE_PAGE.ledger]: today },
  });
}
