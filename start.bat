@echo off
title Project LOVE - Autonomous Life OS

REM -- Ensure Node.js, Python, and Ollama are on PATH
set "PATH=C:\Program Files\nodejs;C:\Users\balab\AppData\Local\Programs\Ollama;%PATH%"
set "PYTHONPATH=C:\Users\balab\OneDrive\Documents\Projects\LLove\love"

echo.
echo  ^<3  Project LOVE - Starting up...
echo  ----------------------------------------
echo.

cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love

REM -- Ensure data dir exists for server log (Terminal Monitor needs it)
if not exist "data" mkdir data

REM -- Start Backend API in new window
REM    stdout+stderr are tee'd to data\server.log by _redirect_stderr_to_log() in main.py
REM    Terminal Monitor watches that file and auto-fixes Python errors via LLM
echo  [1/2] Starting Backend API (port 8000)...
start "LOVE Backend" cmd /k "set PATH=C:\Program Files\nodejs;C:\Users\balab\AppData\Local\Programs\Ollama;%%PATH%% && set PYTHONPATH=C:\Users\balab\OneDrive\Documents\Projects\LLove\love && cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love && venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir core --reload-dir tools --reload-dir agents"

REM -- Wait for backend to initialise
timeout /t 4 /nobreak >nul

REM -- Start Frontend UI in new window
echo  [2/2] Starting Frontend UI (port 5173)...
start "LOVE Frontend" cmd /k "set PATH=C:\Program Files\nodejs;%%PATH%% && cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love\ui && npm run dev"

REM -- Wait then open browser
timeout /t 5 /nobreak >nul
echo.
echo  ^<3  LOVE is running!
echo     Backend:  http://localhost:8000
echo     Frontend: http://localhost:5173
echo     API Docs: http://localhost:8000/docs
echo.
start http://localhost:5173
