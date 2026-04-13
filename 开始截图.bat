@echo off
chcp 65001 >nul
echo ==================================================
echo 梦幻西游 NPC 截图工具
echo ==================================================
echo.
cd /d "D:\Program Files\mhxy\shimen"
python tools\auto_screenshot.py
pause
