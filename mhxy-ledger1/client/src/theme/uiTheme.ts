/** 全站界面配色主题（持久化 prefs.uiTheme + localStorage） */
/** 10 套：赛博青 + 梦幻金保留；其余为水晶/国潮/动漫等风格（与 themes-palettes.css 对应） */
export const UI_THEMES = [
  'cyber',
  'mhxy',
  'crystal',
  'guochao',
  'anime',
  'ink',
  'starry',
  'mori',
  'latte',
  'qingci',
] as const;

export type UiThemeId = (typeof UI_THEMES)[number];

export const UI_THEME_STORAGE_KEY = 'mhxy_ui_theme';

export const DEFAULT_UI_THEME: UiThemeId = 'cyber';

export const UI_THEME_LABEL: Record<UiThemeId, string> = {
  cyber: '赛博青',
  mhxy: '梦幻金',
  crystal: '水晶',
  guochao: '国潮',
  anime: '动漫',
  ink: '水墨',
  starry: '星空',
  mori: '森系',
  latte: '拿铁',
  qingci: '青瓷',
};

const THEME_SET = new Set<string>(UI_THEMES);

export function isUiThemeId(x: unknown): x is UiThemeId {
  return typeof x === 'string' && THEME_SET.has(x);
}

export function readBootstrapUiTheme(): UiThemeId {
  try {
    const t = localStorage.getItem(UI_THEME_STORAGE_KEY);
    if (isUiThemeId(t)) return t;
    if (t) localStorage.removeItem(UI_THEME_STORAGE_KEY);
  } catch {
    /* ignore */
  }
  return DEFAULT_UI_THEME;
}

/** 同步到 `<html data-ui-theme>` 与本地缓存，供登录前与切换时立即生效 */
export function applyUiThemeToDocument(theme: UiThemeId | undefined | null): void {
  const t = theme && isUiThemeId(theme) ? theme : readBootstrapUiTheme();
  document.documentElement.dataset.uiTheme = t;
  try {
    localStorage.setItem(UI_THEME_STORAGE_KEY, t);
  } catch {
    /* ignore */
  }
}

export function resolvedUiThemeFromPrefs(prefsUiTheme: UiThemeId | undefined | null): UiThemeId {
  if (prefsUiTheme && isUiThemeId(prefsUiTheme)) return prefsUiTheme;
  return readBootstrapUiTheme();
}
