# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\eventbus_util.py
from PyQt5.QtCore import QObject
from pyee import EventEmitter
EVENTBUS_ORDER_LIST = "refresh_order_list"
EVENTBUS_ORDER_REMOVE = "remove_order"
EVENTBUS_REFRESH_BALANCE = "refresh_balance"

class EventBusUtil(QObject):

    def __init__(self):
        super().__init__()
        self.eventBus = EventEmitter()


eventBusUtil = EventBusUtil()
