@echo off
setlocal

title Project LOVE - Autonomous Life OS

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
    pause
    exit /b 1
)

REM -- Start Backend API in new window
echo   [1/3] Starting Backend API...
echo         Do NOT close the backend window.
start "LOVE Backend" cmd /k start_backend.bat

REM -- Wait for backend to initialize (takes ~20-25 seconds)
echo   [2/3] Waiting for backend to initialize...
echo         This takes ~25 seconds. Modules are loading...
timeout /t 25 /nobreak >nul
echo         Backend should be ready now.

REM -- Start Frontend UI in new window
echo   [3/3] Starting Frontend UI...
start "LOVE Frontend" cmd /k start_frontend.bat

REM -- Wait for Vite
timeout /t 5 /nobreak >nul

echo.
echo   ^<3  LOVE is running!
echo      Backend:  http://localhost:8000
echo      Frontend: http://localhost:5173
echo.
start http://localhost:5173
