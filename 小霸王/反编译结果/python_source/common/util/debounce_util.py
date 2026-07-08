
from PyQt5.QtCore import QTimer
import functools

def qt_debounce_with_cancel(delay_ms=600, cancel_attrs=None):
    cancel_attrs = cancel_attrs or []
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def qt_debounce(delay_ms=300):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
