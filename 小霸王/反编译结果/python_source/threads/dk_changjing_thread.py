
from PyQt5.QtCore import QThread, QPoint
from PyQt5.QtGui import QColor
from loguru import logger
from common.model.dk_changjing_config_model import json2DKChangJingConfigModel
from common.util.click_util import click
from common.util.color_util import getColorFromFrame, isNeedWuYiColor, isPointColor, isShowPopColorDK, isWhiteTextColor
from common.util.detect_position_util import detectPosition
from common.util.img_util import checkAtDaoJu, findPic, findPics, isInPk, findFourPersonAndClick, isShowFourPerson, waitAssertFuncOk, waitAssertImgOk
from common.util.math_util import distance_between_points
from common.util.scrcpy_util import scrcpyUtil
from cw_changjing.cw_changjing_util import randomClickMap, randomClickMap_CiChouZhiLu
from game_action.common_action_logic import findNpcAndClickLogic, hideTaskAndChanel
from game_action.map_action import goToPositionAction, getMapParams, goToMapAction
from game_action.unit import clickClosePkg, clickOpenMap, clickOpenPkg, closePop, doubleClickProduct

class DKChangJingThread(QThread):
    def __init__(self):
        super().__init__()
        self.dealOrder = None
    
    def setDealOrder(self, order):
        self.dealOrder = order
    
    def run(self):
        pass
    
    def stop(self):
        pass
    
    def startDuiZhang(self):
        pass
    
    def toutouDoOverCheck(self):
        pass
    
    def checkXueLan(self):
        pass
    
    def checkWuYi(self):
        pass
    
    def findSideTargetPoints(self):
        pass
