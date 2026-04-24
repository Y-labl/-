const TOKEN_KEY = 'mhxy_ledger_token';

/** 开发留空：走 Vite 代理到本机 3001。打包后若静态站点与 API 不同源，在 client/.env 设置 VITE_API_BASE=http://127.0.0.1:3001 */
function apiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  const base = String(import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  opts: RequestInit & { json?: unknown } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string>),
  };
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(apiUrl(path), {
    ...opts,
    headers,
    body: opts.json !== undefined ? JSON.stringify(opts.json) : opts.body,
  });
  const raw = await res.text();
  let data: unknown = null;
  if (raw) {
    try {
      data = JSON.parse(raw) as unknown;
    } catch {
      data = null;
    }
  }
  if (!res.ok) {
    const obj = data && typeof data === 'object' && data !== null ? (data as { error?: string }) : null;
    const fromJson = obj?.error;
    const fromText = raw?.trim() && raw.length < 400 ? raw.trim() : '';
    throw new Error(fromJson || fromText || res.statusText || '请求失败');
  }
  return data as T;
}

export const api = {
  login: (body: { username: string; password: string }) =>
    request<{ token: string; user: { id: number; username: string } }>('/api/auth/login', {
      method: 'POST',
      json: body,
    }),
  register: (body: { username: string; password: string }) =>
    request<{ token: string; user: { id: number; username: string } }>('/api/auth/register', {
      method: 'POST',
      json: body,
    }),
  me: () => request<{ user: { id: number; username: string } }>('/api/me'),
  categories: () => request<ItemCategory[]>('/api/categories'),
  items: (categoryId?: number) => {
    const q = categoryId ? `?categoryId=${categoryId}` : '';
    return request<Item[]>(`/api/items${q}`);
  },
  itemGain: (body: { itemId: number; quantity?: number; bizDate?: string }) =>
    request('/api/item-gains', { method: 'POST', json: body }),
  cash: (body: { amount: number; note?: string; bizDate?: string }) =>
    request('/api/cash', { method: 'POST', json: body }),
  points: (body: { points: number; note?: string; bizDate?: string }) =>
    request('/api/points', { method: 'POST', json: body }),
  consumptionCharactersList: () => request<{ items: ConsumptionCharacterRow[] }>('/api/consumption-characters'),
  consumptionCharacterCreate: (body: {
    characterName: string;
    levelLabel?: string;
    sect?: string;
    sortOrder?: number;
  }) => request<ConsumptionCharacterResponse>('/api/consumption-characters', { method: 'POST', json: body }),
  consumptionCharacterUpdate: (
    id: number,
    body: { characterName?: string; levelLabel?: string; sect?: string; sortOrder?: number }
  ) => request<{ ok: boolean }>(`/api/consumption-characters/${id}`, { method: 'PATCH', json: body }),
  consumptionCharacterDelete: (id: number) =>
    request<{ ok: boolean }>(`/api/consumption-characters/${id}`, { method: 'DELETE' }),
  consumptionEntry: (body: {
    bizDate?: string;
    characterId?: number;
    characterName?: string;
    levelLabel?: string;
    sect?: string;
    rmbAmount: number;
    gameCoinW?: number;
    note?: string;
  }) =>
    request<ConsumptionEntryResponse>('/api/consumption-entries', { method: 'POST', json: body }),
  consumptionEntriesList: (bizDate: string, limit?: number) => {
    const q = new URLSearchParams({ bizDate });
    if (limit != null) q.set('limit', String(limit));
    return request<{ items: ConsumptionEntryRow[] }>(`/api/consumption-entries?${q}`);
  },
  consumptionDayBoard: (bizDate: string) => {
    const q = new URLSearchParams({ bizDate });
    return request<ConsumptionDayBoardResponse>(`/api/consumption-day-board?${q}`);
  },
  consumptionDayBoardSaveRow: (body: {
    bizDate: string;
    characterId: number;
    rmbAmount: number;
    dreamCoinW: number;
    note?: string;
    catalogLines: { catalogItemId: number; quantity: number }[];
  }) =>
    request<{ ok: boolean; bizDate: string; characterId: number }>('/api/consumption-day-board/row', {
      method: 'PUT',
      json: body,
    }),
  /** 推荐榜：服务端按 bizDate 推算星期；仅「当天」需传 wallMinutes 用于隐藏已结束场次 */
  tasksRecommended: (bizDate?: string, clock?: { wallMinutes: number }) => {
    const p = new URLSearchParams();
    if (bizDate) p.set('bizDate', bizDate);
    if (clock && clock.wallMinutes != null) p.set('wallMinutes', String(clock.wallMinutes));
    const qs = p.toString();
    return request<RecommendedResponse>(`/api/tasks/recommended${qs ? `?${qs}` : ''}`);
  },
  taskTemplateUpdate: (id: number, body: { enabled?: boolean; manualSortOrder?: number | null }) =>
    request<TaskTemplate>(`/api/tasks/templates/${id}`, { method: 'PATCH', json: body }),
  taskTemplateReorder: (ids: number[]) =>
    request<{ ok: boolean; count: number }>('/api/tasks/templates/reorder', { method: 'POST', json: { ids } }),
  smartParse: (text: string) =>
    request<{ text: string; actions: SmartAction[] }>('/api/smart/parse', {
      method: 'POST',
      json: { text },
    }),
  smartOcr: async (file: File) => {
    const fd = new FormData();
    fd.append('image', file);
    const token = getToken();
    const res = await fetch(apiUrl('/api/smart/ocr'), {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data as { error?: string }).error || 'OCR 失败');
    return data as { ocrText: string; actions: SmartAction[] };
  },
  smartApply: (body: { bizDate: string; actions: SmartAction[] }) =>
    request<{ bizDate: string; results: unknown[] }>('/api/smart/apply', {
      method: 'POST',
      json: body,
    }),
  completeTask: (
    id: number,
    body: { bizDate?: string; startedAt?: string | null; endedAt?: string | null; title?: string }
  ) => request(`/api/tasks/${id}/complete`, { method: 'POST', json: body }),
  taskDone: (body: {
    bizDate?: string;
    taskId?: number;
    externalKey?: string;
    title?: string;
    startedAt?: string | null;
    endedAt?: string | null;
    /** 抓鬼等“可计数任务”本次完成数量（例如 10 只鬼） */
    unitCount?: number;
    source?: string;
  }) => request('/api/tasks/done', { method: 'POST', json: body }),
  taskCandidates: (bizDate?: string) => {
    const q = bizDate ? `?bizDate=${encodeURIComponent(bizDate)}` : '';
    return request<TaskCandidatesResponse>(`/api/tasks/candidates${q}`);
  },
  tasksDoneLog: (opts: { bizDate?: string; fromBizDate?: string; toBizDate?: string }) => {
    const p = new URLSearchParams();
    const from = opts.fromBizDate?.trim();
    const to = opts.toBizDate?.trim();
    if (from && to) {
      p.set('fromBizDate', from);
      p.set('toBizDate', to);
    } else if (opts.bizDate) {
      p.set('bizDate', opts.bizDate);
    }
    return request<TaskDoneLogResponse>(`/api/tasks/done-log?${p}`);
  },
  statsOverview: (bizDate?: string) => {
    const q = bizDate ? `?bizDate=${encodeURIComponent(bizDate)}` : '';
    return request<Overview>(`/api/stats/overview${q}`);
  },
  statsWeekly: (weekStart: string) =>
    request<Weekly>(`/api/stats/weekly?weekStart=${encodeURIComponent(weekStart)}`),
  statsMonthly: (year: number, month: number) =>
    request<Monthly>(`/api/stats/monthly?year=${year}&month=${month}`),
  itemCatalogAll: () =>
    request<ItemCatalogAllResponse>('/api/item-catalog?all=1'),
  itemCatalogCreate: (body: ItemCatalogInput) =>
    request<ItemCatalogRow>('/api/item-catalog', { method: 'POST', json: body }),
  itemCatalogUpdate: (id: number, body: Partial<ItemCatalogInput>) =>
    request<ItemCatalogRow>(`/api/item-catalog/${id}`, { method: 'PATCH', json: body }),
  itemCatalogDelete: (id: number) => request<{ ok: boolean }>(`/api/item-catalog/${id}`, { method: 'DELETE' }),
  itemCatalogBatchDelete: (ids: number[]) =>
    request<{ ok: boolean; deleted: number }>('/api/item-catalog/batch-delete', {
      method: 'POST',
      json: { ids },
    }),
  itemCatalogImportPreset: (replace: boolean) =>
    request<{ ok: boolean; count: number }>('/api/item-catalog/import-preset', {
      method: 'POST',
      json: { replace },
    }),
  itemCatalogUpload: async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const token = getToken();
    const res = await fetch(apiUrl('/api/item-catalog/upload'), {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data as { error?: string }).error || '上传失败');
    return data as { url: string };
  },
  mechLedgerPutTodayLines: (body: {
    bizDate?: string;
    lines: { name: string; valueW: number; count: number }[];
  }) =>
    request<{ ok: boolean; bizDate: string; lineCount: number }>('/api/mech-ledger/today-lines', {
      method: 'PUT',
      json: body,
    }).then((r) => {
      try {
        window.dispatchEvent(new CustomEvent('mhxy-mech-today-lines', { detail: { bizDate: r.bizDate } }));
      } catch {
        /* ignore */
      }
      return r;
    }),
  mechLedgerSaveDay: (body: {
    bizDate?: string;
    pointCardPoints: number;
    onlineCount: number;
    onlinePreset?: number;
    /** 保存收益时刻记账台累计在线时长（秒）；不传则服务端写 NULL */
    elapsedSec?: number | null;
    /** 刷得的现金游戏币（万），与物品单价 w 无关（旧版单字段；与 teamCashGameGoldW 二选一） */
    cashGameGoldW?: number;
    /** 各队现金（万），与队伍本金档位一一对应；有则毛合计为各队之和 */
    teamCashGameGoldW?: number[];
    teamPrincipalsW?: number[];
  }) =>
    request<{
      ok: boolean;
      bizDate: string;
      pointCardPoints: number;
      onlineCount: number;
      cashGameGoldW?: number;
      teamCashGameGoldW?: number[];
      teamPrincipalsW?: number[];
    }>('/api/mech-ledger/save-day', { method: 'POST', json: body }).then((r) => {
      try {
        window.dispatchEvent(
          new CustomEvent('mhxy-mech-day-meta-saved', { detail: { bizDate: r.bizDate } }),
        );
      } catch {
        /* ignore */
      }
      return r;
    }),
  mechLedgerSaveMeta: (body: {
    bizDate?: string;
    onlineCount: number;
    onlinePreset?: number;
    /** 当前累计在线秒数；传入则写入 meta（与记账台计时一致），不传则服务端不改动该列 */
    elapsedSec?: number;
    /** 当前点卡累计（实时同步）；不传则服务端不更新该列 */
    pointCardPoints?: number;
    /** 刷得的现金游戏币（万），与物品单价 w 无关（旧版单字段；与 teamCashGameGoldW 二选一） */
    cashGameGoldW?: number;
    /** 各队现金（万），与队伍本金档位一一对应；有则毛合计为各队之和 */
    teamCashGameGoldW?: number[];
    teamPrincipalsW?: number[];
    /** 记账台计时：暂停累计秒（与 runStart 分离），与 mech_ledger_day_meta 同步 */
    ledgerBaseElapsedSec?: number;
    ledgerRunStartAtMs?: number | null;
    ledgerPointCard?: MechLedgerPointCardSegments;
  }) =>
    request<{ ok: boolean; bizDate: string }>('/api/mech-ledger/save-meta', {
      method: 'POST',
      json: body,
    }),
  /** 刷新/关页时用 keepalive，提高最后一笔 meta 写入成功率（不解析响应） */
  mechLedgerSaveMetaKeepalive: (body: {
    bizDate?: string;
    onlineCount: number;
    onlinePreset?: number;
    elapsedSec?: number;
    pointCardPoints?: number;
    cashGameGoldW?: number;
    teamCashGameGoldW?: number[];
    teamPrincipalsW?: number[];
    ledgerBaseElapsedSec?: number;
    ledgerRunStartAtMs?: number | null;
    ledgerPointCard?: MechLedgerPointCardSegments;
  }) => {
    const token = getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    try {
      void fetch(apiUrl('/api/mech-ledger/save-meta'), {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        keepalive: true,
      });
    } catch {
      /* */
    }
  },
  mechLedgerDaily: (bizDate: string) =>
    request<MechLedgerDailyResponse>(
      `/api/mech-ledger/daily?bizDate=${encodeURIComponent(bizDate)}`
    ),
  mechLedgerDayDates: (limit?: number) =>
    request<{ dates: string[] }>(`/api/mech-ledger/day-dates?limit=${limit ?? 90}`),
  mechLedgerHistory: (limit?: number) =>
    request<MechLedgerHistoryResponse>(`/api/mech-ledger/history?limit=${limit ?? 90}`),
  mechLedgerPrefsGet: () =>
    request<{ gameWan: number; yuan: number; persisted: boolean }>('/api/mech-ledger/prefs'),
  mechLedgerPrefsPut: (body: { yuan: number }) =>
    request<{ gameWan: number; yuan: number; persisted: boolean }>('/api/mech-ledger/prefs', {
      method: 'PUT',
      json: body,
    }),
  clientPrefsGet: () => request<{ prefs: Record<string, unknown> }>('/api/me/client-prefs'),
  clientPrefsPut: (body: { prefs: Record<string, unknown> }) =>
    request<{ ok: boolean }>('/api/me/client-prefs', { method: 'PUT', json: body }),
  mechLedgerSpeechTranscribeConfig: () =>
    request<{ enabled: boolean }>('/api/mech-ledger/speech-transcribe/config'),
  mechLedgerSpeechTranscribe: async (blob: Blob) => {
    const fd = new FormData();
    fd.append('audio', blob, 'recording.webm');
    const token = getToken();
    const res = await fetch('/api/mech-ledger/speech-transcribe', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    const raw = await res.text();
    let data: unknown = null;
    try {
      data = raw ? (JSON.parse(raw) as unknown) : null;
    } catch {
      data = null;
    }
    if (!res.ok) {
      const o = data && typeof data === 'object' && data !== null ? (data as { error?: string }) : null;
      throw new Error(o?.error || '语音识别失败');
    }
    return data as { text: string };
  },
  artifactDaySelectedGet: (bizDate?: string) => {
    const q = bizDate ? `?bizDate=${encodeURIComponent(bizDate)}` : '';
    return request<{ bizDate: string; selected: string[]; updatedAt: string | null }>(
      `/api/artifacts/day-selected${q}`,
    );
  },
  artifactDaySelectedPut: (body: { bizDate: string; selected: string[] }) =>
    request<{ ok: boolean; bizDate: string; selected: string[] }>('/api/artifacts/day-selected', {
      method: 'PUT',
      json: body,
    }),
  artifactBossImageGet: (name: string) =>
    request<{ name: string; imageUrl: string | null; updatedAt: string | null }>(
      `/api/artifacts/boss-image?name=${encodeURIComponent(name)}`,
    ),
  artifactBossImageUpload: async (name: string, file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const token = getToken();
    const res = await fetch(apiUrl(`/api/artifacts/boss-image?name=${encodeURIComponent(name)}`), {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data as { error?: string }).error || '上传失败');
    return data as { ok: boolean; name: string; imageUrl: string };
  },
  artifactBossImageDelete: (name: string) =>
    request<{ ok: boolean; name: string }>(`/api/artifacts/boss-image?name=${encodeURIComponent(name)}`, {
      method: 'DELETE',
    }),
  artifactGuideStateGet: () =>
    request<{ persisted: boolean; state: any | null; updatedAt: string | null }>('/api/artifacts/guide-state'),
  artifactGuideStatePut: (state: unknown) =>
    request<{ ok: true }>('/api/artifacts/guide-state', { method: 'PUT', json: { state } }),
  artifactGuideContentGet: (names: string[]) => {
    const q = new URLSearchParams();
    if (names?.length) q.set('names', names.join(','));
    const qs = q.toString();
    return request<{ items: { name: string; content: any | null; updatedAt: string | null }[] }>(
      `/api/artifacts/guide-content${qs ? `?${qs}` : ''}`,
    );
  },
};

