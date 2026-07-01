# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\net_util.py
import json
from concurrent.futures import ThreadPoolExecutor, Future
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG, pyqtSlot, QThread
from PyQt5.QtWidgets import QWidget
from requests import Response
from common.util.adb_util import adbUtil
from common.util.common_util import app_data, toast
from common.util.math_util import plusReduce
from const import API_HOST, API_LOGIN
THREAD_POOL = ThreadPoolExecutor(max_workers=5)

class NetUtil(QObject):
    callback = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def getRequest(self, widget, urlPathQuery, selfUrl=''):
        future = THREAD_POOL.submit(self._do_get, urlPathQuery, selfUrl)
        future.add_done_callback(lambda f: self._NetUtil__backResponse(widget, f.result(), selfUrl))

    def postRequest(self, widget, urlPath, postParam):
        future = THREAD_POOL.submit(self._do_post, urlPath, postParam)
        future.add_done_callback(lambda f: self._NetUtil__backResponse(widget, f.result()))

    def _do_get(self, urlPathQuery, selfUrl) -> Response:
        """实际执行GET请求（线程池内执行）"""
        token = app_data.value("token")
        requestUrl = API_HOST + urlPathQuery
        if selfUrl != "":
            requestUrl = selfUrl
        return requests.request(url=requestUrl,
          method="get",
          headers={'content-type':"application/json", 
         'Authorization':token})

    def _do_post(self, urlPath, postParam) -> Response:
        """实际执行POST请求（线程池内执行）"""
        token = app_data.value("token")
        response = requests.request(url=(API_HOST + urlPath),
          method="post",
          json={"data": (plusReduce(json.dumps(postParam)))},
          headers={'content-type':"application/json", 
         'Authorization':token})
        if API_LOGIN == urlPath:
            adbUtil.getDeviceModels()
        return response

    def __backResponse(self, widget, response, selfUrl=''):
        if response.status_code == 200:
            if selfUrl == "":
                responseJson = json.loads(plusReduce(response.json()["data"]))
                if responseJson["status"] == "success":
                    self.callback.emit(responseJson)
            elif widget is not None:
                QMetaObject.invokeMethod(self, "_show_toast_safe", Qt.QueuedConnection, Q_ARG(object, widget), Q_ARG(str, responseJson["msg"]))
            else:
                self.callback.emit(response.json())
        else:
            if widget is not None:
                toast(widget, "网络请求失败")

    @pyqtSlot(object, str)
    def _show_toast_safe(self, widget, msg):
        """主线程安全执行toast（由信号/invokeMethod触发）"""
        toast(widget, msg)
