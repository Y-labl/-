import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function tableExists(conn, db, name) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1`,
    [db, name]
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
    console.log('task_templates missing, skip migrate-v14.');
    await conn.end();
    return;
  }

  await conn.query('UPDATE task_done_entries SET task_id = NULL WHERE task_id = 3');
  if (await tableExists(conn, database, 'task_completions')) {
    await conn.query('DELETE FROM task_completions WHERE task_id = 3');
  }
  await conn.query('DELETE FROM task_templates WHERE id = 3');

  await conn.query(`
    UPDATE task_templates SET
      name = '抓鬼 · 鬼王',
      description = '钟馗日常 + 黑无常鬼王，五开一条就够，勿重复勾选'
    WHERE id = 2
  `);

  await conn.query(`UPDATE task_templates SET name = '天命：大闹天宫', description = '附魔宝珠等高价值，五开优先清', sort_order = 50, frequency = 'four_day', cooldown_days = 4 WHERE id = 5`);
  await conn.query(`UPDATE task_templates SET name = '天命：金兜洞', description = '现金、物品均衡，轮换必刷', sort_order = 51, frequency = 'four_day', cooldown_days = 4 WHERE id = 6`);
  await conn.query(`UPDATE task_templates SET name = '天命：乌鸡国', description = '流程短、性价比高', sort_order = 52, frequency = 'four_day', cooldown_days = 4 WHERE id = 7`);
  await conn.query(`UPDATE task_templates SET name = '天命：齐天大圣', description = '天命轮换位，按周期补齐', sort_order = 53, frequency = 'four_day', cooldown_days = 4 WHERE id = 8`);
  await conn.query(`UPDATE task_templates SET name = '侠士天命：通天河', description = '周期长，附魔期望高', sort_order = 60, frequency = 'four_day', cooldown_days = 7 WHERE id = 9`);

  const [dups] = await conn.query(
    `SELECT id FROM task_templates WHERE name IN ('日常抓鬼', '天命副本', '副本：天命')`
  );
  for (const row of dups) {
    const id = row.id;
    await conn.query('UPDATE task_done_entries SET task_id = NULL WHERE task_id = ?', [id]);
    if (await tableExists(conn, database, 'task_completions')) {
      await conn.query('DELETE FROM task_completions WHERE task_id = ?', [id]);
    }
    await conn.query('DELETE FROM task_templates WHERE id = ?', [id]);
  }

  await conn.end();
  console.log('migrate-v14 done: 移除运镖、天命按本拆分、抓鬼合并为一条、删概括/重复模板。');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
