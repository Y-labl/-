import re

src = open(r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py", encoding="utf-8").read()

# Fix pattern: multiple if abs(...) at same indent level that should be nested/combined
# Pattern 1: 3 if statements that should be combined
pattern1 = re.compile(
    r'(    if abs\(r - \d+\) < \d+:)\n'
    r'(    if abs\(g - \d+\) < \d+:)\n'
    r'(    if abs\(b - \d+\) < \d+:)\n'
    r'(    return True)\n'
    r'(    return False)'
)

def fix_func(m):
    r_line = m.group(1)
    g_line = m.group(2)
    b_line = m.group(3)
    # Extract conditions
    r_cond = r_line.strip()[3:]  # remove "if "
    g_cond = g_line.strip()[3:]
    b_cond = b_line.strip()[3:]
    new_if = f"    if {r_cond} and {g_cond} and {b_cond}:"
    return f"{new_if}\n        return True\n    return False"

src = pattern1.sub(fix_func, src)

# Pattern 2: 2 if statements (like _fuRongGuoMapIsLightDK which checks r and b but not g)
pattern2 = re.compile(
    r'(    if abs\(r - \d+\) < \d+:)\n'
    r'(    if abs\(b - \d+\) < \d+:)\n'
    r'(    return True)\n'
    r'(    return False)'
)

def fix_func2(m):
    r_line = m.group(1)
    b_line = m.group(2)
    r_cond = r_line.strip()[3:]
    b_cond = b_line.strip()[3:]
    new_if = f"    if {r_cond} and {b_cond}:"
    return f"{new_if}\n        return True\n    return False"

src = pattern2.sub(fix_func2, src)

open(r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py", "w", encoding="utf-8").write(src)
print("Fixed, len:", len(src))
