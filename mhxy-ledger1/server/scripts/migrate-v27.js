import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * Add weekly dungeon templates to task_templates so they show up in 推荐榜（日常/周常段）。
 * 周常周期以「周一」为起点（与推荐榜 week 统计一致）。
 */
async function main() {
  const database = process.env.MYSQL_DATABASE || 'mhxy_ledger';
  const conn = await mysql.createConnection({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    multipleStatements: true,
  });
  await conn.query(`USE \`${database}\``);

  await conn.query(`
    INSERT IGNORE INTO task_templates
      (id, name, description, frequency, sort_order, cooldown_days)
    VALUES
      (19, '副本：大闹天宫', '每周一次；周一重置。', 'weekly_once', 45, 7),
      (20, '副本：黑风山', '每周一次；周一重置。', 'weekly_once', 46, 7),
      (21, '副本：七绝山', '每周一次；周一重置。', 'weekly_once', 47, 7),
      (22, '副本：石猴授徒', '每周一次；周一重置。', 'weekly_once', 48, 7),
      (23, '副本：红孩儿', '每周一次；周一重置。', 'weekly_once', 49, 7)
  `);

  await conn.end();
  console.log('migrate-v27 done: added weekly dungeons templates (19-23).');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

