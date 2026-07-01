import { useCallback, useSyncExternalStore } from 'react';
import {
  getClientPrefsSnapshot,
  patchClientPrefs,
  subscribeClientPrefs,
} from '../utils/clientPrefsStore';

export const DEFAULT_TABLE_PAGE_SIZE = 20;

export const TABLE_PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

function parseFromPrefs(): number {
  const v = Number(getClientPrefsSnapshot().tablePageSize);
  if ((TABLE_PAGE_SIZE_OPTIONS as readonly number[]).includes(v)) return v;
  return DEFAULT_TABLE_PAGE_SIZE;
}

let pageSizeSnapshot =
  typeof window !== 'undefined' ? parseFromPrefs() : DEFAULT_TABLE_PAGE_SIZE;
const listeners = new Set<() => void>();

function syncFromPrefs() {
  const next = parseFromPrefs();
  if (next !== pageSizeSnapshot) {
    pageSizeSnapshot = next;
    listeners.forEach((l) => l());
  }
}

if (typeof window !== 'undefined') {
  subscribeClientPrefs(syncFromPrefs);
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function getSnapshot() {
  return pageSizeSnapshot;
}

export function setGlobalTablePageSize(n: number) {
  if (!(TABLE_PAGE_SIZE_OPTIONS as readonly number[]).includes(n)) return;
  if (pageSizeSnapshot === n) return;
  patchClientPrefs({ tablePageSize: n });
}

/**
 * 全站共用的「每页条数」：持久化在 user_client_prefs。
 */
export function useSharedTablePageSize() {
  const pageSize = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  const setPageSize = useCallback((n: number) => {
    setGlobalTablePageSize(n);
  }, []);
  return { pageSize, setPageSize, pageSizeOptions: TABLE_PAGE_SIZE_OPTIONS };
}
