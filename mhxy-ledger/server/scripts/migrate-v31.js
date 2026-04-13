import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function columnExists(conn, database, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [database, table, column]
  );
  return rows.length > 0;
}

/**
 * Persist 4-day cycle anchor for dungeons so refresh countdown survives restarts.
 *
 * - Add task_templates.cycle_anchor_at (DATETIME, local wall clock)
 * - Seed anchor for 4-day dungeons (cooldown_days=4): 2026-04-06 08:00:00
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

  if (!(await columnExists(conn, database, 'task_templates', 'cycle_anchor_at'))) {
    await conn.query(`
      ALTER TABLE task_templates
      ADD COLUMN cycle_anchor_at DATETIME NULL
      COMMENT 'Fixed rotation anchor (local). Used by four_day refresh countdown.'
      AFTER cooldown_days
    `);
    console.log('Added task_templates.cycle_anchor_at.');
  } else {
    console.log('cycle_anchor_at already exists, skip ALTER.');
  }

  // Only seed when empty; allow manual overrides later.
  await conn.query(`
    UPDATE task_templates
    SET cycle_anchor_at = '2026-04-06 08:00:00'
    WHERE frequency = 'four_day'
      AND cooldown_days = 4
      AND cycle_anchor_at IS NULL
  `);

  await conn.end();
  console.log('migrate-v31 done: seeded cycle_anchor_at for four_day (4d) templates.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

