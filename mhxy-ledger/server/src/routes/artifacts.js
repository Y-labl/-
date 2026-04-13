import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import multer from 'multer';
import { randomUUID } from 'crypto';
import { fileURLToPath } from 'url';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { todayStr } from '../utils/date.js';
import { normalizeArtifactDayPair } from '../utils/artifactDayPair.js';

export const artifactsRouter = Router();
artifactsRouter.use(authRequired);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uploadsRoot = path.join(__dirname, '../../uploads/artifacts');
function ensureUserDir(userId) {
  const dir = path.join(uploadsRoot, String(userId));
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}
const storage = multer.diskStorage({
  destination(req, _file, cb) {
    try {
      const userId = req.user?.id;
      if (!userId) return cb(new Error('unauthorized'));
      cb(null, ensureUserDir(userId));
    } catch (e) {
      cb(e);
    }
  },
  filename(_req, file, cb) {
    const ext = path.extname(file.originalname || '') || '.png';
    cb(null, `${randomUUID()}${ext}`);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 3 * 1024 * 1024 },
  fileFilter(_req, file, cb) {
    const ok = /^image\/(png|jpeg|webp|gif)$/i.test(file.mimetype);
    if (!ok) return cb(new Error('仅支持 png / jpeg / webp / gif'));
    cb(null, true);
  },
});

function parseBizDate(req) {
  const raw = String(req.query?.bizDate || req.body?.bizDate || todayStr()).slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return todayStr();
  return raw;
}

function normalizeSelected(raw) {
  const arr = Array.isArray(raw) ? raw : [];
  const out = [];
  for (const x of arr) {
    const s = String(x || '').trim();
    if (!s) continue;
    if (s.length > 64) continue;
    out.push(s);
    if (out.length >= 2) break;
  }
  if (out.length === 2) return normalizeArtifactDayPair(out);
  return out;
}

artifactsRouter.get('/day-selected', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req);
  try {
    const [rows] = await pool.query(
      'SELECT selected_json AS selectedJson, updated_at AS updatedAt FROM artifact_day_selected WHERE user_id = ? AND biz_date = ?',
      [uid, bizDate],
    );
    if (!rows.length) return res.json({ bizDate, selected: [], updatedAt: null });
    let selected = [];
    try {
      selected = normalizeSelected(rows[0].selectedJson);
    } catch {
      selected = [];
    }
    res.json({ bizDate, selected, updatedAt: rows[0].updatedAt ?? null });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器选择表。请在 server 目录执行：node scripts/migrate-v38.js' });
    }
    throw e;
  }
});

artifactsRouter.put('/day-selected', async (req, res) => {
  const uid = req.user.id;
  const bizDate = parseBizDate(req);
  const selected = normalizeSelected(req.body?.selected);
  if (selected.length !== 2) {
    return res.status(400).json({ error: 'selected 需为 2 个神器名称' });
  }
  try {
    await pool.query(
      `INSERT INTO artifact_day_selected (user_id, biz_date, selected_json) VALUES (?,?,CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE selected_json = VALUES(selected_json), updated_at = CURRENT_TIMESTAMP`,
      [uid, bizDate, JSON.stringify(selected)],
    );
    res.json({ ok: true, bizDate, selected });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器选择表。请在 server 目录执行：node scripts/migrate-v38.js' });
    }
    throw e;
  }
});

function normalizeArtifactName(raw) {
  const s = String(raw || '').trim();
  if (!s) return '';
  if (s.length > 64) return '';
  return s;
}

artifactsRouter.get('/boss-image', async (req, res) => {
  const uid = req.user.id;
  const name = normalizeArtifactName(req.query?.name);
  if (!name) return res.status(400).json({ error: 'name 为空' });
  try {
    const [rows] = await pool.query(
      'SELECT image_url AS imageUrl, updated_at AS updatedAt FROM artifact_boss_images WHERE user_id = ? AND artifact_name = ?',
      [uid, name],
    );
    if (!rows.length) return res.json({ name, imageUrl: null, updatedAt: null });
    res.json({ name, imageUrl: String(rows[0].imageUrl || ''), updatedAt: rows[0].updatedAt ?? null });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器 BOSS 图表。请在 server 目录执行：node scripts/migrate-v39.js' });
    }
    throw e;
  }
});

