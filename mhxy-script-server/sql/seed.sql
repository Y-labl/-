USE mhxy_script;

INSERT IGNORE INTO device (device_name, device_type, ip_address, port, screen_width, screen_height, status, remark) VALUES
('夜神模拟器', 'windows', '127.0.0.1', 62001, 1280, 720, 1, '主力模拟器'),
('雷电模拟器', 'windows', '127.0.0.1', 5555, 1920, 1080, 1, '备用模拟器'),
('小米手机', 'android', '192.168.1.100', 5555, 1080, 2400, 0, '物理手机'),
('华为手机', 'android', '192.168.1.101', 5555, 1080, 2340, 0, '备用手机');

INSERT IGNORE INTO battle_scene (scene_name, scene_type, game_type, game_area, game_server, role_name, character_level, character_team, auto_battle, auto_recovery, auto_revival, auto_pickup, status, user_id, use_count, success_count, create_time) VALUES
('日常任务-师门', 'pve', 'dianka', '生日快乐', '生日快乐10', '大唐官府01', 69, 'single', 1, 1, 1, 1, 1, 1, 156, 152, NOW()),
('抓鬼任务', 'pve', 'dianka', '生日快乐', '生日快乐10', '大唐官府01', 109, 'single', 1, 1, 1, 1, 1, 1, 89, 85, NOW()),
('副本-水陆大会', 'dungeon', 'dianka', '生日快乐', '生日快乐10', '大唐官府01', 129, 'single', 1, 1, 1, 1, 1, 1, 45, 42, NOW()),
('宝图任务', 'pve', 'dianka', '紫禁城', '紫禁城05', '龙宫02', 89, 'team', 1, 0, 0, 1, 1, 1, 0, 0, NOW()),
('跑环任务', 'pve', 'dianka', '钓鱼岛', '钓鱼岛03', '普陀山01', 109, 'single', 1, 1, 0, 1, 1, 1, 0, 0, NOW()),
('副本-乌鸡国', 'dungeon', 'changwan', '生日快乐', '生日快乐03', '大唐官府02', 109, 'team', 1, 1, 1, 1, 1, 1, 0, 0, NOW());