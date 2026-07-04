# -*- coding: utf-8 -*-
"""日志工具"""
import os

class LogUtil:
    def __init__(self):
        self._parent_path = None
    def getParentPath(self):
        if self._parent_path:
            return self._parent_path
        current = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):
            current = os.path.dirname(current)
        # Return with trailing separator for direct concatenation
        self._parent_path = current + os.sep
        return self._parent_path

logUtil = LogUtil()
