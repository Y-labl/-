import os
os.chdir(r'D:\Program Files\mhxy\zhuagui\dataset')
os.system('yolo task=detect mode=train model=yolov8n.pt data=data.yaml epochs=100 batch=8 imgsz=640 workers=0 project=../trained_model name=zhuagui_v1 plots=False verbose=True')
