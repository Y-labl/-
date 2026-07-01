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
 * task_templates:
 * - enabled: 1=在推荐榜展示；0=移到补录页
 * - manual_sort_order: 手动排序（越小越靠前）；NULL 则回退 sort_order
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

  if (!(await columnExists(conn, database, 'task_templates', 'enabled'))) {
    await conn.query(`
      ALTER TABLE task_templates
      ADD COLUMN enabled TINYINT(1) NOT NULL DEFAULT 1
      COMMENT '1=show in recommended list; 0=hidden (backfill only)'
      AFTER sort_order
    `);
    console.log('Added task_templates.enabled.');
  } else {
    console.log('enabled already exists, skip.');
  }

  if (!(await columnExists(conn, database, 'task_templates', 'manual_sort_order'))) {
    await conn.query(`
      ALTER TABLE task_templates
      ADD COLUMN manual_sort_order INT NULL
      COMMENT 'Manual ordering for recommended list; lower comes first.'
      AFTER enabled
    `);
    console.log('Added task_templates.manual_sort_order.');
  } else {
    console.log('manual_sort_order already exists, skip.');
  }

  await conn.end();
  console.log('migrate-v34 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

