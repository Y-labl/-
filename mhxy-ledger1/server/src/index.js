import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import { authRouter } from './routes/auth.js';
import { catalogRouter } from './routes/catalog.js';
import { ledgerRouter } from './routes/ledger.js';
import { tasksRouter } from './routes/tasks.js';
import { statsRouter } from './routes/stats.js';
import { smartRouter } from './routes/smart.js';
import { itemCatalogRouter } from './routes/itemCatalog.js';
import { artifactsRouter } from './routes/artifacts.js';
import { userClientPrefsRouter } from './routes/userClientPrefs.js';
import { authRequired } from './middleware/auth.js';
import { pool } from './db/pool.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const serverRoot = path.join(__dirname, '..');
dotenv.config({ path: path.join(serverRoot, '.env') });

/** 启动前幂等补列；失败则退出。设 SKIP_DB_AUTO_MIGRATE=1 可跳过 */
function runStartupMigrations() {
  if (String(process.env.SKIP_DB_AUTO_MIGRATE || '').trim() === '1') {
    console.log('[mhxy-server] SKIP_DB_AUTO_MIGRATE=1，已跳过启动迁移');
    return;
  }
  for (const script of ['migrate-v43.js', 'migrate-v44.js', 'migrate-v45.js']) {
    const r = spawnSync(process.execPath, [`scripts/${script}`], {
      cwd: serverRoot,
      stdio: 'inherit',
      env: process.env,
    });
    if (r.status !== 0) {
      console.error(`[mhxy-server] ${script} 失败；或临时设置 SKIP_DB_AUTO_MIGRATE=1`);
      process.exit(1);
    }
  }
}
runStartupMigrations();

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

app.get('/api/health', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ ok: true, db: true });
  } catch (e) {
    res.status(500).json({ ok: false, db: false });
  }
});

app.use('/api/auth', authRouter);

app.get('/api/me', authRequired, async (req, res) => {
  res.json({ user: { id: req.user.id, username: req.user.username } });
});

app.use('/api', userClientPrefsRouter);
app.use('/api', catalogRouter);
app.use('/api', itemCatalogRouter);
app.use('/api', ledgerRouter);
app.use('/api/tasks', tasksRouter);
app.use('/api/stats', statsRouter);
app.use('/api/smart', smartRouter);
app.use('/api/artifacts', artifactsRouter);

app.use((err, req, res, next) => {
  if (res.headersSent) return next(err);
  if (String(req.originalUrl || '').startsWith('/api')) {
    console.error('[api]', err);
    return res.status(500).json({ error: err?.message || '服务器错误' });
  }
  next(err);
});

const port = Number(process.env.PORT || 3001);
/** 默认 0.0.0.0 便于局域网访问；仅本机可设 HOST=127.0.0.1 */
const host = String(process.env.HOST || '0.0.0.0').trim() || '0.0.0.0';
const server = app.listen(port, host, () => {
  console.log(`MHXY Ledger API http://127.0.0.1:${port}（本机）`);
  if (host === '0.0.0.0' || host === '::') {
    console.log(`MHXY Ledger API 局域网：请用本机 IP 访问，例如 http://<本机局域网IP>:${port}`);
  }
});

server.on('error', (err) => {
  const code = err && err.code;
  if (code === 'EADDRINUSE') {
    console.error(`[mhxy-server] Port ${port} already in use (another API is running).`);
    console.error(
      '[mhxy-server] Close other "mhxy-ledger-server" cmd windows, or end duplicate node.exe, then start again.',
    );
  } else {
    console.error('[mhxy-server] Listen error:', err);
  }
  process.exit(1);
});
