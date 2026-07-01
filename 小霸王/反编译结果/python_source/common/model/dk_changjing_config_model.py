# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\dk_changjing_config_model.py
import json

def json2DKChangJingConfigModel(jsonStr):
    dkChangJingConfigModel = json.loads(jsonStr, object_hook=DKChangJingConfigModel)
    if hasattr(dkChangJingConfigModel, "roleAddXueMode") is False:
        dkChangJingConfigModel.roleAddXueMode = defaultDKChangJingConfigModelDic["roleAddXueMode"]
    if hasattr(dkChangJingConfigModel, "roleAddLanMode") is False:
        dkChangJingConfigModel.roleAddLanMode = defaultDKChangJingConfigModelDic["roleAddLanMode"]
    if hasattr(dkChangJingConfigModel, "roleXuePercent") is False:
        dkChangJingConfigModel.roleXuePercent = defaultDKChangJingConfigModelDic["roleXuePercent"]
    if hasattr(dkChangJingConfigModel, "roleLanPercent") is False:
        dkChangJingConfigModel.roleLanPercent = defaultDKChangJingConfigModelDic["roleLanPercent"]
    if hasattr(dkChangJingConfigModel, "isZhua") is False:
        dkChangJingConfigModel.isZhua = defaultDKChangJingConfigModelDic["isZhua"]
    if hasattr(dkChangJingConfigModel, "isTou") is False:
        dkChangJingConfigModel.isTou = defaultDKChangJingConfigModelDic["isTou"]
    if hasattr(dkChangJingConfigModel, "isPkJiNeng") is False:
        dkChangJingConfigModel.isPkJiNeng = defaultDKChangJingConfigModelDic["isPkJiNeng"]
    if hasattr(dkChangJingConfigModel, "isPkPuGong") is False:
        dkChangJingConfigModel.isPkPuGong = defaultDKChangJingConfigModelDic["isPkPuGong"]
    if hasattr(dkChangJingConfigModel, "isPkFangYu") is False:
        dkChangJingConfigModel.isPkFangYu = defaultDKChangJingConfigModelDic["isPkFangYu"]
    if hasattr(dkChangJingConfigModel, "isPkAuto") is False:
        dkChangJingConfigModel.isPkAuto = defaultDKChangJingConfigModelDic["isPkAuto"]
    if hasattr(dkChangJingConfigModel, "isPkTaoPao") is False:
        dkChangJingConfigModel.isPkTaoPao = defaultDKChangJingConfigModelDic["isPkTaoPao"]
    if hasattr(dkChangJingConfigModel, "isDuiZhang") is False:
        dkChangJingConfigModel.isDuiZhang = defaultDKChangJingConfigModelDic["isDuiZhang"]
    return dkChangJingConfigModel


def dkChangJingConfig2Json(obj):
    dkChangJingConfig = json.dumps(obj, cls=DKChangJingConfigEncoder, indent=4, ensure_ascii=False)
    dkChangJingConfig = dkChangJingConfig.replace("\n", "").replace("\r", "")
    return dkChangJingConfig


class DKChangJingConfigModel:

    def __init__(self, dict_):
        self.__dict__.update(dict_)


defaultDKChangJingConfigModelDic = {
 'roleAddXueMode': '"秘制"', 
 'roleAddLanMode': '"秘制"', 
 'roleXuePercent': '"30"', 
 'roleLanPercent': '"30"', 
 'isZhua': False, 
 'isTou': False, 
 'isPkJiNeng': False, 
 'isPkPuGong': False, 
 'isPkFangYu': False, 
 'isPkAuto': False, 
 'isPkTaoPao': False, 
 'isDuiZhang': True}

class DKChangJingConfigEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")
        if isinstance(obj, int):
            return int(obj)
        if isinstance(obj, float):
            return float(obj)
        if isinstance(obj, DKChangJingConfigModel):
            return obj.__dict__
        return super(DKChangJingConfigEncoder, self).default(obj)
