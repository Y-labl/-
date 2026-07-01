# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: balance_record.py
# Compiled at: 2026-07-01 07:28:44
# Size of source mod 2**32: 911 bytes
import json

def dict2BalanceRecordList(res):
    return json.loads((json.dumps(res)), object_hook=parseBalanceRecordList)


def parseBalanceRecordList(dct):
    return BalanceRecord(dct["balance"], dct["type"], dct["createdAt"], dct["wincount"], dct["buytype"], dct["rmb"], dct["userbalance"])


class BalanceRecord:

    def __init__(self, balance, type, createdAt, wincount, buytype, rmb, userbalance):
        self.balance = balance
        self.type = type
        self.createdAt = createdAt
        self.wincount = wincount
        self.buytype = buytype
        self.rmb = rmb
        self.userbalance = userbalance
