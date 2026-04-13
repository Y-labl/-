import subprocess
import os

os.chdir(r'D:\Program Files\mhxy\zhuagui\dataset')
subprocess.run(['python', r'..\tools\train_local_test.py'])
