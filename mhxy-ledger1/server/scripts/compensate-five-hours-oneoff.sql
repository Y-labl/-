-- 一次性补偿：在「今天」的 mech_ledger_day_meta 上为某用户 +5 小时在线时长。
-- 请在「与记账台 API 实际连接」的 MySQL 上执行；把下面的 YOUR_USER_ID、'YYYY-MM-DD' 改成你的。
-- 只执行其中一段（跑表中 / 已停表），不要两段都跑。
-- 以后不必再执行；这不是定时任务。

-- ========== A) 当前正在计时（ledger_run_start_at_ms 非空）==========
-- 原理：把开始时刻往前拨 5 小时，总时长 +5h，且不会被 save-meta 用 base=0 盖掉。
/*
UPDATE mech_ledger_day_meta
SET
  ledger_run_start_at_ms = GREATEST(1, ledger_run_start_at_ms - 18000000),
  elapsed_sec = LEAST(86400000, COALESCE(elapsed_sec, 0) + 18000)
WHERE user_id = YOUR_USER_ID
  AND biz_date = '2026-04-11'
  AND ledger_run_start_at_ms IS NOT NULL;
*/

-- ========== B) 当前已停表（ledger_run_start_at_ms 为空）==========
/*
UPDATE mech_ledger_day_meta
SET
  ledger_base_elapsed_sec = LEAST(86400000, COALESCE(ledger_base_elapsed_sec, 0) + 18000),
  elapsed_sec = LEAST(86400000, COALESCE(elapsed_sec, 0) + 18000)
WHERE user_id = YOUR_USER_ID
  AND biz_date = '2026-04-11'
  AND ledger_run_start_at_ms IS NULL;
*/

-- 执行后可在记账台强制刷新（Ctrl+F5）。若仍不变，说明连的不是这台库。
