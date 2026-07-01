/**
 * 游戏内金额（单位已是「万」）：格式化为「100万」「2459.7万」直读，无千分位，小数去尾 0。
 * @param maximumFractionDigits 小数位数上限（四舍五入），默认 2
 */
export function formatWanZhCN(n: number, maximumFractionDigits = 2): string {
  if (!Number.isFinite(n)) return '—';
  const sign = n < 0 ? '-' : '';
  const v = Math.abs(n);
  const p = 10 ** maximumFractionDigits;
  const r = Math.round(v * p) / p;
  let t = r.toFixed(maximumFractionDigits).replace(/\.?0+$/, '');
  if (t === '' || t === '-0') t = '0';
  return `${sign}${t}万`;
}
