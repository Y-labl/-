# -*- coding: utf-8 -*-
# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: index.py
# Compiled at: 2026-07-01 07:29:31
# Size of source mod 2**32: 25423 bytes
import os.path, sched, sys, threading, random, time, winreg, psutil, pynvml, requests, win32gui
from PyQt5 import QtGui
from PyQt5.QtCore import QPoint, QSettings, QTimer, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QWidget, QMainWindow, QPushButton, QGridLayout, QLabel, QVBoxLayout, QScrollArea, QAction, QMenu, QHBoxLayout, QApplication, QCheckBox
from datetime import datetime
import logging, vmdiff_util
from color_util import isStone, isStoneText, is120PointCount
from computer_util import computerInfo, ping
from more_setting import MoreSettingWin
from more_userinfo import MoreUserInfoWin
from robot_thread import RobotThread
from tools.tall.tall import TallWin
from time_util import getNow
from mouse_util import mouseUtil, MouseInfo
import time_util
from const import API_HOST, API_USERINFO, PerStoneBalance, API_REDUCEBALANCE, AppVersion, BuyTime1, Buy120140, CountDownTime, API_ISCHARGED, Buy120, VmXiaoyao, VmXiaoyaoOtherType, VmLeidian, VmScrcpy, AutoStartTime, API_STONELOG, LastDealTime, LvtongTime12, LvtongTime20, GxTimeMs, GxTimePre, stonePointList, pointList120_5or6
from findstone_thread import FindStoneThread
from stone_util import app_data, toast
from user import dict2User
from vm import VM
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

