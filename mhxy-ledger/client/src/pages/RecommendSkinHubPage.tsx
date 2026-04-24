import { NavLink } from 'react-router-dom';
import { RECOMMEND_SKINS } from './recommendSkinMeta';
import './RecommendSkinHubPage.css';

export function RecommendSkinHubPage() {
  return (
    <div className="rec-skin-hub">
      <div className="rec-skin-hub__head">
        <h2>推荐榜 · 主题皮肤</h2>
        <p className="muted">
          以下主题与 <code>demo-styles</code> 中 HTML 对应（见角标；「水晶风」为扩展）。点击后<strong>全站界面主题</strong>会记住；也可在顶栏「主题」菜单切换。
        </p>
        <NavLink to="/app/tasks" className="btn btn-ghost rec-skin-hub__back">
          返回默认推荐榜
        </NavLink>
      </div>
      <div className="rec-skin-hub__grid">
        {RECOMMEND_SKINS.map((s) => (
          <NavLink key={s.id} to={`/app/tasks/style/${s.id}`} className={`rec-skin-hub__card rec-skin-hub__card--${s.id}`}>
            <span className="rec-skin-hub__card-label">{s.label}</span>
            <span className="rec-skin-hub__card-demo">{s.demo}</span>
          </NavLink>
        ))}
      </div>
    </div>
  );
}
