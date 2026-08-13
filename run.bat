@echo off
rem 用 pythonw 启动：不弹出控制台黑框（先显示启动画面，再加载主程序）
cd /d "%~dp0"
start "mhxy" "C:\Users\user\AppData\Local\Programs\Python\Python38\pythonw.exe" "launcher.py"
