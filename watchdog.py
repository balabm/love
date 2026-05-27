import subprocess
import time
import sys
import os

while True:
    process = subprocess.Popen(
        ["venv/Scripts/python.exe", "-m", "api.main"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    process.wait()
    
    if process.returncode != 0:
        print("Server crashed. Sentinel restarting in 3 seconds...")
        time.sleep(3)
    else:
        break
