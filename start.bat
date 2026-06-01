@echo off
setlocal EnableDelayedExpansion
title Project LOVE - Autonomous Life OS

REM -- Use system Python (no venv exists)
set "PYTHON=C:\Users\balab\AppData\Local\Programs\Python\Python312\python.exe"
set "PATH=C:\Program Files\nodejs;C:\Users\balab\AppData\Local\Programs\Ollama;%PATH%"
set "PYTHONPATH=C:\Users\balab\OneDrive\Documents\Projects\LLove\love"

echo.
echo   ^<3  Project LOVE - Starting up...
echo   ----------------------------------------
echo.

cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love

REM -- Ensure data dir exists
if not exist "data" mkdir data

REM -- Kill any existing Python processes on port 8000
echo   [0/3] Cleaning up stale processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM -- Verify Python exists
if not exist "%PYTHON%" (
    echo   [ERROR] Python not found at %PYTHON%
    echo           Install Python 3.12 or update this batch file.
    pause
    exit /b 1
)

REM -- Start Backend API in new window
echo   [1/3] Starting Backend API (port 8000)...
echo         This takes ~20-30 seconds. Do NOT close the window.
start "LOVE Backend" cmd /k "set PATH=C:\Program Files\nodejs;C:\Users\balab\AppData\Local\Programs\Ollama;%%PATH%% ^&^& set PYTHONPATH=C:\Users\balab\OneDrive\Documents\Projects\LLove\love ^&^& cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love ^&^& %PYTHON% -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir core --reload-dir tools --reload-dir agents"

REM -- Wait for backend to actually respond
echo   [2/3] Waiting for backend to be ready...
set /a attempts=0
set /a max_attempts=60
:health_check
set /a attempts+=1
powershell -Command "try { $r=Invoke-WebRequest -Uri 'http://localhost:8000/health' -Method GET -Headers @{'X-API-Key'='love-dev-key'} -TimeoutSec 2 -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } } catch { }; exit 1" >nul 2>&1
if !errorlevel! neq 0 (
    if !attempts! lss !max_attempts! (
        echo         Attempt !attempts!/!max_attempts! - backend still loading...
        timeout /t 2 /nobreak >nul
        goto health_check
    ) else (
        echo.
        echo   [ERROR] Backend failed to start within timeout.
        echo           Check the LOVE Backend terminal window for errors.
        pause
        exit /b 1
    )
)
echo         Backend is UP and responding!

REM -- Start Frontend UI in new window
echo   [3/3] Starting Frontend UI (port 5173)...
start "LOVE Frontend" cmd /k "set PATH=C:\Program Files\nodejs;%%PATH%% ^&^& cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love\ui ^&^& npm run dev"

REM -- Wait for Vite to start
timeout /t 5 /nobreak >nul

echo.
echo   ^<3  LOVE is running!
echo      Backend:  http://localhost:8000
echo      Frontend: http://localhost:5173
echo      API Docs: http://localhost:8000/docs
echo.
echo   IMPORTANT: If the UI shows ^'offline^', press Ctrl+F5 in the browser.
echo.
start http://localhost:5173
