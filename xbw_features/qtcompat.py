# -*- coding: utf-8 -*-
"""
PyQt5 兼容层（纯 Python 实现）

反编译自“小霸王”的代码大量使用 PyQt5 的 QPoint / QColor，合并进本工程后
不希望为此引入整套 PyQt5。这里用纯 Python 实现反编译代码用到的全部接口：

    QPoint: x() / y() / + - * / == / hash
    QColor: red() / green() / blue() / alpha() / ==
"""


class QPoint(object):
    __slots__ = ("_x", "_y")

    def __init__(self, x=0, y=0):
        # PyQt 语义：QPoint 内部为整数，构造时取整
        self._x = int(x)
        self._y = int(y)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def setX(self, x):
        self._x = x

    def setY(self, y):
        self._y = y

    def __add__(self, other):
        return QPoint(self._x + other.x(), self._y + other.y())

    def __sub__(self, other):
        return QPoint(self._x - other.x(), self._y - other.y())

    def __mul__(self, factor):
        return QPoint(self._x * factor, self._y * factor)

    def __truediv__(self, factor):
        return QPoint(self._x / factor, self._y / factor)

    def __eq__(self, other):
        if other is None:
            return False
        try:
            return self._x == other.x() and self._y == other.y()
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._x, self._y))

    def __repr__(self):
        return "QPoint({}, {})".format(self._x, self._y)


class QColor(object):
    __slots__ = ("_r", "_g", "_b", "_a")

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], QColor):
            c = args[0]
            self._r, self._g, self._b, self._a = c._r, c._g, c._b, c._a
        elif len(args) >= 3:
            self._r = int(args[0])
            self._g = int(args[1])
            self._b = int(args[2])
            self._a = int(args[3]) if len(args) > 3 else 255
        elif len(args) == 1 and isinstance(args[0], str):
            s = args[0].lstrip("#")
            self._r = int(s[0:2], 16)
            self._g = int(s[2:4], 16)
            self._b = int(s[4:6], 16)
            self._a = 255
        else:
            self._r = self._g = self._b = 0
            self._a = 255

    def red(self):
        return self._r

    def green(self):
        return self._g

    def blue(self):
        return self._b

    def alpha(self):
        return self._a

    def __eq__(self, other):
        if other is None:
            return False
        return (self._r, self._g, self._b, self._a) == (other.red(), other.green(), other.blue(), other.alpha())

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._r, self._g, self._b, self._a))

    def __repr__(self):
        return "QColor({}, {}, {}, {})".format(self._r, self._g, self._b, self._a)
