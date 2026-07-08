@echo off
cd /d "%~dp0"

echo ========================================
echo   Xiao Xi Tian Automation
echo ========================================
echo.

set PYTHON_EXE=%USERPROFILE%\AppData\Local\Programs\Python\Python38\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=.venv\Scripts\python.exe
)

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo Starting Xiao Xi Tian...
"%PYTHON_EXE%" xiaoxitian_main.py

echo.
echo ========================================
echo Program exited. (code: %errorlevel%)
echo ========================================
pause
