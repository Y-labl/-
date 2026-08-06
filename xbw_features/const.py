# -*- coding: utf-8 -*-
"""小霸王三功能合并包常量（路径指向本工程）。"""
import os as _os

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

_BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
PROJECT_DIR = _os.path.dirname(_BASE_DIR)          # D:\mhxy-auto-fight
FOURPERSON_CNN_PATH = _os.path.join(_BASE_DIR, "_internal", "subor.onnx")
SCRCPY_SERVER_PATH = _os.path.join(_BASE_DIR, "_internal", "subor.jar")
SCRCPY_PATH = _os.path.join(PROJECT_DIR, "scrcpy", "scrcpy.exe")

# findPic 模板搜索目录（本项目 image/ 与 images/，兼容原“逻辑素材”目录）
TEMPLATE_DIRS = [
    _os.path.join(PROJECT_DIR, "image"),
    _os.path.join(PROJECT_DIR, "images"),
    _os.path.join(PROJECT_DIR, "_decompiled", "final", "逻辑素材"),
    _os.path.join(PROJECT_DIR, "逻辑素材"),
]

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
gameType = "点卡服"
waitServerT = 6
isSanXing = False
OpenId = "subor"
AppVersion = 41

# 图灵云 API 配置（四小人网络识别兜底；与本工程 mhxy_engine 的账号保持一致）
TULING_API_URL = "http://www.tulingcloud.com/tuling/predict"
TULING_AUTH = {
    "username": "yqning5",
    "password": "sai+123",
    "ID": 48117555,
    "version": "3.1.1",
}
