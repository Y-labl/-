import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function tableExists(conn, database, table) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1`,
    [database, table],
  );
  return rows.length > 0;
}

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

  if (!(await tableExists(conn, database, 'task_templates'))) {
    console.log('task_templates missing, skip.');
    await conn.end();
    return;
  }

  // Insert if not exists by name (no unique constraint).
  const templates = [
    {
      name: '副本：九色鹿',
      description: '周常副本：每周可刷 2 次（周一早上 08:00 重置次数）',
      frequency: 'weekly_twice',
      sortOrder: 70,
      cooldownDays: 7,
    },
    {
      name: '副本：维摩诘',
      description: '周常副本：每周可刷 1 次（周一早上 08:00 重置次数）',
      frequency: 'weekly_once',
      sortOrder: 71,
      cooldownDays: 7,
    },
  ];

  for (const t of templates) {
    const [rows] = await conn.query('SELECT id FROM task_templates WHERE name = ? LIMIT 1', [t.name]);
    if (rows.length) {
      console.log(`task_templates: exists "${t.name}", skip.`);
      continue;
    }
    await conn.query(
      `INSERT INTO task_templates (name, description, frequency, sort_order, cooldown_days, enabled)
       VALUES (?,?,?,?,?,1)`,
      [t.name, t.description, t.frequency, t.sortOrder, t.cooldownDays],
    );
    console.log(`task_templates: inserted "${t.name}".`);
  }

  await conn.end();
  console.log('migrate-v46 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

