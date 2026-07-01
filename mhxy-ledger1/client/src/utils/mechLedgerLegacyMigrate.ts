/**
 * 旧版记账台计时在 localStorage `mhxy_mech_ledger_timer_v1`；
 * 现与 `mech_ledger_day_meta.ledger_base_elapsed_sec` / `ledger_run_start_at_ms` 同步。
 */
import { api } from '../api';

const TIMER_KEY = 'mhxy_mech_ledger_timer_v1';

export async function migrateMechLedgerTimerFromLocalStorage(bizDate: string): Promise<void> {
  let raw: string | null;
  try {
    raw = localStorage.getItem(TIMER_KEY);
  } catch {
    return;
  }
  if (!raw?.trim()) return;

  let parsed: { baseElapsedSec?: number; runStartAt?: number | null };
  try {
    parsed = JSON.parse(raw) as { baseElapsedSec?: number; runStartAt?: number | null };
  } catch {
    return;
  }

  const base = Math.max(0, Math.floor(Number(parsed.baseElapsedSec) || 0));
  let runMs: number | null = parsed.runStartAt != null ? Number(parsed.runStartAt) : null;
  if (runMs != null && (!Number.isFinite(runMs) || runMs <= 0)) runMs = null;

  try {
    const daily = await api.mechLedgerDaily(bizDate);
    const serverRun = daily.ledgerRunStartAtMs;
    const serverBase = daily.ledgerBaseElapsedSec;
    const serverHasTimer =
      (serverRun != null && Number.isFinite(Number(serverRun)) && Number(serverRun) > 0) ||
      (serverBase != null && Number.isFinite(Number(serverBase)) && Number(serverBase) > 0);
    if (serverHasTimer) {
      try {
        localStorage.removeItem(TIMER_KEY);
      } catch {
        /* ignore */
      }
      return;
    }

    const onlineCount = Math.max(1, daily.onlineRoles || 1);
    await api.mechLedgerSaveMeta({
      bizDate,
      onlineCount,
      cashGameGoldW: Number.isFinite(Number(daily.cashGameGoldW)) ? Number(daily.cashGameGoldW) : 0,
      teamPrincipalsW: Array.isArray(daily.teamPrincipalsW) ? daily.teamPrincipalsW : [],
      ledgerBaseElapsedSec: base,
      ledgerRunStartAtMs: runMs,
      ...(Array.isArray(daily.teamCashGameGoldW) && daily.teamCashGameGoldW.length > 0
        ? { teamCashGameGoldW: daily.teamCashGameGoldW }
        : {}),
      ...(daily.ledgerPointCard ? { ledgerPointCard: daily.ledgerPointCard } : {}),
    });
    try {
      localStorage.removeItem(TIMER_KEY);
    } catch {
      /* ignore */
    }
  } catch {
    /* 保留 key，下次再试 */
  }
}
