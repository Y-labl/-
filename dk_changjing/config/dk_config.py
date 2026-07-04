# -*- coding: utf-8 -*-
"""点卡场景配置模型（参照原版 dk_changjing_config_model.py）

原版默认配置:
  roleAddXueMode: "秘制", roleAddLanMode: "秘制"
  roleXuePercent: 30, roleLanPercent: 30
  isZhua: False, isTou: False
  isPkJiNeng: False, isPkPuGong: False, isPkFangYu: False, isPkAuto: False, isPkTaoPao: False
  isDuiZhang: True
  注意: 原版没有 isWuYi 配置项，checkWuYi 无条件执行。新项目增加 is_wuyi 开关。
"""
import json, os

ADD_XUE_MODES = ["秘制", "红碗", "酒肆"]
ADD_LAN_MODES = ["秘制", "蓝碗", "酒肆"]

class DKConfig:
    def __init__(self, data=None):
        d = data or {}
        self.role_add_xue_mode = d.get("role_add_xue_mode", "秘制")
        self.role_add_lan_mode = d.get("role_add_lan_mode", "秘制")
        self.role_xue_percent = int(d.get("role_xue_percent", 30))
        self.role_lan_percent = int(d.get("role_lan_percent", 30))
        self.is_zhua = d.get("is_zhua", False)
        self.is_tou = d.get("is_tou", False)
        self.is_pk_jineng = d.get("is_pk_jineng", False)
        self.is_pk_pugong = d.get("is_pk_pugong", False)
        self.is_pk_fangyu = d.get("is_pk_fangyu", False)
        self.is_pk_auto = d.get("is_pk_auto", True)  # 新项目默认开启自动战斗
        self.is_pk_taopao = d.get("is_pk_taopao", False)
        self.is_duizhang = d.get("is_duizhang", True)
        self.is_wuyi = d.get("is_wuyi", False)  # 新增: 原版无此配置, checkWuYi 无条件执行

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, s):
        return cls(json.loads(s))

    @classmethod
    def load(cls, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls.from_json(f.read())
        except: return cls()

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
