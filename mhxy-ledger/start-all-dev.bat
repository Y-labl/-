@echo off
setlocal

rem mhxy-ledger: start server + client (npm run dev) in two new windows
rem Keep this file ASCII-only so cmd.exe (GBK) does not misparse UTF-8 bytes.

set "ROOT=%~dp0"
set "PATH=%PATH%;%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs"

if not exist "%ROOT%server\package.json" (
  echo ERROR: missing server\package.json
  echo Script dir: %ROOT%
  echo Put this .bat in the mhxy-ledger root folder.
  pause
  exit /b 1
)
if not exist "%ROOT%client\package.json" (
  echo ERROR: missing client\package.json
  pause
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo ERROR: npm not found in PATH.
  echo Install Node.js with "Add to PATH", or add its folder to PATH.
  pause
  exit /b 1
)

echo Server: %ROOT%server
echo Client: %ROOT%client
echo.

echo Checking MySQL database status...
netstat -ano | findstr ":3306" | findstr LISTENING >nul 2>&1
if errorlevel 1 (
  echo MySQL is not running on port 3306. Attempting to start MySQL...
  call "D:\MySQL\start-mysql-if-needed.bat"
  if errorlevel 1 (
    echo WARNING: Could not start MySQL. Please start it manually.
  ) else (
    echo MySQL started successfully.
  )
) else (
  echo MySQL is already running on port 3306.
)
echo.

echo Freeing listen ports 3001 ^(API^) and 5173 ^(Vite^) if a previous run is still bound...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%free-listen-ports.ps1" 3001 5173
if errorlevel 1 (
  echo WARNING: Could not free a port ^(permission or system process^). If startup fails, close the old window or Task Manager.
  echo.
)
echo Note: server uses "npm start" ^(stable^). For auto-reload on code edits use: npm run dev
echo.

start "mhxy-ledger-server" /D "%ROOT%server" cmd /k "set SKIP_DB_AUTO_MIGRATE=1 && npm start"
start "mhxy-ledger-client" /D "%ROOT%client" cmd /k "npm run dev"

echo Started server and client in new windows. This window can be closed; services keep running.
echo Stop them with Ctrl+C in each window.
echo.
pause
