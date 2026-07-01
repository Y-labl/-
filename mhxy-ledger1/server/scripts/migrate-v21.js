import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * 皇宫飞贼：在 task_templates 上写入与日历一致的时段（日历未迁移/读失败时推荐榜仍有数据）。
 * 与「活动：皇宫飞贼」同名，便于与 calendar_activities 去重时只保留一条。
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

  const [rows] = await conn.query(
    'SELECT id FROM task_templates WHERE id = 12 OR name IN (?, ?) ORDER BY id LIMIT 1',
    ['日常：皇宫飞贼', '活动：皇宫飞贼']
  );
  const id = rows[0]?.id ?? 12;

  await conn.query(
    `UPDATE task_templates SET
       name = '活动：皇宫飞贼',
       description = '周一至周五，中午 12:00 至下午 14:00（即 12 点–下午 2 点；以游戏内为准）。',
       schedule_weekdays = '1,2,3,4,5',
       schedule_start = '12:00:00',
       schedule_end = '14:00:00',
       schedule_pin_early_minutes = 20
     WHERE id = ?`,
    [id]
  );

  await conn.end();
  console.log(`migrate-v21 done: task_templates id=${id} 已设为皇宫飞贼周一至周五 12:00–14:00。`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
