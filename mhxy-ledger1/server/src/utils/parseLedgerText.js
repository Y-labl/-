/**
 * 从合并文本中解析记账意图（规则引擎，非大模型）。
 * @param {string} text
 * @param {{ id: number; name: string }[]} items 名称越长优先匹配
 */
export function parseLedgerText(text, items) {
  const raw = String(text || '').trim();
  if (!raw) return [];

  const compact = raw.replace(/\s+/g, '');
  const out = [];
  const usedRanges = [];

  const sortedItems = [...items].sort((a, b) => b.name.length - a.name.length);

  function markUsed(start, end) {
    usedRanges.push([start, end]);
  }

  function overlaps(start, end) {
    return usedRanges.some(([s, e]) => !(end <= s || start >= e));
  }

  // 点卡 / 点数
  const ptPatterns = [
    /(?:点卡|点数|点)(\d{1,7})/g,
    /(\d{1,7})(?:点卡|点数)(?!万)/g,
  ];
  for (const re of ptPatterns) {
    let m;
    while ((m = re.exec(compact)) !== null) {
      const num = Number(m[1]);
      if (!Number.isNaN(num) && num >= 0) {
        out.push({ type: 'points', points: num, note: raw.slice(0, 120) });
        markUsed(m.index, m.index + m[0].length);
      }
    }
  }

  // 现金：X万
  const wanRe = /(-?\d+(?:\.\d+)?)万/g;
  let wm;
  while ((wm = wanRe.exec(compact)) !== null) {
    const amount = Number(wm[1]) * 10000;
    if (!Number.isNaN(amount)) {
      out.push({ type: 'cash', amount, note: raw.slice(0, 120) });
      markUsed(wm.index, wm.index + wm[0].length);
    }
  }

  // 现金：关键词后的数字
  const cashRe = /(?:现金|银子|梦幻币|游戏币)(-?\d+(?:\.\d+)?)(?!万)/g;
  let cm;
  while ((cm = cashRe.exec(compact)) !== null) {
    const amount = Number(cm[1]);
    if (!Number.isNaN(amount)) {
      out.push({ type: 'cash', amount, note: raw.slice(0, 120) });
      markUsed(cm.index, cm.index + cm[0].length);
    }
  }

  // 物品：子串匹配（名称越长优先）
  for (const it of sortedItems) {
    if (!it.name || it.name.length < 2) continue;
    const needle = it.name.replace(/\s/g, '');
    let idx = compact.indexOf(needle);
    if (idx < 0) idx = raw.indexOf(it.name);
    if (idx < 0) continue;
    const end = idx + Math.max(needle.length, it.name.length);
    if (overlaps(idx, end)) continue;
    out.push({ type: 'item', itemId: it.id, quantity: 1, note: raw.slice(0, 120) });
    markUsed(idx, end);
    break;
  }

  return out;
}
