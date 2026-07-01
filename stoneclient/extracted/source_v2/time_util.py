# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: time_util.py
from datetime import datetime, timedelta
sysTDur = 0

def getNow():
    return datetime.now() - timedelta(milliseconds=sysTDur)
