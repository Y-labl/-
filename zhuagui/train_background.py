import subprocess
import os

# 设置环境变量
env = os.environ.copy()
env['POLARS_SKIP_CPU_CHECK'] = '1'
env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 切换到 dataset 目录
os.chdir(r'D:\Program Files\mhxy\zhuagui\dataset')

# 启动训练
subprocess.Popen([
    'yolo', 'task=detect', 'mode=train', 'model=yolov8n.pt',
    'data=data.yaml', 'epochs=100', 'batch=8', 'imgsz=640',
    'workers=0', 'project=../trained_model', 'name=zhuagui_v1',
    'plots=False', 'verbose=True'
], env=env)

print("训练已在后台启动...")
print("请等待训练完成，预计需要 30-60 分钟")
