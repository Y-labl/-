# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\gendui_config_model.py
import json

def json2GenDuiConfigModel(jsonStr):
    genDuiConfigModel = json.loads(jsonStr, object_hook=GenDuiConfigModel)
    return genDuiConfigModel


def genDuiConfig2Json(obj):
    genDuiConfig = json.dumps(obj, cls=GenDuiConfigEncoder, indent=4, ensure_ascii=False)
    genDuiConfig = genDuiConfig.replace("\n", "").replace("\r", "")
    return genDuiConfig


class GenDuiConfigModel:

    def __init__(self, dict_):
        self.__dict__.update(dict_)


defaultGenDuiConfigModelDic = {
 'roleAddXueMode': '"秘制"', 
 'roleAddLanMode': '"秘制"', 
 'roleXuePercent': '"50"', 
 'roleLanPercent': '"50"'}

class GenDuiConfigEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")
        if isinstance(obj, int):
            return int(obj)
        if isinstance(obj, float):
            return float(obj)
        if isinstance(obj, GenDuiConfigModel):
            return obj.__dict__
        return super(GenDuiConfigEncoder, self).default(obj)
