# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\baotu_config_model.py
import json

def json2BaoTuConfigModel(jsonStr):
    baoTuConfigModel = json.loads(jsonStr, object_hook=BaoTuConfigModel)
    return baoTuConfigModel


def baoTuConfig2Json(obj):
    baoTuConfig = json.dumps(obj, cls=BaoTuConfigEncoder, indent=4, ensure_ascii=False)
    baoTuConfig = baoTuConfig.replace("\n", "").replace("\r", "")
    return baoTuConfig


class BaoTuConfigModel:

    def __init__(self, dict_):
        self.__dict__.update(dict_)


defaultBaoTuConfigModelDic = {"isWaQiLinShan": False}

class BaoTuConfigEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")
        if isinstance(obj, int):
            return int(obj)
        if isinstance(obj, float):
            return float(obj)
        if isinstance(obj, BaoTuConfigModel):
            return obj.__dict__
        return super(BaoTuConfigEncoder, self).default(obj)
