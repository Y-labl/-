@echo off
cd /d "%~dp0"

echo ========================================
echo   Dian Ka Chang Jing Automation
echo ========================================
echo.

set PYTHON_EXE=%USERPROFILE%\AppData\Local\Programs\Python\Python38\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found: %PYTHON_EXE%
    echo Please install Python 3.8 and dependencies.
    pause
    exit /b 1
)

echo Starting...
"%PYTHON_EXE%" main.py

echo.
echo ========================================
echo Program exited. (code: %errorlevel%)
echo ========================================
pause
