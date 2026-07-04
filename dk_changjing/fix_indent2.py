import re

src = open(r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py", encoding="utf-8").read()

# Fix the broken combined if statements (extra colons)
src = src.replace("if abs(r - 150) < 20: and abs(g - 163) < 20: and abs(b - 130) < 20:", "if abs(r - 150) < 20 and abs(g - 163) < 20 and abs(b - 130) < 20:")
src = src.replace("if abs(r - 181) < 20: and abs(g - 166) < 20: and abs(b - 139) < 20:", "if abs(r - 181) < 20 and abs(g - 166) < 20 and abs(b - 139) < 20:")
src = src.replace("if abs(r - 224) < 30: and abs(g - 197) < 30: and abs(b - 190) < 30:", "if abs(r - 224) < 30 and abs(g - 197) < 30 and abs(b - 190) < 30:")
src = src.replace("if abs(r - 214) < 20: and abs(g - 199) < 20: and abs(b - 189) < 20:", "if abs(r - 214) < 20 and abs(g - 199) < 20 and abs(b - 189) < 20:")
src = src.replace("if abs(r - 245) < 20: and abs(g - 209) < 20: and abs(b - 146) < 20:", "if abs(r - 245) < 20 and abs(g - 209) < 20 and abs(b - 146) < 20:")
src = src.replace("if abs(r - 226) < 20: and abs(g - 187) < 20: and abs(b - 103) < 20:", "if abs(r - 226) < 20 and abs(g - 187) < 20 and abs(b - 103) < 20:")
src = src.replace("if abs(r - 70) < 20: and abs(g - 165) < 20: and abs(b - 160) < 20:", "if abs(r - 70) < 20 and abs(g - 165) < 20 and abs(b - 160) < 20:")
src = src.replace("if abs(r - 235) < 20: and abs(g - 198) < 20: and abs(b - 150) < 20:", "if abs(r - 235) < 20 and abs(g - 198) < 20 and abs(b - 150) < 20:")
src = src.replace("if abs(r - 229) < 20: and abs(g - 164) < 20: and abs(b - 84) < 20:", "if abs(r - 229) < 20 and abs(g - 164) < 20 and abs(b - 84) < 20:")
src = src.replace("if abs(r - 185) < 20: and abs(g - 164) < 20: and abs(b - 117) < 20:", "if abs(r - 185) < 20 and abs(g - 164) < 20 and abs(b - 117) < 20:")

# Use a more general regex to fix remaining issues
# Pattern: if COND1: and COND2: and COND3:
src = re.sub(r'if (.+?): and (.+?): and (.+?):', r'if \1 and \2 and \3:', src)
src = re.sub(r'if (.+?): and (.+?):', r'if \1 and \2:', src)

open(r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py", "w", encoding="utf-8").write(src)
print("Fixed again, len:", len(src))
