# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\model\version_control_model.py
import json

def dict2VersionControlList(res):
    versionControlModel = json.loads((json.dumps(res)), object_hook=parseVersionControlList)
    return versionControlModel


def parseVersionControlList(dct):
    return VersionControlModel(dct["id"], dct["openId"], dct["version"], dct["newVersion"], dct["forceVersion"], dct["content"], dct["downloadUrl"], dct["config"], dct["moreConfig"])


class VersionControlModel:

    def __init__(self, id, openId, version, newVersion, forceVersion, content, downloadUrl, config, moreConfig):
        self.id = id
        self.openId = openId
        self.version = version
        self.newVersion = newVersion
        self.forceVersion = forceVersion
        self.content = content
        self.downloadUrl = downloadUrl
        self.config = config
        self.moreConfig = moreConfig
