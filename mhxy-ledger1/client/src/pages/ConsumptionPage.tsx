import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import {
  api,
  type ConsumptionCharacterRow,
  type ConsumptionDayBoardRow,
  type ConsumptionDayCatalogLine,
  type ItemCatalogAllResponse,
  type ItemCatalogRow,
} from '../api';
import { BizDatePickerField } from '../components/BizDatePickerField';
import { TablePaginationBar } from '../components/TablePaginationBar';
import { useTablePagination } from '../hooks/useTablePagination';
import { localBizDate } from '../utils/bizDate';
import { BIZ_DATE_PAGE } from '../utils/pageBizDate';
import { usePageBizDate } from '../utils/usePageBizDate';
import { formatWanZhCN } from '../utils/formatWanZhCN';
import './ConsumptionPage.css';

const SECT_SUGGESTIONS = [
  '大唐官府',
  '化生寺',
  '女儿村',
  '方寸山',
  '天宫',
  '龙宫',
  '五庄观',
  '普陀山',
  '阴曹地府',
  '盘丝洞',
  '狮驼岭',
  '魔王寨',
  '神木林',
  '凌波城',
  '无底洞',
  '女魃墓',
  '天机城',
  '花果山',
];

function flattenCatalog(panels: ItemCatalogAllResponse['panels']): ItemCatalogRow[] {
  const keys: (keyof ItemCatalogAllResponse['panels'])[] = [
    'fixed',
    'var',
    'yaksha_white',
    'yaksha_reward',
    'scene',
  ];
  const out: ItemCatalogRow[] = [];
  for (const k of keys) {
    out.push(...(panels[k] ?? []));
  }
  out.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
  return out;
}

function itemNameHasRuneStone(name: string) {
  return name.includes('符石');
}

/**
 * 从物品库条目解析珍珠等级（数字键，如 "120"），用于与物品库名称/等级标签对齐。
 * 优先匹配「N级」，其次 levelLabel 纯数字，再尝试名称中珍珠后的数字。
 */
function extractPearlLevelKey(item: ItemCatalogRow): string | null {
  if (!item.name.includes('珍珠')) return null;
  const name = item.name;
  const m1 = name.match(/(\d+)\s*级/);
  if (m1) return m1[1];
  const ll = (item.levelLabel || '').trim();
  if (/^\d+$/.test(ll)) return ll;
  const m2 = name.match(/珍珠[^\d]{0,6}(\d{1,3})/);
  if (m2) return m2[1];
  return null;
}

/** 珍珠等级下拉固定选项（与常用装备等级段一致） */
const PEARL_LEVEL_SELECT_KEYS: string[] = ['70', '80', '90', '100', '110', '120', '130', '140'];

/** 按等级聚合物品库中的珍珠，供筛选与单价展示 */
function buildPearlLevelsMap(catalog: ItemCatalogRow[]) {
  const map = new Map<string, ItemCatalogRow[]>();
  for (const it of catalog) {
    const key = extractPearlLevelKey(it);
    if (key == null) continue;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(it);
  }
  return map;
}

function formatPriceWRange(items: ItemCatalogRow[]) {
  const prices = [...new Set(items.map((i) => Number(i.priceW)).filter((p) => Number.isFinite(p) && p > 0))];
  if (prices.length === 0) return null;
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  if (min === max) return `${min} 万`;
  return `${min}～${max} 万`;
}

function formatConsumptionItemsLabel(lines: ConsumptionDayCatalogLine[]): string {
  if (lines.length === 0) return '';
  return lines.map((l) => `${l.name}×${l.quantity}`).join('、');
}

function sumCatalogLinesValueW(lines: ConsumptionDayCatalogLine[], catalogById: Map<number, ItemCatalogRow>): number {
  let s = 0;
  for (const l of lines) {
    const it = catalogById.get(l.catalogItemId);
    const pw = it ? Number(it.priceW) : NaN;
    if (Number.isFinite(pw) && pw >= 0) s += pw * l.quantity;
  }
  return Math.round(Math.max(0, s) * 10000) / 10000;
}

