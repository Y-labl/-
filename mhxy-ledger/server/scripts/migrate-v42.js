import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * task_templates id=13「活动：门派闯关」来自 migrate-v2：仅周日、无「每月第几个周日」，
 * 会在每个周日进入推荐榜；与 calendar_activities / feed（仅第 1 个周日）重复且口径错误。
 * 停用后仅走月历；补录仍可通过 live 条目操作。
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

  const [r] = await conn.query(
    `UPDATE task_templates
     SET enabled = 0
     WHERE id = 13 AND name = '活动：门派闯关'`,
  );
  console.log(`migrate-v42: task_templates id=13 affectedRows=${r.affectedRows}`);

  await conn.end();
  console.log('migrate-v42 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
