import jwt from 'jsonwebtoken';

export function authRequired(req, res, next) {
  const h = req.headers.authorization || '';
  const m = h.match(/^Bearer\s+(.+)$/i);
  if (!m) return res.status(401).json({ error: '未登录' });
  try {
    const payload = jwt.verify(m[1], process.env.JWT_SECRET || 'dev');
    req.user = { id: payload.sub, username: payload.username };
    next();
  } catch {
    return res.status(401).json({ error: '登录已失效' });
  }
}
