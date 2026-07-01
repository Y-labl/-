import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column],
  );
  return rows.length > 0;
}

/**
 * Ensure new dungeons follow the same 4-day rotation as others:
 * - frequency=four_day, cooldown_days=4
 * - cycle_anchor_at seeded (when column exists) so countdown matches other dungeons
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
    WHERE name IN ('副本：秘境降妖', '副本：猴王出世')
  `);

  if (await columnExists(conn, database, 'task_templates', 'cycle_anchor_at')) {
    await conn.query(`
      UPDATE task_templates
      SET cycle_anchor_at = '2026-04-06 08:00:00'
      WHERE name IN ('副本：秘境降妖', '副本：猴王出世')
        AND frequency = 'four_day'
        AND cooldown_days = 4
        AND cycle_anchor_at IS NULL
    `);
  }

  await conn.end();
  console.log('migrate-v36 done: synced new dungeons to 4-day rotation + anchor.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

