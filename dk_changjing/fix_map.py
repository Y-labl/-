# fix_map.py - comprehensive fix for v2 map_action.py
import re

SRC = r"D:\Program Files\mhxy-project\小霸王\反编译结果_v2\python_source\game_action\map_action.py"
DST = r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py"

with open(SRC, "r", encoding="utf-8") as f:
    content = f.read()

# === Fix 1: Combine consecutive if statements ===
# Pattern: if cond1:\nif cond2:\nif cond3:\nreturn True\nreturn False
def combine_ifs(m):
    lines = m.group(0).strip().split("\n")
    indent = lines[0][:len(lines[0]) - len(lines[0].lstrip())]
    conds = []
    returns = []
    for l in lines:
        s = l.strip()
        if s.startswith("if ") and s.endswith(":"):
            conds.append(s[3:-1].strip())
        elif s == "return True":
            returns.append("return True")
        elif s == "return False":
            returns.append("return False")
    if conds and returns:
        combined = indent + "if " + " and ".join(conds) + ":"
        body = indent + "    " + returns[0]
        rest = "\n".join(indent + r for r in returns[1:])
        return combined + "\n" + body + ("\n" + rest if rest else "")
    return m.group(0)

# Pattern for 3 ifs + return True + return False
content = re.sub(
    r"(?:    )?if abs\(r - \d+\) < \d+:\n"
    r"(?:    )?if abs\(g - \d+\) < \d+:\n"
    r"(?:    )?if abs\(b - \d+\) < \d+:\n"
    r"(?:    )?return True\n"
    r"(?:    )?return False",
    combine_ifs,
    content
)
# Pattern for 2 ifs + return True + return False (like fuRongGuo)
content = re.sub(
    r"(?:    )?if abs\(r - \d+\) < \d+:\n"
    r"(?:    )?if abs\(b - \d+\) < \d+:\n"
    r"(?:    )?return True\n"
    r"(?:    )?return False",
    combine_ifs,
    content
)

# === Fix 2: Garbled Unicode ===
content = content.replace("\ufffd\ufffd\ufffd\ufffd", "点卡服")
content = content.replace("\ufffd\ufffd\ufffd\ufffd\ufffd", "畅玩服")

# === Fix 3: Fix class __init__ indentation ===
old_init = "    def __init__(self, area, isFlyMap, isMapLightFunc, mapLeftBottomPoint, xyRange, xyWidthHeight):\n    self.area = area\n    self.isFlyMap = isFlyMap\n    self.isMapLightFunc = isMapLightFunc\n    self.mapLeftBottomPoint = mapLeftBottomPoint\n    self.xyRange = xyRange\n    self.xyWidthHeight = xyWidthHeight"
new_init = "    def __init__(self, area, isFlyMap, isLightFunc, mapLeftBottomPoint, xyWidthHeight, xyRange):\n        self.area = area\n        self.isFlyMap = isFlyMap\n        self.isLightFunc = isLightFunc\n        self.mapLeftBottomPoint = mapLeftBottomPoint\n        self.xyWidthHeight = xyWidthHeight\n        self.xyRange = xyRange"
if old_init in content:
    content = content.replace(old_init, new_init)

# Fix isMapLightFunc -> isLightFunc everywhere
content = content.replace("isMapLightFunc", "isLightFunc")

# Fix function name mappings
mappings = {
    "_huaGuoShanMapIsLightDK": "_huaGuoShanIsLightDK",
    "_beiJuLuZhouMapIsLightDK": "_isReturnTrueFuc",
    "_dongHaiYuanMapIsLightDK": "_isReturnTrueFuc",
    "_nvBaMuMapIsLightDK": "_isReturnTrueFuc",
    "_qingQiuMapIsLightDK": "_isReturnTrueFuc",
    "_lingBoChengMapIsLightDK": "_isReturnTrueFuc",
    "_yueGongMapIsLightDK": "_isReturnTrueFuc",
    "_wuZhiShanMapIsLightDK": "_isReturnTrueFuc",
    "_qiLinShanMapIsLightDK": "_isReturnTrueFuc",
    "_diaoSiDongMapIsLightDK": "_wanZiShanShanIsLightDK",
    "_nvErCunMapIsLightDK": "_nvErCunIsLightDK",
    "_jiaoWaiMapIsLightDK": "_jiangNanYeWaiIsLightDK",
    "_daTangGuanFuMapIsLightDK": "_daTangGuoJingIsLightDK",
    "_jiuLiChengMapIsLightDK": "_isReturnTrueFuc",
    "_siTuoLingMapIsLightDK": "_isReturnTrueFuc",
    "_moJiaCunMapIsLightDK": "_isReturnTrueFuc",
}
for old, new in mappings.items():
    content = content.replace(old, new)

