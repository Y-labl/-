import { Router } from 'express';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';

export const catalogRouter = Router();
catalogRouter.use(authRequired);

catalogRouter.get('/categories', async (_req, res) => {
  const [rows] = await pool.query(
    'SELECT id, name, sort_order AS sortOrder FROM item_categories ORDER BY sort_order, id'
  );
  res.json(rows);
});

catalogRouter.get('/items', async (req, res) => {
  const categoryId = req.query.categoryId;
  let sql =
    'SELECT id, category_id AS categoryId, name, image_url AS imageUrl, sort_order AS sortOrder FROM items';
  const params = [];
  if (categoryId) {
    sql += ' WHERE category_id = ?';
    params.push(Number(categoryId));
  }
  sql += ' ORDER BY sort_order, id';
  const [rows] = await pool.query(sql, params);
  res.json(rows);
});
