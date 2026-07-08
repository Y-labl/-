-- ============================================
-- 梦幻西游自动化脚本系统 数据库初始化脚本
-- 数据库: mhxy_script
-- 用户名: root
-- 密码: root
-- ============================================

-- 注意：执行前请先确保数据库已创建:
-- CREATE DATABASE IF NOT EXISTS mhxy_script DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE mhxy_script;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(128) NOT NULL COMMENT '密码(MD5)',
    phone VARCHAR(20) COMMENT '手机号',
    email VARCHAR(100) COMMENT '邮箱',
    avatar VARCHAR(255) DEFAULT '' COMMENT '头像URL',
    status TINYINT DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    balance INT DEFAULT 100000 COMMENT '余额(金币)',
    total_time INT DEFAULT 0 COMMENT '累计使用时长(分钟)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ============================================
-- 2. 设备表
-- ============================================
CREATE TABLE IF NOT EXISTS device (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '设备ID',
    device_name VARCHAR(100) NOT NULL COMMENT '设备名称',
    device_type VARCHAR(20) DEFAULT 'android' COMMENT '设备类型: android/ios/windows',
    device_id VARCHAR(100) UNIQUE COMMENT '设备唯一标识',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    port INT DEFAULT 5555 COMMENT '端口',
    screen_width INT COMMENT '屏幕宽度',
    screen_height INT COMMENT '屏幕高度',
    status TINYINT DEFAULT 0 COMMENT '状态: 0离线 1在线 2使用中',
    user_id BIGINT COMMENT '所属用户ID',
    current_order_id BIGINT COMMENT '当前任务ID',
    remark VARCHAR(255) COMMENT '备注',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';

-- ============================================
-- 3. 截图记录表
-- ============================================
CREATE TABLE IF NOT EXISTS screenshot (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '截图ID',
    device_id BIGINT NOT NULL COMMENT '设备ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size INT COMMENT '文件大小(字节)',
    thumbnail_path VARCHAR(500) COMMENT '缩略图路径',
    screen_width INT COMMENT '截图宽度',
    screen_height INT COMMENT '截图高度',
    label VARCHAR(50) COMMENT '标签/描述',
    tags VARCHAR(255) COMMENT '标签(逗号分隔)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '截图时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='截图记录表';

-- ============================================
-- 4. 录制任务表
-- ============================================
CREATE TABLE IF NOT EXISTS recording (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '录制ID',
    device_id BIGINT NOT NULL COMMENT '设备ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    task_name VARCHAR(100) NOT NULL COMMENT '任务名称',
    output_path VARCHAR(500) COMMENT '输出文件路径',
    output_file VARCHAR(255) COMMENT '输出文件名',
    duration INT DEFAULT 0 COMMENT '录制时长(秒)',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    fps INT DEFAULT 30 COMMENT '帧率',
    resolution VARCHAR(20) DEFAULT '1920x1080' COMMENT '分辨率',
    status TINYINT DEFAULT 0 COMMENT '状态: 0等待 1录制中 2已完成 3失败',
    error_msg VARCHAR(500) COMMENT '错误信息',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='录制任务表';

-- ============================================
-- 5. 观看连接表
-- ============================================
CREATE TABLE IF NOT EXISTS view_connection (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '连接ID',
    device_id BIGINT NOT NULL COMMENT '设备ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    connection_type VARCHAR(20) DEFAULT 'scrcpy' COMMENT '连接方式: scrcpy/adb',
    stream_url VARCHAR(500) COMMENT '流地址',
    quality VARCHAR(20) DEFAULT 'original' COMMENT '画质: original/high/medium/low',
    bit_rate INT DEFAULT 8000000 COMMENT '码率',
    status TINYINT DEFAULT 0 COMMENT '状态: 0断开 1连接中 2已连接',
    client_ip VARCHAR(50) COMMENT '客户端IP',
    connect_time DATETIME COMMENT '连接时间',
    disconnect_time DATETIME COMMENT '断开时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='观看连接表';

-- ============================================
-- 6. 打怪场景配置表
-- ============================================
CREATE TABLE IF NOT EXISTS battle_scene (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '场景ID',
    scene_name VARCHAR(100) NOT NULL COMMENT '场景名称',
    scene_type VARCHAR(50) DEFAULT 'pve' COMMENT '场景类型: pve/pvp/dungeon/boss',
    game_type VARCHAR(20) DEFAULT 'dianka' COMMENT '游戏区服: dianka/changwan',
    game_area VARCHAR(50) COMMENT '游戏区',
    game_server VARCHAR(50) COMMENT '游戏服',
    role_name VARCHAR(50) COMMENT '角色名称',
    level_range VARCHAR(20) COMMENT '等级范围',
    character_level INT COMMENT '角色等级',
    character_team VARCHAR(20) DEFAULT 'single' COMMENT '组队模式: single/team',
    
    -- 战斗策略配置 (JSON格式)
    battle_strategy JSON COMMENT '战斗策略配置',
    -- 技能配置 (JSON格式)
    skill_config JSON COMMENT '技能配置',
    -- 药品配置 (JSON格式)
    medicine_config JSON COMMENT '药品配置',
    -- 宠物配置 (JSON格式)
    pet_config JSON COMMENT '宠物配置',
    -- 喊话配置 (JSON格式)
    shout_config JSON COMMENT '喊话配置',
    
    -- 执行参数
    auto_battle TINYINT DEFAULT 1 COMMENT '自动战斗: 0否 1是',
    auto_recovery TINYINT DEFAULT 1 COMMENT '自动恢复: 0否 1是',
    auto_revival TINYINT DEFAULT 1 COMMENT '自动复活: 0否 1是',
    auto_pickup TINYINT DEFAULT 1 COMMENT '自动拾取: 0否 1是',
    
    -- 模板图片路径
    template_path VARCHAR(500) COMMENT '模板路径',
    
    status TINYINT DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    user_id BIGINT COMMENT '所属用户',
    use_count INT DEFAULT 0 COMMENT '使用次数',
    success_count INT DEFAULT 0 COMMENT '成功次数',
    total_duration INT DEFAULT 0 COMMENT '累计运行时长(秒)',
    
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打怪场景配置表';

-- ============================================
-- 7. 任务执行记录表
-- ============================================
CREATE TABLE IF NOT EXISTS task_execution (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '执行ID',
    task_type VARCHAR(30) NOT NULL COMMENT '任务类型: battle/screenshot/recording/view',
    task_id BIGINT NOT NULL COMMENT '关联任务ID',
    device_id BIGINT NOT NULL COMMENT '设备ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    
    -- 执行状态
    status TINYINT DEFAULT 0 COMMENT '状态: 0等待 1执行中 2成功 3失败 4取消',
    progress INT DEFAULT 0 COMMENT '进度(0-100)',
    current_step VARCHAR(100) COMMENT '当前步骤',
    error_msg VARCHAR(500) COMMENT '错误信息',
    
    -- 时间记录
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration INT DEFAULT 0 COMMENT '执行时长(秒)',
    
    -- 结果数据 (JSON格式)
    result_data JSON COMMENT '执行结果数据',
    
    -- 统计信息
    battle_count INT DEFAULT 0 COMMENT '战斗次数',
    kill_count INT DEFAULT 0 COMMENT '击杀数量',
    death_count INT DEFAULT 0 COMMENT '死亡次数',
    gold_earned INT DEFAULT 0 COMMENT '获得金币',
    exp_earned INT DEFAULT 0 COMMENT '获得经验',
    
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务执行记录表';

-- ============================================
-- 8. 模板图片表
-- ============================================
CREATE TABLE IF NOT EXISTS template_image (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID',
    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
    template_path VARCHAR(500) NOT NULL COMMENT '模板路径',
    category VARCHAR(50) DEFAULT 'general' COMMENT '分类: button/dialog/npc/monster/item/general',
    description VARCHAR(255) COMMENT '描述',
    match_threshold DECIMAL(4,2) DEFAULT 0.85 COMMENT '匹配阈值',
    width INT COMMENT '图片宽度',
    height INT COMMENT '图片高度',
    file_size INT COMMENT '文件大小',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    success_count INT DEFAULT 0 COMMENT '成功次数',
    user_id BIGINT COMMENT '创建用户',
    status TINYINT DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板图片表';

-- ============================================
-- 9. 偷卡配置表（设备级）
-- ============================================
CREATE TABLE IF NOT EXISTS steal_card_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    device_id BIGINT NOT NULL UNIQUE COMMENT '设备ID(每个设备独立配置)',
    config_name VARCHAR(100) DEFAULT '偷卡配置' COMMENT '配置名称',
    target_monsters VARCHAR(500) DEFAULT '噬天虎,炎魔神,金身僧' COMMENT '目标怪物(逗号分隔)',
    auto_battle TINYINT DEFAULT 1 COMMENT '自动战斗: 0否 1是',
    auto_recovery TINYINT DEFAULT 1 COMMENT '自动恢复: 0否 1是',
    auto_revival TINYINT DEFAULT 1 COMMENT '自动复活: 0否 1是',
    auto_pickup TINYINT DEFAULT 1 COMMENT '自动拾取: 0否 1是',
    map_click_area VARCHAR(100) DEFAULT '80,180,980,2200' COMMENT '地图随机点击区域 x1,y1,x2,y2',
    template_confidence DECIMAL(4,2) DEFAULT 0.80 COMMENT '模板匹配阈值',
    walk_interval INT DEFAULT 500 COMMENT '随机行走间隔(毫秒)',
    steal_attempts INT DEFAULT 3 COMMENT '每场战斗偷取尝试次数',
    status TINYINT DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='偷卡配置表(设备级)';

-- ============================================
-- 10. 操作日志表
-- ============================================
CREATE TABLE IF NOT EXISTS operation_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    user_name VARCHAR(50) COMMENT '用户名',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    module VARCHAR(50) COMMENT '模块',
    target_type VARCHAR(50) COMMENT '操作对象类型',
    target_id BIGINT COMMENT '操作对象ID',
    description VARCHAR(500) COMMENT '操作描述',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(255) COMMENT 'User-Agent',
    request_data TEXT COMMENT '请求数据',
    response_data TEXT COMMENT '响应数据',
    status TINYINT DEFAULT 1 COMMENT '状态: 0失败 1成功',
    error_msg VARCHAR(500) COMMENT '错误信息',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- ============================================
-- 10. 系统配置表
-- ============================================
CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '类型: string/number/boolean/json',
    config_name VARCHAR(100) COMMENT '配置名称',
    config_group VARCHAR(50) DEFAULT 'default' COMMENT '配置分组',
    description VARCHAR(255) COMMENT '描述',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- ============================================
-- 初始化数据
-- ============================================

-- 插入默认管理员用户 (密码: admin123)
INSERT IGNORE INTO sys_user (username, password, phone, email, balance, status) VALUES
('admin', '0192023a7bbd73250516f069df18b500', '13800138000', 'admin@mhxy.com', 1000000, 1),
('test', 'e10adc3949ba59abbe56e057f20f883e', '13900139000', 'test@mhxy.com', 500000, 1);

-- 插入默认系统配置
INSERT IGNORE INTO system_config (config_key, config_value, config_type, config_name, config_group, description) VALUES
('app.name', '梦幻西游自动化脚本', 'string', '应用名称', 'basic', '系统名称'),
('app.version', '1.0.0', 'string', '版本号', 'basic', '当前版本'),
('app.theme', 'light', 'string', '主题', 'basic', '默认主题'),
('device.max_count', '10', 'number', '最大设备数', 'device', '单用户最大设备数'),
('task.max_concurrent', '5', 'number', '最大并发任务', 'task', '最大并发任务数'),
('screenshot.save_days', '30', 'number', '截图保存天数', 'screenshot', '自动清理天数'),
('recording.save_days', '7', 'number', '录制保存天数', 'recording', '自动清理天数'),
('battle.auto_retry', '3', 'number', '自动重试次数', 'battle', '战斗失败自动重试'),
('battle.retry_interval', '5', 'number', '重试间隔(秒)', 'battle', '重试间隔时间');

-- ============================================
-- 创建索引
-- ============================================
CREATE INDEX idx_device_user ON device(user_id);
CREATE INDEX idx_device_status ON device(status);
CREATE INDEX idx_screenshot_device ON screenshot(device_id);
CREATE INDEX idx_screenshot_user ON screenshot(user_id);
CREATE INDEX idx_recording_device ON recording(device_id);
CREATE INDEX idx_recording_status ON recording(status);
CREATE INDEX idx_battle_scene_user ON battle_scene(user_id);
CREATE INDEX idx_task_execution_user ON task_execution(user_id);
CREATE INDEX idx_task_execution_status ON task_execution(status);
CREATE INDEX idx_operation_log_user ON operation_log(user_id);
CREATE INDEX idx_operation_log_time ON operation_log(create_time);

-- ============================================
-- 视图定义
-- ============================================

-- 用户设备视图
CREATE OR REPLACE VIEW v_user_devices AS
SELECT 
    d.*,
    u.username,
    u.phone
FROM device d
LEFT JOIN sys_user u ON d.user_id = u.id;

-- 任务执行统计视图
CREATE OR REPLACE VIEW v_task_stats AS
SELECT 
    user_id,
    task_type,
    COUNT(*) as total_count,
    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) as fail_count,
    SUM(duration) as total_duration
FROM task_execution
GROUP BY user_id, task_type;