export type ItemCatalogRow = {
  id: number;
  name: string;
  imageUrl: string;
  priceW: number;
  levelLabel: string;
  description: string;
  panel: 'fixed' | 'var' | 'yaksha_white' | 'yaksha_reward' | 'scene';
  sortOrder: number;
};

export type ItemCatalogAllResponse = {
  panels: Record<
    'fixed' | 'var' | 'yaksha_white' | 'yaksha_reward' | 'scene',
    ItemCatalogRow[]
  >;
};

export type ItemCatalogInput = {
  name: string;
  imageUrl?: string;
  priceW?: number;
  levelLabel?: string;
  description?: string;
  panel?: ItemCatalogRow['panel'];
  sortOrder?: number;
};

export type ItemCategory = { id: number; name: string; sortOrder: number };
export type Item = {
  id: number;
  categoryId: number;
  name: string;
  imageUrl: string;
  sortOrder: number;
};
export type TaskTemplate = {
  source: 'db' | 'live';
  id?: number;
  externalKey?: string;
  name: string;
  description: string;
  frequency: 'daily' | 'four_day' | 'weekly_once' | 'weekly_twice';
  sortOrder: number;
  enabled?: boolean;
  manualSortOrder?: number | null;
  cooldownDays: number;
  /** 上次完成时刻（用于实时计算「xx后刷新」）；仅 DB 模板可靠 */
  lastDoneAt?: string | null;
  /** true 表示尚在冷却期（推荐榜仍展示但不可点完成） */
  inCooldown?: boolean;
  /** 固定轮换副本下一次刷新时刻（服务端计算，重启不丢） */
  nextRefreshAt?: string | null;
  weeklyCap?: number;
  weeklyRemaining?: number;
  /** 可完成次数上限（默认 1；抓鬼按「10 只=1 次」折算） */
  capTimes?: number;
  /** 剩余可完成次数（同 capTimes 口径） */
  remainingTimes?: number;
  schedulePinned?: boolean;
  scheduleHot?: boolean;
  scheduleOngoing?: boolean;
  scheduleJustEnded?: boolean;
  scheduleLabel?: string | null;
  hasSchedule?: boolean;
  /** 当天限时活动已过了结束时间（榜尾展示，补录可勾） */
  schedulePassed?: boolean;
  /** timed=限时；daily=师门/抓鬼/神器任务（起、转）/天命等 */
  recommendKind?: 'timed' | 'daily' | 'weekly';
  /** 五开较少刷的限时项，排在日常推荐之后 */
  wukaiTail?: boolean;
  /** 推荐星级 1–5（五开榜） */
  stars?: number;
  /** 五开必刷基准顺位，越小越靠前 */
  wukaiRank?: number;
  /** 本业务日已在推荐榜点过完成，仍展示在榜尾 */
  recordedDoneToday?: boolean;
};

