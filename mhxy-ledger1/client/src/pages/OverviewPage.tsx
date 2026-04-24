import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  api,
  type MechLedgerDailyResponse,
  type Monthly,
  type Overview,
  type Weekly,
} from '../api';
import { addLocalDays, localBizDate, mondayOfLocalWeekContaining, mondayOfTodayCalendarWeek } from '../utils/bizDate';
import { BIZ_DATE_PAGE, getLedgerBizDate, isLedgerBizDateLocked } from '../utils/pageBizDate';
import { usePageBizDate } from '../utils/usePageBizDate';
import { itemWTotalToYuan, loadGameYuanPair, yuanPerWFromPair } from './ledger/ledgerYuanRatio';
import { BizDatePickerField } from '../components/BizDatePickerField';
import { BizMonthPickerField } from '../components/BizMonthPickerField';
import { formatWanZhCN } from '../utils/formatWanZhCN';

export function OverviewPage() {
  const [viewDate, setViewDate] = usePageBizDate(BIZ_DATE_PAGE.overview);
  const ledgerBiz = useMemo(() => getLedgerBizDate(), []);
  /** 自然周：默认本周一～本周日（7 天），与上方「当日」业务日期无关 */
  const [weekStart, setWeekStart] = useState(() => mondayOfTodayCalendarWeek());
  const [year, setYear] = useState(() => {
    const d = new Date();
    return d.getFullYear();
  });
  const [month, setMonth] = useState(() => new Date().getMonth() + 1);
  const [o, setO] = useState<Overview | null>(null);
  const [w, setW] = useState<Weekly | null>(null);
  const [mstat, setMstat] = useState<Monthly | null>(null);
  const [err, setErr] = useState('');
  const [mechDaily, setMechDaily] = useState<MechLedgerDailyResponse | null>(null);
  const [mechErr, setMechErr] = useState('');
  const [gameYuan, setGameYuan] = useState(() => loadGameYuanPair());
  const yuanPerWanW = useMemo(() => yuanPerWFromPair(gameYuan), [gameYuan]);

  /** 与 weekStart 配套的周日（API 仍只传周一） */
  const weekEndStr = useMemo(() => addLocalDays(weekStart, 6), [weekStart]);

  useEffect(() => {
    const sync = () => setGameYuan(loadGameYuanPair());
    window.addEventListener('mhxy-ledger-yuan-ratio', sync);
    const onVis = () => {
      if (document.visibilityState === 'visible') sync();
    };
    document.addEventListener('visibilitychange', onVis);
    return () => {
      window.removeEventListener('mhxy-ledger-yuan-ratio', sync);
      document.removeEventListener('visibilitychange', onVis);
    };
  }, []);

  const loadStats = useCallback(async () => {
    const [ov, we, mo] = await Promise.all([
      api.statsOverview(viewDate),
      api.statsWeekly(weekStart),
      api.statsMonthly(year, month),
    ]);
    setO(ov);
    setW(we);
    setMstat(mo);
    setErr('');
  }, [viewDate, weekStart, year, month]);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        await loadStats();
      } catch (e) {
        if (!cancel) setErr(e instanceof Error ? e.message : '加载失败');
      }
    })();
    return () => {
      cancel = true;
    };
  }, [loadStats]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState !== 'visible') return;
      void loadStats().catch(() => {});
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, [loadStats]);

  /** 总览只读数据库 mech_ledger_day_meta + 物品聚合，不读浏览器 Session */
  const reloadMechLedger = useCallback(async () => {
    try {
      const md = await api.mechLedgerDaily(viewDate);
      setMechDaily(md);
      setMechErr('');
    } catch (e) {
      setMechDaily(null);
      setMechErr(e instanceof Error ? e.message : '记账台数据加载失败');
    }
  }, [viewDate]);

  useEffect(() => {
    void reloadMechLedger();
  }, [reloadMechLedger]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === 'visible') void reloadMechLedger();
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, [reloadMechLedger]);

  useEffect(() => {
    const inWeekRange = (d: string) => d >= weekStart && d <= weekEndStr;
    const onEvt = (e: Event) => {
      const ce = e as CustomEvent<{ bizDate?: string }>;
      const d0 = String(ce?.detail?.bizDate || '').slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(d0)) return;
      if (d0 === viewDate) void reloadMechLedger();
      if (inWeekRange(d0)) void loadStats().catch(() => {});
      const ym = `${year}-${String(month).padStart(2, '0')}`;
      if (d0.startsWith(ym)) void loadStats().catch(() => {});
    };
    window.addEventListener('mhxy-mech-today-lines', onEvt as EventListener);
    return () => window.removeEventListener('mhxy-mech-today-lines', onEvt as EventListener);
  }, [viewDate, loadStats, month, weekEndStr, weekStart, reloadMechLedger, year]);

  useEffect(() => {
    const onDayMeta = (e: Event) => {
      const ce = e as CustomEvent<{ bizDate?: string }>;
      const d0 = String(ce?.detail?.bizDate || '').slice(0, 10);
      if (d0 === viewDate) void reloadMechLedger();
    };
    window.addEventListener('mhxy-mech-day-meta-saved', onDayMeta as EventListener);
    return () => window.removeEventListener('mhxy-mech-day-meta-saved', onDayMeta as EventListener);
  }, [viewDate, reloadMechLedger]);

  const normalizeDayKey = useCallback((d: unknown): string => {
    // 兼容服务端把 DATE 序列化成 ISO（带 T）的情况：只取 YYYY-MM-DD
    const s = String(d ?? '').trim();
    if (!s) return '';
    return s.length >= 10 ? s.slice(0, 10) : s;
  }, []);

  const mechTodayItemQty = useMemo(() => {
    if (!mechDaily?.lines?.length) return 0;
    return mechDaily.lines.reduce((s, l) => s + Math.max(0, Math.floor(Number(l.count) || 0)), 0);
  }, [mechDaily]);

  const weekBars = useMemo(() => {
    if (!w) return [];
    const map = new Map<string, number>();
    for (const row of w.itemByDay) {
      map.set(normalizeDayKey(row.d), Number(row.qty));
    }
    // 兜底：当天物品行是实时同步的，用它覆盖当天数量（避免聚合表延迟导致当天为 0）
    if (viewDate) map.set(viewDate, mechTodayItemQty);
    const out: { label: string; v: number }[] = [];
    const start = new Date(`${w.weekStart}T12:00:00`);
    for (let i = 0; i < 7; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      out.push({ label: String(d.getDate()), v: map.get(key) ?? 0 });
    }
    const max = Math.max(1, ...out.map((x) => x.v));
    return out.map((b) => ({ ...b, h: Math.round((b.v / max) * 100) }));
  }, [viewDate, mechTodayItemQty, normalizeDayKey, w]);

  const monthBars = useMemo(() => {
    if (!mstat) return [];
    const map = new Map<string, number>();
    for (const row of mstat.itemByDay) {
      map.set(normalizeDayKey(row.d), Number(row.qty));
    }
    if (viewDate) map.set(viewDate, mechTodayItemQty);
    const start = new Date(`${mstat.year}-${String(mstat.month).padStart(2, '0')}-01T12:00:00`);
    const end = new Date(start);
    end.setMonth(start.getMonth() + 1);
    end.setDate(0); // 本月最后一天

    const out: { label: string; v: number }[] = [];
    for (let d = new Date(start); d.getTime() <= end.getTime(); d.setDate(d.getDate() + 1)) {
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      out.push({ label: String(d.getDate()).padStart(2, '0'), v: map.get(key) ?? 0 });
    }
    const max = Math.max(1, ...out.map((x) => x.v));
    return out.map((b) => ({ ...b, h: Math.round((b.v / max) * 100) }));
  }, [viewDate, mechTodayItemQty, mstat, normalizeDayKey]);

  const mechItemW = useMemo(() => {
    if (!mechDaily) return 0;
    const total = mechDaily.lines.reduce((s, l) => s + l.valueW * l.count, 0);
    const trash = Number(mechDaily.vendorTrashW ?? 0);
    return Math.max(0, total - (Number.isFinite(trash) ? trash : 0));
  }, [mechDaily]);

  const mechYuan = useMemo(() => itemWTotalToYuan(mechItemW, yuanPerWanW), [mechItemW, yuanPerWanW]);

  const mechOk = Boolean(mechDaily && !mechErr);

  const itemConvertYuan = mechOk ? mechYuan : null;
  const goldGrossWan = mechOk ? (mechDaily!.cashGameGoldW ?? 0) : null;
  const goldNetWan =
    mechOk && mechDaily
      ? (() => {
          if (mechDaily.netCashGameGoldW != null && Number.isFinite(mechDaily.netCashGameGoldW)) {
            return mechDaily.netCashGameGoldW;
          }
          const tc = mechDaily.teamCashGameGoldW;
          const tp = mechDaily.teamPrincipalsW ?? [];
          if (tc?.length) {
            let net = 0;
            for (let i = 0; i < tc.length; i++) {
              const c = Number(tc[i]) || 0;
              const p = Number(tp[i]) || 0;
              if (c <= 0) continue;
              net += c - p;
            }
            return net;
          }
          const gross = mechDaily.cashGameGoldW ?? 0;
          if (gross <= 0) return 0;
          return gross - tp.reduce((a, b) => a + (Number(b) || 0), 0);
        })()
      : null;
  const goldConvertYuan = goldNetWan !== null ? goldNetWan * yuanPerWanW : null;
  const totalCashYuan =
    itemConvertYuan !== null && goldConvertYuan !== null ? itemConvertYuan + goldConvertYuan : null;

  /** 与现金总额（元）同源：净现金梦幻币（万）+ 物品合计（w），括号内展示用 */
  const totalDreamCoinWan =
    mechOk && goldNetWan != null && Number.isFinite(goldNetWan) && Number.isFinite(mechItemW)
      ? goldNetWan + mechItemW
      : null;

  const netCashYuan =
    o && totalCashYuan !== null ? totalCashYuan - (o.consumptionRmb ?? 0) : null;

  /** 与下方按日柱状图同一套合并逻辑，避免「合计」与柱子不一致 */
  const weekItemQuantitySum = useMemo(() => weekBars.reduce((s, b) => s + b.v, 0), [weekBars]);

  const monthItemQuantitySum = useMemo(() => monthBars.reduce((s, b) => s + b.v, 0), [monthBars]);

  const fmtYuan2 = (n: number | null) =>
    n === null
      ? '—'
      : n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div>
      <div className="topbar">
        <h2>总览</h2>
      </div>

      {err && <p style={{ color: 'var(--danger)' }}>{err}</p>}

      <section style={{ marginBottom: '1.5rem' }}>
        <h3 className="muted" style={{ margin: '0 0 0.5rem' }}>
          当日（{viewDate}）
        </h3>
        {isLedgerBizDateLocked() && localBizDate() !== getLedgerBizDate() ? (
          <p className="muted" style={{ fontSize: '0.82rem', margin: '0.1rem 0 0.65rem', lineHeight: 1.45 }}>
            记账台已「开始计时」并锁定其业务日：自然日已到 {localBizDate()}，记账台仍在统计 {getLedgerBizDate()}。结束当次统计请在记账台<strong>清除计时并换日</strong>（正式收益快照需再点「保存收益」）。本总览、任务、消耗等页的日期<strong>各自独立</strong>，仅影响对应页面。
          </p>
        ) : null}
        <p className="muted" style={{ fontSize: '0.78rem', margin: '0 0 0.65rem', lineHeight: 1.45 }}>
          当日记账（点卡、现金、物品合计）均来自<strong>数据库</strong>；记账台会自动把当前数据写入库，打开总览即可同步，无需在总览清理 Session。
        </p>
        <p className="muted" style={{ fontSize: '0.78rem', margin: '0 0 0.65rem', lineHeight: 1.45 }}>
          下方日期<strong>仅影响本页「当日」</strong>；记账台、任务、消耗、神器攻略等页的<strong>业务日各自独立</strong>。
        </p>
        <div
          className="overview-biz-date-row"
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '0.45rem 0.75rem',
            marginBottom: '0.75rem',
          }}
        >
          <BizDatePickerField
            id="overview-biz-date"
            value={viewDate}
            onChange={(v) => setViewDate(v || localBizDate())}
          />
          {viewDate !== getLedgerBizDate() ? (
            <button
              type="button"
              className="btn btn-ghost"
              style={{ padding: '0.45rem 0.6rem', fontSize: '0.82rem' }}
              title={`记账台当前业务日为 ${getLedgerBizDate()}，点卡/物品/现金实时数据通常看这个日子`}
              onClick={() => setViewDate(getLedgerBizDate())}
            >
              切到记账台日期（{getLedgerBizDate()}）
            </button>
          ) : null}
        </div>
        {mechErr && (
          <p className="muted" style={{ margin: '0.5rem 0', fontSize: '0.85rem' }}>
            记账台：{mechErr}
          </p>
        )}
        {(o || mechOk) && (
          <div className="overview-daily-grid-4">
            <div
              className="card stat-box overview-cash-total-card"
              style={{ gridColumn: 1, gridRow: 1 }}
            >
              <h3>现金总额（元）</h3>
              <div className="num">{fmtYuan2(totalCashYuan)}</div>
              {totalDreamCoinWan !== null ? (
                <p className="overview-cash-total-note muted">
                  梦幻币总额：（{formatWanZhCN(totalDreamCoinWan).replace(/万$/, 'W')}）
                </p>
              ) : null}
            </div>
            <div className="card stat-box" style={{ gridColumn: 1, gridRow: 2 }}>
              <h3>现金净额（元）</h3>
              <div className="num">{fmtYuan2(netCashYuan)}</div>
            </div>
            <div className="card stat-box" style={{ gridColumn: 2, gridRow: 1 }}>
              <h3>点卡消耗（点）</h3>
              <div className="num">
                {mechOk
                  ? Number(mechDaily!.pointCardPoints || 0).toFixed(2)
                  : o
                    ? Number(o.pointCard).toFixed(2)
                    : '—'}
              </div>
            </div>
            <div className="card stat-box" style={{ gridColumn: 2, gridRow: 2 }}>
              <h3>点卡充值（元）</h3>
              <div className="num">
                {o ? (
                  (o.consumptionRmb ?? 0).toLocaleString('zh-CN', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  })
                ) : (
                  '—'
                )}
              </div>
            </div>
            <div className="card stat-box" style={{ gridColumn: 3, gridRow: 1 }}>
              <h3>物品合计 (w)</h3>
              <div className="num">{mechOk ? mechItemW.toFixed(1) : '—'}</div>
            </div>
            <div className="card stat-box" style={{ gridColumn: 3, gridRow: 2 }}>
              <h3>物品折算价格（元）</h3>
              <div className="num">{fmtYuan2(itemConvertYuan)}</div>
            </div>
            <div className="card stat-box" style={{ gridColumn: 4, gridRow: 1 }}>
              <h3>现金梦幻币—净</h3>
              <div className="num">
                {mechOk && goldNetWan != null ? formatWanZhCN(goldNetWan) : '—'}
              </div>
              {mechOk && goldGrossWan != null && goldGrossWan !== goldNetWan ? (
                <div className="muted" style={{ fontSize: '0.78rem', marginTop: '0.25rem' }}>
                  毛 {formatWanZhCN(goldGrossWan)}
                </div>
              ) : null}
            </div>
            <div className="card stat-box" style={{ gridColumn: 4, gridRow: 2 }}>
              <h3>净现金折算（元）</h3>
              <div className="num">{fmtYuan2(goldConvertYuan)}</div>
            </div>
          </div>
        )}

        {o && o.taskCompletions.length > 0 && (
          <div className="card" style={{ padding: '1rem' }}>
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>今日已完成任务</h3>
            <ul style={{ margin: 0, paddingLeft: '1.1rem', color: 'var(--muted)' }}>
              {o.taskCompletions.map((t) => (
                <li key={t.id} style={{ marginBottom: 6 }}>
                  <strong style={{ color: 'var(--text)' }}>{t.taskName}</strong>
                  {t.dedupeKey?.startsWith('live:') && (
                    <span className="muted" style={{ marginLeft: 6, fontSize: '0.8rem' }}>
                      （限时）
                    </span>
                  )}
                  {t.startedAt && t.endedAt && (
                    <span style={{ marginLeft: 8 }}>
                      耗时约{' '}
                      {Math.max(
                        1,
                        Math.round(
                          (new Date(t.endedAt).getTime() - new Date(t.startedAt).getTime()) / 60000
                        )
                      )}
                      {' '}
                      分钟
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section style={{ marginBottom: '1.5rem' }}>
        <h3 className="muted" style={{ margin: '0 0 0.5rem' }}>
          本周
        </h3>
        <div
          className="overview-week-range-row"
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '0.5rem 0.75rem',
            marginBottom: '0.65rem',
          }}
        >
          <BizDatePickerField
            id="overview-week-from"
            label="从"
            value={weekStart}
            onChange={(v) => {
              if (!v) return;
              setWeekStart(mondayOfLocalWeekContaining(v));
            }}
          />
          <span className="muted" style={{ userSelect: 'none' }}>
            ～
          </span>
          <BizDatePickerField
            id="overview-week-to"
            label="至"
            value={weekEndStr}
            onChange={(v) => {
              if (!v) return;
              setWeekStart(mondayOfLocalWeekContaining(v));
            }}
          />
        </div>
        {w && (
          <p className="muted" style={{ fontSize: '0.8rem', margin: '0.35rem 0 0.65rem', lineHeight: 1.45 }}>
            自然周 {w.weekStart}～{w.weekEnd}（周一～周日共 7 天），与上方「当日」业务日期无关；点卡充值优先统计消耗页「充值(元)」，无则旧表或点数×0.1。
          </p>
        )}
        {w && (
          <>
            <div className="stat-grid">
              <div className="card stat-box">
                <h3>现金净额（元）</h3>
                <div className="num">{fmtYuan2(w.netCashYuan ?? null)}</div>
              </div>
              <div className="card stat-box">
                <h3>本周现金总额（元）</h3>
                <div className="num">{fmtYuan2((w.totalCashYuan ?? null) as number | null)}</div>
              </div>
              <div className="card stat-box">
                <h3>周点卡充值（元）</h3>
                <div className="num">
                  {(Number(w.pointCardRechargeYuan) || 0).toLocaleString('zh-CN', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  })}
                </div>
              </div>
              <div className="card stat-box">
                <h3>周现金</h3>
                <div className="num">{w.cash.toLocaleString('zh-CN')}</div>
              </div>
              <div className="card stat-box">
                <h3>周点卡</h3>
                <div className="num">{Number(w.pointCard).toFixed(2)}</div>
              </div>
              <div className="card stat-box">
                <h3>完成任务次数</h3>
                <div className="num">{w.taskCompletionsCount}</div>
              </div>
              <div className="card stat-box">
                <h3>物品数量合计</h3>
                <div className="num">{weekItemQuantitySum.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}</div>
              </div>
              <div className="card stat-box">
                <h3>在线角色数</h3>
                <div className="num">{Number(w.onlineRolesWeekMax ?? 0)}</div>
              </div>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>物品数量（按日）</h3>
              <div className="bar-chart bar-chart-week">
                {weekBars.map((b) => (
                  <div
                    key={b.label}
                    className="bar"
                    style={{ height: `${Math.max(8, b.h)}%` }}
                    title={`${w.weekStart}～${w.weekEnd}：${b.label} 号 物品数量 ${b.v}`}
                  >
                    <span className="bar-v" aria-hidden="true">
                      {b.v}
                    </span>
                    <span className="bar-label">{b.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </section>

      <section>
        <h3 className="muted" style={{ margin: '0 0 0.5rem' }}>
          本月
        </h3>
        <div style={{ marginBottom: '0.75rem' }}>
          <BizMonthPickerField
            id="overview-month"
            label="统计月份"
            year={year}
            month={month}
            onChange={(y, m) => {
              setYear(y);
              setMonth(m);
            }}
          />
        </div>
        {mstat && (
          <>
            <p className="muted" style={{ fontSize: '0.8rem', margin: '0.35rem 0 0.65rem', lineHeight: 1.45 }}>
              {mstat.year} 年 {mstat.month} 月自然月（1 日～月末），与「当日」业务日期无关；点卡充值口径同上（消耗页优先，其次旧表/点数折算）。
            </p>
            <div className="stat-grid">
              <div className="card stat-box">
                <h3>现金净额（元）</h3>
                <div className="num">{fmtYuan2(mstat.netCashYuan ?? null)}</div>
              </div>
              <div className="card stat-box">
                <h3>本月现金总额（元）</h3>
                <div className="num">{fmtYuan2((mstat.totalCashYuan ?? null) as number | null)}</div>
              </div>
              <div className="card stat-box">
                <h3>月点卡充值（元）</h3>
                <div className="num">
                  {(Number(mstat.pointCardRechargeYuan) || 0).toLocaleString('zh-CN', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  })}
                </div>
              </div>
              <div className="card stat-box">
                <h3>月点卡</h3>
                <div className="num">{Number(mstat.pointCard).toFixed(2)}</div>
              </div>
              <div className="card stat-box">
                <h3>完成任务次数</h3>
                <div className="num">{mstat.taskCompletionsCount}</div>
              </div>
              <div className="card stat-box">
                <h3>物品数量合计</h3>
                <div className="num">
                  {monthItemQuantitySum.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>物品数量（本月有记录的日子）</h3>
              <div className="bar-chart" style={{ minHeight: 140 }}>
                {monthBars.map((b) => (
                  <div
                    key={b.label + b.v}
                    className="bar"
                    style={{ height: `${Math.max(8, b.h)}%` }}
                    title={`${mstat.year}-${String(mstat.month).padStart(2, '0')}-${b.label}：物品数量 ${b.v}`}
                  >
                    <span className="bar-v" aria-hidden="true">
                      {b.v}
                    </span>
                    <span className="bar-label">{b.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
