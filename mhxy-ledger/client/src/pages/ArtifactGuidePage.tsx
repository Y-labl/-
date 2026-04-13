import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './ArtifactGuidePage.css';
import { api } from '../api';
import { BIZ_DATE_PAGE } from '../utils/pageBizDate';
import { usePageBizDate } from '../utils/usePageBizDate';
import {
  artifactPhaseOf,
  artifactQiOfZhuan,
  artifactZhuanOfQi,
  normalizeArtifactDayPair,
  pickOneQiOneZhuanFromHits,
  splitSelectedArtifactsByPhase,
} from '../utils/artifacts';

type Phase = '起' | '转';
type Star = 1 | 2 | 3 | 4 | 5;

type MaterialItem = {
  name: string;
  qty: number;
  /** 品（药/烹饪常用），不确定时可留空；默认按“最低品”理解 */
  quality?: number | null;
  /** 若为 true：显示为 “≥{quality}品” */
  qualityIsMin?: boolean;
  note?: string;
};

type ArtifactLine = {
  id: string;
  phase: Phase;
  name: string;
  /** 每星需要准备的材料清单（可为空，逐步补全） */
  materialsByStar: Partial<Record<Star, MaterialItem[]>>;
};

type Stored = {
  version: 1;
  /** 内置数据修订号：仅用于把少量预填条目迁到新版，不覆盖你已改过的神器 */
  dataRev?: number;
  /** 攻略页材料清单当前查看的星级（1–5），持久化到数据库 */
  viewStar?: Star;
  items: ArtifactLine[];
};

function clampViewStar(raw: unknown): Star {
  const n = Math.round(Number(raw));
  if (n === 1 || n === 2 || n === 3 || n === 4 || n === 5) return n;
  return 5;
}

const GUIDE_DATA_REV = 2;

function resetAllMaterialQualities(items: ArtifactLine[]): ArtifactLine[] {
  return items.map((line) => {
    const mbs = { ...line.materialsByStar };
    for (const star of [1, 2, 3, 4, 5] as Star[]) {
      const list = mbs[star];
      if (!list?.length) continue;
      mbs[star] = list.map((m) => ({ ...m, quality: null, qualityIsMin: false }));
    }
    return { ...line, materialsByStar: mbs };
  });
}

function migrateGuideStored(s: Stored): Stored {
  const rev = s.dataRev ?? 0;
  if (rev >= GUIDE_DATA_REV) return { ...s, dataRev: GUIDE_DATA_REV };

  const dflt = defaultItems();
  const duqin = dflt.find((x) => x.id === '起:独弦琴之思');

  let items = s.items;
  if (duqin) {
    items = items.map((it) => {
      if (it.id !== '起:独弦琴之思') return it;
      const first5 = it.materialsByStar[5]?.[0]?.name;
      if (first5 === '召唤兽（指定类型+五行）') {
        return { ...it, materialsByStar: { ...duqin.materialsByStar } };
      }
      return it;
    });
  }

  if (rev < 2) {
    items = resetAllMaterialQualities(items);
  }

  return { ...s, items, dataRev: GUIDE_DATA_REV };
}

function seedAllStars(list: MaterialItem[]): Partial<Record<Star, MaterialItem[]>> {
  return { 1: list, 2: list, 3: list, 4: list, 5: list };
}

