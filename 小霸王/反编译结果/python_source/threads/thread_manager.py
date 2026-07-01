# decompyle3 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: threads\thread_manager.py
from const import TYPE_BAOTU, TYPE_PAOYU, TYPE_CW_CHANGJING, TYPE_GENDUI, TYPE_DK_CHANGJING
from threads.baotu_thread import BaoTuThread
from threads.cw_changjing_thread import CWChangJingThread
from threads.dk_changjing_thread import DKChangJingThread
from threads.gendui_thread import GenDuiThread
from threads.paoyu_thread import PaoYuThread

class ThreadManager(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = (object.__new__)(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.baoTuThreads = []
        self.paoYuThreads = []
        self.cwChangJingThreads = []
        self.dkChangJingThreads = []
        self.genDuiThreads = []

    def startThread(self, dealOrder):
        targetThread = None
        if dealOrder.type == TYPE_BAOTU:
            targetThread = self.getBaoTuThreadWithNew(dealOrder)
        elif dealOrder.type == TYPE_PAOYU:
            targetThread = self.getPaoYuThreadWithNew(dealOrder)
        elif dealOrder.type == TYPE_CW_CHANGJING:
            targetThread = self.getCWChangJingThreadWithNew(dealOrder)
        elif dealOrder.type == TYPE_GENDUI:
            targetThread = self.getGenDuiThreadWithNew(dealOrder)
        elif dealOrder.type == TYPE_DK_CHANGJING:
            targetThread = self.getDKChangJingThreadWithNew(dealOrder)
        if targetThread:
            targetThread.setDealOrder(dealOrder)
            targetThread.start()

    def getBaoTuThreadWithNew(self, dealOrder):
        for thread in self.baoTuThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread
            newThread = BaoTuThread()
            self.baoTuThreads.append(newThread)
            return newThread

    def getBaoTuThreadWithoutNew(self, dealOrder):
        for thread in self.baoTuThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread

    def getPaoYuThreadWithNew(self, dealOrder):
        for thread in self.paoYuThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread
            newThread = PaoYuThread()
            self.paoYuThreads.append(newThread)
            return newThread

    def getPaoYuThreadWithoutNew(self, dealOrder):
        for thread in self.paoYuThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread

    def getCWChangJingThreadWithNew(self, dealOrder):
        for thread in self.cwChangJingThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread
            newThread = CWChangJingThread()
            self.cwChangJingThreads.append(newThread)
            return newThread

    def getCWChangJingThreadWithoutNew(self, dealOrder):
        for thread in self.cwChangJingThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread

    def getDKChangJingThreadWithNew(self, dealOrder):
        for thread in self.dkChangJingThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread
            newThread = DKChangJingThread()
            self.dkChangJingThreads.append(newThread)
            return newThread

    def getDKChangJingThreadWithoutNew(self, dealOrder):
        for thread in self.dkChangJingThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread

    def getGenDuiThreadWithNew(self, dealOrder):
        for thread in self.genDuiThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread
            newThread = GenDuiThread()
            self.genDuiThreads.append(newThread)
            return newThread

    def getGenDuiThreadWithoutNew(self, dealOrder):
        for thread in self.genDuiThreads:
            if thread.dealOrder.id == dealOrder.id:
                return thread


threadManager = ThreadManager()
