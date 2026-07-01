import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';
import multer from 'multer';
import { fileURLToPath } from 'url';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { getItemCatalogPresetRows } from '../data/itemCatalogPreset.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uploadsRoot = path.join(__dirname, '../../uploads/catalog');

function ensureUserDir(userId) {
  const dir = path.join(uploadsRoot, String(userId));
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

const storage = multer.diskStorage({
  destination(_req, file, cb) {
    try {
      const userId = _req.user?.id;
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
  limits: { fileSize: 2 * 1024 * 1024 },
  fileFilter(_req, file, cb) {
    const ok = /^image\/(png|jpeg|webp|gif)$/i.test(file.mimetype);
    if (!ok) return cb(new Error('仅支持 png / jpeg / webp / gif'));
    cb(null, true);
  },
});

export const itemCatalogRouter = Router();
itemCatalogRouter.use(authRequired);

/** JWT sub 可能是字符串，统一为数字再参与 SQL，避免个别环境下驱动/比较异常 */
itemCatalogRouter.use((req, res, next) => {
  const n = Number(req.user?.id);
  if (!Number.isFinite(n) || n < 1) {
    return res.status(401).json({ error: '登录状态异常，请重新登录' });
  }
  req.user = { ...req.user, id: n };
  next();
});

const PANELS = ['fixed', 'var', 'yaksha_white', 'yaksha_reward', 'scene'];

const TABLE = 'catalog_items';

function wrapAsync(handler, fallback) {
  return (req, res, next) => {
    Promise.resolve(handler(req, res)).catch((e) => {
      if (res.headersSent) return next(e);
      itemCatalogErr(res, e, fallback);
    });
  };
}

function itemCatalogErr(res, e, fallback = '操作失败') {
  console.error('[item-catalog]', e);
  const code = e?.code;
  if (code === 'ER_NO_SUCH_TABLE') {
    return res.status(503).json({
      error:
        '数据库缺少物品价格表 catalog_items。请在 mhxy-ledger/server 下执行：npm run db:migrate-v5，或 npm run db:schema',
    });
  }
  if (code === 'ER_BAD_FIELD_ERROR') {
    return res.status(503).json({
      error: '数据库表 catalog_items 字段与程序不一致，请执行 npm run db:migrate-v5 或重新 db:schema',
    });
  }
  if (code === 'ECONNREFUSED' || code === 'ENOTFOUND') {
    return res.status(503).json({ error: '无法连接数据库，请检查 MySQL 是否已启动' });
  }
  return res.status(500).json({ error: fallback });
}

itemCatalogRouter.get(
  '/item-catalog',
  wrapAsync(async (req, res) => {
    const userId = req.user.id;
    const all = req.query.all === '1' || req.query.all === 'true';
    const panel = req.query.panel;

    let sql = `SELECT id, name, image_url AS imageUrl, price_w AS priceW, level_label AS levelLabel, description, panel, sort_order AS sortOrder FROM ${TABLE} WHERE user_id = ?`;
    const params = [userId];
    if (panel && typeof panel === 'string' && PANELS.includes(panel)) {
      sql += ' AND panel = ?';
      params.push(panel);
    }
    sql += ' ORDER BY panel, sort_order ASC, id ASC';
    const [rows] = await pool.query(sql, params);

    if (all) {
      const panels = Object.fromEntries(PANELS.map((p) => [p, []]));
      for (const r of rows) {
        if (panels[r.panel]) panels[r.panel].push(r);
      }
      return res.json({ panels });
    }
    res.json(rows);
  }, '加载物品库失败')
);

itemCatalogRouter.post('/item-catalog', wrapAsync(async (req, res) => {
    const userId = req.user.id;
    const { name, imageUrl, priceW, levelLabel, description, panel, sortOrder } = req.body || {};
    if (!name || typeof name !== 'string') {
      return res.status(400).json({ error: '名称必填' });
    }
    const p = PANELS.includes(panel) ? panel : 'fixed';
    const img = typeof imageUrl === 'string' ? imageUrl.slice(0, 512) : '';
    const price = Number(priceW);
    const lvl = typeof levelLabel === 'string' ? levelLabel.slice(0, 64) : '';
    const desc = typeof description === 'string' ? description.slice(0, 600) : '';
    const sort = Number.isFinite(Number(sortOrder)) ? Number(sortOrder) : 0;

    const [r] = await pool.query(
      `INSERT INTO ${TABLE} (user_id, name, image_url, price_w, level_label, description, panel, sort_order)
       VALUES (?,?,?,?,?,?,?,?)`,
      [userId, name.slice(0, 128), img, Number.isFinite(price) ? price : 0, lvl, desc, p, sort]
    );
    const id = r.insertId;
    const [[row]] = await pool.query(
      `SELECT id, name, image_url AS imageUrl, price_w AS priceW, level_label AS levelLabel, description, panel, sort_order AS sortOrder FROM ${TABLE} WHERE id = ? AND user_id = ?`,
      [id, userId]
    );
    res.status(201).json(row);
}, '新增失败'));

itemCatalogRouter.patch('/item-catalog/:id', wrapAsync(async (req, res) => {
    const userId = req.user.id;
    const id = Number(req.params.id);
    if (!Number.isFinite(id)) return res.status(400).json({ error: '无效 id' });

    const fields = [];
    const params = [];
    const b = req.body || {};
    if (b.name !== undefined) {
      fields.push('name = ?');
      params.push(String(b.name).slice(0, 128));
    }
    if (b.imageUrl !== undefined) {
      fields.push('image_url = ?');
      params.push(String(b.imageUrl).slice(0, 512));
    }
    if (b.priceW !== undefined) {
      fields.push('price_w = ?');
      params.push(Number(b.priceW));
    }
    if (b.levelLabel !== undefined) {
      fields.push('level_label = ?');
      params.push(String(b.levelLabel).slice(0, 64));
    }
    if (b.description !== undefined) {
      fields.push('description = ?');
      params.push(String(b.description).slice(0, 600));
    }
    if (b.panel !== undefined && PANELS.includes(b.panel)) {
      fields.push('panel = ?');
      params.push(b.panel);
    }
    if (b.sortOrder !== undefined) {
      fields.push('sort_order = ?');
      params.push(Number(b.sortOrder));
    }
    if (!fields.length) return res.status(400).json({ error: '无更新字段' });

    params.push(id, userId);
    const [r] = await pool.query(
      `UPDATE ${TABLE} SET ${fields.join(', ')} WHERE id = ? AND user_id = ?`,
      params
    );
    if (r.affectedRows === 0) return res.status(404).json({ error: '未找到' });

    const [[row]] = await pool.query(
      `SELECT id, name, image_url AS imageUrl, price_w AS priceW, level_label AS levelLabel, description, panel, sort_order AS sortOrder FROM ${TABLE} WHERE id = ?`,
      [id]
    );
    res.json(row);
}, '保存失败'));

itemCatalogRouter.delete('/item-catalog/:id', wrapAsync(async (req, res) => {
    const userId = req.user.id;
    const id = Number(req.params.id);
    const [r] = await pool.query(`DELETE FROM ${TABLE} WHERE id = ? AND user_id = ?`, [id, userId]);
    if (r.affectedRows === 0) return res.status(404).json({ error: '未找到' });
    res.json({ ok: true });
}, '删除失败'));

itemCatalogRouter.post('/item-catalog/batch-delete', wrapAsync(async (req, res) => {
    const userId = req.user.id;
    const raw = req.body?.ids;
    if (!Array.isArray(raw) || raw.length === 0) {
      return res.status(400).json({ error: '请选择要删除的条目' });
    }
    const uniq = [...new Set(raw.map((x) => Number(x)).filter((n) => Number.isFinite(n) && n > 0))];
    if (uniq.length === 0) return res.status(400).json({ error: '无效的 id' });
    if (uniq.length > 500) return res.status(400).json({ error: '单次最多删除 500 条' });
    const ph = uniq.map(() => '?').join(',');
    const [r] = await pool.query(`DELETE FROM ${TABLE} WHERE user_id = ? AND id IN (${ph})`, [
      userId,
      ...uniq,
    ]);
    res.json({ ok: true, deleted: Number(r.affectedRows) || 0 });
}, '批量删除失败'));

itemCatalogRouter.post('/item-catalog/upload', (req, res, next) => {
  upload.single('file')(req, res, (err) => {
    if (err) return res.status(400).json({ error: err.message || '上传失败' });
    next();
  });
}, (req, res) => {
  if (!req.file) return res.status(400).json({ error: '缺少文件' });
  const url = `/uploads/catalog/${req.user.id}/${req.file.filename}`;
  res.json({ url });
});

itemCatalogRouter.post('/item-catalog/import-preset', wrapAsync(async (req, res) => {
    const userId = req.user.id;
    const replace = Boolean(req.body?.replace);
    const rows = getItemCatalogPresetRows();

    const conn = await pool.getConnection();
    try {
      await conn.beginTransaction();
      if (replace) {
        await conn.query(`DELETE FROM ${TABLE} WHERE user_id = ?`, [userId]);
      }
      for (const row of rows) {
        await conn.query(
          `INSERT INTO ${TABLE} (user_id, name, image_url, price_w, level_label, description, panel, sort_order)
           VALUES (?,?,?,?,?,?,?,?)`,
          [
            userId,
            row.name,
            row.imageUrl,
            row.priceW,
            row.levelLabel,
            row.description,
            row.panel,
            row.sortOrder,
          ]
        );
      }
      await conn.commit();
    } catch (e) {
      await conn.rollback();
      throw e;
    } finally {
      conn.release();
    }

    const [[{ cnt }]] = await pool.query(`SELECT COUNT(*) AS cnt FROM ${TABLE} WHERE user_id = ?`, [userId]);
    res.json({ ok: true, count: Number(cnt) || 0 });
}, '导入失败'));
