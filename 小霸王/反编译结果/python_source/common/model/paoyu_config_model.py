# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\paoyu_config_model.py
import json

def json2PaoYuConfigModel(jsonStr):
    paoYuConfigModel = json.loads(jsonStr, object_hook=PaoYuConfigModel)
    return paoYuConfigModel


def paoYuConfig2Json(obj):
    paoYuConfig = json.dumps(obj, cls=PaoYuConfigEncoder, indent=4, ensure_ascii=False)
    paoYuConfig = paoYuConfig.replace("\n", "").replace("\r", "")
    return paoYuConfig


class PaoYuConfigModel:

    def __init__(self, dict_):
        self.__dict__.update(dict_)


defaultPaoYuConfigModelDic = {"isWaQiLinShan": False}

class PaoYuConfigEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")
        if isinstance(obj, int):
            return int(obj)
        if isinstance(obj, float):
            return float(obj)
        if isinstance(obj, PaoYuConfigModel):
            return obj.__dict__
        return super(PaoYuConfigEncoder, self).default(obj)
