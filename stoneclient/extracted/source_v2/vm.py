# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.10
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: vm.py


class VM:

    def __init__(self, vmType, winName, parent, child):
        self.vmType = vmType
        self.winName = winName
        self.parent = parent
        self.child = child
