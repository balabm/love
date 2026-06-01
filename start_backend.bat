@echo off
cd /d C:\Users\balab\OneDrive\Documents\Projects\LLove\love
set "PATH=C:\Program Files\nodejs;C:\Users\balab\AppData\Local\Programs\Ollama;%PATH%"
set "PYTHONPATH=C:\Users\balab\OneDrive\Documents\Projects\LLove\love"
C:\Users\balab\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir core --reload-dir tools --reload-dir agents