function defaultItems(): ArtifactLine[] {
  const qi = [
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
  ];
  const zhuan = [
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
  ];

  // 物品名与数量参考公开攻略；品质默认不预填（自行双击或编辑补）。
  const qiSeed: Record<string, MaterialItem[]> = {
    '轩辕剑之陨': [
      { name: '随机烹饪', qty: 10, note: '最多 10 个（数量不定）' },
      { name: '蛟龙', qty: 1 },
      { name: '凤凰', qty: 1 },
      { name: '噬天虎', qty: 1, note: '老虎' },
      { name: '龙龟', qty: 1, note: '大海龟' },
    ],
    '黄金甲之谜': [{ name: '三级药', qty: 5, note: '指定类型' }],
    '泪痕碗之念': [
      { name: '三级药', qty: 5, note: '指定类型' },
      { name: '1级家具', qty: 1, note: '数量随星级变化' },
      { name: '2级家具', qty: 1, note: '数量随星级变化' },
    ],
    '墨魂笔之踪': [{ name: '三级药', qty: 5, note: '指定类型' }],
    '月光草之逝': [{ name: '三级药', qty: 1, note: '总品质 500（合计）' }],
    '昆仑镜之忆': [{ name: '烹饪', qty: 5 }],
    '玲珑结之愿': [{ name: '三级药', qty: 5 }],
    '明火珠之影': [{ name: '70级武器', qty: 5, note: '指定范围' }],
    '噬魂齿之争': [
      { name: '烹饪', qty: 5, note: '指定' },
      { name: '三级药', qty: 5, note: '指定' },
    ],
    '四神鼎之怨': [{ name: '血色茶花', qty: 130, note: '约 130 个' }],
    '独弦琴之思': [
      {
        name: '镇兽台·金（代表金）',
        qty: 1,
        note: '灵符女娲×1；可用凤凰替代（难度略升）。宠自身五行不限，按阵台提示摆',
      },
      {
        name: '镇兽台·木（代表木）',
        qty: 1,
        note: '芙蓉仙子×1。宠自身五行不限',
      },
      {
        name: '镇兽台·水（代表水）',
        qty: 1,
        note: '幽灵×1；可用野鬼替代（难度略升）。宠自身五行不限',
      },
      {
        name: '镇兽台·火（代表火）',
        qty: 1,
        note: '星灵仙子×1。宠自身五行不限',
      },
      {
        name: '镇兽台·土（代表土）',
        qty: 1,
        note: '踏云兽×1；可用牛妖替代（难度略升）。宠自身五行不限',
      },
      {
        name: '【分支一·含弹琴】',
        qty: 1,
        note:
          '网易百科流程：分支一在奏乐环节；需三级药（≥90品）×5 给吴天兵。五开/多开奏乐协作成本高',
      },
      {
        name: '三级药（分支一·吴天兵）',
        qty: 5,
        note: '仅走分支一时准备',
      },
      {
        name: '【分支二·不弹琴·五开推荐】',
        qty: 1,
        note:
          '叶子猪攻略写明：分支二可跳过弹琴；流程里给守门天将烹饪（数量以 NPC 对话为准，常见备 5 个）',
      },
      {
        name: '烹饪（分支二·守门天将）',
        qty: 5,
        note: '仅走分支二时准备；不弹琴',
      },
    ],
    '清泽谱之惠': [{ name: '烹饪', qty: 5, note: '或 5 个高级烹饪' }],
    '星斗盘之约': [
      { name: '三级药', qty: 5 },
      { name: '2级家具', qty: 5, note: '文中示例：金柳露' },
    ],
    '华光玉之伤': [{ name: '（未明确）', qty: 1, note: '该汇总未给出固定索取物品；以实测为准' }],
    '天罡印之谋': [{ name: '（未明确）', qty: 1, note: '该汇总未给出固定索取物品；以实测为准' }],
    '千机锁之梏': [{ name: '酒', qty: 5 }],
    '莫愁铃之恩': [{ name: '三级药', qty: 5 }],
    '鸿蒙石之鉴': [{ name: '（未明确）', qty: 1, note: '该汇总未给出固定索取物品；以实测为准' }],
    '魔息角之怒': [{ name: '（未明确）', qty: 1, note: '该汇总未给出固定索取物品；以实测为准' }],
  };

  const zhuanSeed: Record<string, MaterialItem[]> = {
    '命陨轩辕剑': [{ name: '三级药', qty: 5 }],
    '重铸黄金甲': [{ name: '三级药', qty: 5 }],
    '情葬泪痕碗': [{ name: '三级药', qty: 5 }],
    '义绝墨魂笔': [{ name: '三级药', qty: 5, note: '相同类型' }],
    '历劫月光草': [{ name: '烹饪', qty: 5 }],
    '离焰明火珠': [{ name: '60级武器', qty: 5, note: '指定类型' }],
    '魔灭噬魂齿': [{ name: '三级药', qty: 5 }],
    '计斗四神鼎': [{ name: '酒', qty: 5, note: '相同类型' }],
    '悲瑟独弦琴': [{ name: '三级药', qty: 6 }],
    '忧思华光玉': [{ name: '三级药', qty: 5 }],
    '迷踪清泽谱': [{ name: '三级药', qty: 5 }],
    '魂印星斗盘': [{ name: '三级药', qty: 5 }],
    '觅影玲珑结': [{ name: '三级药', qty: 5 }],
    '神归昆仑镜': [{ name: '（未明确）', qty: 1, note: '该汇总未写明索取物品；以实测为准' }],
    '诡夺天罡印': [{ name: '（未明确）', qty: 1, note: '该汇总未写明索取物品；以实测为准' }],
  };

  const mk = (phase: Phase, name: string): ArtifactLine => {
    const seed = phase === '起' ? qiSeed[name] : zhuanSeed[name];
    return {
      id: `${phase}:${name}`,
      phase,
      name,
      materialsByStar: seed ? seedAllStars(seed) : {},
    };
  };

  return [...qi.map((n) => mk('起', n)), ...zhuan.map((n) => mk('转', n))];
}

function allArtifactNames(): string[] {
  return defaultItems().map((x) => x.name);
}

/** 神器 OCR 清洗：兼容全角标点、异体「转」、NFKC 归一化（减少「看着一样码点不同」导致整段匹配失败） */
function normalizeArtifactOcrText(raw: string): string {
  let s = String(raw || '')
    .normalize('NFKC')
    .replace(/[：︰﹕∶]/g, ':')
    .replace(/[轉転]/g, '转')
    .replace(/\s+/g, '');
  s = s.replace(/（未完成）/g, '').replace(/\(未完成\)/g, '').replace(/未完成/g, '');
  s = s.replace(/[（）()]/g, '');
  return s;
}

/** 解析「起 … 转 …」两段（允许冒号前后有空格、起前可有杂字）；失败返回 null */
function parseQiZhuanSegments(t: string): { qiSeg: string; zhuanSeg: string } | null {
  const s = String(t || '').trim();
  const m = s.match(/起\s*:\s*(.+?)\s*转\s*:\s*(.+)$/u);
  if (m) return { qiSeg: m[1].trim(), zhuanSeg: m[2].trim() };
  return null;
}

function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  const dp = new Array(n + 1);
  for (let j = 0; j <= n; j++) dp[j] = j;
  for (let i = 1; i <= m; i++) {
    let prev = dp[0];
    dp[0] = i;
    for (let j = 1; j <= n; j++) {
      const tmp = dp[j];
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
      dp[j] = Math.min(dp[j] + 1, dp[j - 1] + 1, prev + cost);
      prev = tmp;
    }
  }
  return dp[n];
}

