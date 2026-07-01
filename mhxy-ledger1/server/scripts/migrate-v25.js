import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/** 维摩诘：每周 1 次；九色鹿：每周 2 次；周一为周期起点（与推荐榜 week 一致） */
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
    ALTER TABLE task_templates
    MODIFY COLUMN frequency ENUM('daily','four_day','weekly_once','weekly_twice')
    NOT NULL DEFAULT 'daily'
  `);
  console.log('task_templates.frequency extended with weekly_once / weekly_twice.');

  await conn.query(`
    INSERT IGNORE INTO task_templates
      (id, name, description, frequency, sort_order, cooldown_days)
    VALUES
      (17, '副本：维摩诘', '每周一次；周一重置次数，用完当周次日从推荐榜隐藏；完成当日在榜尾显示已完成。', 'weekly_once', 43, 7),
      (18, '副本：九色鹿', '每周两次；周一重置；刷一次后显示剩余次数，两次均完成则次日从推荐榜移除，完成当日显示已完成。', 'weekly_twice', 44, 7)
  `);

  await conn.end();
  console.log('migrate-v25 done: 维摩诘 / 九色鹿 模板（id 17 / 18）。');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
