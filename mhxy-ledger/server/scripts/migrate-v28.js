import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * Fix frequency for newly added dungeons:
 * - They should rotate every 4 days (four_day, cooldown 4), not weekly.
 * - Place them after existing four_day dungeons (sort_order 54..58).
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
    UPDATE task_templates
    SET frequency = 'four_day', cooldown_days = 4
    WHERE id BETWEEN 19 AND 23
  `);

  await conn.query(`
    UPDATE task_templates SET sort_order = 54 WHERE id = 19;
    UPDATE task_templates SET sort_order = 55 WHERE id = 20;
    UPDATE task_templates SET sort_order = 56 WHERE id = 21;
    UPDATE task_templates SET sort_order = 57 WHERE id = 22;
    UPDATE task_templates SET sort_order = 58 WHERE id = 23;
  `);

  await conn.end();
  console.log('migrate-v28 done: tasks 19-23 set to four_day (cooldown 4) + sort 54..58.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

