
from PyQt5.QtCore import QThread, QPoint
from loguru import logger
from common.model.cw_changjing_config_model import json2CWChangJingConfigModel
from common.util.click_util import click
from common.util.color_util import getColorFromFrame, isWhiteTextColor
from common.util.detect_position_util import detectPosition
from common.util.img_util import findPic, isInPk, findFourPersonAndClick, isShowFourPerson
from common.util.scrcpy_util import scrcpyUtil
from cw_changjing.cw_changjing_util import randomClickMap
from game_action.map_action import goToPositionAction, getMapParams, goToMapAction
from game_action.unit import clickOpenMap, closePop

class CWChangJingThread(QThread):
    def __init__(self):
        super().__init__()
        self.dealOrder = None
        self.isRunning = False
    
    def setDealOrder(self, order):
        self.dealOrder = order
    
    def run(self):
        self.isRunning = True
        while self.isRunning:
            self.msleep(1000)
    
    def stop(self):
        self.isRunning = False
    
    def startDuiZhang(self):
        pass
