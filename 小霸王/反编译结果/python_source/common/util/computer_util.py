# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: common\util\computer_util.py
import os, platform, winreg, psutil, pynvml

def computerInfo():
    info = ""
    try:
        cpuDict = cpu()
        info += "\ncpu名称:" + cpuDict.get("cpu_name")
        info += "\t核心数量:" + str(cpuDict.get("cpu_core"))
        info += "\t使用率:" + str(cpuDict.get("cpu_avg")) + "%"
        gpuDict = gpu()
        if gpuDict is not None:
            info += "\ngpu名称:" + gpuDict.get("gpu_name")
            info += "\t数量:" + str(gpuDict.get("gpu_count"))
            info += "\t内存大小:" + str(gpuDict.get("gpu_memory_total"))
            info += "\t已使用:" + str(gpuDict.get("gpu_memory_used"))
        memoryDict = memory()
        info += "\n内存总量:" + str(memoryDict.get("menory_total"))
        info += "\t已使用:" + str(memoryDict.get("menory_used"))
        info += "\t使用率:" + str(memoryDict.get("menory_percent")) + "%\n"
    except:
        pass
    else:
        return info


def cpu():
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0")
    cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")
    key.Close()
    data = dict(cpu_name=(cpu_name[0]),
      cpu_core=(psutil.cpu_count(False)),
      cpu_avg=(psutil.cpu_percent(1)))
    return data


def bytes_to_gb(sizes):
    sizes = round(sizes / 1073741824, 2)
    return f"{sizes} GB"


def gpuParse error at or near `SETUP_FINALLY' instruction at offset 0


def memory():
    data = dict(menory_total=(bytes_to_gb(psutil.virtual_memory().total)),
      menory_percent=(psutil.virtual_memory().percent),
      menory_used=(bytes_to_gb(psutil.virtual_memory().used)))
    return data


command = "-n 1" if platform.system().lower() == "windows" else "-c 1"

def ping(host):
    response = os.popen(f"ping {command} {host}")
    output = response.readlines()
    return output