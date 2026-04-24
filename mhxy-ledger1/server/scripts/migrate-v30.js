import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * Fix schedule for 帮派迷宫:
 * - Only Mon(1) and Thu(4), not every day / not Mon-Thu.
 * This updates task_templates row used by 推荐榜 when calendar_activities is absent.
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

  const [res] = await conn.query(
    `UPDATE task_templates
     SET schedule_weekdays = '1,4',
         description = '周一、周四 20:00–22:00（以游戏内为准）'
     WHERE id = 14`
  );
  // mysql2 returns ResultSetHeader for UPDATE
  // eslint-disable-next-line no-console
  console.log('affectedRows:', res?.affectedRows, 'changedRows:', res?.changedRows);

  await conn.end();
  console.log('migrate-v30 done: 帮派迷宫 set to Mon+Thu.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

