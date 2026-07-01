REM XiaoBaWang Decompile Launcher
@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [INFO] Installing deps...
pip install pyinstxtractor uncompyle6 -q 2>nul

echo [INFO] Running full decompile...
python full_decompile.py

echo.
echo [DONE] Output in ..\反编译结果\
pause