export type RecommendedResponse = {
  bizDate: string;
  weekday: number;
  wallMinutes: number;
  /** true：查阅非今日，展示该日全部限时场次 */
  dayPlan?: boolean;
  tasks: TaskTemplate[];
  pinnedSummary: string[];
  activityFeed: {
    source: string;
    fetched: boolean;
    error: string | null;
    updatedAt: string;
    count: number;
  };
};

export type TaskCandidatesResponse = {
  bizDate: string;
  weekday: number;
  items: {
    source: 'db' | 'live';
    id?: number;
    externalKey?: string;
    name: string;
    description: string;
    frequency: string;
    enabled?: boolean;
    manualSortOrder?: number | null;
    kind: string;
    /** kind=waiting_update：推荐榜次数用尽，待周期刷新 */
    capTimes?: number;
    remainingTimes?: number;
    weeklyCap?: number;
    weeklyRemaining?: number;
  }[];
  activityFeed: { source: string; updatedAt: string };
};

export type TaskDoneLogResponse = {
  fromBizDate: string;
  toBizDate: string;
  items: {
    id: number;
    title: string;
    startedAt: string | null;
    endedAt: string | null;
    durationSeconds?: number | null;
    source: string;
    createdAt: string;
    bizDate?: string;
  }[];
};

