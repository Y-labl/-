# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: const.py
API_HOST = "http://111.229.123.236:3000"
API_LOGIN = "/users/login"
API_UPDATE_USERINFO = "/users/userinfo-user"
API_STONELOG = "/stonelog/log"
API_DEALORDER_LIST = "/dealorder/mylist"
API_USERINFO = "/users/userinfo"
API_DEALORDER_CREATE = "/dealorder/create"
API_DEALORDER_INFO = "/dealorder/info"
API_DEALORDER_DELETE = "/dealorder/delete"
API_DEALORDER_UPDATE = "/dealorder/user_update"
API_USER_REDUCEB = "/users/reduceb"
API_VERSIONCONTROL_LIST = "/versioncontrol/list"
SCRCPY_SERVER_PATH = "{}小霸王/_internal/subor.jar"
PingTime = " 00:00:00.000Z"
TYPE_PING = 6
TYPE_BAOTU = 20
TYPE_CW_CHANGJING = 21
TYPE_PAOYU = 22
TYPE_GENDUI = 23
TYPE_DK_CHANGJING = 24
ORDER_TYPE_MAPS = {
 '宝图(2币/天)': 20, 
 '畅玩场景(4币/天)': 21, 
 '跑玉(3币/天)': 22, 
 '跟队(1币/天)': 23, 
 '点卡场景(2币/天)': 24}
REVERSE_ORDER_TYPE_MAPS = {v: k for k, v in ORDER_TYPE_MAPS.items()}
gameType = ""
waitServerT = 6
OpenId = "subor"
AppVersion = 24

# ---- dk_changjing 修正 ----
import os
_THIS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 如果是 dk_changjing\core\original\const.py，则项目根目录是 dk_changjing
# 小霸王项目在上级目录
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
_XBW_ROOT = os.path.join(os.path.dirname(_PROJECT_ROOT), "小霸王", "小霸王")

# 设置游戏类型（默认点卡服）
if not gameType:
    gameType = "点卡服"

# 修正 getParentPath（在 log_util.py 中）
