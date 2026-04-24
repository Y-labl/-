/** 「一键导入」预设行：与切图 sheet-fixed / sheet-var 顺序一致 */

function pad2(n) {
  return n < 10 ? `0${n}` : String(n);
}

const FIXED_NAMES = [
  '金刚石',
  '定魂珠',
  '龙鳞',
  '避水珠',
  '夜光珠',
  '金锭',
  '兽决',
  '高级兽决',
  '星辉石',
  '宝石',
  '藏宝图',
  '五宝盒',
  '环装',
  '书铁',
  '强化石',
  '金币袋',
];

/** 兽决：格子基础价作未维护分档时的回退，与前端默认「夜」档 90 对齐 */
const FIXED_PRICES = [150, 190, 85, 70, 95, 120, 90, 450, 725, 80, 3, 420, 8, 60, 80, 5];

/** 固定价区 17…格（材料位）：名称与收购参考价（万 w）；未列出的仍为「材料 N」及公式价（与游戏内「金瓶玉露」一致） */
const FIXED_MATERIAL_OVERRIDES = {
  1: { name: '金瓶玉露', priceW: 6 },
  2: { name: '超级金瓶玉露', priceW: 42 },
  3: { name: '树苗', priceW: 37 },
  4: { name: '月华露', priceW: 7 },
  5: { name: '彩果', priceW: 27 },
  6: { name: '超级金柳露', priceW: 30 },
};

export function getItemCatalogPresetRows() {
  const rows = [];

  for (let i = 1; i <= 36; i++) {
    let name;
    let priceW;
    if (i <= 16) {
      name = FIXED_NAMES[i - 1];
      priceW = FIXED_PRICES[i - 1];
    } else {
      const matIdx = i - 16;
      const ov = FIXED_MATERIAL_OVERRIDES[matIdx];
      if (ov) {
        name = ov.name;
        priceW = ov.priceW;
      } else {
        name = `材料 ${matIdx}`;
        priceW = 5 + ((i - 17) % 7) * 2;
      }
    }
    rows.push({
      name,
      imageUrl: `/mhxy-items/sheet-fixed-${pad2(i)}.png`,
      priceW,
      levelLabel: '',
      description: '',
      panel: 'fixed',
      sortOrder: i - 1,
    });
  }

  for (let i = 1; i <= 16; i++) {
    rows.push({
      name: `浮动价 ${i}`,
      imageUrl: `/mhxy-items/sheet-var-${pad2(i)}.png`,
      priceW: 20 + (i - 1) * 15,
      levelLabel: '',
      description: '',
      panel: 'var',
      sortOrder: i - 1,
    });
  }

  rows.push(
    {
      name: '白玩1',
      imageUrl: '/mhxy-items/sheet-fixed-47.png',
      priceW: 0,
      levelLabel: '',
      description: '不计收益可留 0',
      panel: 'yaksha_white',
      sortOrder: 0,
    },
    {
      name: '白玩2',
      imageUrl: '/mhxy-items/sheet-fixed-48.png',
      priceW: 0,
      levelLabel: '',
      description: '',
      panel: 'yaksha_white',
      sortOrder: 1,
    },
    {
      name: '白玩3',
      imageUrl: '/mhxy-items/sheet-var-16.png',
      priceW: 0,
      levelLabel: '',
      description: '',
      panel: 'yaksha_white',
      sortOrder: 2,
    }
  );

  for (let i = 0; i < 10; i++) {
    rows.push({
      name: `奖励 ${i + 1}`,
      imageUrl: `/mhxy-items/sheet-fixed-${pad2(37 + i)}.png`,
      priceW: 10,
      levelLabel: '',
      description: '',
      panel: 'yaksha_reward',
      sortOrder: i,
    });
  }

  for (let i = 0; i < 24; i++) {
    rows.push({
      name: `场景掉落 ${i + 1}`,
      imageUrl: `/mhxy-items/sheet-var-${pad2((i % 16) + 1)}.png`,
      priceW: 5 + (i % 8) * 3,
      levelLabel: '',
      description: '',
      panel: 'scene',
      sortOrder: i,
    });
  }

  return rows;
}
