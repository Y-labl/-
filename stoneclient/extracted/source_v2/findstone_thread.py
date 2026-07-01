import time
import win32gui
from PyQt5.QtCore import QThread, pyqtSignal, QPoint, QTimer
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication
import vmdiff_util
from mouse_util import mouseUtil, MouseInfo
from color_util import isStone, isStoneText, is120PointCount, isResultPopShow
from const import (stonePointList, BuyTime1, BuyTime2, Buy120140, Buy120, BuyAuto,
                   pointList120_5or6, VmXiaoyao, VmScrcpy, GxTimePre)
from time_util import getNow

# 常量：从原始字节码反汇编中还原
perStoneSend = 0.05   # 每次找晶石间隔（秒）
perPriceSend = 0.02   # 每次价格检测间隔（秒）
perPopSend = 0.2      # 每次弹窗检测间隔（秒）
totalSend = 5         # 最大重试次数（curFindSend > 5 即约 5 秒超时）


class FindStoneThread(QThread):
    fail_res_signal = pyqtSignal()
    succ_res_signal = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, vm, buyTime, buyType, gxTimeMs):
        super(FindStoneThread, self).__init__()
        self.parent = vm.parent
        self.child = vm.child

        self.curFindSend = 0

        self.winName = vm.winName
        if vm.vmType == VmXiaoyao:
            self.winName += "[逍]"
        elif vm.vmType == VmScrcpy:
            self.winName += "[机]"  # 手机投屏
        else:
            self.winName += "[雷]"

        self.buyTime = 0.11
        self.vmType = vm.vmType
        self.initBuyTime(buyTime)
        self.buyType = buyType
        self.gxTimeMs = gxTimeMs
        self.startFindT = datetime.now()

    def initBuyTime(self, buyTime):
        if buyTime == BuyTime1:
            if self.vmType == VmXiaoyao:
                self.buyTime = 0.08
            else:
                self.buyTime = 0.11
        elif buyTime == BuyTime2:
            if self.vmType == VmXiaoyao:
                self.buyTime = 0.11
            else:
                self.buyTime = 0.15

    def run(self):
        nowTime = getNow()
        dateStr = (str(nowTime.date().year) + "-"
                   + str(nowTime.date().month) + "-"
                   + str(nowTime.date().day))
        timeStr = dateStr + GxTimePre + str(self.gxTimeMs) + "Z"
        clickGxTime = datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S.%fZ")

        gx_start_time = (clickGxTime - nowTime).total_seconds()

        self.log_signal.emit(self.winName + "距离抢购时间"
                             + GxTimePre + str(self.gxTimeMs) + "Z"
                             + "还剩：" + str("%.3f" % gx_start_time)
                             + "秒，请等待...")

        if gx_start_time > 0:
            time.sleep(gx_start_time)

        # 先点击兑换功勋按钮
        tip = "{}点击兑换功勋".format(self.winName)
        mouseUtil.click(self.getClickHwnd(),
                        MouseInfo(vmdiff_util.VmGxPoint(self.vmType), tip))

        # 重置找晶石起始时间
        self.startFindT = datetime.now()
        stonePoints = None

        while True:
            stonePoints = self.getStones(self.parent)
            if stonePoints is not None:
                break

            self.curFindSend += perStoneSend
            time.sleep(perStoneSend)

            if self.curFindSend > totalSend:
                self.log_signal.emit("{}超过{}s未发现晶石".format(self.winName, totalSend))
                self.fail_res_signal.emit()
                return

        if stonePoints is not None:
            self.dealFindStone(stonePoints)

    def dealFindStone(self, stonePoints):
        if self.buyType == Buy120140:
            self.clickStoneBuy(stonePoints[0], True, needClickStone=True)
        elif self.buyType == Buy120:
            self.find120AndBuy(stonePoints)
        elif self.buyType == BuyAuto:
            if len(stonePoints) == 1:
                self.clickStoneBuy(stonePoints[0], True, needClickStone=True)
            elif len(stonePoints) > 1:
                self.find120AndBuy(stonePoints)

    def find120AndBuy(self, stonePoints):
        curFindPriceSend = 0
        stonePoint = stonePoints[0]

        startT = datetime.now()
        tip = "{}花费{}ms发现{}个晶石,选中判断120({},{})".format(
            self.winName,
            int((datetime.now() - self.startFindT).total_seconds() * 1000),
            len(stonePoints),
            stonePoint.x(),
            stonePoint.y()
        )

        # 先点击晶石，弹出价格窗口
        mouseUtil.click(self.getClickHwnd(),
                        MouseInfo(stonePoint, tip))

        # 循环检测价格
        while True:
            screen = QApplication.primaryScreen()
            img = screen.grabWindow(self.parent).toImage()
            pointCount_120 = is120PointCount(img, self.vmType)

            if pointCount_120 > 0:
                is120 = pointCount_120 >= len(pointList120_5or6)
                levelTip = "120" if is120 else "140"

                self.log_signal.emit("{}花费{}ms读取到价格为{}".format(
                    self.winName,
                    int((datetime.now() - startT).total_seconds() * 1000),
                    levelTip
                ))

                if is120:
                    self.clickStoneBuy(stonePoint, False, needClickStone=False)
                    return
                elif len(stonePoints) > 1:
                    self.clickStoneBuy(stonePoints[1], True, needClickStone=True)
                    return
                else:
                    self.fail_res_signal.emit()
                    return

            curFindPriceSend += perPriceSend
            time.sleep(perPriceSend)

            if curFindPriceSend > 1:
                self.log_signal.emit("{}花费1s未获取到价格".format(self.winName))
                self.fail_res_signal.emit()
                return

    def clickStoneBuy(self, stonePoint, needClickStone):
        if needClickStone:
            stoneX = stonePoint.x()
            stoneY = stonePoint.y()
            tip = "{}点击石头({},{})".format(self.winName, stoneX, stoneY)
            mouseUtil.click(self.getClickHwnd(),
                            MouseInfo(QPoint(stoneX, stoneY), tip))
            time.sleep(self.buyTime)

        tip = "{}点击够买".format(self.winName)
        mouseUtil.click(self.getClickHwnd(),
                        MouseInfo(vmdiff_util.VmBuyPoint(self.vmType), tip))

        while True:
            screen = QApplication.primaryScreen()
            img = screen.grabWindow(self.parent).toImage()

            if isResultPopShow(img, self.vmType):
                if isStoneText(img, self.vmType):
                    self.succ_res_signal.emit()
                else:
                    self.fail_res_signal.emit()
                return
            time.sleep(perPopSend)

    def getStones(self, hwnd):
        if not win32gui.IsWindow(hwnd):
            return None

        screen = QApplication.primaryScreen()
        img = screen.grabWindow(hwnd).toImage()

        if self.buyType == Buy120140:
            for point in stonePointList:
                offset = vmdiff_util.VmPointOffset(self.vmType)
                if isStone(img, point + offset):
                    return [point]
            return None

        resPoints = []
        for point in stonePointList:
            offset = vmdiff_util.VmPointOffset(self.vmType)
            if isStone(img, point + offset):
                resPoints.append(point)
                if len(resPoints) > 1:
                    break

        if len(resPoints) > 0:
            return resPoints
        return None

    def getClickHwnd(self):
        if self.vmType == VmXiaoyao:
            return self.parent
        # 雷电和 scrcpy 都使用 child（scrcpy 的 child==parent）
        return self.child
