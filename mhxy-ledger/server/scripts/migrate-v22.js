import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/** 神器在同一玩法下分「起」「转」两条独立日常模板 */
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
    UPDATE task_templates SET
      name = '日常：神器任务（起）',
      description = '新起神器任务线；与「转」为两条独立日常。'
    WHERE id = 4
  `);

  await conn.query(`
    INSERT IGNORE INTO task_templates
      (id, name, description, frequency, sort_order, cooldown_days)
    VALUES
      (16, '日常：神器任务（转）', '已起神器后的转换、洗炼等；与「起」为两条独立日常。', 'daily', 41, 1)
  `);

  await conn.query(`
    UPDATE task_templates SET
      name = '日常：神器任务（转）',
      description = '已起神器后的转换、洗炼等；与「起」为两条独立日常。'
    WHERE id = 16
  `);

  await conn.end();
  console.log('migrate-v22 done: 神器任务已固定为「起」「转」两条模板（id 4 / 16）。');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
