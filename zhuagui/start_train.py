import subprocess
import os

# 切换到 dataset 目录
os.chdir(r'D:\Program Files\mhxy\zhuagui\dataset')

# 启动训练
subprocess.run(['python', r'..\tools\train_final.py'])
