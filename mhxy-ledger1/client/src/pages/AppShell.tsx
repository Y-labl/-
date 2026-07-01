import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { getToken, setToken } from '../api';
import { ThemeMenu } from '../theme/ThemeMenu';
import {
  clearClientPrefsMemory,
  flushClientPrefsNow,
  hydrateClientPrefs,
} from '../utils/clientPrefsStore';
import { hydrateGameYuanPairFromServer } from './ledger/ledgerYuanRatio';

export function AppShell() {
  const nav = useNavigate();
  const [bootReady, setBootReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      setBootReady(true);
      return;
    }
    let cancelled = false;
    void (async () => {
      await hydrateGameYuanPairFromServer();
      if (cancelled) return;
      await hydrateClientPrefs();
      if (!cancelled) setBootReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <ThemeMenu />
      <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>多开账本</h1>
          <p className="sidebar-sub">五开收益 · 日常 · 统计</p>
        </div>
        <nav className="nav">
          <NavLink to="/app" end>
            总览
          </NavLink>
          <NavLink to="/app/tasks">推荐榜</NavLink>
          <NavLink to="/app/ledger">记账台</NavLink>
          <NavLink to="/app/ledger/daily">每日收益</NavLink>
          <NavLink to="/app/cash">消耗</NavLink>
          <NavLink to="/app/guide/artifacts">神器攻略</NavLink>
          <NavLink to="/app/ledger/catalog">物品库</NavLink>
        </nav>
        <button
          type="button"
          className="btn btn-ghost"
          style={{ width: '100%', marginTop: '1.25rem' }}
          onClick={() => {
            void flushClientPrefsNow().finally(() => {
              clearClientPrefsMemory();
              setToken(null);
              nav('/login', { replace: true });
            });
          }}
        >
          退出登录
        </button>
      </aside>
      <div className="main">
        {bootReady ? <Outlet /> : <div className="muted">加载偏好…</div>}
      </div>
    </div>
    </>
  );
}