artifactsRouter.post('/boss-image', upload.single('file'), async (req, res) => {
  const uid = req.user.id;
  const name = normalizeArtifactName(req.query?.name);
  if (!name) return res.status(400).json({ error: 'name 为空' });
  if (!req.file?.filename) return res.status(400).json({ error: '请上传图片 file 字段' });
  const url = `/uploads/artifacts/${uid}/${req.file.filename}`;
  try {
    await pool.query(
      `INSERT INTO artifact_boss_images (user_id, artifact_name, image_url) VALUES (?,?,?)
       ON DUPLICATE KEY UPDATE image_url = VALUES(image_url), updated_at = CURRENT_TIMESTAMP`,
      [uid, name, url],
    );
    res.json({ ok: true, name, imageUrl: url });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器 BOSS 图表。请在 server 目录执行：node scripts/migrate-v39.js' });
    }
    throw e;
  }
});

artifactsRouter.delete('/boss-image', async (req, res) => {
  const uid = req.user.id;
  const name = normalizeArtifactName(req.query?.name);
  if (!name) return res.status(400).json({ error: 'name 为空' });
  try {
    await pool.query('DELETE FROM artifact_boss_images WHERE user_id = ? AND artifact_name = ?', [uid, name]);
    res.json({ ok: true, name });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器 BOSS 图表。请在 server 目录执行：node scripts/migrate-v39.js' });
    }
    throw e;
  }
});

function normalizeGuideState(raw) {
  const o = raw && typeof raw === 'object' ? raw : null;
  if (!o) return null;
  const ver = Number(o.version);
  const items = Array.isArray(o.items) ? o.items : null;
  if (ver !== 1 || !items) return null;
  // Light validation to avoid storing junk; client owns full schema.
  return { ...o, version: 1, items };
}

artifactsRouter.get('/guide-state', async (req, res) => {
  const uid = req.user.id;
  try {
    const [rows] = await pool.query(
      'SELECT state_json AS stateJson, updated_at AS updatedAt FROM artifact_guide_state WHERE user_id = ? LIMIT 1',
      [uid],
    );
    if (!rows.length) return res.json({ persisted: false, state: null, updatedAt: null });
    let state = null;
    try {
      state = normalizeGuideState(rows[0].stateJson);
    } catch {
      state = null;
    }
    res.json({ persisted: true, state, updatedAt: rows[0].updatedAt ?? null });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器攻略表。请在 server 目录执行：node scripts/migrate-v40.js' });
    }
    throw e;
  }
});

artifactsRouter.put('/guide-state', async (req, res) => {
  const uid = req.user.id;
  const state = normalizeGuideState(req.body?.state);
  if (!state) return res.status(400).json({ error: 'state 无效' });
  try {
    await pool.query(
      `INSERT INTO artifact_guide_state (user_id, state_json) VALUES (?, CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE state_json = VALUES(state_json), updated_at = CURRENT_TIMESTAMP`,
      [uid, JSON.stringify(state)],
    );
    res.json({ ok: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器攻略表。请在 server 目录执行：node scripts/migrate-v40.js' });
    }
    throw e;
  }
});

function normalizeGuideNames(raw) {
  const s = String(raw || '').trim();
  if (!s) return [];
  const out = [];
  for (const part of s.split(',').map((x) => x.trim())) {
    if (!part) continue;
    if (part.length > 64) continue;
    out.push(part);
    if (out.length >= 80) break;
  }
  return out;
}

artifactsRouter.get('/guide-content', async (req, res) => {
  const names = normalizeGuideNames(req.query?.names);
  try {
    if (!names.length) {
      const [rows] = await pool.query(
        'SELECT artifact_name AS name, content_json AS contentJson, updated_at AS updatedAt FROM artifact_guide_content ORDER BY artifact_name',
      );
      const items = rows.map((r) => ({
        name: String(r.name || ''),
        content: r.contentJson ?? null,
        updatedAt: r.updatedAt ?? null,
      }));
      return res.json({ items });
    }
    const placeholders = names.map(() => '?').join(',');
    const [rows] = await pool.query(
      `SELECT artifact_name AS name, content_json AS contentJson, updated_at AS updatedAt
       FROM artifact_guide_content
       WHERE artifact_name IN (${placeholders})`,
      names,
    );
    const items = rows.map((r) => ({
      name: String(r.name || ''),
      content: r.contentJson ?? null,
      updatedAt: r.updatedAt ?? null,
    }));
    res.json({ items });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: '数据库缺少神器攻略内容表。请在 server 目录执行：node scripts/migrate-v41.js' });
    }
    throw e;
  }
});

