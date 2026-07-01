import { useLayoutEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppTheme } from '../contexts/AppThemeContext';
import { isRecommendSkinId } from './recommendSkinMeta';

/** /app/tasks/style/:skinId — 写入全站主题并回到推荐榜 */
export function RecommendSkinRoute() {
  const { skinId } = useParams();
  const nav = useNavigate();
  const { setThemeId } = useAppTheme();

  useLayoutEffect(() => {
    if (isRecommendSkinId(skinId)) {
      setThemeId(skinId);
      nav('/app/tasks', { replace: true });
    } else {
      nav('/app/tasks/styles', { replace: true });
    }
  }, [skinId, setThemeId, nav]);

  return null;
}
