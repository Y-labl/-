import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

/** 梦幻日历限时活动（与任务页推荐合并；wukai_rank 越小越靠前，参考常见五开收益与攻略优先级） */
const ROWS = [
  ['tianjiangxingchen', '活动：天降星辰', '周一至周四晚间，五开高收益常备', '1,2,3,4', '20:00:00', '22:00:00', 30, 5, 3, 3, null],
  ['bangpai-zhuangyuan', '帮战相关：帮派迷宫', '周一三五+无帮战周周五日 20–22（实际开放以帮派/当周帮战为准）', '1,3,5,0', '20:00:00', '22:00:00', 30, 5, 4, 4, null],
  ['huangong-feizei', '活动：皇宫飞贼', '周一至周五，中午 12:00 至下午 14:00（即 12 点–下午 2 点；以游戏内为准）', '1,2,3,4,5', '12:00:00', '14:00:00', 20, 5, 5, 5, null],
  ['miaoshou-renxin', '活动：妙手仁心', '周一至周五下午', '1,2,3,4,5', '15:00:00', '17:30:00', 20, 4, 6, 6, null],
  ['tianxia-meishi', '活动：天下美食', '周一、周三晚间', '1,3', '19:00:00', '21:10:00', 25, 4, 7, 7, null],
  ['chenxin', '活动：慈心渡鬼', '周六上午', '6', '10:00:00', '11:30:00', 20, 5, 8, 8, null],
  ['jiangyao', '活动：降妖伏魔', '周六下午', '6', '15:00:00', '17:00:00', 30, 4, 9, 9, null],
  ['cal-wenyun', '活动：文韵墨香', '每月第二周周日 14:30–17:00', '0', '14:30:00', '17:00:00', 25, 5, 10, 10, 2],
  ['cal-caihong', '活动：彩虹争霸赛', '每月第三周周日（报名常以活动预告为准）', '0', '15:00:00', '17:00:00', 30, 5, 11, 11, 3],
  ['cal-yingxiong', '活动：英雄大会', '每月第四周周日（多场叠压，时段见游戏内）', '0', '13:00:00', '18:00:00', 35, 4, 12, 12, 4],
  ['menpai-sunday', '活动：门派闯关', '每月第一周周日', '0', '15:00:00', '17:00:00', 30, 5, 13, 13, 1],
  ['cal-xiaochang', '活动：校场演兵', '周二、周四晚间', '2,4', '19:00:00', '21:30:00', 25, 4, 14, 14, null],
  ['cal-chunse', '活动：春色满园', '周二下午', '2', '15:00:00', '17:00:00', 20, 4, 15, 15, null],
  ['cal-miaofa', '活动：妙法慧心', '周三下午', '3', '15:00:00', '17:00:00', 20, 4, 16, 16, null],
  ['cal-qiaoyou', '活动：巧诱妖灵', '周四下午', '4', '15:00:00', '17:30:00', 20, 4, 17, 17, null],
  ['cal-mita', '活动：秘塔探险', '周四下午', '4', '15:00:00', '17:00:00', 20, 4, 18, 18, null],
  ['cal-tianlai', '活动：天籁之音', '周五下午至晚间', '5', '16:00:00', '18:35:00', 25, 4, 19, 19, null],
  ['cal-xunmeng', '活动：寻梦追忆', '无帮战周周六晚间（开放以游戏内为准）', '6', '19:30:00', '21:30:00', 25, 4, 20, 20, null],
  ['cal-shequ', '活动：社区活动', '周六上午', '6', '10:30:00', '12:00:00', 20, 4, 21, 21, null],
  ['cal-jianzhi-huashan', '活动：剑指华山', '周六晚间（决战华山）', '6', '21:00:00', '22:00:00', 20, 4, 22, 22, null],
  ['cal-keju', '活动：科举大赛', '每月第二周周日（与文韵等同日不同玩法，以游戏内为准）', '0', '10:00:00', '18:00:00', 30, 4, 23, 23, 2],
  ['cal-changan', '活动：长安保卫战', '每月第五周周日（无第五周则当月无此场）', '0', '10:00:00', '22:00:00', 35, 4, 50, 50, 5],
];

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
    CREATE TABLE IF NOT EXISTS calendar_activities (
      id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      act_key VARCHAR(64) NOT NULL,
      name VARCHAR(128) NOT NULL,
      description VARCHAR(512) NOT NULL DEFAULT '',
      schedule_weekdays VARCHAR(32) NOT NULL DEFAULT '' COMMENT '0=周日..6=周六',
      schedule_start TIME NOT NULL,
      schedule_end TIME NOT NULL,
      pin_early_minutes INT UNSIGNED NOT NULL DEFAULT 30,
      stars TINYINT UNSIGNED NOT NULL DEFAULT 4,
      wukai_rank INT NOT NULL DEFAULT 50,
      sort_order INT NOT NULL DEFAULT 50,
      month_week TINYINT UNSIGNED NULL COMMENT '当月第几个周日；NULL=不按此规则',
      is_active TINYINT(1) NOT NULL DEFAULT 1,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY ux_cal_act_key (act_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `);

  const ph = ROWS.map(() => '(?,?,?,?,?,?,?,?,?,?,?,?)').join(',');
  const flat = ROWS.flatMap((r) => [...r, 1]);

  await conn.query(
    `INSERT INTO calendar_activities
      (act_key, name, description, schedule_weekdays, schedule_start, schedule_end,
       pin_early_minutes, stars, wukai_rank, sort_order, month_week, is_active)
     VALUES ${ph}
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
       is_active = VALUES(is_active)`,
    flat
  );

  await conn.end();
  console.log(`migrate-v16 done: calendar_activities seeded (${ROWS.length} rows).`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
