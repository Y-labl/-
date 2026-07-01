-- MHXY Ledger v1 schema
USE mhxy_ledger;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS item_categories (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS items (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  category_id INT UNSIGNED NOT NULL,
  name VARCHAR(128) NOT NULL,
  image_url VARCHAR(512) NOT NULL DEFAULT '',
  sort_order INT NOT NULL DEFAULT 0,
  CONSTRAINT fk_items_cat FOREIGN KEY (category_id) REFERENCES item_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS item_gains (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  item_id INT UNSIGNED NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_gains_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_gains_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
  KEY idx_gains_user_date (user_id, biz_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cash_entries (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  amount DECIMAL(14,2) NOT NULL,
  note VARCHAR(255) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cash_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_cash_user_date (user_id, biz_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS point_card_entries (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  points INT NOT NULL,
  note VARCHAR(255) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_point_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_point_user_date (user_id, biz_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS consumption_characters (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  character_name VARCHAR(64) NOT NULL,
  level_label VARCHAR(32) NOT NULL DEFAULT '',
  sect VARCHAR(32) NOT NULL DEFAULT '',
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY ux_cc_user_name (user_id, character_name),
  KEY idx_cc_user_sort (user_id, sort_order, id),
  CONSTRAINT fk_cc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS consumption_entries (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  character_id BIGINT UNSIGNED NULL,
  biz_date DATE NOT NULL,
  character_name VARCHAR(64) NOT NULL DEFAULT '',
  level_label VARCHAR(32) NOT NULL DEFAULT '',
  sect VARCHAR(32) NOT NULL DEFAULT '',
  rmb_amount DECIMAL(10,2) NOT NULL,
  game_coin_w DECIMAL(14,4) NOT NULL DEFAULT 0 COMMENT '游戏币消耗（万）',
  note VARCHAR(255) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_consumption_user_date (user_id, biz_date),
  CONSTRAINT fk_consumption_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_consumption_character FOREIGN KEY (character_id) REFERENCES consumption_characters(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS consumption_day_totals (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  character_id BIGINT UNSIGNED NOT NULL,
  rmb_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  dream_coin_w DECIMAL(14,4) NOT NULL DEFAULT 0 COMMENT '梦幻币消耗（万）',
  note VARCHAR(255) NOT NULL DEFAULT '',
  catalog_lines_json JSON NOT NULL DEFAULT ('[]') COMMENT '物品消耗 [{catalogItemId,quantity,name}]',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY ux_cdt_user_date_char (user_id, biz_date, character_id),
  KEY idx_cdt_user_date (user_id, biz_date),
  CONSTRAINT fk_cdt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_cdt_character FOREIGN KEY (character_id) REFERENCES consumption_characters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS task_templates (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description VARCHAR(512) NOT NULL DEFAULT '',
  frequency ENUM('daily','four_day','weekly_once','weekly_twice') NOT NULL DEFAULT 'daily',
  sort_order INT NOT NULL DEFAULT 100,
  enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=show in recommended list; 0=hidden (backfill only)',
  manual_sort_order INT NULL COMMENT 'Manual ordering for recommended list; lower comes first.',
  cooldown_days INT NOT NULL DEFAULT 4,
  schedule_weekdays VARCHAR(32) NULL COMMENT '0=周日..6=周六，逗号分隔',
  schedule_start TIME NULL,
  schedule_end TIME NULL,
  schedule_pin_early_minutes INT UNSIGNED NOT NULL DEFAULT 30,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS task_completions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  task_id INT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  started_at DATETIME NULL,
  ended_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_tc_task FOREIGN KEY (task_id) REFERENCES task_templates(id) ON DELETE CASCADE,
  KEY idx_tc_user_task_date (user_id, task_id, biz_date),
  KEY idx_tc_user_ended (user_id, ended_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS task_done_entries (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  dedupe_key VARCHAR(180) NOT NULL,
  task_id INT UNSIGNED NULL,
  title VARCHAR(256) NOT NULL,
  started_at DATETIME NULL,
  ended_at DATETIME NULL,
  duration_seconds INT UNSIGNED NULL COMMENT 'started_at 到 ended_at 的秒数',
  unit_count INT UNSIGNED NULL COMMENT 'Per-entry count for special tasks (e.g. weekly ghost captures).',
  source VARCHAR(32) NOT NULL DEFAULT 'complete',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY ux_done_user_date_key (user_id, biz_date, dedupe_key),
  KEY idx_done_user_date (user_id, biz_date),
  KEY idx_done_user_ended (user_id, ended_at),
  KEY idx_done_task (user_id, task_id),
  CONSTRAINT fk_done_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_done_template FOREIGN KEY (task_id) REFERENCES task_templates(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS catalog_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(128) NOT NULL,
  image_url VARCHAR(512) NOT NULL DEFAULT '',
  price_w DECIMAL(14,2) NOT NULL DEFAULT 0.00,
  level_label VARCHAR(64) NOT NULL DEFAULT '',
  description VARCHAR(600) NOT NULL DEFAULT '',
  panel VARCHAR(32) NOT NULL DEFAULT 'fixed',
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_catalog_user_panel (user_id, panel, sort_order),
  CONSTRAINT fk_catalog_items_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mech_catalog_line_agg (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  item_name VARCHAR(191) NOT NULL,
  unit_price_w DECIMAL(14,4) NOT NULL,
  quantity INT UNSIGNED NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_mech_line_user_date (user_id, biz_date),
  CONSTRAINT fk_mech_line_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mech_ledger_day_meta (
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  point_card_points DECIMAL(14,2) NOT NULL DEFAULT 0,
  point_card_saved_at DATETIME NULL COMMENT '点卡快照写入时刻；仅点「保存收益」/「保存并清除计时」时更新',
  online_roles INT UNSIGNED NOT NULL DEFAULT 1,
  elapsed_sec INT UNSIGNED NULL COMMENT '保存收益快照时的累计在线时长（秒）',
  ledger_base_elapsed_sec INT UNSIGNED NULL COMMENT '记账台计时暂停底数（秒）',
  ledger_run_start_at_ms BIGINT NULL COMMENT '计时运行中墙钟 ms；停表为 NULL',
  ledger_point_card_json JSON NULL COMMENT '点卡分段',
  cash_game_gold_w DECIMAL(14,4) NOT NULL DEFAULT 0 COMMENT '刷得现金游戏币（万），与物品单价w无关',
  team_principals_w JSON NULL COMMENT '队伍本金(万) JSON数组',
  team_cash_game_gold_w JSON NULL COMMENT '各队现金梦幻币(万)；NULL=旧版仅 cash_game_gold_w 为毛合计',
  saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, biz_date),
  CONSTRAINT fk_mech_day_meta_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mech_ledger_user_prefs (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  rmb_yuan DECIMAL(12,2) NOT NULL DEFAULT 30.00 COMMENT '锚定万数游戏币对应的人民币，与客户端 LEDGER_GAME_WAN_ANCHOR 一致',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_mech_prefs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mech_ledger_session_state (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  state_json JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_mech_sess_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS artifact_day_selected (
  user_id BIGINT UNSIGNED NOT NULL,
  biz_date DATE NOT NULL,
  selected_json JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, biz_date),
  CONSTRAINT fk_artifact_day_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS artifact_boss_images (
  user_id BIGINT UNSIGNED NOT NULL,
  artifact_name VARCHAR(64) NOT NULL,
  image_url VARCHAR(512) NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, artifact_name),
  CONSTRAINT fk_artifact_boss_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS artifact_guide_state (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  state_json JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_artifact_guide_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS artifact_guide_content (
  artifact_name VARCHAR(64) NOT NULL PRIMARY KEY,
  content_json JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_client_prefs (
  user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  prefs_json JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_ucp_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS calendar_activities (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  act_key VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  description VARCHAR(512) NOT NULL DEFAULT '',
  schedule_weekdays VARCHAR(32) NOT NULL DEFAULT '' COMMENT '0=周日..6=周六，逗号分隔',
  schedule_start TIME NOT NULL,
  schedule_end TIME NOT NULL,
  schedule_start_2 TIME NULL COMMENT '第二段开始（如英雄大会第二场）',
  schedule_end_2 TIME NULL COMMENT '第二段结束',
  pin_early_minutes INT UNSIGNED NOT NULL DEFAULT 30,
  stars TINYINT UNSIGNED NOT NULL DEFAULT 4,
  wukai_rank INT NOT NULL DEFAULT 50,
  sort_order INT NOT NULL DEFAULT 50,
  month_week TINYINT UNSIGNED NULL COMMENT '当月第几个「锚定星期」；NULL=仅按 weekday',
  month_anchor_weekday TINYINT UNSIGNED NULL COMMENT '与 month_week：0=周日..6=周六；月度门派闯关等为0，双龙为6',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY ux_cal_act_key (act_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
