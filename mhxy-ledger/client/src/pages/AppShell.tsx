import { useCallback, useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { api, getToken, setToken } from '../api';
import { useAppTheme } from '../contexts/AppThemeContext';
import {
  clearClientPrefsMemory,
  flushClientPrefsNow,
  hydrateClientPrefs,
} from '../utils/clientPrefsStore';
import { hydrateGameYuanPairFromServer } from './ledger/ledgerYuanRatio';
import type { AppThemeId } from './recommendSkinMeta';
import { APP_THEME_OPTIONS } from './recommendSkinMeta';
import './AppShell.css';

export function AppShell() {
  const nav = useNavigate();
  const { themeId, setThemeId } = useAppTheme();
  const [bootReady, setBootReady] = useState(false);
  const [user, setUser] = useState<{ id: number; username: string } | null>(null);
  const [themeOpen, setThemeOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);

  const themeWrapRef = useRef<HTMLDivElement>(null);
  const userWrapRef = useRef<HTMLDivElement>(null);

  const loadMe = useCallback(() => {
    if (!getToken()) {
      setUser(null);
      return;
    }
    void api
      .me()
      .then((r) => setUser(r.user))
      .catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!getToken()) {
      setBootReady(true);
      setUser(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      await hydrateGameYuanPairFromServer();
      if (cancelled) return;
      await hydrateClientPrefs();
      if (cancelled) return;
      try {
        const r = await api.me();
        if (!cancelled) setUser(r.user);
      } catch {
        if (!cancelled) setUser(null);
      }
      if (!cancelled) setBootReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!themeOpen && !userOpen) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node;
      if (themeWrapRef.current?.contains(t)) return;
      if (userWrapRef.current?.contains(t)) return;
      setThemeOpen(false);
      setUserOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [themeOpen, userOpen]);

  function pickTheme(id: AppThemeId) {
    setThemeId(id);
    setThemeOpen(false);
  }

  function logout() {
    void flushClientPrefsNow().finally(() => {
      clearClientPrefsMemory();
      setToken(null);
      setUserOpen(false);
      nav('/login', { replace: true });
    });
  }

  return (
    <div className="app-shell">
      <header className="app-shell-header">
        <div className="app-shell-header__fill" aria-hidden />
        <div className="app-shell-menu" ref={themeWrapRef}>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            aria-expanded={themeOpen}
            aria-haspopup="menu"
            onClick={() => {
              setThemeOpen((v) => !v);
              setUserOpen(false);
            }}
          >
            主题
          </button>
          {themeOpen ? (
            <div className="app-shell-dropdown" role="menu" aria-label="选择界面主题">
              <div className="app-shell-dropdown__title">界面主题（全站）</div>
              {APP_THEME_OPTIONS.map((o) => (
                <button
                  key={o.id}
                  type="button"
                  role="menuitem"
                  className={`app-shell-dropdown__item${themeId === o.id ? ' app-shell-dropdown__item--active' : ''}`}
                  onClick={() => pickTheme(o.id)}
                >
                  {o.label}
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <div className="app-shell-menu" ref={userWrapRef}>
          <button
            type="button"
            className="btn btn-ghost btn-sm app-shell-header__trigger"
            aria-expanded={userOpen}
            aria-haspopup="menu"
            onClick={() => {
              setUserOpen((v) => !v);
              setThemeOpen(false);
              if (!user) loadMe();
            }}
          >
            {user?.username ?? '用户'}
          </button>
          {userOpen ? (
            <div className="app-shell-dropdown" role="menu" aria-label="用户菜单">
              {user ? (
                <div className="app-shell-user-panel">
                  <div className="app-shell-user-panel__name">{user.username}</div>
                  <div className="app-shell-user-panel__id">用户 ID：{user.id}</div>
                </div>
              ) : (
                <div className="app-shell-user-panel">
                  <div className="app-shell-user-panel__name muted">未获取到用户信息</div>
                  <button type="button" className="app-shell-dropdown__item" onClick={() => loadMe()}>
                    重试加载
                  </button>
                </div>
              )}
              <button type="button" role="menuitem" className="app-shell-dropdown__item app-shell-dropdown__danger" onClick={() => logout()}>
                退出登录
              </button>
            </div>
          ) : null}
        </div>
      </header>

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
        </aside>
        <div className="main">
          {bootReady ? <Outlet /> : <div className="muted">加载偏好…</div>}
        </div>
      </div>
    </div>
  );
}
