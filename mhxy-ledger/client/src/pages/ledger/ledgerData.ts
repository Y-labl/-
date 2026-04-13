/** 日常格与截图左 6×8 / 右 2×8 按「行优先」对齐；名称与图不一致时请改顺序或改 iconFile */

import { LEDGER_ICON_POOL_SIZE } from './ledgerIcons';

export type LedgerItemDef = {
  id: string;
  iconIndex: number;
  /** 切图产物：sheet-fixed-01…48、sheet-var-01…16 */
  iconFile?: string;
  /** 完整地址：/mhxy-items/… 或 /uploads/…（与 iconFile 二选一即可） */
  imageUrl?: string;
  emoji: string;
  name: string;
  valueW: number;
  levelLabel?: string;
  description?: string;
};

const pool = (i: number) => i % LEDGER_ICON_POOL_SIZE;

const pad2 = (n: number) => (n < 10 ? `0${n}` : String(n));

const DAILY_FIXED_RAW: Omit<LedgerItemDef, 'iconIndex' | 'iconFile'>[] = [
  { id: 'd1', emoji: '💎', name: '金刚石', valueW: 150 },
  { id: 'd2', emoji: '🔮', name: '定魂珠', valueW: 190 },
  { id: 'd3', emoji: '📿', name: '龙鳞', valueW: 85 },
  { id: 'd4', emoji: '⚱️', name: '避水珠', valueW: 70 },
  { id: 'd5', emoji: '🧿', name: '夜光珠', valueW: 95 },
  { id: 'd6', emoji: '🔩', name: '金锭', valueW: 120 },
  { id: 'd7', emoji: '📜', name: '兽决', valueW: 90 },
  { id: 'd8', emoji: '📘', name: '高级兽决', valueW: 450 },
  { id: 'd9', emoji: '⭐', name: '星辉石', valueW: 35 },
  { id: 'd10', emoji: '💠', name: '宝石', valueW: 25 },
  { id: 'd11', emoji: '🗺️', name: '藏宝图', valueW: 3 },
  { id: 'd12', emoji: '🎁', name: '五宝盒', valueW: 420 },
  { id: 'd13', emoji: '🛡️', name: '环装', valueW: 8 },
  { id: 'd14', emoji: '⚔️', name: '书铁', valueW: 60 },
  { id: 'd15', emoji: '🪙', name: '强化石', valueW: 12 },
  { id: 'd16', emoji: '💰', name: '金币袋', valueW: 5 },
  { id: 'dx0', emoji: '🧩', name: '金瓶玉露', valueW: 6 },
  { id: 'dx1', emoji: '🎯', name: '超级金瓶玉露', valueW: 42 },
  { id: 'dx2', emoji: '🎲', name: '树苗', valueW: 37 },
  { id: 'dx3', emoji: '🏺', name: '月华露', valueW: 7 },
  { id: 'dx4', emoji: '🧩', name: '彩果', valueW: 27 },
  { id: 'dx5', emoji: '🎯', name: '超级金柳露', valueW: 30 },
  ...Array.from({ length: 14 }, (_, i) => {
    const j = i + 6;
    return {
      id: `dx${j}`,
      emoji: ['🧩', '🎯', '🎲', '🏺'][j % 4],
      name: `材料 ${j + 1}`,
      valueW: 5 + (j % 7) * 2,
    };
  }),
];

export const DAILY_FIXED_ITEMS: LedgerItemDef[] = DAILY_FIXED_RAW.map((row, i) => ({
  ...row,
  iconIndex: pool(i),
  iconFile: i < 48 ? `sheet-fixed-${pad2(i + 1)}.png` : undefined,
}));

export const DAILY_VAR_ITEMS: LedgerItemDef[] = Array.from({ length: 16 }, (_, i) => ({
  id: `v${i}`,
  iconIndex: pool(i + 8),
  iconFile: `sheet-var-${pad2(i + 1)}.png`,
  emoji: ['🐉', '👹', '🔥', '❄️'][i % 4],
  name: `浮动价 ${i + 1}`,
  valueW: 20 + i * 15,
}));

export const YAKSHA_WHITE: LedgerItemDef[] = [
  {
    id: 'yw1',
    iconIndex: pool(0),
    iconFile: 'sheet-fixed-47.png',
    emoji: '🐢',
    name: '白玩1',
    valueW: 0,
  },
  {
    id: 'yw2',
    iconIndex: pool(1),
    iconFile: 'sheet-fixed-48.png',
    emoji: '🦎',
    name: '白玩2',
    valueW: 0,
  },
  {
    id: 'yw3',
    iconIndex: pool(2),
    iconFile: 'sheet-var-16.png',
    emoji: '🐊',
    name: '白玩3',
    valueW: 0,
  },
];

export const YAKSHA_REWARD: LedgerItemDef[] = Array.from({ length: 10 }, (_, i) => ({
  id: `yr${i}`,
  iconIndex: pool(i + 3),
  iconFile: `sheet-fixed-${pad2(37 + i)}.png`,
  emoji: i % 3 === 0 ? '🐲' : i % 3 === 1 ? '👤' : '✨',
  name: `奖励 ${i + 1}`,
  valueW: 10,
}));

export const MOCK_HISTORY = [
  { date: '2024-12-28', profitYuan: 207.2, note: '五开' },
  { date: '2024-12-20', profitYuan: 135, note: '五开' },
  { date: '2024-12-15', profitYuan: 189, note: '五开' },
  { date: '2024-12-01', profitYuan: 156, note: '五开' },
  { date: '2024-11-22', profitYuan: 98, note: '五开' },
];

export const YAKSHA_COUNTER_KEYS = [
  { key: 'y1', label: '一黄', color: '#ffb347' },
  { key: 'y2', label: '二黄', color: '#ffd56b' },
  { key: 'y3', label: '三黄', color: '#ffe599' },
  { key: 'y4', label: '四黄', color: '#fff2a8' },
  { key: 'y5', label: '五黄', color: '#ffffff' },
  { key: 'hm', label: '画魂', color: '#a78bfa' },
  { key: 'lg', label: '绿龟', color: '#4ade80' },
  { key: 'wn', label: '万年', color: '#38bdf8' },
  { key: 'ym', label: '炎魔', color: '#f87171' },
  { key: 'xx', label: '吸血', color: '#fb923c' },
  { key: 'gj', label: '鬼将', color: '#c084fc' },
] as const;
