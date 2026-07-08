@echo off
chcp 65001 >nul
echo ============================================
echo    梦幻西游自动化脚本 - Vue前端
echo ============================================
echo.

cd /d "%~dp0"

REM 检查Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

REM 检查npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到npm
    pause
    exit /b 1
)

echo [提示] 首次运行需要安装依赖...
echo.

REM 安装依赖
echo [1/2] 安装项目依赖...
call npm install

if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败!
    pause
    exit /b 1
)

echo.
echo [2/2] 启动开发服务器...
echo.
echo 前端地址: http://localhost:3000
echo API代理:  http://localhost:3000/api -> http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务
echo ============================================

REM 启动开发服务器
call npm run dev

pause
