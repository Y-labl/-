export type ArtifactPhase = '起' | '转';

// Keep this list in sync with ArtifactGuidePage defaultItems().
const QI = new Set<string>([
  '黄金甲之谜',
  '噬魂齿之争',
  '清泽谱之惠',
  '昆仑镜之忆',
  '明火珠之影',
  '泪痕碗之念',
  '四神鼎之怨',
  '独弦琴之思',
  '星斗盘之约',
  '华光玉之伤',
  '墨魂笔之踪',
  '天罡印之谋',
  '月光草之逝',
  '轩辕剑之陨',
  '玲珑结之愿',
  '莫愁铃之恩',
  '千机锁之梏',
  '鸿蒙石之鉴',
  '魔息角之怒',
]);

const ZHUAN = new Set<string>([
  '魂印星斗盘',
  '离焰明火珠',
  '历劫月光草',
  '觅影玲珑结',
  '义绝墨魂笔',
  '悲瑟独弦琴',
  '迷踪清泽谱',
  '情葬泪痕碗',
  '神归昆仑镜',
  '重铸黄金甲',
  '魔灭噬魂齿',
  '计斗四神鼎',
  '诡夺天罡印',
  '忧思华光玉',
  '命陨轩辕剑',
]);

const QI_TO_ZHUAN: Record<string, string> = {
  黄金甲之谜: '重铸黄金甲',
  噬魂齿之争: '魔灭噬魂齿',
  清泽谱之惠: '迷踪清泽谱',
  昆仑镜之忆: '神归昆仑镜',
  明火珠之影: '离焰明火珠',
  泪痕碗之念: '情葬泪痕碗',
  四神鼎之怨: '计斗四神鼎',
  独弦琴之思: '悲瑟独弦琴',
  星斗盘之约: '魂印星斗盘',
  华光玉之伤: '忧思华光玉',
  墨魂笔之踪: '义绝墨魂笔',
  天罡印之谋: '诡夺天罡印',
  月光草之逝: '历劫月光草',
  轩辕剑之陨: '命陨轩辕剑',
  玲珑结之愿: '觅影玲珑结',
};

export function artifactPhaseOf(name: string): ArtifactPhase | null {
  const s = String(name || '').trim();
  if (!s) return null;
  if (QI.has(s)) return '起';
  if (ZHUAN.has(s)) return '转';
  return null;
}

export function artifactZhuanOfQi(qiName: string): string | null {
  const s = String(qiName || '').trim();
  if (!s) return null;
  return QI_TO_ZHUAN[s] || null;
}

/** 转神器名 → 对应起神器名（与 QI_TO_ZHUAN 互逆） */
export function artifactQiOfZhuan(zhuanName: string): string | null {
  const s = String(zhuanName || '').trim();
  if (!s) return null;
  for (const [qi, zhuan] of Object.entries(QI_TO_ZHUAN)) {
    if (zhuan === s) return qi;
  }
  return null;
}

/**
 * 游戏内每日「起」「转」各随机一条，**不必**是同剧情线的配对。
 * 从 OCR 多命中里各取一个起名、一个转名（按 hits 出现顺序取第一个）。
 */
export function pickOneQiOneZhuanFromHits(names: string[]): [string, string] | null {
  const hits = names.map((x) => String(x || '').trim()).filter(Boolean);
  if (hits.length < 2) return null;
  const qi = hits.find((n) => artifactPhaseOf(n) === '起');
  const zhuan = hits.find((n) => artifactPhaseOf(n) === '转');
  if (qi && zhuan) return [qi, zhuan];
  return null;
}

/**
 * 仅做两件事：① 已知一起一转时统一为 [起名, 转名] 便于展示；② 不重写为「剧情配对表」里的另一条名。
 * 双起/双转等脏数据保持原样（需用户重传截图或手改）。
 */
export function normalizeArtifactDayPair(selected: string[]): string[] {
  if (!Array.isArray(selected) || selected.length === 0) return [];
  const a = String(selected[0] || '').trim();
  const b = String(selected[1] || '').trim();
  if (!a) return b ? [b] : [];
  if (!b) return [a];
  if (a === b) return [a, b];

  const pa = artifactPhaseOf(a);
  const pb = artifactPhaseOf(b);

  if (pa === '起' && pb === '转') return [a, b];
  if (pa === '转' && pb === '起') return [b, a];

  return [a, b];
}

export function splitSelectedArtifactsByPhase(selected: string[]): { qi: string | null; zhuan: string | null } {
  let qi: string | null = null;
  let zhuan: string | null = null;
  for (const s of selected || []) {
    const nm = String(s || '').trim();
    const ph = artifactPhaseOf(nm);
    if (ph === '起' && !qi) qi = nm;
    else if (ph === '转' && !zhuan) zhuan = nm;
  }
  return { qi, zhuan };
}

export function artifactTaskTitleFromTaskName(taskName: string, selected: string[]): string | null {
  const { qi, zhuan } = splitSelectedArtifactsByPhase(selected);
  if (!qi || !zhuan) return null;
  const n = String(taskName || '');
  if (/（\s*起\s*）/.test(n)) return `神器 起：${qi}`;
  if (/（\s*转\s*）/.test(n)) return `神器 转：${zhuan}`;
  return `神器：${qi}、${zhuan}`;
}