export type SmartAction =
  | { type: 'cash'; amount: number; note?: string }
  | { type: 'points'; points: number; note?: string }
  | { type: 'item'; itemId: number; quantity?: number; note?: string };
export type ConsumptionDayCatalogLine = {
  catalogItemId: number;
  name: string;
  quantity: number;
};

export type ConsumptionDayBoardRow = {
  characterId: number;
  characterName: string;
  levelLabel: string;
  sect: string;
  rmbAmount: number;
  dreamCoinW: number;
  note: string;
  catalogLines: ConsumptionDayCatalogLine[];
};

export type ConsumptionDayBoardResponse = {
  bizDate: string;
  rows: ConsumptionDayBoardRow[];
};

export type ConsumptionCharacterRow = {
  id: number;
  characterName: string;
  levelLabel: string;
  sect: string;
  sortOrder: number;
  createdAt: string;
};

export type ConsumptionCharacterResponse = {
  id: number;
  characterName: string;
  levelLabel: string;
  sect: string;
  sortOrder: number;
};

export type ConsumptionEntryResponse = {
  id: number;
  bizDate: string;
  characterId: number | null;
  characterName: string;
  levelLabel: string;
  sect: string;
  rmbAmount: number;
  gameCoinW: number;
  note: string;
};

export type ConsumptionEntryRow = {
  id: number;
  characterId: number | null;
  bizDate: string;
  characterName: string;
  levelLabel: string;
  sect: string;
  rmbAmount: number;
  gameCoinW?: number | null;
  note: string;
  createdAt: string;
};

