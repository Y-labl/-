import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/**
 * 双龙之战：每日神器争夺、周间竞技/护卫、每月第二周六大决战
 * （细分阶段见 description，以当周维护/游戏内为准）
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

  await conn.query(
    `UPDATE calendar_activities SET
       name = '活动：双龙之战·每月大决战',
       description = '跨服阵营大决战；每月第二周周六 14:00–17:00（报名/前哨环节见维护公告）。'
     WHERE act_key = 'cal-shuanglong'`
  );

  await conn.query(
    `INSERT INTO calendar_activities
      (act_key, name, description, schedule_weekdays, schedule_start, schedule_end,
       pin_early_minutes, stars, wukai_rank, sort_order, month_week, month_anchor_weekday, is_active)
     VALUES
       ('cal-shuanglong-shenqi-daily', '活动：双龙之战·神器争夺战（每日）',
        '每晚神器争夺：22:00–23:30（乱流来客、碎片争夺等阶段以游戏内为准）。',
        '0,1,2,3,4,5,6', '22:00:00', '23:30:00', 25, 5, 21, 21, NULL, NULL, 1),
       ('cal-shuanglong-huwei', '活动：双龙之战·护卫巨兽',
        '每周 18:00–19:00 护卫巨兽玩法。开放星期以游戏内为准，此处按周一至周四与周间竞技同期占位。',
        '1,2,3,4', '18:00:00', '19:00:00', 20, 4, 22, 22, NULL, NULL, 1),
       ('cal-shuanglong-jingji', '活动：双龙之战·竞技对战（周一至周四）',
        '周间 19:15–22:00 竞技对战场次，以游戏内匹配与公告为准。',
        '1,2,3,4', '19:15:00', '22:00:00', 25, 4, 23, 23, NULL, NULL, 1)
     ON DUPLICATE KEY UPDATE
       name = VALUES(name),
       description = VALUES(description),
       schedule_weekdays = VALUES(schedule_weekdays),
       schedule_start = VALUES(schedule_start),
       schedule_end = VALUES(schedule_end),
       pin_early_minutes = VALUES(pin_early_minutes),
       stars = VALUES(stars),
       wukai_rank = VALUES(wukai_rank),
       sort_order = VALUES(sort_order),
       month_week = VALUES(month_week),
       month_anchor_weekday = VALUES(month_anchor_weekday),
       is_active = VALUES(is_active)`
  );

  await conn.end();
  console.log('migrate-v19 done: 双龙之战 每日/周间/月度 已写入 calendar_activities。');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
