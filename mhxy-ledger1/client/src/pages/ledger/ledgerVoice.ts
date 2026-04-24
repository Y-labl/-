/**
 * 记账台：语音输入解析与物品名匹配（Web Speech API，中文）
 */

import type { LedgerItemDef } from './ledgerData';

export type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives?: number;
  start(): void;
  stop(): void;
  abort?(): void;
  onresult:
    | ((
        this: SpeechRecognitionLike,
        ev: { results: SpeechRecognitionResultList; resultIndex?: number },
      ) => void)
    | null;
  onerror: ((this: SpeechRecognitionLike, ev: { error: string }) => void) | null;
  onend: ((this: SpeechRecognitionLike, ev: Event) => void) | null;
};

export type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

export function getBrowserSpeechRecognitionConstructor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') return null;
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

/** 去掉口语前缀/尾词，便于匹配格子名称 */
export function normalizeVoiceNameQuery(raw: string): string {
  let s = raw.trim().replace(/\s+/g, ' ');
  s = s.replace(
    /^(给我|我要|帮我|给我来|帮我记|添加|加一下|加|来个|来一个|再来一个|再记一个|记载|记录|记账|来|上)+/u,
    '',
  );
  s = s.replace(/(的|吧|啊|呀|呢|嗯|哈|哦)+$/u, '').trim();
  return s;
}

const VOICE_QTY_CLASS = '个|只|份|枚|张|块|本|颗|条|件|把';
const CN_QTY_WORD: Record<string, number> = {
  两: 2,
  二: 2,
  三: 3,
  四: 4,
  五: 5,
  六: 6,
  七: 7,
  八: 8,
  九: 9,
  十: 10,
};

function parseQtyToken(tok: string): number {
  const n = parseInt(tok, 10);
  if (!Number.isNaN(n) && /^\d{1,4}$/.test(tok)) {
    return Math.min(999, Math.max(1, n));
  }
  const c = CN_QTY_WORD[tok];
  return c != null ? Math.min(999, c) : 1;
}

/** 口语「八十级」→「80级」，与物品库里「80级武器」等名称对齐（须最长优先） */
const SPOKEN_LEVEL_TO_DIGIT: [string, string][] = [
  ['一百六十', '160'],
  ['一百五十', '150'],
  ['一百四十', '140'],
  ['一百三十', '130'],
  ['一百二十五', '125'],
  ['一百二十', '120'],
  ['一百二', '120'],
  ['一百', '100'],
  ['九十', '90'],
  ['八十', '80'],
  ['七十', '70'],
  ['六十', '60'],
];

const SPOKEN_LEVEL_PREFIXES = SPOKEN_LEVEL_TO_DIGIT.map(([cn]) => cn) as unknown as readonly string[];

function replaceSpokenChineseLevels(compressed: string): string {
  let s = compressed.trim();
  if (!s) return s;
  if (s.startsWith('八零级')) {
    return `80级${s.slice(3)}`;
  }
  for (const [cn, num] of SPOKEN_LEVEL_TO_DIGIT) {
    const head = `${cn}级`;
    if (s.startsWith(head)) {
      return `${num}级${s.slice(head.length)}`;
    }
  }
  return s;
}

/** 去掉开头的「NN级」，用于「八十级晶石」→「晶石」这类分档物品 */
function stripLeadingSpokenLevel(compressed: string): string {
  const s = compressed.trim();
  if (!s) return s;
  const d = s.match(/^(\d{1,3})级/u);
  if (d) {
    const rest = s.slice(d[0].length);
    return rest || s;
  }
  for (const lv of SPOKEN_LEVEL_PREFIXES) {
    const p = `${lv}级`;
    if (s.startsWith(p)) {
      const rest = s.slice(p.length);
      return rest || s;
    }
  }
  if (s.startsWith('八零级')) {
    const rest = s.slice(3);
    return rest || s;
  }
  return s;
}

/** 与物品库「60级武器」「80级装备」等整行名称一致时不再归并到「书铁」 */
const TIER_WEAPON_OR_ARMOR = /^\d{1,3}级(武器|装备)$/u;

/** 无等级时的口语 → 默认账本里的「书铁」等 */
function applySpokenLedgerAliases(compressed: string): string {
  const s = compressed.trim();
  if (!s) return s;
  if (s.includes('灵饰书')) return s;
  if (s.includes('宝宝') && s.includes('武器')) return s;
  if (TIER_WEAPON_OR_ARMOR.test(s)) return s;
  if (s.includes('制造指南') || s.includes('百炼精铁') || (s.includes('指南书') && !s.includes('灵饰'))) {
    return '书铁';
  }
  if (s.includes('武器')) {
    return '书铁';
  }
  return s;
}

