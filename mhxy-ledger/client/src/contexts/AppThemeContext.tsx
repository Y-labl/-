import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { AppThemeId } from '../pages/recommendSkinMeta';
import { isRecommendSkinId } from '../pages/recommendSkinMeta';

const STORAGE_KEY = 'mhxy_app_theme';

function readStoredTheme(): AppThemeId {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (!v || v === 'default') return 'default';
    if (isRecommendSkinId(v)) return v;
  } catch {
    /* ignore */
  }
  return 'default';
}

type AppThemeContextValue = {
  themeId: AppThemeId;
  setThemeId: (id: AppThemeId) => void;
};

const AppThemeContext = createContext<AppThemeContextValue | null>(null);

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const [themeId, setThemeIdState] = useState<AppThemeId>(readStoredTheme);

  const setThemeId = useCallback((id: AppThemeId) => {
    setThemeIdState(id);
    try {
      if (id === 'default') localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* ignore */
    }
  }, []);

  useLayoutEffect(() => {
    const root = document.documentElement;
    if (themeId === 'default') root.removeAttribute('data-app-theme');
    else root.setAttribute('data-app-theme', themeId);
  }, [themeId]);

  const value = useMemo(() => ({ themeId, setThemeId }), [themeId, setThemeId]);

  return <AppThemeContext.Provider value={value}>{children}</AppThemeContext.Provider>;
}

export function useAppTheme(): AppThemeContextValue {
  const ctx = useContext(AppThemeContext);
  if (!ctx) throw new Error('useAppTheme must be used within AppThemeProvider');
  return ctx;
}
