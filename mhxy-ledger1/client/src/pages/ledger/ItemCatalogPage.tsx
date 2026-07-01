import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type ItemCatalogRow, type ItemCatalogInput } from '../../api';
import {
  LEDGER_LEVEL_OPTIONS,
  LEDGER_LINGSHI_TYPES,
  LEDGER_PICK_BOOK_ITEM_NAME,
  buildLedgerPickedDisplayName,
  getPriceFromMatrix,
  isLingshiBookCatalogName,
  loadLingshiBookMatrix,
  parseLingshiBookDisplayName,
  saveLingshiBookMatrix,
  type LingshiBookType,
} from './lingshiBookCatalog';
import {
  RUYI_DAN_ITEM_NAME,
  RUYI_ELEMENTS,
  buildRuyiDanDisplayName,
  getRuyiDanPrice,
  isRuyiDanCatalogName,
  loadRuyiDanPrices,
  parseRuyiDanDisplayName,
  saveRuyiDanPrices,
  type RuyiElement,
} from './ruyiDanCatalog';
import {
  BEAST_SCROLL_ITEM_NAME,
  buildBeastScrollDisplayName,
  isBeastScrollCatalogName,
  loadBeastScrollRows,
  parseBeastScrollDisplayName,
  saveBeastScrollRows,
  type BeastScrollRow,
} from './beastScrollCatalog';
import {
  TIERED_ITEM_CONFIG,
  getTieredMinPriceAndLevel,
  getTieredMinPriceForBase,
  isTieredCatalogName,
  isTieredPickBaseName,
  loadTieredPricesByBase,
  parseTieredCatalogDisplayName,
  saveTieredPricesByBase,
  type TieredPickBaseName,
} from './tieredItemCatalog';
import './MechanicalLedgerPage.css';
import './ItemCatalogPage.css';

const PANELS: { key: ItemCatalogRow['panel']; label: string }[] = [
  { key: 'fixed', label: '固定价格区' },
  { key: 'var', label: '浮动价区' },
  { key: 'yaksha_white', label: '夜叉 · 白玩' },
  { key: 'yaksha_reward', label: '夜叉 · 奖励' },
  { key: 'scene', label: '场景' },
];

const PANEL_ORDER: Record<ItemCatalogRow['panel'], number> = {
  fixed: 0,
  var: 1,
  yaksha_white: 2,
  yaksha_reward: 3,
  scene: 4,
};

function panelLabel(key: ItemCatalogRow['panel']) {
  return PANELS.find((p) => p.key === key)?.label ?? key;
}

/** 新增时：所属分区内当前最大 sort_order + 1（分区无行则为 0） */
function nextSortOrderForPanel(panel: ItemCatalogRow['panel'], list: ItemCatalogRow[]): number {
  let max = -1;
  for (const r of list) {
    if (r.panel === panel && Number.isFinite(r.sortOrder) && r.sortOrder > max) max = r.sortOrder;
  }
  return max + 1;
}

function defaultForm(): ItemCatalogInput & { panel: ItemCatalogRow['panel'] } {
  return {
    name: '',
    imageUrl: '',
    priceW: 0,
    levelLabel: '',
    description: '',
    panel: 'fixed',
    sortOrder: 0,
  };
}

