"""
LOVE Background Service Launcher

Keeps LOVE running in the background on Windows.
Uses pythonw.exe so no console window appears.

To install as Windows startup:
  python service/love_service.py install

To run once (testing):
  python service/love_service.py run

To stop:
  python service/love_service.py stop
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
PYTHONW = PROJECT_ROOT / "venv" / "Scripts" / "pythonw.exe"
PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
UVICORN = PROJECT_ROOT / "venv" / "Scripts" / "uvicorn.exe"
PID_FILE = PROJECT_ROOT / "data" / "service.pid"
LOG_FILE = PROJECT_ROOT / "data" / "service.log"
API_MAIN = PROJECT_ROOT / "api" / "main.py"

SERVICE_PORT = 8000


def is_running() -> bool:
    """Check if the service is already running."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is alive
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        return False


def start_service():
    """Start LOVE as a background process."""
    if is_running():
        print("LOVE service is already running.")
        return

    print(f"Starting LOVE background service on port {SERVICE_PORT}...")

    # Use pythonw on Windows (no console) or python on Linux
    launcher = str(PYTHONW) if PYTHONW.exists() else str(PYTHON)

    cmd = [
        launcher, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", str(SERVICE_PORT),
        "--log-level", "warning",
    ]

    log_file = open(LOG_FILE, "a")
    log_file.write(f"\n[{datetime.now().isoformat()}] LOVE service starting...\n")

    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=log_file,
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32" else 0,
    )

    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(proc.pid))
    print(f"LOVE service started (PID: {proc.pid})")
    print(f"UI: http://localhost:{SERVICE_PORT}")
    print(f"Log: {LOG_FILE}")


def stop_service():
    """Stop the LOVE service."""
    if not is_running():
        print("LOVE service is not running.")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        import psutil
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=10)
        PID_FILE.unlink(missing_ok=True)
        print(f"LOVE service stopped (PID: {pid})")
    except Exception as e:
        print(f"Stop error: {e}")
        PID_FILE.unlink(missing_ok=True)


def install_startup():
    """Install LOVE to run on Windows startup via Task Scheduler."""
    if sys.platform != "win32":
        print("Startup install is Windows-only. On Linux, use systemd.")
        return

    script_path = Path(__file__).absolute()
    python_path = PYTHON if PYTHON.exists() else sys.executable

    # Create a Task Scheduler XML
    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}" run</Arguments>
      <WorkingDirectory>{PROJECT_ROOT}</WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
</Task>"""

    task_file = PROJECT_ROOT / "data" / "love_startup_task.xml"
    task_file.write_text(task_xml, encoding="utf-16")

    # Register via schtasks
    try:
        result = subprocess.run(
            ["schtasks", "/create", "/xml", str(task_file), "/tn", "LOVE_AutoStart", "/f"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("LOVE registered as Windows startup task.")
        else:
            print(f"Task Scheduler registration failed: {result.stderr}")
            print(f"You can manually import: {task_file}")
    except Exception as e:
        print(f"Task Scheduler error: {e}")
        print(f"Manually import this XML in Task Scheduler: {task_file}")


def status():
    """Show service status."""
    running = is_running()
    print(f"LOVE Service: {'RUNNING' if running else 'STOPPED'}")
    if running:
        try:
            pid = int(PID_FILE.read_text().strip())
            print(f"PID: {pid}")
            print(f"UI: http://localhost:{SERVICE_PORT}")
        except Exception:
            pass


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        start_service()
    elif cmd == "start":
        start_service()
    elif cmd == "stop":
        stop_service()
    elif cmd == "restart":
        stop_service()
        import time; time.sleep(2)
        start_service()
    elif cmd == "status":
        status()
    elif cmd == "install":
        install_startup()
    else:
        print(f"Usage: python service/love_service.py [run|start|stop|restart|status|install]")
