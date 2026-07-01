/**
 * 与 client/src/utils/artifacts.ts 中 normalizeArtifactDayPair 一致：
 * 每日「起」「转」各自随机，不必同剧情线；此处只做 [起名, 转名] 排序。
 */
const QI = new Set([
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

const ZHUAN = new Set([
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

function phaseOf(name) {
  const s = String(name || '').trim();
  if (!s) return null;
  if (QI.has(s)) return '起';
  if (ZHUAN.has(s)) return '转';
  return null;
}

export function normalizeArtifactDayPair(selected) {
  if (!Array.isArray(selected) || selected.length === 0) return [];
  const a = String(selected[0] || '').trim();
  const b = String(selected[1] || '').trim();
  if (!a) return b ? [b] : [];
  if (!b) return [a];
  if (a === b) return [a, b];

  const pa = phaseOf(a);
  const pb = phaseOf(b);

  if (pa === '起' && pb === '转') return [a, b];
  if (pa === '转' && pb === '起') return [b, a];

  return [a, b];
}
