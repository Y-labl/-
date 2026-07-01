import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type ItemCategory } from '../api';

export function ItemsHubPage() {
  const [cats, setCats] = useState<ItemCategory[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    api
      .categories()
      .then(setCats)
      .catch((e) => setErr(e instanceof Error ? e.message : '加载失败'));
  }, []);

  return (
    <div>
      <div className="topbar">
        <h2>物品分类</h2>
      </div>
      <p className="muted">点进分类后，点击物品卡片即可记到「当日收益」。</p>
      {err && <p style={{ color: 'var(--danger)' }}>{err}</p>}
      <div className="grid-items">
        {cats.map((c) => (
          <Link key={c.id} to={`/app/items/${c.id}`} className="item-tile" style={{ textDecoration: 'none' }}>
            <div
              className="thumb"
              style={{
                background: `linear-gradient(135deg, hsl(${(c.id * 47) % 360} 55% 35%), hsl(${(c.id * 23) % 360} 45% 22%))`,
              }}
            >
              📦
            </div>
            <div style={{ fontWeight: 700 }}>{c.name}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
