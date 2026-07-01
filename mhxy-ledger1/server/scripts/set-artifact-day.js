/**
 * 写入 artifact_day_selected（所有用户同一 biz_date）。
 *
 * 用法：
 *   node scripts/set-artifact-day.js 忧思华光玉 黄金甲之谜
 *   node scripts/set-artifact-day.js 2026-04-11 黄金甲之谜 重铸黄金甲
 *
 * 未写日期时默认今天（服务器本地日历日）。
 * 起/转不必同剧情线；脚本只做与 API 相同的 [起名, 转名] 排序。
 */
import { pool } from '../src/db/pool.js';
import { normalizeArtifactDayPair } from '../src/utils/artifactDayPair.js';
import { todayStr } from '../src/utils/date.js';

async function main() {
  const args = process.argv.slice(2).filter(Boolean);
  let bizDate;
  let name1;
  let name2;
  if (args.length >= 3 && /^\d{4}-\d{2}-\d{2}$/.test(args[0])) {
    [bizDate, name1, name2] = args;
  } else if (args.length === 2) {
    bizDate = todayStr();
    [name1, name2] = args;
  } else {
    console.error(
      '用法: node scripts/set-artifact-day.js [YYYY-MM-DD] <神器名1> <神器名2>\n' +
        '示例: node scripts/set-artifact-day.js 忧思华光玉 黄金甲之谜',
    );
    process.exit(1);
  }

  const selected = normalizeArtifactDayPair([name1, name2]);
  if (selected.length !== 2) {
    console.error('规范化后不足 2 项:', selected);
    process.exit(1);
  }

  const [users] = await pool.query('SELECT id FROM users');
  if (!users.length) {
    console.log('users 表无账号，未写入。');
    await pool.end();
    return;
  }

  const json = JSON.stringify(selected);
  for (const u of users) {
    await pool.query(
      `INSERT INTO artifact_day_selected (user_id, biz_date, selected_json) VALUES (?,?,CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE selected_json = VALUES(selected_json), updated_at = CURRENT_TIMESTAMP`,
      [u.id, bizDate, json],
    );
  }

  console.log(`已写入 ${users.length} 个账号 ${bizDate}：${selected[0]}（起）+ ${selected[1]}（转）`);
  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
