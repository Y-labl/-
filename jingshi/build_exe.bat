@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 若你 Python 不在此路径，改成你的 python.exe 全路径
set "PY_EXE=D:\Programs\Python311\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

echo 目录: %CD%
echo Python: %PY_EXE%
echo.

"%PY_EXE%" -m PyInstaller "晶石购买助手.spec" --clean --noconfirm
set "EC=%ERRORLEVEL%"

echo.
if %EC% neq 0 (
  echo [失败] 退出码 %EC%，请把上面滚动内容复制保存便于排查。
) else (
  echo [成功] dist\晶石购买助手.exe
)

echo.
pause
