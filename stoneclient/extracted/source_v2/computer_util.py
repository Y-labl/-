import os
import platform
import winreg
import psutil
import pynvml


def computerInfo():
    info = ""
    try:
        cpuDict = cpu()
        info += "\ncpu名称:" + cpuDict.get("cpu_name", "")
        info += "\t核心数量:" + str(cpuDict.get("cpu_core", ""))
        info += "\t使用率:" + str(cpuDict.get("cpu_percent", "")) + "%"

        gpuDict = gpu()
        if gpuDict:
            info += "\ngpu名称:" + gpuDict.get("gpu_name", "")
            info += "\tgpu数量:" + str(len(gpuDict.get("gpu_count", [])))
            info += "\tgpu显存总量:" + str(gpuDict.get("gpu_memory_total", "")) + "GB"
            info += "\tgpu显存已用:" + str(gpuDict.get("gpu_memory_used", "")) + "GB"
            info += "\tgpu显存剩余:" + str(gpuDict.get("gpu_memory_free", "")) + "GB"

        memDict = memory()
        info += "\n内存总量:" + str(memDict.get("menory_total", "")) + "GB"
        info += "\t内存使用率:" + str(memDict.get("menory_percent", "")) + "%"
        info += "\t内存已用:" + str(memDict.get("menory_used", "")) + "GB"
    except:
        pass
    return info


def cpu():
    return {
        "cpu_name": platform.processor(),
        "cpu_core": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
    }


def bytes_to_gb(b):
    try:
        return round(b / (1024 ** 3), 2)
    except:
        return 0


def gpu():
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        if gpu_count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = pynvml.nvmlDeviceGetName(handle)
            gpu_memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "gpu_name": gpu_name,
                "gpu_count": gpu_count,
                "gpu_memory_total": bytes_to_gb(gpu_memory.total),
                "gpu_memory_used": bytes_to_gb(gpu_memory.used),
                "gpu_memory_free": bytes_to_gb(gpu_memory.free),
            }
    except:
        pass
    return None


def memory():
    vmem = psutil.virtual_memory()
    return {
        "menory_total": bytes_to_gb(vmem.total),
        "menory_percent": vmem.percent,
        "menory_used": bytes_to_gb(vmem.used),
    }


command = "-n 1" if platform.system().lower() == "windows" else "-c 1"


def ping(host):
    response = os.popen(f"ping {command} {host}")
    output = response.readlines()
    return output