export default function ItemCatalogPage() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<ItemCatalogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageMsg, setPageMsg] = useState<{ text: string; err?: boolean } | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [modalEditingId, setModalEditingId] = useState<number | null>(null);
  const [modalMsg, setModalMsg] = useState<{ text: string; err?: boolean } | null>(null);
  const [lingshiTabLevel, setLingshiTabLevel] = useState<string>('120');
  const [lingshiPickType, setLingshiPickType] = useState<LingshiBookType>(LEDGER_LINGSHI_TYPES[0]);
  const [lingshiMatrix, setLingshiMatrix] = useState<Record<string, Record<LingshiBookType, number>>>(() =>
    loadLingshiBookMatrix()
  );
  const [ruyiPrices, setRuyiPrices] = useState<Record<RuyiElement, number>>(() => loadRuyiDanPrices());
  const [ruyiPickElement, setRuyiPickElement] = useState<RuyiElement>(RUYI_ELEMENTS[0]);
  const [beastRows, setBeastRows] = useState<BeastScrollRow[]>(() => loadBeastScrollRows());
  const [beastPickId, setBeastPickId] = useState(() => loadBeastScrollRows()[0]?.id ?? '');
  const [tieredTabLevel, setTieredTabLevel] = useState('120');
  const [tieredPrices, setTieredPrices] = useState<Record<string, number>>({});
  const [imageUploading, setImageUploading] = useState(false);

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [batchDeleting, setBatchDeleting] = useState(false);
  const [reorderBusy, setReorderBusy] = useState(false);
  /** 正在拖动的物品（HTML5 DnD，仅可在同分区内松手排序） */
  const [dragInfo, setDragInfo] = useState<null | { id: number; panel: ItemCatalogRow['panel'] }>(null);
  /** 与 dragInfo 同步；dragover 会在 dragstart 后立刻触发，早于 state 提交，必须用 ref 才能 preventDefault */
  const dragInfoRef = useRef<null | { id: number; panel: ItemCatalogRow['panel'] }>(null);
  /** 悬停目标：插入在该卡上方或下方 */
  const [dropHint, setDropHint] = useState<null | { id: number; before: boolean }>(null);
  const headerSelectRef = useRef<HTMLInputElement>(null);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  const load = useCallback(async () => {
    setLoading(true);
    setPageMsg(null);
    try {
      const r = await api.itemCatalogAll();
      const flat = PANELS.flatMap(({ key }) => r.panels[key] ?? []);
      setRows(flat);
    } catch (e) {
      setRows([]);
      const msg = e instanceof Error && e.message ? e.message : '加载失败';
      if (msg === '未登录' || msg === '登录已失效') {
        navigate('/login', { replace: true });
        return;
      }
      setPageMsg({ text: msg, err: true });
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const valid = new Set(rows.map((r) => r.id));
    setSelectedIds((prev) => prev.filter((id) => valid.has(id)));
  }, [rows]);

  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      const po = PANEL_ORDER[a.panel] - PANEL_ORDER[b.panel];
      if (po !== 0) return po;
      if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
      return a.id - b.id;
    });
  }, [rows]);

  /** 晶石/附魔宝珠/珍珠/炼妖石/种子：列表单价列显示分档最低价（随本机定价表刷新） */
  const tieredMinPriceByBase = useMemo(() => {
    const out = {} as Record<TieredPickBaseName, number>;
    for (const b of Object.keys(TIERED_ITEM_CONFIG) as TieredPickBaseName[]) {
      out[b] = getTieredMinPriceForBase(b);
    }
    return out;
  }, [rows, modalOpen]);

  const catalogRowDisplayPriceW = useCallback((row: ItemCatalogRow) => {
    const n = row.name.trim();
    if (isTieredPickBaseName(n)) return tieredMinPriceByBase[n];
    return Number(row.priceW) || 0;
  }, [tieredMinPriceByBase]);

  const formIsLingshiBook = useMemo(() => isLingshiBookCatalogName(form.name), [form.name]);
  const formIsRuyiDan = useMemo(() => isRuyiDanCatalogName(form.name), [form.name]);
  const formIsBeastScroll = useMemo(() => isBeastScrollCatalogName(form.name), [form.name]);
  const tieredBase = useMemo((): TieredPickBaseName | null => {
    const t = form.name.trim();
    if (isTieredPickBaseName(t)) return t;
    const p = parseTieredCatalogDisplayName(t);
    return p?.base ?? null;
  }, [form.name]);

  useEffect(() => {
    if (!modalOpen || !formIsLingshiBook) return;
    setLingshiMatrix(loadLingshiBookMatrix());
  }, [modalOpen, formIsLingshiBook]);

  useEffect(() => {
    if (!modalOpen || !formIsRuyiDan) return;
    setRuyiPrices(loadRuyiDanPrices());
  }, [modalOpen, formIsRuyiDan]);

  useEffect(() => {
    if (!modalOpen || !formIsBeastScroll) return;
    const next = loadBeastScrollRows();
    setBeastRows(next);
    setBeastPickId((id) => (next.some((r) => r.id === id) ? id : next[0]?.id ?? ''));
  }, [modalOpen, formIsBeastScroll]);

  useEffect(() => {
    if (!modalOpen || !tieredBase) return;
    const levels = TIERED_ITEM_CONFIG[tieredBase].levels;
    setTieredPrices(loadTieredPricesByBase(tieredBase));
    setTieredTabLevel((cur) => (levels.includes(cur) ? cur : levels[0] ?? cur));
  }, [modalOpen, tieredBase]);

  useEffect(() => {
    const el = headerSelectRef.current;
    if (!el) return;
    const ids = sortedRows.map((r) => r.id);
    const n = ids.filter((id) => selectedIds.includes(id)).length;
    el.indeterminate = ids.length > 0 && n > 0 && n < ids.length;
  }, [selectedIds, sortedRows]);

  function openAdd() {
    setModalEditingId(null);
    const base = defaultForm();
    setForm({ ...base, sortOrder: nextSortOrderForPanel(base.panel, rows) });
    setModalMsg(null);
    setModalOpen(true);
  }

  function syncLingshiPickerFromName(name: string) {
    const p = parseLingshiBookDisplayName(name);
    if (p && (LEDGER_LEVEL_OPTIONS as readonly string[]).includes(p.level)) {
      setLingshiTabLevel(p.level);
      setLingshiPickType(p.type);
    } else {
      setLingshiTabLevel('120');
      setLingshiPickType(LEDGER_LINGSHI_TYPES[0]);
    }
  }

  function syncRuyiPickerFromName(name: string) {
    const el = parseRuyiDanDisplayName(name);
    if (el) {
      setRuyiPickElement(el);
    } else {
      setRuyiPickElement(RUYI_ELEMENTS[0]);
    }
  }

  function syncBeastPickerFromName(name: string) {
    const label = parseBeastScrollDisplayName(name);
    const rows = loadBeastScrollRows();
    if (label) {
      const hit = rows.find((r) => r.label.trim() === label);
      setBeastPickId(hit?.id ?? rows[0]?.id ?? '');
    } else {
      setBeastPickId(rows[0]?.id ?? '');
    }
  }

  function syncTieredPickerFromName(name: string) {
    const raw = name.trim();
    const parsed = parseTieredCatalogDisplayName(raw);
    const base: TieredPickBaseName | null = isTieredPickBaseName(raw)
      ? (raw as TieredPickBaseName)
      : parsed?.base ?? null;
    if (!base) return;
    const cfg = TIERED_ITEM_CONFIG[base];
    if (parsed && cfg.levels.includes(parsed.level)) {
      setTieredTabLevel(parsed.level);
      return;
    }
    setTieredTabLevel(getTieredMinPriceAndLevel(base).level);
  }

  function openEdit(row: ItemCatalogRow) {
    setModalEditingId(row.id);
    const nm = row.name.trim();
    const priceW = isTieredPickBaseName(nm) ? getTieredMinPriceForBase(nm) : row.priceW;
    setForm({
      name: row.name,
      imageUrl: row.imageUrl,
      priceW,
      levelLabel: row.levelLabel,
      description: row.description,
      panel: row.panel,
      sortOrder: row.sortOrder,
    });
    setModalMsg(null);
    setModalOpen(true);
    if (isLingshiBookCatalogName(row.name)) {
      syncLingshiPickerFromName(row.name);
    }
    if (isRuyiDanCatalogName(row.name)) {
      syncRuyiPickerFromName(row.name);
    }
    if (isBeastScrollCatalogName(row.name)) {
      syncBeastPickerFromName(row.name);
    }
    if (isTieredCatalogName(row.name)) {
      syncTieredPickerFromName(row.name);
    }
  }

  const closeModal = useCallback(() => {
    setModalOpen(false);
    setModalEditingId(null);
    setModalMsg(null);
    setImageUploading(false);
  }, []);

  const uploadImageFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setModalMsg({ text: '剪贴板中不是图片', err: true });
      return;
    }
    setImageUploading(true);
    setModalMsg(null);
    try {
      const { url } = await api.itemCatalogUpload(file);
      setForm((prev) => ({ ...prev, imageUrl: url }));
      setModalMsg({ text: '已上传，地址已填入「图片地址」', err: false });
    } catch (err) {
      setModalMsg({ text: (err as Error).message, err: true });
    } finally {
      setImageUploading(false);
    }
  }, []);

  function applyLingshiPick() {
    saveLingshiBookMatrix(lingshiMatrix);
    const price = getPriceFromMatrix(lingshiMatrix, lingshiTabLevel, lingshiPickType);
    const name = buildLedgerPickedDisplayName(LEDGER_PICK_BOOK_ITEM_NAME, lingshiTabLevel, lingshiPickType);
    setForm((f) => ({
      ...f,
      name,
      priceW: price,
      levelLabel: `${lingshiTabLevel}级`,
    }));
  }

  function applyRuyiPick() {
    saveRuyiDanPrices(ruyiPrices);
    const price = getRuyiDanPrice(ruyiPrices, ruyiPickElement);
    const name = buildRuyiDanDisplayName(ruyiPickElement);
    setForm((f) => ({
      ...f,
      name,
      priceW: price,
      levelLabel: ruyiPickElement,
    }));
  }

  function applyBeastPick() {
    const row = beastRows.find((r) => r.id === beastPickId) ?? beastRows[0];
    if (!row) return;
    saveBeastScrollRows(beastRows);
    setForm((f) => ({
      ...f,
      name: buildBeastScrollDisplayName(row.label),
      priceW: row.priceW,
      levelLabel: row.label,
    }));
  }

  function applyTieredPick() {
    if (!tieredBase) return;
    saveTieredPricesByBase(tieredBase, tieredPrices);
    const price = tieredPrices[tieredTabLevel] ?? 0;
    const name = buildLedgerPickedDisplayName(tieredBase, tieredTabLevel);
    setForm((f) => ({
      ...f,
      name,
      priceW: price,
      levelLabel: `${tieredTabLevel}级`,
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) {
      setModalMsg({ text: '请填写名称', err: true });
      return;
    }
    if (isLingshiBookCatalogName(form.name)) {
      saveLingshiBookMatrix(lingshiMatrix);
    }
    if (isRuyiDanCatalogName(form.name)) {
      saveRuyiDanPrices(ruyiPrices);
    }
    if (isBeastScrollCatalogName(form.name)) {
      saveBeastScrollRows(beastRows);
    }
    if (tieredBase) {
      saveTieredPricesByBase(tieredBase, tieredPrices);
    }
    setModalMsg(null);
    try {
      if (modalEditingId != null) {
        await api.itemCatalogUpdate(modalEditingId, form);
        setPageMsg({ text: '已保存修改' });
      } else {
        const sortOrder = nextSortOrderForPanel(form.panel, rows);
        await api.itemCatalogCreate({ ...form, sortOrder });
        setPageMsg({ text: '已新增物品' });
      }
      closeModal();
      await load();
    } catch (err) {
      setModalMsg({ text: (err as Error).message, err: true });
    }
  }

  async function onDelete(id: number) {
    if (!window.confirm('确定删除该物品？')) return;
    try {
      await api.itemCatalogDelete(id);
      setPageMsg({ text: '已删除' });
      if (modalEditingId === id) closeModal();
      setSelectedIds((prev) => prev.filter((x) => x !== id));
      await load();
    } catch (err) {
      setPageMsg({ text: (err as Error).message, err: true });
    }
  }

  function toggleSelectId(id: number) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function toggleSelectAll() {
    if (sortedRows.length === 0) return;
    const ids = sortedRows.map((r) => r.id);
    const allOn = ids.length > 0 && ids.every((id) => selectedIds.includes(id));
    if (allOn) {
      setSelectedIds((prev) => prev.filter((id) => !ids.includes(id)));
    } else {
      setSelectedIds((prev) => [...new Set([...prev, ...ids])]);
    }
  }

  async function onBatchDelete() {
    if (selectedIds.length === 0) return;
    const tip = `确定删除已选的 ${selectedIds.length} 条？（含重复项可一并勾选删除）此操作不可恢复。`;
    if (!window.confirm(tip)) return;
    setBatchDeleting(true);
    setPageMsg(null);
    try {
      const { deleted } = await api.itemCatalogBatchDelete(selectedIds);
      setSelectedIds([]);
      setPageMsg({ text: `已删除 ${deleted} 条` });
      await load();
    } catch (err) {
      setPageMsg({ text: (err as Error).message, err: true });
    } finally {
      setBatchDeleting(false);
    }
  }

  const applyPanelReorder = useCallback(
    async (panel: ItemCatalogRow['panel'], orderedIds: number[]) => {
      if (orderedIds.length === 0) return;
      setReorderBusy(true);
      setPageMsg(null);
      try {
        await Promise.all(orderedIds.map((id, i) => api.itemCatalogUpdate(id, { sortOrder: i })));
        const orderMap = new Map(orderedIds.map((id, i) => [id, i]));
        setRows((prev) =>
          prev.map((r) =>
            r.panel === panel && orderMap.has(r.id) ? { ...r, sortOrder: orderMap.get(r.id)! } : r,
          ),
        );
        setPageMsg({ text: '排序已保存', err: false });
      } catch (e) {
        setPageMsg({ text: e instanceof Error ? e.message : '排序保存失败', err: true });
        await load();
      } finally {
        setReorderBusy(false);
        dragInfoRef.current = null;
        setDragInfo(null);
        setDropHint(null);
      }
    },
    [load],
  );

  function onCatalogDragStart(e: React.DragEvent, row: ItemCatalogRow) {
    if (batchDeleting || reorderBusy) {
      e.preventDefault();
      return;
    }
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(row.id));
    e.dataTransfer.setData('application/x-mhxy-catalog-panel', row.panel);
    const payload = { id: row.id, panel: row.panel };
    dragInfoRef.current = payload;
    setDragInfo(payload);
    setDropHint(null);
  }

  function onCatalogDragEnd() {
    dragInfoRef.current = null;
    setDragInfo(null);
    setDropHint(null);
  }

  /** 捕获阶段：光标在图片/按钮等子元素上时，target 不是 li，必须在 li 上抢先 preventDefault 才能松手放置 */
  function onCatalogDragOverCapture(e: React.DragEvent, row: ItemCatalogRow) {
    const d = dragInfoRef.current;
    if (!d || row.id === d.id || row.panel !== d.panel) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const before = e.clientY < rect.top + rect.height / 2;
    setDropHint({ id: row.id, before });
  }

  function onCatalogDragOver(e: React.DragEvent, row: ItemCatalogRow) {
    const d = dragInfoRef.current;
    if (!d || row.id === d.id || row.panel !== d.panel) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const before = e.clientY < rect.top + rect.height / 2;
    setDropHint({ id: row.id, before });
  }

  function onCatalogDragLeave(e: React.DragEvent) {
    const related = e.relatedTarget as Node | null;
    if (related && (e.currentTarget as HTMLElement).contains(related)) return;
    setDropHint(null);
  }

  async function onCatalogDrop(e: React.DragEvent, targetRow: ItemCatalogRow) {
    e.preventDefault();
    const dragId = Number(e.dataTransfer.getData('text/plain'));
    if (!Number.isFinite(dragId)) return;
    const panelRaw = e.dataTransfer.getData('application/x-mhxy-catalog-panel') as ItemCatalogRow['panel'];
    const dragged = sortedRows.find((r) => r.id === dragId);
    if (!dragged || dragged.panel !== targetRow.panel || dragId === targetRow.id) {
      dragInfoRef.current = null;
      setDragInfo(null);
      setDropHint(null);
      return;
    }
    if (panelRaw && panelRaw !== dragged.panel) {
      dragInfoRef.current = null;
      setDragInfo(null);
      setDropHint(null);
      return;
    }

    const panel = dragged.panel;
    const panelRows = sortedRows.filter((r) => r.panel === panel);
    const fromIdx = panelRows.findIndex((r) => r.id === dragId);
    const toIdxRaw = panelRows.findIndex((r) => r.id === targetRow.id);
    if (fromIdx < 0 || toIdxRaw < 0) return;

    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const before = e.clientY < rect.top + rect.height / 2;

    const without = panelRows.filter((r) => r.id !== dragId);
    const targetNewIdx = fromIdx < toIdxRaw ? toIdxRaw - 1 : toIdxRaw;
    let insertAt = before ? targetNewIdx : targetNewIdx + 1;
    insertAt = Math.max(0, Math.min(insertAt, without.length));

    const nextRows = [...without];
    nextRows.splice(insertAt, 0, dragged);
    const orderedIds = nextRows.map((r) => r.id);

    await applyPanelReorder(panel, orderedIds);
  }

  async function onImport(replace: boolean) {
    const tip = replace
      ? '将清空当前账号下所有物品再导入模板，确定？'
      : '将在现有数据后追加一整套模板（可能重复），确定？';
    if (!window.confirm(tip)) return;
    try {
      const r = await api.itemCatalogImportPreset(replace);
      setPageMsg({ text: `导入完成，当前共 ${r.count} 条` });
      await load();
    } catch (err) {
      setPageMsg({ text: (err as Error).message, err: true });
    }
  }

  function pickImageFileFromClipboard(dt: DataTransfer | null): File | null {
    if (!dt) return null;
    for (const item of Array.from(dt.items)) {
      if (item.kind === 'file' && item.type.startsWith('image/')) {
        const f = item.getAsFile();
        if (f) return f;
      }
    }
    if (dt.files?.length) {
      for (let i = 0; i < dt.files.length; i++) {
        const f = dt.files[i];
        if (f.type.startsWith('image/')) return f;
      }
    }
    return null;
  }

  useEffect(() => {
    if (!modalOpen) return;
    const onPaste = (e: ClipboardEvent) => {
      const file = pickImageFileFromClipboard(e.clipboardData);
      if (!file) return;
      e.preventDefault();
      e.stopPropagation();
      void uploadImageFile(file);
    };
    document.addEventListener('paste', onPaste, true);
    return () => document.removeEventListener('paste', onPaste, true);
  }, [modalOpen, uploadImageFile]);

  async function onUploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    await uploadImageFile(file);
  }

  useEffect(() => {
    if (!modalOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeModal();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [modalOpen, closeModal]);

  return (
    <div className="mech-ledger-root item-catalog-page item-catalog-page--mech">
      <div className="mech-inner">
        <header className="mech-titlebar">
          <h1>物品库</h1>
          <nav className="mech-menubar" aria-label="页面导航">
            <Link to="/app/ledger">返回记账台</Link>
            <Link to="/app/cash">消耗</Link>
            <Link to="/app/ledger/daily">每日收益</Link>
          </nav>
        </header>

        <section className="item-catalog-upper" aria-label="操作与说明">
          <p className="item-catalog-upper-hint muted">
            数据来自当前账号 MySQL 物品库；记账台单价以此为准。灵饰书 / 如意丹 / 兽决 / 分档物品等在弹窗内维护。点卡片「编辑」修改；弹窗内支持 Ctrl+V
            粘贴截图上传。鼠标移到物品图上会出现中央拖动提示，按住拖动可排序（仅同一分区内），松手后自动写库。
          </p>
          <div className="item-catalog-toolbar item-catalog-toolbar--mech">
            <label className="item-catalog-select-all-inline">
              <input
                ref={headerSelectRef}
                type="checkbox"
                title="全选全部物品"
                checked={sortedRows.length > 0 && sortedRows.every((r) => selectedIds.includes(r.id))}
                disabled={loading || batchDeleting || sortedRows.length === 0}
                onChange={toggleSelectAll}
              />
              <span>全选</span>
            </label>
            <button type="button" className="mech-btn" onClick={openAdd}>
              新增物品
            </button>
            <button type="button" className="mech-btn" onClick={() => onImport(true)}>
              导入预设（覆盖）
            </button>
            <button type="button" className="mech-btn" onClick={() => onImport(false)}>
              导入预设（追加）
            </button>
            <button type="button" className="mech-btn" onClick={() => load()} disabled={loading}>
              刷新
            </button>
            <button
              type="button"
              className="mech-btn"
              disabled={loading || batchDeleting || selectedIds.length === 0}
              onClick={() => void onBatchDelete()}
            >
              批量删除{selectedIds.length > 0 ? `（${selectedIds.length}）` : ''}
            </button>
          </div>
          {pageMsg && (
            <p className={`item-catalog-banner ${pageMsg.err ? 'err' : ''}`} role="status">
              {pageMsg.text}
            </p>
          )}
        </section>

        <div className="mech-body item-catalog-mech-body">
          <div className="mech-panel-block item-catalog-cards-panel">
            {loading ? (
              <p className="item-catalog-cards-empty">加载中…</p>
            ) : sortedRows.length === 0 ? (
              <p className="item-catalog-cards-empty">暂无数据。可点击「新增物品」或「导入预设」。</p>
            ) : (
              <ul className="item-catalog-card-grid">
                {sortedRows.map((row) => {
                  const isDragging = dragInfo?.id === row.id;
                  const dh = dropHint?.id === row.id;
                  const dropBefore = dh && dropHint.before;
                  const dropAfter = dh && !dropHint.before;
                  return (
                  <li
                    key={row.id}
                    className={`item-catalog-card${isDragging ? ' item-catalog-card--dragging' : ''}${dropBefore ? ' item-catalog-card--drop-before' : ''}${dropAfter ? ' item-catalog-card--drop-after' : ''}`}
                    onDragOverCapture={(e) => onCatalogDragOverCapture(e, row)}
                    onDragOver={(e) => onCatalogDragOver(e, row)}
                    onDragLeave={onCatalogDragLeave}
                    onDrop={(e) => void onCatalogDrop(e, row)}
                  >
                    <label className="item-catalog-card-check">
                      <input
                        type="checkbox"
                        checked={selectedSet.has(row.id)}
                        disabled={batchDeleting || reorderBusy}
                        onChange={() => toggleSelectId(row.id)}
                        aria-label={`选择 ${row.name}`}
                      />
                    </label>
                    <div className="item-catalog-card-media">
                      {row.imageUrl ? (
                        <img
                          className="item-catalog-card-img"
                          src={row.imageUrl}
                          alt=""
                          loading="lazy"
                          draggable={false}
                        />
                      ) : (
                        <div className="item-catalog-card-img item-catalog-card-img--placeholder" aria-hidden>
                          无图
                        </div>
                      )}
                      <button
                        type="button"
                        className="item-catalog-drag-on-img"
                        draggable={!batchDeleting && !reorderBusy}
                        title="拖动排序（仅同分区）"
                        aria-label={`拖动排序：${row.name}`}
                        onDragStart={(e) => onCatalogDragStart(e, row)}
                        onDragEnd={onCatalogDragEnd}
                      >
                        <span className="item-catalog-drag-on-img-icon" aria-hidden />
                      </button>
                    </div>
                    <div className="item-catalog-card-body">
                      <div
                        className="item-catalog-card-title"
                        title={`${row.name}（${catalogRowDisplayPriceW(row)} w）`}
                      >
                        <span className="item-catalog-card-name">{row.name}</span>
                        <span className="item-catalog-card-title-price">
                          （{catalogRowDisplayPriceW(row)} w）
                        </span>
                      </div>
                      <div className="item-catalog-card-meta">
                        <span>{panelLabel(row.panel)}</span>
                        {row.levelLabel ? <span> · {row.levelLabel}</span> : null}
                        <span className="item-catalog-card-sort"> · 排序 {row.sortOrder}</span>
                      </div>
                      <div className="item-catalog-card-actions">
                        <button
                          type="button"
                          className="mech-btn item-catalog-card-edit-btn"
                          disabled={batchDeleting || reorderBusy}
                          onClick={() => openEdit(row)}
                        >
                          编辑
                        </button>
                        <button
                          type="button"
                          className="mech-btn item-catalog-card-del-btn"
                          disabled={batchDeleting || reorderBusy}
                          onClick={() => onDelete(row.id)}
                        >
                          删除
                        </button>
                      </div>
                      {row.description ? (
                        <p className="item-catalog-card-desc">{row.description}</p>
                      ) : null}
                    </div>
                  </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </div>

      {modalOpen && (
        <>
          <div
            className="modal-backdrop item-catalog-modal-backdrop"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) closeModal();
            }}
          >
            <div
              className={`modal card item-catalog-modal${
                formIsLingshiBook || formIsRuyiDan || formIsBeastScroll || tieredBase
                  ? ' item-catalog-modal--lingshi'
                  : ''
              }`}
              role="dialog"
              aria-modal="true"
              aria-labelledby="item-catalog-modal-title"
            >
              <h2 id="item-catalog-modal-title">
                {modalEditingId != null ? `编辑 · #${modalEditingId}` : '新增物品'}
              </h2>
              <form onSubmit={onSubmit}>
                <div className="item-catalog-grid">
                  <label>
                    名称 *
                    <input
                      className="input"
                      value={form.name}
                      onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                      placeholder="如 金刚石"
                      required
                    />
                  </label>
                  {formIsLingshiBook && (
                    <div className="item-catalog-lingshi-embedded item-catalog-grid-full">
                      <h3 className="item-catalog-lingshi-embed-title">灵饰书 · 各等级定价与本条</h3>
                      <p className="item-catalog-lingshi-lead">
                        Tab 为等级；每行填单价（万 w）。左侧选「本条」种类后点「写入名称与单价」更新上方名称/单价/等级；点「保存」也会把整张定价表写入本机浏览器。
                      </p>
                      <div className="item-catalog-lingshi-tabs" role="tablist" aria-label="灵饰书等级">
                        {LEDGER_LEVEL_OPTIONS.map((lv) => (
                          <button
                            key={lv}
                            type="button"
                            role="tab"
                            aria-selected={lingshiTabLevel === lv}
                            className={`item-catalog-lingshi-tab${lingshiTabLevel === lv ? ' is-active' : ''}`}
                            onClick={() => setLingshiTabLevel(lv)}
                          >
                            {lv}级
                          </button>
                        ))}
                      </div>
                      <div className="item-catalog-lingshi-panel" role="tabpanel">
                        <table className="item-catalog-lingshi-table">
                          <thead>
                            <tr>
                              <th className="item-catalog-lingshi-col-pick" scope="col">
                                本条
                              </th>
                              <th scope="col">种类</th>
                              <th scope="col">单价（万 w）</th>
                            </tr>
                          </thead>
                          <tbody>
                            {LEDGER_LINGSHI_TYPES.map((t) => (
                              <tr key={t}>
                                <td className="item-catalog-lingshi-col-pick">
                                  <input
                                    type="radio"
                                    name="itemCatalogLingshiPickType"
                                    checked={lingshiPickType === t}
                                    onChange={() => setLingshiPickType(t)}
                                    aria-label={`本条物品选${t}`}
                                  />
                                </td>
                                <td className="item-catalog-lingshi-type-label">{t}</td>
                                <td>
                                  <input
                                    className="input item-catalog-lingshi-price-input"
                                    type="number"
                                    step="0.01"
                                    min={0}
                                    value={lingshiMatrix[lingshiTabLevel]?.[t] ?? 0}
                                    onChange={(e) => {
                                      const n = Number(e.target.value);
                                      setLingshiMatrix((prev) => ({
                                        ...prev,
                                        [lingshiTabLevel]: {
                                          ...prev[lingshiTabLevel],
                                          [t]: Number.isFinite(n) && n >= 0 ? n : 0,
                                        },
                                      }));
                                    }}
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="item-catalog-lingshi-price-preview">
                        将写入：灵饰书 · {lingshiTabLevel}级 · {lingshiPickType}，单价{' '}
                        {getPriceFromMatrix(lingshiMatrix, lingshiTabLevel, lingshiPickType)} w
                      </p>
                      <div className="item-catalog-lingshi-embed-actions">
                        <button type="button" className="btn btn-primary" onClick={applyLingshiPick}>
                          写入名称与单价
                        </button>
                      </div>
                    </div>
                  )}
                  {formIsRuyiDan && (
                    <div className="item-catalog-lingshi-embedded item-catalog-grid-full">
                      <h3 className="item-catalog-lingshi-embed-title">如意丹 · 五行定价与本条</h3>
                      <p className="item-catalog-lingshi-lead">
                        无等级，仅按五行分别填单价（万 w）。左侧选「本条」属性后点「写入名称与单价」更新名称/单价/等级列（等级列填五行字便于辨认）；点「保存」也会把定价写入本机浏览器。
                      </p>
                      <div className="item-catalog-lingshi-panel" role="region" aria-label="如意丹五行单价">
                        <table className="item-catalog-lingshi-table">
                          <thead>
                            <tr>
                              <th className="item-catalog-lingshi-col-pick" scope="col">
                                本条
                              </th>
                              <th scope="col">属性</th>
                              <th scope="col">单价（万 w）</th>
                            </tr>
                          </thead>
                          <tbody>
                            {RUYI_ELEMENTS.map((el) => (
                              <tr key={el}>
                                <td className="item-catalog-lingshi-col-pick">
                                  <input
                                    type="radio"
                                    name="itemCatalogRuyiPickEl"
                                    checked={ruyiPickElement === el}
                                    onChange={() => setRuyiPickElement(el)}
                                    aria-label={`本条物品选${el}`}
                                  />
                                </td>
                                <td className="item-catalog-lingshi-type-label">{el}</td>
                                <td>
                                  <input
                                    className="input item-catalog-lingshi-price-input"
                                    type="number"
                                    step="0.01"
                                    min={0}
                                    value={ruyiPrices[el] ?? 0}
                                    onChange={(e) => {
                                      const n = Number(e.target.value);
                                      setRuyiPrices((prev) => ({
                                        ...prev,
                                        [el]: Number.isFinite(n) && n >= 0 ? n : 0,
                                      }));
                                    }}
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="item-catalog-lingshi-price-preview">
                        将写入：{RUYI_DAN_ITEM_NAME} · {ruyiPickElement}，单价 {getRuyiDanPrice(ruyiPrices, ruyiPickElement)}{' '}
                        w
                      </p>
                      <div className="item-catalog-lingshi-embed-actions">
                        <button type="button" className="btn btn-primary" onClick={applyRuyiPick}>
                          写入名称与单价
                        </button>
                      </div>
                    </div>
                  )}
                  {formIsBeastScroll && (
                    <div className="item-catalog-lingshi-embedded item-catalog-grid-full">
                      <h3 className="item-catalog-lingshi-embed-title">兽决 · 种类定价与本条</h3>
                      <p className="item-catalog-lingshi-lead">
                        无等级。每行可改「种类」名称与单价（万 w）；默认价来自行情模板。左侧选「本条」后点「写入名称与单价」；「保存」写入本机浏览器，记账台选兽决种类时按此价入账。可添加 / 删除行。
                      </p>
                      <div className="item-catalog-lingshi-panel" role="region" aria-label="兽决种类单价">
                        <table className="item-catalog-lingshi-table">
                          <thead>
                            <tr>
                              <th className="item-catalog-lingshi-col-pick" scope="col">
                                本条
                              </th>
                              <th scope="col">种类</th>
                              <th scope="col">单价（万 w）</th>
                              <th className="item-catalog-lingshi-col-pick" scope="col">
                                操作
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {beastRows.map((row) => (
                              <tr key={row.id}>
                                <td className="item-catalog-lingshi-col-pick">
                                  <input
                                    type="radio"
                                    name="itemCatalogBeastPick"
                                    checked={beastPickId === row.id}
                                    onChange={() => setBeastPickId(row.id)}
                                    aria-label={`本条物品选${row.label}`}
                                  />
                                </td>
                                <td>
                                  <input
                                    className="input item-catalog-lingshi-type-input"
                                    type="text"
                                    value={row.label}
                                    onChange={(e) => {
                                      const v = e.target.value;
                                      setBeastRows((prev) =>
                                        prev.map((r) => (r.id === row.id ? { ...r, label: v } : r))
                                      );
                                    }}
                                    placeholder="种类名称"
                                  />
                                </td>
                                <td>
                                  <input
                                    className="input item-catalog-lingshi-price-input"
                                    type="number"
                                    step="0.01"
                                    min={0}
                                    value={row.priceW}
                                    onChange={(e) => {
                                      const n = Number(e.target.value);
                                      setBeastRows((prev) =>
                                        prev.map((r) =>
                                          r.id === row.id
                                            ? { ...r, priceW: Number.isFinite(n) && n >= 0 ? n : 0 }
                                            : r
                                        )
                                      );
                                    }}
                                  />
                                </td>
                                <td>
                                  <button
                                    type="button"
                                    className="btn btn-ghost"
                                    style={{ fontSize: '0.75rem', padding: '0.2rem 0.45rem' }}
                                    onClick={() => {
                                      const next = beastRows.filter((r) => r.id !== row.id);
                                      if (next.length === 0) {
                                        const one = { id: `b-${Date.now()}`, label: '未命名', priceW: 0 };
                                        setBeastRows([one]);
                                        setBeastPickId(one.id);
                                        return;
                                      }
                                      setBeastRows(next);
                                      if (beastPickId === row.id) setBeastPickId(next[0]!.id);
                                    }}
                                  >
                                    删除
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="item-catalog-lingshi-price-preview">
                        将写入：{BEAST_SCROLL_ITEM_NAME} ·{' '}
                        {beastRows.find((r) => r.id === beastPickId)?.label ?? '—'}，单价{' '}
                        {beastRows.find((r) => r.id === beastPickId)?.priceW ?? 0} w
                      </p>
                      <div className="item-catalog-lingshi-embed-actions">
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => {
                            const id = `b-${Date.now()}`;
                            setBeastRows((prev) => [...prev, { id, label: '新种类', priceW: 0 }]);
                            setBeastPickId(id);
                          }}
                        >
                          添加种类
                        </button>
                        <button type="button" className="btn btn-primary" onClick={applyBeastPick}>
                          写入名称与单价
                        </button>
                      </div>
                    </div>
                  )}
                  {tieredBase && (
                    <div className="item-catalog-lingshi-embedded item-catalog-grid-full">
                      <h3 className="item-catalog-lingshi-embed-title">{tieredBase} · 各等级定价（无种类）</h3>
                      <p className="item-catalog-lingshi-lead">
                        Tab 为等级，下方填该等级单价（万 w）。
                        {tieredBase === '种子' ? (
                          <>「种子」为 2 / 3 / 4 级三档。</>
                        ) : (
                          <>
                            晶石与灵饰书共用 60–140 档；附魔宝珠为 80–160 等；珍珠 50–160；炼妖石 105–145。
                          </>
                        )}{' '}
                        点「写入名称与单价」更新本条；「保存」写入本机浏览器供记账台引用。
                      </p>
                      <div className="item-catalog-lingshi-tabs" role="tablist" aria-label={`${tieredBase}等级`}>
                        {TIERED_ITEM_CONFIG[tieredBase].levels.map((lv) => (
                          <button
                            key={lv}
                            type="button"
                            role="tab"
                            aria-selected={tieredTabLevel === lv}
                            className={`item-catalog-lingshi-tab${tieredTabLevel === lv ? ' is-active' : ''}`}
                            onClick={() => setTieredTabLevel(lv)}
                          >
                            {lv}级
                          </button>
                        ))}
                      </div>
                      <div className="item-catalog-lingshi-panel" role="tabpanel">
                        <label className="item-catalog-tiered-single-price">
                          {tieredTabLevel}级 · 单价（万 w）
                          <input
                            className="input"
                            type="number"
                            step="0.01"
                            min={0}
                            value={tieredPrices[tieredTabLevel] ?? 0}
                            onChange={(e) => {
                              const n = Number(e.target.value);
                              setTieredPrices((prev) => ({
                                ...prev,
                                [tieredTabLevel]: Number.isFinite(n) && n >= 0 ? n : 0,
                              }));
                            }}
                          />
                        </label>
                      </div>
                      <p className="item-catalog-lingshi-price-preview">
                        将写入：{buildLedgerPickedDisplayName(tieredBase, tieredTabLevel)}，单价{' '}
                        {tieredPrices[tieredTabLevel] ?? 0} w
                      </p>
                      <div className="item-catalog-lingshi-embed-actions">
                        <button type="button" className="btn btn-primary" onClick={applyTieredPick}>
                          写入名称与单价
                        </button>
                      </div>
                    </div>
                  )}
                <label>
                  单价（万 w）
                  <input
                    className="input"
                    type="number"
                    step="0.01"
                    value={form.priceW ?? 0}
                    onChange={(e) => setForm((f) => ({ ...f, priceW: Number(e.target.value) }))}
                  />
                </label>
                <label>
                  等级
                  <input
                    className="input"
                    value={form.levelLabel ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, levelLabel: e.target.value }))}
                    placeholder="如 150 或 无级别"
                  />
                </label>
                {modalEditingId != null ? (
                  <label>
                    排序
                    <input
                      className="input"
                      type="number"
                      value={form.sortOrder ?? 0}
                      onChange={(e) => setForm((f) => ({ ...f, sortOrder: Number(e.target.value) }))}
                    />
                  </label>
                ) : (
                  <div className="item-catalog-sort-auto" role="status">
                    <span className="item-catalog-sort-auto-label">排序</span>
                    <span className="item-catalog-sort-auto-value">
                      自动：{nextSortOrderForPanel(form.panel, rows)}（{panelLabel(form.panel)} 内当前最大排序 +1）
                    </span>
                  </div>
                )}
                <label className="item-catalog-grid-full">
                  图片地址
                  <input
                    className="input"
                    value={form.imageUrl ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, imageUrl: e.target.value }))}
                    placeholder="/mhxy-items/sheet-fixed-01.png 或 /uploads/catalog/…"
                  />
                  <span className="item-catalog-paste-hint">
                    截图后在本弹窗内按 Ctrl+V 可自动上传；或使用下方「上传图片」。
                    {imageUploading ? ' 正在上传…' : ''}
                  </span>
                </label>
                <label className="item-catalog-grid-full">
                  描述
                  <textarea
                    className="input item-catalog-textarea"
                    value={form.description ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                    placeholder="可选备注"
                  />
                </label>
                <label>
                  所属分区
                  <select
                    className="input"
                    value={form.panel}
                    onChange={(e) => {
                      const panel = e.target.value as ItemCatalogRow['panel'];
                      setForm((f) => ({
                        ...f,
                        panel,
                        ...(modalEditingId == null ? { sortOrder: nextSortOrderForPanel(panel, rows) } : {}),
                      }));
                    }}
                  >
                    {PANELS.map(({ key, label }) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {modalMsg && (
                <p className={`item-catalog-msg ${modalMsg.err ? 'err' : ''}`} style={{ marginTop: '0.5rem' }}>
                  {modalMsg.text}
                </p>
              )}

              <div className="item-catalog-form-actions" style={{ marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary" disabled={imageUploading}>
                  {modalEditingId != null ? '保存' : '添加'}
                </button>
                <button type="button" className="btn btn-ghost" onClick={closeModal}>
                  取消
                </button>
                <label
                  className={`btn btn-ghost${imageUploading ? ' item-catalog-upload-disabled' : ''}`}
                  style={{ cursor: imageUploading ? 'not-allowed' : 'pointer' }}
                >
                  上传图片
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    hidden
                    disabled={imageUploading}
                    onChange={onUploadFile}
                  />
                </label>
              </div>
            </form>
          </div>
        </div>
        </>
      )}
    </div>
  );
}
