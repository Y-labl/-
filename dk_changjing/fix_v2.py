import re

src = open(r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py", encoding="utf-8").read()

# Fix __init__ - v2 has class body unindented  
# Find the __init__ method and indent its body
old_init = """    def __init__(self, area, isFlyMap, isMapLightFunc, mapLeftBottomPoint, xyRange, xyWidthHeight):
    self.area = area
    self.isFlyMap = isFlyMap
    self.isMapLightFunc = isMapLightFunc
    self.mapLeftBottomPoint = mapLeftBottomPoint
    self.xyRange = xyRange
    self.xyWidthHeight = xyWidthHeight"""
new_init = """    def __init__(self, area, isFlyMap, isLightFunc, mapLeftBottomPoint, xyWidthHeight, xyRange):
        self.area = area
        self.isFlyMap = isFlyMap
        self.isLightFunc = isLightFunc
        self.mapLeftBottomPoint = mapLeftBottomPoint
        self.xyWidthHeight = xyWidthHeight
        self.xyRange = xyRange"""
if old_init in src:
    src = src.replace(old_init, new_init)
    print("Fixed __init__")
else:
    print("WARNING: __init__ not matched")

# Fix all mapParamsList entries that use isMapLightFunc -> isLightFunc
src = src.replace("isMapLightFunc", "isLightFunc")

# Fix the function name references - many detection functions were named differently in v2
# _huaGuoShanMapIsLightDK in mapParamsList should be _huaGuoShanIsLightDK
src = src.replace("_huaGuoShanMapIsLightDK", "_huaGuoShanIsLightDK")
src = src.replace("_beiJuLuZhouMapIsLightDK", "_isReturnTrueFuc")  # not defined in v2
src = src.replace("_dongHaiYuanMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_nvBaMuMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_qingQiuMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_lingBoChengMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_yueGongMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_wuZhiShanMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_qiLinShanMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_diaoSiDongMapIsLightDK", "_wanZiShanShanIsLightDK")
src = src.replace("_nvErCunMapIsLightDK", "_nvErCunIsLightDK")
src = src.replace("_jiaoWaiMapIsLightDK", "_jiangNanYeWaiIsLightDK")
src = src.replace("_daTangGuanFuMapIsLightDK", "_daTangGuoJingIsLightDK")
src = src.replace("_jiuLiChengMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_siTuoLingMapIsLightDK", "_isReturnTrueFuc")
src = src.replace("_moJiaCunMapIsLightDK", "_isReturnTrueFuc")

open(r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py", "w", encoding="utf-8").write(src)
print("Fixed, len:", len(src))
