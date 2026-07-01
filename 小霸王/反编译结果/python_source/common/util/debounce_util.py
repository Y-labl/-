# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\debounce_util.py
from PyQt5.QtCore import QTimer
import functools

def qt_debounce_with_cancel(delay_ms=600, cancel_attrs=None):
    """
    Qt防抖+取消请求 增强装饰器 - 修复所有报错：
    1. TypeError: disconnect() failed 无连接报错
    2. AttributeError: 无receivers属性报错
    :param delay_ms: 防抖延迟时间，默认300ms
    :param cancel_attrs: 需要取消的请求对象属性名列表，如["netUtil1", "netUtil2"]
    """
    cancel_attrs = cancel_attrs or []

    def decorator(func):

        @functools.wraps(func)
        def wrapperParse error at or near `LOAD_STR' instruction at offset 0

        return wrapper

    return decorator


def qt_debounce(delay_ms=300):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            debounce_timer_attr = f"_debounce_timer_{func.__name__}"
            if not hasattrselfdebounce_timer_attr:
                timer = QTimer(self)
                timer.setSingleShot(True)
                setattrselfdebounce_timer_attrtimer
            debounce_timer = getattrselfdebounce_timer_attr
            try:
                debounce_timer.timeout.disconnect
            except (TypeError, AttributeError):
                pass
            else:

                def real_call():
                    func(self, *args, **kwargs)

                debounce_timer.timeout.connect(real_call)
                debounce_timer.start(delay_ms)

        return wrapper

    return decorator