function dreamWFieldFromNumber(w: number): string {
  if (!Number.isFinite(w) || w <= 0) return '';
  const x = Math.round(w * 10000) / 10000;
  return String(x);
}

export function ConsumptionPage() {
  const [bizDate, setBizDate] = usePageBizDate(BIZ_DATE_PAGE.consumption);
  const [board, setBoard] = useState<ConsumptionDayBoardRow[]>([]);
  const [characters, setCharacters] = useState<ConsumptionCharacterRow[]>([]);
  const [catalogFlat, setCatalogFlat] = useState<ItemCatalogRow[]>([]);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [boardLoading, setBoardLoading] = useState(true);
  const [charsLoaded, setCharsLoaded] = useState(false);
  const [rosterOpen, setRosterOpen] = useState(false);

  const [newName, setNewName] = useState('');
  const [newLevel, setNewLevel] = useState('');
  const [newSect, setNewSect] = useState('');
  const [rosterErr, setRosterErr] = useState('');

  const loadBoard = useCallback(async () => {
    setBoardLoading(true);
    try {
      const r = await api.consumptionDayBoard(bizDate);
      setBoard(r.rows);
    } catch {
      setBoard([]);
    } finally {
      setBoardLoading(false);
    }
  }, [bizDate]);

  const boardReloadTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scheduleBoardReload = useCallback(() => {
    if (boardReloadTimerRef.current) clearTimeout(boardReloadTimerRef.current);
    boardReloadTimerRef.current = setTimeout(() => {
      boardReloadTimerRef.current = null;
      void loadBoard();
    }, 400);
  }, [loadBoard]);

  useEffect(() => {
    setBoard([]);
  }, [bizDate]);

  const loadCharacters = useCallback(async () => {
    try {
      const r = await api.consumptionCharactersList();
      setCharacters(r.items);
    } catch {
      setCharacters([]);
    } finally {
      setCharsLoaded(true);
    }
  }, []);

  const loadCatalog = useCallback(async () => {
    try {
      const r = await api.itemCatalogAll();
      setCatalogFlat(flattenCatalog(r.panels));
    } catch {
      setCatalogFlat([]);
    }
  }, []);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  useEffect(() => {
    loadCharacters();
    loadCatalog();
  }, [loadCharacters, loadCatalog]);

  function openRoster() {
    setRosterErr('');
    setNewName('');
    setNewLevel('');
    setNewSect('');
    setRosterOpen(true);
    loadCharacters();
  }

  async function addCharacter(e: React.FormEvent) {
    e.preventDefault();
    setRosterErr('');
    const name = newName.trim();
    if (!name) return setRosterErr('请填写角色名称');
    try {
      await api.consumptionCharacterCreate({
        characterName: name,
        levelLabel: newLevel.trim(),
        sect: newSect.trim(),
      });
      setNewName('');
      setNewLevel('');
      setNewSect('');
      await loadCharacters();
      await loadBoard();
    } catch (ex) {
      setRosterErr(ex instanceof Error ? ex.message : '失败');
    }
  }

  async function removeCharacter(id: number) {
    if (!window.confirm('确定从名单中移除该角色？当日消耗行会一并删除。')) return;
    setRosterErr('');
    try {
      await api.consumptionCharacterDelete(id);
      await loadCharacters();
      await loadBoard();
    } catch (ex) {
      setRosterErr(ex instanceof Error ? ex.message : '失败');
    }
  }

  /** 以维护名单为准固定展示行；board 仅合并已保存的当日数据 */
  const displayRows = useMemo((): ConsumptionDayBoardRow[] => {
    if (characters.length === 0) return [];
    const byId = new Map(board.map((r) => [r.characterId, r]));
    return characters.map((c) => {
      const b = byId.get(c.id);
      if (b) return b;
      return {
        characterId: c.id,
        characterName: c.characterName,
        levelLabel: c.levelLabel,
        sect: c.sect,
        rmbAmount: 0,
        dreamCoinW: 0,
        note: '',
        catalogLines: [],
      };
    });
  }, [characters, board]);

  const totals = useMemo(() => {
    return displayRows.reduce(
      (acc, r) => {
        acc.rmb += Number(r.rmbAmount);
        acc.dream += Number(r.dreamCoinW);
        acc.itemQty += r.catalogLines.reduce((s, l) => s + l.quantity, 0);
        return acc;
      },
      { rmb: 0, dream: 0, itemQty: 0 }
    );
  }, [displayRows]);

  const consumptionDayPg = useTablePagination(displayRows);
  const rosterPg = useTablePagination(characters);

  return (
    <div>
      <div className="topbar">
        <h2>消耗</h2>
        <div className="consumption-top-actions">
          <Link to="/app/ledger" className="btn btn-ghost">
            返回记账台
          </Link>
        </div>
      </div>
      <p className="muted">
        <strong>业务日期</strong>与总览一致（YYYY-MM-DD）。<strong>当日记录</strong>固定展示维护角色（每人一行）；金额与备注在<strong>输入框失焦</strong>时自动保存，选完物品点「确定」后也会自动保存。<strong>梦幻币(万)</strong>会按物品库单价×数量与所选物品联动（改物品或单价后点确定会重算；单价为 0 时请先在物品库维护）。备注为空时会自动填入物品摘要。
      </p>

      <div className="consumption-toolbar">
        <BizDatePickerField id="consumption-biz-date" value={bizDate} onChange={setBizDate} />
        <button type="button" className="btn btn-ghost consumption-toolbar-btn" onClick={openRoster}>
          维护角色
        </button>
      </div>

      {msg && <p style={{ color: 'var(--accent)' }}>{msg}</p>}
      {err && <p style={{ color: 'var(--danger)' }}>{err}</p>}

      <div className="card" style={{ padding: '1rem' }}>
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <div>
            <h3 style={{ margin: 0 }}>当日记录</h3>
            <p className="muted" style={{ margin: '0.25rem 0 0', fontSize: '0.8rem' }}>
              点卡 · 人民币 · 梦幻币 · 物品
            </p>
          </div>
          <span className="muted" style={{ fontSize: '0.88rem' }}>
            合计 ¥{totals.rmb.toFixed(2)}
            <span> · 梦幻币 {formatWanZhCN(totals.dream)}</span>
            {totals.itemQty > 0 && <span> · 物品件数 {totals.itemQty}</span>}
          </span>
        </div>
        {!charsLoaded ? (
          <p className="muted">加载中…</p>
        ) : displayRows.length === 0 ? (
          <p className="muted">暂无维护角色，请点击「维护角色」添加。</p>
        ) : (
          <div className="consumption-day-table-wrap">
            {boardLoading && (
              <p className="muted" style={{ fontSize: '0.82rem', marginBottom: '0.5rem' }}>
                正在同步当日已保存数据…
              </p>
            )}
            <table className="consumption-table consumption-day-table">
              <colgroup>
                <col className="consumption-col-char" />
                <col className="consumption-col-level" />
                <col className="consumption-col-sect" />
                <col className="consumption-col-num" />
                <col className="consumption-col-num" />
                <col className="consumption-col-items" />
                <col className="consumption-col-note" />
              </colgroup>
              <thead>
                <tr>
                  <th scope="col">角色</th>
                  <th scope="col">等级</th>
                  <th scope="col">门派</th>
                  <th className="num" scope="col">
                    充值(元)
                  </th>
                  <th className="num" scope="col">
                    梦幻币(万)
                  </th>
                  <th scope="col">物品消耗</th>
                  <th scope="col">备注</th>
                </tr>
              </thead>
              <tbody>
                {consumptionDayPg.slice.map((row) => (
                  <DayCharacterRow
                    key={row.characterId}
                    bizDate={bizDate}
                    row={row}
                    catalogOptions={catalogFlat}
                    onPersisted={scheduleBoardReload}
                    onPersistError={(name, message) => {
                      setErr(`${name}：${message}`);
                      setMsg('');
                    }}
                  />
                ))}
              </tbody>
            </table>
            <TablePaginationBar
              page={consumptionDayPg.page}
              totalPages={consumptionDayPg.totalPages}
              total={consumptionDayPg.total}
              pageSize={consumptionDayPg.pageSize}
              onPageChange={consumptionDayPg.setPage}
              onPageSizeChange={consumptionDayPg.setPageSize}
            />
          </div>
        )}
      </div>

      {rosterOpen && (
        <div
          className="modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="consumption-roster-title"
          onMouseDown={(ev) => {
            if (ev.target === ev.currentTarget) setRosterOpen(false);
          }}
        >
          <div className="modal card consumption-modal" onMouseDown={(e) => e.stopPropagation()}>
            <h2 id="consumption-roster-title">维护角色</h2>
            <p className="muted" style={{ margin: '0 0 1rem', fontSize: '0.85rem' }}>
              名单长期有效；当日表格按此名单生成一行。同名角色不可重复。
            </p>
            {rosterErr && <p style={{ color: 'var(--danger)', marginBottom: '0.75rem' }}>{rosterErr}</p>}
            {characters.length === 0 ? (
              <p className="muted" style={{ marginBottom: '1rem' }}>
                暂无角色，请在下方添加。
              </p>
            ) : (
              <div className="consumption-roster-table-wrap">
                <table className="consumption-table consumption-roster-table">
                  <thead>
                    <tr>
                      <th>角色</th>
                      <th>等级</th>
                      <th>门派</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {rosterPg.slice.map((c) => (
                      <RosterRow
                        key={c.id}
                        c={c}
                        onSaved={async () => {
                          await loadCharacters();
                          await loadBoard();
                        }}
                        onRemove={() => removeCharacter(c.id)}
                      />
                    ))}
                  </tbody>
                </table>
                <TablePaginationBar
                  page={rosterPg.page}
                  totalPages={rosterPg.totalPages}
                  total={rosterPg.total}
                  pageSize={rosterPg.pageSize}
                  onPageChange={rosterPg.setPage}
                  onPageSizeChange={rosterPg.setPageSize}
                />
              </div>
            )}
            <form onSubmit={addCharacter} className="consumption-form consumption-roster-add">
              <h3 className="consumption-roster-add-title">新增角色</h3>
              <label className="consumption-field">
                <span>角色名称</span>
                <input className="input" placeholder="例如：剑侠客·一区" value={newName} onChange={(e) => setNewName(e.target.value)} />
              </label>
              <label className="consumption-field">
                <span>等级</span>
                <input className="input" placeholder="例如：175、化圣9" value={newLevel} onChange={(e) => setNewLevel(e.target.value)} />
              </label>
              <label className="consumption-field">
                <span>门派</span>
                <input
                  className="input"
                  list="mhxy-sect-list-consumption"
                  placeholder="可输入或从列表选"
                  value={newSect}
                  onChange={(e) => setNewSect(e.target.value)}
                />
              </label>
              <datalist id="mhxy-sect-list-consumption">
                {SECT_SUGGESTIONS.map((s) => (
                  <option key={s} value={s} />
                ))}
              </datalist>
              <div className="consumption-form-actions">
                <button className="btn btn-primary" type="submit">
                  添加
                </button>
              </div>
            </form>
            <div className="consumption-modal-actions" style={{ marginTop: '1rem' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setRosterOpen(false)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DayCharacterRow({
  bizDate,
  row,
  catalogOptions,
  onPersisted,
  onPersistError,
}: {
  bizDate: string;
  row: ConsumptionDayBoardRow;
  catalogOptions: ItemCatalogRow[];
  onPersisted: () => void;
  onPersistError: (characterName: string, message: string) => void;
}) {
  const syncToken = `${row.characterId}|${row.rmbAmount}|${row.dreamCoinW}|${row.note}|${row.catalogLines.map((l) => `${l.catalogItemId}:${l.quantity}`).join(';')}`;

  const [rmbStr, setRmbStr] = useState(() => (row.rmbAmount === 0 ? '' : String(row.rmbAmount)));
  const [dreamStr, setDreamStr] = useState(() => (row.dreamCoinW === 0 ? '' : String(row.dreamCoinW)));
  const [note, setNote] = useState(row.note);
  const [lines, setLines] = useState<ConsumptionDayCatalogLine[]>(() => [...row.catalogLines]);
  const [itemModal, setItemModal] = useState(false);

  useEffect(() => {
    setRmbStr(row.rmbAmount === 0 ? '' : String(row.rmbAmount));
    setDreamStr(row.dreamCoinW === 0 ? '' : String(row.dreamCoinW));
    const itemsSummary = formatConsumptionItemsLabel(row.catalogLines);
    setNote(row.note.trim() !== '' ? row.note : itemsSummary);
    setLines([...row.catalogLines]);
  }, [syncToken, bizDate]);

  const itemsLabel =
    lines.length === 0
      ? '—'
      : lines.map((l) => `${l.name}×${l.quantity}`).join('、');

  const executePersist = useCallback(
    async (overrides?: {
      linesOverride?: ConsumptionDayCatalogLine[];
      dreamStrOverride?: string;
      noteOverride?: string;
    }): Promise<{ ok: boolean; err?: string }> => {
      const linesToSave = overrides?.linesOverride ?? lines;
      const dreamSrc = overrides?.dreamStrOverride !== undefined ? overrides.dreamStrOverride : dreamStr;
      const noteSrc = overrides?.noteOverride !== undefined ? overrides.noteOverride : note;
      const rmb = rmbStr.trim() === '' ? 0 : Number(rmbStr);
      const dream = dreamSrc.trim() === '' ? 0 : Number(dreamSrc);
      if (Number.isNaN(rmb) || rmb < 0) return { ok: false, err: '人民币金额无效' };
      if (Number.isNaN(dream) || dream < 0) return { ok: false, err: '梦幻币（万）无效' };
      try {
        await api.consumptionDayBoardSaveRow({
          bizDate,
          characterId: row.characterId,
          rmbAmount: rmb,
          dreamCoinW: dream,
          note: noteSrc.trim(),
          catalogLines: linesToSave.map((l) => ({ catalogItemId: l.catalogItemId, quantity: l.quantity })),
        });
        return { ok: true };
      } catch (ex) {
        return { ok: false, err: ex instanceof Error ? ex.message : '保存失败' };
      }
    },
    [bizDate, row.characterId, rmbStr, dreamStr, note, lines]
  );

  const autoSave = useCallback(async () => {
    const r = await executePersist();
    if (!r.ok) {
      if (r.err) onPersistError(row.characterName, r.err);
      return;
    }
    onPersisted();
  }, [executePersist, onPersistError, onPersisted, row.characterName]);

  return (
    <>
      <tr>
        <td>{row.characterName}</td>
        <td>{row.levelLabel || '—'}</td>
        <td>{row.sect || '—'}</td>
        <td className="consumption-day-cell-num">
          <input
            className="input consumption-day-input"
            type="number"
            min={0}
            step="0.01"
            placeholder="0"
            value={rmbStr}
            onChange={(e) => setRmbStr(e.target.value)}
            onBlur={() => {
              void autoSave();
            }}
            aria-label={`${row.characterName} 充值元`}
          />
        </td>
        <td className="consumption-day-cell-num">
          <input
            className="input consumption-day-input"
            type="number"
            min={0}
            step="0.0001"
            placeholder="0"
            value={dreamStr}
            onChange={(e) => setDreamStr(e.target.value)}
            onBlur={() => {
              void autoSave();
            }}
            aria-label={`${row.characterName} 梦幻币万`}
          />
        </td>
        <td className="consumption-day-items-cell">
          <button type="button" className="btn btn-ghost btn-sm consumption-day-items-btn" onClick={() => setItemModal(true)}>
            物品
          </button>
        </td>
        <td className="consumption-day-note-cell">
          {lines.length > 0 && note.trim() !== itemsLabel && (
            <div className="consumption-day-note-items-line" title={itemsLabel}>
              {itemsLabel}
            </div>
          )}
          <input
            className="input consumption-day-input consumption-day-input--note"
            placeholder={lines.length > 0 ? '补充说明（可选）' : '—'}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            onBlur={() => {
              void autoSave();
            }}
            aria-label={`${row.characterName} 备注`}
          />
        </td>
      </tr>
      {itemModal &&
        createPortal(
          <CatalogLinesModal
            catalogOptions={catalogOptions}
            initialLines={lines}
            onClose={() => setItemModal(false)}
            onCommit={(next) => {
              const byId = new Map(catalogOptions.map((c) => [c.id, c]));
              const newItemW = sumCatalogLinesValueW(next, byId);
              const oldItemW = sumCatalogLinesValueW(lines, byId);
              const prevDreamNum = dreamStr.trim() === '' ? 0 : Number(dreamStr);
              const safePrev =
                Number.isFinite(prevDreamNum) && prevDreamNum >= 0 ? prevDreamNum : 0;
              const nextDreamNum = Math.round((safePrev - oldItemW + newItemW) * 10000) / 10000;
              const dreamFormatted = dreamWFieldFromNumber(nextDreamNum);

              const label = formatConsumptionItemsLabel(next);
              const noteAfter = note.trim() === '' && label ? label : note;

              setDreamStr(dreamFormatted);
              setLines(next);
              setNote(noteAfter);
              setItemModal(false);
              void (async () => {
                const r = await executePersist({
                  linesOverride: next,
                  dreamStrOverride: dreamFormatted,
                  noteOverride: noteAfter,
                });
                if (!r.ok) {
                  if (r.err) onPersistError(row.characterName, r.err);
                  return;
                }
                onPersisted();
              })();
            }}
          />,
          document.body
        )}
    </>
  );
}

function CatalogLinesModal({
  catalogOptions,
  initialLines,
  onClose,
  onCommit,
}: {
  catalogOptions: ItemCatalogRow[];
  initialLines: ConsumptionDayCatalogLine[];
  onClose: () => void;
  onCommit: (lines: ConsumptionDayCatalogLine[]) => void;
}) {
  const [draft, setDraft] = useState<ConsumptionDayCatalogLine[]>(() => initialLines.map((l) => ({ ...l })));
  const [pickId, setPickId] = useState<number | ''>('');
  const [pickQty, setPickQty] = useState('1');
  const [filterRune, setFilterRune] = useState(false);
  const [filterPearl, setFilterPearl] = useState(false);
  const [pearlLevel, setPearlLevel] = useState('');

  const pearlsByLevel = useMemo(() => buildPearlLevelsMap(catalogOptions), [catalogOptions]);

  const pearlLevelPriceHint = useMemo(() => {
    if (!filterPearl || !pearlLevel) return null;
    const items = pearlsByLevel.get(pearlLevel);
    if (!items?.length) return null;
    const r = formatPriceWRange(items);
    if (!r) return '该等级珍珠在物品库中单价为 0 或未维护，可在物品库填写单价（万）。';
    return `该等级参考单价（物品库）：${r}`;
  }, [filterPearl, pearlLevel, pearlsByLevel]);

  const filteredPickOptions = useMemo(() => {
    if (!filterRune && !filterPearl) {
      return [...catalogOptions].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
    }
    const byId = new Map<number, ItemCatalogRow>();
    if (filterRune) {
      for (const it of catalogOptions) {
        if (itemNameHasRuneStone(it.name)) byId.set(it.id, it);
      }
    }
    if (filterPearl && pearlLevel) {
      for (const it of pearlsByLevel.get(pearlLevel) ?? []) {
        byId.set(it.id, it);
      }
    }
    return [...byId.values()].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
  }, [catalogOptions, filterRune, filterPearl, pearlLevel, pearlsByLevel]);

  useEffect(() => {
    if (pickId === '') return;
    if (!filteredPickOptions.some((x) => x.id === pickId)) setPickId('');
  }, [filteredPickOptions, pickId]);

  function addLine() {
    if (pickId === '') return;
    const id = Number(pickId);
    const qty = Math.max(1, Math.floor(Number(pickQty) || 1));
    const item = filteredPickOptions.find((x) => x.id === id) ?? catalogOptions.find((x) => x.id === id);
    if (!item) return;
    const i = draft.findIndex((l) => l.catalogItemId === id);
    if (i >= 0) {
      const next = [...draft];
      next[i] = { ...next[i], quantity: next[i].quantity + qty };
      setDraft(next);
    } else {
      setDraft([...draft, { catalogItemId: id, name: item.name, quantity: qty }]);
    }
    setPickQty('1');
  }

  function removeLine(catalogItemId: number) {
    setDraft(draft.filter((l) => l.catalogItemId !== catalogItemId));
  }

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="consumption-items-title"
      onMouseDown={(ev) => {
        if (ev.target === ev.currentTarget) onClose();
      }}
    >
      <div className="modal card consumption-modal consumption-items-modal" onMouseDown={(e) => e.stopPropagation()}>
        <h2 id="consumption-items-title">物品消耗（物品库）</h2>
        {catalogOptions.length === 0 ? (
          <p className="muted">物品库为空，请先在记账台物品库中添加物品。</p>
        ) : (
          <>
            <div className="consumption-items-filters" role="group" aria-label="物品类型筛选">
              <label className="consumption-items-filter-check">
                <input
                  type="checkbox"
                  checked={filterRune}
                  onChange={(e) => setFilterRune(e.target.checked)}
                />
                <span>符石</span>
              </label>
              <label className="consumption-items-filter-check">
                <input
                  type="checkbox"
                  checked={filterPearl}
                  onChange={(e) => {
                    setFilterPearl(e.target.checked);
                    if (!e.target.checked) setPearlLevel('');
                  }}
                />
                <span>珍珠</span>
              </label>
              {filterPearl && (
                <select
                  className="input consumption-items-pearl-level"
                  value={pearlLevel}
                  onChange={(e) => setPearlLevel(e.target.value)}
                  aria-label="珍珠等级"
                >
                  <option value="">选择珍珠等级…</option>
                  {PEARL_LEVEL_SELECT_KEYS.map((lv) => {
                    const items = pearlsByLevel.get(lv) ?? [];
                    const pr = formatPriceWRange(items);
                    return (
                      <option key={lv} value={lv}>
                        {lv}级{pr ? ` · ${pr}` : ''}
                      </option>
                    );
                  })}
                </select>
              )}
            </div>
            {filterPearl && pearlLevelPriceHint && (
              <p className="consumption-pearl-price-hint" style={{ fontSize: '0.85rem', margin: '0 0 0.65rem' }}>
                {pearlLevelPriceHint}
              </p>
            )}
            {filterPearl && !pearlLevel && (
              <p className="muted" style={{ fontSize: '0.82rem', margin: '0 0 0.65rem' }}>
                已勾选珍珠，请先在上方选择等级，再在下拉中选具体物品（单价见物品库）。
              </p>
            )}
            {(filterRune || filterPearl) && filteredPickOptions.length === 0 && (
              <p className="muted" style={{ fontSize: '0.82rem', margin: '0 0 0.65rem' }}>
                当前筛选下没有匹配物品，请检查物品库名称是否含「符石」或「珍珠」与等级，或取消勾选查看全部。
              </p>
            )}
            <div className="consumption-items-add-row">
              <select
                className="input"
                value={pickId === '' ? '' : String(pickId)}
                onChange={(e) => setPickId(e.target.value ? Number(e.target.value) : '')}
                aria-label="选择物品"
              >
                <option value="">
                  {filterRune || filterPearl ? '筛选后的物品…' : '选择物品…'}
                </option>
                {filteredPickOptions.map((it) => (
                  <option key={it.id} value={it.id}>
                    {it.name}
                    {Number(it.priceW) > 0 ? ` · ${Number(it.priceW)}万` : ''}
                  </option>
                ))}
              </select>
              <input
                className="input"
                type="number"
                min={1}
                step={1}
                value={pickQty}
                onChange={(e) => setPickQty(e.target.value)}
                style={{ width: '5rem' }}
                aria-label="数量"
              />
              <button type="button" className="btn btn-ghost" onClick={addLine}>
                添加
              </button>
            </div>
            {draft.length === 0 ? (
              <p className="muted" style={{ margin: '0.75rem 0' }}>
                暂无行，可从上方选择物品添加。
              </p>
            ) : (
              <ul className="consumption-items-list">
                {draft.map((l) => (
                  <li key={l.catalogItemId}>
                    <span>
                      {l.name} × {l.quantity}
                    </span>
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => removeLine(l.catalogItemId)}>
                      删除
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
        <div className="consumption-modal-actions" style={{ marginTop: '1rem' }}>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            取消
          </button>
          <button type="button" className="btn btn-primary" onClick={() => onCommit(draft)}>
            确定
          </button>
        </div>
      </div>
    </div>
  );
}

function RosterRow({
  c,
  onSaved,
  onRemove,
}: {
  c: ConsumptionCharacterRow;
  onSaved: () => Promise<void>;
  onRemove: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(c.characterName);
  const [level, setLevel] = useState(c.levelLabel);
  const [sect, setSect] = useState(c.sect);
  const [busy, setBusy] = useState(false);
  const [localErr, setLocalErr] = useState('');

  useEffect(() => {
    if (!editing) {
      setName(c.characterName);
      setLevel(c.levelLabel);
      setSect(c.sect);
    }
  }, [c, editing]);

  async function save() {
    setLocalErr('');
    setBusy(true);
    try {
      await api.consumptionCharacterUpdate(c.id, {
        characterName: name.trim(),
        levelLabel: level.trim(),
        sect: sect.trim(),
      });
      setEditing(false);
      await onSaved();
    } catch (ex) {
      setLocalErr(ex instanceof Error ? ex.message : '失败');
    } finally {
      setBusy(false);
    }
  }

  if (!editing) {
    return (
      <tr>
        <td>{c.characterName}</td>
        <td>{c.levelLabel || '—'}</td>
        <td>{c.sect || '—'}</td>
        <td className="consumption-roster-actions">
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
            编辑
          </button>
          <button type="button" className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }} onClick={onRemove}>
            删除
          </button>
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td colSpan={4} style={{ padding: '0.65rem 0.5rem', background: 'rgba(0,0,0,0.12)' }}>
        {localErr && <p style={{ color: 'var(--danger)', fontSize: '0.82rem', margin: '0 0 0.5rem' }}>{localErr}</p>}
        <div className="consumption-roster-edit-grid">
          <label className="consumption-field">
            <span>角色名称</span>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="consumption-field">
            <span>等级</span>
            <input className="input" value={level} onChange={(e) => setLevel(e.target.value)} />
          </label>
          <label className="consumption-field">
            <span>门派</span>
            <input
              className="input"
              list={`mhxy-sect-roster-${c.id}`}
              value={sect}
              onChange={(e) => setSect(e.target.value)}
            />
          </label>
          <datalist id={`mhxy-sect-roster-${c.id}`}>
            {SECT_SUGGESTIONS.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
          <div className="consumption-roster-edit-btns">
            <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => setEditing(false)}>
              取消
            </button>
            <button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={save}>
              保存
            </button>
          </div>
        </div>
      </td>
    </tr>
  );
}