# === Fix 4: Fix getMapParams ===
old_gmp = "def getMapParams(area):\n    if const.gameType == \"点卡服\":\n    for mapParams in mapParamsListDK:\n    if mapParams.area == area:\n    return mapParams\n    else:\n    if const.gameType == \"畅玩服\":\n    for mapParams in mapParamsListCW:\n    if mapParams.area == area:\n    return mapParams"
new_gmp = "def getMapParams(area):\n    if const.gameType == \"点卡服\":\n        for mapParams in mapParamsListDK:\n            if mapParams.area == area:\n                return mapParams\n    else:\n        if const.gameType == \"畅玩服\":\n            for mapParams in mapParamsListCW:\n                if mapParams.area == area:\n                    return mapParams\n    return None"
if old_gmp in content:
    content = content.replace(old_gmp, new_gmp)

# === Fix 5: Fix clickNpcAction ===
old_cna = '''def clickNpcAction(deviceId, mapParams, npcPoint, clickPopImgName=None,
                   middleImgNames=None, assertImgName=None, assertFunc=None,
                   withClickDismiss=True, isYiZhan=False, curTryT=0):
    try:
        if not mapParams.area == longAnCheng or isYiZhan:
            if mapParams.area == "长寿郊外":
                openHideAction(deviceId)
            if isYiZhan:
                findOneFromPics(deviceId, ["驿站老板1", "驿站老板2", "驿站老板3", "驿站老板4"], withClick=True)
            if npcPoint.y() <= 13 or npcPoint.x() <= 23:
                time.sleep(1.5)
            clickPoint = _getNpcAbsolutePoint(deviceId, mapParams, npcPoint)
            clickNpcPerson(deviceId, clickPoint,
                middleImgNames=middleImgNames,
                middleFunc=(lambda: isShowPopColorDK(deviceId, withClickDismiss=withClickDismiss)),
                nextImgName=clickPopImgName)
            clickNpcDialog(deviceId, preImgName=clickPopImgName,
                nextImgName=assertImgName, nextFunc=assertFunc)
    except Exception as e:
        logger.debug(f"clickNpcAction Exception: {e}")'''
new_cna = '''def clickNpcAction(deviceId, mapParams, npcPoint, clickPopImgName=None,
                   middleImgNames=None, assertImgName=None, assertFunc=None,
                   withClickDismiss=True, isYiZhan=False, curTryT=0):
    try:
        if not mapParams.area == "长安城" or isYiZhan:
            if mapParams.area == "长寿郊外":
                openHideAction(deviceId)
            if isYiZhan:
                findOneFromPics(deviceId, ["驿站老板1", "驿站老板2", "驿站老板3", "驿站老板4"], withClick=True)
            if npcPoint.y() <= 13 or npcPoint.x() <= 23:
                time.sleep(1.5)
            clickPoint = _getNpcAbsolutePoint(deviceId, mapParams, npcPoint)
            clickNpcPerson(deviceId, clickPoint,
                middleImgNames=middleImgNames,
                middleFunc=(lambda: isShowPopColorDK(deviceId, withClickDismiss=withClickDismiss)),
                nextImgName=clickPopImgName)
            clickNpcDialog(deviceId, preImgName=clickPopImgName,
                nextImgName=assertImgName, nextFunc=assertFunc)
    except Exception as e:
        logger.debug(f"clickNpcAction Exception: {e}")'''
if old_cna in content:
    content = content.replace(old_cna, new_cna)

with open(DST, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Fixed, saved to {DST}")
print(f"Total: {len(content)} chars, {content.count(chr(10))} lines")
