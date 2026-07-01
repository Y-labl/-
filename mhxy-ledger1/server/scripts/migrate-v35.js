import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * Add new dungeon templates to recommended list:
 * - 副本：秘境降妖
 * - 副本：猴王出世
 *
 * Both are treated as four_day (4 days refresh) like other dungeons.
 * Default enabled=1 so they show in 推荐榜.
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

  // Pick sort_order after existing four_day block (50..60, 54..58 already used by added dungeons)
  // Use 61,62 to keep stable ordering; users can override via manual_sort_order later.
  await conn.query(`
    INSERT INTO task_templates (name, description, frequency, sort_order, cooldown_days, enabled)
    SELECT * FROM (
      SELECT '副本：秘境降妖' AS name, '四天一刷副本（推荐榜可手动排序）' AS description, 'four_day' AS frequency, 61 AS sort_order, 4 AS cooldown_days, 1 AS enabled
      UNION ALL
      SELECT '副本：猴王出世' AS name, '四天一刷副本（推荐榜可手动排序）' AS description, 'four_day' AS frequency, 62 AS sort_order, 4 AS cooldown_days, 1 AS enabled
    ) x
    WHERE NOT EXISTS (SELECT 1 FROM task_templates t WHERE t.name = x.name LIMIT 1)
  `);

  await conn.end();
  console.log('migrate-v35 done: added dungeons 秘境降妖/猴王出世.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

