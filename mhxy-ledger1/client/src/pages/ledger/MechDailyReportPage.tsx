import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type MechLedgerDailyResponse } from '../../api';
import {
  addLocalDays,
  formatLocalDateTime,
  localBizDate,
  pointCardPointsToYuan,
} from '../../utils/bizDate';
import { BIZ_DATE_PAGE } from '../../utils/pageBizDate';
import { usePageBizDate } from '../../utils/usePageBizDate';
import {
  LEDGER_GAME_WAN_ANCHOR,
  itemWTotalToYuan,
  loadGameYuanPair,
  yuanPerWFromPair,
} from './ledgerYuanRatio';
import { BizDatePickerField } from '../../components/BizDatePickerField';
import { TablePaginationBar } from '../../components/TablePaginationBar';
import { useTablePagination } from '../../hooks/useTablePagination';
import { formatWanZhCN } from '../../utils/formatWanZhCN';
import './MechDailyReportPage.css';

function formatElapsedSec(sec: number | null | undefined): string {
  if (sec == null || !Number.isFinite(Number(sec)) || Number(sec) < 0) return '—';
  const s = Math.floor(Number(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  return `${h}小时${m}分${r}秒`;
}

function formatWanAmount(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(Number(n))) return '—';
  return formatWanZhCN(Number(n));
}

/** 各队本金/现金（万）：只列出 &gt;0 的队 */
function formatTeamWanBreakdown(vals: number[] | undefined | null): string {
  if (!vals?.length) return '—';
  const parts: string[] = [];
  for (let i = 0; i < vals.length; i++) {
    const v = Number(vals[i]);
    if (!Number.isFinite(v) || v <= 0) continue;
    parts.push(`队${i + 1}：${formatWanZhCN(v)}`);
  }
  return parts.length ? parts.join('；') : '—';
}

export default function MechDailyReportPage() {
  const [bizDate, setBizDate] = usePageBizDate(BIZ_DATE_PAGE.mechDaily);
  const [data, setData] = useState<MechLedgerDailyResponse | null>(null);
  const [dates, setDates] = useState<string[]>([]);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(true);
  const [gameYuan, setGameYuan] = useState(() => loadGameYuanPair());
  const yuanPerWanW = useMemo(() => yuanPerWFromPair(gameYuan), [gameYuan]);

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

  const loadDailyAndIndex = useCallback(async () => {
    const [daily, idx] = await Promise.all([
      api.mechLedgerDaily(bizDate),
      api.mechLedgerDayDates(120),
    ]);
    setData(daily);
    setDates(idx.dates);
    setErr('');
  }, [bizDate]);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        await loadDailyAndIndex();
      } catch (e) {
        if (!cancel) {
          setData(null);
          setErr(e instanceof Error ? e.message : '加载失败');
        }
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [loadDailyAndIndex]);

  /** 记账台「保存收益」打快照会派发事件；实时写入由 today-lines/save-meta 完成。本页日期与记账台、总览各自独立 */
  useEffect(() => {
    const onLines = (e: Event) => {
      const ce = e as CustomEvent<{ bizDate?: string }>;
      const d0 = String(ce?.detail?.bizDate || '').slice(0, 10);
      if (d0 === bizDate) void loadDailyAndIndex().catch(() => {});
    };
    const onDaySaved = (e: Event) => {
      const ce = e as CustomEvent<{ bizDate?: string }>;
      const d0 = String(ce?.detail?.bizDate || '').slice(0, 10);
      if (d0 === bizDate) void loadDailyAndIndex().catch(() => {});
    };
    window.addEventListener('mhxy-mech-today-lines', onLines as EventListener);
    window.addEventListener('mhxy-mech-day-meta-saved', onDaySaved as EventListener);
    return () => {
      window.removeEventListener('mhxy-mech-today-lines', onLines as EventListener);
      window.removeEventListener('mhxy-mech-day-meta-saved', onDaySaved as EventListener);
    };
  }, [bizDate, loadDailyAndIndex]);

  /** 记账台会定时写入 meta；前台每分钟拉一次便于看到近似的在线时长（页面在前台时） */
  useEffect(() => {
    const id = window.setInterval(() => {
      if (document.visibilityState !== 'visible') return;
      void api.mechLedgerDaily(bizDate).then((daily) => setData(daily)).catch(() => {});
    }, 60_000);
    return () => clearInterval(id);
  }, [bizDate]);

  const totals = useMemo(() => {
    if (!data) return { itemW: 0, combinedYuan: 0 };
    const itemW = data.lines.reduce((s, l) => s + l.valueW * l.count, 0);
    const hasSnapshot = data.pointCardPoints > 0 || data.savedAt;
    /** 与接口一致：有各队现金时用净现金，否则用毛 − 本金（由服务端算好的 netCashGameGoldW） */
    const cashW = hasSnapshot
      ? Number.isFinite(Number(data.netCashGameGoldW))
        ? Number(data.netCashGameGoldW)
        : Number(data.cashGameGoldW) || 0
      : 0;
    const combinedW = itemW + cashW;
    return { itemW, combinedYuan: itemWTotalToYuan(combinedW, yuanPerWanW) };
  }, [data, yuanPerWanW]);

  const reportLines = useMemo(() => data?.lines ?? [], [data]);
  const linesPg = useTablePagination(reportLines);

  return (
    <div className="mech-daily-page">
      <div className="topbar">
        <div>
          <h2>每日收益明细</h2>
          <p className="muted" style={{ margin: '0.35rem 0 0', fontSize: '0.88rem' }}>
            上方业务日与总览、记账台<strong>各自记忆</strong>；刚在记账台保存的请选<strong>同一天</strong>，或点下方「有记录」里的日期。数据来自记账台：物品行为单价折算的
            w；现金与点卡随记账台实时写入库，「保存收益」再打当日正式快照。金价固定 {LEDGER_GAME_WAN_ANCHOR} 万游戏币 ={' '}
            {gameYuan.yuan.toFixed(2)} 元（每 1 w = {Number(yuanPerWanW.toFixed(6))} 元）。
          </p>
        </div>
        <div className="mech-daily-top-actions">
          <Link to="/app/ledger" className="btn btn-ghost">
            返回记账台
          </Link>
        </div>
      </div>

      <div className="mech-daily-controls card">
        <div className="mech-daily-controls-row">
          <BizDatePickerField
            id="mech-daily-biz-date"
            value={bizDate}
            onChange={(v) => setBizDate(v || localBizDate())}
          />
          <div className="mech-daily-nav-btns">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setBizDate(addLocalDays(bizDate, -1))}
            >
              上一日
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setBizDate(localBizDate())}>
              今天
            </button>
          </div>
        </div>
        {dates.length > 0 && (
          <div className="mech-daily-pills">
            <span className="muted" style={{ fontSize: '0.8rem', marginRight: '0.35rem' }}>
              有记录：
            </span>
            {dates.slice(0, 14).map((d) => (
              <button
                key={d}
                type="button"
                className={`mech-daily-pill ${d === bizDate ? 'active' : ''}`}
                onClick={() => setBizDate(d)}
              >
                {d.slice(5)}
              </button>
            ))}
            {dates.length > 14 && <span className="muted">…</span>}
          </div>
        )}
      </div>

      {err && (
        <p className="mech-daily-err" role="alert">
          {err}
        </p>
      )}

      {loading && !err && <p className="muted">加载中…</p>}

      {!loading && data && (
        <section className="card mech-daily-section">
          <h3 className="mech-daily-section-title">物品（单价 w × 数量）</h3>
          <div className="mech-daily-table-wrap">
            <table className="mech-daily-table">
              <thead>
                <tr>
                  <th>物品名称</th>
                  <th className="num">单价 (w)</th>
                  <th className="num">数量</th>
                  <th className="num">小计 (w)</th>
                  <th className="num">折算 (元)</th>
                </tr>
              </thead>
              <tbody>
                {data.lines.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="mech-daily-empty">
                      该日暂无已同步的物品行。请在记账台点选物品，或确认已登录且数据库已执行 migrate-v6。
                    </td>
                  </tr>
                ) : (
                  linesPg.slice.map((row, i) => {
                    const sub = row.valueW * row.count;
                    return (
                      <tr key={`${row.name}-${row.valueW}-${(linesPg.page - 1) * linesPg.pageSize + i}`}>
                        <td>{row.name}</td>
                        <td className="num">{row.valueW}</td>
                        <td className="num">{row.count}</td>
                        <td className="num">{sub.toFixed(1)}</td>
                        <td className="num muted">{(sub * yuanPerWanW).toFixed(2)}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
            <TablePaginationBar
              page={linesPg.page}
              totalPages={linesPg.totalPages}
              total={linesPg.total}
              pageSize={linesPg.pageSize}
              onPageChange={linesPg.setPage}
              onPageSizeChange={linesPg.setPageSize}
            />
          </div>

          <h3 className="mech-daily-section-title" style={{ marginTop: '1.25rem' }}>
            汇总
          </h3>
          <div className="mech-daily-table-wrap">
            <table className="mech-daily-table mech-daily-summary-table">
              <thead>
                <tr>
                  <th className="num">在线角色数</th>
                  <th className="num">在线时长</th>
                  <th className="num">物品合计 (w)</th>
                  <th>本金</th>
                  <th className="num">现金毛</th>
                  <th className="num">净现金</th>
                  <th className="num">折算</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="num">{data.onlineRoles > 0 ? data.onlineRoles : '—'}</td>
                  <td className="num">{formatElapsedSec(data.elapsedSec)}</td>
                  <td className="num">{totals.itemW.toFixed(1)}</td>
                  <td className="mech-daily-team-cells">
                    <div className="mech-daily-team-primary">{formatTeamWanBreakdown(data.teamPrincipalsW)}</div>
                  </td>
                  <td className="num mech-daily-team-cells">
                    {data.pointCardPoints > 0 || data.savedAt ? (
                      <div>{formatWanAmount(data.cashGameGoldW)}</div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="num">
                    {data.pointCardPoints > 0 || data.savedAt
                      ? formatWanAmount(data.netCashGameGoldW)
                      : '—'}
                  </td>
                  <td className="num">{totals.combinedYuan.toFixed(2)}</td>
                  <td className="mech-daily-summary-time">
                    {data.savedAt ? formatLocalDateTime(data.savedAt) : '—'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="muted mech-daily-point-extra">
            点卡消耗{' '}
            {data.pointCardPoints > 0 || data.savedAt
              ? `${data.pointCardPoints.toFixed(2)} 点`
              : '—（未保存）'}
            ；金价 {LEDGER_GAME_WAN_ANCHOR} 万 = {gameYuan.yuan.toFixed(2)} 元；折合每 1 w ={' '}
            {Number(yuanPerWanW.toFixed(8))} 元
          </p>
          <p className="muted mech-daily-footnote">
            物品行：小计 (w) ×（{gameYuan.yuan.toFixed(2)} 元 ÷ {LEDGER_GAME_WAN_ANCHOR}
            万）。汇总「折算」=（物品合计 + 净现金）× 每 1 w 折合元；本金/现金毛/净现金列以「N万」展示；「净现金」由服务端按各队（现金 − 本金）汇总。在线时长由服务端按 meta 与跑表状态折算（记账台约每 5 分钟与保存收益等写入库）。未点「保存收益」时现金/净额可能为「—」，本金仍可按 meta 显示。
          </p>
        </section>
      )}
    </div>
  );
}
