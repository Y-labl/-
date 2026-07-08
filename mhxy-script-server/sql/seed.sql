USE mhxy_script;

INSERT IGNORE INTO battle_scene (scene_name, scene_type, game_type, game_area, game_server, role_name, character_level, character_team, auto_battle, auto_recovery, auto_revival, auto_pickup, status, user_id, use_count, success_count, create_time) VALUES
('日常任务-师门', 'pve', 'dianka', '生日快乐', '生日快乐10', '大唐官府01', 69, 'single', 1, 1, 1, 1, 1, 1, 156, 152, NOW()),
('抓鬼任务', 'pve', 'dianka', '生日快乐', '生日快乐10', '大唐官府01', 109, 'single', 1, 1, 1, 1, 1, 1, 89, 85, NOW()),
('宝图任务', 'pve', 'dianka', '紫禁城', '紫禁城15', '龙宫02', 89, 'team', 1, 0, 0, 1, 1, 1, 0, 0, NOW()),
('跑环任务', 'pve', 'dianka', '钓鱼岛', '钓鱼岛03', '普陀山01', 109, 'single', 1, 1, 0, 1, 1, 1, 0, 0, NOW()),
('副本-乌鸡国', 'dungeon', 'changwan', '生日快乐', '生日快乐03', '大唐官府02', 109, 'team', 1, 1, 1, 1, 1, 1, 0, 0, NOW()),
('小西天偷卡', 'steal_card', 'dianka', '生日快乐', '生日快乐10', '大唐官府01', 69, 'single', 1, 1, 1, 1, 1, 1, 0, 0, NOW());

INSERT IGNORE INTO template_image (template_name, category, template_path, file_size, width, height, match_threshold, description, usage_count, success_count, status, create_time) VALUES
('打开地图', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/打开地图.bmp', 9054, 0, 0, 0.85, '点击打开地图按钮', 0, 0, 1, NOW()),
('关闭地图', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/关闭地图.bmp', 11754, 0, 0, 0.85, '点击关闭地图按钮', 0, 0, 1, NOW()),
('小西天地图', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/小西天模板.bmp', 1774774, 0, 0, 0.80, '小西天地图定位模板', 0, 0, 1, NOW()),
('小西天1', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/xiaoxitian1.png', 2545704, 0, 0, 0.80, '小西天战斗场景截图1', 0, 0, 1, NOW()),
('小西天2', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/xiaoxitian2.png', 2565795, 0, 0, 0.80, '小西天战斗场景截图2', 0, 0, 1, NOW()),
('小西天3', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/xiaoxitian3.png', 1574931, 0, 0, 0.80, '小西天战斗场景截图3', 0, 0, 1, NOW()),
('小西天4', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/xiaoxitian4.png', 1803132, 0, 0, 0.80, '小西天战斗场景截图4', 0, 0, 1, NOW()),
('战斗场景', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/zhandou1.png', 1400943, 0, 0, 0.80, '战斗场景截图', 0, 0, 1, NOW()),
('战斗法术', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/战斗-法术.bmp', 15222, 0, 0, 0.85, '战斗法术按钮', 0, 0, 1, NOW()),
('战斗防御', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/战斗防御.bmp', 14946, 0, 0, 0.85, '战斗防御按钮', 0, 0, 1, NOW()),
('噬天虎', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/噬天虎.bmp', 7614, 0, 0, 0.80, '噬天虎怪物模板', 0, 0, 1, NOW()),
('炎魔神', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/炎魔神.bmp', 6438, 0, 0, 0.80, '炎魔神怪物模板', 0, 0, 1, NOW()),
('金身僧', 'monster', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/金身僧.bmp', 7942, 0, 0, 0.80, '金身僧怪物模板', 0, 0, 1, NOW()),
('妙手空空技能', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/妙手空空技能.png', 9760, 0, 0, 0.85, '妙手空空技能图标', 0, 0, 1, NOW()),
('好友', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/好友.bmp', 12834, 0, 0, 0.85, '好友按钮', 0, 0, 1, NOW()),
('道具', 'button', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/道具.bmp', 10858, 0, 0, 0.85, '道具按钮', 0, 0, 1, NOW()),
('地点模板', 'dialog', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/地点模板.bmp', 35670, 0, 0, 0.80, '地点识别模板', 0, 0, 1, NOW()),
('坐标模板', 'dialog', 'D:/Program Files/mhxy-project/mhxy-script-server/templates/坐标模板.bmp', 8790, 0, 0, 0.80, '坐标识别模板', 0, 0, 1, NOW());