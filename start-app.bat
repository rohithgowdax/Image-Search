@echo off
title VisualSearch AI - Launcher
color 0B

echo.
echo  +===========================================+
echo  ^|       VisualSearch AI - Starting Up        ^|
echo  +===========================================+
echo.

:: ── Kill any stale processes on ports 3000 and 8000 ─────────────────
echo [1/4] Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: ── Start Backend ────────────────────────────────────────────────────
echo [2/4] Starting Backend (FastAPI + CLIP)...
if not exist "%~dp0backend\venv\Scripts\activate.bat" (
    echo   ERROR: venv not found at backend\venv
    echo   Run: cd backend ^& python -m venv venv ^& venv\Scripts\activate ^& pip install -r requirements.txt
    pause
    exit /b 1
)

start "VisualSearch Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo   Backend starting at http://localhost:8000 ...
echo   (CLIP model may take 15-30s to load on first run)

:: ── Start Frontend ───────────────────────────────────────────────────
echo [3/4] Starting Frontend (React)...
if not exist "%~dp0frontend\node_modules" (
    echo   node_modules not found - installing...
    cd /d "%~dp0frontend"
    npm install
    cd /d "%~dp0"
)

start "VisualSearch Frontend" cmd /k "cd /d %~dp0frontend && npm start"
echo   Frontend starting at http://localhost:3000 ...

:: ── Wait and Open Browser ────────────────────────────────────────────
echo [4/4] Waiting for servers to be ready...
timeout /t 12 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo  +===========================================+
echo  ^|  App is running!                          ^|
echo  ^|  Frontend : http://localhost:3000         ^|
echo  ^|  Backend  : http://localhost:8000         ^|
echo  ^|  API Docs : http://localhost:8000/api/docs^|
echo  ^|                                           ^|
echo  ^|  Close the two terminal windows to stop.  ^|
echo  +===========================================+
echo.
pause