export type Overview = {
  bizDate: string;
  cash: number;
  pointCard: number;
  consumptionRmb: number;
  consumptionGameCoinW?: number;
  itemGainCount: number;
  itemQuantitySum: number;
  taskCompletions: {
    id: number;
    taskId: number | null;
    taskName: string;
    startedAt: string | null;
    endedAt: string | null;
    bizDate: string;
    dedupeKey?: string;
  }[];
};
export type Weekly = {
  weekStart: string;
  weekEnd: string;
  cash: number;
  /** 现金记账（元）：cash_entries.amount 本周合计 */
  cashRmb?: number;
  pointCard: number;
  /** 消耗页点卡充值（元）本周合计，与当日「点卡充值（元）」同源 */
  pointCardRechargeYuan?: number;
  itemByDay: { d: string; qty: string | number }[];
  taskCompletionsCount: number;
  /** 本周各日「保存收益」快照中在线角色数的最大值 */
  onlineRolesWeekMax: number;
  /** 本周在线时长（秒）：Σ mech_ledger_day_meta.elapsed_sec */
  onlineElapsedSecSum?: number;
  /** 与总览「当日」现金净额同口径：记账台物品+梦幻币折算元 − 区间内消耗页点卡充值（元） */
  netCashYuan: number | null;
  /** 与总览「当日」现金总额同口径：记账台物品+梦幻币折算元（未扣消耗） */
  totalCashYuan?: number | null;
};
export type Monthly = {
  year: number;
  month: number;
  cash: number;
  /** 现金记账（元）：cash_entries.amount 本月合计 */
  cashRmb?: number;
  pointCard: number;
  /** 消耗页点卡充值（元）本月合计 */
  pointCardRechargeYuan?: number;
  itemByDay: { d: string; qty: string | number }[];
  taskCompletionsCount: number;
  /** 本月在线时长（秒）：Σ mech_ledger_day_meta.elapsed_sec */
  onlineElapsedSecSum?: number;
  /** 月均口径的自然日天数：当前月=截至今天，否则=整月天数 */
  onlineAvgDayCount?: number;
  /** 与总览「当日」现金净额同口径 */
  netCashYuan: number | null;
  /** 与总览「当日」现金总额同口径：记账台物品+梦幻币折算元（未扣消耗） */
  totalCashYuan?: number | null;
};

