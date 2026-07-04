# Minimal unit_core for dk_changjing
import functools

def checkStatusOk(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def closePopAndReRunCommonUnit(deviceId, wrapper, bound_args):
    pass

def finalDealException(deviceId):
    pass

def checkLandscape(deviceId):
    pass

def checkUiHang(deviceId):
    pass

def checkNetErrorUI(deviceId):
    pass