/** 在紧凑字符串上做中文等级数字化、再剥离前缀或别名，供语音匹配 */
export function prepareVoiceNameForLedgerMatch(compressedName: string): string {
  const base = compressedName.replace(/\s/g, '');
  if (!base) return '';
  const digitized = replaceSpokenChineseLevels(base);
  if (TIER_WEAPON_OR_ARMOR.test(digitized)) {
    return digitized;
  }
  const stripped = stripLeadingSpokenLevel(digitized);
  const core = stripped !== digitized ? stripped : digitized;
  return applySpokenLedgerAliases(core);
}

/** 从识别文本解析数量与物品关键词，如「3个修炼果」「修炼果 2」「八十级武器两个」 */
export function parseVoiceLedgerCommand(raw: string): { quantity: number; nameQuery: string } {
  const s = raw
    .trim()
    .replace(/[，。、；;．]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!s) return { quantity: 1, nameQuery: '' };

  let m = s.match(/^(\d{1,4})\s*(?:个|只|份|枚|张|块|本|颗)?\s*(.+)$/);
  if (m) {
    const q = Math.min(999, Math.max(1, parseInt(m[1], 10)));
    return { quantity: q, nameQuery: normalizeVoiceNameQuery(m[2].trim()) };
  }
  m = s.match(/^(.+?)\s+(\d{1,4})\s*(?:个|只|份|枚|张|块|本|颗)?$/);
  if (m) {
    const q = Math.min(999, Math.max(1, parseInt(m[2], 10)));
    return { quantity: q, nameQuery: normalizeVoiceNameQuery(m[1].trim()) };
  }
  const tail = new RegExp(`^(.+)(\\d{1,4}|[两二三四五六七八九十])(${VOICE_QTY_CLASS})$`, 'u');
  const tm = s.replace(/\s/g, '').match(tail);
  if (tm) {
    const namePart = tm[1].trim();
    const qty = parseQtyToken(tm[2]);
    if (namePart.length >= 1) {
      return { quantity: qty, nameQuery: normalizeVoiceNameQuery(namePart) };
    }
  }
  return { quantity: 1, nameQuery: normalizeVoiceNameQuery(s) };
}

/** 按标点/空格拆成多段，用于结束录入时批量匹配 */
export function splitVoiceSegments(raw: string): string[] {
  const s = raw
    .trim()
    .replace(/[，。、；;．!！?？]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!s) return [];
  return s.split(' ').map((x) => x.trim()).filter(Boolean);
}

/**
 * 无空格连读时，从左到右贪心匹配最长物品名（如「红玛瑙金银锦盒」）
 */
export function extractItemsGreedyFromTranscript(
  transcript: string,
  items: readonly LedgerItemDef[],
): LedgerItemDef[] {
  const uniq = [...new Map(items.map((i) => [i.name, i])).values()].sort(
    (a, b) => b.name.replace(/\s/g, '').length - a.name.replace(/\s/g, '').length,
  );
  let rest = replaceSpokenChineseLevels(transcript.replace(/\s/g, ''));
  const out: LedgerItemDef[] = [];
  let guard = 0;
  while (rest.length > 0 && guard < 400) {
    guard += 1;
    rest = replaceSpokenChineseLevels(rest);
    let hit: LedgerItemDef | null = null;
    for (const it of uniq) {
      const n = it.name.replace(/\s/g, '');
      if (n.length >= 1 && rest.startsWith(n)) {
        hit = it;
        break;
      }
    }
    if (!hit) {
      rest = rest.slice(1);
      continue;
    }
    out.push(hit);
    rest = rest.slice(hit.name.replace(/\s/g, '').length);
  }
  return out;
}

/**
 * 在格子列表中按名称匹配：优先「识别全文包含物品全名」，其次「物品全名包含识别关键词」（关键词至少 2 字）
 */
export function findBestVoiceLedgerItem(
  nameQuery: string,
  items: readonly LedgerItemDef[],
): LedgerItemDef | null {
  const base = normalizeVoiceNameQuery(nameQuery).replace(/\s/g, '');
  if (!base) return null;
  const prepared = prepareVoiceNameForLedgerMatch(base);
  const queries = prepared === base ? [base] : [prepared, base];

  let best: LedgerItemDef | null = null;
  let bestScore = 0;

  for (const q of queries) {
    if (!q) continue;
    for (const it of items) {
      const n = it.name.replace(/\s/g, '');
      if (!n) continue;

      if (q.includes(n)) {
        const score = n.length * 1000 + 1;
        if (score > bestScore) {
          best = it;
          bestScore = score;
        }
      } else if (q.length >= 2 && n.includes(q)) {
        const score = q.length * 100;
        if (score > bestScore) {
          best = it;
          bestScore = score;
        }
      }
    }
  }
  return best;
}
