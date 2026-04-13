@echo off
chcp 65001 >nul
echo ============================================================
echo 训练 YOLOv8 - 抓鬼任务 NPC 识别（完整版 100 轮）
echo ============================================================
echo.
echo 数据集：annotation_100 共 100 张（请先 inject_mouse_only 再训可含鼠标 class6）
echo 配置：100 epochs, batch=8, imgsz=640
echo 预计时间：1-2 小时
echo.
echo 警告：请确保电脑散热良好！
echo.
echo 按任意键开始训练...
pause >nul
echo.

cd /d "%~dp0dataset"
python ..\tools\train_local_full.py

echo.
echo 训练结束！
echo 按任意键退出...
pause >nul
