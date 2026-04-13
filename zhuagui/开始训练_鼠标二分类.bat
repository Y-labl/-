@echo off
chcp 65001 >nul
echo 训练 YOLOv8：钟馗+鼠标（2 类），数据 yolo_dataset（标签须已 remap 为 0/1）
echo 若未执行过 remap，请先：python tools\backup_remap_yolo_2class.py
echo.
cd /d "%~dp0"
python tools\train_mouse_2c.py
pause
