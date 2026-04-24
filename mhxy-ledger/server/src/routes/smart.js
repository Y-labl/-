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
let ocrChiSimReady = false;

function cjkCharCount(s) {
  const m = String(s || '').match(/[\u4e00-\u9fff]/g);
  return m ? m.length : 0;
}

function scoreOcrText(s) {
  const t = String(s || '');
  const cjk = cjkCharCount(t);
  const hasQiZhuan = /起\s*[:：]/.test(t) && /转\s*[:：]/.test(t);
  const hasAsciiSpam = /[A-Za-z]{3,}/.test(t);
  // Prefer: has 起/转 + more CJK. Penalize ASCII spam.
  return (hasQiZhuan ? 1000 : 0) + cjk - (hasAsciiSpam ? 10 : 0);
}

async function getOcrWorker() {
  if (process.env.SMART_OCR_DISABLED === '1') return null;
  if (!ocrWorkerPromise) {
    ocrWorkerPromise = (async () => {
      // NOTE: our installed tesseract.js expects signature:
      //   createWorker(langs?, oem?, options?, config?)
      // so the first argument must be language(s), not an options object.
      //
      // IMPORTANT: do NOT pass function values (e.g. logger callback) into createWorker in Node worker_threads;
      // Node's structuredClone cannot clone functions and will crash with DataCloneError.
      const langPath =
        (process.env.SMART_OCR_LANG_PATH || '').trim() ||
        // Default public tessdata mirror (requires outbound internet).
        'https://tessdata.projectnaptha.com/4.0.0';

      // Prefer Chinese simplified; if chi_sim cannot be loaded, we will surface a clear error.
      let worker;
      try {
        worker = await createWorker('chi_sim', undefined, { langPath });
        ocrChiSimReady = true;
      } catch {
        ocrChiSimReady = false;
        // Still return worker so /ocr can respond with a helpful message instead of gibberish.
        try {
          worker = await createWorker('eng', undefined, { langPath });
        } catch {
          /* ignore */
        }
      }
      // Some UI screenshots are tiny; nudge DPI.
      if (typeof worker.setParameters === 'function') {
        await worker.setParameters({ user_defined_dpi: '300' });
      }
      return worker;
    })();
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
  if (!ocrChiSimReady) {
    return res.status(503).json({
      error:
        'OCR 中文语言包 chi_sim 未能加载，当前会退回英文识别导致乱码。请确保服务器可联网下载 tessdata，或设置环境变量 SMART_OCR_LANG_PATH 指向可用的 tessdata 路径/URL（含 chi_sim.traineddata）。',
    });
  }
  try {
    // Two-pass OCR with different page segmentation modes (PSM):
    // - 6: Assume a block of text (good default for UI panels)
    // - 7: Single text line (sometimes better for short "起:xxx 转:yyy" snippets)
    let text1 = '';
    let text2 = '';
    try {
      await worker.setParameters({ tessedit_pageseg_mode: '6', preserve_interword_spaces: '1' });
      const r1 = await worker.recognize(req.file.buffer);
      text1 = r1?.data?.text ?? '';
    } catch {
      text1 = '';
    }
    try {
      await worker.setParameters({ tessedit_pageseg_mode: '7', preserve_interword_spaces: '1' });
      const r2 = await worker.recognize(req.file.buffer);
      text2 = r2?.data?.text ?? '';
    } catch {
      text2 = '';
    }
    const text = scoreOcrText(text2) > scoreOcrText(text1) ? text2 : text1;
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
