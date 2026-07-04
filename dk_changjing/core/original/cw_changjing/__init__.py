def randomClickMap(deviceId, mapParams):
    import random
    from PyQt5.QtCore import QPoint
    from common.util.click_util import click
    lb = mapParams.mapLeftBottomPoint
    wh = mapParams.xyWidthHeight
    px = lb.x() + random.randint(0, wh.x())
    py = lb.y() + random.randint(0, wh.y())
    click(deviceId, QPoint(px, py))

def randomClickMap_CiChouZhiLu(deviceId):
    import random
    from PyQt5.QtCore import QPoint
    from common.util.click_util import click
    click(deviceId, QPoint(random.randint(400, 700), random.randint(50, 100)))
