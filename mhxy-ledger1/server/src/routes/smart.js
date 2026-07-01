import { Router } from 'express';
import multer from 'multer';
import { createWorker } from 'tesseract.js';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { todayStr } from '../utils/date.js';
import { parseLedgerText } from '../utils/parseLedgerText.js';

export const smartRouter = Router();
smartRouter.use(authRequired);

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 8 * 1024 * 1024 },
});

let ocrWorkerPromise = null;

async function getOcrWorker() {
  if (process.env.SMART_OCR_DISABLED === '1') return null;
  if (!ocrWorkerPromise) {
    ocrWorkerPromise = createWorker(['chi_sim', 'eng'], 1, {
      logger: () => {},
    });
  }
  return ocrWorkerPromise;
}

smartRouter.post('/parse', async (req, res) => {
  const text = String(req.body?.text || '').trim();
  if (!text) return res.status(400).json({ error: 'text 为空' });
  const [rows] = await pool.query('SELECT id, name FROM items ORDER BY CHAR_LENGTH(name) DESC');
  const actions = parseLedgerText(text, rows);
  res.json({ text, actions });
});

smartRouter.post('/ocr', upload.single('image'), async (req, res) => {
  if (!req.file?.buffer) return res.status(400).json({ error: '请上传图片 image 字段' });
  const worker = await getOcrWorker();
  if (!worker) {
    return res.status(503).json({ error: 'OCR 已禁用（SMART_OCR_DISABLED=1）' });
  }
  try {
    const {
      data: { text },
    } = await worker.recognize(req.file.buffer);
    const [rows] = await pool.query('SELECT id, name FROM items ORDER BY CHAR_LENGTH(name) DESC');
    const actions = parseLedgerText(text, rows);
    res.json({ ocrText: text, actions });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'OCR 识别失败，请换清晰截图或改用语音' });
  }
});

smartRouter.post('/apply', async (req, res) => {
  const bizDate = String(req.body?.bizDate || todayStr());
  const actions = Array.isArray(req.body?.actions) ? req.body.actions : [];
  if (!actions.length) return res.status(400).json({ error: 'actions 为空' });
  const uid = req.user.id;
  const results = [];

  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    for (const a of actions) {
      if (a.type === 'cash') {
        const amount = Number(a.amount);
        if (Number.isNaN(amount)) continue;
        const note = String(a.note || '智能录入').slice(0, 255);
        const [r] = await conn.query(
          'INSERT INTO cash_entries (user_id, biz_date, amount, note) VALUES (?,?,?,?)',
          [uid, bizDate, amount, note]
        );
        results.push({ type: 'cash', id: r.insertId, amount });
      } else if (a.type === 'points') {
        const points = Math.max(0, Number(a.points));
        if (Number.isNaN(points)) continue;
        const note = String(a.note || '智能录入').slice(0, 255);
        const [r] = await conn.query(
          'INSERT INTO point_card_entries (user_id, biz_date, points, note) VALUES (?,?,?,?)',
          [uid, bizDate, points, note]
        );
        results.push({ type: 'points', id: r.insertId, points });
      } else if (a.type === 'item') {
        const itemId = Number(a.itemId);
        const quantity = Math.max(1, Number(a.quantity || 1));
        if (!itemId) continue;
        const [r] = await conn.query(
          'INSERT INTO item_gains (user_id, biz_date, item_id, quantity) VALUES (?,?,?,?)',
          [uid, bizDate, itemId, quantity]
        );
        results.push({ type: 'item', id: r.insertId, itemId, quantity });
      }
    }
    await conn.commit();
  } catch (e) {
    await conn.rollback();
    console.error(e);
    return res.status(500).json({ error: '写入失败' });
  } finally {
    conn.release();
  }

  res.json({ bizDate, results });
});