/** 标准神器名 n 中，出现在 seg 里的最长连续子串长度（≥2 才有意义；用于 OCR 个别错字） */
function longestCanonSubstringInSeg(n: string, seg: string): number {
  const s = String(n || '');
  const t = String(seg || '');
  if (!s || !t) return 0;
  let best = 0;
  for (let i = 0; i < s.length; i++) {
    for (let j = i + 2; j <= s.length; j++) {
      if (t.includes(s.slice(i, j))) best = Math.max(best, j - i);
    }
  }
  return best;
}

/** 段内标准名整段包含（优先最长名，避免短串误命中） */
function pickExactArtifactInSeg(seg: string, candidates: readonly string[]): string | null {
  const t = String(seg || '').trim();
  if (!t) return null;
  const hits = candidates.filter((n) => n && t.includes(n));
  if (!hits.length) return null;
  hits.sort((a, b) => b.length - a.length || a.localeCompare(b, 'zh-CN'));
  return hits[0];
}

/**
 * 在候选标准名中，按「与 OCR 片段最长公共连续子串」选一条；并列时用与片段的编辑距离决选（不再直接放弃）。
 * 若子串太短，最后用编辑距离兜底（仅当与最近候选差距足够小）。
 */
function fuzzyPickOneArtifact(seg: string, candidates: readonly string[]): string | null {
  const t = String(seg || '').trim();
  if (!t) return null;
  const scored = candidates.map((name) => ({
    name,
    len: longestCanonSubstringInSeg(name, t),
  }));
  scored.sort((a, b) => b.len - a.len || b.name.length - a.name.length || a.name.localeCompare(b.name, 'zh-CN'));
  const bestLen = scored[0]?.len ?? 0;
  if (bestLen < 2) {
    return pickClosestArtifactByEdit(seg, candidates);
  }
  const tied = scored.filter((s) => s.len === bestLen);
  tied.sort(
    (a, b) =>
      levenshtein(t, a.name) - levenshtein(t, b.name) || a.name.localeCompare(b.name, 'zh-CN'),
  );
  return tied[0]!.name;
}

/** 编辑距离最近的标准名；与最近名差距过大则放弃 */
function pickClosestArtifactByEdit(seg: string, candidates: readonly string[]): string | null {
  const t = String(seg || '').trim();
  if (!t || t.length < 2) return null;
  let best: { name: string; d: number } | null = null;
  for (const name of candidates) {
    const d = levenshtein(t, name);
    if (!best || d < best.d) best = { name, d };
  }
  if (!best) return null;
  const maxLen = Math.max(t.length, best.name.length);
  const allow = Math.max(2, Math.ceil(maxLen / 2));
  if (best.d > allow) return null;
  return best.name;
}

/**
 * 有「起:…转:…」结构时优先：分段精确匹配 → 分段模糊；避免全局后缀先凑满 2 个错名导致永远走不到分段逻辑。
 */
function tryPhaseAwarePickFromOcr(t: string, names: string[]): string[] {
  const parsed = parseQiZhuanSegments(t);
  if (!parsed) return [];
  const qiNames = names.filter((n) => artifactPhaseOf(n) === '起');
  const zhuanNames = names.filter((n) => artifactPhaseOf(n) === '转');
  const qi = pickExactArtifactInSeg(parsed.qiSeg, qiNames) ?? fuzzyPickOneArtifact(parsed.qiSeg, qiNames);
  const zhuan =
    pickExactArtifactInSeg(parsed.zhuanSeg, zhuanNames) ?? fuzzyPickOneArtifact(parsed.zhuanSeg, zhuanNames);
  if (!qi || !zhuan) return [];
  return [qi, zhuan];
}

function pickArtifactsFromOcrText(ocrText: string): string[] {
  const raw = String(ocrText || '');
  if (!raw.trim()) return [];
  const t = normalizeArtifactOcrText(raw);
  const names = allArtifactNames();

  const phasePair = tryPhaseAwarePickFromOcr(t, names);
  if (phasePair.length === 2) return normalizeArtifactDayPair(phasePair);

  // ① 无清晰起/转分段时：整段「标准名包含」
  const exactHits: string[] = [];
  for (const n of names) {
    if (n && t.includes(n)) exactHits.push(n);
  }
  if (exactHits.length >= 2) {
    const oneEach = pickOneQiOneZhuanFromHits(exactHits);
    if (oneEach) return normalizeArtifactDayPair(oneEach);
    return normalizeArtifactDayPair(exactHits.slice(0, 2));
  }

  // ② 容错：按“公共后缀”匹配（例如：OCR 可能只识别到「…之谜」「…谱」）
  const suffixLen = (s: string) => Math.min(4, Math.max(2, Math.floor(s.length / 2)));
  const scored: { name: string; score: number }[] = [];
  for (const n of names) {
    const k = String(n || '').trim();
    if (!k) continue;
    const suf = k.slice(-suffixLen(k));
    if (!suf) continue;
    const idx = t.indexOf(suf);
    if (idx < 0) continue;
    let score = suf.length * 10;
    const window = t.slice(Math.max(0, idx - 6), Math.min(t.length, idx + suf.length + 6));
    if (window.includes('起:')) score += 5;
    if (window.includes('转:')) score += 5;
    scored.push({ name: k, score });
  }
  scored.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name, 'zh-CN'));

  const out: string[] = [];
  for (const x of [...exactHits, ...scored.map((s) => s.name)]) {
    if (!x || out.includes(x)) continue;
    out.push(x);
    if (out.length >= 2) break;
  }
  if (out.length >= 2) return normalizeArtifactDayPair(out.slice(0, 2));

  return out;
}

function isLikelyImageFile(f: File | null | undefined): f is File {
  if (!f) return false;
  if (f.type.startsWith('image/')) return true;
  return /\.(png|jpe?g|webp|bmp|gif)$/i.test(f.name);
}

