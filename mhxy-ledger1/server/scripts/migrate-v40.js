import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * 月度「第 N 个周日」限时：与 wukai-activities-feed.json 对齐（门派闯关 / 科举 / 彩虹 / 英雄大会 / 长安保卫战）。
 * 英雄大会在库中仍为连续时段 13:30–18:00（中间空档以 JSON 多段 windows 为准）。
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

  const updates = [
    [
      'menpai-sunday',
      '活动：门派闯关',
      '每月第一周周日 15:00–17:00 开放（以游戏内为准）',
      '15:00:00',
      '17:00:00',
    ],
    [
      'cal-keju',
      '活动：科举大赛',
      '每月第二周周日 14:30–17:00 开放（以游戏内为准）',
      '14:30:00',
      '17:00:00',
    ],
    [
      'cal-caihong',
      '活动：彩虹争霸赛',
      '每月第三周周日 15:00–17:00 开放（以游戏内为准）',
      '15:00:00',
      '17:00:00',
    ],
    [
      'cal-yingxiong',
      '活动：英雄大会',
      '每月第四周周日：比武 13:30–15:30、16:00–18:00（以游戏内为准；库内为连续 13:30–18:00）',
      '13:30:00',
      '18:00:00',
    ],
    [
      'cal-changan',
      '活动：长安保卫战',
      '每月第五周周日 14:00–16:00 开放（当月无第五周则不开放；以游戏内为准）',
      '14:00:00',
      '16:00:00',
    ],
  ];

  for (const [actKey, name, description, scheduleStart, scheduleEnd] of updates) {
    const [r] = await conn.query(
      `UPDATE calendar_activities
       SET name = ?, description = ?, schedule_start = ?, schedule_end = ?
       WHERE act_key = ?`,
      [name, description, scheduleStart, scheduleEnd, actKey],
    );
    console.log(`migrate-v40: ${actKey} rows=${r.affectedRows}`);
  }

  await conn.end();
  console.log('migrate-v40 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
