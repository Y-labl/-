@echo off
chcp 65001 >nul
echo ============================================
echo    梦幻西游自动化图色脚本 - 启动脚本
echo ============================================
echo.

cd /d "%~dp0"

REM 检查Java
where java >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Java，请先安装JDK 17+
    pause
    exit /b 1
)

REM 检查Maven
where mvn >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未找到Maven，将使用mvnw (如果有)
)

REM 启动前先清理
echo [1/2] 清理并编译项目...
call mvn clean compile -q

if %errorlevel% neq 0 (
    echo [错误] 编译失败!
    pause
    exit /b 1
)

echo [2/2] 启动Spring Boot应用...
echo.
echo 服务启动后访问: http://localhost:8080
echo 按 Ctrl+C 停止服务
echo.
echo ============================================

REM 启动应用
call mvn spring-boot:run

pause
