-- v2: 定时活动字段 + 智能记账（仅结构说明，实际迁移用 scripts/migrate-v2.js 幂等执行）

-- ALTER TABLE task_templates
--   ADD COLUMN schedule_weekdays VARCHAR(32) NULL COMMENT '0=周日..6=周六，逗号分隔' AFTER cooldown_days,
--   ADD COLUMN schedule_start TIME NULL AFTER schedule_weekdays,
--   ADD COLUMN schedule_end TIME NULL AFTER schedule_start,
--   ADD COLUMN schedule_pin_early_minutes INT UNSIGNED NOT NULL DEFAULT 30 AFTER schedule_end;