class IndexWindow(QMainWindow):

    def __init__(self):
        super(IndexWindow, self).__init__()
        self.initClockApm = 500
        self.app_data = QSettings("config.ini", QSettings.IniFormat)
        self.app_data.setIniCodec("UTF-8")
        self.initClockTimer = QTimer()
        self.initClockTimer.timeout.connect(self.initClock)
        self.clockTimer = QTimer()
        self.clockTimer.timeout.connect(self.clockOperate)
        self.mBanlance = 0
        self.mPhone = ""
        self.tipTxt = ""
        self.buyTime = BuyTime1
        self.buyType = Buy120
        self.gxTimeMs = GxTimeMs
        self.moreSettingWin = None
        self.userInfoWin = None
        self.hasStartDeal = False
        self.thread1 = None
        self.thread2 = None
        self.thread3 = None
        self.thread4 = None
        self.thread5 = None
        self.thread6 = None
        self.thread7 = None
        self.thread8 = None
        self.thread9 = None
        self.thread10 = None
        self.thread11 = None
        self.thread12 = None
        self.robotThread1 = None
        self.robotThread2 = None
        self.robotThread3 = None
        self.robotThread4 = None
        self.robotThread5 = None
        self.robotThread6 = None
        self.robotThread7 = None
        self.robotThread8 = None
        self.robotThread9 = None
        self.robotThread10 = None
        self.fightStoneSuccCount = 0
        self.fightStoneFailCount = 0
        self.clickGxTime = None
        self.initUI()
        self.initWaitReduceBalance()
        self.initUserData()
        self.initSetting()
        mouseUtil.mouse_log_singal.connect(self.dLog)
        self.vms = []
        self.selected_vms = []  # user selected devices
        self.openMhVms = []

    def initUI(self):
        self.setFixedSize(750, 520)
        self.setWindowTitle("小石头系统")
        self.setWindowIcon(QIcon(":/logo.ico"))
        fontSize10 = QFont()
        fontSize12 = QFont()
        fontSize14 = QFont()
        fontSize16 = QFont()
        fontSize20 = QFont()
        fontSize10.setPointSize(10)
        fontSize12.setPointSize(12)
        fontSize14.setPointSize(14)
        fontSize16.setPointSize(16)
        fontSize20.setPointSize(20)
        self.main_widget = QWidget()
        self.main_widget.setContentsMargins(2, 2, 2, 2)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        self.console_mine_widget = QWidget()
        self.console_mine_layout = QVBoxLayout()
        self.console_mine_widget.setLayout(self.console_mine_layout)
        self.console_widget = QWidget()
        self.console_widget.setStyleSheet("QWidget{background-color:#E6E6FA;}")
        self.console_layout = QGridLayout()
        self.console_widget.setLayout(self.console_layout)
        self.consoleTitleLabel = QLabel("操作台")
        self.consoleTitleLabel.setFont(fontSize16)
        self.consoleMoreBtn = QPushButton("更多>>", self)
        self.consoleMoreBtn.clicked.connect(self.moreSettingClick)
        self.clockLabel = QLabel("", self)
        self.clockLabel.setFont(fontSize20)
        self.console_radio_widget = QWidget()
        self.console_radio_layout = QGridLayout()
        self.console_radio_widget.setLayout(self.console_radio_layout)
        self.startBtn = QPushButton("启动", self)
        self.startBtn.setFixedSize(60, 60)
        self.startBtn.setStyleSheet("color:white;font-size:14pt;font-family:楷体;background-color:#BB5566EE;border-radius:30px;border:2px groove #5566EE;border-style:outset;")
        self.startBtn.clicked.connect(self.checkBalance)
        self.console_layout.addWidget(self.consoleTitleLabel, 0, 0, 1, 1)
        self.console_layout.addWidget(self.consoleMoreBtn, 0, 1, 1, 1)
        self.console_layout.addWidget(self.clockLabel, 1, 0, 1, 2)
        self.deviceBtn = QPushButton("设备", self)
        self.deviceBtn.setFixedSize(60, 30)
        self.deviceBtn.setStyleSheet("color:#333;font-size:10pt;font-family:楷体;background-color:#E8E8E8;border-radius:5px;border:1px solid #999;")
        self.deviceBtn.clicked.connect(self.showDeviceManager)
        self.console_layout.addWidget(self.startBtn, 2, 1, 1, 1)
        self.console_layout.addWidget(self.deviceBtn, 2, 0, 1, 1)
        self.mine_widget = QWidget()
        self.mine_widget.setStyleSheet("QWidget{background-color:#D4F2E7;}")
        self.mine_layout = QGridLayout()
        self.mine_widget.setLayout(self.mine_layout)
        self.mineTitleLabel = QLabel("我的信息")
        self.mineTitleLabel.setFont(fontSize16)
        self.mineMoreBtn = QPushButton(">>", self)
        self.mineMoreBtn.clicked.connect(self.moreUserInfoClick)
        self.mineRefreshBtn = QPushButton("刷新")
        self.mineRefreshBtn.clicked.connect(self.clickrefreshUserInfo)
        self.phoneLabel = QLabel("手机号:")
        self.balanceLabel = QLabel("余额:")
        self.balanceLabel.setFont(fontSize14)
        self.mine_layout.addWidget(self.mineTitleLabel, 0, 0, 1, 1)
        self.mine_layout.addWidget(self.mineMoreBtn, 0, 1, 1, 1)
        self.mine_layout.addWidget(self.mineRefreshBtn, 1, 0, 1, 2)
        self.mine_layout.addWidget(self.phoneLabel, 2, 0, 1, 2)
        self.mine_layout.addWidget(self.balanceLabel, 3, 0, 1, 2)
        self.console_mine_layout.addWidget(self.console_widget)
        self.console_mine_layout.addWidget(self.mine_widget)
        self.setting_log_widget = QWidget()
        self.setting_log_layout = QVBoxLayout()
        self.setting_log_widget.setLayout(self.setting_log_layout)
        self.curSettingLabel = QLabel("")
        self.curSettingLabel.setStyleSheet("QLabel{color:rgb(225,0,0,255);font-size:14px;font-weight:normal;font-family:Arial;}")
        self.consoleLogWidget = QWidget()
        self.consoleLogWidget.setStyleSheet("QWidget{background-color:#FFF5EE;}")
        self.consoleLogLayout = QVBoxLayout()
        self.consoleLogWidget.setLayout(self.consoleLogLayout)
        self.consoleLogTitleLabel = QLabel("日志")
        self.consoleLogTitleLabel.setFont(fontSize16)
        self.consoleLogBtnLayout = QHBoxLayout()
        self.clearLogBtn = QPushButton("清空")
        self.clearLogBtn.setFixedSize(50, 25)
        self.clearLogBtn.clicked.connect(self.clearLog)
        self.exportLogBtn = QPushButton("导出")
        self.exportLogBtn.setFixedSize(50, 25)
        self.exportLogBtn.clicked.connect(self.exportLog)
        self.logEnableCb = QCheckBox("记录日志")
        self.logEnableCb.setChecked(True)
        self.logEnableCb.setStyleSheet("font-size:9pt;")
        self.consoleLogBtnLayout.addWidget(self.consoleLogTitleLabel)
        self.consoleLogBtnLayout.addStretch()
        self.consoleLogBtnLayout.addWidget(self.logEnableCb)
        self.consoleLogBtnLayout.addWidget(self.clearLogBtn)
        self.consoleLogBtnLayout.addWidget(self.exportLogBtn)
        self.logScrollWidget = QScrollArea()
        self.logScrollWidget.setWidgetResizable(True)
        self.logScrollWidget.setStyleSheet("QScrollArea{border:0px;background-color:#FFF5EE;}")
        self.tipLabel = QLabel("", self)
        self.tipLabel.setFont(fontSize10)
        self.tipLabel.setWordWrap(True)
        self.logScrollWidget.setWidget(self.tipLabel)
        self.logScrollWidget.setMinimumSize(480, 360)
        self.consoleLogLayout.addLayout(self.consoleLogBtnLayout)
        self.consoleLogLayout.addWidget(self.logScrollWidget, 30, Qt.AlignTop | Qt.AlignLeft)
        self.setting_log_layout.addWidget(self.curSettingLabel)
        self.setting_log_layout.addWidget(self.consoleLogWidget)
        self.main_layout.addWidget(self.console_mine_widget)
        self.main_layout.addWidget(self.setting_log_widget)
        self.main_layout.setStretchFactor(self.console_mine_widget, 1)
        self.main_layout.setStretchFactor(self.setting_log_widget, 3)
        self.tallAction = QAction(self)
        self.tallAction.setText("自动喊话(管理员打开软件+梦幻独立窗口)")
        self.tallAction.setFont(fontSize12)
        self.tallAction.triggered.connect(self.showTall)
        self.lvtongAction12 = QAction(self)
        self.lvtongAction12.setText("12点抢绿通(只逍遥)")
        self.lvtongAction12.setFont(fontSize12)
        self.lvtongAction12.triggered.connect(lambda: self.startLvtong(LvtongTime12))
        self.lvtongAction20 = QAction(self)
        self.lvtongAction20.setText("20点抢绿通(只逍遥)")
        self.lvtongAction20.setFont(fontSize12)
        self.lvtongAction20.triggered.connect(lambda: self.startLvtong(LvtongTime20))
        self.openMHAction = QAction(self)
        self.openMHAction.setText("打开梦幻互通并修复(只逍遥)")
        self.openMHAction.setFont(fontSize12)
        self.openMHAction.triggered.connect(self.startMhRepair)
        self.enterMHAction = QAction(self)
        self.enterMHAction.setText("进入游戏(只逍遥)")
        self.enterMHAction.setFont(fontSize12)
        self.enterMHAction.triggered.connect(self.enterMh)
        self.openClockAction = QAction(self)
        self.openClockAction.setText("解锁(密码是1111)(只逍遥)")
        self.openClockAction.setFont(fontSize12)
        self.openClockAction.triggered.connect(self.openClock)
        self.openGxAction = QAction(self)
        self.openGxAction.setText("调出兑换功勋(杨戬61,20)(只逍遥)")
        self.openGxAction.setFont(fontSize12)
        self.openGxAction.triggered.connect(self.openGx)
        self.openPackageAction = QAction(self)
        self.openPackageAction.setText("打开关闭背包(只逍遥)")
        self.openPackageAction.setFont(fontSize12)
        self.openPackageAction.triggered.connect(self.openPackage)
        self.testPingAction = QAction(self)
        self.testPingAction.setText("测试ping")
        self.testPingAction.setFont(fontSize12)
        self.testPingAction.triggered.connect(self.testPing)
        self.testGxAction = QAction(self)
        self.testGxAction.setText("测试点击兑换功勋")
        self.testGxAction.setFont(fontSize12)
        self.testGxAction.triggered.connect(self.testGx)
        self.testFindStoneAction = QAction(self)
        self.testFindStoneAction.setText("测试抢晶石功能")
        self.testFindStoneAction.setFont(fontSize12)
        self.testFindStoneAction.triggered.connect(self.testFindStone)
        self.testCoordAction = QAction(self)
        self.testCoordAction.setText("坐标捕获(点击投屏窗口记录位置)")
        self.testCoordAction.setFont(fontSize12)
        self.testCoordAction.triggered.connect(self.startCoordCapture)
        self.testPreviewAction = QAction(self)
        self.testPreviewAction.setText("预览点击位置(实时显示窗口+坐标框)")
        self.testPreviewAction.setFont(fontSize12)
        self.testPreviewAction.triggered.connect(self.startClickPreview)
        self.testConfirmAction = QAction(self)
        self.testConfirmAction.setText("测试点击确认按钮")
        self.testConfirmAction.setFont(fontSize12)
        self.testConfirmAction.triggered.connect(self.testConfirmClick)
        self.openAutoStartAction = QAction(self)
        self.openAutoStartAction.setText("11:55自动点启动")
        self.openAutoStartAction.setFont(fontSize12)
        self.openAutoStartAction.triggered.connect(self.openAutoStart)
        self.toolsMenu1 = QMenu("&工具箱", self)
        self.toolsMenu2 = QMenu("&便捷操作", self)
        self.toolsMenu3 = QMenu("&测试", self)
        self.toolsMenu1.setStyleSheet("QMenu::item { padding: 10px; border: 1px solid #5566EE}")
        self.toolsMenu2.setStyleSheet("QMenu::item { padding: 10px; border: 1px solid #5566EE}")
        self.toolsMenu3.setStyleSheet("QMenu::item { padding: 10px; border: 1px solid #5566EE}")
        self.menuBar().addMenu(self.toolsMenu2)
        self.menuBar().addMenu(self.toolsMenu3)
        self.menuBar().addMenu(self.toolsMenu1)
        self.menuBar().setFont(fontSize10)
        self.menuBar().setStyleSheet("QMenuBar { background-color: #F0F0F0}")
        self.toolsMenu1.addAction(self.tallAction)
        self.toolsMenu1.addAction(self.lvtongAction12)
        self.toolsMenu1.addAction(self.lvtongAction20)
        self.toolsMenu2.addAction(self.openMHAction)
        self.toolsMenu2.addAction(self.enterMHAction)
        self.toolsMenu2.addAction(self.openClockAction)
        self.toolsMenu2.addAction(self.openGxAction)
        self.toolsMenu2.addAction(self.openAutoStartAction)
        self.toolsMenu3.addAction(self.openPackageAction)
        self.toolsMenu3.addAction(self.testPingAction)
        self.toolsMenu3.addAction(self.testGxAction)
        self.toolsMenu3.addAction(self.testFindStoneAction)
        self.toolsMenu3.addAction(self.testCoordAction)
        self.toolsMenu3.addAction(self.testPreviewAction)
        self.toolsMenu3.addAction(self.testConfirmAction)
        self.statusBar().showMessage("当前版本号:" + str(AppVersion))
        self.clockTimer.start(100)
        self.initClockTimer.start(30000)
        self.initClock()
        self.testPingTime = 0
        self.parentPath = ""


    def testGx(self):
        """测试：点击兑换功勋按钮（使用已绑定设备）"""
        if len(self.selected_vms) > 0:
            test_vms = self.selected_vms
        else:
            self.vms = []
            win32gui.EnumWindows(self.getMHWinList, 0)
            test_vms = self.vms
        if len(test_vms) == 0:
            toast(self, "未检测到设备（请先点击设备绑定）")
            return
        self.dLog("测试兑换功勋：使用" + str(len(test_vms)) + "个设备，直接点击...")
        from mouse_util import mouseUtil, MouseInfo
        from vmdiff_util import VmGxPoint
        import win32gui as _wg, win32api as _wa, win32con as _wc, time as _t
        for vm in test_vms:
            try:
                gx = VmGxPoint(vm.vmType)
                mouseUtil.click(vm.parent, MouseInfo(gx, "兑换功勋"))
                self.dLog("已点击 [" + vm.winName[:10] + "] (" + str(gx.x()) + "," + str(gx.y()) + ")")
            except Exception as e:
                self.dLog("点击失败: " + str(e))
        toast(self, "已对" + str(len(test_vms)) + "个设备执行点击")

    def _getCoordScale(self, hwnd):
        """计算 scrcpy 窗口的坐标缩放比例（基于逍遥模拟器 800x600 标准分辨率）"""
        try:
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            # 逍遥模拟器标准窗口约 800x600，计算缩放
            scale_x = w / 800.0
            scale_y = h / 600.0
            return w, h, scale_x, scale_y
        except:
            return 800, 600, 1.0, 1.0

    def testFindStone(self):
        try:
            if len(self.selected_vms) > 0:
                test_vms = self.selected_vms
            else:
                self.vms = []
                win32gui.EnumWindows(self.getMHWinList, 0)
                test_vms = self.vms
            self.dLog('测试抢晶石：使用' + str(len(test_vms)) + '个设备')
            if len(test_vms) == 0:
                toast(self, '未检测到设备（请先点击设备绑定）')
                return
            import win32api, win32con
            from vmdiff_util import VmGxPoint
            for i, vm in enumerate(test_vms):
                try:
                    if not win32gui.IsWindow(vm.parent):
                        self.dLog('窗口' + str(i+1) + ' 已关闭，跳过')
                        continue
                    w, h, sx, sy = self._getCoordScale(vm.parent)
                    self.dLog('窗口' + str(i+1) + ' 尺寸: ' + str(w) + 'x' + str(h) + ' 缩放: ' + str(round(sx,3)) + 'x' + str(round(sy,3)))
                    if w < 300 or h < 100:
                        self.dLog('窗口' + str(i+1) + ' 尺寸异常，跳过')
                        continue
                    # step1: click gongxun
                    gx = VmGxPoint(vm.vmType)
                    self.dLog('窗口' + str(i+1) + ' 兑换功勋 (' + str(gx.x()) + ',' + str(gx.y()) + ')')
                    win32gui.PostMessage(vm.parent, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, win32api.MAKELONG(gx.x(), gx.y()))
                    time.sleep(0.05)
                    win32gui.PostMessage(vm.parent, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(gx.x(), gx.y()))
                    time.sleep(0.5)
                    # step2: scan crystal
                    screen = QApplication.primaryScreen()
                    img = screen.grabWindow(vm.parent).toImage()
                    found_points = []
                    for point in stonePointList:
                        scaled_x = int(point.x() * sx)
                        scaled_y = int(point.y() * sy)
                        offset = vmdiff_util.VmPointOffset(vm.vmType)
                        check_point = QPoint(scaled_x + offset.x(), scaled_y + offset.y())
                        if isStone(img, check_point):
                            found_points.append(check_point)
                    try:
                        img.save('debug_scan_win' + str(i+1) + '.png')
                    except:
                        pass
                    crystal_points = [pt for pt in found_points if pt.y() > 40]
                    if len(crystal_points) == 0:
                        self.dLog('窗口' + str(i+1) + ' 未发现晶石 (' + str(len(found_points)) + ' candidates)')
                        continue
                    # cluster by x, get center y
                    # 过滤：只保留大色块（>=10个连续命中点）
                    x_groups = {}
                    for pt in crystal_points:
                        x_key = pt.x()
                        if x_key not in x_groups:
                            x_groups[x_key] = []
                        x_groups[x_key].append(pt.y())
                    if len(x_groups) == 0:
                        self.dLog('窗口' + str(i+1) + ' 无命中')
                        continue
                    first_x = sorted(x_groups.keys())[0]
                    y_list = sorted(x_groups[first_x])
                    mid_y = y_list[len(y_list)//2]
                    click_pt = QPoint(first_x, mid_y)
                    self.dLog('窗口' + str(i+1) + ' 晶石 x=' + str(first_x) + ' y=' + str(y_list[0]) + '-' + str(y_list[-1]) + ' click(' + str(click_pt.x()) + ',' + str(click_pt.y()) + ')')
                    # step3: background click crystal
                    win32gui.PostMessage(vm.parent, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, win32api.MAKELONG(click_pt.x(), click_pt.y()))
                    time.sleep(0.05)
                    win32gui.PostMessage(vm.parent, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(click_pt.x(), click_pt.y()))
                    time.sleep(0.5)
                    # step3.5: check price (gold text to the right of crystal)
                    screen2 = QApplication.primaryScreen()
                    img2 = screen2.grabWindow(vm.parent).toImage()
                    # save post-click debug
                    try:
                        img2.save('debug_after_click_win' + str(i+1) + '.png')
                    except:
                        pass
                    gold_count = 0
                    for dy in range(-15, 10):
                        for dx in range(20, 100):
                            try:
                                c = img2.pixelColor(click_pt.x() + dx, click_pt.y() + dy)
                                if c.red() > 150 and c.green() > 100 and c.blue() < 130:
                                    gold_count += 1
                            except:
                                pass
                    selected = gold_count >= 5
                    self.dLog('窗口' + str(i+1) + ' gold=' + str(gold_count) + ' -> ' + ('已选中' if selected else '未选中'))
                    if not selected:
                        continue
                    # step4: background click buy (840,430)
                    buy_x, buy_y = 840, 430
                    self.dLog('窗口' + str(i+1) + ' 购买 (' + str(buy_x) + ',' + str(buy_y) + ')')
                    import win32api, win32con
                    lParam = win32api.MAKELONG(buy_x, buy_y)
                    win32gui.PostMessage(vm.parent, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                    time.sleep(0.05)
                    win32gui.PostMessage(vm.parent, win32con.WM_LBUTTONUP, 0, lParam)
                except Exception as e:
                    self.dLog('窗口' + str(i+1) + ' error: ' + str(e))
                    import traceback
                    traceback.print_exc()
            toast(self, '测试完成，请查看日志')
        except Exception as e:
            toast(self, '测试失败: ' + str(e))
            import traceback
            traceback.print_exc()

    def clearLog(self):
        """清空日志"""
        self.tipLabel.setText("")
        self.tipLabel.setMinimumHeight(0)
        self.dLog("日志已清空")

    def exportLog(self):
        """导出日志到文件"""
        from datetime import datetime
        filename = "log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.tipLabel.text())
            toast(self, "日志已导出到: " + filename)
        except Exception as e:
            toast(self, "导出失败: " + str(e))

    def showDeviceManager(self):
        """显示设备管理窗口 - 可选择绑定设备"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox
        self.vms = []
        win32gui.EnumWindows(self.getMHWinList, 0)
        dlg = QDialog(self)
        dlg.setWindowTitle("设备管理 - 选择要绑定的设备")
        dlg.setMinimumSize(440, 320)
        layout = QVBoxLayout(dlg)
        info = QLabel("检测到 " + str(len(self.vms)) + " 个设备，勾选后点绑定")
        info.setWordWrap(True)
        info.setStyleSheet("color:#333; font-size:11pt; padding:5px;")
        layout.addWidget(info)
        group = QGroupBox("设备列表")
        group_layout = QVBoxLayout(group)
        checkboxes = []
        if len(self.vms) == 0:
            group_layout.addWidget(QLabel("  未检测到设备，请打开模拟器或投屏窗口后点刷新"))
        else:
            selected_refs = set(id(v) for v in self.selected_vms)
            for i, vm in enumerate(self.vms):
                cb = QCheckBox("[" + str(i+1) + "] " + vm.winName + "  (" + vm.vmType + ")")
                cb.setChecked(id(vm) in selected_refs or len(self.selected_vms) == 0)
                cb.vm = vm
                checkboxes.append(cb)
                group_layout.addWidget(cb)
        layout.addWidget(group)
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新设备")
        select_all_btn = QPushButton("全选")
        deselect_all_btn = QPushButton("取消全选")
        bind_btn = QPushButton("绑定选中设备")
        bind_btn.setStyleSheet("QPushButton{color:white;background-color:#5566EE;padding:8px 16px;border-radius:4px;font-weight:bold;}")
        def do_refresh():
            dlg.close()
            self.showDeviceManager()
        def do_select_all():
            for cb in checkboxes:
                cb.setChecked(True)
        def do_deselect_all():
            for cb in checkboxes:
                cb.setChecked(False)
        def do_bind():
            self.selected_vms = [cb.vm for cb in checkboxes if cb.isChecked()]
            dlg.close()
            if len(self.selected_vms) > 0:
                names = ", ".join([v.winName[:10] for v in self.selected_vms[:3]])
                if len(self.selected_vms) > 3:
                    names += " ..."
                toast(self, "已绑定 " + str(len(self.selected_vms)) + " 个设备: " + names)
                self.dLog("设备绑定: " + str(len(self.selected_vms)) + "个 (" + names + ")")
            else:
                toast(self, "未选择任何设备")
                self.selected_vms = []
        refresh_btn.clicked.connect(do_refresh)
        select_all_btn.clicked.connect(do_select_all)
        deselect_all_btn.clicked.connect(do_deselect_all)
        bind_btn.clicked.connect(do_bind)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(bind_btn)
        layout.addLayout(btn_layout)
        dlg.exec_()

    def startCoordCapture(self):
        """坐标捕获模式：在投屏窗口上点击即可记录坐标"""
        from PyQt5.QtWidgets import QMessageBox
        if len(self.selected_vms) > 0:
            cap_vms = self.selected_vms
        else:
            self.vms = []
            win32gui.EnumWindows(self.getMHWinList, 0)
            cap_vms = self.vms
        if len(cap_vms) == 0:
            toast(self, "未检测到设备")
            return
        
        self.dLog("=== 坐标捕获模式开启 ===")
        self.dLog("请在投屏窗口内点击你要获取的位置，按 Ctrl+C 结束")
        self.dLog("窗口尺寸: " + str(len(cap_vms)) + "个设备")
        for i, vm in enumerate(cap_vms):
            rect = win32gui.GetWindowRect(vm.parent)
            w, h = rect[2]-rect[0], rect[3]-rect[1]
            self.dLog("  [" + str(i+1) + "] " + vm.winName + " " + str(w) + "x" + str(h))
        
        self._capture_active = True
        self._capture_vms = cap_vms
        self._capture_timer = QTimer()
        self._capture_timer.timeout.connect(self._doCoordCapture)
        self._capture_timer.start(500)
        toast(self, "坐标捕获已开启，点击投屏窗口记录位置")

    def _doCoordCapture(self):
        """定时检测鼠标点击"""
        import win32api
        try:
            if not hasattr(self, "_capture_active") or not self._capture_active:
                return
            # Check left mouse button
            if win32api.GetAsyncKeyState(0x01) & 0x8000:  # Left button pressed
                if not hasattr(self, "_last_capture_time"):
                    self._last_capture_time = 0
                import time
                now = time.time()
                if now - self._last_capture_time < 1.5:
                    return  # debounce
                self._last_capture_time = now
                
                cursor = win32gui.GetCursorPos()
                for i, vm in enumerate(self._capture_vms):
                    # 用 GetWindowRect 计算相对坐标（与 click 保持一致）
                    rect = win32gui.GetWindowRect(vm.parent)
                    rel_x = cursor[0] - rect[0]
                    rel_y = cursor[1] - rect[1]
                    w, h = rect[2]-rect[0], rect[3]-rect[1]
                    # Also calculate unscaled (800-based) coordinates
                    sx = 800.0 / w if w > 0 else 1.0
                    sy = 600.0 / h if h > 0 else 1.0
                    orig_x = int(rel_x * sx)
                    orig_y = int(rel_y * sy)
                    if 0 <= rel_x <= w and 0 <= rel_y <= h:
                        self.dLog("点击: rel=(" + str(rel_x) + "," + str(rel_y) + ") orig=(" + str(orig_x) + "," + str(orig_y) + ") [" + vm.winName[:10] + "]")
        except Exception as e:
            self.dLog("坐标捕获错误: " + str(e))

    def testConfirmClick(self):
        """测试：单独点击确认按钮（需先打开兑换功勋弹窗）"""
        if len(self.selected_vms) > 0:
            test_vms = self.selected_vms
        else:
            self.vms = []
            win32gui.EnumWindows(self.getMHWinList, 0)
            test_vms = self.vms
        if len(test_vms) == 0:
            toast(self, "未检测到设备")
            return
        from mouse_util import mouseUtil, MouseInfo
        from vmdiff_util import VmBuyPoint
        import win32gui, win32api, win32con, time
        for vm in test_vms:
            try:
                win32gui.SetForegroundWindow(vm.parent)
                time.sleep(0.3)
                buy = VmBuyPoint(vm.vmType)
                mouseUtil.click(vm.parent, MouseInfo(buy, "确认点击(" + str(buy.x()) + "," + str(buy.y()) + ")"))
                self.dLog("已点击确认按钮 (" + str(buy.x()) + "," + str(buy.y()) + ") 在 [" + vm.winName[:10] + "]")
            except Exception as e:
                self.dLog("点击确认失败: " + str(e))
        toast(self, "已执行确认点击")


    def startClickPreview(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
        from PyQt5.QtCore import Qt
        import win32gui as _wg
        
        if len(self.selected_vms) > 0:
            pv_vms = self.selected_vms
        else:
            self.vms = []
            _wg.EnumWindows(self.getMHWinList, 0)
            pv_vms = self.vms
        if len(pv_vms) == 0:
            toast(self, "未检测到设备")
            return
        
        vm = pv_vms[0]
        from vmdiff_util import VmGxPoint, VmBuyPoint
        gx = VmGxPoint(vm.vmType)
        buy = VmBuyPoint(vm.vmType)
        
        screen = QApplication.primaryScreen()
        original_pix = screen.grabWindow(vm.parent)
        
        def draw_markers(pixmap, gx_pt, buy_pt, custom_pt=None):
            painter = QPainter(pixmap)
            pen_g = QPen(QColor(0, 255, 0), 3)
            painter.setPen(pen_g)
            painter.drawRect(gx_pt.x()-12, gx_pt.y()-12, 24, 24)
            pen_r = QPen(QColor(255, 50, 50), 3)
            painter.setPen(pen_r)
            painter.drawRect(buy_pt.x()-12, buy_pt.y()-12, 24, 24)
            pen_y = QPen(QColor(255, 255, 0), 2)
            painter.setPen(pen_y)
            painter.drawLine(gx_pt.x(), gx_pt.y()-18, gx_pt.x(), gx_pt.y()+18)
            painter.drawLine(gx_pt.x()-18, gx_pt.y(), gx_pt.x()+18, gx_pt.y())
            if custom_pt is not None:
                pen_c = QPen(QColor(0, 200, 255), 3)
                painter.setPen(pen_c)
                painter.drawRect(custom_pt.x()-15, custom_pt.y()-15, 30, 30)
                painter.drawLine(custom_pt.x(), custom_pt.y()-20, custom_pt.x(), custom_pt.y()+20)
                painter.drawLine(custom_pt.x()-20, custom_pt.y(), custom_pt.x()+20, custom_pt.y())
            painter.end()
        
        pix = original_pix.copy()
        draw_markers(pix, gx, buy)
        
        dlg = QDialog(self)
        dlg.setWindowTitle("点击位置预览 - " + vm.winName[:20] + "  绿=兑换功勋  红=确认")
        layout = QVBoxLayout(dlg)
        img = QLabel()
        scaled = pix.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img.setPixmap(scaled)
        layout.addWidget(img)
        info = QLabel("绿框: 兑换功勋(" + str(gx.x()) + "," + str(gx.y()) + ")  |  红框: 确认(" + str(buy.x()) + "," + str(buy.y()) + ")")
        info.setStyleSheet("font-size:11pt; padding:5px;")
        layout.addWidget(info)
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("X:"))
        x_edit = QLineEdit()
        x_edit.setFixedWidth(70)
        x_edit.setPlaceholderText("x坐标")
        input_layout.addWidget(x_edit)
        input_layout.addWidget(QLabel("Y:"))
        y_edit = QLineEdit()
        y_edit.setFixedWidth(70)
        y_edit.setPlaceholderText("y坐标")
        input_layout.addWidget(y_edit)
        go_btn = QPushButton("定位")
        input_layout.addWidget(go_btn)
        layout.addLayout(input_layout)
        
        class _CustomPt:
            def __init__(self, x, y):
                self._x = x
                self._y = y
            def x(self):
                return self._x
            def y(self):
                return self._y
        
        def on_locate():
            try:
                cx = int(x_edit.text())
                cy = int(y_edit.text())
                new_pix = original_pix.copy()
                draw_markers(new_pix, gx, buy, _CustomPt(cx, cy))
                new_scaled = new_pix.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(new_scaled)
            except:
                pass
        
        go_btn.clicked.connect(on_locate)
        x_edit.returnPressed.connect(on_locate)
        y_edit.returnPressed.connect(on_locate)
        dlg.exec_()
    def showTall(self):
        self.tallWin = TallWin()
        self.tallWin.show()

    def clockOperate(self):
        self.clockLabel.setText(getNow().strftime("%Y-%m-%d\n%H:%M:%S.%f")[0:-5])

    def initWaitReduceBalance(self):
        waitReduceBanlance = app_data.value("waitReduceBanlance")
        if waitReduceBanlance is not None:
            waitReduceBanlance = int(waitReduceBanlance)
            if waitReduceBanlance > 0:
                self.reduceBalance(waitReduceBanlance, True)

    def initUserData(self):
        self.refreshUserInfo(False)

    def moreSettingClick(self):
        self.moreSettingWin = MoreSettingWin(self.buyTime, self.buyType, self.gxTimeMs, self.geometry().x(), self.geometry().y())
        self.moreSettingWin.buytime_signal.connect(self.selectBuyTime)
        self.moreSettingWin.buytype_signal.connect(self.selectBuyType)
        self.moreSettingWin.gxtimems_signal.connect(self.selectGxTimeMs)
        self.moreSettingWin.show()

    def moreUserInfoClick(self):
        self.userInfoWin = MoreUserInfoWin(self.geometry().x() + self.geometry().width(), self.geometry().y())
        self.userInfoWin.show()

    def initSetting(self):
        self.buyTime = app_data.value("buyTime", BuyTime1)
        self.buyType = app_data.value("buyType", Buy120)
        self.gxTimeMs = app_data.value("gxTimeMs", GxTimeMs)
        self.curSettingLabel.setText("【{}】【{}{}ms】".format(self.buyType, GxTimePre, self.gxTimeMs))

    def selectBuyTime(self, buyT):
        self.buyTime = buyT
        app_data.setValue("buyTime", buyT)

    def selectBuyType(self, buyType):
        self.buyType = buyType
        app_data.setValue("buyType", buyType)
        self.curSettingLabel.setText("【{}】".format(self.buyType))

    def selectGxTimeMs(self, gxTimeMs):
        self.gxTimeMs = gxTimeMs
        app_data.setValue("gxTimeMs", gxTimeMs)
        self.curSettingLabel.setText("【{}】【{}{}ms】".format(self.buyType, GxTimePre, self.gxTimeMs))

    def initClock(self, afterFunc=None):
        s = datetime.now()
        try:
            response = requests.request(url="http://api.pinduoduo.com/api/server/_stm", method="get", timeout=3)
        except Exception:
            # 网络不通时跳过时间同步，不影响主流程
            if afterFunc is not None:
                afterFunc()
            return
        e = datetime.now()
        if response.status_code == 200:
            apm = int((e - s).total_seconds() * 1000)
            logger.debug("请求时间耗时：" + str(apm) + "ms")
            if apm < self.initClockApm or apm < 30:
                curT = response.json()["server_time"] + apm
                sysT = int(datetime.now().timestamp() * 1000)
                time_util.sysTDur = sysT - curT
                self.initClockApm = apm
                logger.debug("采纳的请求时间耗时：" + str(apm) + "ms")
            if afterFunc is not None:
                afterFunc()
        else:
            if afterFunc is not None:
                afterFunc()

    def refreshUserInfo(self, isTip):
        token = app_data.value("token")
        with open("api_debug.log", "a", encoding="utf-8") as log:
            log.write(f"refreshUserInfo token={token[:20]}...\n")
        response = requests.request(url=(API_HOST + API_USERINFO), method="get", headers={'content-type':"application/json", 
         'Authorization':token})
        with open("api_debug.log", "a", encoding="utf-8") as log:
            log.write(f"refreshUserInfo status={response.status_code}\n")
            try:
                log.write(f"refreshUserInfo body={response.json()}\n")
            except:
                log.write(f"refreshUserInfo body_raw={response.text[:200]}\n")
        if response.status_code == 200:
            if response.json()["status"] == "success":
                user = dict2User(response.json()["obj"])
                self.phoneLabel.setText("手机号:{}****".format(user.phone[0:-4]))
                self.balanceLabel.setText("余额:" + str(user.balance) + "小石头")
                self.mPhone = user.phone
                self.mBanlance = user.balance
                if isTip:
                    toast(self, "刷新成功")
            elif self.mBanlance < 5:
                toast(self, "小石头不多了，请提前充值")
            else:
                toast(self, response.json()["msg"] + "请重新打开小石头")
                self.close()
        else:
            toast(self, "网络请求失败,请重新打开小石头")
            self.close()

    def clickrefreshUserInfo(self):
        self.refreshUserInfo(True)

    def checkBalance(self):
        with open("start_debug.log", "a", encoding="utf-8") as log:
            log.write("checkBalance called\n")
        try:
            self.refreshUserInfo(False)
            with open("start_debug.log", "a", encoding="utf-8") as log:
                log.write(f"refresh done, balance={self.mBanlance}\n")
        except Exception as e:
            with open("start_debug.log", "a", encoding="utf-8") as log:
                log.write(f"refresh FAILED: {e}\n")
        self.vms = []
        self.selected_vms = []  # user selected devices
        win32gui.EnumWindows(self.getMHWinList, 0)
        self.dLog("当前几开：{} (绑定{}个)".format(len(self.vms), len(active_vms)))
        waitReduceBanlance = app_data.value("waitReduceBanlance")
        if waitReduceBanlance is not None:
            waitReduceBanlance = int(waitReduceBanlance)
            if waitReduceBanlance > 0:
                toast(self, "未结算故障,请联系")
                return
        elif self.mBanlance >= len(active_vms) * PerStoneBalance:
            self.startBtn.hide()
            self.setupTimerWork()
            toast(self, "启动成功")
            self.uploadLog("启动成功", self.tipTxt)
            self.testPing()
        else:
            maxCountTip = ""
            if self.mBanlance > 0:
                maxCountTip = "(所剩小石头只够{}开抢)".format(int(self.mBanlance / PerStoneBalance))
            toast(self, "启动失败，小石头不足，请联系充值" + maxCountTip)

    def setupTimerWork(self):
        nowTime = getNow()
        startTimerTime = datetime.strptime(str(nowTime.date().year) + "-" + str(nowTime.date().month) + "-" + str(nowTime.date().day) + CountDownTime, "%Y-%m-%d %H:%M:%S.%fZ")
        setup_start_timer = (startTimerTime - nowTime).total_seconds()
        if setup_start_timer < 0:
            self.dLog("当前选择：【{}】【{}{}ms】".format(self.buyType, GxTimePre, self.gxTimeMs))
            self.doTimerWorkPre()
        else:
            self.dLog("当前选择：【{}】【{}{}ms】".format(self.buyType, GxTimePre, self.gxTimeMs))
            self.dLog("提示：将在{}开启30秒倒计时".format(CountDownTime))
            timer = threading.Timer(setup_start_timer, self.doTimerWorkPre)
            timer.start()

    def doTimerWorkPre(self):
        self.initClock(self.doTimerWork)

    def doTimerWork(self):
        nowTime = getNow()
        lastDealTime = datetime.strptime(str(nowTime.date().year) + "-" + str(nowTime.date().month) + "-" + str(nowTime.date().day) + LastDealTime, "%Y-%m-%d %H:%M:%S.%fZ")
        setup_lastdeal_timer = (lastDealTime - nowTime).total_seconds()
        lastDealTimer = threading.Timer(setup_lastdeal_timer, self.doLastDeal)
        lastDealTimer.start()
        if len(self.selected_vms) > 0:
            work_vms = self.selected_vms
        else:
            work_vms = self.vms
        for index in range(len(work_vms)):
            if index == 0:
                self.thread1 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread1.fail_res_signal.connect(self.fightStoneFail)
                self.thread1.succ_res_signal.connect(self.fightStoneSucc)
                self.thread1.log_signal.connect(self.dLog)
                self.thread1.start()
            elif index == 1:
                self.thread2 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread2.fail_res_signal.connect(self.fightStoneFail)
                self.thread2.succ_res_signal.connect(self.fightStoneSucc)
                self.thread2.log_signal.connect(self.dLog)
                self.thread2.start()
            elif index == 2:
                self.thread3 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread3.fail_res_signal.connect(self.fightStoneFail)
                self.thread3.succ_res_signal.connect(self.fightStoneSucc)
                self.thread3.log_signal.connect(self.dLog)
                self.thread3.start()
            elif index == 3:
                self.thread4 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread4.fail_res_signal.connect(self.fightStoneFail)
                self.thread4.succ_res_signal.connect(self.fightStoneSucc)
                self.thread4.log_signal.connect(self.dLog)
                self.thread4.start()
            elif index == 4:
                self.thread5 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread5.fail_res_signal.connect(self.fightStoneFail)
                self.thread5.succ_res_signal.connect(self.fightStoneSucc)
                self.thread5.log_signal.connect(self.dLog)
                self.thread5.start()
            elif index == 5:
                self.thread6 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread6.fail_res_signal.connect(self.fightStoneFail)
                self.thread6.succ_res_signal.connect(self.fightStoneSucc)
                self.thread6.log_signal.connect(self.dLog)
                self.thread6.start()
            elif index == 6:
                self.thread7 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread7.fail_res_signal.connect(self.fightStoneFail)
                self.thread7.succ_res_signal.connect(self.fightStoneSucc)
                self.thread7.log_signal.connect(self.dLog)
                self.thread7.start()
            elif index == 7:
                self.thread8 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread8.fail_res_signal.connect(self.fightStoneFail)
                self.thread8.succ_res_signal.connect(self.fightStoneSucc)
                self.thread8.log_signal.connect(self.dLog)
                self.thread8.start()
            elif index == 8:
                self.thread9 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread9.fail_res_signal.connect(self.fightStoneFail)
                self.thread9.succ_res_signal.connect(self.fightStoneSucc)
                self.thread9.log_signal.connect(self.dLog)
                self.thread9.start()
            elif index == 9:
                self.thread10 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread10.fail_res_signal.connect(self.fightStoneFail)
                self.thread10.succ_res_signal.connect(self.fightStoneSucc)
                self.thread10.log_signal.connect(self.dLog)
                self.thread10.start()
            elif index == 10:
                self.thread11 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread11.fail_res_signal.connect(self.fightStoneFail)
                self.thread11.succ_res_signal.connect(self.fightStoneSucc)
                self.thread11.log_signal.connect(self.dLog)
                self.thread11.start()
            elif index == 11:
                self.thread12 = FindStoneThread(work_vms[index], self.buyTime, self.buyType, self.gxTimeMs)
                self.thread12.fail_res_signal.connect(self.fightStoneFail)
                self.thread12.succ_res_signal.connect(self.fightStoneSucc)
                self.thread12.log_signal.connect(self.dLog)
                self.thread12.start()
            else:
                self.dLog("最多12开")

    def fightStoneFail(self):
        self.fightStoneFailCount += 1
        print("fightStoneFailCount:{} fightStoneSuccCount:{} 虚拟机数量:{}".format(self.fightStoneFailCount, self.fightStoneSuccCount, len(self.vms)))
        if self.fightStoneFailCount + self.fightStoneSuccCount >= len(work_vms):
            if self.hasStartDeal is False:
                self.startDeal(",")

    def fightStoneSucc(self):
        self.fightStoneSuccCount += 1
        print("fightStoneFailCount:{} fightStoneSuccCount:{} 虚拟机数量:{}".format(self.fightStoneFailCount, self.fightStoneSuccCount, self.vms))
        if self.fightStoneFailCount + self.fightStoneSuccCount >= len(work_vms):
            if self.hasStartDeal is False:
                self.startDeal(",")

    def doLastDeal(self):
        if self.hasStartDeal is False:
            self.startDeal(",,")

    def startDeal(self, fromWhere):
        self.hasStartDeal = True
        self.dLog("一共抢{}个晶石{} 消费{}小石头".format(self.fightStoneSuccCount, fromWhere, self.fightStoneSuccCount * PerStoneBalance))
        if self.fightStoneSuccCount > 0:
            self.reduceBalance(self.fightStoneSuccCount * PerStoneBalance, False)
        else:
            print("保存日志1")
            self.saveLog()

    def reduceBalance(self, reduceBalance, isDealWaitRecuceBalance):
        postParam = {'balance':reduceBalance, 
         'wincount':len(self.vms), 
         'buytype':self.buyType}
        token = app_data.value("token")
        response = requests.request(url=(API_HOST + API_REDUCEBALANCE), method="put", json=postParam, headers={'content-type':"application/json", 
         'Authorization':token})
        print(str(response.json()))
        if response.status_code == 200:
            if response.json()["status"] == "success":
                self.dLog("成功结算{}小石头".format(reduceBalance))
                self.refreshUserInfo(False)
                if isDealWaitRecuceBalance:
                    app_data.remove("waitReduceBanlance")
            else:
                toast(self, response.json()["msg"])
                self.dLog("结算{}小石头失败,将在下次结算".format(reduceBalance))
                app_data.setValue("waitReduceBanlance", reduceBalance)
        else:
            toast(self, "网络请求失败")
            self.dLog("结算{}小石头失败,将在下次结算".format(reduceBalance))
            app_data.setValue("waitReduceBanlance", reduceBalance)
        print("保存日志2")
        self.saveLog()

    def getMHWinList(self, hwnd, mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if class_name in (VmXiaoyao, VmXiaoyaoOtherType, VmLeidian, VmScrcpy):
                vmType = class_name
                winName = win32gui.GetWindowText(hwnd)
                controls = []
                win32gui.EnumChildWindows(hwnd, lambda hwnd, param: param.append(hwnd), controls)
                if len(controls) > 0:
                    self.vms.append(VM(vmdiff_util.VmWinType(vmType), winName, hwnd, controls[0]))
                elif vmType == VmScrcpy:
                    self.vms.append(VM(vmdiff_util.VmWinType(vmType), winName, hwnd, hwnd))
                elif vmType in (VmXiaoyao, VmXiaoyaoOtherType):
                    self.vms.append(VM(vmdiff_util.VmWinType(VmScrcpy), winName, hwnd, hwnd))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        nowTime = getNow()
        self.clickGxTime = datetime.strptime(str(nowTime.date().year) + "-" + str(nowTime.date().month) + "-" + str(nowTime.date().day) + GxTimePre + str(self.gxTimeMs) + "Z", "%Y-%m-%d %H:%M:%S.%fZ")
        dur = (nowTime - self.clickGxTime).total_seconds()
        print("nell-closeDuration: {}".format(dur))
        if 0 < dur < 15:
            toast(self, "资源回收中,请等待...")
            event.ignore()
        else:
            event.accept()
            if self.userInfoWin is not None:
                self.userInfoWin.close()
            if self.moreSettingWin is not None:
                self.moreSettingWin.close()
            QApplication.quit()

    def startMhRepair(self):
        self.openMhVms = []
        win32gui.EnumWindows(self.getOpenMHWinList, 0)
        self.startRobotThread("startMhRepair")

    def enterMh(self):
        self.openMhVms = []
        win32gui.EnumWindows(self.getOpenMHWinList, 0)
        self.startRobotThread("enterMh")

    def openClock(self):
        self.openMhVms = []
        win32gui.EnumWindows(self.getOpenMHWinList, 0)
        self.startRobotThread("openClock")

    def openGx(self):
        self.openMhVms = []
        win32gui.EnumWindows(self.getOpenMHWinList, 0)
        self.startRobotThread("openGx")

    def openPackage(self):
        self.openMhVms = []
        win32gui.EnumWindows(self.getOpenMHWinList, 0)
        self.startRobotThread("openPackage")

    def openAutoStart(self):
        if self.startBtn.isVisible() is False:
            return
        nowTime = getNow()
        autoStartTimerTime = datetime.strptime(str(nowTime.date().year) + "-" + str(nowTime.date().month) + "-" + str(nowTime.date().day) + AutoStartTime, "%Y-%m-%d %H:%M:%S.%fZ")
        auto_start_timer_dur = (autoStartTimerTime - nowTime).total_seconds()
        self.dLog("将在" + AutoStartTime + "点击启动，还剩：" + str("%.3f" % auto_start_timer_dur) + "秒，请等待...")
        timer = threading.Timer(auto_start_timer_dur, lambda: self.startBtn.click())
        timer.start()

    def startLvtong(self, constTime):
        self.openMhVms = []
        win32gui.EnumWindows(self.getOpenMHWinList, 0)
        nowTime = getNow()
        autoLvtongTimerTime = datetime.strptime(str(nowTime.date().year) + "-" + str(nowTime.date().month) + "-" + str(nowTime.date().day) + constTime, "%Y-%m-%d %H:%M:%S.%fZ")
        auto_start_timer_dur = (autoLvtongTimerTime - nowTime).total_seconds()
        self.dLog("将在" + constTime + "点击预定，还剩：" + str("%.3f" % auto_start_timer_dur) + "秒，当前" + str(len(self.openMhVms)) + "开，请等待...")
        timer1 = threading.Timer(auto_start_timer_dur, lambda: self.autoLvtong())
        timer1.start()
        self.uploadLog("启动绿通", self.tipTxt)

    def autoLvtong(self):
        self.startRobotThread("lvtongClick")

    def lvtongRes(self, lvLog):
        self.dLog(lvLog)
        self.uploadLog("绿通结果", self.tipTxt)

    def startRobotThread(self, type):
        for index in range(len(self.openMhVms)):
            if index == 0:
                self.robotThread1 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread1.lvtong_signal.connect(self.lvtongRes)
                self.robotThread1.start()
            if index == 1:
                self.robotThread2 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread2.lvtong_signal.connect(self.lvtongRes)
                self.robotThread2.start()
            if index == 2:
                self.robotThread3 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread3.lvtong_signal.connect(self.lvtongRes)
                self.robotThread3.start()
            if index == 3:
                self.robotThread4 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread4.lvtong_signal.connect(self.lvtongRes)
                self.robotThread4.start()
            if index == 4:
                self.robotThread5 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread5.lvtong_signal.connect(self.lvtongRes)
                self.robotThread5.start()
            if index == 5:
                self.robotThread6 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread6.lvtong_signal.connect(self.lvtongRes)
                self.robotThread6.start()
            if index == 6:
                self.robotThread7 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread7.lvtong_signal.connect(self.lvtongRes)
                self.robotThread7.start()
            if index == 7:
                self.robotThread8 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread8.lvtong_signal.connect(self.lvtongRes)
                self.robotThread8.start()
            if index == 8:
                self.robotThread9 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread9.lvtong_signal.connect(self.lvtongRes)
                self.robotThread9.start()
            if index == 9:
                self.robotThread10 = RobotThread(self.openMhVms[index], type, self.parentPath)
                self.robotThread10.lvtong_signal.connect(self.lvtongRes)
                self.robotThread10.start()

    def getOpenMHWinList(self, hwnd, mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if class_name in (VmXiaoyao, VmXiaoyaoOtherType, VmLeidian, VmScrcpy):
                vmType = class_name
                winName = win32gui.GetWindowText(hwnd)
                controls = []
                win32gui.EnumChildWindows(hwnd, lambda hwnd, param: param.append(hwnd), controls)
                if len(controls) > 0:
                    self.openMhVms.append(VM(vmdiff_util.VmWinType(vmType), winName, hwnd, controls[0]))
                elif vmType == VmScrcpy:
                    self.openMhVms.append(VM(vmdiff_util.VmWinType(vmType), winName, hwnd, hwnd))
                elif vmType in (VmXiaoyao, VmXiaoyaoOtherType):
                    self.openMhVms.append(VM(vmdiff_util.VmWinType(VmScrcpy), winName, hwnd, hwnd))

    def dLog(self, tip):
        if tip is None or len(tip) == 0:
            return
        if hasattr(self, "logEnableCb") and not self.logEnableCb.isChecked():
            return
        now = getNow()
        logger.debug(tip)
        self.tipTxt = self.tipTxt + "\n" + now.strftime("%H:%M:%S.%f")[0:-3] + ":" + tip
        self.tipLabel.setText(self.tipTxt)

    def saveLog(self):
        now = getNow()
        content = now.strftime("%Y-%m-%d %H:%M") + "  当前版本V" + str(AppVersion) + computerInfo() + self.tipTxt
        logDir = "log"
        if not os.path.isdir(logDir):
            os.mkdir(logDir)
        with open((logDir + "\\" + now.strftime("%Y-%m-%d %H.%M") + ".txt"), "w", encoding="utf-8") as f:
            f.write(content)
        randomT = float(random.uniform(2, 3))
        timer = threading.Timer(randomT, lambda: self.uploadLog("抢晶石结算", content))
        timer.start()

    def uploadLog(self, type, content):
        postParam = {'app':"stone", 
         'type':type, 
         'phone':self.mPhone, 
         'content':content}
        token = app_data.value("token")
        response = requests.request(url=(API_HOST + API_STONELOG), method="post", json=postParam, headers={'content-type':"application/json", 
         'Authorization':token})
        print(str(response.json()))

    def testPing(self):
        try:
            now = getNow()
            self.testPingTime = 0
            testPingTimer = QTimer()
            self.tipTxt = self.tipTxt + " \n" + now.strftime("%H:%M:%S.%f")[0:-3] + " 测试ping:"
            self.tipLabel.setText(self.tipTxt)
            testPingTimer.timeout.connect(lambda: self.doPing(testPingTimer))
            testPingTimer.start(1000)
        except:
            pass

    def doPing(self, testPingTimer):
        try:
            self.testPingTime += 1
            pingRes = ping("www.baidu.com")
            msList = pingRes[len(pingRes) - 1].split("=")
            self.tipTxt = self.tipTxt + msList[len(msList) - 1].strip() + " "
            self.tipLabel.setText(self.tipTxt)
            if self.testPingTime >= 10:
                testPingTimer.stop()
                toast(self, "测试ping完成")
        except:
            pass


