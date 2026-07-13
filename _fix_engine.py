# -*- coding: utf-8 -*-
import sys
filepath = r"D:\mhxy-auto-fight\mhxy_engine.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Read {len(lines)} lines")

# Fix 1: _wait_combat_end
lines[876] = '        for _ in range(30):\n'
lines[881] = '            time.sleep(0.3)\n'
print("Fix 1 OK")

# Fix 2: _is_show_four_person
new_block2 = [
    '    def _is_show_four_person(self):\n',
    '        """检测四小人界面：好友入口+打开地图+PK逃跑均不可见"""\n',
    '        for _ in range(2):\n',
    '            frame = self.get_frame()\n',
    '            if frame is None:\n',
    '                return False\n',
    '            if self.find(frame, "好友入口") is not None:\n',
    '                return False\n',
    '            if self.find(frame, "打开地图") is not None:\n',
    '                return False\n',
    '            if self.find(frame, "PK-逃跑", threshold=0.50) is not None:\n',
    '                return False\n',
    '            time.sleep(0.15)\n',
    '        return True\n',
]
lines[882:895] = new_block2
print("Fix 2 OK")

# Fix 3: check_and_heal_after_combat
new_block3 = [
    '        # 直接取帧检测血量（已确认非战斗）\n',
    '        time.sleep(0.05)\n',
    '        f = self.get_frame()\n',
    '        if f is None:\n',
    '            return\n',
    '\n',
    '        hp, mp, bb, no_bb = self.detect_hp_mp_bb(f)\n',
]
lines[530:545] = new_block3
print("Fix 3 OK")

# Fix 4: post_combat sleeps
lines[1005] = '            time.sleep(0.2)\n'
lines[1010] = '            time.sleep(0.2)\n'
print("Fix 4 OK")

# Fix 5: remove post-combat sleep in main loop
lines[1100] = '                    continue\n'
print("Fix 5 OK")

# Fix 6: Add four person detection in main loop
insert6 = [
    '\n',
    '                # === 非战斗：先检测四小人 ===\n',
    '                if not in_pk and not self.was_in_pk:\n',
    '                    if self._is_show_four_person():\n',
    '                        self._log(f"[{loop}] 👥 检测到四小人界面")\n',
    '                        self._handle_four_person()\n',
    '                        time.sleep(0.2)\n',
    '                        continue\n',
    '\n',
]
lines[1101:1101] = insert6
print("Fix 6 OK")

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Written {len(lines)} lines. Done!")
