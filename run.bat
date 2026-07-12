@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================
echo   梦幻西游 自动打怪 控制面板
echo ====================================
echo.
echo 正在启动...
echo.
python 小西天自动打怪_GUI.py
pause