/** 从剪贴板取第一张图片（兼容 Windows 截图、部分浏览器 type 为空） */
function imageFileFromClipboardData(dt: DataTransfer | null): File | null {
  if (!dt) return null;
  const fromList = dt.files?.length ? dt.files[0] : null;
  if (isLikelyImageFile(fromList)) return fromList;
  if (!dt.items?.length) return null;
  for (const it of Array.from(dt.items)) {
    if (it.kind === 'file') {
      const f = it.getAsFile();
      if (isLikelyImageFile(f)) return f;
      continue;
    }
    if (it.type?.startsWith('image/')) {
      const f = it.getAsFile();
      if (f) return f;
    }
  }
  return null;
}

function imageFileFromDataTransfer(dt: DataTransfer | null): File | null {
  if (!dt?.files?.length) return null;
  const f = dt.files[0];
  return isLikelyImageFile(f) ? f : null;
}

async function preprocessImageForOcr(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) return file;
  try {
    const bmp = await createImageBitmap(file);
    const scale = 3;
    const w = Math.max(1, Math.floor(bmp.width * scale));
    const h = Math.max(1, Math.floor(bmp.height * scale));
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) return file;

    // Upscale + mild contrast helps small, thin fonts.
    ctx.imageSmoothingEnabled = false;
    ctx.filter = 'contrast(1.45) saturate(0)';
    ctx.drawImage(bmp, 0, 0, w, h);

    const blob: Blob | null = await new Promise((resolve) =>
      canvas.toBlob((b) => resolve(b), 'image/png', 1.0),
    );
    if (!blob) return file;
    return new File([blob], file.name.replace(/\.\w+$/, '') + '.png', { type: 'image/png' });
  } catch {
    return file;
  }
}

/** 已填品质时去掉备注里的（…）与 (…) 攻略提示，保留「指定类型」等短语 */
function materialNoteForDisplay(note: string, stripParentheticalHints: boolean): string {
  const t = note.trim();
  if (!t) return '';
  if (!stripParentheticalHints) return t;
  return t
    .replace(/（[^）]*）/g, '')
    .replace(/\([^)]*\)/g, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/[，,、]\s*$/g, '')
    .trim();
}

function fmtMat(x: MaterialItem) {
  const qn = x.quality != null && Number.isFinite(Number(x.quality)) ? Number(x.quality) : null;
  const q =
    qn != null && qn > 0 ? `（${x.qualityIsMin ? '≥' : ''}${qn}品）` : '';
  const qty = Number.isFinite(Number(x.qty)) && Number(x.qty) > 1 ? `×${Math.floor(Number(x.qty))}` : '';
  const noteRaw = (x.note || '').trim();
  const noteOut = materialNoteForDisplay(noteRaw, qn != null && qn > 0);
  return `${x.name}${q}${qty}${noteOut ? ` · ${noteOut}` : ''}`;
}

