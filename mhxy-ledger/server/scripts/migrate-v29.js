import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * Copy/wording fixes:
 * - 4-day dungeons (19-23) should describe 4-day rotation.
 * - "维摩诘/九色鹿" are daily activities in naming (not "副本：").
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

  // Rename daily activities (keep weekly caps logic unchanged).
  await conn.query(`
    UPDATE task_templates
    SET name = '日常：维摩诘'
    WHERE id = 17
  `);
  await conn.query(`
    UPDATE task_templates
    SET name = '日常：九色鹿'
    WHERE id = 18
  `);

  // Fix 4-day rotation descriptions (ids 19-23).
  await conn.query(`
    UPDATE task_templates
    SET description = '普通副本，四天一轮节奏'
    WHERE id BETWEEN 19 AND 23
  `);

  await conn.end();
  console.log('migrate-v29 done: naming + description fixes.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

