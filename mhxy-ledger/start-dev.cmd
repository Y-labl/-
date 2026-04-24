@echo off
setlocal

rem mhxy-ledger: start API (3001) + Vite in two windows. Keep ASCII-only for cmd (GBK).

set "ROOT=%~dp0"
set "PATH=%PATH%;%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs"

if not exist "%ROOT%server\package.json" (
  echo [start-dev] ERROR: missing server\package.json
  echo Put start-dev.cmd in repo root next to server\ and client\.
  pause
  exit /b 1
)
if not exist "%ROOT%client\package.json" (
  echo [start-dev] ERROR: missing client\package.json
  pause
  exit /b 1
)

if not exist "%ROOT%server\.env" (
  echo [start-dev] WARNING: server\.env missing. Copy server\.env.example to server\.env and set MySQL, then run again.
  echo.
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [start-dev] ERROR: npm not found. Install Node.js with "Add to PATH".
  pause
  exit /b 1
)

echo Releasing listen ports 3001 ^(API^) and 5173 ^(Vite^) if a previous run is still bound...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%free-listen-ports.ps1" 3001 5173
if errorlevel 1 (
  echo [start-dev] WARNING: could not free a port. If the page still says API offline, close old cmd windows or check Task Manager.
  echo.
)

echo Starting BACKEND first, then frontend. If the browser shows "cannot connect to API", read the BACKEND window ^(MySQL / migration errors^).
echo.

start "mhxy-ledger backend" /D "%ROOT%server" cmd /k "npm run dev"
timeout /t 3 /nobreak >nul
start "mhxy-ledger frontend" /D "%ROOT%client" cmd /k "npm run dev"

echo Started. This window can be closed; servers keep running. Stop with Ctrl+C in each service window.
pause
endlocal
