@echo off
title Project LOVE - Autonomous Life OS
echo.
echo  ♥  Project LOVE - Starting up...
echo  ────────────────────────────────
echo.

cd /d D:\Balamurugan\Love\love

REM -- Start Backend API in new window
echo  [1/2] Starting Backend API (port 8000)...
start "LOVE Backend" cmd /k "cd /d D:\Balamurugan\Love\love && set PYTHONPATH=D:\Balamurugan\Love\love && venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir core --reload-dir tools --reload-dir agents --reload-dir voice"

REM -- Wait for backend to initialise
timeout /t 3 /nobreak >nul

REM -- Start Frontend UI in new window
echo  [2/2] Starting Frontend UI (port 5173)...
start "LOVE Frontend" cmd /k "cd /d D:\Balamurugan\Love\love\ui && npm run dev"

REM -- Wait then open browser
timeout /t 4 /nobreak >nul
echo.
echo  ♥  LOVE is running!
echo     Backend:  http://localhost:8000
echo     Frontend: http://localhost:5173
echo     API Docs: http://localhost:8000/docs
echo.
start http://localhost:5173