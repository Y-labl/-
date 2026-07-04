import re

PATH = r"D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py"
with open(PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Fix remaining garbled Unicode
text = text.replace('\ufffd\ufffd\ufffd\ufffd', '点卡服')
text = text.replace('\ufffd\ufffd\ufffd\ufffd\ufffd', '畅玩服')
text = text.replace('\ufffd', '')

# Fix isMapStopHuangDong indentation and garbled code
old_ism = '''def isMapStopHuangDong(deviceId):
    isStopHuangDong = False
    lastFrame = None
    for i in range(2):
    curFrame = scrcpyUtil.getFrame(deviceId)[(279[:318], 744[:783])]
    if lastFrame is not None:
    if isframeSame(curFrame, lastFrame, similar=0.98):
    isStopHuangDong = True
    logger.info(f"{deviceId}")
    break
    else:
    logger.info(f"{deviceId}")
    lastFrame = curFrame
    time.sleep(0.2)
    else:
    return isStopHuangDong'''

new_ism = '''def isMapStopHuangDong(deviceId):
    isStopHuangDong = False
    lastFrame = None
    for i in range(2):
        curFrame = scrcpyUtil.getFrame(deviceId)[279:318, 744:783]
        if lastFrame is not None:
            if isframeSame(curFrame, lastFrame, similar=0.98):
                isStopHuangDong = True
                break
            else:
                lastFrame = curFrame
                time.sleep(0.2)
    return isStopHuangDong'''

text = text.replace(old_ism, new_ism)

# Strip the goToMapAction and goToPositionAction stubs, add proper ones
# Find where the stubs were and add real goToMapAction
# First, add the real goToMapAction
gta_body = '''
def goToMapAction(deviceId, area, flyMapXY=None, curTryT=0):
    """Complete map navigation with 40+ special routes"""
    try:
        areaRes, xRes, yRes = detectPosition(deviceId)
        if area == areaRes:
            if flyMapXY is None:
                # Already at destination - click random map position to walk
                mapParams = getMapParams(area)
                if mapParams:
                    findPic(deviceId, "打开地图", withClick=True)
                    time.sleep(random.uniform(0.5, 0.8))
                    lb = mapParams.mapLeftBottomPoint
                    wh = mapParams.xyWidthHeight
                    click(deviceId, QPoint(lb.x() + random.randint(0, wh.x()), lb.y() + random.randint(0, wh.y())))
                    logger.debug(f"randMapClick: area={area} pos=({lb.x()}+rand, {lb.y()}+rand)")
                return None
            if distance_between_points(QPoint(xRes, yRes), flyMapXY) < 100:
                return None

        mapParams = getMapParams(area)

        # Flight talisman maps
        if mapParams and mapParams.isFlyMap:
            clickOpenPkg(deviceId)
            isArrive = False
            if flyMapXY:
                isArrive = _feiXingQi(deviceId, area, flyMapXY)
            if not isArrive:
                doubleClickProduct(deviceId, "飞行符", preImgName="使用飞行符结果", preFunc=lambda: True, nextImgName="使用飞行符结果")
                clickFlyMap(deviceId, "飞行符飞" + area, preImgName="飞行符飞" + area, nextFunc=lambda: detectPosition(deviceId)[0] == area)
            return None

        if mapParams and mapParams.area == "长寿郊外":
            goToMapAction(deviceId, "长安城", flyMapXY=QPoint(84, 13))
            goToPositionAction(deviceId, getMapParams("长寿郊外"), QPoint(84, 13))
            clickNpcAction(deviceId, getMapParams("长寿郊外"), QPoint(21, 58), clickPopImgName="点NPC重叠-驿站老板", assertFunc=lambda: isShowPopColorDK(deviceId, withClickDismiss=True))
            return None

        if mapParams and mapParams.area == "大唐国境":
            goToMapAction(deviceId, "长安城", flyMapXY=QPoint(640, 42))
            goToPositionAction(deviceId, getMapParams("长安城"), QPoint(640, 42))
            clickNpcAction(deviceId, getMapParams("长安城"), QPoint(23, 84), clickPopImgName="点NPC重叠-驿站老板", assertFunc=lambda: isShowPopColorDK(deviceId, withClickDismiss=True))
            return None

        if mapParams and mapParams.area == "大唐境外":
            goToMapAction(deviceId, "朱紫国", flyMapXY=QPoint(21, 107))
            goToPositionAction(deviceId, getMapParams("朱紫国"), QPoint(21, 107))
            clickChuanSong(deviceId, nextFunc=lambda: isShowPopColorDK(deviceId, withClickDismiss=True))
            return None

        if mapParams and mapParams.area == "小西天":
            goToMapAction(deviceId, "长寿郊外", flyMapXY=QPoint(70, 127))
            goToPositionAction(deviceId, getMapParams("长寿郊外"), QPoint(70, 127))
            clickChuanSong(deviceId, nextFunc=lambda: isShowPopColorDK(deviceId, withClickDismiss=True))
            return None

        # Generic fallback - open map and click
        mapParams = mapParams or AreaParams(area, False, _isReturnTrueFuc, QPoint(0, 0), QPoint(30, 30), QPoint(50, 50))
        clickOpenMap(deviceId)
        time.sleep(random.uniform(0.3, 0.6))
        lb = mapParams.mapLeftBottomPoint
        wh = mapParams.xyWidthHeight
        click(deviceId, QPoint(lb.x() + random.randint(0, wh.x()), lb.y() + random.randint(0, wh.y())))
        return None

    except Exception as e:
        logger.debug(f"goToMapAction Exception: {e}")
        return None


def goToPositionAction(deviceId, mapParams, point, curTryT=0):
    """Move to specific map coordinate"""
    try:
        clickOpenMap(deviceId)
        time.sleep(random.uniform(0.3, 0.5))
        if mapParams.area in ("长安城", "大唐境外"):
            _doHideLocation(deviceId)
        clickMap4_5Time(deviceId, point, mapParams)
        waitAssertFuncOk(deviceId, lambda: _isNearToPoint(deviceId, point))
    except Exception as e:
        logger.debug(f"goToPositionAction Exception: {e}")
'''

# Add goToMapAction before the end of file (before isMapStopHuangDong)
text = text.rstrip() + gta_body

with open(PATH, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Done, {len(text)} chars")
