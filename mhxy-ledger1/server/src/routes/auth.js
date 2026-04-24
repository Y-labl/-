import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { pool } from '../db/pool.js';

export const authRouter = Router();

authRouter.post('/register', async (req, res) => {
  const username = String(req.body?.username || '').trim();
  const password = String(req.body?.password || '');
  if (username.length < 2 || username.length > 32) {
    return res.status(400).json({ error: '用户名长度 2–32' });
  }
  if (password.length < 6) return res.status(400).json({ error: '密码至少 6 位' });
  try {
    const hash = bcrypt.hashSync(password, 10);
    const [r] = await pool.query(
      'INSERT INTO users (username, password_hash) VALUES (?, ?)',
      [username, hash]
    );
    const token = signToken(r.insertId, username);
    return res.json({ token, user: { id: r.insertId, username } });
  } catch (e) {
    if (e.code === 'ER_DUP_ENTRY') {
      return res.status(409).json({ error: '用户名已存在' });
    }
    console.error(e);
    return res.status(500).json({ error: '注册失败' });
  }
});

authRouter.post('/login', async (req, res) => {
  const username = String(req.body?.username || '').trim();
  const password = String(req.body?.password || '');
  try {
    const [rows] = await pool.query('SELECT id, password_hash FROM users WHERE username = ?', [
      username,
    ]);
    const row = rows[0];
    if (!row?.password_hash) {
      return res.status(401).json({ error: '账号或密码错误' });
    }
    let match = false;
    try {
      match = bcrypt.compareSync(password, row.password_hash);
    } catch {
      match = false;
    }
    if (!match) {
      return res.status(401).json({ error: '账号或密码错误' });
    }
    const token = signToken(row.id, username);
    return res.json({ token, user: { id: row.id, username } });
  } catch (e) {
    console.error('[auth/login]', e);
    const msg =
      e && typeof e === 'object' && 'code' in e && e.code === 'ECONNREFUSED'
        ? '无法连接数据库，请确认 MySQL 已启动且 .env 配置正确'
        : e && typeof e === 'object' && 'code' in e && String(e.code).startsWith('ER_')
          ? '数据库异常，请检查库 mhxy_ledger 是否已初始化（npm run db:schema / db:seed）'
          : '登录服务暂时不可用，请稍后重试';
    return res.status(503).json({ error: msg });
  }
});

function signToken(id, username) {
  return jwt.sign(
    { sub: String(id), username },
    process.env.JWT_SECRET || 'dev',
    { expiresIn: '30d' }
  );
}
