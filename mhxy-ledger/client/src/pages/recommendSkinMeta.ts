/** 与 demo-styles 对应 + 项目扩展（水晶） */
export const RECOMMEND_SKINS = [
  { id: 'neon', label: '霓虹风', demo: '1-neon.html' },
  { id: 'anime', label: '动漫风', demo: '1-anime.html' },
  { id: 'mechanical', label: '机械风', demo: '2-mechanical.html' },
  { id: 'romantic', label: '浪漫风', demo: '3-romantic.html' },
  { id: 'fresh', label: '清新风', demo: '4-fresh.html' },
  { id: 'dragon', label: '烈焰风', demo: '5-dragon.html' },
  { id: 'galaxy', label: '星河风', demo: '6-galaxy.html' },
  { id: 'water', label: '水流风', demo: '7-water.html' },
  { id: 'china', label: '国潮风', demo: '8-china.html' },
  { id: 'glass', label: '玻璃风', demo: '10-glass.html' },
  { id: 'crystal', label: '水晶风', demo: '扩展' },
] as const;

export type RecommendSkinId = (typeof RECOMMEND_SKINS)[number]['id'];

/** 全站 UI 主题：默认梦幻风 + RECOMMEND_SKINS */
export type AppThemeId = 'default' | RecommendSkinId;

export const APP_THEME_OPTIONS: { id: AppThemeId; label: string }[] = [
  { id: 'default', label: '梦幻默认' },
  ...RECOMMEND_SKINS.map((s) => ({ id: s.id, label: s.label })),
];

const SKIN_SET = new Set<string>(RECOMMEND_SKINS.map((s) => s.id));

export function isRecommendSkinId(s: string | undefined): s is RecommendSkinId {
  return s != null && SKIN_SET.has(s);
}

export function recommendSkinLabel(id: RecommendSkinId): string {
  return RECOMMEND_SKINS.find((x) => x.id === id)?.label ?? id;
}

export function isAppThemeId(s: string | undefined): s is AppThemeId {
  return s === 'default' || isRecommendSkinId(s);
}
