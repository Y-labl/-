import json

class DKChangJingConfigModel:
    def __init__(self):
        self.isDuiZhang = True
        self.isZhua = False
        self.isTou = False
        self.isPkJiNeng = False
        self.isPkPuGong = False
        self.isPkTaoPao = False
        self.isPkAuto = True
        self.roleAddXueMode = "不使用"
        self.roleAddLanMode = "不使用"
        self.bbAddXueMode = "不使用"
        self.bbAddLanMode = "不使用"

def json2DKChangJingConfigModel(jsonStr):
    config = DKChangJingConfigModel()
    if jsonStr:
        try:
            data = json.loads(jsonStr)
            for k, v in data.items():
                if hasattr(config, k):
                    setattr(config, k, v)
        except:
            pass
    return config
