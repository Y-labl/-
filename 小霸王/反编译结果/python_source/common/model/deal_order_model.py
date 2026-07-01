# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\deal_order_model.py
import json
from common.model.dk_changjing_config_model import dkChangJingConfig2Json, defaultDKChangJingConfigModelDic
from common.model.gendui_config_model import defaultGenDuiConfigModelDic, genDuiConfig2Json

def dict2DealOrderList(res):
    dealOrderModel = json.loads((json.dumps(res)), object_hook=parseDealOrderList)
    return dealOrderModel


def parseDealOrderList(dct):
    if not dct.get("gendiconfig", False):
        dct["genduiconfig"] = genDuiConfig2Json(defaultGenDuiConfigModelDic)
    if not dct.get("dkchangjingconfig", False):
        dct["dkchangjingconfig"] = dkChangJingConfig2Json(defaultDKChangJingConfigModelDic)
    return DealOrderModel(dct["id"], dct["parth"], dct["type"], dct["phone"], dct["deviceid"], dct["isactive"], dct["expiretime"], dct["isruning"], dct["winname"], dct["baotuconfig"], dct["paoyuconfig"], dct["cwchangjingconfig"], dct["genduiconfig"], dct["dkchangjingconfig"], dct["remark"], dct["funclist"], dct["area"])


class DealOrderModel:

    def __init__(self, id, parth, type, phone, deviceid, isactive, expiretime, isruning, winname, baotuconfig, paoyuconfig, cwchangjingconfig, genduiconfig, dkchangjingconfig, remark, funclist, area):
        self.id = id
        self.parth = parth
        self.type = type
        self.phone = phone
        self.deviceid = deviceid
        self.isactive = isactive
        self.expiretime = expiretime
        self.isruning = isruning
        self.winname = winname
        self.baotuconfig = baotuconfig
        self.paoyuconfig = paoyuconfig
        self.cwchangjingconfig = cwchangjingconfig
        self.genduiconfig = genduiconfig
        self.dkchangjingconfig = dkchangjingconfig
        self.remark = remark
        self.funclist = funclist
        self.area = area

    def toString(self):
        return "DealOrderModel[ id : {}, parth: {}, type: {}, phone: {}, deviceid: {}, isactive: {}, expiretime: {}, isruning: {}, winname: {}, baotuconfig: {}, paoyuconfig: {}, cwchangjingconfig: {}, genduiconfig: {},remark: {}, funclist: {}, area: {}]".format(self.id, self.parth, self.type, self.phone, self.deviceid, self.isactive, self.expiretime, self.isruning, self.winname, self.baotuconfig, self.paoyuconfig, self.cwchangjingconfig, self.genduiconfig, self.remark, self.funclist, self.area)
