export type ArtifactGuideContent = {
  /** 高层提示（可选） */
  overview?: string[];
  /** 分支/选项建议（可选） */
  branches?: { title: string; recommend: string; why?: string; notes?: string[] }[];
  /** 按战斗拆解（核心展示） */
  battles: { title: string; steps: string[]; tips?: string[] }[];
  /** optional: if you later have a stable image URL */
  bossImageUrl?: string;
  sources: { title: string; url: string }[];
};

// 攻略内容不在前端内置：由服务端从数据库返回（/api/artifacts/guide-content）
export const ARTIFACT_GUIDE_CONTENT: Record<string, ArtifactGuideContent> = {};

