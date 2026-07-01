# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: user.py
# Compiled at: 2026-07-01 07:28:41
# Size of source mod 2**32: 565 bytes
import json

def dict2User(res):
    return json.loads((json.dumps(res)), object_hook=User)


class User(object):

    def __init__(self, dict_):
        self.__dict__.update(dict_)
