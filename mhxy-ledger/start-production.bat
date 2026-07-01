@echo off
setlocal

rem mhxy-ledger: Start production build (Preview + API)
rem Frontend runs on port 4173 (default preview port)
rem Backend runs on port 3001

set "ROOT=%~dp0"
set "PATH=%PATH%;%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs"

if not exist "%ROOT%server\package.json" (
  echo [start-production] ERROR: missing server\package.json
  pause
  exit /b 1
)
if not exist "%ROOT%client\package.json" (
  echo [start-production] ERROR: missing client\package.json
  pause
  exit /b 1
)

if not exist "%ROOT%client\dist" (
  echo [start-production] ERROR: client\dist not found. Please run 'npm run build' in client directory first.
  pause
  exit /b 1
)

if not exist "%ROOT%server\.env" (
  echo [start-production] WARNING: server\.env missing. Copy server\.env.example to server\.env and set MySQL, then run again.
  echo.
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [start-production] ERROR: npm run dev. Install Node.js with "Add to PATH".
  pause
  exit /b 1
)

echo Releasing listen ports 3001 ^(API^) and 4173 ^(Preview^) if a previous run is still bound...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%free-listen-ports.ps1" 3001 4173
if errorlevel 1 (
  echo [start-production] WARNING: could not free a port.
  echo.
)

echo Starting BACKEND and FRONTEND production servers...
echo.
echo Backend will run on: http://localhost:3001
echo Frontend will run on: http://localhost:4173
echo.

start "mhxy-ledger backend" (port 3001) /D "%ROOT%server" cmd /k "npm start"
timeout /t 2 /nobreak >nul
start "mhxy-ledger frontend" (port 4173) /D "%ROOT%client" cmd /k "npm run preview"

echo.
echo Started. This window can be closed; servers keep running.
echo Stop with Ctrl+C in each service window.
pause
endlocal
