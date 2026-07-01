/**
 * 旧版神器攻略存在 localStorage key mhxy_artifact_guide_v1。
 * 登录后、清浏览器前：若库里还没有有效状态，则写入 artifact_guide_state 并删掉该 key。
 */
import { api } from '../api';

const LEGACY_KEY = 'mhxy_artifact_guide_v1';

function serverHasUsableGuideState(r: {
  persisted: boolean;
  state: { version?: number; items?: unknown } | null;
}): boolean {
  if (!r.persisted || !r.state) return false;
  const items = r.state.items;
  return r.state.version === 1 && Array.isArray(items) && items.length > 0;
}

export async function migrateArtifactGuideFromLocalStorage(): Promise<void> {
  let raw: string | null;
  try {
    raw = localStorage.getItem(LEGACY_KEY);
  } catch {
    return;
  }
  if (!raw?.trim()) return;

  try {
    const r = await api.artifactGuideStateGet();
    if (serverHasUsableGuideState(r)) {
      try {
        localStorage.removeItem(LEGACY_KEY);
      } catch {
        /* ignore */
      }
      return;
    }

    const parsed = JSON.parse(raw) as { version?: number; items?: unknown };
    if (parsed?.version === 1 && Array.isArray(parsed.items) && parsed.items.length > 0) {
      await api.artifactGuideStatePut(parsed);
    }
    try {
      localStorage.removeItem(LEGACY_KEY);
    } catch {
      /* ignore */
    }
  } catch {
    /* 网络失败等：保留 legacy key，下次登录再迁 */
  }
}
