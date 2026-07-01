@echo off
setlocal enabledelayedexpansion

title XiaoBaWang Decompile Tool

echo ===================================================================
echo   XiaoBaWang - Full Decompile Tool
echo   Menghuan Xiyou Mobile Game Bot Reverse Engineering
echo ===================================================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python ready

echo.
echo [2/4] Installing dependencies...
pip install pyinstxtractor uncompyle6 -q 2>nul
echo [OK] Dependencies ready

echo.
echo [3/4] Running full decompile...
echo ===================================================================
echo.

cd /d "%~dp0"
python full_decompile.py

set RESULT=%errorlevel%

echo.
echo ===================================================================
echo [4/4] Done! (exit code: %RESULT%)
echo.
echo Output directory: ..\反编译结果\
echo.
echo If Java decompile failed, download jadx-gui:
echo   https://github.com/skylot/jadx/releases
echo Then drag subor.jar into jadx-gui and File -^> Save All
echo ===================================================================
echo.

pause
exit /b %RESULT%