export type MechLedgerDailyResponse = {
  bizDate: string;
  lines: { name: string; valueW: number; count: number }[];
  pointCardPoints: number;
  onlineRoles: number;
  /** 刷得的现金游戏币（万），与物品行单价 w 无关（毛收入合计） */
  cashGameGoldW: number;
  /** 卖商人回收的低价值物品合计(w)，用于净现金折算时从物品收益中扣除避免重复计入 */
  vendorTrashW?: number;
  /** 各队现金梦幻币（万）；缺省表示旧版仅毛合计 */
  teamCashGameGoldW?: number[];
  /** 各队伍本金（万） */
  teamPrincipalsW?: number[];
  /** 净现金（万）：有各队现金时 = Σ(队现金 − 队本金)；否则 = 毛 − 本金合计 */
  netCashGameGoldW?: number;
  /** 点卡快照写入时刻（点「保存收益」时更新；清除换日可能触达新日行，见记账台逻辑） */
  pointCardSavedAt?: string | null;
  savedAt: string | null;
  /** 累计在线总秒数（GET /daily 已按 ledger 跑表状态折算，与记账台 HUD 一致）；无数据时为 null */
  elapsedSec?: number | null;
  /** 记账台计时底数（秒），与 runStart 分离 */
  ledgerBaseElapsedSec?: number | null;
  /** 计时进行中时的墙钟 ms；停表则为 null */
  ledgerRunStartAtMs?: number | null;
  ledgerPointCard?: MechLedgerPointCardSegments;
};

export type MechLedgerHistoryRow = {
  bizDate: string;
  profitW: number;
  netCashGameGoldW: number;
  itemW: number;
  vendorTrashW: number;
  onlineRoles: number;
  savedAt: string | null;
};

export type MechLedgerHistoryResponse = {
  items: MechLedgerHistoryRow[];
};

/** 点卡分段：closedSlices 为已结束区间；当前区间从 segmentStartElapsed 到「现在」，人数取当前在线合计 */
export type MechLedgerPointCardSegments = {
  closedSlices: { durationSec: number; roles: number }[];
  segmentStartElapsed: number;
};
