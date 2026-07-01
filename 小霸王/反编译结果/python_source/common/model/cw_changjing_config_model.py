# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\cw_changjing_config_model.py
import json

def json2CWChangJingConfigModel(jsonStr):
    cWChangJingConfigModel = json.loads(jsonStr, object_hook=CWChangJingConfigModel)
    return cWChangJingConfigModel


def cWChangJingConfig2Json(obj):
    cWChangJingConfig = json.dumps(obj, cls=CWChangJingConfigEncoder, indent=4, ensure_ascii=False)
    cWChangJingConfig = cWChangJingConfig.replace("\n", "").replace("\r", "")
    return cWChangJingConfig


class CWChangJingConfigModel:

    def __init__(self, dict_):
        self.__dict__.update(dict_)


defaultCWChangJingConfigModelDic = {"isDuiZhang": False}

class CWChangJingConfigEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")
        if isinstance(obj, int):
            return int(obj)
        if isinstance(obj, float):
            return float(obj)
        if isinstance(obj, CWChangJingConfigModel):
            return obj.__dict__
        return super(CWChangJingConfigEncoder, self).default(obj)
