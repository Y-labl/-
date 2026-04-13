import path from 'path';
import dotenv from 'dotenv';
import mysql from 'mysql2/promise';

dotenv.config({ path: path.join(process.cwd(), '.env') });

const biz = process.argv[2] || '2026-04-11';

async function main() {
  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'mhxy_ledger',
  });
  const [rows] = await pool.query(
    `SELECT user_id, biz_date, online_roles, elapsed_sec, ledger_base_elapsed_sec, ledger_run_start_at_ms,
            point_card_points, team_principals_w, team_cash_game_gold_w, ledger_point_card_json, saved_at
     FROM mech_ledger_day_meta WHERE biz_date = ? ORDER BY user_id`,
    [biz],
  );
  console.log(JSON.stringify(rows, null, 2));
  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
