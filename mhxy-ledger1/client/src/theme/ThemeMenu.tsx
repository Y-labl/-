import { useEffect, useRef, useState } from 'react';
import { getClientPrefsSnapshot, patchClientPrefs, subscribeClientPrefs } from '../utils/clientPrefsStore';
import { UI_THEMES, UI_THEME_LABEL, resolvedUiThemeFromPrefs } from './uiTheme';
import './theme-menu.css';

export function ThemeMenu() {
  const [, bump] = useState(0);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => subscribeClientPrefs(() => bump((x) => x + 1)), []);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      const el = wrapRef.current;
      if (el && !el.contains(e.target as Node)) setOpen(false);
    };
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onEsc);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onEsc);
    };
  }, [open]);

  const snap = getClientPrefsSnapshot();
  const current = resolvedUiThemeFromPrefs(snap.uiTheme);

  return (
    <div className="theme-menu-floating" ref={wrapRef}>
      <button
        type="button"
        className="btn btn-ghost theme-menu-trigger"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="theme-menu-trigger-label">主题</span>
        <span className="theme-menu-trigger-current">{UI_THEME_LABEL[current]}</span>
        <span className="theme-menu-caret" aria-hidden>
          ▾
        </span>
      </button>
      {open ? (
        <div className="theme-menu-panel card" role="listbox" aria-label="界面主题">
          <div className="theme-menu-grid">
            {UI_THEMES.map((id) => (
              <button
                key={id}
                type="button"
                role="option"
                aria-selected={current === id}
                className={`theme-menu-item${current === id ? ' is-active' : ''}`}
                onClick={() => {
                  patchClientPrefs({ uiTheme: id });
                  setOpen(false);
                }}
              >
                {UI_THEME_LABEL[id]}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