export function ArtifactGuidePage() {
  const [bizDate] = usePageBizDate(BIZ_DATE_PAGE.artifactGuide);
  const [q, setQ] = useState('');
  const [editTarget, setEditTarget] = useState<{ id: string; star: Star } | null>(null);
  const [draftText, setDraftText] = useState('');
  const [todaySelected, setTodaySelected] = useState<string[]>([]);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadErr, setUploadErr] = useState('');
  const [lastOcrText, setLastOcrText] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [viewMode, setViewMode] = useState<'today' | 'all'>('all');
  const [bossImageByName, setBossImageByName] = useState<Record<string, string>>({});
  const [guideContentByName, setGuideContentByName] = useState<Record<string, any>>({});
  const bossUploadRef = useRef<HTMLInputElement | null>(null);
  const bossUploadTargetRef = useRef<string>('');
  const pasteZoneRef = useRef<HTMLDivElement | null>(null);

  const [stored, setStored] = useState<Stored>(() => ({ version: 1, dataRev: GUIDE_DATA_REV, items: defaultItems() }));
  const [guideBusy, setGuideBusy] = useState(true);
  const [guideErr, setGuideErr] = useState('');
  const saveTimerRef = useRef<number | null>(null);

  const persistGuideState = useCallback((next: Stored) => {
    if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(() => {
      void api.artifactGuideStatePut({ ...next, dataRev: next.dataRev ?? GUIDE_DATA_REV }).catch(() => {});
    }, 450);
  }, []);

  const viewStar = clampViewStar(stored.viewStar);
  const setViewStar = useCallback(
    (s: Star) => {
      const next = { ...stored, viewStar: s };
      setStored(next);
      persistGuideState(next);
    },
    [stored, persistGuideState],
  );

  useEffect(() => {
    setUploadErr('');
    void api
      .artifactDaySelectedGet(bizDate)
      .then((r) => {
        const raw = Array.isArray(r.selected) ? r.selected.slice(0, 2) : [];
        const sel = raw.length === 2 ? normalizeArtifactDayPair(raw) : raw;
        setTodaySelected(sel);
        setViewMode(sel.length === 2 ? 'today' : 'all');
      })
      .catch(() => {
        setTodaySelected([]);
        setViewMode('all');
      });
  }, [bizDate]);

  useEffect(() => {
    let cancelled = false;
    setGuideBusy(true);
    setGuideErr('');
    void api
      .artifactGuideStateGet()
      .then((r) => {
        if (cancelled) return;
        const s = r?.state as Stored | null;
        if (s && s.version === 1 && Array.isArray(s.items)) {
          setStored(migrateGuideStored(s));
        } else {
          const empty = { version: 1 as const, dataRev: GUIDE_DATA_REV, items: defaultItems() };
          setStored(empty);
          void api.artifactGuideStatePut(empty).catch(() => {});
        }
      })
      .catch((e) => {
        if (cancelled) return;
        setGuideErr(e instanceof Error ? e.message : '加载失败');
        setStored({ version: 1, dataRev: GUIDE_DATA_REV, items: defaultItems() });
      })
      .finally(() => {
        if (!cancelled) setGuideBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleUpload = async (file: File) => {
    if (!isLikelyImageFile(file)) {
      setUploadErr('请选择图片文件（PNG、JPG、WebP 等）');
      return;
    }
    setUploadErr('');
    setUploadBusy(true);
    try {
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(file);
      });
      const pre = await preprocessImageForOcr(file);
      const r = await api.smartOcr(pre);
      const ocrText = String(r.ocrText || '');
      setLastOcrText(ocrText);
      const picked = pickArtifactsFromOcrText(ocrText);
      if (picked.length !== 2) {
        const brief = ocrText.trim() ? `OCR：${ocrText.trim().slice(0, 90)}${ocrText.trim().length > 90 ? '…' : ''}` : 'OCR：空';
        throw new Error(`未识别出 2 种神器名称，请换更清晰截图（包含两条神器名称的区域）。${brief}`);
      }
      try {
        await api.artifactDaySelectedPut({ bizDate, selected: picked });
      } catch (e) {
        const msg = e instanceof Error ? e.message : '写入失败';
        if (/Cannot\s+PUT/i.test(msg) || /day-selected/i.test(msg)) {
          throw new Error(`${msg}。请确认已重启服务端，并执行：server 目录 node scripts/migrate-v38.js`);
        }
        throw e;
      }
      setTodaySelected(picked);
    } catch (e) {
      setUploadErr(e instanceof Error ? e.message : '识别失败');
    } finally {
      setUploadBusy(false);
    }
  };

  const clearPreview = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl('');
    setLastOcrText('');
    setUploadErr('');
  }, [previewUrl]);

  const tryPasteFromClipboard = async (e: React.ClipboardEvent) => {
    if (uploadBusy) return;
    const file = imageFileFromClipboardData(e.clipboardData);
    if (!file) {
      setUploadErr(
        '剪贴板里未检测到图片。请先截图或复制图片，点一下灰框后再按 Ctrl+V；或将图片文件拖入灰框。',
      );
      return;
    }
    e.preventDefault();
    await handleUpload(file);
  };

  const items = useMemo(() => {
    const kw = q.trim();
    const onlyToday = viewMode === 'today' && todaySelected.length === 2;
    const todaySet = onlyToday ? new Set(todaySelected) : null;
    return stored.items
      .filter((x) => (todaySet ? todaySet.has(x.name) : true))
      .filter((x) => (kw ? x.name.includes(kw) : true))
      .sort((a, b) => {
        if (a.phase !== b.phase) return a.phase === '起' ? -1 : 1;
        return a.name.localeCompare(b.name, 'zh-CN');
      });
  }, [q, stored.items, todaySelected, viewMode]);

  const allModePairs = useMemo(() => {
    const kw = q.trim();
    const byName = new Map<string, ArtifactLine>();
    for (const it of stored.items) byName.set(it.name, it);
    const qItems = stored.items
      .filter((x) => x.phase === '起')
      .filter((x) => (kw ? x.name.includes(kw) || (artifactZhuanOfQi(x.name) || '').includes(kw) : true))
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
    return qItems.map((qi) => {
      const zName = artifactZhuanOfQi(qi.name);
      const z = zName ? byName.get(zName) || null : null;
      return { qi, zhuan: z };
    });
  }, [q, stored.items]);

  useEffect(() => {
    // 懒加载：仅拉取当前列表中会渲染的神器图片（自定义覆盖）
    const names = Array.from(new Set(items.map((x) => x.name))).filter(Boolean);
    let cancelled = false;
    (async () => {
      for (const n of names) {
        if (cancelled) return;
        if (bossImageByName[n]) continue;
        try {
          const r = await api.artifactBossImageGet(n);
          if (cancelled) return;
          if (r.imageUrl) {
            setBossImageByName((m) => (m[n] ? m : { ...m, [n]: r.imageUrl as string }));
          }
        } catch {
          /* ignore */
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [items, bossImageByName]);

  useEffect(() => {
    // 懒加载：拉取攻略内容（DB），不在前端内置
    const names = Array.from(new Set(items.map((x) => x.name))).filter(Boolean);
    const missing = names.filter((n) => !guideContentByName[n]);
    if (!missing.length) return;
    let cancelled = false;
    void api
      .artifactGuideContentGet(missing)
      .then((r) => {
        if (cancelled) return;
        const next: Record<string, any> = {};
        for (const it of r.items || []) {
          if (!it?.name) continue;
          next[String(it.name)] = it.content || null;
        }
        setGuideContentByName((m) => ({ ...m, ...next }));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [items, guideContentByName]);

  const openEdit = (id: string, star: Star) => {
    const it = stored.items.find((x) => x.id === id);
    const list = it?.materialsByStar?.[star] || [];
    setDraftText(list.map(fmtMat).join('\n'));
    setEditTarget({ id, star });
  };

  const applyEdit = () => {
    if (!editTarget) return;
    const { id, star } = editTarget;
    const lines = draftText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    // 输入格式：物品名（120品）×2 · 备注
    const parsed: MaterialItem[] = lines.map((line) => {
      const [left, noteRaw] = line.split('·').map((s) => s.trim());
      const note = noteRaw || '';

      let name = left;
      let quality: number | null = null;
      let qualityIsMin = false;
      let qty = 1;

      const mQ = left.match(/（\s*(≥)?\s*(\d{1,3})\s*品\s*）/);
      if (mQ) {
        qualityIsMin = !!mQ[1];
        quality = Math.floor(Number(mQ[2]));
        name = name.replace(mQ[0], '').trim();
      }
      const mQty = name.match(/×\s*(\d+)\s*$/);
      if (mQty) {
        qty = Math.max(1, Math.floor(Number(mQty[1])));
        name = name.replace(mQty[0], '').trim();
      }

      const q = quality != null && quality > 0 ? quality : null;
      return { name, qty, quality: q, qualityIsMin: q != null ? qualityIsMin : false, note };
    });

    const nextItems = stored.items.map((x) => {
      if (x.id !== id) return x;
      return {
        ...x,
        materialsByStar: {
          ...x.materialsByStar,
          [star]: parsed,
        },
      };
    });
    const next: Stored = { ...stored, items: nextItems };
    setStored(next);
    persistGuideState(next);
    setEditTarget(null);
  };

  const clearStar = (id: string, star: Star) => {
    const it = stored.items.find((x) => x.id === id);
    if (!it) return;
    const nextItems = stored.items.map((x) => {
      if (x.id !== id) return x;
      const nextMap = { ...x.materialsByStar };
      delete (nextMap as any)[star];
      return { ...x, materialsByStar: nextMap };
    });
    const next: Stored = { ...stored, items: nextItems };
    setStored(next);
    persistGuideState(next);
  };

  const editQualityByDblClick = (artifactId: string, star: Star, idx: number) => {
    const it = stored.items.find((x) => x.id === artifactId);
    const list = it?.materialsByStar?.[star] || [];
    const target = list[idx];
    if (!target) return;

    const cur = target.quality != null ? String(target.quality) : '';
    const nextRaw = window.prompt(`修改品质（留空=清除）\n${it?.name || ''} · ${star}★ · ${target.name}`, cur);
    if (nextRaw == null) return;
    const s = nextRaw.trim();
    const nextQ = s ? Math.floor(Number(s)) : null;
    if (s && (!Number.isFinite(Number(nextQ)) || Number(nextQ) < 0)) return;
    const storedQ = nextQ != null && nextQ > 0 ? nextQ : null;

    const nextItems = stored.items.map((x) => {
      if (x.id !== artifactId) return x;
      const prevList = x.materialsByStar?.[star] || [];
      const newList = prevList.map((m, i) =>
        i === idx ? { ...m, quality: storedQ, qualityIsMin: storedQ != null ? true : false } : m,
      );
      return { ...x, materialsByStar: { ...x.materialsByStar, [star]: newList } };
    });
    const next: Stored = { ...stored, items: nextItems };
    setStored(next);
    persistGuideState(next);
  };

  const stars: Star[] = [1, 2, 3, 4, 5];

  const lockAsToday = useCallback(
    async (it: ArtifactLine) => {
      const ph = artifactPhaseOf(it.name);
      if (!ph) return;
      const cur = splitSelectedArtifactsByPhase(todaySelected);
      const nextQi =
        ph === '起' ? it.name : cur.qi ?? artifactQiOfZhuan(it.name);
      const nextZhuan =
        ph === '转' ? it.name : cur.zhuan ?? artifactZhuanOfQi(it.name);
      if (!nextQi || !nextZhuan) {
        setUploadErr('无法自动凑齐「起/转」两条神器，请先通过截图识别设置今日神器。');
        return;
      }
      const picked = normalizeArtifactDayPair([nextQi, nextZhuan]);
      try {
        await api.artifactDaySelectedPut({ bizDate, selected: picked });
        setTodaySelected(picked);
        setViewMode('today');
        setUploadErr('');
      } catch (e) {
        setUploadErr(e instanceof Error ? e.message : '写入失败');
      }
    },
    [bizDate, todaySelected],
  );

  const renderCard = (it: ArtifactLine, opts?: { showLock?: boolean }) => {
    const list = it.materialsByStar?.[viewStar] || [];
    const guide = guideContentByName[it.name] || null;
    const bossUrl = bossImageByName[it.name] || guide?.bossImageUrl || '';
    return (
      <div key={it.id} className="card artifact-guide-card">
        <div className="artifact-guide-card-head">
          <div className="artifact-guide-card-title">
            <span style={{ marginRight: 8, color: 'var(--muted)', fontSize: '0.82rem' }}>{it.phase}：</span>
            {it.name}
          </div>
          <div className="artifact-guide-card-actions">
            {opts?.showLock ? (
              <button
                type="button"
                className="btn btn-ghost btn-sm artifact-guide-lock-btn"
                aria-label="锁定为今日神器"
                onClick={() => void lockAsToday(it)}
              >
                <svg
                  className="artifact-guide-lock-ic"
                  width="26"
                  height="26"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden
                >
                  <path
                    d="M7 11V8a5 5 0 0 1 10 0v3"
                    stroke="#ffffff"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <rect
                    x="6"
                    y="11"
                    width="12"
                    height="10"
                    rx="2"
                    stroke="#ffffff"
                    strokeWidth="3"
                  />
                </svg>
              </button>
            ) : null}
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => openEdit(it.id, viewStar)}>
              编辑 {viewStar}★
            </button>
            {list.length ? (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => clearStar(it.id, viewStar)}
                title="清空该星级材料"
              >
                清空
              </button>
            ) : null}
          </div>
        </div>

        {list.length ? (
          <ul className="artifact-guide-mats">
            {list.map((m, idx) => (
              <li
                key={idx}
                title="双击修改品质"
                onDoubleClick={() => editQualityByDblClick(it.id, viewStar, idx)}
                style={{ cursor: 'pointer' }}
              >
                {fmtMat(m)}
              </li>
            ))}
          </ul>
        ) : (
          <div className="muted" style={{ fontSize: '0.88rem' }}>
            未填写。可点右上角“编辑 {viewStar}★”补充你区服/你习惯的准备清单。
          </div>
        )}

        <div style={{ marginTop: 10 }}>
          <div className="muted" style={{ fontSize: '0.82rem', fontWeight: 700, marginBottom: 6 }}>
            攻略要点
          </div>
          {guide ? (
            <>
              {guide.overview?.length ? (
                <>
                  <div className="muted" style={{ fontSize: '0.78rem', fontWeight: 800, margin: '2px 0 6px' }}>
                    总览
                  </div>
                  <ul className="artifact-guide-mats">
                    {guide.overview.map((s: string, i: number) => (
                      <li key={`ov:${i}`} title={s}>
                        {s}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}

              {guide.branches?.length ? (
                <>
                  <div className="muted" style={{ fontSize: '0.78rem', fontWeight: 800, margin: '10px 0 6px' }}>
                    分支建议
                  </div>
                  <ul className="artifact-guide-mats">
                    {guide.branches.map((b: any, i: number) => (
                      <li key={`br:${i}`} title={b.title}>
                        <strong>{b.title}</strong>：{b.recommend}
                        {b.why ? <span className="muted">（原因：{b.why}）</span> : null}
                        {b.notes?.length ? (
                          <span className="muted">（注意：{b.notes.filter(Boolean).join('；')}）</span>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}

              {guide.battles?.length ? (
                <>
                  <div className="muted" style={{ fontSize: '0.78rem', fontWeight: 800, margin: '10px 0 6px' }}>
                    战斗流程
                  </div>
                  {guide.battles.map((b: any, bi: number) => (
                    <div key={`bt:${bi}`} style={{ marginTop: bi ? 10 : 0 }}>
                      <div style={{ fontWeight: 900, color: 'rgba(255,255,255,0.86)', fontSize: '0.88rem' }}>
                        {b.title}
                      </div>
                      <ul className="artifact-guide-mats" style={{ marginTop: 6 }}>
                        {b.steps.map((s: string, si: number) => (
                          <li key={`bt:${bi}:${si}`} title={s}>
                            {s}
                          </li>
                        ))}
                      </ul>
                      {b.tips?.length ? (
                        <div className="muted" style={{ fontSize: '0.78rem', marginTop: 4 }}>
                          要点：{b.tips.filter(Boolean).join('；')}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </>
              ) : null}
              <div className="muted" style={{ fontSize: '0.78rem', marginTop: 6 }}>
                参考：
                {(guide.sources || []).map((s: any, i: number) => (
                  <span key={s.url}>
                    {i ? ' · ' : ' '}
                    <a href={s.url} target="_blank" rel="noreferrer">
                      {s.title}
                    </a>
                  </span>
                ))}
              </div>
              {bossUrl ? (
                <div style={{ marginTop: 10 }}>
                  <img
                    src={bossUrl}
                    alt={`${it.name} BOSS 战斗图`}
                    style={{
                      maxWidth: '100%',
                      maxHeight: 260,
                      borderRadius: 10,
                      border: '1px solid rgba(148,163,184,0.18)',
                      display: 'block',
                      cursor: 'pointer',
                    }}
                    title="点击可上传替换该神器 BOSS 战斗图"
                    onClick={() => {
                      bossUploadTargetRef.current = it.name;
                      bossUploadRef.current?.click();
                    }}
                  />
                </div>
              ) : (
                <div className="muted" style={{ fontSize: '0.78rem', marginTop: 6 }}>
                  BOSS 战斗图：我会逐步补默认直链；你也可以点下方按钮上传自己的截图替换。
                </div>
              )}
              <div style={{ marginTop: 8, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    bossUploadTargetRef.current = it.name;
                    bossUploadRef.current?.click();
                  }}
                >
                  上传/更换战斗图
                </button>
                {bossImageByName[it.name] ? (
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => {
                      void api
                        .artifactBossImageDelete(it.name)
                        .then(() =>
                          setBossImageByName((m) => {
                            const next = { ...m };
                            delete next[it.name];
                            return next;
                          }),
                        )
                        .catch(() => {});
                    }}
                  >
                    恢复默认
                  </button>
                ) : null}
              </div>
            </>
          ) : (
            <div className="muted" style={{ fontSize: '0.82rem' }}>
              攻略加载中/未入库。请先在 server 目录执行：node scripts/migrate-v41.js
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderEmptyZhuan = (qiName: string) => (
    <div className="card artifact-guide-card artifact-guide-card--empty" key={`empty:${qiName}`}>
      <div className="muted" style={{ fontSize: '0.9rem', fontWeight: 800 }}>
        转神器：暂无对应
      </div>
      <div className="muted" style={{ marginTop: 6, fontSize: '0.82rem' }}>
        该起神器暂未收录到“转”列表（或游戏版本未开放）。后续需要的话我再补。
      </div>
    </div>
  );

  return (
    <div>
      <div className="topbar">
        <h2>神器攻略</h2>
      </div>

      <div className="card" style={{ padding: '0.85rem 1rem', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <strong>当日神器（{bizDate}）</strong>
          {todaySelected.length === 2 ? (
            <span className="muted">
              {todaySelected[0]}、{todaySelected[1]}
            </span>
          ) : (
            <span className="muted">未设置。上传截图后本页将只显示当天 2 种神器。</span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 10, marginTop: 10, flexWrap: 'wrap' }}>
          {todaySelected.length === 2 ? (
            <button type="button" className="btn btn-primary" onClick={() => setViewMode('today')}>
              今日神器
            </button>
          ) : null}
          <button type="button" className="btn btn-ghost" onClick={() => setViewMode('all')}>
            显示全部
          </button>
          {previewUrl || lastOcrText || uploadErr ? (
            <button type="button" className="btn btn-ghost" disabled={uploadBusy} onClick={clearPreview}>
              删除截图/清空识别
            </button>
          ) : null}
        </div>
        <div
          ref={pasteZoneRef}
          className="artifact-guide-paste-zone"
          tabIndex={0}
          onPaste={(e) => void tryPasteFromClipboard(e)}
          onClick={() => pasteZoneRef.current?.focus()}
          onDragOver={(ev) => {
            ev.preventDefault();
            ev.dataTransfer.dropEffect = 'copy';
          }}
          onDrop={(ev) => {
            ev.preventDefault();
            if (uploadBusy) return;
            const f = imageFileFromDataTransfer(ev.dataTransfer);
            if (!f) {
              setUploadErr('请拖入图片文件，或点一下灰框后 Ctrl+V 粘贴截图（粘贴后自动识别）。');
              return;
            }
            void handleUpload(f);
          }}
        >
          <div className="artifact-guide-paste-hint">
            <span>
              点一下灰框 → <strong>Ctrl+V</strong> 粘贴截图，<strong>自动识别</strong>；亦可拖入图片
            </span>
            {uploadBusy ? <span className="muted">识别中…</span> : null}
          </div>
          {previewUrl ? (
            <div className="artifact-guide-paste-preview">
              <img src={previewUrl} alt="已粘贴截图预览" />
            </div>
          ) : null}
        </div>
        {uploadErr ? (
          <p style={{ color: 'var(--danger)', margin: '0.6rem 0 0', fontSize: '0.88rem' }}>{uploadErr}</p>
        ) : null}
        {lastOcrText ? (
          <details style={{ marginTop: 10 }}>
            <summary className="muted" style={{ cursor: 'pointer' }}>
              查看 OCR 原文
            </summary>
            <pre
              style={{
                margin: '0.5rem 0 0',
                padding: '0.6rem 0.75rem',
                fontSize: '0.78rem',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                borderRadius: 8,
                background: 'rgba(2,10,18,0.35)',
                border: '1px solid rgba(148,163,184,0.18)',
                color: '#94a3b8',
                maxHeight: 220,
                overflow: 'auto',
              }}
            >
              {lastOcrText.trim()}
            </pre>
          </details>
        ) : null}
      </div>

      <p className="muted" style={{ marginTop: '0.5rem' }}>
        材料清单默认<strong>不预填品质</strong>（按你区服自填）；可<strong>双击材料行</strong>改品质，或点「编辑」批量改。数据保存在数据库（同账号跨设备同步）。
        {guideBusy ? '（加载中…）' : ''}
        {guideErr ? `（加载失败：${guideErr}，已回退到本地缓存）` : ''}
      </p>

      <div className="artifact-guide-controls">
        <input
          className="input"
          placeholder="搜索神器名…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="artifact-guide-star-tabs" role="tablist" aria-label="星级筛选">
          {stars.map((s) => (
            <button
              key={s}
              type="button"
              role="tab"
              aria-selected={viewStar === s}
              className={`artifact-guide-star-tab ${viewStar === s ? 'active' : ''}`}
              onClick={() => setViewStar(s)}
              title={`查看 ${s} 星准备物品`}
            >
              {s}★
            </button>
          ))}
        </div>
      </div>

      {viewMode === 'all' ? (
        <div className="artifact-guide-pair-list">
          {allModePairs.map((p) => (
            <div key={p.qi.id} className="artifact-guide-pair-row">
              {renderCard(p.qi, { showLock: Boolean(q.trim()) })}
              {p.zhuan ? renderCard(p.zhuan, { showLock: Boolean(q.trim()) }) : renderEmptyZhuan(p.qi.name)}
            </div>
          ))}
        </div>
      ) : (
        <div className="artifact-guide-list">
          {items.map((it) => renderCard(it, { showLock: Boolean(q.trim()) }))}
        </div>
      )}

      <input
        ref={bossUploadRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          const name = bossUploadTargetRef.current;
          if (!f || !name) return;
          void api
            .artifactBossImageUpload(name, f)
            .then((r) => setBossImageByName((m) => ({ ...m, [name]: r.imageUrl })))
            .catch(() => {});
        }}
      />

      {editTarget ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="card modal artifact-guide-modal" onMouseDown={(e) => e.stopPropagation()}>
            <h2>
              编辑材料：{stored.items.find((x) => x.id === editTarget.id)?.name} · {editTarget.star}★
            </h2>
            <p className="muted" style={{ fontSize: '0.88rem', marginTop: 0 }}>
              每行一条。格式示例：
              <br />
              <code>金香玉（120品）×2</code>
              <br />
              <code>蛇胆酒（100品） · 可用任意同类高品</code>
            </p>
            <textarea
              className="input"
              style={{ minHeight: 220, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace' }}
              value={draftText}
              onChange={(e) => setDraftText(e.target.value)}
              placeholder="例如：\n金香玉（120品）×2\n蛇胆酒（100品）"
            />
            <div className="row" style={{ marginTop: '1rem' }}>
              <button type="button" className="btn btn-primary" onClick={applyEdit}>
                保存
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setEditTarget(null)}>
                取消
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

