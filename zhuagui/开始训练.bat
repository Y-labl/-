@echo off
chcp 65001 >nul
echo ============================================================
echo 训练 YOLOv8 - 抓鬼任务 NPC 识别
echo ============================================================
echo.
echo 数据集：97 张图片，7 个类别
echo 配置：10 epochs（测试），batch=4, imgsz=640
echo 预计时间：10-15 分钟
echo.
echo 按任意键开始训练...
pause >nul
echo.

cd /d "%~dp0dataset"
python ..\tools\train_local_test.py

echo.
echo 训练结束！
echo 按任意键退出...
pause >nul
