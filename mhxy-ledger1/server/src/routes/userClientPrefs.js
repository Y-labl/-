import { Router } from 'express';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';

export const userClientPrefsRouter = Router();
userClientPrefsRouter.use(authRequired);

const MAX_PREFS_BYTES = 512000;

function parsePrefsRow(raw) {
  if (raw == null) return {};
  if (typeof raw === 'object' && !Buffer.isBuffer(raw)) {
    return raw && typeof raw === 'object' && !Array.isArray(raw) ? { ...raw } : {};
  }
  if (typeof Buffer !== 'undefined' && Buffer.isBuffer(raw)) {
    try {
      const o = JSON.parse(raw.toString('utf8'));
      return o && typeof o === 'object' && !Array.isArray(o) ? o : {};
    } catch {
      return {};
    }
  }
  if (typeof raw === 'string') {
    try {
      const o = JSON.parse(raw);
      return o && typeof o === 'object' && !Array.isArray(o) ? o : {};
    } catch {
      return {};
    }
  }
  return {};
}

userClientPrefsRouter.get('/me/client-prefs', async (req, res) => {
  const uid = req.user.id;
  try {
    const [rows] = await pool.query(
      'SELECT prefs_json AS prefsJson FROM user_client_prefs WHERE user_id = ? LIMIT 1',
      [uid],
    );
    const prefs = rows.length ? parsePrefsRow(rows[0].prefsJson) : {};
    res.json({ prefs });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 user_client_prefs。请在 server 目录执行：node scripts/migrate-v45.js',
      });
    }
    throw e;
  }
});

userClientPrefsRouter.put('/me/client-prefs', async (req, res) => {
  const uid = req.user.id;
  const body = req.body?.prefs;
  if (body == null || typeof body !== 'object' || Array.isArray(body)) {
    return res.status(400).json({ error: 'prefs 须为 JSON 对象' });
  }
  const jsonStr = JSON.stringify(body);
  if (Buffer.byteLength(jsonStr, 'utf8') > MAX_PREFS_BYTES) {
    return res.status(400).json({ error: 'prefs 体积过大' });
  }
  try {
    await pool.query(
      `INSERT INTO user_client_prefs (user_id, prefs_json) VALUES (?, CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE prefs_json = VALUES(prefs_json), updated_at = CURRENT_TIMESTAMP`,
      [uid, jsonStr],
    );
    res.json({ ok: true });
  } catch (e) {
    if (e?.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({
        error: '数据库缺少 user_client_prefs。请在 server 目录执行：node scripts/migrate-v45.js',
      });
    }
    throw e;
  }
});
