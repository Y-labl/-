import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Item } from '../api';
import { SmartLedgerPanel } from '../components/SmartLedgerPanel';
import { BizDatePickerField } from '../components/BizDatePickerField';

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const emoji = ['🪨', '📜', '🗺️', '🛡️', '📕', '📗', '💎', '🔮', '⭐', '📘', '⚒️', '💰', '🎫'];

export function ItemsGridPage() {
  const { categoryId } = useParams();
  const cid = Number(categoryId);
  const [items, setItems] = useState<Item[]>([]);
  const [bizDate, setBizDate] = useState(todayISO);
  const [toast, setToast] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!cid) return;
    api
      .items(cid)
      .then(setItems)
      .catch((e) => setErr(e instanceof Error ? e.message : '加载失败'));
  }, [cid]);

  async function onPick(it: Item) {
    setErr('');
    setToast('');
    try {
      await api.itemGain({ itemId: it.id, quantity: 1, bizDate });
      setToast(`已记录：${it.name} ×1（${bizDate}）`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : '记录失败');
    }
  }

  return (
    <div>
      <div className="topbar">
        <h2>物品</h2>
        <Link to="/app/items" className="btn btn-ghost">
          ← 返回分类
        </Link>
      </div>
      <div className="row" style={{ marginBottom: '0.75rem', alignItems: 'center' }}>
        <BizDatePickerField id="items-grid-biz-date" value={bizDate} onChange={setBizDate} />
      </div>
      {toast && <p style={{ color: 'var(--accent)' }}>{toast}</p>}
      {err && <p style={{ color: 'var(--danger)' }}>{err}</p>}

      <SmartLedgerPanel bizDate={bizDate} title="语音 / 截图记物品与现金" />

      <div className="grid-items">
        {items.map((it, i) => (
          <button
            key={it.id}
            type="button"
            className="item-tile"
            onClick={() => onPick(it)}
            style={{ border: 'none', color: 'inherit' }}
          >
            <div
              className="thumb"
              style={{
                background: `linear-gradient(145deg, hsl(${(it.id * 31) % 360} 50% 42%), hsl(${(it.id * 17) % 360} 40% 24%))`,
              }}
            >
              {emoji[it.id % emoji.length]}
            </div>
            <div style={{ fontWeight: 700 }}>{it.name}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
