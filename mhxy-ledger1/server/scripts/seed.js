import path from 'path';
import mysql from 'mysql2/promise';
import bcrypt from 'bcryptjs';
import dotenv from 'dotenv';
import { getItemCatalogPresetRows } from '../src/data/itemCatalogPreset.js';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function main() {
  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'mhxy_ledger',
    waitForConnections: true,
    connectionLimit: 4,
  });

  const hash = bcrypt.hashSync('12345678', 10);
  await pool.query(
    `INSERT INTO users (username, password_hash) VALUES (?, ?)
     ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)`,
    ['demo', hash]
  );

  const [[demoUser]] = await pool.query('SELECT id FROM users WHERE username = ? LIMIT 1', ['demo']);
  const demoId = demoUser?.id;

  const [nameRows] = await pool.query(
    `SELECT TABLE_NAME AS n FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN ('catalog_items', 'mech_catalog_items')`
  );
  const tableName =
    nameRows.find((r) => r.n === 'catalog_items')?.n ||
    nameRows.find((r) => r.n === 'mech_catalog_items')?.n;

  if (demoId && tableName) {
    const [[{ cnt }]] = await pool.query(
      `SELECT COUNT(*) AS cnt FROM \`${tableName}\` WHERE user_id = ?`,
      [demoId]
    );
    const n = Number(cnt) || 0;
    if (n > 0) {
      console.log(
        `物品库：demo 账号已有 ${n} 条记录，跳过预设导入（避免 npm run db:seed 覆盖你已维护的名称与价格）。`
      );
      console.log('若需强行恢复内置模板，请在网页「物品库」使用「导入预设（覆盖）」。');
    } else {
      const preset = getItemCatalogPresetRows();
      const placeholders = preset.map(() => '(?,?,?,?,?,?,?,?)').join(',');
      const flat = preset.flatMap((row) => [
        demoId,
        row.name,
        row.imageUrl,
        row.priceW,
        row.levelLabel,
        row.description,
        row.panel,
        row.sortOrder,
      ]);
      await pool.query(
        `INSERT INTO \`${tableName}\`
          (user_id, name, image_url, price_w, level_label, description, panel, sort_order)
         VALUES ${placeholders}`,
        flat
      );
      console.log(`物品库：已为 demo 录入 ${preset.length} 条预设。`);
    }
  } else if (!tableName) {
    console.log('物品库：表不存在，已跳过。请先执行 npm run db:migrate-v5 或 npm run db:schema');
  }

  await pool.end();
  console.log('Demo user ready: demo / 12345678');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
